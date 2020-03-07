# Business Search       URL -- 'https://api.yelp.com/v3/businesses/search'
# Business Match        URL -- 'https://api.yelp.com/v3/businesses/matches'
# Phone Search          URL -- 'https://api.yelp.com/v3/businesses/search/phone'

# Business Details      URL -- 'https://api.yelp.com/v3/businesses/{id}'
# Business Reviewers    URL -- 'https://api.yelp.com/v3/businesses/{id}/reviews'

"""
Crawl Yelp restaurants Data into AWS DynamoDb
"""

# Import the modules
import requests
from yelpapi import YelpAPI
from getAPIKey import getAPIKey
import boto3, json, decimal

# Define the API Key, Define the Endpoint, and define the Header
API_KEY = getAPIKey()
ENDPOINT = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization':'bearer %s' %API_KEY}


# Cuisine list
# CUISINE_TYPES = ["indian", "italian", "mediterranean", "french", "japanese", "chinese","spanish", "american", "mexican"]



Manhattan = \
    ['10026', '10027', '10030', '10037', '10039', '10001', '10011',
     '10018', '10019', '10020', '10036', '10029', '10035', '10010',
     '10016', '10017', '10022', '10012', '10013', '10014', '10004',
     '10005', '10006', '10007', '10038', '10280', '10002', '10003',
     '10009', '10021', '10028', '10044', '10065', '10075', '10128', '10023', '10024', '10025']

Bronx = ['10453' , '10457' , '10460' , '10458' , '10467' , '10468' , '10451' , '10452' , '10456' ,
 '10454' , '10455' , '10459' , '10474' , '10463' , '10471' , '10466' , '10469' , '10470' ,
 '10475' , '10461' , '10462' , '10464' , '10465' , '10472' , '10473']

Brooklyn = ['11212' , '11213' ,'11216' , '11233' , '11238' , '11209' , '11214' ,
 '11228' , '11204' , '11218' , '11219' , '11230' , '11234' , '11236' , '11239' ,
 '11223' , '11224' , '11229' , '11235' , '11201' , '11205' , '11215' , '11217' ,
 '11231' , '11203' , '11210' , '11225' , '11226' , '11207' , '11208' , '11211' ,
 '11222' , '11220' , '11232' , '11206' , '11221' , '11237']

Queens = \
['11361' , '11362' , '11363' , '11364' , '11354' , '11355' , '11356' , '11357' , '11358' ,
 '11359' , '11360' , '11365' , '11366' , '11367' , '11412' , '11423' , '11432' , '11433' ,
 '11434' , '11435' , '11436' , '11101' , '11102' , '11103' , '11104' , '11105' , '11106' ,
 '11374' , '11375' , '11379' , '11385' , '11691' , '11692' , '11693' , '11694' , '11695' ,
 '11697' , '11004' , '11005' , '11411' , '11413' , '11422' , '11426' , '11427' , '11428' ,
 '11429' , '11414' , '11415' , '11416' , '11417' , '11418' , '11419' , '11420' , '11421' ,
 '11368' , '11369' , '11370' , '11372' , '11373' , '11377' , '11378']

Staten_island = \
['10302' , '10303' , '10310' , '10306' , '10307' , '10308' , '10309' , '10312' , '10301' , '10304' , '10305' , '10314']


for each_zipcode in Manhattan:

    # Search PARAMETERS
    PARAMETERS = {'term':'restaurants',
                  'limit':30,
                  'offset':0,   # Here we change each time, from 0 to 'a limit' then 'two limit'
                  'radius':1500,
                  'location':'New York, NY ' + each_zipcode,
                  }

    # Make a request to the yelp API
    response = requests.get(url = ENDPOINT, params= PARAMETERS, headers = HEADERS)

    # Convert the JSON string to a Dictionary
    business_data = response.json()


    # # Filter data, if a business is closed, drop it. Also we verify the zip code is the same of what we search. It reduces duplication.
    # for biz in business_data['businesses']:
    #     if biz['is_closed'] == False and biz['location']['zip_code'] == each_zipcode:
    #         print(biz)
    #         print(biz['id'])
    #
    #         # DETAILS_ENDPOINT = 'https://api.yelp.com/v3/businesses/{}'.format(biz['id'])
    #         # details_response = requests.get(url=DETAILS_ENDPOINT, headers=HEADERS)
    #         # details_data = details_response.json()
    #         # print('The open time is ' + details_data['hours'][0]['open'][0]['start'])
    #         # print('The close time is ' + details_data['hours'][0]['open'][0]['end'])
    #
    #         print("The coordinate is latitude: " + str(biz['coordinates']['latitude']) + ", longtitude: " + str(biz['coordinates']['longitude']))
    #
    #         print("The restaurant Name is " + biz['name'])
    #         # print("The Category is " + str(biz['categories']))  # Here we have to split each category and put them in DB by comma
    #
    #         categories = ""
    #         for each_category in biz['categories']:
    #         #     print("category is " + str(each_category['alias']))
    #             categories = categories + each_category['alias'] + ", "
    #         print(categories[:-2])
    #         print("The review count is " + str(biz['review_count']))
    #         # print("The open time will be " + str(biz['hours']['open'][0]['start']))
    #         print("The rating is " + str(biz['rating']))
    #         print("The location is " + biz['location']['address1'])
    #         print("The zip code is " + biz['location']['zip_code'])
    #         print(biz['phone'])
    #         print("\n\n")



    # Helper class to convert a DynamoDB item to JSON.
    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                if abs(o) % 1 > 0:
                    return float(o)
                else:
                    return int(o)
            return super(DecimalEncoder, self).default(o)

    # # Store the data into DynamoDB
    # dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url='http://localhost:8000') # This is for downloadable version

    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('YelpDining')


    # Store data into table
    for biz in business_data['businesses']:
        if biz['is_closed'] == False and biz['location']['zip_code'] == each_zipcode:
            # Before transfer into Json item, convert the categories attributes
            print(biz)

            # # Find the start and end time of each restaurant
            # DETAILS_ENDPOINT = 'https://api.yelp.com/v3/businesses/{}'.format(biz['id'])
            # details_response = requests.get(url=DETAILS_ENDPOINT, headers=HEADERS)
            # details_data = details_response.json()
            # # print('The open time is ' + details_data['hours'][0]['open'][0]['start'])
            # # print('The close time is ' + details_data['hours'][0]['open'][0]['end'])
            # try:
            #     start_time = str(details_data['hours'][0]['open'][0]['start'])
            #     end_time = str(details_data['hours'][0]['open'][0]['end'])
            # except Exception as e:
            #     print("Unexpected Error: {}".format(e))
            #     break


            categories = ""
            for each_category in biz['categories']:
                categories = categories + each_category['alias'] + ", "


            item={ # After test, add categories
                'ID':str(biz['id']),
                'name':str(biz['name']),
                'categories': str(categories[:-2]),
                'coordinate': str(biz['coordinates']['latitude']) + ", " + str(biz['coordinates']['longitude']),
                'review_count': str(biz['review_count']),
                'rating':str(biz['rating']),
                'address':biz['location']['address1'],
                'zip_code':str(biz['location']['zip_code']),
                'phone':str(biz['phone']),

                # 'start_time': start_time,
                # 'end_time': end_time,

                'boroughs': 'Manhattan',    # For each borough, change the name
            }
            try:
                item_add = table.put_item(Item=item)
                print('PutItem succeeded:')
                print(json.dumps(item_add, indent=4, cls=DecimalEncoder))
            except Exception as e:
                print("Unexpected Error: {}".format(e))
                continue


