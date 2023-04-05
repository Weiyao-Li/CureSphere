import os
import json
import boto3
import uuid
import requests
from datetime import datetime

# Initialize AWS services
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

def lambda_handler(event, context):
    # Get message from SQS
    message = json.loads(event['Records'][0]['body'])

    # Extract appointment details from the message
    doctor_id = message['doctor_id']
    patient_id = message['patient_id']
    appointment_time = message['appointment_time']
    user_email = message['user_email']

    # Integrate with Calendly API
    calendly_api_key = os.environ['CALENDLY_API_KEY']
    headers = {'Authorization': f'Bearer {calendly_api_key}'}
    calendly_url = f'https://api.calendly.com/scheduled_events/{doctor_id}'
    appointment_payload = {
        'start_time': appointment_time,
        'invitees': [{'email': user_email}]
    }
    response = requests.post(calendly_url, json=appointment_payload, headers=headers)
    if response.status_code != 201:
        return {
            'statusCode': response.status_code,
            'body': response.text
        }

    # Create unique appointment ID
    appointment_id = str(uuid.uuid4())

    # Post to both Doctor and Patient DB
    doctor_table = dynamodb.Table('Doctor')
    patient_table = dynamodb.Table('Patient')
    appointment_info = {
        'appointment_id': appointment_id,
        'doctor_id': doctor_id,
        'patient_id': patient_id,
        'appointment_time': appointment_time
    }
    doctor_table.put_item(Item=appointment_info)
    patient_table.put_item(Item=appointment_info)

    # Send appointment confirmed email to user email (SES)
    subject = 'Appointment Confirmation'
    body = f'Dear user,\n\nYour appointment with Doctor {doctor_id} has been confirmed for {appointment_time}.\n\nAppointment ID: {appointment_id}\n\nThank you!'

    ses.send_email(
        Source='noreply@example.com',
        Destination={
            'ToAddresses': [user_email]
        },
        Message={
            'Subject': {
                'Data': subject
            },
            'Body': {
                'Text': {
                    'Data': body
                }
            }
        }
    )

    return {
        'statusCode': 200,
        'body': 'Appointment booked and confirmation email sent.'
    }

    # TODO - integrate with Calendly API

    # TODO - create unique appointment ID

    # TODO - post to both Doc and Patient DB

    # TODO - send appointment confirmed email to user email (SES)