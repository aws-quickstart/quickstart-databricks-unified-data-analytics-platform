from AccountApiSession import AccountApiSession


class ManagedKeysConfiguration:
  def __init__(self, data: dict):
    self.id = data['customer_managed_key_id']
    self.keyArn = data['aws_key_info']['key_arn']
    self.keyAlias = data['aws_key_info']['key_alias'] if 'key_alias' in data['aws_key_info'] else None
    self.resuseKeyForClusterVolumes = data['aws_key_info']['reuse_key_for_cluster_volumes'] if 'reuse_key_for_cluster_volumes' in data['aws_key_info'] else None
    self.useCases = data['use_cases']
    if 'STORAGE' in self.useCases and self.resuseKeyForClusterVolumes is None:
      self.resuseKeyForClusterVolumes = True


class ManagedKeysConfigurationsManager:
  def __init__(self, apiSession: AccountApiSession):
    self.__apiSession = apiSession
  

  # Creates a new managed key configuration object
  def create(self, keyArn: str, keyAlias: str, useCases: list, reuseKeyForClusterVolumes: bool):
    postData = {
      "aws_key_info": { "key_arn": keyArn },
      "use_cases": useCases
    }
    if keyAlias is not None:
      postData['aws_key_info']['key_alias'] = keyAlias
    if reuseKeyForClusterVolumes is not None and 'STORAGE' in useCases:
      postData['aws_key_info']['reuse_key_for_cluster_volumes'] = reuseKeyForClusterVolumes
    return ManagedKeysConfiguration(self.__apiSession.post('/customer-managed-keys', postData))


  # Deletes an existing managed keys configuration using its id
  def delete(self, managedKeyId: str):
    self.__apiSession.delete('/customer-managed-keys/' + managedKeyId)


  # Retrieves an existing managed keys configuration using its id
  def get(self, managedKeyId: str):
    return ManagedKeysConfiguration(self.__apiSession.get('/customer-managed-keys/' + managedKeyId))


  # Retrieves the list of existing managed keys configurations
  def list(self):
    return [ ManagedKeysConfiguration(objectData) for objectData in self.__apiSession.get('/customer-managed-keys') ]
