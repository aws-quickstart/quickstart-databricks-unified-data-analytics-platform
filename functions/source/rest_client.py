import cfnresponse
import threading
import logging

from AccountApiSession import AccountApiSession
from CredentialConfigurations import CredentialConfigurationsManager
from StorageConfigurations import StorageConfigurationsManager
from ManagedKeysConfigurations import ManagedKeysConfigurationsManager
from NetworkConfigurations import NetworkConfiguratiosnManager
from Workspaces import WorkspaceManager

def timeout(event, context):
    logging.error('Execution is about to time out, sending failure response to CloudFormation')
    cfnresponse.send(event, context, cfnresponse.FAILED, {}, None)


def checkForMissingProperties(event, propertyList: list):
    for property in propertyList:
        if property not in event['ResourceProperties']:
            raise Exception('Property "' + property + '" not specified')


def handler(event, context):
    # User Agent version
    userAgentVersion = '1.5.0'

    # Check for the existence of an action key and support for the action
    supportedActions = (
        'CREATE_CREDENTIALS',
        'CREATE_STORAGE_CONFIGURATIONS',
        'CREATE_CUSTOMER_MANAGED_KEY',
        'CREATE_NETWORKS',
        'CREATE_WORKSPACES'
    )
    if 'action' not in event['ResourceProperties'] or event['ResourceProperties']['action'] not in supportedActions:
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, None, reason = 'No supported action specified')
        return
    action = event['ResourceProperties']['action']

    # make sure we send a failure to CloudFormation if the function is going to timeout
    timer = threading.Timer((context.get_remaining_time_in_millis()
            / 1000.00) - 0.5, timeout, args=[event, context])
    timer.start()

    # The default return values (to CloudFormation)
    status = cfnresponse.SUCCESS
    reason = None
    responseData = {}
    physicalResourceId = event['PhysicalResourceId'] if 'PhysicalResourceId' in event else None

    try:
        # Create the Account API session
        checkForMissingProperties(event, ['accountId', 'username', 'password'])
        apiSession = AccountApiSession(
            event['ResourceProperties']['accountId'],
            event['ResourceProperties']['username'],
            event['ResourceProperties']['password'],
            event['ResourceProperties']['user_agent'] + ' - ' + userAgentVersion if 'user_agent' in event['ResourceProperties'] else None
        )

        # Credentials configuration
        if action == 'CREATE_CREDENTIALS':
            credentialsManager = CredentialConfigurationsManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['credentials_name', 'role_arn'])
                credentialsConfiguration = credentialsManager.create(
                    name = event['ResourceProperties']['credentials_name'],
                    roleArn = event['ResourceProperties']['role_arn']
                )
                physicalResourceId = credentialsConfiguration.id
            # deletion
            elif event['RequestType'] == 'Delete':
                credentialsManager.delete(physicalResourceId)

        # Storage configuration
        elif action == 'CREATE_STORAGE_CONFIGURATIONS':
            storageManager = StorageConfigurationsManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['storage_config_name', 's3bucket_name'])
                storageConfiguration = storageManager.create(
                    name = event['ResourceProperties']['storage_config_name'],
                    bucket = event['ResourceProperties']['s3bucket_name']
                )
                physicalResourceId = storageConfiguration.id
            # deletion
            elif event['RequestType'] == 'Delete':
                storageManager.delete(physicalResourceId)

        # Customer Managed Key
        elif action == 'CREATE_CUSTOMER_MANAGED_KEY':
            keyManager = ManagedKeysConfigurationsManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['key_arn', 'use_cases'])
                keyAlias = event['ResourceProperties']['key_alias'] if 'key_alias' in event['ResourceProperties'] else None
                useCasesString = event['ResourceProperties']['use_cases']
                useCases = []
                if useCasesString == 'BOTH':
                    useCases += ['MANAGED_SERVICES', 'STORAGE']
                else: useCases.append(useCasesString)
                reuseKeyForClusterVolumesString = event['ResourceProperties']['reuse_key_for_cluster_volumes'] if 'reuse_key_for_cluster_volumes' in event['ResourceProperties'] else 'False'
                keyConfiguration = keyManager.create(
                    keyArn = event['ResourceProperties']['key_arn'],
                    keyAlias = keyAlias,
                    useCases = useCases,
                    reuseKeyForClusterVolumes = (reuseKeyForClusterVolumesString == 'True')
                )
                physicalResourceId = keyConfiguration.id
            # deletion
            elif event['RequestType'] == 'Delete':
                keyManager.delete(physicalResourceId)

        # Network configuration
        elif action == 'CREATE_NETWORKS':
            networkManager = NetworkConfiguratiosnManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['network_name', 'vpc_id', 'subnet_ids', 'security_group_ids'])
                networkConfiguration = networkManager.create(
                    name = event['ResourceProperties']['network_name'],
                    vpcId = event['ResourceProperties']['vpc_id'],
                    subnetIds = event['ResourceProperties']['subnet_ids'].split(','),
                    securityGroupIds = event['ResourceProperties']['security_group_ids'].split(','),
                    restAccessEndpointId = event['ResourceProperties']['rest_access_endpoint_id'] if 'rest_access_endpoint_id' in event['ResourceProperties'] else None,
                    relayAccessEndpointId = event['ResourceProperties']['relay_access_endpoint_id'] if 'relay_access_endpoint_id' in event['ResourceProperties'] else None
                )
                physicalResourceId = networkConfiguration.id
            # deletion
            elif event['RequestType'] == 'Delete':
                networkManager.delete(physicalResourceId)

        # Workspace
        elif action == 'CREATE_WORKSPACES':
            workspaceManager = WorkspaceManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['workspace_name', 'aws_region', 'credentials_id', 'storage_config_id'])
                workspace = workspaceManager.create(
                    name = event['ResourceProperties']['workspace_name'],
                    region = event['ResourceProperties']['aws_region'],
                    credentialsId = event['ResourceProperties']['credentials_id'],
                    storageConfigurationId = event['ResourceProperties']['storage_config_id'],
                    networkId = event['ResourceProperties']['network_id'] if 'network_id' in event['ResourceProperties'] else None,
                    privateAccessSettingsId = event['ResourceProperties']['private_access_settings_id'] if 'private_access_settings_id' in event['ResourceProperties'] else None,
                    deploymentName = event['ResourceProperties']['deployment_name'] if 'deployment_name' in event['ResourceProperties'] else None,
                    storageCustomerManagedKeyId = event['ResourceProperties']['storage_customer_managed_key_id'] if 'storage_customer_managed_key_id' in event['ResourceProperties'] else None,
                    managedServicesCustomerManagedKeyId = event['ResourceProperties']['managed_services_customer_managed_key_id'] if 'managed_services_customer_managed_key_id' in event['ResourceProperties'] else None,
                    hipaaEnabled = (event['ResourceProperties']['hipaa_parm'] == 'True') if 'hipaa_parm' in event['ResourceProperties'] else False,
                    oemCustomerName = event['ResourceProperties']['customer_name'] if 'customer_name' in event['ResourceProperties'] else None,
                    oemAuthoritativeUserEmail = event['ResourceProperties']['authoritative_user_email'] if 'authoritative_user_email' in event['ResourceProperties'] else None,
                    oemAuthoritativeUserFullName = event['ResourceProperties']['authoritative_user_full_name'] if 'authoritative_user_full_name' in event['ResourceProperties'] else None
                )
                physicalResourceId = workspace.id
            # deletion
            elif event['RequestType'] == 'Delete':
                networkManager.workspaceManager(physicalResourceId)
        
    except Exception as e:
        reason = str(e)
        logging.exception(reason)
        status = cfnresponse.FAILED
    finally:
        timer.cancel()
        cfnresponse.send(event, context, status, responseData, physicalResourceId, reason = reason)
