import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/783455253012/lf1_to_lf2_v2'


# --- Helpers that build all the responses ---


def elicit_slot(session_attributes, active_contexts, intent, slot_to_elicit, message):
    return {
        'sessionState': {
            'activeContexts': [{
                'name': 'intentContext',
                'contextAttributes': active_contexts,
                'timeToLive': {
                    'timeToLiveInSeconds': 600,
                    'turnsToLive': 1
                }
            }],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': intent,
        }
    }


def confirm_intent(active_contexts, session_attributes, intent, message):
    return {
        'sessionState': {
            'activeContexts': [active_contexts],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ConfirmIntent'
            },
            'intent': intent
        }
    }


def close(session_attributes, active_contexts, fulfillment_state, intent, message):
    response = {
        'sessionState': {
            'activeContexts': [{
                'name': 'intentContext',
                'contextAttributes': active_contexts,
                'timeToLive': {
                    'timeToLiveInSeconds': 600,
                    'turnsToLive': 1
                }
            }],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close',
            },
            'intent': intent,
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }

    return response


def delegate(session_attributes, active_contexts, intent, message):
    return {
        'sessionState': {
            'activeContexts': [{
                'name': 'intentContext',
                'contextAttributes': active_contexts,
                'timeToLive': {
                    'timeToLiveInSeconds': 600,
                    'turnsToLive': 1
                }
            }],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Delegate',
            },
            'intent': intent,
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }


def initial_message(intent_name):
    response = {
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': 'Location' if intent_name == 'DiningSuggestionsIntent' else 'GreetingIntent'
            },
            'intent': {
                'confirmationState': 'None',
                'name': intent_name,
                'state': 'InProgress'
            }
        }
    }

    return response


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(value):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary of the Slots section in the payloads.
    Note that this function would have negative impact on performance.
    """

    if value is not None:
        return value['value']['interpretedValue']
    else:
        return None


# keep
# def isvalid_city(city):
#     valid_cities = ['new york']
#     return city.lower() in valid_cities
#
#
# def isvalid_cuisine(cuisine):
#     valid_cuisines = ['greek', 'indian', 'american', 'french', 'italian']
#     return cuisine.lower() in valid_cuisines


# keep
def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': message_content
        # 'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_appointment(slots):
    date = try_ex(slots['date'])

    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date',
                                           'I did not understand your check in date.  When would you like to check in?')
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'Date',
                                           'Reservations must be scheduled at least one day in advance.  Can you try '
                                           'a different date?')
    else:
        return build_validation_result(
            False,
            'Date',
            'Elicit Date'
        )
    return {'isValid': True}


""" --- Functions that control the bot's behavior --- """


def book_appointment(intent_request):
    """
    Performs dialog management and fulfillment for booking a hotel.
    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """

    intent = intent_request['sessionState']['intent']
    slots = intent_request['sessionState']['intent']['slots']

    session_attributes = {'sessionId': intent_request['sessionId']}

    active_contexts = {}

    confirmation_status = intent_request['sessionState']['intent']['confirmationState']

    # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
    # TODO change validate
    validation_result = validate_appointment(intent_request['sessionState']['intent']['slots'])

    if not validation_result['isValid']:
        slots = intent_request['sessionState']['intent']['slots']
        slots[validation_result['violatedSlot']] = None

        return elicit_slot(
            session_attributes,
            active_contexts,
            intent_request['sessionState']['intent'],
            validation_result['violatedSlot'],
            validation_result['message']
        )

    # Otherwise, let native DM rules determine how to elicit for slots and prompt for confirmation.
    else:
        city = try_ex(slots['city'])
        date = try_ex(slots['date'])
        specialty = try_ex(slots['specialty'])
        # email = try_ex(slots['Email'])
        # no_of_people = try_ex(slots['NumberOfPeople'])
        booking_time = try_ex(slots['time'])

        if city and date and specialty and booking_time:
            # Load confirmation history and track the current reservation.
            reservation = json.dumps({
                'city': city,
                'specialty': specialty,
                'date': date,
                'time': booking_time
            })

        if confirmation_status == 'None':
            return delegate(session_attributes, active_contexts, intent,
                            'Confirm book appointment')

        elif confirmation_status == 'Confirmed':
            # Creating the request for restaurant suggestion. In a real application, this would likely involve a call
            # to a backend service.
            intent['confirmationState'] = "Confirmed"
            intent['state'] = "Fulfilled"
            print(type(intent_request['sessionState']['intent']['slots']),
                  intent_request['sessionState']['intent']['slots'])
            sqs_message = {
                "Location": slots['city']['value']['resolvedValues'][0],  # not necessary?
                "Specialty": slots['specialty']['value']['resolvedValues'][0],
                "Date": slots['date']['value']['resolvedValues'][0],
                # "Email": slots['Email']['value']['resolvedValues'][0],
                # "NumberOfPeople": slots['NumberOfPeople']['value']['resolvedValues'][0],
                "Time": slots['time']['value']['resolvedValues'][0]
            }
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(sqs_message),
            )

            return close(session_attributes, active_contexts, 'Fulfilled', intent,
                         'Thanks, I have placed your appointment! Please let me know if you would like further '
                         'appointments '
                         )


# --- Intents ---
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    logger.debug(intent_request)

    slots = intent_request['sessionState']['intent']['slots']

    city = slots['city'] if 'city' in slots else None
    specialty = slots['specialty'] if 'specialty' in slots else None

    intent_name = intent_request['sessionState']['intent']['name']

    # Ignoring initial invocation, which happens after the first interaction of the end user with the intents in the
    # testing interface
    if not isinstance(city, type(None)) or not isinstance(specialty, type(None)):
        logger.debug('dispatch sessionId={}, intentName={}'.format(intent_request['sessionId'],
                                                                   intent_request['sessionState']['intent']['name']))

        # Dispatch to your bot's intent handlers
        if intent_name == 'BookAppointment':
            return book_appointment(intent_request)

        raise Exception('Intent with name ' + intent_name + ' not supported')

    logger.debug('Conversation initiated')
    return initial_message(intent_name)


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    # logger.debug('event.bot.name={}'.format(event['bot']['name']))
    print('dispatch is', dispatch(event))
    return dispatch(event)
