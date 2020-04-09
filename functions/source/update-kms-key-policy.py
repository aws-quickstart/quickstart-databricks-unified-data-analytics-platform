import json
import logging
import threading
import boto3
import cfnresponse

# boto client
client = boto3.client('kms')
# Databricks kms key policy statement
databricks_statement = {
    "Sid": "Allow Databricks to use KMS key for BYOK",
    "Effect": "Allow", 
    "Principal": { 
        "AWS": "arn:aws:iam::414351767826:root" 
    },
    "Action": [ 
        "kms:Encrypt", 
        "kms:Decrypt" 
    ], 
    "Resource": "*"
}

def get_key_policy(key_id):
    response = client.get_key_policy(
        KeyId=key_id,
        PolicyName='default'
    )
    key_policy = response['Policy']
    print('kms key policy is: '+ str(key_policy))
    return(key_policy)

def update_key_policy(key_id):
    current_key_policy = json.loads(get_key_policy(key_id))
    statements = current_key_policy['Statement']
    print('no. of statements in current policy are : {}'.format(len(statements)))
    # add databricks statement into kms policy statement
    statements.append(databricks_statement)
    print('no. of statements in new policy are : {}'.format(len(statements)))
    # Update new statements in current key policy
    current_key_policy['Statement'] = statements
    print('new policy is : {}'.format(current_key_policy))
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
        key_id = event['ResourceProperties']['KMSKeyID']
        
        print('key_id - '+key_id)
        
        if event['RequestType'] == 'Create':
            update_key_policy(key_id)
        else:
            pass
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        status = cfnresponse.FAILED
    finally:
        timer.cancel()
        cfnresponse.send(event, context, status, {}, None)