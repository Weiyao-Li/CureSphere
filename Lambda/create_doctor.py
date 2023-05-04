import json
import boto3
import datetime
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    try:
        ddb_results = insert_data(event['headers'])
        return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
                },
                'body': json.dumps({'results': ddb_results})
            }
    except Exception as e:
        return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
                },
                'body': f'Invalid input:{e}'
            }
            


def insert_data(data, db=None, table='doctors'):
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
    # record['appointment_id'] = ''
    record['doctor_id'] = data['email']
    record['windows'] = []
    # Convert string data['available_days'] to a list -> TO CHANGE BASED ON FRONTEND INPUT
    available_days = get_list_from_string(data['available_days'])
    print("Available days:" + str(available_days))
    for i in range(len(available_days)):
        day_dict = {}
        day_dict[available_days[i]] = [] # Each day has a list of slots
        
        # Convert string data['available_time_slots'] to a list -> TO CHANGE BASED ON FRONTEND INPUT
        available_time_slots = get_list_from_string(data['available_time_slots'])
        print("Available time slots:" + str(available_time_slots))
        for time_slot in split_time_slot(available_time_slots[i]):
            slot_dict = {}
            slot_dict[time_slot] = 'free'
            day_dict[available_days[i]].append(slot_dict)
        
        record['windows'].append(day_dict)
    return record
    
def split_time_slot(time_slot):
    start, end = time_slot.split('-')
    start_time, start_meridian = start[:-2], start[-2:]
    end_time, end_meridian = end[:-2], end[-2:]
    start_hour, start_minute = map(int, start_time.split(':'))
    end_hour, end_minute = map(int, end_time.split(':'))
    
    if start_meridian == 'PM' and start_hour != 12:
        start_hour += 12
    if end_meridian == 'PM' and end_hour != 12:
        end_hour += 12
    
    start_minutes = start_hour * 60 + start_minute
    end_minutes = end_hour * 60 + end_minute
    
    time_windows = []
    current_minutes = start_minutes
    
    while current_minutes < end_minutes:
        current_time = f"{current_minutes // 60:02d}:{current_minutes % 60:02d}"
        next_minutes = current_minutes + 30
        next_time = f"{next_minutes // 60:02d}:{next_minutes % 60:02d}"
        time_windows.append(f"{current_time}-{next_time}")
        current_minutes = next_minutes
    print("Time windows: " + str(time_windows))
    return time_windows

def get_list_from_string(string):
    res = []
    string = string.replace("[", "")
    string = string.replace("]", "")
    elems = string.split(",")
    for elem in elems:
        res.append(elem)
    return res    
    
