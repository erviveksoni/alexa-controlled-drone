# Amazon Alexa Voice Controlled Drone

In this project, I demonstrates developing an Alexa skill to fly and control DJI Tello drone. 
This projects leverages AWS IoT platform to enable communication between Raspberry Pi Zero, DJI Tello and a custom Amazon Alexa skill giving the ability to control the drone via voice commands.

This is the second project in the series of projects I am doing using DJI Tello and Raspberry Pi.
In case you missed my first project on controlling DJI Tello with Xbox Controller, here is the [link to it](https://github.com/erviveksoni/raspberrypi-controlled-tello).

Here is a [short video](https://www.youtube.com/watch?v=rT4CF4Krcc8) where I am flying the drone using Alexa voice commands:

<img src="/images/alexa_drone_logo.jpg" alt="Alexa Tello" width="600" height="274" border="10" />
<br/><br/>

At high level, following are the sequence of events which take place during this interaction:
1. User invokes the Alexa skill (in our case `drone pilot`) and issues a voice command
2. Alexa skill validates this command with the available set of intents associated to the skill
3. Alexa then sends the identified intent to the configured AWS Lambda function endpoint
4. The lambda function receives incoming command, 
    * Creates the command message and sends it to the AWS IoT device via MQTT channel
    * The lambda function also responds to the Alexa command with a success message
6. A Raspberry Pi zero (connected to the DJI Tello via WIFI) suscribes to the AWS IoT MQTT channel for new messages
7. Upon receiving a message, the the Raspberry Pi interprets the MQTT message and issues a corresponding DJI Tello specific command

In case you are new to AWS and Raspberry Pi, you may feel a lot is going around to make this work but I promise it's very easy once you follow through the steps. 

This project will also enable you to implement other ideas on similar lines or completely different since the blocks/services used here are very much needed for developing any IoT application.

## Prerequisites
- Raspberry Pi Zero W or any Raspberry Pi with WIFI on-board
- [DJI Tello](https://store.dji.com/product/tello). Ensure your Tello is setup and you are able to fly with your phone app.
- [WiFi Dongle](https://www.raspberrypi.org/products/raspberry-pi-usb-wifi-dongle/)
- If you are using Raspberry Pi Zero W: Micro USB to USB Type A female adapter [something like this](https://www.amazon.com/CableCreation-Adapter-Compatible-Samsung-Function/dp/B01LXBS8EJ/)
- AWS Account. You can create one for free [here](https://aws.amazon.com/free/)
- Amazon Alexa Developer account. You can create one for free [here](https://developer.amazon.com)
- Amazon Alexa Device or Alexa App (get it from app store or google play) installed on your phone.
> __Note__: Ensure you sign iinto the Alexa app from the same email address you used for creating Amazon Alexa Developer account.
