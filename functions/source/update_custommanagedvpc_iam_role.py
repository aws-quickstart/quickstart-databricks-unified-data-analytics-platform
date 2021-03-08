import json
import logging
import threading
import boto3
import cfnresponse

# boto client

client = boto3.client('iam')

custom_managed_vpc_policy = {
    "Version": "2012-10-17",
    "Statement": [
      {
       "Sid": "VpcNonresourceSpecificActions",
       "Effect": "Allow",
       "Action": [
          "ec2:AuthorizeSecurityGroupEgress",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupEgress",
          "ec2:RevokeSecurityGroupIngress"
       ], 
       "Resource": [
       ], 
       "Condition": {
         "StringEquals": {
         }   
       }
      }
    ]  
}

sg = "arn:aws:ec2:AWSREGION:ACCOUNTID:security-group/SECURITYGROUPID"  
vpc = "ec2:vpc: arn:aws:ec2:AWSREGION:ACCOUNTID:vpc/VPCID"

def put_role_policy_sg(role_name, aws_region, accountid, security_group_ids, vpcid):
    global sg
    global vpc
    global custom_managed_vpc_policy
    sg_list = ([id.strip() for id in security_group_ids.split(",")])
    print('security groups list: {}'.format(sg_list),"\n")
    resource = custom_managed_vpc_policy['Statement'][0]['Resource']
    # Replace AWSREGION & ACCOUNTID strings for the Security Groups in the working area  
    sg = sg.replace('AWSREGION', aws_region)
    sg = sg.replace('ACCOUNTID', accountid)

    # Build the Resource block of the policy
    for i in sg_list: 
        sg_str = sg.replace('SECURITYGROUPID', str(i))
        resource.append(sg_str)
         
    # Update the policy with the Resource block         
    custom_managed_vpc_policy['Statement'][0]['Resource'] = resource  

    # Replace AWSREGION, ACCOUNTID and VPCID strings for the VPC in the working area
    vpc = vpc.replace('AWSREGION', aws_region)
    vpc = vpc.replace('ACCOUNTID', accountid)
    vpc = vpc.replace('VPCID', vpcid) 

    # Build the Condition block of the policy
    custom_managed_vpc_policy['Statement'][0]['Condition']['StringEquals'] = vpc   
    print('Managed Policy: {}'.format(json.dumps(custom_managed_vpc_policy)))

    response = client.put_role_policy(
        RoleName=role_name,
        PolicyName='databricks-cross-account-iam-role-policy-sg',
        PolicyDocument=json.dumps(custom_managed_vpc_policy)
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
        role_name = event['ResourceProperties']['RoleName']
        aws_region = event['ResourceProperties']['AWSRegion']
        accountId = event['ResourceProperties']['AccountId']
        security_group_ids = event['ResourceProperties']['SecurityGroupIds']
        vpcid = event['ResourceProperties']['VPCID']
        
        print('role_name - '+role_name)
        print('aws_region - '+aws_region)
        print('account_Id - '+accountId)
        print('security_group_ids - '+security_group_ids)
        print('vpcid - '+vpcid)
        
        if event['RequestType'] == 'Create':
            put_role_policy_sg(role_name, aws_region, accountId, security_group_ids, vpcid)
        else:
            pass
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        status = cfnresponse.FAILED
    finally:
        timer.cancel()
        cfnresponse.send(event, context, status, {}, None)