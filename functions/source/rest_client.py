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
    # make sure we send a failure to CloudFormation if the function is going to timeout
    timer = threading.Timer((context.get_remaining_time_in_millis()
            / 1000.00) - 0.5, timeout, args=[event, context])
    timer.start()

    print('Received event: %s' % json.dumps(event))
    status = cfnresponse.SUCCESS
    responseData = {}

    try:
        # Do no do anything if requestType is DELETE
        if event['RequestType'] == 'Create':            

            if event['ResourceProperties']['action'] == 'CREATE_CUSTOMER_MANAGED_KEY':
                post_result = create_customer_managed_key(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['key_arn'],
                                    event['ResourceProperties']['key_alias'],
                                    event['ResourceProperties']['key_region'],
                                    event['ResourceProperties']['encodedbase64'],
                                    event['ResourceProperties']['user_agent']
                                )
                responseData['CustomerManagedKeyId'] = post_result['customer_managed_key_id'] 

            if event['ResourceProperties']['action'] == 'CREATE_CREDENTIALS':
                post_result = create_credentials(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['credentials_name'],
                                    event['ResourceProperties']['role_arn'],
                                    event['ResourceProperties']['encodedbase64'],
                                    event['ResourceProperties']['user_agent']
                                )
                responseData['CredentialsId'] = post_result['credentials_id']
                responseData['ExternalId'] = post_result['aws_credentials']['sts_role']['external_id']

            if event['ResourceProperties']['action'] == 'CREATE_STORAGE_CONFIGURATIONS':
                post_result = create_storage_configurations(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['storage_config_name'],
                                    event['ResourceProperties']['s3bucket_name'],
                                    event['ResourceProperties']['encodedbase64'],
                                    event['ResourceProperties']['user_agent']
                                )
                responseData['StorageConfigId'] = post_result['storage_configuration_id']
            
            if event['ResourceProperties']['action'] == 'CREATE_NETWORKS':
                post_result = create_networks(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['network_name'],
                                    event['ResourceProperties']['vpc_id'],
                                    event['ResourceProperties']['subnet_ids'],
                                    event['ResourceProperties']['security_group_ids'],
                                    event['ResourceProperties']['encodedbase64'],
                                    event['ResourceProperties']['user_agent']
                                )
                responseData['NetworkId'] = post_result['network_id']

            if event['ResourceProperties']['action'] == 'CREATE_WORKSPACES':
                # Handle default_cluster Flag
                if event['ResourceProperties'].get('default_cluster') == 'Yes':
                        event['ResourceProperties']['default_cluster'] = True
                    else:
                        event['ResourceProperties']['default_cluster'] = False

                # Handle Hippa Flag
                if event['ResourceProperties'].get('hipaa_parm') == 'Yes':
                        event['ResourceProperties']['hipaa_parm'] = True
                    else:
                        event['ResourceProperties']['hipaa_parm'] = False

                post_result = create_workspaces(
                                    event['ResourceProperties']['accountId'],
                                    event['ResourceProperties']['workspace_name'],
                                    event['ResourceProperties']['deployment_name'],
                                    event['ResourceProperties']['aws_region'],
                                    event['ResourceProperties']['credentials_id'],
                                    event['ResourceProperties']['storage_config_id'],
                                    event['ResourceProperties']['encodedbase64'],
                                    event['ResourceProperties']['network_id'],
                                    event['ResourceProperties']['customer_managed_key_id'],
                                    event['ResourceProperties']['pricing_tier'],
                                    event['ResourceProperties']['hipaa_parm'],
                                    event['ResourceProperties']['customer_name'],
                                    event['ResourceProperties']['authoritative_user_email'],
                                    event['ResourceProperties']['authoritative_user_full_name'],
                                    event['ResourceProperties']['user_agent'],
                                    event['ResourceProperties']['default_cluster'],
                                )
                responseData['WorkspaceId'] = post_result['workspace_id']
                responseData['WorkspaceStatus'] = post_result['workspace_status']
                responseData['WorkspaceStatusMsg'] = post_result['workspace_status_message']
                responseData['DeploymentName'] = post_result['deployment_name']
                responseData['PricingTier'] = post_result['pricing_tier']
                responseData['ClusterPolicyId'] = post_result['policy_id']                    

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

# POST - create customer managed key 
def create_customer_managed_key(account_id, key_arn, key_alias, key_region, encodedbase64, user_agent):

    version = '1.1.0'
    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/customer-managed-keys"
    
    # Json data
    DATA = {
        "aws_key_info": {
            "key_arn": key_arn,
            "key_alias": key_alias,
            "key_region": key_region
        }
    }

    response = post_request(URL, DATA, encodedbase64, user_agent, version)
    print(response)
    
    # parse response
    customer_managed_key_id = response['customer_managed_key_id']
    print('customer_managed_key_id - {}'.format(customer_managed_key_id))
    return response

