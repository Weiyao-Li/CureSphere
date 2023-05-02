import datetime
import boto3
import json
import time
import os
import logging
import re
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Configure the DynamoDB client
dynamodb = boto3.resource('dynamodb')


# --- Helpers that build all of the responses ---

def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']


def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    if 'sessionAttributes' in sessionState:
        return sessionState['sessionAttributes']
    return {}


def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None:
        logger.debug('resolvedValue={}'.format(slots[slotName]['value']['resolvedValues']))
        return slots[slotName]['value']['interpretedValue']
    else:
        return None


def elicit_slot(intent_request, session_attributes, slot, slots, message):
    print("in eliciting slot")
    return {'sessionState': {'dialogAction': {'type': 'ElicitSlot',
                                              'slotToElicit': slot,
                                              },
                             'intent': {'name': intent_request['sessionState']['intent']['name'],
                                        'slots': slots,
                                        'state': 'InProgress'
                                        },
                             'sessionAttributes': session_attributes,
                             #  'originatingRequestId': '70d49ca7-53de-4e1e-ac0a-70ecfc45b70a'
                             },
            'sessionId': intent_request['sessionId'],
            'messages': [message],
            'requestAttributes': intent_request['requestAttributes']
            if 'requestAttributes' in intent_request else None
            }


def build_validation_result(isvalid, violated_slot, slot_elicitation_style, message_content):
    return {'isValid': isvalid,
            'violatedSlot': violated_slot,
            'slotElicitationStyle': slot_elicitation_style,
            'message': {'contentType': 'PlainText',
                        'content': message_content}
            }


def GetItemInDatabase(postal_code):
    """
    Perform database check for transcribed postal code. This is a no-op
    check that shows that postal_code can't be found in the database.
    """
    return None


def close(intent_request, session_attributes, fulfillment_state, message):
    intent_request['sessionState']['intent']['state'] = fulfillment_state
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent_request['sessionState']['intent'],
            'originatingRequestId': '2d3558dc-780b-422f-b9ec-7f6a1bd63f2e'
        },
        'messages': [message],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def delegate(intent_request, slots):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Delegate"
            },
            "intent": {
                "name": intent_request['sessionState']['intent']['name'],
                "slots": slots,
                "state": "ReadyForFulfillment"
            },
            'sessionId': intent_request['sessionId'],
            "requestAttributes": intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
        }}


def current_time():
    now = datetime.datetime.now()
    hour = str(now.hour).zfill(2)
    minute = str(now.minute).zfill(2)
    return f"{hour}:{minute}"


# patientId, date, time, doctorId
def validationProcess(zipcode):
    if zipcode:
        print('zipcode is: ', zipcode)
        pattern = r"^\d{5}(-\d{4})?$"  # Zip code pattern: five digits, optionally followed by a dash and four more
        # digits
        if not bool(re.match(pattern, zipcode)):
            return build_validation_result(False,
                                           'zipcode',
                                           'SpellByWord',
                                           'Invalid zipcode')
    print('returningTrue!!!!!')
    return build_validation_result(True,
                                   '',
                                   'SpellbyWord',
                                   '')


def get_specialty_from_symptoms(symptom_list):
    print('[DEBUG] inside get_specialty_from_symptom')
    symptom_specialty_table = dynamodb.Table('SymptomSpecialty')

    specialties = set()
    for symptom in symptom_list:
        try:
            response = symptom_specialty_table.get_item(
                Key={'symptom': symptom}
            )
            if 'Item' in response:
                for specialty in response['Item']['specialties']:
                    specialties.add(specialty)
        except ClientError as e:
            print('Error', e.response['Error']['Message'])
    print('[DEBUG] finished get_specialty_from_symptom', list(specialties))
    return list(specialties)


