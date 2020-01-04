import json
import logging
import os

import alexa_response_builder
from iot_send_client import awsIoTClient

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
awsclient = None


##############################
# Configurations
##############################

config = { 
         'host': 'a1g1yvj52z2sc3-ats.iot.us-east-2.amazonaws.com',
         'rootCAName': 'root-CA.crt',
         'certificateName': 'drone1.cert.pem',
         'privateKeyName' : 'drone1.private.key',
         'clientId': 'drone_alexa',
         'port' : 8883
}


##############################
# Program Entry
##############################

def lambda_handler(event, context):
    global awsclient
    response = None

    try:
        awsclient = awsIoTClient(config)

        if event['request']['type'] == "LaunchRequest":
            response = on_launch(event, context)
    
        elif event['request']['type'] == "IntentRequest":
            response = intent_router(event, context)
        
    except Exception as e:
        response = on_processing_error(event, context, e)
    
    return response

def on_launch(event, context):
    return alexa_response_builder.statement("To start, you should say: Alexa, ask drone pilot to take off.")

def intent_router(event, context):
    return intent_router(event, context)
    
def on_processing_error(event, context, exc):
    logging.error(exc)
    return alexa_response_builder.statement("An error occured while processing your request.")


##############################
# Routing
##############################

def intent_router(event, context):
    intent = event['request']['intent']['name']
    
    logging.info('Alexa intent: ' + intent)

    # Custom Intents

    if intent == "TakeoffIntent":
        return respond_intent("Drone taking off" , "drone/takeoff", None)

    if intent == "LandIntent":
        return respond_intent("Drone landing" , "drone/land", None)

    if intent == "DirectionIntent":
        if('value' in event['request']['intent']['slots']['direction']):
            value = event['request']['intent']['slots']['direction']['value']        
            return respond_intent("Drone going "+ value , "drone/direction", value)
        else:
            return alexa_response_builder.continue_dialog()

    if intent == "FlipIntent":
        return respond_intent("Flip" , "drone/flip", None)

    if intent == "RotateIntent":        
        if('value' in event['request']['intent']['slots']['direction']):
            value = event['request']['intent']['slots']['direction']['value']        
            return respond_intent("Drone rotating "+ value , "drone/rotate", value)
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


##############################
# Required Intents
##############################


def cancel_intent():
    return alexa_response_builder.simple_statement("You want to cancel")	#don't use CancelIntent as title it causes code reference error during certification 


def help_intent():
    return alexa_response_builder.simple_statement("You want help")		#same here don't use CancelIntent


def stop_intent():
    return alexa_response_builder.simple_statement("You want to stop")		#here also don't use StopIntent

def fallback_intent():
    return alexa_response_builder.simple_statement("Sorry, I do not understand the command.")		#here also don't use FallbackIntent


##############################
# Response
##############################

def respond_intent(command ,topic, value):
    awsclient.publish_message(topic, value)
    return alexa_response_builder.statement(command)
