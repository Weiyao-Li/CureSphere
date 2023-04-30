import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
import json

# Elasticsearch configuration
REGION = 'us-east-1'
HOST = 'search-appointments-ijrmccfpodio2x2fsobemencsu.us-east-1.es.amazonaws.com'
INDEX = 'appointments'

# DynamoDB table name
dynamodb_table = 'medicinedata'

# Elasticsearch configuration
es = Elasticsearch(
    hosts=[{'host': HOST, 'port': 443}],
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# DynamoDB configuration
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(dynamodb_table)


def get_latest_medicine_name(appointment_id):
    # Query ElasticSearch for the latest medicine entry with given appointmentId
    query = {
        "size": 1,
        "sort": [
            {"timestamp": {"order": "desc"}}
        ],
        "query": {
            "term": {
                "a_id": appointment_id
            }
        }
    }

    response = es.search(index=INDEX, body=query)
    if response['hits']['total']['value'] > 0:
        return response['hits']['hits'][0]['_source']['medicine']
    else:
        return None


def get_medicine_comparison(medicine_name):
    # Query the MedicineDataDB for the lowest 3 products with the same medicine name
    response = table.scan(
        FilterExpression='#name = :medicine_name',
        ExpressionAttributeNames={
            '#name': 'medicine_name'
        },
        ExpressionAttributeValues={
            ':medicine_name': medicine_name
        }
    )

    if response['Count'] > 0:
        # Sort the results by price and take the lowest 3 products
        sorted_medicines = sorted(response['Items'], key=lambda x: x['price'])[:3]

        # Prepare the result for display
        result = []
        for medicine in sorted_medicines:
            result.append({
                'seller_name': medicine['seller_name'],
                'medicine_name': medicine['medicine_name'],
                'price': medicine['price'],
                'zip_code': medicine['zip_code']
            })
        return result
    else:
        return None


def lambda_handler(event, context):
    appointment_id = event['appointmentId']
    print('here is the app_id you get: ', appointment_id)

    medicine_name = get_latest_medicine_name(appointment_id)
    print('here is the medicine name you get: ', medicine_name)

    if medicine_name:
        comparison_result = get_medicine_comparison(medicine_name)
        if comparison_result:
            return {
                'statusCode': 200,
                'body': json.dumps(comparison_result)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({"message": "No medicine data found in the database."})
            }
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({"message": "No latest medicine name found for the given appointmentId."})
        }


# workflow:
# the doctor as the user will input the name of the prescription into the elastic search.
# And please assume that there is a MedicineDataDB that has seller column, medicine name column, price column, and zip code.
# Here is the logic: the patient will click a refresh button and input an unique appointmentId and get the most updated medicine name that the doctor inputted in the elastic search.
# Specifically, the unique appointmentId is used to lock in that corresponding patient.
# Then, we will use that medicine name to go to MedicineDataDB to do the price comparison by selecting the lowest 3 products with the same medicine name as the name of the prescription in the db.
# What would return to the patient would be the seller name, medicine name, price and zip code,
# so that the user would know the existence of a lower-price medicine product and where it is and who is selling it.

# change
'''
event include incoming appointmentId
use this unique id to query es.
'''

