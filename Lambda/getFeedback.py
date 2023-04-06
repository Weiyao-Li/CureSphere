import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
HOST = 'search-appointments-whwmhyoyfbzboqplkkjwxnecxq.us-east-1.es.amazonaws.com'
INDEX = 'appointment'

def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event))
    results = query('a_id1') #appointment id
    #results -> [{'a_id': 'a_id1', 'feedback': 'fb1', 'medicine': 'm1', 'a_link': 'a_link1'}]
    a_fb = results[0]['feedback']
    print("feedback", results[0]['feedback'])
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps({'feedback': a_fb})
    }

def query(term):
    q = {'size': 5, 'query': {'multi_match': {'query': term}}}
    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)
    res = client.search(index=INDEX, body=q)
    print(res)
    hits = res['hits']['hits']
    results = []
    for hit in hits:
        results.append(hit['_source'])
    return results

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)