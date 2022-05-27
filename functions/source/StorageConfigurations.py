from AccountApiSession import AccountApiSession

# Storage Configuration object
class StorageConfiguration:
  def __init__(self, data: dict):
    self.id = data['storage_configuration_id']
    self.name = data['storage_configuration_name']
    self.bucket = data['root_bucket_info']['bucket_name']


# A class to manage storage configuration objects
class StorageConfigurationsManager:
  def __init__(self, apiSession: AccountApiSession):
    self.__apiSession = apiSession


  # Creates a new storage configuration
  def create(self, name: str, bucket: str):
    postData = {
      "storage_configuration_name": name,
      "root_bucket_info": { 
        "bucket_name": bucket
      }
    }
    return StorageConfiguration(self.__apiSession.post('/storage-configurations', postData))


  # Deletes an existing storage configuration using its id
  def delete(self, storageConfigurationId: str):
    self.__apiSession.delete('/storage-configurations/' + storageConfigurationId)


  # Retrieves an existing storage configuration using its id
  def get(self, storageConfigurationId: str):
    return StorageConfiguration(self.__apiSession.get('/storage-configurations/' + storageConfigurationId))


  # Retrieves the list of existing storage configurations
  def list(self):
    return [StorageConfiguration(objectData) for objectData in self.__apiSession.get('/storage-configurations')]