# POST - create credentials
def create_credentials(account_id, credentials_name, role_arn, encodedbase64, user_agent):

    version = '1.1.0' 
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

    response = post_request(URL, DATA, encodedbase64, user_agent, version)
    print(response)
    
    # parse response
    credentials_id = response['credentials_id']
    external_id = response['aws_credentials']['sts_role']['external_id']
    print('credentials_id - {}, external_id - {}'.format(credentials_id, external_id))
    return response

# POST - create storage configuration
def create_storage_configurations(account_id, storage_config_name, s3bucket_name, encodedbase64, user_agent):
    
    version = '1.1.0'
    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/storage-configurations"
    
    # Json data
    DATA = {
        "storage_configuration_name": storage_config_name,
        "root_bucket_info": {
            "bucket_name": s3bucket_name
        }
    }

    response = post_request(URL, DATA, encodedbase64, user_agent, version)
    print(response)
    
    # parse response
    storage_configuration_id = response['storage_configuration_id']
    print('storage_configuration_id - {}'.format(storage_configuration_id))
    return response

# POST - create network
def create_networks(account_id, network_name, vpc_id, subnet_ids, security_group_ids, encodedbase64, user_agent):
    
    version = '1.1.0'
    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/networks"

    # Json data
    DATA = {
        "network_name": network_name,
        "vpc_id": vpc_id,
        "subnet_ids": [id.strip() for id in subnet_ids.split(",")],
        "security_group_ids": [id.strip() for id in security_group_ids.split(",")]
    }

    response = post_request(URL, DATA, encodedbase64, user_agent, version)
    print(response)

    # parse response
    network_id = response['network_id']
    print('network_id - {}'.format(network_id))
    return response

