import json
import boto3
import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    print(event)
    dynamodb = boto3.resource('dynamodb')

    doctorId = str(event['headers']['doctorid'])
    date = str(event['queryStringParameters']['date'])

    doctor_table = dynamodb.Table('doctors')

    doctor_response = doctor_table.query(
        KeyConditionExpression=Key('doctor_id').eq(doctorId)
    )

    doctor = doctor_response['Items'][0]
    availability_windows = doctor['windows']

    # Find the day for the given date
    date_obj = datetime.datetime.strptime(date, '%m/%d/%Y')
    day_for_date = date_obj.strftime('%A')

    isAvailable = False
    for day_dict in availability_windows:
        if day_dict.get(day_for_date) is not None:
            isAvailable = True
            slots = getSlots(day_dict[day_for_date])
            if len(slots) == 0:
                isAvailable = False
            break

    if isAvailable:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'Day': day_for_date, 'Slots': slots})
        }
    else:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'Message': 'Booking unavailable!'})
        }


def getSlots(slots_list):
    available_slots = []
    for slot in slots_list:
        if slot[list(slot.keys())[0]] == 'free':
            available_slots.append(list(slot.keys())[0])
    return available_slots