import json
import boto3
import datetime
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    file_name = "sampleMedicineData.json"
    with open(file_name) as json_file:
        data = json.load(json_file)
        json_file.close()
        insert_data(data)
    return

def insert_data(data_list, db=None, table='medicinedata'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # overwrite if the same index is provided
    for data in data_list:
        response = table.put_item(Item=data)
    print('@insert_data: response', response)
    return response