import json
import boto3
import datetime
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    print(event)
    insert_data(event)


def insert_data(data, db=None, table='patients'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    record = transform_data(data)
    response = table.put_item(Item=record)
    print('@insert_data: response', response)
    return response


def transform_data(data):
    record = {}
    for key in data.keys():
        record[key] = data[key]
    record['appointment_link'] = ''
    record['patient_id'] = data['email']
    return record
