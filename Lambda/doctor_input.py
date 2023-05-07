import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from datetime import datetime
import time

REGION = 'us-east-1'
HOST = 'search-appointments-ijrmccfpodio2x2fsobemencsu.us-east-1.es.amazonaws.com'
INDEX = 'appointment'

def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event))
    
    #3 input : a_id, feedback, medicine (all string)
    feedback = event['headers']["feedback"]
    medicine = event['headers']["medicine"]
    a_id = event['headers']['a_id']

    #for testing -> works well!
    # feedback = "updated5/1"
    # medicine = "updated5/1"
    # a_id = "NrAT1IcBAh0ClifDPt_a"
    
    # {"index": {"_index": "appointment", "_id": 1}}
    # {"a_id": "a_id1", "feedback": "fb1", "medicine":"m1", "a_link": "a_link1", "doctor_id": "d1", "patient_id": "p1", "timestamp": 124.344}
    
    # updated
    # {'appointmentId': appointment_id, 'doctorId': doctorId, 'patientId': patientId, 'date': date, 'time': time, 'timestamp':timestamp}

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
    print("before update results", results[0])
    appointmentId = results[0]['appointmentId'] #should be same with a_id   
    doctorId = results[0]['doctorId']    
    patientId = results[0]['patientId']   
    date = results[0]['date']  
    time = results[0]['time']
    timestamp = results[0]['timestamp']
    
    #results = client.get(index = INDEX, id = a_id)
    # a_link = results['_source']['a_link']    
    # doctor_id = results['_source']['doctor_id']    
    # patient_id = results['_source']['patient_id']   
    # timestamp = results['_source']['timestamp']   
    
    #1 save the record
    data = {'appointmentId': appointmentId, 'doctorId': doctorId, 'patientId': patientId, 'date': date, 'time': time, "feedback": feedback, "medicine": medicine, 'timestamp':timestamp}
    #data ={"a_id": a_id, "feedback": feedback, "medicine": medicine, "a_link": a_link, "doctor_id": doctor_id , "patient_id":patient_id, "timestamp":timestamp}
    
    #2 delete the current record
    #TODO testing: get _id of the result
    r_id = query_id(a_id)
    r_id = r_id[0]
    print(r_id)
    res = client.delete(index=INDEX, id=r_id)
    #3 update the record (create new one)
    res = client.index(index=INDEX, id=r_id, body=data)
    print(res)
    
    # bulk_request = ""
    # action = {"index": {"_index": INDEX, "_id": "tmp_id"}}
    # bulk_request += json.dumps(action) + "\n" + json.dumps(data) + "\n"
    # response = client.bulk(body=bulk_request)
    
    # # response = client.update(index=INDEX, id = a_id, body = {'_source':data}) -> not working
    
    
    results = client.get(index = INDEX, id = r_id)
    print("after update results : ", results)
    
    update_doctor_slot_to_free(doctorId, date, time)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': '*',
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
    
def query_id(term):
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
        results.append(hit['_id'])
    return results

def update_doctor_slot_to_free(doctor_id, date, time):
    dynamodb = boto3.resource('dynamodb')
    doctors_table = dynamodb.Table('doctors')
    
    date_obj = datetime.strptime(date, '%m/%d/%Y')
    day_for_date = date_obj.strftime('%A')
    
    response = doctors_table.get_item(Key={'doctor_id': doctor_id})
    doctor = response['Item']
    availability_windows = doctor['windows']
    
    for day_dict in availability_windows:
        if day_for_date in day_dict:
            for slot in day_dict[day_for_date]:
                if time in slot:
                    slot[time] = 'free'
                    break
    
    update_expression = 'SET windows = :windows'
    expression_attribute_values = {':windows': availability_windows}
    
    doctors_table.update_item(
        Key={'doctor_id': doctor_id},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
