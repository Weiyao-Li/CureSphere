import json
import os
import random
import boto3
import time
import uuid
from opensearchpy import OpenSearch, RequestsHttpConnection
from boto3.dynamodb.conditions import Key, Attr
from requests_aws4auth import AWS4Auth
from botocore.vendored import requests
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from datetime import datetime

REGION = 'us-east-1'
HOST = 'search-appointments-ijrmccfpodio2x2fsobemencsu.us-east-1.es.amazonaws.com'
INDEX = 'appointment'


# Add this function to post appointment details to Elasticsearch
def post_to_elastic_search(appointment_details):
    awsauth = get_awsauth(REGION, 'es')
    os_client = OpenSearch(
        hosts=[{'host': HOST, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    os_client.index(index=INDEX, body=appointment_details)


def lambda_handler(event, context):
    print(event)
    # Extracting relevant info from the event
    patientId = event['headers']['patientid']
    doctorId = event['headers']['doctorid']
    timeInput = event['queryStringParameters']['Time']
    date = event['queryStringParameters']['Date']

    timeInput = str(timeInput)
    date = str(date)
    doctorId = str(doctorId)
    patientId = str(patientId)

    # Generate unique appointment ID and timestamp
    appointment_id = str(uuid.uuid4())
    timestamp = int(time.time())

    dynamodb = boto3.resource('dynamodb')

    # Define tables
    doctor_table = dynamodb.Table('doctors')
    patient_table = dynamodb.Table('patients')

    # Query doctor information using the query method
    doctor_response = doctor_table.query(
        KeyConditionExpression=Key('doctor_id').eq(doctorId)
    )

    print("here is", doctor_response)

    doctor = doctor_response['Items'][0]
    doctor_first_name = doctor['firstName']
    doctor_last_name = doctor['lastName']
    doctor_location = doctor['city']
    doctor_email = doctor['email']
    doctor_specialties = doctor['specialties']

    # Query patient information using the query method
    patient_response = patient_table.query(
        KeyConditionExpression=Key('patient_id').eq(patientId)
    )

    print("here is", patient_response)

    patient = patient_response['Items'][0]
    patient_first_name = patient['firstName']
    patient_last_name = patient['lastName']
    patient_location = patient['city']
    patient_email = patient['email']

    # Prepare email content
    email_subject = "Appointment Confirmation"
    email_body = f"Hello {patient_first_name} {patient_last_name},\n\nYou have an appointment with Dr. {doctor_first_name} {doctor_last_name} on {date} at {timeInput}.\n\nDr. {doctor_first_name} {doctor_last_name} specializes in {doctor_specialties} and their office is located at {doctor_location}. You can schedule a meeting with them using the following link: calendly link\n\nBest regards,\nYour Healthcare Team"

    # Send email to patient
    send_email(patient_email, email_subject, email_body)

    # Prepare email content for doctor
    doctor_email_subject = "New Appointment Notification"
    doctor_email_body = f"Hello Dr. {doctor_first_name} {doctor_last_name},\n\nYou have a new appointment with {patient_first_name} {patient_last_name} on {date} at {timeInput}.\n\nPatient Details:\nName: {patient_first_name} {patient_last_name}\nLocation: {patient_location}\nEmail: {patient_email}\n\nBest regards,\nYour Healthcare Team"

    # Send email to doctor
    send_email(doctor_email, doctor_email_subject, doctor_email_body)

    # Prepare appointment details dictionary
    appointment_details = {
        'appointmentId': appointment_id,
        'timestamp': timestamp,
        'doctorId': doctorId,
        'patientId': patientId,
        'date': date,
        'time': timeInput,
        'feedback': "",
        'medicine': ""
    }

    # Post appointment details to Elasticsearch
    post_to_elastic_search(appointment_details)
    
    # Find the matching day and time slot, then update it to 'taken'
    availability_windows = doctor['windows']
    date_obj = datetime.strptime(date, '%m/%d/%Y')
    day_of_week = date_obj.strftime('%A')
    
    for day_dict in availability_windows:
        if day_dict.get(day_of_week) is not None:
            slots = day_dict[day_of_week]
            for slot_obj in slots:
                slot_time, status = list(slot_obj.items())[0]
                if timeInput == slot_time and status == 'free':
                    slot_obj[slot_time] = 'taken'
                    break
    
    # Update the doctor's availability in the original doctor object
    doctor['windows'] = availability_windows
    
    # Update the doctor's availability in DynamoDB
    doctor_table.update_item(
        Key={'doctor_id': doctorId},
        UpdateExpression="SET windows = :windows",
        ExpressionAttributeValues={
            ":windows": doctor['windows']
        }
    )
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': '*',
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

# 1. email to user
# 2. es: send date, time, patientID, docID, timestamp(time), unique appointment id
