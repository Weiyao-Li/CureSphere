import boto3
import json

def lambda_handler(event, context):
    # Get the username and password from the event
    username = event['headers']['username']
    password = event['headers']['password']

    # Create a DynamoDB client
    dynamodb = boto3.resource('dynamodb')

    # Check for the username and password match in the patientsDB and doctorsDB
    try:
        patient_result = search_user_in_db(username, 'patients', dynamodb)
        doctor_result = search_user_in_db(username, 'doctors', dynamodb)

        if patient_result and patient_result['password'] == password:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*',
                },
                'body': json.dumps({'result': 'patient'})
            }
        elif doctor_result and doctor_result['password'] == password:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*',
            },
                'body': json.dumps({'result': 'doctor'})
            }
        else:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*',
            },
                'body': json.dumps({'error': 'Invalid username or password'})
            }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'error': 'An error occurred while checking credentials'})
        }

def search_user_in_db(username, table_name, dynamodb):
    table = dynamodb.Table(table_name)
    if table_name == 'patients':
        response = table.get_item(Key={'patient_id': username})
    if table_name == 'doctors':
        response = table.get_item(Key={'doctor_id': username})

    if 'Item' in response:
        return response['Item']
    else:
        return None
