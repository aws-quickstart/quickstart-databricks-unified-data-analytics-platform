from AccountApiSession import AccountApiSession
import hipaa
import json

# The workspace manager
class WorkspaceManager:
  def __init__(self, apiSession: AccountApiSession, deploymentName: str):
    self.__workspaceApiSession = apiSession.workspaceApiSession(deploymentName)


  # Adds a HIPAA cluster policy
  def addHipaaClusterPolicy(self):
    postData = {
      "name": "Default Cluster Policy (HIPAA)",
      "definition": json.dumps(hipaa.clusterPolicy)
    }
    response = self.__workspaceApiSession.post('/policies/clusters/create', postData)
    return response['policy_id']

  # Registers an instance profile
  def addInstanceProfile(self, instanceProfileArn: str, registerForSQL: bool = False):
    postData = {"instance_profile_arn": instanceProfileArn}
    _ = self.__workspaceApiSession.post('/instance-profiles/add', postData)

    if registerForSQL:
      configData = self.__workspaceApiSession.get('/sql/config/warehouses')
      configData["instance_profile_arn"] = instanceProfileArn
      _ = self.__workspaceApiSession.put('/sql/config/warehouses', configData)
  
    return instanceProfileArn
  
  # Creates a starter cluster
  def createStarterCluster(self, instanceProfileArn: str = None, policyId: str = None):
    clusterData = {
      "cluster_name": "[default]basic-starter-cluster",
      "spark_version": "13.3.x-scala2.12",
      "runtime_engine": "PHOTON",
      "node_type_id": "m5d.large",
      "num_workers": 0,
      "start_cluster": True,
      "autotermination_minutes": 15,
      "spark_conf": {
          "spark.databricks.cluster.profile": "singleNode",
          "spark.master": "local[*]"
      },
      "custom_tags": {
          "ResourceClass": "SingleNode",
          "DatabricksDefault": True,
          "Origin": "AWSQuickstartCloudformationLambda"
      }
    }
    if instanceProfileArn is not None:
      clusterData['aws_attributes'] = { "instance_profile_arn": instanceProfileArn }
    if policyId is not None: clusterData['policy_id'] = policyId
    response = self.__workspaceApiSession.post('/clusters/create', clusterData)
    return response['cluster_id']

  # Terminates a cluster
  def terminateCluster(self, clusterId: str):
    _ = self.__workspaceApiSession.post('/clusters/permanent-delete', { "cluster_id": clusterId })
