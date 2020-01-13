import json
import logging
import time

import alexa_response_builder
from iot_client import awsIoTClient

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
awsclient = None
telemetry_data = None

##############################
# Configurations
##############################

config = {
    'host': 'a1g1yvj52z2sc3-ats.iot.us-east-2.amazonaws.com',
    'rootCAName': 'root-CA.crt',
    'certificateName': '12c5b3de6e-certificate.pem.crt',
    'privateKeyName': '12c5b3de6e-private.pem.key',
    'clientId': 'drone_alexa_lambda',
    'port': 8883
}


thing_name = "Tello"

device_shadow_get_topic = "$aws/things/" + thing_name + "/shadow/get"
device_shadow_get_accepted_topic = "$aws/things/" + thing_name + "/shadow/get/accepted"


##############################
# Program Entry
##############################

def lambda_handler(event, context):
    global awsclient
    response = None

    try:
        awsclient = awsIoTClient(config)
        awsclient.subscribe([device_shadow_get_accepted_topic], message_callback)
        awsclient.publish_message(device_shadow_get_topic, '')
        time.sleep(100e-3)  # 100ms

        if event['request']['type'] == "LaunchRequest":
            response = on_launch(event, context)

        elif event['request']['type'] == "IntentRequest":
            response = intent_router(event, context)

    except Exception as e:
        logging.error(str(e))
        response = on_processing_error(event, context, e)

    return response


def on_launch(event, context):
    return alexa_response_builder.statement("To start, you should say: Alexa, ask drone pilot to take off.")


def intent_router(event, context):
    return intent_router(event, context)


def on_processing_error(event, context, exc):
    logging.error(exc)
    return alexa_response_builder.statement("An error occured while processing your request.")


def message_callback(client, userdata, message):
    global telemetry_data
    try:
        topic = message.topic
        if topic == device_shadow_get_accepted_topic:
            # {"state":{"reported":{"ALT":0,"SPD":0,"BAT":63,"WIFI":90,"CAM":0,"MODE":1,"ISONLINE":false}}}
            rawdata = str(message.payload.decode("utf-8"))
            rawdata = json.loads(rawdata)
            telemetry_data = rawdata["state"]["reported"]
            logging.info(telemetry_data)

    except Exception as e:
        logging.error("Error occurred " + str(e))


##############################
# Routing
##############################

def intent_router(event, context):
    intent = event['request']['intent']['name']
    logging.info('Alexa intent: ' + intent)

    if intent == "ConnectionStatusIntent":
        if telemetry_data is None or telemetry_data["ISONLINE"] is False:
            return alexa_response_builder.statement("Drone pilot is offline.")
        else:
            return alexa_response_builder.statement("Drone pilot is online.")

    if telemetry_data is None or telemetry_data["ISONLINE"] is False:
        logging.info('Drone pilot offline...')
        return alexa_response_builder.statement("Drone pilot is offline. Cannot complete your request.")

    # Custom Intents

    if intent == "StatusIntent":
        if 'value' in event['request']['intent']['slots']['status']:
            value = event['request']['intent']['slots']['status']['value']
            return handle_status_intent(value)
        else:
            return alexa_response_builder.continue_dialog()

    if intent == "TakeoffIntent":
        return respond_intent("Drone taking off", "drone/takeoff", None)

    if intent == "LandIntent":
        return respond_intent("Drone landing", "drone/land", None)

    if intent == "DirectionIntent":
        if 'value' in event['request']['intent']['slots']['direction']:
            value = event['request']['intent']['slots']['direction']['value']
            return respond_intent("Drone going " + value, "drone/direction", value)
        else:
            return alexa_response_builder.continue_dialog()

    if intent == "FlipIntent":
        return respond_intent("Flip", "drone/flip", None)

    if intent == "RotateIntent":
        if 'value' in event['request']['intent']['slots']['direction']:
            value = event['request']['intent']['slots']['direction']['value']
            return respond_intent("Drone rotating " + value, "drone/rotate", value)
        else:
            return alexa_response_builder.continue_dialog()

    # Required Intents

    if intent == "AMAZON.CancelIntent":
        return cancel_intent()

    if intent == "AMAZON.HelpIntent":
        return help_intent()

    if intent == "AMAZON.StopIntent":
        return stop_intent()

    if intent == "AMAZON.FallbackIntent":
        return fallback_intent()


def handle_status_intent(value):
    if value.lower() == "battery":
        televalue = telemetry_data["BAT"]
        text = str(televalue) + " percent battery left!"
        return alexa_response_builder.statement(text)
    elif value.lower() == "wi-fi" or value.lower() == "wifi" or value.lower() == "wireless":
        televalue = telemetry_data["WIFI"]
        if televalue > 70:
            text = "WIFI signal is strong"
        elif 40 < televalue < 70:
            text = "WIFI signal is medium"
        else:
            text = "WIFI signal is weak"
        return alexa_response_builder.statement(text)
    elif value.lower() == "camera":
        televalue = telemetry_data["CAM"]
        if televalue == 1:
            text = "Camera is ON"
        else:
            text = "Camera is OFF"
        return alexa_response_builder.statement(text)
    else:
        return alexa_response_builder.statement("Not sure about the status of " + value)


##############################
# Required Intents
##############################


def cancel_intent():
    return alexa_response_builder.simple_statement(
        "You want to cancel")  # don't use CancelIntent as title it causes code reference error during certification


def help_intent():
    return alexa_response_builder.simple_statement("You want help")  # same here don't use CancelIntent


def stop_intent():
    return alexa_response_builder.simple_statement("You want to stop")  # here also don't use StopIntent


def fallback_intent():
    return alexa_response_builder.simple_statement(
        "Sorry, I do not understand the command.")  # here also don't use FallbackIntent


##############################
# Response
##############################

def respond_intent(command, topic, value):
    if telemetry_data["BAT"] < 15:
        logging.info('Drone pilot battery low...')
        return alexa_response_builder.statement("Drone battery low. Cannot complete your request.")
    message = {'value': value}
    payload = json.dumps(message)
    awsclient.publish_message(topic, payload)
    return alexa_response_builder.statement(command)
