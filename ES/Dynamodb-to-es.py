import boto3
import requests
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
from boto3.dynamodb.conditions import Key, Attr
import json


host = 'search-nycdinsug-cqh3du3evatsfcjdhhhjz24uru.us-east-1.es.amazonaws.com'
region = 'us-east-1'

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

# CUISINE_TYPES = ["indian", "italian", "mediterranean", "french", "japanese", "chinese","spanish", "american", "mexican"]


# Build Elasticsearch index configuration
es = Elasticsearch(
    hosts = [{'host':host, 'port':443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

# Scan the DynamoDB table by boroughs and create index for different boroughs
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('YelpDining')
print('Dining from YelpTable')


pe = "ID, categories, boroughs"

response = table.scan(
    ProjectionExpression=pe
)
print(response)


# 这里有问题，相当于db所有数据全塞给es了？不科学啊
for each_data in response['Items']:
    print(each_data)
    es.index(index="restaurants", doc_type="restaurants", id=each_data['ID'], body=each_data)



# # Just a test for the correctness of ElasticSearch, after testing, delete it.
# dsl = {
#     'query':{
#         "bool":{
#             "must": [
#                 {"match": {"categories": "caribbean"}},
#                 {"match": {"boroughs": "Bronx"}}
#             ]
#         }
#     }
# }
#
# id_list = []
# result = es.search(index='restaurants', doc_type='restaurants', body=dsl)
# # response = json.loads(result, indent=2, ensure_ascii=False)
#
# for each_element in result['hits']['hits']:
#     print(each_element)
#     id = each_element['_source']['ID']
#     id_list.append(id)
# # print(id_list)


