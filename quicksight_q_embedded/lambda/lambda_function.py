import json, boto3, os, re, base64, secrets

def lambda_handler(event, context):
    try:
        def getQuickSightDashboardUrl(awsAccountId, region, allowedDomain,TopicID):
            #Create QuickSight client
            quickSight = boto3.client('quicksight', region_name=region);
            QnAconf={'GenerativeQnA': {'InitialTopicId': TopicId}}
            topicArn=['arn:aws:quicksight:'+region+':'+awsAccountId+':topic/'+TopicId]
            #Generate Anonymous Embed url
            #Billing for anonymous embedding can be associated to a particular namespace. For our sample, we will pass in the default namespace.
            #ISVs who desire to track this at customer level can pass in the relevant customer namespace instead of default.
            response = quickSight.generate_embed_url_for_anonymous_user(
                     AwsAccountId = awsAccountId,
                     Namespace = 'default',
                     ExperienceConfiguration = QnAconf,
                     AuthorizedResourceArns = topicArn,
                     AllowedDomains = [allowedDomain],
                     SessionLifetimeInMinutes = 60
                 )
            return response

        #Get AWS Account Id
        awsAccountId = context.invoked_function_arn.split(':')[4]
    
        #Read in the environment variables
        region = os.environ['DashboardRegion']
        TopicId = os.environ['TopicId']
   
        
        if event['headers'] is None or event['requestContext'] is None:
            apiGatewayUrl = 'ApiGatewayUrlIsNotDerivableWhileTestingFromApiGateway'
            allowedDomain = 'http://localhost'
        else:
            apiGatewayUrl = event['headers']['Host']+event['requestContext']['path']
            allowedDomain = 'https://'+event['headers']['Host']
            
        #Set the html file to use based on mode. Generate embed url 
        htmlFile = open('content/QBarSample.html', 'r')
        response = getQuickSightDashboardUrl(awsAccountId, region, allowedDomain,TopicId)

        #Read contents of sample html file
        htmlContent = htmlFile.read()        
        scriptNonce = secrets.token_urlsafe();
        #Replace place holders.
        htmlContent = re.sub('<ScriptNonce>', scriptNonce, htmlContent)            
        #Replace Embed URL placeholder.
        htmlContent = re.sub('<QSEmbedUrl>', response['EmbedUrl'], htmlContent)

    
            #Return HTML. 
        return {'statusCode':200,
                'headers': {
                                "Content-Security-Policy":"default-src 'self' ;\
                                    upgrade-insecure-requests;\
                                    script-src 'self' \
                                    'unsafe-inline' \
                                    https://unpkg.com/amazon-quicksight-embedding-sdk@2.8.0/dist/quicksight-embedding-js-sdk.min.js\
                                    https://code.jquery.com/jquery-3.5.1.min.js\
                                    https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js;\
                                    style-src  'unsafe-inline' \
                                    https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css;\
                                    child-src 'self' blob: https://*.quicksight.aws.amazon.com/ ;\
                                    img-src 'self' data: ;\
                                    base-uri 'self';\
                                    object-src 'self';\
                                    frame-ancestors 'self' ",
                                "Content-Type":"text/html"
                },
                'body':htmlContent
                }



    except Exception as e: #catch all
        return {'statusCode':400,
                'headers': {"Access-Control-Allow-Origin": "-",
                            "Content-Type":"text/plain"},
                'body':json.dumps('Error: ' + str(e))
                }     