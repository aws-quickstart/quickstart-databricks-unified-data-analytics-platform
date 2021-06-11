import json
import logging
import threading
import boto3
import cfnresponse

# boto client

client = boto3.client('kms')

databricks_s3bucketonly_statement1 = {
  "Sid": "Allow Databricks to use KMS key for DBFS",
  "Effect": "Allow",
  "Principal":{
    "AWS":"arn:aws:iam::414351767826:root"
  },
  "Action": [
    "kms:Encrypt",
    "kms:Decrypt",
    "kms:ReEncrypt*",
    "kms:GenerateDataKey*",
    "kms:DescribeKey"
  ],
  "Resource": "*"
}

databricks_s3bucketonly_statement2 = {
  "Sid": "Allow Databricks to use KMS key for DBFS (Grants)",
  "Effect": "Allow",
  "Principal":{
    "AWS":"arn:aws:iam::414351767826:root"
  },
  "Action": [
    "kms:CreateGrant",
    "kms:ListGrants",
    "kms:RevokeGrant"
  ],
  "Resource": "*",
  "Condition": {
    "Bool": {
      "kms:GrantIsForAWSResource": "true"
    }
  }
}

databricks_s3bucketandEBS_statement1 = {
  "Sid": "Allow Databricks to use KMS key for DBFS",
  "Effect": "Allow",
  "Principal":{
    "AWS":"arn:aws:iam::414351767826:root"
  },
  "Action": [
    "kms:Encrypt",
    "kms:Decrypt",
    "kms:ReEncrypt*",
    "kms:GenerateDataKey*",
    "kms:DescribeKey"
  ],
  "Resource": "*"
}

databricks_s3bucketandEBS_statement2 = {
  "Sid": "Allow Databricks to use KMS key for DBFS (Grants)",
  "Effect": "Allow",
  "Principal":{
    "AWS":"arn:aws:iam::414351767826:root"
  },
  "Action": [
    "kms:CreateGrant",
    "kms:ListGrants",
    "kms:RevokeGrant"
  ],
  "Resource": "*",
  "Condition": {
    "Bool": {
      "kms:GrantIsForAWSResource": "true"
    }
  }
}

databricks_s3bucketandEBS_statement3 = {
  "Sid": "Allow Databricks to use KMS key for EBS",
  "Effect": "Allow",
  "Principal": {
    "AWS": "ARNCREDENTIALS"
  },
  "Action": [
    "kms:Decrypt",
    "kms:GenerateDataKey*",
    "kms:CreateGrant",
    "kms:DescribeKey"
  ],
  "Resource": "*",
  "Condition": {
    "ForAnyValue:StringLike": {
      "kms:ViaService": "ec2.*.amazonaws.com"
    }
  }
}

def get_key_policy(key_id):
    response = client.get_key_policy(
        KeyId=key_id,
        PolicyName='default'
    )
    key_policy = response['Policy']
    print('kms key policy is: '+ str(key_policy))
    return(key_policy)

def update_key_policy(key_id, arn_credentials, reuse_key_for_cluster_volumes):
    global databricks_s3bucketandEBS_statement
    global databricks_s3bucketonly_statement
    current_key_policy = json.loads(get_key_policy(key_id))
    statements = current_key_policy['Statement']
    print('no. of statements in current policy are : {}'.format(len(statements)))

    # update the kms policy statement
    if reuse_key_for_cluster_volumes == 'True':
        databricks_s3bucketandEBS_statement3['Principal']['AWS'] = str(arn_credentials)
        statements.append(databricks_s3bucketandEBS_statement1)
        statements.append(databricks_s3bucketandEBS_statement2)
        statements.append(databricks_s3bucketandEBS_statement3)
    else:
        statements.append(databricks_s3bucketonly_statement1)
        statements.append(databricks_s3bucketonly_statement2) 

    print('no. of statements in new policy are : {}'.format(len(statements)))
    current_key_policy['Statement'] = statements
    print('new policy is : {}'.format(json.dumps(current_key_policy)))  
    
    # Update new statements in current key policy
    response = client.put_key_policy(
        KeyId=key_id,
        PolicyName='default',
        Policy=json.dumps(current_key_policy)
    )
    
def timeout(event, context):
    logging.error('Execution is about to time out, sending failure response to CloudFormation')
    cfnresponse.send(event, context, cfnresponse.FAILED, {}, None)

def handler(event, context):
    # make sure we send a failure to CloudFormation if the function
    # is going to timeout
    timer = threading.Timer((context.get_remaining_time_in_millis()
            / 1000.00) - 0.5, timeout, args=[event, context])
    timer.start()
    print('Received event: %s' % json.dumps(event))
    status = cfnresponse.SUCCESS
    
    try:
        key_id = event['ResourceProperties']['key_id']
        arn_credentials = event['ResourceProperties']['arn_credentials']
        use_cases = event['ResourceProperties']['use_cases']
        reuse_key_for_cluster_volumes = event['ResourceProperties']['reuse_key_for_cluster_volumes']

        if event['RequestType'] == 'Create':
            #  Nothing to do if MANAGED_SERVICES is the use case
            if use_cases == 'STORAGE' or 'BOTH':
                update_key_policy(key_id, arn_credentials, reuse_key_for_cluster_volumes)
        
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        status = cfnresponse.FAILED
    finally:
        timer.cancel()
        cfnresponse.send(event, context, status, {}, None)