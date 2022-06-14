from AccountApiSession import AccountApiSession
from AwsSession import AwsSession
from DatabricksEndpoints import DatabricksEndpoints

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


  def createForRestAccess(self, name: str, region: str, vpcId: str, subnetIds: list, securityGroupIds: list, tags: dict):
    # Get the endpoint service
    databricksEndpoints = DatabricksEndpoints(region)
    endpointService = databricksEndpoints.restaccess
    if endpointService is None:
      raise Exception('Region "' + region + '" is not supported for the REST API VPC endpoint (PrivateLink)')
    return self.__create(name, endpointService, region, vpcId, subnetIds, securityGroupIds, tags)


  def createForRelayAccess(self, name: str, region: str, vpcId: str, subnetIds: list, securityGroupIds: list, tags: dict):
    # Get the endpoint service
    databricksEndpoints = DatabricksEndpoints(region)
    endpointService = databricksEndpoints.relayaccess
    if endpointService is None:
      raise Exception('Region "' + region + '" is not supported for Cluster Relay VPC endpoint (PrivateLink)')
    return self.__create(name, endpointService, region, vpcId, subnetIds, securityGroupIds, tags)


  def delete(self, vpcEndpointId: str):
    # First we need to retrieve the object to obtain the aws endpoint identifier
    endpointObject = self.get(vpcEndpointId)
    awsVpcEndpointId = endpointObject.awsVpcEnpointId
    region = endpointObject.awsRegion
    # Delete the VPC endpoint on AWS
    awsSession = AwsSession(region)
    errorMessage = awsSession.deleteVpcEndpoint(awsVpcEndpointId)
    if errorMessage is not None: raise Exception(errorMessage)
    # Delete the VPC endpoint object from the Databricks account
    errorMessage = self.__deleteEndpointObject(vpcEndpointId)
    if errorMessage is not None: raise Exception(errorMessage)


  def __create(self, name: str, endpointService: str, region: str, vpcId: str, subnetIds: list, securityGroupIds: list, tags: dict):
    # Create the VPC endpoint
    awsSession = AwsSession(region)    
    awsVpcEndpointId = awsSession.createVpcEndpoint(endpointService, vpcId, subnetIds, securityGroupIds, tags)

    # Activate the VPC endpoint
    vpcEndpointObject = None
    errorMessage = None
    try:
      postData = {
        "vpc_endpoint_name": name,
        "aws_vpc_endpoint_id": awsVpcEndpointId,
        "region": region
      }
      vpcEndpointObject = VpcEndpoint(self.__apiSession.post('/vpc-endpoints', postData))
      if vpcEndpointObject.state == 'rejected':
        raise Exception('Endpoint rejected when attempting to create it on the Databricks account')
    except Exception as e:
      errorMessage = str(e)
      # Roll back: delete the VPC endpoint
      _ = awsSession.deleteVpcEndpoint(awsVpcEndpointId)
    if errorMessage is not None: raise Exception(errorMessage)

    # Wait until the endpoint is active
    errorMessage = awsSession.waitForVpcEndpointToBecomeAvailable(awsVpcEndpointId)
    if errorMessage is not None:
      # Roll back: delete the VPC endpoint
      _ = awsSession.deleteVpcEndpoint(awsVpcEndpointId)
      # Delete the endpoint
      _ = self.__deleteEndpointObject(vpcEndpointObject.id)
    if errorMessage is not None: raise Exception(errorMessage)
  
    # Enable DNS (and wait until it becomes available again)
    try:
      awsSession.enableDnsForVpcEndpoint(awsVpcEndpointId)
    except Exception as e:
      errorMessage = str(e)
      # Roll back: delete the VPC endpoint
      _ = awsSession.deleteVpcEndpoint(awsVpcEndpointId)
      # Delete the endpoint
      _ = self.__deleteEndpointObject(vpcEndpointObject.id)
    if errorMessage is not None: raise Exception(errorMessage)

    # All set. Return the object
    return vpcEndpointObject


  # Deletes an endpoint object from the account
  def __deleteEndpointObject(self, endpointId: str):
    try:
      self.__apiSession.delete('/vpc-endpoints/' + endpointId)
      return None
    except Exception as e:
      return str(e)


  # Retrieves an existing vpc endpoint using its id
  def get(self, vpcEndpointId: str):
    return VpcEndpoint(self.__apiSession.get('/vpc-endpoints/' + vpcEndpointId))


  # List the existing endpoints
  def list(self):
    return [VpcEndpoint(objectData) for objectData in self.__apiSession.get('/vpc-endpoints')]
