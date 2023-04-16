import json
import boto3
import datetime
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    print(event)
    return lookup_data(key=event[key])


def lookup_data(key, db=None, table='doctors'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    try:
        response = table.get_item(Key=key)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print(response['Item'])
        return response['Item']
