import json
import logging
import threading
import boto3
import cfnresponse
client = boto3.client('iam')

def get_trust_policy(role_name):
    # describe iam role
    response_get_role = client.get_role(
        RoleName=role_name
    )
    trust_policy = response_get_role['Role']['AssumeRolePolicyDocument']
    print('iam role trust policy is: '+ str(trust_policy))
    return(trust_policy)

def update_trust_policy(role_name, external_id):
    current_trust_policy = get_trust_policy(role_name)
    # replace placeholder in trust policy stmt with external id
    current_trust_policy['Statement'][0]['Condition']['StringEquals']['sts:ExternalId'] = external_id
    print('new trust policy: {}'.format(json.dumps(current_trust_policy)))
    # update iam role trust policy document
    response = client.update_assume_role_policy(
        RoleName=role_name,
        PolicyDocument=json.dumps(current_trust_policy)
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
        external_id = event['ResourceProperties']['ExternalId']
        role_name = event['ResourceProperties']['IAMRoleName']
        
        print('external_id - '+external_id)
        print('iam_role_name - '+role_name)
        
        if event['RequestType'] == 'Create':
            update_trust_policy(role_name, external_id)
        else:
            pass
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        status = cfnresponse.FAILED
    finally:
        timer.cancel()
        cfnresponse.send(event, context, status, {}, None)