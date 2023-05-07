import json
import boto3
import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    try:
        dynamodb = boto3.resource('dynamodb')
        patientId = event['pathParameters']['id']
        patient_table = dynamodb.Table('patients')

        patient_response = patient_table.query(
            KeyConditionExpression=Key('patient_id').eq(patientId)
        )

        patient = patient_response['Items'][0]
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'Patient': patient})
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'Patient': f"Error: {e}"})
        }
