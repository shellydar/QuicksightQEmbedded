import json, boto3, os, re, base64, secrets

def lambda_handler(event, context):
    try:
        def getQuickSightDashboardUrl(awsAccountId, dashboardIdList, dashboardRegion, allowedDomain,TopicID):
            #Create QuickSight client
            quickSight = boto3.client('quicksight', region_name=dashboardRegion);
        
            #Construct dashboardArnList from dashboardIdList
            dashboardArnList=[ 'arn:aws:quicksight:'+dashboardRegion+':'+awsAccountId+':dashboard/'+dashboardId for dashboardId in dashboardIdList]
            dashboardConf={'Dashboard':{'InitialDashboardId':dashboardIdList[0]}}
            QnAconf={'GenerativeQnA': {'InitialTopicId': TopicId}}
            topicArn=['arn:aws:quicksight:'+dashboardRegion+':'+awsAccountId+':topic/'+TopicId]
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
        dashboardIdList = re.sub(' ','',os.environ['DashboardIdList']).split(',')
        dashboardNameList = os.environ['DashboardNameList'].split(',')
        dashboardRegion = os.environ['DashboardRegion']
        TopicId = os.environ['TopicId']
        #You might want to embed QuickSight into static or dynamic pages.
        #We will use this API gateway and Lambda combination to simulate both scenarios.
        #In Dynamic mode, we will generate the embed url from QuickSight and send back an HTML page with that url specified.
        #In Static mode, we will first return static HTML. 
        #This page when loaded at client side will make another API gateway call to get the embed url and will then launch the dashboard.
        #We are handling these interactions by using a query string parameter with three possible values - dynamic, static & getUrl.
        mode='dynamic'
        response={} 
        if event['queryStringParameters'] is None:
            mode='dynamic'
        elif 'mode' in event['queryStringParameters'].keys():
            if event['queryStringParameters']['mode'] in ['static','getUrl']:
                mode=event['queryStringParameters']['mode']
            else:
                mode='unsupportedValue'
        else:
            mode='dynamic'
        
        if event['headers'] is None or event['requestContext'] is None:
            apiGatewayUrl = 'ApiGatewayUrlIsNotDerivableWhileTestingFromApiGateway'
            allowedDomain = 'http://localhost'
        else:
            apiGatewayUrl = event['headers']['Host']+event['requestContext']['path']
            allowedDomain = 'https://'+event['headers']['Host']
            
        #Set the html file to use based on mode. Generate embed url for dynamic and getUrl modes.
        #Also, If mode is static, get the api gateway url from event. 
        #In a truly static use case (like an html page getting served out of S3, S3+CloudFront),this url be hard coded in the html file
        #Deriving this from event and replacing in html file at run time to avoid having to come back to lambda 
        #to specify the api gateway url while you are building this sample in your environment.
        if mode == 'dynamic':
            htmlFile = open('content/QBarSample.html', 'r')
            response = getQuickSightDashboardUrl(awsAccountId, dashboardIdList, dashboardRegion, allowedDomain,TopicId)
        elif mode == 'static':
            htmlFile = open('content/StaticSample.html', 'r')
        elif mode == 'getUrl':
            response = getQuickSightDashboardUrl(awsAccountId, dashboardIdList, dashboardRegion, allowedDomain,TopicId)
    
        if mode in ['dynamic','static']:
            #Read contents of sample html file
            htmlContent = htmlFile.read()        
            scriptNonce = secrets.token_urlsafe();
            #Replace place holders.
            htmlContent = re.sub('<ScriptNonce>', scriptNonce, htmlContent)            
            if mode == 'dynamic':
                #Replace Embed URL placeholder.
                htmlContent = re.sub('<QSEmbedUrl>', response['EmbedUrl'], htmlContent)
            elif mode == 'static':
                #Replace API Gateway url placeholder
                htmlContent = re.sub('<QSApiGatewayUrl>', apiGatewayUrl, htmlContent)
    
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
        else:
            #Return response from generate embed url call.
            #Access-Control-Allow-Origin doesn't come into play in this sample as origin is the API Gateway url itself.
            #When using the static mode wherein initial static HTML is loaded from a different domain, this header becomes relevant.

            return {'statusCode':200,
                    'headers': {"Access-Control-Allow-Origin": "-",
                                "Content-Type":"text/plain"},
                    'body':json.dumps(response)
                    } 


    except Exception as e: #catch all
        return {'statusCode':400,
                'headers': {"Access-Control-Allow-Origin": "-",
                            "Content-Type":"text/plain"},
                'body':json.dumps('Error: ' + str(e))
                }     