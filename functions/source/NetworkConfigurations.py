from AccountApiSession import AccountApiSession

# Network configuration object
class NetworkConfiguration:
  def __init__(self, data: dict):
    self.id = data['network_id']
    self.name = data['network_name']
    self.vpcId = data['vpc_id']
    self.subnetIds = data['subnet_ids']
    self.securityGroupIds = data['security_group_ids']
    self.status = data['vpc_status']
    self.restApiEndpointId = data['vpc_endpoints']['rest_api'][0] if 'vpc_endpoints' in data and 'rest_api' in data['vpc_endpoints'] and len(data['vpc_endpoints']['rest_api']) > 0 else None
    self.relayEndpointId = data['vpc_endpoints']['dataplane_relay'][0] if 'vpc_endpoints' in data and 'dataplane_relay' in data['vpc_endpoints'] and len(data['vpc_endpoints']['dataplane_relay']) > 0 else None


# A class to manage the network configuration objects
class NetworkConfiguratiosnManager:
  def __init__(self, apiSession: AccountApiSession):
    self.__apiSession = apiSession


  # Creates a network object
  def create(self, name: str, vpcId: str, subnetIds: list, securityGroupIds: list, restAccessEndpointId: str, relayAccessEndpointId: str):
    postData = {
      "network_name": name,
      "vpc_id": vpcId,
      "subnet_ids": subnetIds,
      "security_group_ids": securityGroupIds
    }
    if restAccessEndpointId is not None and relayAccessEndpointId is not None:
      postData["vpc_endpoints"] = {
        "rest_api": [ restAccessEndpointId ],
        "dataplane_relay": [ relayAccessEndpointId ]
      }
    return NetworkConfiguration(self.__apiSession.post('/networks', postData))


  # Deletes an existing network configuration using its id
  def delete(self, networkId: str):
    self.__apiSession.delete('/networks/' + networkId)


  # Retrieves an existing network configuration using its id
  def get(self, networkId: str):
    return NetworkConfiguration(self.__apiSession.get('/networks/' + networkId))


  # Retrieves the list of existing network configurations
  def list(self):
    return [ NetworkConfiguration(objectData) for objectData in self.__apiSession.get('/networks') ]
