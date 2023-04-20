import datetime
import boto3
import json
import time
import os
import logging

# maybe import math and re, To-do later

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


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
    print("in elicitng slot")
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
def validationProcess(Date, Time):
    # Date Validation
    if Date:
        print("Debug: date is:", Date)
        year, month, day = map(int, Date.split('-'))
        date_to_check = datetime.date(year, month, day)
        if date_to_check < datetime.date.today():
            return build_validation_result(False, 'Date', 'SpellByWord', 'Please enter a valid Dining date')

        if Time:
            print("Debug: time is:", Time)
            year, month, day = map(int, Date.split('-'))
            date_to_check = datetime.date(year, month, day)
            now = current_time()
            print("this is currwnt time")
            print(now)
            if (date_to_check <= datetime.date.today() and Time < now) or not Time:
                print("error in time")
                return build_validation_result(False, 'Time', 'SpellByWord', 'Please enter valid time')
    print('returningTrue!!!!!')
    return build_validation_result(True,
                                   '',
                                   'SpellbyWord',
                                   '')

def BookAppointmentIntent(intent_request):
    state = intent_request['sessionState']

    Date = get_slot(intent_request, "date")
    Time = get_slot(intent_request, "time")
    patientId = get_slot(intent_request, "patientId")
    doctorId = get_slot(intent_request, "doctorId")

    session_attributes = get_session_attributes(intent_request)

    # type of event that triggered the function
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        print("Here we are in DialogCodeHook!")

        slots = get_slots(intent_request)

        resOfValidation = validationProcess(Date, Time)
        print("result of validation")
        print(resOfValidation)
        if not resOfValidation['isValid']:
            slots[resOfValidation['violatedSlot']] = None
            print("now eliciting")
            print(resOfValidation)
            result = elicit_slot(intent_request, session_attributes, resOfValidation['violatedSlot'], slots,
                                 resOfValidation['message'])
            print("the result of elicit slot")
            print(result)
            return result

    if not Date or not Time or not patientId or not doctorId:
        return delegate(intent_request, get_slots(intent_request))
    else:
        send_message_to_SQS(
            Date,
            Time,
            patientId,
            doctorId
        )
        return close(intent_request,
                     session_attributes,
                     'Fulfilled',
                     {'contentType': 'PlainText',
                      'content': 'Thanks. We will send you email shortly'})


# --- Intents ---

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    intent_name = intent_request['sessionState']['intent']['name']
    # state = intent_request['sessionState']

    if intent_name == 'BookAppointment':
        result = BookAppointmentIntent(intent_request)
        print("the final BookAppointment intent")
        print(result)
        return result
    print("Error!", intent_name)


def send_message_to_SQS(Date, Time, patientId, doctorId):
    sqs = boto3.client('sqs')

    response = sqs.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/227639073722/bookAppointmentSQS",
        MessageAttributes={
            'Date': {
                'DataType': 'String',
                'StringValue': Date
            },
            'Time': {
                'DataType': 'String',
                'StringValue': Time
            },
            'patientId': {
                'DataType': 'String',
                'StringValue': patientId
            },
            'doctorId': {
                'DataType': 'String',
                'StringValue': doctorId
            }
        },

        MessageBody=('Information about user inputs of Dining Chatbot.'),
    )


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