from difflib import context_diff
from AccountApiSession import AccountApiSession

# Log Delivery Configuration class
class LogDeliveryConfiguration:
  def __init__(self, data: dict):
    confData = data['log_delivery_configuration']
    self.id = confData['config_id']
    self.name = confData['config_name']
    self.credentialsId = confData['credentials_id']
    self.storageId = confData['storage_configuration_id']
    self.status = confData['status']
    self.outputFormat = confData['output_format']
    self.logType = confData['log_type']
    self.deliveryPathPrefix = confData['delivery_path_prefix'] if 'delivery_path_prefix' in confData else ''
    self.deliveryStartTime = confData['delivery_start_time'] if 'delivery_start_time' in confData else None


# A manager for log delivery configurations
class LogDeliveryConfigurationManager:
  def __init__(self, apiSession: AccountApiSession):
    self.__apiSession = apiSession

  # Creates a new log delivery configuration object
  def create(self, name: str, logType: str, outputFormat: str, credentialsId: str, storageId: str,
    enabled: bool = True, workspaceIds: list = [], deliveryPathPrefix: str = None, deliveryStartTime: str = None):
    postData = {
      "config_name": name,
      'status': 'ENABLED' if enabled else 'DISABLED',
      'log_type': logType,
      'output_format': outputFormat,
      'credentials_id': credentialsId,
      'storage_configuration_id': storageId
    }
    if len(workspaceIds)>0: postData['workspace_ids_filter'] = workspaceIds
    if deliveryPathPrefix is not None: postData['delivery_path_prefix'] = deliveryPathPrefix
    if deliveryStartTime is not None: postData['delivery_start_time'] = deliveryStartTime

    return LogDeliveryConfiguration(self.__apiSession.post('/log-delivery', postData))


  # Enables or Disables log delivery
  def enableDelivery(self, configId: str, enabled: bool):
    patchData = {
      'status': 'ENABLED' if enabled else 'DISABLED'
    }
    return LogDeliveryConfiguration(self.__apiSession.patch('/log-delivery/' + configId, patchData))


  # Deletes an existing log delivery configuration using its id
  def delete(self, configId: str):
    self.__apiSession.delete('/log-delivery/' + configId)


  # Retrieves an existing log delivery configuration using its id
  def get(self, configId: str):
    return LogDeliveryConfiguration(self.__apiSession.get('/log-delivery/' + configId))


  # Retrieves the list of existing log delivery configurations
  def list(self):
    return [ LogDeliveryConfiguration(objectData) for objectData in self.__apiSession.get('/log-delivery') ]
