from BaseDatabricksApiSession import BaseDatabricksApiSession
from WorkspaceApiSession import WorkspaceApiSession
from urllib3.util import make_headers

# Class handling the calls to the Databricks Account REST API
class AccountApiSession(BaseDatabricksApiSession):

  # Initializes the session with the account id, user name and password
  def __init__(self, accountId: str, userName: str, password: str, userAgent: str = None):
    baseURL = 'https://accounts.cloud.databricks.com/api/2.0/accounts/' + accountId
    self.__userName = userName
    self.__password = password
    headers = make_headers(basic_auth = self.__userName + ':' + self.__password)
    headers['Content-Type'] = 'application/json'
    self.__userAgent = userAgent
    if userAgent is not None:
      headers['User-Agent'] = userAgent
    super().__init__(baseURL, headers)

  # Creates a session for a deployed workspace using the same credentials
  def workspaceApiSession(self, deploymentName: str):
    return WorkspaceApiSession(deploymentName, self.__userName, self.__password, self.__userAgent)
