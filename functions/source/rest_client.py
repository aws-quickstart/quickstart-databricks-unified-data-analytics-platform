import cfnresponse
import threading
import logging

from AccountApiSession import AccountApiSession
from CredentialConfigurations import CredentialConfigurationsManager
from StorageConfigurations import StorageConfigurationsManager
from ManagedKeysConfigurations import ManagedKeysConfigurationsManager
from NetworkConfigurations import NetworkConfiguratiosnManager
from Workspaces import WorkspacesManager
from WorkspaceManager import WorkspaceManager
from VpcEndpoints import VpcEndpointsManager
from PrivateAccessSettings import PrivateAccessSettingsManager

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
        'CREATE_WORKSPACES',
        'CREATE_WORKSPACE_VPC_ENPDPOINT',
        'CREATE_BACKEND_VPC_ENPDPOINT',
        'CREATE_PRIVATE_ACCESS_CONFIGURATION',
        'CREATE_HIPAA_CLUSTER_POLICY',
        'REGISTER_INSTANCE_PROFILE',
        'CREATE_STARTER_CLUSTER'
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
    physicalResourceId: str = event['PhysicalResourceId'] if 'PhysicalResourceId' in event else None

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
                responseData['ExternalId'] = credentialsConfiguration.externalId
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

        # PrivateLink VPC endpoints
        elif action in ('CREATE_WORKSPACE_VPC_ENPDPOINT', 'CREATE_BACKEND_VPC_ENPDPOINT'):
            endpointManager = VpcEndpointsManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['aws_region', 'endpoint_name', 'vpc_id', 'subnet_ids', 'security_group_ids'])
                endpoint = None
                endpointName = event['ResourceProperties']['endpoint_name']
                aws_region = event['ResourceProperties']['aws_region']
                vpcId = event['ResourceProperties']['vpc_id']
                subnetIds = [i.strip() for i in event['ResourceProperties']['subnet_ids'].split(',')]
                securityGroupIds = [i.strip() for i in event['ResourceProperties']['security_group_ids'].split(',')]
                tags = {'Name': endpointName}
                if action == 'CREATE_WORKSPACE_VPC_ENPDPOINT':
                    endpoint = endpointManager.createForRestAccess(endpointName, aws_region, vpcId, subnetIds, securityGroupIds, tags)
                else:
                    endpoint = endpointManager.createForRelayAccess(endpointName, aws_region, vpcId, subnetIds, securityGroupIds, tags)
                physicalResourceId = endpoint.id
            # deletion
            elif event['RequestType'] == 'Delete':
                endpointManager.delete(physicalResourceId)

        # Network configuration
        elif action == 'CREATE_NETWORKS':
            networkManager = NetworkConfiguratiosnManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['network_name', 'vpc_id', 'subnet_ids', 'security_group_ids'])
                networkConfiguration = networkManager.create(
                    name = event['ResourceProperties']['network_name'],
                    vpcId = event['ResourceProperties']['vpc_id'],
                    subnetIds = [i.strip() for i in event['ResourceProperties']['subnet_ids'].split(',')],
                    securityGroupIds = [i.strip() for i in event['ResourceProperties']['security_group_ids'].split(',')],
                    restAccessEndpointId = event['ResourceProperties']['rest_access_endpoint_id'] if 'rest_access_endpoint_id' in event['ResourceProperties'] else None,
                    relayAccessEndpointId = event['ResourceProperties']['relay_access_endpoint_id'] if 'relay_access_endpoint_id' in event['ResourceProperties'] else None
                )
                physicalResourceId = networkConfiguration.id
            # deletion
            elif event['RequestType'] == 'Delete':
                networkManager.delete(physicalResourceId)

        # Private Access Configuration
        elif action == 'CREATE_PRIVATE_ACCESS_CONFIGURATION':
            privateAccessSettingsManager = PrivateAccessSettingsManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['aws_region', 'private_access_settings_name', 'public_access_enabled', 'allowed_vpc_endpoint_ids'])
                privateAccessSettings = privateAccessSettingsManager.create(
                    name = event['ResourceProperties']['private_access_settings_name'],
                    region = event['ResourceProperties']['aws_region'],
                    publicAccessEnabled = event['ResourceProperties']['public_access_enabled'],
                    privateAccessLevel = 'ENDPOINT',
                    allowedVpcEndpointIds = [i.strip() for i in event['ResourceProperties']['allowed_vpc_endpoint_ids'].split(',')]
                )
                physicalResourceId = privateAccessSettings.id
            # deletion
            elif event['RequestType'] == 'Delete':
                privateAccessSettingsManager.delete(physicalResourceId)

        # Workspace
        elif action == 'CREATE_WORKSPACES':
            workspacesManager = WorkspacesManager(apiSession)
            # creation
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['workspace_name', 'aws_region', 'credentials_id', 'storage_config_id'])
                workspace = workspacesManager.create(
                    name = event['ResourceProperties']['workspace_name'],
                    region = event['ResourceProperties']['aws_region'],
                    credentialsId = event['ResourceProperties']['credentials_id'],
                    storageConfigurationId = event['ResourceProperties']['storage_config_id'],
                    networkId = event['ResourceProperties']['network_id'] if 'network_id' in event['ResourceProperties'] else None,
                    privateAccessSettingsId = event['ResourceProperties']['private_access_settings_id'] if 'private_access_settings_id' in event['ResourceProperties'] else None,
                    deploymentName = event['ResourceProperties']['deployment_name'] if 'deployment_name' in event['ResourceProperties'] and event['ResourceProperties']['deployment_name'] != '' else None,
                    storageCustomerManagedKeyId = event['ResourceProperties']['storage_customer_managed_key_id'] if 'storage_customer_managed_key_id' in event['ResourceProperties'] else None,
                    managedServicesCustomerManagedKeyId = event['ResourceProperties']['managed_services_customer_managed_key_id'] if 'managed_services_customer_managed_key_id' in event['ResourceProperties'] else None,
                    oemCustomerName = event['ResourceProperties']['customer_name'] if 'customer_name' in event['ResourceProperties'] else None,
                    oemAuthoritativeUserEmail = event['ResourceProperties']['authoritative_user_email'] if 'authoritative_user_email' in event['ResourceProperties'] else None,
                    oemAuthoritativeUserFullName = event['ResourceProperties']['authoritative_user_full_name'] if 'authoritative_user_full_name' in event['ResourceProperties'] else None
                )
                physicalResourceId = str(workspace.id)
                responseData['DeploymentName'] = workspace.deploymentName
                responseData['WorkspaceStatus'] = workspace.status
                responseData['WorkspaceStatusMsg'] = workspace.statusMessage
                responseData['PricingTier'] = workspace.pricingTier
                responseData['ClusterPolicyId'] = workspace.clusterPolicyId
                # Check if the workspace is running
                if workspace.status != 'RUNNING': raise Exception(workspace.statusMessage)
            # deletion
            elif event['RequestType'] == 'Delete':
                if physicalResourceId.isnumeric():
                    workspacesManager.delete(int(physicalResourceId))

        #### Workspace actions

        # Adding the HIPAA cluster policy
        elif action == 'CREATE_HIPAA_CLUSTER_POLICY':
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['workspace_deployment_name'])
                workspaceManager = WorkspaceManager(apiSession, event['ResourceProperties']['workspace_deployment_name'])
                physicalResourceId = workspaceManager.addHipaaClusterPolicy()

        # Adding an instance profile
        elif action == 'REGISTER_INSTANCE_PROFILE':
            if event['RequestType'] == 'Create':
                checkForMissingProperties(event, ['workspace_id', 'instance_profile_arn'])
                # Retrieve the workspace object for its deployment name and its pricing tier
                workspacesManager = WorkspacesManager(apiSession)
                workspaceObject = workspacesManager.get(int(event['ResourceProperties']['workspace_id']))
                pricingTier = workspaceObject.pricingTier
                registerForSQL = (pricingTier is not None) and (pricingTier != 'STANDARD')
                workspaceManager = WorkspaceManager(apiSession, workspaceObject.deploymentName)
                physicalResourceId = workspaceManager.addInstanceProfile(
                    event['ResourceProperties']['instance_profile_arn'],
                    registerForSQL
                )
        
        # Creating a Starter cluster
        elif action == 'CREATE_STARTER_CLUSTER':
            checkForMissingProperties(event, ['workspace_deployment_name'])
            workspaceManager = WorkspaceManager(apiSession, event['ResourceProperties']['workspace_deployment_name'])
            if event['RequestType'] == 'Create':
                physicalResourceId = workspaceManager.createStarterCluster(
                    instanceProfileArn = event['ResourceProperties']['instance_profile_arn'] if 'instance_profile_arn' in event['ResourceProperties'] else None,
                    policyId = event['ResourceProperties']['policy_id'] if 'policy_id' in event['ResourceProperties'] else None
                )
            # deletion
            elif event['RequestType'] == 'Delete':
                workspaceManager.terminateCluster(physicalResourceId)
    
    except Exception as e:
        reason = str(e)
        logging.exception(reason)
        status = cfnresponse.FAILED
    finally:
        timer.cancel()
        cfnresponse.send(event, context, status, responseData, physicalResourceId, reason = reason)
