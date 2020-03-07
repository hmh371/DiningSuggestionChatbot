import json
import boto3

def lambda_handler(event, context):
    print(event['messages'][0]['unstructured']['text'])

    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='mike_ChatBot_Lex',
        botAlias='$LATEST',
        userId=event['messages'][0]['unstructured']['id'],
        sessionAttributes={},
        requestAttributes={},
        inputText=event['messages'][0]['unstructured']['text']
    )
    print(response['message'])
    return{"messages": [{
      "type": "string",
      "unstructured": {
        "id": event['messages'][0]['unstructured']['id'],
        "text": response['message'],
        "timestamp": "string"
      }
    }
  ]
    

}