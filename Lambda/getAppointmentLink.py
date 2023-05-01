import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
HOST = 'search-appointments-ijrmccfpodio2x2fsobemencsu.us-east-1.es.amazonaws.com'
INDEX = 'appointment'

def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event))
    # -> input : appointment ID, past or current
    # -> output : past/current record (entire one, not just the link)
    
    # appointment ID is obtained from DB based on input event - 
    # 1) doctor/patient role, 2) email address (which is doctor_id/patient_id, PK of table)
    
    role = event["role"]
    email = event["email"]
    print(role, email)
    #role = "doctor"
    #email = "hameed.arshad@gmail.com"


    #get appointment_id from doctorDB or patientDB using email(key)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(role+'s') #db name : doctors, patients
    filter = Key(role+"_id").eq(email)
    result = table.scan(FilterExpression=filter)
    print("result:", result)
    
    appointment_id = result['Items'][0]['appointment_id']
    print("appointment_id from dynamodb:", appointment_id)
    
    #appointment_id = event['appointment_id']
    appointment_type = event['is_current'] #"curr" for current appointment, "past" for past appointments
    
    result_current = []
    results_past = []
    
    most_recent_timestamp = None
    results = query(appointment_id)
    for result in results:
        if most_recent_timestamp is None or most_recent_timestamp < result['timestamp']:
            result_current = [result]
            most_recent_timestamp = result['timestamp']
            
    for result in results:
        if result['timestamp'] != most_recent_timestamp:
            results_past.append(result)
            
            
    if appointment_type == "curr":
        return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            },
        'body': json.dumps({'current_appointment': result_current})
        }
    elif appointment_type == "past":
        return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            },
        'body': json.dumps({'past_appointments': results_past})
        }
    else:
        return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            },
        'body': json.dumps({'wrong input for appointment type'})
        }
        
    
    # #results = query('a_id3') #appointment id #for testing
    # print("results : ", results)
    # #results -> [{'a_id': 'a_id1', 'feedback': 'fb1', 'medicine': 'm1', 'a_link': 'a_link1'}]
    # a_link = results[0]['a_link']
    # print("appointment_link", results[0]['a_link'])
    # return {
    #     'statusCode': 200,
    #     'headers': {
    #         'Content-Type': 'application/json',
    #         'Access-Control-Allow-Headers': 'Content-Type',
    #         'Access-Control-Allow-Origin': '*',
    #         'Access-Control-Allow-Methods': '*',
    #     },
    #     'body': json.dumps({'appointment_link': a_link})
    # }

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
