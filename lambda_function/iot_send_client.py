import json
import logging

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


class awsIoTClient():
   


    def __init__(self, config):
        self.certfolder = "certs"
        #self.event_value = 0
        self.myAWSIoTMQTTClient = AWSIoTMQTTClient(config['clientId'])
        # Configure logging
        self.logger = logging.getLogger("AWSIoTPythonSDK.core")
        self.logger.setLevel(logging.DEBUG)
        streamHandler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        streamHandler.setFormatter(formatter)
        self.logger.addHandler(streamHandler)

        self.myAWSIoTMQTTClient.configureEndpoint(config['host'], config['port'])
        self.myAWSIoTMQTTClient.configureCredentials(
            self.certfolder+ "/" + config['rootCAName'], 
            self.certfolder+ "/" + config['privateKeyName'], 
            self.certfolder+ "/" + config['certificateName'])

        # AWSIoTMQTTClient connection configuration
        self.myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
        self.myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect to AWS IoT
        self.myAWSIoTMQTTClient.connect()
        self.logger.log(logging.DEBUG, "Connected to host...")
    

    def publish_message(self, topic, payload):
        # Publish to the topic 
        message = {}
        message['value'] = payload
        messageJson = json.dumps(message)
        self.myAWSIoTMQTTClient.publish(topic, messageJson, 1)
        self.logger.log(logging.INFO, 'Published topic %s: %s\n' % (topic, messageJson))
