import os
import json
import boto3
import uuid
import requests

# Initialize AWS services
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')


def lambda_handler(event, context):
    # Get the personal token from environment variables
    calendly_personal_token = os.environ[
        'eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNjgwODA2ODY5LCJqdGkiOiIzY2VkOTdiZS1iZTFjLTQwMmEtOTQxMi1mZTk3OTg5NGIzMjUiLCJ1c2VyX3V1aWQiOiJhMWMwZmQ5OC1lMGVjLTQ3NmEtOTljOC04ODE4NWIyMzc0YTYifQ.6aUvcvyKcRJ8lVo_SuZ8BgMfpueVWe8YEXMd6Hy1ZqM7kHZ-YaRFSBGaaMIUjEXxvC_KNLMSQ7RPQ4jucWKJ_w']

    # Get message from SQS
    message = json.loads(event['Records'][0]['body'])

    # Extract appointment details from the message
    doctor_id = message['Doctor_ID']
    patient_id = message['Patient_ID']
    appointment_date = message['Date']
    appointment_time = message['Time']

    # Retrieve doctor and patient information from DynamoDB
    doctor_table = dynamodb.Table('DoctorDB')
    patient_table = dynamodb.Table('PatientDB')

    doctor_response = doctor_table.get_item(Key={'doctor_id': doctor_id})
    patient_response = patient_table.get_item(Key={'patient_id': patient_id})

    doctor = doctor_response['Item']
    patient = patient_response['Item']

    # Extract relevant information from the database
    user_email = patient['email']
    location = doctor['location']
    specialty = doctor['specialty']

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

    # Update Doctor and Patient DB with appointment information
    doctor_table.update_item(
        Key={'doctor_id': doctor_id},
        UpdateExpression='SET appointments = list_append(if_not_exists(appointments, :empty_list), :appointment)',
        ExpressionAttributeValues={':appointment': [appointment_id], ':empty_list': []}
    )

    patient_table.update_item(
        Key={'patient_id': patient_id},
        UpdateExpression='SET appointments = list_append(if_not_exists(appointments, :empty_list), :appointment)',
        ExpressionAttributeValues={':appointment': [appointment_id], ':empty_list': []}
    )

    # Send appointment confirmed email to user email (SES)
    subject = 'Appointment Confirmation'
    body = f'Dear {patient["first_name"]} {patient["last_name"]},\n\nYour appointment with Doctor {doctor["first_name"]} {doctor["last_name"]} ({specialty}) has been confirmed for {appointment_date} at {appointment_time} at {location}.\n\nAppointment ID: {appointment_id}\n\nThank you!'

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
