import random
import string
import uuid
import cfnresponse

"""
If included in a Cloudformation build as a CustomResource, generate a random string of length
given by the 'length' parameter.
By default the character set used is upper and lowercase ascii letters plus digits.
If the 'punctuation' parameter is specified this also includes punctuation.
"""

def handler(event, context):

    status = cfnresponse.SUCCESS
    responseData = {}

    if event['RequestType'] == 'Delete':
        return cfnresponse.send(event, context, status, responseData, None)

    try:
        length = int(event['ResourceProperties']['Length'])
    except:
        status = cfnresponse.FAILED
        return cfnresponse.send(event, context, status, responseData, None)
    try:
        punctuation = event['ResourceProperties']['Punctuation']
    except KeyError:
        punctuation = False
    try:
        rds_compatible = event['ResourceProperties']['RDSCompatible']
    except KeyError:
        rds_compatible = False
    valid_characters = string.ascii_letters+string.digits
    if punctuation not in [False,'false','False']:
        valid_characters = valid_characters + string.punctuation
    if rds_compatible not in [False,'false','False']:
        valid_characters = valid_characters.translate(None,'@/"')

    random_string = ''.join(random.choice(valid_characters) for i in range(length))
    responseData['RandomString'] = random_string.lower()

    return cfnresponse.send(event, context, status, responseData, None)