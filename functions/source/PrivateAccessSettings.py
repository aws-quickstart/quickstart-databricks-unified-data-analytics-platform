from AccountApiSession import AccountApiSession

# Private Access Settings Configuration
class PrivateAccessSettingsConfiguration:
  def __init__(self, data: dict):
    self.id = data['private_access_settings_id']
    self.name = data['private_access_settings_name']
    self.publicAccessEnabled = data['public_access_enabled']
    self.privateAccessLevel = data['private_access_level'] if 'private_access_level' in data else 'ANY'
    self.allowedVpcEndpointIds = data['allowed_vpc_endpoint_ids'] if 'allowed_vpc_endpoint_ids' in data else []


class PrivateAccessSettingsManager:
  def __init__(self, apiSession: AccountApiSession):
    self.__apiSession = apiSession


  # Creates a new settings object
  def create(self, name: str, region: str, publicAccessEnabled: bool, privateAccessLevel: str, allowedVpcEndpointIds: list):
    postData = {
      "private_access_settings_name": name,
      "region": region,
      "public_access_enabled": publicAccessEnabled,
      "private_access_level": privateAccessLevel,
      "allowed_vpc_endpoint_ids": allowedVpcEndpointIds
    }
    return PrivateAccessSettingsConfiguration(self.__apiSession.post('/private-access-settings', postData))


  # Updates a settings object
  def update(self, settingsId: str, name: str, region: str, publicAccessEnabled: bool, privateAccessLevel: str, allowedVpcEndpointIds: list):
    putData = {
      "private_access_settings_name": name,
      "region": region,
      "public_access_enabled": publicAccessEnabled,
      "private_access_level": privateAccessLevel,
      "allowed_vpc_endpoint_ids": allowedVpcEndpointIds
    }
    return PrivateAccessSettingsConfiguration(self.__apiSession.put('/private-access-settings/' + settingsId, putData))


  # Deletes an existing private access settings object using its id
  def delete(self, settingsId: str):
    self.__apiSession.delete('/private-access-settings/' + settingsId)


  # Retrieves an existing private access settings object using its id
  def get(self, settingsId: str):
    return PrivateAccessSettingsConfiguration(self.__apiSession.get('/private-access-settings/' + settingsId))


  # Retrieves the list of existing private access settings objects
  def list(self):
    return [ PrivateAccessSettingsConfiguration(objectData) for objectData in self.__apiSession.get('/private-access-settings') ]