# POST - create workspace
def create_workspaces(account_id, workspace_name, deployment_name, aws_region, credentials_id, storage_config_id, encodedbase64, network_id, customer_managed_key_id, pricing_tier, hipaa_parm, customer_name, authoritative_user_email, authoritative_user_full_name, user_agent, default_cluster):
    
    version = '1.2.0'
    # api-endpoint
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/workspaces"
    
    # Json data
    DATA = {
        "workspace_name": workspace_name, 
        "aws_region": aws_region, 
        "credentials_id": credentials_id, 
        "storage_configuration_id": storage_config_id,
        "pricing_tier": pricing_tier
    }

    NETWORKDATA = {
        "network_id": network_id
    }

    MANAGEDKEYDATA = {
        "customer_managed_key_id": customer_managed_key_id
    }

    DEPLOYMENTDATA = {
        "deployment_name": deployment_name
    }

    OEMDATA = {
        "external_customer_info": {
            "customer_name": customer_name,
            "authoritative_user_email": authoritative_user_email,
            "authoritative_user_full_name": authoritative_user_full_name
        }     
    }

    # Add network_id to the request object when provided
    if network_id != '':
        DATA.update(NETWORKDATA)

    # Add customer_managed__key_id to the request object when provided
    if customer_managed_key_id != '':
        DATA.update(MANAGEDKEYDATA)

    # Add deployment_name to the request object when provided, FYI Trial PAYG does not have a deployment_name or a deployment prefix
    if deployment_name != '':
        DATA.update(DEPLOYMENTDATA)

    # Add customer_info to the request object when provided, for the OEM program
    if customer_name != '':
        DATA.update(OEMDATA)

    response = post_request(URL, DATA, encodedbase64, user_agent, version)
    print(response)
    # parse the workspace_id elements from the response
    workspace_id = response['workspace_id']
    workspace_status = response['workspace_status']
    deployment_name = response['deployment_name']
    pricing_tier = response['pricing_tier']

    while workspace_status == 'PROVISIONING':
        time.sleep(10)
        response = get_workspace(account_id, workspace_id, encodedbase64, user_agent)
        workspace_status = response['workspace_status']
        workspace_status_message = response['workspace_status_message'] 
        print('workspace_id - {}, status - {}, message - {}'.format(workspace_id, workspace_status, workspace_status_message))  

    if workspace_status == 'FAILED':
        print('workspace FAILED about to raise an exception')
        raise Exception(workspace_status_message)

    if workspace_status == 'RUNNING':
        if hipaa_parm:
            # api-endpoint
            URL = "https://"+deployment_name+".cloud.databricks.com/api/2.0/policies/clusters/create"

            # Json data
            DATA = {
                "name": "Default Cluster Policy (HIPAA)", 
                "definition": "{\"node_type_id\":{\"type\":\"allowlist\",\"values\":[\"c5.xlarge\",\"c5.2xlarge\",\"c5.4xlarge\",\"c5.9xlarge\",\"c5.12xlarge\",\"c5.18xlarge\",\"c5.24xlarge\",\"c5d.xlarge\",\"c5d.2xlarge\",\"c5d.4xlarge\",\"c5d.9xlarge\",\"c5d.12xlarge\",\"c5d.18xlarge\",\"c5d.24xlarge\",\"g4dn.xlarge\",\"g4dn.2xlarge\",\"g4dn.4xlarge\",\"g4dn.8xlarge\",\"g4dn.12xlarge\",\"g4dn.16xlarge\",\"i3en.large\",\"i3en.xlarge\",\"i3en.2xlarge\",\"i3en.3xlarge\",\"i3en.6xlarge\",\"i3en.12xlarge\",\"i3en.24xlarge\",\"m5.large\",\"m5.xlarge\",\"m5.2xlarge\",\"m5.4xlarge\",\"m5.8xlarge\",\"m5.12xlarge\",\"m5.16xlarge\",\"m5.24xlarge\",\"m5a.large\",\"m5a.xlarge\",\"m5a.2xlarge\",\"m5a.4xlarge\",\"m5a.8xlarge\",\"m5a.12xlarge\",\"m5a.16xlarge\",\"m5a.24xlarge\",\"m5d.large\",\"m5d.xlarge\",\"m5d.2xlarge\",\"m5d.4xlarge\",\"m5d.8xlarge\",\"m5d.12xlarge\",\"m5d.16xlarge\",\"m5d.24xlarge\",\"r5.large\",\"r5.xlarge\",\"r5.2xlarge\",\"r5.4xlarge\",\"r5.8xlarge\",\"r5.12xlarge\",\"r5.16xlarge\",\"r5.24xlarge\",\"r5a.large\",\"r5a.xlarge\",\"r5a.2xlarge\",\"r5a.4xlarge\",\"r5a.8xlarge\",\"r5a.12xlarge\",\"r5a.16xlarge\",\"r5a.24xlarge\",\"r5d.large\",\"r5d.xlarge\",\"r5d.2xlarge\",\"r5d.4xlarge\",\"r5d.8xlarge\",\"r5d.12xlarge\",\"r5d.16xlarge\",\"r5d.24xlarge\",\"z1d.large\",\"z1d.xlarge\",\"z1d.2xlarge\",\"z1d.3xlarge\",\"z1d.6xlarge\",\"z1d.12xlarge\"],\"defaultValue\":\"c5.xlarge\"},\"driver_node_type_id\":{\"type\":\"allowlist\",\"values\":[\"c5.xlarge\",\"c5.2xlarge\",\"c5.4xlarge\",\"c5.9xlarge\",\"c5.12xlarge\",\"c5.18xlarge\",\"c5.24xlarge\",\"c5d.xlarge\",\"c5d.4xlarge\",\"c5d.2xlarge\",\"c5d.4xlarge\",\"c5d.9xlarge\",\"c5d.12xlarge\",\"c5d.18xlarge\",\"c5d.24xlarge\",\"g4dn.xlarge\",\"g4dn.2xlarge\",\"g4dn.4xlarge\",\"g4dn.8xlarge\",\"g4dn.12xlarge\",\"g4dn.16xlarge\",\"i3en.large\",\"i3en.xlarge\",\"i3en.2xlarge\",\"i3en.3xlarge\",\"i3en.6xlarge\",\"i3en.12xlarge\",\"i3en.24xlarge\",\"m5.large\",\"m5.xlarge\",\"m5.2xlarge\",\"m5.4xlarge\",\"m5.8xlarge\",\"m5.12xlarge\",\"m5.16xlarge\",\"m5.24xlarge\",\"m5a.large\",\"m5a.xlarge\",\"m5a.2xlarge\",\"m5a.4xlarge\",\"m5a.8xlarge\",\"m5a.12xlarge\",\"m5a.16xlarge\",\"m5a.24xlarge\",\"m5d.large\",\"m5d.xlarge\",\"m5d.2xlarge\",\"m5d.4xlarge\",\"m5d.8xlarge\",\"m5d.12xlarge\",\"m5d.16xlarge\",\"m5d.24xlarge\",\"r5.large\",\"r5.xlarge\",\"r5.2xlarge\",\"r5.4xlarge\",\"r5.8xlarge\",\"r5.12xlarge\",\"r5.16xlarge\",\"r5.24xlarge\",\"r5a.large\",\"r5a.xlarge\",\"r5a.2xlarge\",\"r5a.4xlarge\",\"r5a.8xlarge\",\"r5a.12xlarge\",\"r5a.16xlarge\",\"r5a.24xlarge\",\"r5d.large\",\"r5d.xlarge\",\"r5d.2xlarge\",\"r5d.4xlarge\",\"r5d.8xlarge\",\"r5d.12xlarge\",\"r5d.16xlarge\",\"r5d.24xlarge\",\"z1d.large\",\"z1d.xlarge\",\"z1d.2xlarge\",\"z1d.3xlarge\",\"z1d.6xlarge\",\"z1d.12xlarge\"],\"defaultValue\":\"c5.xlarge\"}}"
            } 

            print(DATA)    
            response_policy = post_request(URL, DATA, encodedbase64, user_agent, version)
            print(response_policy)
            # parse the policy_id element from the response
            policy_id = response_policy['policy_id']
       
            response.update(response_policy)
            print(response)

        else:
            cluster_policy_str = {
                "policy_id": "Cluster Policy is Not Applicable - HIPAA flag is set to NO"
                }  
            response.update(cluster_policy_str)    
            print(response)

        if default_cluster:
            # api-endpoint
            URL = "https://{deployment_name}.cloud.databricks.com/api/2.0/policies/clusters/create".format(deployment_name=deployment_name)

            # Json data
            DATA = {
                "name": "Default Cluster Policy",
                "definition": "{\"spark_version\":{\"type\":\"fixed\",\"value\":\"next-major-version-scala2.12\",\"hidden\":true}}"
            }

            print(DATA)
            response_policy = post_request(URL, DATA, encodedbase64, user_agent, version)
            print(response_policy)
            # parse the policy_id element from the response
            policy_id = response_policy['policy_id']

            response.update(response_policy)
            print(response)

            # DEFAULT CLUSTER in Terminating State
            CLUSTER_URL = "https://{deployment_name}.cloud.databricks.com/api/2.0/clusters/create".format(deployment_name=deployment_name)

            CLUSTER_DATA = {
                "cluster_name": "basic-starter-cluster",
                "spark_version": "7.6.x-scala2.12",
                "node_type_id": "m5d.large",
                "num_workers": 0,
                "start_cluster": False,
                "spark_conf": {
                    "spark.databricks.cluster.profile": "singleNode",
                    "spark.master": "local[*]"
                },
                "custom_tags": {
                    "ResourceClass": "SingleNode"
                }
            }

            try:
                default_cluster = post_request(CLUSTER_URL, CLUSTER_DATA, encodedbase64, user_agent, version)
                print(default_cluster)
                # parse the cluster_id element from the response
                cluster_id = default_cluster['cluster_id']

                print(cluster_id)

            except Exception as e:
                logging.error('Exception: %s' % e, exc_info=True)
                
        else:
            cluster_policy_str = {
                "policy_id": "Default Cluster Policy is Not Applicable - Default cluster flag is set to NO"
            }
            response.update(cluster_policy_str)
            print(response)

    else:
        cluster_policy_str = {
            "policy_id": "Cluster Policy cannot be created because the workspace creation has FAILED!"
            }  
        response.update(cluster_policy_str)    
        print(response)
         

    return response
    

