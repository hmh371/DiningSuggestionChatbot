from botocore.vendored import requests
import json
import os
import time
import dateutil.parser
import logging
import datetime
import urllib
import sys
import boto3

try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def isvalid_city(city):
    valid_cities = ['new york', 'manhattan', 'brooklyn', ]
    return city.lower() in valid_cities


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def isvalid_cuisine_type(cuisine_type):
    cuisines = ["indian", "italian", "mediterranean", "french", "japanese", "chinese", "spanish", "american", "mexican"]
    return cuisine_type.lower() in cuisines


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_suggest_place(slots):
    v_city = slots['Location']
    v_date = slots['Date']
    v_time = slots['Time']
    v_peoplecount = safe_int(slots['NumberOfPeople'])
    v_cuisine_type = slots['Cuisine']

    if v_city and not isvalid_city(v_city):
        return build_validation_result(
            False,
            'Location',
            'We currently do not support {} as a valid destination.  Can you try a different city?'.format(v_city)
        )

    if v_date:
        if not isvalid_date(v_date):
            return build_validation_result(False, 'Date',
                                           'I did not understand the data you provided. Can you please tell me what date are you planning to go?')
        if datetime.datetime.strptime(v_date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date',
                                           'Suggestions cannot be made for date earlier than today.  Can you try a different date?')

    if v_peoplecount is not None:
        num_people = int(v_peoplecount)
        if num_people > 20 or num_people < 0:
            return build_validation_result(False,
                                           'NumberOfPeople',
                                           'Please add people betweek 0 to 20')

    if v_cuisine_type and not isvalid_cuisine_type(v_cuisine_type):
        return build_validation_result(
            False,
            'Cuisine',
            'I did not recognize that cuisine.  What cuisine would you like to try?  '
            'Popular cuisines are Japanese, Indian, or Italian')

    return {'isValid': True}


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': {'contentType': 'PlainText', 'content': message}
        }
    }

    return response


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


def safe_int(n):
    if n is not None:
        return int(n)
    return n


def diningSuggestions(intent_request):
    location = intent_request['currentIntent']['slots']['Location']
    cuisine = intent_request['currentIntent']['slots']['Cuisine']
    peopleNum = intent_request['currentIntent']['slots']['NumberOfPeople']
    date = intent_request['currentIntent']['slots']['Date']
    time_open = intent_request['currentIntent']['slots']['Time']
    phone = str(intent_request['currentIntent']['slots']['Phone'])

    # cuisine = "chinese"
    # phone_num = "+16263285824"
    # location = "brooklyn"
    # date = "2019-10-17"
    # dining_time = "13:00"
    # peopleNum = "2"

    if phone[:2] != '+1':
        phone = '+1' + phone

    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    if intent_request['invocationSource'] == 'DialogCodeHook':
        validation_result = validate_suggest_place(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            intent_request['currentIntent']['slots'][validation_result['violatedSlot']] = None
            # print(validation_result['message'])
            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                validation_result['violatedSlot'],
                validation_result['message']
            )

        return delegate(session_attributes, intent_request['currentIntent']['slots'])

    sqsmessage = cuisine + ' ' + phone
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/584092006642/Chatbot_SQS'
    # queue_url = 'https://sqs.us-east-1.amazonaws.com/971614317796/chatbotsqs'
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageAttributes={
            'cuisine': {
                'DataType': 'String',
                'StringValue': cuisine
            },
            'phone': {
                'DataType': 'String',
                'StringValue': phone
            },
            'location': {
                'DataType': 'String',
                'StringValue': location
            },
            'peoplenum': {
                'DataType': 'String',
                'StringValue': peopleNum
            },
            'date': {
                'DataType': 'String',
                'StringValue': date
            },
            'time': {
                'DataType': 'String',
                'StringValue': time_open
            }
        },
        MessageBody=(
            sqsmessage
        )
    )

    return close(
        session_attributes,
        'Fulfilled',
        'I have sent my suggestions to the following phone number: \n' + phone
    )


def greeting(intent_request):
    response = {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText',
                'content': 'Yo, how can I help?'}
        }
    }
    return response


def thankyou(intent_request):
    response = {
        'dialogAction': {
            "type": "ElicitIntent",
            'message': {
                'contentType': 'PlainText',
                'content': 'You\'re welcome!'}
        }
    }
    return response


def dispatch(intent_request):
    logger.debug(
        'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return greeting(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thankyou(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return diningSuggestions(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)