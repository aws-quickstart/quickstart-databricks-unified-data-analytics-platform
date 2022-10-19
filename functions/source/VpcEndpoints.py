from AccountApiSession import AccountApiSession

# The vpc endpoint object
class VpcEndpoint:
  def __init__(self, data: dict):
    self.id = data['vpc_endpoint_id']
    self.name = data['vpc_endpoint_name']
    self.awsVpcEnpointId = data['aws_vpc_endpoint_id']
    self.useCase = data['use_case']
    self.awsRegion = data['region']
    self.state = data['state']


# A class to manage the vpc endpoint objects
class VpcEndpointsManager:
  def __init__(self, apiSession: AccountApiSession):
    self.__apiSession = apiSession


  def delete(self, vpcEndpointId: str):
    self.__apiSession.delete('/vpc-endpoints/' + vpcEndpointId)


  def create(self, name: str, awsVpcEndpointId: str, region: str):
    # Register the VPC endpoint
    vpcEndpointObject = None
    postData = {
      "vpc_endpoint_name": name,
      "aws_vpc_endpoint_id": awsVpcEndpointId,
      "region": region
    }
    vpcEndpointObject = VpcEndpoint(self.__apiSession.post('/vpc-endpoints', postData))
    if vpcEndpointObject.state == 'rejected':
      raise Exception('Endpoint rejected when attempting to create it on the Databricks account')
    return vpcEndpointObject


  # Retrieves an existing vpc endpoint using its id
  def get(self, vpcEndpointId: str):
    return VpcEndpoint(self.__apiSession.get('/vpc-endpoints/' + vpcEndpointId))


  # List the existing endpoints
  def list(self):
    return [VpcEndpoint(objectData) for objectData in self.__apiSession.get('/vpc-endpoints')]
