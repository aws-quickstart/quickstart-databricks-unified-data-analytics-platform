import boto3
import time

# A class to wrap the AWS API
class AwsSession:
  def __init__(self, region: str):
    self.__ec2Client = boto3.session.Session(region_name=region).client('ec2')


  # Creates a VPC endpoint for a given service
  def createVpcEndpoint(self, endpointService: str, vpcId: str, subnetIds: list, securityGroupIds: list, tags: dict):
    tagList = [{"Key": k, "Value": tags[k]} for k in tags]
    vpcEndpointData = self.__ec2Client.create_vpc_endpoint(
      VpcEndpointType = 'Interface',
      VpcId = vpcId,
      ServiceName = endpointService,
      SubnetIds = subnetIds,
      SecurityGroupIds = securityGroupIds,
      TagSpecifications=[
        {
          "ResourceType": "vpc-endpoint",
          "Tags": tagList
        }
      ]
    )
    if 'VpcEndpoint' not in vpcEndpointData or 'VpcEndpointId' not in vpcEndpointData['VpcEndpoint']:
      raise Exception('Could not create a VPC endpoint')
    return vpcEndpointData['VpcEndpoint']['VpcEndpointId']


  # Deletes a VPC endpoint
  def deleteVpcEndpoint(self, vpcEndpointId: str):
    deleted = False
    try:
      self.__ec2Client.delete_vpc_endpoints(VpcEndpointIds = [vpcEndpointId])
      deleted = True
    except Exception as e:
      return str(e)
    if deleted:
      while True:
        try:
          _ = self.__ec2Client.describe_vpc_endpoints(Filters=[{'Name':'vpc-endpoint-id', 'Values': [vpcEndpointId]}])['VpcEndpoints'][0]['State']
          time.sleep(5)
        except Exception as e: break
    return None


  # Enables DNS of a VPC endpoint
  def enableDnsForVpcEndpoint(self, vpcEndpointId: str):
    self.__ec2Client.modify_vpc_endpoint(VpcEndpointId=vpcEndpointId, PrivateDnsEnabled=True)
    errorMessage = self.waitForVpcEndpointToBecomeAvailable(vpcEndpointId)
    if errorMessage is not None:
      raise Exception(errorMessage)


  # Waits until an endpoint becomes active
  def waitForVpcEndpointToBecomeAvailable(self, vpcEndpointId: str):
    while True: # Wait for the endpoint to become available
      try:
        if self.__ec2Client.describe_vpc_endpoints(
          Filters=[{
            'Name':'vpc-endpoint-id',
            'Values': [vpcEndpointId]
          }])['VpcEndpoints'][0]['State'] == 'available':
          return None
      except Exception as e:
        return str(e)
      time.sleep(5)
