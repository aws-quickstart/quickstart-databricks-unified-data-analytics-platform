from BaseDatabricksApiSession import BaseDatabricksApiSession
from urllib3.util import make_headers

# Class handling the calls to the Databricks Account REST API
class WorkspaceApiSession(BaseDatabricksApiSession):

  # Initializes the session with the workspace deployment name, user name and password
  def __init__(self, workspaceDeploymentName: str, userName: str, password: str, userAgent: str = None):
    baseURL = 'https://' + workspaceDeploymentName + '.cloud.databricks.com/api/2.0'
    headers = make_headers(basic_auth = userName + ':' + password) | {'Content-Type': 'application/json'}
    if userAgent is not None:
      headers['User-Agent'] = userAgent
    super().__init__(baseURL, headers)
