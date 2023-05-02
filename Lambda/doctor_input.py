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

    #for testing -> works well!
    # feedback = "updated5/1"
    # medicine = "updated5/1"
    # a_id = "NrAT1IcBAh0ClifDPt_a"
    
    # {"index": {"_index": "appointment", "_id": 1}}
    # {"a_id": "a_id1", "feedback": "fb1", "medicine":"m1", "a_link": "a_link1", "doctor_id": "d1", "patient_id": "p1", "timestamp": 124.344}
    
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
    
    results = client.get(index = INDEX, id = a_id)
    print("before update results", results)
    a_link = results['_source']['a_link']    
    doctor_id = results['_source']['doctor_id']    
    patient_id = results['_source']['patient_id']   
    timestamp = results['_source']['timestamp']   
    
    #1 save the record
    data ={"a_id": a_id, "feedback": feedback, "medicine": medicine, "a_link": a_link, "doctor_id": doctor_id , "patient_id":patient_id, "timestamp":timestamp}
    #2 delete the current record
    res = client.delete(index=INDEX, id=a_id)
    #3 update the record (create new one)
    res = client.index(index=INDEX, id=a_id, body=data)
    print(res)
    
    # bulk_request = ""
    # action = {"index": {"_index": INDEX, "_id": "tmp_id"}}
    # bulk_request += json.dumps(action) + "\n" + json.dumps(data) + "\n"
    # response = client.bulk(body=bulk_request)
    
    # # response = client.update(index=INDEX, id = a_id, body = {'_source':data}) -> not working
    
    
    results = client.get(index = INDEX, id = a_id)
    print("after update results : ", results)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps({'doctor_input_update': res})
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
    q = {'size': 30, 'query': {'multi_match': {'query': term}}}
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