def get_doctor_from_specialty(specialties, patient_zipcode, num_results=3):
    doctor_table = dynamodb.Table('doctors')
    returned_docs = []

    index_name = 'department-index'
    index = None
    for i, gsi in enumerate(doctor_table.global_secondary_indexes):
        if gsi['IndexName'] == index_name:
            index = doctor_table.global_secondary_indexes[i]
            break
    print('[DEBUG] index is: ', index)
    for specialty in specialties:
        try:
            response = doctor_table.query(
                IndexName=index['IndexName'],
                KeyConditionExpression=Key('department').eq(specialty)
            )
            print('[DEBUG] doctorsDB response: ', response)
            doctors = response['Items']
            patient_doctor_distance = [
                distance_from_zipcode(patient_zipcode, d['clinic_zip_code']) for d in doctors
            ]
            sorted_doctors = sorted(zip(doctors, patient_doctor_distance), key=lambda x: x[1])
            top_k_sorted_doctors = [doctor for doctor, distance in sorted_doctors[:num_results]]

            for d in top_k_sorted_doctors:
                doctor_data = {
                    'doctor_id': d['doctor_id'],
                    'firstName': d['firstName'],
                    'lastName': d['lastName'],
                    'email': d['email'],
                    'clinic_zip_code': d['clinic_zip_code']
                }
                returned_docs.append(doctor_data)
        except ClientError as e:
            print('Error', e.response['Error']['Message'])
    return returned_docs


def distance_from_zipcode(zip1, zip2):
    return abs(int(zip1) - int(zip2))


def GetRecommendedDoctors(intent_request):
    state = intent_request['sessionState']

    zipcode = get_slot(intent_request, "zipcode")
    symptom1 = get_slot(intent_request, "symptom1")
    symptom2 = get_slot(intent_request, "symptom2")
    symptom3 = get_slot(intent_request, "symptom3")

    session_attributes = get_session_attributes(intent_request)

    # type of event that triggered the function
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        print("Here we are in DialogCodeHook!")

        slots = get_slots(intent_request)

        resOfValidation = validationProcess(zipcode)
        print("Validation result: ", resOfValidation)
        if not resOfValidation['isValid']:
            slots[resOfValidation['violatedSlot']] = None
            print("now eliciting")
            print(resOfValidation)
            result = elicit_slot(intent_request, session_attributes, resOfValidation['violatedSlot'], slots,
                                 resOfValidation['message'])
            print("the result of elicit slot")
            print(result)
            return result
    if not zipcode:
        return elicit_slot(intent_request, session_attributes, 'zipcode', get_slots(intent_request),
                           {'contentType': 'PlainText', 'content': 'Please provide your zip code'})

    if not zipcode and not symptom1:
        return delegate(intent_request, get_slots(intent_request))
    else:
        symptoms = [symptom1]
        if symptom2:
            symptoms.append(symptom2)
        if symptom3:
            symptoms.append(symptom3)

        returned_specialties = get_specialty_from_symptoms(symptoms)
        print("[DEBUG] Returned specialties are: ", returned_specialties[:3])

        top_k_doctors = get_doctor_from_specialty(specialties=returned_specialties, patient_zipcode=zipcode,
                                                  num_results=5)
        print(f"[DEBUG] Top {len(top_k_doctors)} are: {top_k_doctors}")

        # return {
        #     'statusCode': 200,
        #     'headers': {
        #         'Content-Type': 'application/json',
        #         'Access-Control-Allow-Headers': 'Content-Type',
        #         'Access-Control-Allow-Origin': '*',
        #         'Access-Control-Allow-Methods': '*'
        #     },
        #     'body': json.dumps({'results': top_k_doctors})
        # }
        # return list of doctors to Lex
        doctor_info_string = ""
        for doctor in top_k_doctors:
            doctor_info_string += f"Doctor ID: {doctor['doctor_id']}, First Name: {doctor['firstName']}, Last Name: {doctor['lastName']}, Email: {doctor['email']}, Clinic Zip Code: {doctor['clinic_zip_code']}\n"

        # Update the response to include the doctor information string
        return close(intent_request, session_attributes, 'Fulfilled', {
            'contentType': 'PlainText',
            'content': doctor_info_string,
        })


# --- Intents ---

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    intent_name = intent_request['sessionState']['intent']['name']
    # state = intent_request['sessionState']

    if intent_name == 'GetRecommendedDoctors':
        result = GetRecommendedDoctors(intent_request)
        print("the GetRecommendedDoctors intent")
        print(result)
        return result
    print("Error!", intent_name)


# --- Main handler ---
def lambda_handler(event, context):
    """
    Route the incoming request based on the intent.
    The JSON body of the request is provided in the event slot.
    """

    # By default, treat the user request as coming from
    # Eastern Standard Time.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()

    logger.debug('event={}'.format(json.dumps(event)))
    response = dispatch(event)
    print("The final response of the lambda handler")
    print(response)
    return response
