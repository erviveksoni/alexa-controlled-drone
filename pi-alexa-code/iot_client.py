import json
import logging
import time

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


class awsIoTClient():

    def __init__(self, config):
        self.loop = True
        self.certfolder = "certs"
        # self.event_value = 0
        self.myAWSIoTMQTTClient = AWSIoTMQTTClient(config['clientId'], cleanSession=False)
        # Configure logging
        self.logger = logging.getLogger("AWSIoTPythonSDK.core")
        self.logger.setLevel(logging.ERROR)
        streamHandler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        streamHandler.setFormatter(formatter)
        self.logger.addHandler(streamHandler)

        self.myAWSIoTMQTTClient.configureEndpoint(config['host'], config['port'])
        self.myAWSIoTMQTTClient.configureCredentials(
            self.certfolder + "/" + config['rootCAName'],
            self.certfolder + "/" + config['privateKeyName'],
            self.certfolder + "/" + config['certificateName'])

        # AWSIoTMQTTClient connection configuration
        self.myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
        self.myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

        # Connect to AWS IoT
        self.myAWSIoTMQTTClient.connect()
        self.logger.log(logging.DEBUG, "Connected to host...")

    def publish_message(self, topic, payload):
        # Publish to the topic 
        self.myAWSIoTMQTTClient.publish(topic, payload, 1)
        self.logger.log(logging.DEBUG, 'Published topic %s: %s\n' % (topic, payload))

    def suscribe(self, topics, callback):
        self.logger.log(logging.DEBUG, "Starting to suscribe...")
        for topic in topics:
            self.myAWSIoTMQTTClient.subscribe(topic, 1, callback)

    def disconnect(self):
        self.loop = False
        self.myAWSIoTMQTTClient.disconnect()
        self.logger.log(logging.DEBUG, "Disconnected...")
