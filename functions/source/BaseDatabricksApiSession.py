from urllib3 import PoolManager
import json

# Class handling the calls to the Databricks REST API
class BaseDatabricksApiSession:
  # Initializes the session with the base url and the standard headers
  def __init__(self, baseUrl: str, headers: dict):
    self.__baseURL = baseUrl
    self.__headers = headers
    self.__http = PoolManager()

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
