from AccountApiSession import AccountApiSession

# Credential Configuration object
class CredentialConfiguration:
  def __init__(self, data: dict):
    self.id = data['credentials_id']
    self.name = data['credentials_name']
    self.roleArn = data['aws_credentials']['sts_role']['role_arn']


# A class to manage credential configuration objects
class CredentialConfigurationsManager:
  def __init__(self, apiSession: AccountApiSession):
    self.__apiSession = apiSession


  # Creates a new credential configuration
  def create(self, name: str, roleArn: str):
    postData = {
      "credentials_name": name,
      "aws_credentials": { 
        "sts_role": {
          "role_arn": roleArn
        }
      }
    }
    return CredentialConfiguration(self.__apiSession.post('/credentials', postData))


  # Deletes an existing credential configuration using its id
  def delete(self, credentialsId: str):
    self.__apiSession.delete('/credentials/' + credentialsId)


  # Retrieves an existing credential configuration using its id
  def get(self, credentialsId: str):
    return CredentialConfiguration(self.__apiSession.get('/credentials/' + credentialsId))


  # Retrieves the list of existing credential configurations
  def list(self):
    return [
      CredentialConfiguration(objectData)
      for objectData in self.__apiSession.get('/credentials')
    ]
