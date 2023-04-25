import json
import os
import random
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from boto3.dynamodb.conditions import Key, Attr
from requests_aws4auth import AWS4Auth
from botocore.vendored import requests
from botocore.exceptions import ClientError

REGION = 'us-east-1'
HOST = 'search-appointments-ijrmccfpodio2x2fsobemencsu.us-east-1.es.amazonaws.com'
INDEX = 'appointments'


def lambda_handler(event, context):
    # Extracting relevant info from the event
    patientId = event['patientId']
    doctorId = event['doctorId']
    time = event['Time']
    date = event['Date']

    dynamodb = boto3.resource('dynamodb')

    # Define tables
    doctor_table = dynamodb.Table('doctors')
    patient_table = dynamodb.Table('patients')

    # Query doctor information
    doctor_response = doctor_table.get_item(
        Key={
            'doctorId': doctorId
        }
    )

    doctor = doctor_response['Item']
    doctor_first_name = doctor['firstName']
    doctor_last_name = doctor['lastName']
    doctor_location = doctor['location']
    doctor_email = doctor['email']
    doctor_specialties = doctor['specialties']
    doctor_calendly_link = doctor['calendlyLink']

    # Query patient information
    patient_response = patient_table.get_item(
        Key={
            'patientId': patientId
        }
    )

    patient = patient_response['Item']
    patient_first_name = patient['firstName']
    patient_last_name = patient['lastName']
    patient_location = patient['location']
    patient_email = patient['email']

    # Prepare email content
    email_subject = "Appointment Confirmation"
    email_body = f"Hello {patient_first_name} {patient_last_name},\n\nYou have an appointment with Dr. {doctor_first_name} {doctor_last_name} on {date} at {time}.\n\nDr. {doctor_first_name} {doctor_last_name} specializes in {doctor_specialties} and their office is located at {doctor_location}. You can schedule a meeting with them using the following link: {doctor_calendly_link}\n\nBest regards,\nYour Healthcare Team"

    # Send email to patient
    send_email(patient_email, email_subject, email_body)

    # Prepare email content for doctor
    doctor_email_subject = "New Appointment Notification"
    doctor_email_body = f"Hello Dr. {doctor_first_name} {doctor_last_name},\n\nYou have a new appointment with {patient_first_name} {patient_last_name} on {date} at {time}.\n\nPatient Details:\nName: {patient_first_name} {patient_last_name}\nLocation: {patient_location}\nEmail: {patient_email}\n\nBest regards,\nYour Healthcare Team"

    # Send email to doctor
    send_email(doctor_email, doctor_email_subject, doctor_email_body)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps({'message': 'Appointment booked and email sent.'})
    }


def send_email(email, subject, body_text):
    SENDER = "wl2872@columbia.edu"
    RECIPIENT = email
    AWS_REGION = "us-east-1"
    SUBJECT = subject
    BODY_TEXT = (body_text)
    CHARSET = "UTF-8"
    client = boto3.client('ses', region_name=AWS_REGION)

    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )

    # Error Handling
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
