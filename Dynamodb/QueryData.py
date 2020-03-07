import boto3
import json
import decimal
from boto3.dynamodb.conditions import Key, Attr

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

# dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url='http://localhost:8000') # It is for downloadable version
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

table = dynamodb.Table('YelpDining')

print('Dining from YelpTable')

id_list = ['nnat3QDogbkOGWR00jfPqw', 'BHUYHKdOToyRhg83Vkpd8w', 'tBLMIVOtA6LFtv7PDGj9Wg', 'y3-70vWvjH7TY-XONHijtQ', 'Exlgsnzm5KjkooYE7AH3Uw', 'Mu8MCycvAuCWhCX_E8DSjQ', 'Sd8cNodYP1fmeJ3BA_sTqw', 'Au3yez0bNmImD5beNJzcSQ', 'VowfUbVepyT39PO1NyjRRA']

result_list = []
for each_id in id_list:
    response = table.query(
        KeyConditionExpression=Key('ID').eq('i-pIkOZDCv7UVwFyMO5QlQ')
    )

    for i in response['Items']:
        result_list.append(i)
print(result_list)
