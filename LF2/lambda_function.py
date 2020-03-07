import boto3
import json
import logging
from botocore.vendored import requests
from boto3.dynamodb.conditions import Key, Attr
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth.aws4auth import AWS4Auth
import time


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



def poll_from_queue():
    cuisine = None
    phone_num = None
    location = None
    dining_date = None
    dining_time = None
    num_people = None

    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/584092006642/Chatbot_SQS'
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    message = None

    try:
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        logger.debug('Received and deleted message: %s' % message)
    except KeyError:
        logger.debug("Empty queue")
        return (cuisine, phone_num, location, dining_date, dining_time, num_people)

    if message is None:
        logger.debug("Empty message")
        return (cuisine, phone_num, location, dining_date, dining_time, num_people)

    try:
        cuisine = message["MessageAttributes"]["cuisine"]["StringValue"]
        phone_num = message["MessageAttributes"]["phone"]["StringValue"]
        location = message["MessageAttributes"]["location"]["StringValue"]
        dining_date = message["MessageAttributes"]["date"]["StringValue"]
        dining_time = message["MessageAttributes"]["time"]["StringValue"]
        num_people = message["MessageAttributes"]["peoplenum"]["StringValue"]

    except KeyError:
        logger.debug("No Cuisine or PhoneNum key found in message")
        return (cuisine, phone_num, location, dining_date, dining_time, num_people)

    return (cuisine, phone_num, location, dining_date, dining_time, num_people)



def lambda_handler(event, context):
    cuisine, phone_num, location, dining_date, dining_time, num_people = poll_from_queue()

    print("return from sqs, The information is as follows: ", cuisine, phone_num, location, dining_date, dining_time, num_people)

    # Configuration for ElasticSearch Service
    host = 'search-es-dining-suggestion-gtvtqxsol26hb4gg7olq3pycfy.us-east-1.es.amazonaws.com'
    region = 'us-east-1'

    service = 'es'
    credentials = boto3.Session().get_credentials()
    # awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    # Build Elasticsearch index configuration
    es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        # http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    dsl = {
        'query': {
            "bool": {
                "must": [
                    {"match": {"categories": cuisine}},
                    {"match": {"boroughs": location}}
                ]
            }
        }
    }


    result = es.search(index='restaurants', doc_type='restaurants', body=dsl)

    id_list = []    # id_list store the all the matching ids for our sqs query. Use them to find the db matching data.
    for each_element in result['hits']['hits']:
        # print(each_element)
        id = each_element['_source']['ID']
        id_list.append(id)

    # Only get the first three suggestions
    id_list = id_list[:3]

    # Query DynamoDB to find matching data
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('YelpDining')
    result_list = []
    for each_id in id_list:
        response = table.query(
            KeyConditionExpression=Key('ID').eq(each_id)
        )

        for i in response['Items']:
            result_list.append(i)
    print(result_list)


    # SNS and other services
    response_sns_text = 'Here are my suggestions for {cuisine} food in {location} on {diningDate} at {diningTime} for {numPeople} people: \n'.format(
        cuisine=cuisine,
        location=location,
        diningDate=dining_date,
        diningTime=dining_time,
        numPeople=num_people
    )

    for i, restaurant in enumerate(result_list):
        response_sns_text += str(i + 1) + '.' + restaurant['name'] + '\n'
        response_sns_text += 'address: ' + restaurant['address'] + ', ' + '\n'


    # messagingClient = boto3.client('sns')
    # response = messagingClient.publish(
    #     PhoneNumber=phone_num,
    #     Message=response_sns_text,
    #     MessageStructure='string',
    # )
    # logger.debug("Message '%s' sent to %s" % (response_sns_text, phone_num))
    # return response_sns_text

    sns = boto3.client('sns')
    sns.publish(
        # TopicArn=message['topic'],
        # Subject=message['subject'],
        # Message=message['body']
        TopicArn='arn:aws:sns:us-east-1:584092006642:Mike_ChatBot:93052fcc-b560-41bc-9ada-1afc0e876d60',
        Subject='Yo This is the subject of the message.',
        Message=response_sns_text
    )

    return ('Sent a message to an Amazon SNS topic.')