# GET - get workspace
def get_workspace(account_id, workspace_id, encodedbase64, user_agent):
    
    version = '1.1.0'
    # api-endpoint
    workspace_identifier = str(workspace_id)
    URL = "https://accounts.cloud.databricks.com/api/2.0/accounts/"+account_id+"/workspaces/"+workspace_identifier

    response = get_request(URL, encodedbase64, user_agent, version)
    
    return response

# POST request function
def post_request(url, json_data, encodedbase64, user_agent, version):
    # sending post request and saving the response as response object
    resp = requests.post(url, json=json_data, headers={"Authorization": "Basic %s" % encodedbase64, "User-Agent": "%s - %s" % (user_agent, version)})
    
    # extracting data in json format 
    data = resp.json() 
    
    # If the response was successful, no Exception will be raised
    resp.raise_for_status()
    
    print('Successful POST call!!')
    return data

# GET request function
def get_request(url, encodedbase64, user_agent, version):
    # sending get request and saving the response as response object 
    resp = requests.get(url=url, headers={"Authorization": "Basic %s" % encodedbase64, "User-Agent": "%s - %s" % (user_agent, version)})
    
    # extracting data in json format 
    data = resp.json() 
    
    # If the response was successful, no Exception will be raised
    resp.raise_for_status()
    
    print('Successful GET call!!')
    return data