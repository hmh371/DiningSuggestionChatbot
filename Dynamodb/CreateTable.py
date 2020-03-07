import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

table = dynamodb.create_table(
    TableName='YelpDining',
    KeySchema=[
        {
            'AttributeName':'ID',
            'KeyType':'HASH'    # Partition key
        }
    ],
    AttributeDefinitions=[
        {
            'AttributeName':'ID',
            'AttributeType':'S'
        }
    ],
    ProvisionedThroughput={
        'ReadCapacityUnits': 10,
        'WriteCapacityUnits': 10
    }
)

print("Table status", table.table_status)