# importing the requests library 
import requests 
from requests.exceptions import HTTPError
import cfnresponse
import threading
import logging
import json
import time

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
    responseData = {}

    try:
        # Do no do anything if requestType is DELETE
        if event['RequestType'] == 'Create':            

            if event['ResourceProperties']['action'] == 'CREATE_CREDENTIALS':
                post_result = create_credentials(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['credentials_name'],
                                    event['ResourceProperties']['role_arn'],
                                    event['ResourceProperties']['username'],
                                    event['ResourceProperties']['password']
                                )
                responseData['CredentialsId'] = post_result['credentials_id']
                responseData['ExternalId'] = post_result['aws_credentials']['sts_role']['external_id']

            if event['ResourceProperties']['action'] == 'CREATE_STORAGE_CONFIGURATIONS':
                post_result = create_storage_configurations(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['storage_config_name'],
                                    event['ResourceProperties']['s3bucket_name'],
                                    event['ResourceProperties']['username'],
                                    event['ResourceProperties']['password']
                                )
                responseData['StorageConfigId'] = post_result['storage_configuration_id']
            
            if event['ResourceProperties']['action'] == 'CREATE_NETWORKS':
                post_result = create_networks(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['network_name'],
                                    event['ResourceProperties']['vpc_id'],
                                    event['ResourceProperties']['subnet_ids'],
                                    event['ResourceProperties']['security_group_ids'],
                                    event['ResourceProperties']['username'],
                                    event['ResourceProperties']['password']
                                )
                responseData['NetworkId'] = post_result['network_id']

            if event['ResourceProperties']['action'] == 'CREATE_WORKSPACES':
                post_result = create_workspaces(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['workspace_name'],
                                    event['ResourceProperties']['deployment_name'],
                                    event['ResourceProperties']['aws_region'],
                                    event['ResourceProperties']['credentials_id'],
                                    event['ResourceProperties']['storage_config_id'],
                                    event['ResourceProperties']['username'],
                                    event['ResourceProperties']['password'],
                                    event['ResourceProperties']['network_id'],
                                    event['ResourceProperties']['noprivateip']
                                )
                responseData['WorkspaceId'] = workspace_ids
                responseData['WorkspaceStatus'] = workspace_statuses
                responseData['WorkspaceStatusMsg'] = workspace_status_msgs

            if event['ResourceProperties']['action'] == 'GET_WORKSPACES':
                get_wrkspc_result = get_workspaces(
                                        event['ResourceProperties']['accountId'],
                                        event['ResourceProperties']['workspace_id'],
                                        event['ResourceProperties']['username'],
                                        event['ResourceProperties']['password']
                                    )
                responseData['WorkspaceStatus'] = get_wrkspc_result['workspace_status']
                responseData['WorkspaceStatusMsg'] = get_wrkspc_result['workspace_status_message']
        
        else:
            logging.debug('RequestType - {}'.format(event['RequestType']))
        
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        print(f'HTTP content: {http_err.response.content}')
        status = cfnresponse.FAILED
    except Exception as e:
        logging.error('Exception: %s' % e, exc_info=True)
        status = cfnresponse.FAILED
    finally:
        timer.cancel()
        cfnresponse.send(event, context, status, responseData, None)

# POST - create credentials
def create_credentials(account_id, credentials_name, role_arn, username, password):

    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/credentials"
    
    # Json data
    DATA = {
        "credentials_name": credentials_name, 
        "aws_credentials": {
            "sts_role": {
                "role_arn": role_arn
            }
        }
    }

    response = post_request(URL, DATA, username, password)
    print(response)
    
    # parse response
    credentials_id = response['credentials_id']
    external_id = response['aws_credentials']['sts_role']['external_id']
    print('credentials_id - {}, external_id - {}'.format(credentials_id, external_id))
    return response

# POST - create storage configuration
def create_storage_configurations(account_id, storage_config_name, s3bucket_name, username, password):
    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/storage-configurations"
    
    # Json data
    DATA = {
        "storage_configuration_name": storage_config_name,
        "root_bucket_info": {
            "bucket_name": s3bucket_name
        }
    }

    response = post_request(URL, DATA, username, password)
    print(response)
    
    # parse response
    storage_configuration_id = response['storage_configuration_id']
    print('storage_configuration_id - {}'.format(storage_configuration_id))
    return response

# POST - create network
def create_networks(account_id, network_name, vpc_id, subnet_ids, security_group_ids, username, password):
    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/networks"

    # Json data
    DATA = {
        "network_name": network_name,
        "vpc_id": vpc_id,
        "subnet_ids": [id.strip() for id in subnet_ids.split(",")],
        "security_group_ids": [id.strip() for id in security_group_ids.split(",")]
    }

    response = post_request(URL, DATA, username, password)
    print(response)

    # parse response
    network_id = response['network_id']
    print('network_id - {}'.format(network_id))
    return response

# POST - create workspace
def create_workspaces(account_id, workspace_name, deployment_name, aws_region, credentials_id, storage_config_id, username, password, network_id, noprivateip):
    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/workspaces"
    
    # Json data
    DATA = {
        "workspace_name": workspace_name, 
        "deployment_name": deployment_name, 
        "aws_region": aws_region, 
        "credentials_id": credentials_id, 
        "storage_configuration_id": storage_config_id
    }

    # Add networkId to the request object, if one is provided
    if network_id != '':
        DATA["network_id"] = network_id
        DATA["is_no_public_ip_enabled"] = noprivateip

    response = post_request(URL, DATA, username, password)
    print(response)
    
    # parse response
    workspace_id = response['workspace_id']
    workspace_status = response['workspace_status']
    workspace_status_message = response['workspace_status_message']
    print('workspace_id - {}, status - {}, message - {}'.format(workspace_id, workspace_status, workspace_status_message))
    return response

# GET - get workspace
def get_workspaces(account_id, workspace_id, username, password):
    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/workspaces/"+workspace_id

    response = get_request(URL, username, password)
    print(response)

    # parse response
    workspace_status = response['workspace_status']
    workspace_status_message = response['workspace_status_message']
    print('workspace status - {}, msg - {}'.format(workspace_status, workspace_status_message))
    return response
    

# POST request function
def post_request(url, json_data, username, password):
    # sending post request and saving the response as response object
    resp = requests.post(url, json=json_data, auth=(username, password))
    
    # extracting data in json format 
    data = resp.json() 
    
    # If the response was successful, no Exception will be raised
    resp.raise_for_status()
    
    print('Successful POST call!!')
    return data

# GET request function
def get_request(url, username, password):
    # sending get request and saving the response as response object 
    resp = requests.get(url = url, auth=(username, password)) 
    
    # extracting data in json format 
    data = resp.json() 
    
    # If the response was successful, no Exception will be raised
    resp.raise_for_status()
    
    print('Successful GET call!!')
    return data