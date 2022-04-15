import urllib3
import json

# Class handling the calls to the Databricks Account REST API
class AccountApiSession:
  # Initializes the session with the account id, user name and password
  def __init__(self, accountId: str, userName: str, password: str):
    self.__baseURL = 'https://accounts.cloud.databricks.com/api/2.0/accounts/' + accountId
    self.__headers = urllib3.util.make_headers(basic_auth = userName + ':' + password) | {'Content-Type': 'application/json'}
    self.__http = urllib3.PoolManager()

  def __treatResponse(self, response: dict, successStatusCodes: list):
    if response.status in successStatusCodes:
      return json.loads(response.data.decode())
    else:
      errorMessage = 'Unknown Error'
      try: errorMessage = json.loads(response.data.decode())['message']
      except: errorMessage = response.reason
      raise Exception(errorMessage)

  # Makes a get call
  def get(self, path: str):
    response = self.__http.request('GET', self.__baseURL + path, headers = self.__headers)
    return self.__treatResponse(response, [200,])

  # Makes a put call
  def put(self, path: str, data: dict):
    response = self.__http.request('PUT', self.__baseURL + path, headers = self.__headers, body = json.dumps(data))
    return self.__treatResponse(response, [200,])

  # Makes a post call
  def post(self, path: str, data: dict):
    response = self.__http.request('POST', self.__baseURL + path, headers = self.__headers, body = json.dumps(data))
    return self.__treatResponse(response, [200, 201])

  # Makes a patch call
  def patch(self, path: str, data: dict):
    response = self.__http.request('PATCH', self.__baseURL + path, headers = self.__headers, body = json.dumps(data))
    return self.__treatResponse(response, [200,])

  # Makes a delete call
  def delete(self, path: str):
    response = self.__http.request('DELETE', self.__baseURL + path, headers = self.__headers)
    return self.__treatResponse(response, [200,])
