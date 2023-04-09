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
    # Get the personal token from environment variables
    calendly_personal_token = os.environ['eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNjgwODA2ODY5LCJqdGkiOiIzY2VkOTdiZS1iZTFjLTQwMmEtOTQxMi1mZTk3OTg5NGIzMjUiLCJ1c2VyX3V1aWQiOiJhMWMwZmQ5OC1lMGVjLTQ3NmEtOTljOC04ODE4NWIyMzc0YTYifQ.6aUvcvyKcRJ8lVo_SuZ8BgMfpueVWe8YEXMd6Hy1ZqM7kHZ-YaRFSBGaaMIUjEXxvC_KNLMSQ7RPQ4jucWKJ_w']

    # Get message from SQS
    message = json.loads(event['Records'][0]['body'])

    # Extract appointment details from the message
    doctor_id = message['Doctor_ID']
    patient_id = message['Patient_ID']
    location = message['Location']
    specialty = message['Specialty']
    appointment_date = message['Date']
    appointment_time = message['Time']
    user_email = message['Email']

    # Combine date and time for Calendly appointment
    appointment_datetime = f'{appointment_date}T{appointment_time}'

    # Integrate with Calendly API
    headers = {'Authorization': f'Bearer {calendly_personal_token}'}
    calendly_url = f'https://api.calendly.com/scheduled_events/{doctor_id}'
    appointment_payload = {
        'start_time': appointment_datetime,
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
        'location': location,
        'specialty': specialty,
        'appointment_date': appointment_date,
        'appointment_time': appointment_time
    }
    doctor_table.put_item(Item=appointment_info)
    patient_table.put_item(Item=appointment_info)

    # Send appointment confirmed email to user email (SES)
    subject = 'Appointment Confirmation'
    body = f'Dear user,\n\nYour appointment with Doctor {doctor_id} has been confirmed for {appointment_date} at {appointment_time}.\n\nAppointment ID: {appointment_id}\n\nThank you!'

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

    # TODO - post to both Doc and Patient DB and Opensearch appointments

    # TODO - send appointment confirmed email to user email (SES)
