import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import time

REGION = 'us-east-1'
HOST = 'search-appointments-ijrmccfpodio2x2fsobemencsu.us-east-1.es.amazonaws.com'
INDEX = 'appointment'

def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event))
    
    feedback = event["feedback"]
    medicine = event["medicine"]
    a_id = event['a_id']
    # a_id = "a_id3"
    
    #feed_back
    # {"index": {"_index": "appointment", "_id": 1}}
    # {"a_id": "a_id1", "feedback": "fb1", "medicine":"m1", "a_link": "a_link1", "doctor_id": , "patient_id": }
    
    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)
                        
                        
    # mapping = client.indices.get_mapping(index=INDEX)
    # print(mapping)
    
    results = query(a_id)
    a_link = results[0]['a_link']    
    doctor_id = results[0]['doctor_id']    
    patient_id = results[0]['patient_id']    
    
    data ={"a_id": a_id, "feedback": feedback, "medicine": medicine, "a_link": a_link, "doctor_id": doctor_id , "patient_id":patient_id, "timestamp":time.time() }
            
    bulk_request = ""
    action = {"index": {"_index": INDEX, "_id": a_id}}
    bulk_request += json.dumps(action) + "\n" + json.dumps(data) + "\n"
        
    response = client.bulk(body=bulk_request)
    print(response)
    # #post("aaa", 'a_id_test1')
    
    results = query('a_id3') #appointment id #for testing
    
    print("results : ", results)
    #results -> [{'a_id': 'a_id1', 'feedback': 'fb1', 'medicine': 'm1', 'a_link': 'a_link1'}]
    a_link = results[0]['a_link']
    print("appointment_link", results[0]['a_link'])
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps({'appointment_link': a_link})
    }
    
def post(document, key):
    awsauth = get_awsauth(REGION, 'es')
    client = boto3.client('opensearch')
    host = client.describe_domain(DomainName=INDEX)['DomainStatus']['Endpoint']

    es_client = OpenSearch(hosts=[{
        'host': host,
        'port': 443
    }],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection)

    index_name = INDEX
    index_body = {
        'settings': {
            'index': {
                'number_of_shards': 1
            }
        }
    }

    res = es_client.index(index=INDEX, id=key, body=document)
    print(res)
    print(es_client.get(index=INDEX, id=key))

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
