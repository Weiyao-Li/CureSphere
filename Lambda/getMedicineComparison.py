import boto3
import json
import decimal
from json import JSONEncoder


# Custom JSON Encoder to handle Decimal type
class DecimalEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


REGION = 'us-east-1'
# DynamoDB table name
dynamodb_table = 'medicinedata'

# DynamoDB configuration
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(dynamodb_table)


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
                'zip_code': int(medicine['zip_code'])
            })
        return result
    else:
        return None


def lambda_handler(event, context):
    print('event is', event)

    medicine_name = event['headers']['medicineName']
    print('here is the medicine name you get: ', medicine_name)

    if medicine_name:
        comparison_result = get_medicine_comparison(medicine_name)

        if comparison_result:
            return {
                'statusCode': 200,
                'body': json.dumps(comparison_result, cls=DecimalEncoder)
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
