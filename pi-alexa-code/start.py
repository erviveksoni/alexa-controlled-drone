import json
import logging
import os

from iot_receive_client import awsIoTClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)
awsclient = None


##############################
# Configurations
##############################

config = { 
         'host': 'a1g1yvj52z2sc3-ats.iot.us-east-2.amazonaws.com',
         'rootCAName': 'root-CA.crt',
         'certificateName': 'drone1.cert.pem',
         'privateKeyName' : 'drone1.private.key',
         'clientId': 'drone_alexa_sender',
         'port' : 8883
}

##############################
# Callback
##############################

def message_callback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


##############################
# Entry point
##############################

if __name__ == "__main__":

    try:
        awsclient = awsIoTClient(config)
        awsclient.suscribe(['drone/takeoff','drone/land','drone/direction','drone/rotate','drone/flip'],message_callback)
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt...')
    except Exception as e:
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # traceback.print_exception(exc_type, exc_value, exc_traceback)
        logging.error(str(e))
    finally:
        if(awsclient is not None):
            awsclient.disconnect()
        logging.info('Exiting program...')
