from AccountApiSession import AccountApiSession
import time

# The workspace object
class Workspace:
  def __init__(self, data: dict):
    self.id = data['workspace_id']
    self.name = data['workspace_name']
    self.credentialsId = data['credentials_id']
    self.storageConfigurationId = data['storage_configuration_id']
    self.region = data['aws_region']
    self.status = data['workspace_status']
    self.networkId = data['network_id'] if 'network_id' else None
    self.privateAccessSettingsId = data['private_access_settings_id'] if 'private_access_settings_id' in data else None
    self.deploymentName = data['deployment_name'] if 'deployment_name' in data else None
    self.pricingTier = data['pricing_tier'] if 'pricing_tier' in data else None


# The workspace manager
class WorkspaceManager:
  def __init__(self, apiSession: AccountApiSession):
    self.__apiSession = apiSession


  # Creates a new workspace
  def create(self, name: str, region: str, credentialsId: str, storageConfigurationId: str,
    networkId: str = None, privateAccessSettingsId: str = None, deploymentName: str = None,
    storageCustomerManagedKeyId: str = None, managedServicesCustomerManagedKeyId: str = None):
    postData = {
      "workspace_name": name,
      "aws_region": region,
      "credentials_id": credentialsId,
      "storage_configuration_id": storageConfigurationId
    }
    if networkId is not None: postData["network_id"] = networkId
    if deploymentName is not None: postData['deployment_name'] = deploymentName
    if privateAccessSettingsId is not None: postData['private_access_settings_id'] = privateAccessSettingsId
    if storageCustomerManagedKeyId is not None: postData['storage_customer_managed_key_id'] = storageCustomerManagedKeyId
    if managedServicesCustomerManagedKeyId is not None: postData['managed_services_customer_managed_key_id'] = managedServicesCustomerManagedKeyId
    # Issue the API call
    workspaceObject = Workspace(self.__apiSession.post('/workspaces', postData))
    # Wait for the workspace to start running
    while True:
      time.sleep(5)
      try:
        workspaceObject = self.get(workspaceObject.id)
        if workspaceObject.status == 'RUNNING': break
      except Exception as e:
        print(str(e))
    return workspaceObject


  # Updates a workspace
  def update(self, workspaceId: int, credentialsId: str, networkId: str, storageConfigurationId: str):
    postData = {
      "credentials_id": credentialsId,
      "network_id": networkId
    }
    if storageConfigurationId is not None:
      postData["storage_customer_managed_key_id"] = storageConfigurationId
    # Issue the API call
    workspaceObject = Workspace(self.__apiSession.patch('/workspaces/' + str(workspaceId), postData))
    # Wait for the workspace to start running
    while True:
      time.sleep(5)
      try:
        workspaceObject = self.get(workspaceId)
        if workspaceObject.status == 'RUNNING': break
      except Exception as e:
        print(str(e))
    return workspaceObject


  # Deletes an existing workspace using its id
  def delete(self, workspaceId: int):
    self.__apiSession.delete('/workspaces/' + str(workspaceId))


  # Retrieves an existing workspace using its id
  def get(self, workspaceId: int):
    return Workspace(self.__apiSession.get('/workspaces/' + str(workspaceId)))


  # Retrieves the list of existing workspaces
  def list(self):
    return [ Workspace(objectData) for objectData in self.__apiSession.get('/workspaces') ]
