#TODO add check parameters, if no headers/query return UNAUTHIRIZED but in log add error  

r'''
    This lambda is responsible for authorizing requests to the S3 bucket.
    It checks if the request has the required headers and query parameters.
    If the headers and query parameters are present, it returns an allow policy.
    Otherwise, it returns a deny policy.
    The request must have the following headers:
        - Header-param: header-value
        - Query: query-value
'''

def lambda_handler(event, context):
    print(event)

    # Retrieve request parameters from the Lambda function input:
    headers = event['headers']
    queryStringParameters = event['queryStringParameters']
    
    if (headers['auth-s3'] == "gandalf-the-white" 
            and queryStringParameters['test-s3'] == "speak-friend-and-enter"):
        response = generatePolicy('Allow', event["methodArn"])
        print('authorized')
        return response
    else:
        print('unauthorized')
        return generatePolicy('Deny', event["methodArn"])


def generatePolicy( effect, resource):
    authResponse = {}
    if (effect and resource):
        policyDocument = {}
        policyDocument['Version'] = '2012-10-17'
        policyDocument['Statement'] = []
        statementOne = {}
        statementOne['Action'] = 'execute-api:Invoke'
        statementOne['Effect'] = effect
        statementOne['Resource'] = resource
        policyDocument['Statement'] = [statementOne]
        authResponse['policyDocument'] = policyDocument

    return authResponse
