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


# USERTABLE= 'user_history'
#
# def insert_table(email,data):
#     res = [{'email':email, 'data':data}]
#     db = boto3.resource('dynamodb')
#     table = db.Table(USERTABLE)
#
#     for data in res:
#         response = table.put_item(Item=data)
#     print('@insert_data: response', response)

def lambda_handler(event, context):
    sqs = boto3.client('sqs')
    s_queue_s = sqs.get_queue_url(QueueName='appointments')
    queue_url = s_queue_s['QueueUrl']

    # now getting response from sqs
    response_from_sqs = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
    )
    print(response_from_sqs)

    if response_from_sqs:

        # retrieving relevant info
        patientId = response_from_sqs['Messages'][0]["MessageAttributes"]['patientId']["StringValue"]
        doctorId = response_from_sqs['Messages'][0]["MessageAttributes"]['doctorId']["StringValue"]
        time = response_from_sqs['Messages'][0]["MessageAttributes"]['Time']["StringValue"]
        date = response_from_sqs['Messages'][0]["MessageAttributes"]['Date']["StringValue"]

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


        # recommendBackMessage = []
        # for n in Business_ID_list:
        #     response_from_DB = table.query(
        #         KeyConditionExpression=Key('id').eq(n)
        #     )
        #     recommend_restaurant = response_from_DB['Items'][0]["name"]
        #     recommend_address = response_from_DB['Items'][0]["address"]
        #     recommendBackMessage.append({
        #         "name": recommend_restaurant,
        #         "address": recommend_address
        #     })
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



        # Delete queue info, fifo
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=response_from_sqs['Messages'][0]['ReceiptHandle']
        )

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'results': message_to_user})
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
            'body': json.dumps("SQS queue is now empty")
        }


def query(input):
    q = {'size': 20, 'query': {'multi_match': {'query': input}}}

    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
        http_auth=get_awsauth(REGION, 'es'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection)

    res = client.search(index=INDEX, body=q)
    hits = res['hits']['hits']
    result = []
    while len(result) != 3:
        index = random.randint(0, 19)
        RestaurantID = hits[index]['_source']['id']
        if RestaurantID not in result:
            result.append(RestaurantID)
    return result


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
