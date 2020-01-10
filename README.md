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
> __Note__: Ensure you sign in into the Alexa app from the same email address you used for creating Amazon Alexa Developer account. If you are using Alexa device, then the device should be configured with the same email address.

## Hardware

You can follow the steps mentioned in the [hardware](https://github.com/erviveksoni/raspberrypi-controlled-tello#hardware) section of my previous project to also prepare for the upcoming projects. 

Alternatively, to keep it very simple here just connect the Micro USB to USB Type A female adapter + Wifi dongle to the Raspberry Pi (Zero).


## Software

- Let's start by download this Repository on your development machine  
  `git clone https://github.com/erviveksoni/alexa-controlled-drone`
- `cd` into the `alexa-controlled-drone` directory
- Create a new folder `certs` 

### Provision AWS IoT Device

Let's start by setting up a device in AWS IoT to enable us communication with Raspberry Pi.

#### Creating Policy
- [Sign in](https://console.aws.amazon.com/console/home) into the AWS Console
- In the find service section, search for the service `IoT Core`
- On the left hand navigation, click to expand `Secure` and then select `Policies`
- Click `Create` in the top right corner of the screen
- In the create policy screen, click `Advanced mode`
- Provide a policy name e.g. AlexaPolicy
- Replace the `ACCOUNT_NUMBER` with your AWS [Account Id](https://console.aws.amazon.com/billing/home?#/account) in the next below
````json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topic/drone/takeoff",
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topic/drone/land",
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topic/drone/direction",
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topic/drone/rotate",
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topic/drone/flip"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe"
      ],
      "Resource": [
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topicfilter/drone/takeoff",
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topicfilter/drone/land",
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topicfilter/drone/direction",
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topicfilter/drone/rotate",
        "arn:aws:iot:us-east-2:ACCOUNT_NUMBER:topicfilter/drone/flip"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect"
      ],
      "Resource": "*"
    }
  ]
}
````
- Paste the policy text into the text box and click `Create`

#### Creating a Thing
- On the left hand navigation, click to expand `Manage` and then select `Thing`
- Click `Create` in the top right corner of the screen
- Click `Create a single thing` button in the next screen
- Provide a name for the things e.g.Tello
- Click `Next`
- Click `Create certificate` in front of One-click certificate creation (recommended)
- Download all the 3 certificate files for your thing (public, private and certificate) and save them into `certs` folder
- Click `Active` button to activate the root CA for AWS IoT
- Download the root CA certificate for AWS IoT from [here](https://docs.aws.amazon.com/iot/latest/developerguide/server-authentication.html#server-authentication-certs) and save it into `certs` folder
- Click `Attach a policy` button and select the policy `AlexaPolicy` you created in the above section
- Click `Register thing` to finish Thing creation
- Once the Thing is created, open the thing details and click `Interact` in the left hand navigation
- Make a note of the value of `REST API Endpoint` under the HTTPS section for later use. 
e.g. `xxxxxxxxxxxxxx-ats.iot.us-east-2.amazonaws.com`
We will use this endpoint to interact with the Thing later in the process. 

At this point, we have all the stuff ready to communicate with the Thing.

### Creating AWS Lambda Function

Next step is to create an AWS Lambda function which will be invoked by the Alexa skill. 
The message passed by the Alexa invocation to the Lambda function will be validated against a list of allowed actions and further sent to the Thing we created in the above step.

Every message passed to the Lambda function represents a type of action the user wants to execute. Further every action has a designated MQTT topic defined in the policy attached to the Thing.

#### Creating Lambda Function
- In the AWS developer console, search for `lambda`
- Click `Lambda` in the results to navigate to the Lambda console
- Click `Create function` in the top right corner of the screen
- Put the function name as `Alexafunction`
- Runs time as `Python 3.7`
- Click `Create function`
- In the `Designer` section, click `Add trigger`
- In the Trigger configuration page, select `Alexa Skill Kit`
- Select `disable` option for the Skill ID verification
- Click `Add` to complete adding an alexa trigger
- On the Designer section, click the lamda function icon
- Go to `Basic settings` section of the page
- On a safer side, set memory as `256 MB` and Timeout as `10 seconds`
- Click `Save` button on the top right corner to save changes
- Make a note of the lambda function `ARN` from the top right corner of the screen

#### Packaging Lambda Function Code
- Copy the `certs` folder in the root of the `alexa-controlled-drone` directory to the `lambda_function` subdirectory
- `cd` into the `lambda_function` sub directory
- Open `lambda_function.py` file in your preferred text editor 
- Update the config section at the top of this file with the cert names and Rest API Endpoint details you noted earlier 
````python
config = { 
         'host': '<REST API Endpoint>',
         'rootCAName': '<Root certificate file name>',
         'certificateName': '<Certificate file name>',
         'privateKeyName' : '<Private key file name>',
         'clientId': 'drone_alexa',
         'port' : 8883
}
````
- Save changes and close the file
- Open command line and type
`pip3 install AWSIoTPythonSDK -t .` to download AWSIoTPythonSDK inside the `lambda_function` directory
- Create a zip package with only the **contents** of the `lambda_function` directory

    `zip -9r lambda.zip AWSIoTPythonSDK* certs/* iot_send_client.py lambda_function.py alexa_response_builder.py`
- At this point you should have a zip file `lambda.zip` ready to be uploaded to AWS Lambda function

#### Upload Lambda Function Package
- Back on the Lambda function console, from the Designer section, click the lamda function icon
- Expand the `Code entry type` dropdown and select `Upload a .zip file`
- Click `Upload` button and browse and select the `lambda.zip` file
- Click `Save` button on the top right corner to save changes

You should now be able to see your code in the online code editor interface of AWS Lambda.

### Creating Alexa Skill
Now we are all set to create an Alexa skill which will interact with user to receive commands and fly the drone.

- Sign into [Alexa Skills Kit Developer Console](https://developer.amazon.com/alexa/console/ask) with your credential created in prerequisite section
- Click `Create Skill` button
- Give your skill a name e.g. `Tello Voice Control`
- Select a default language. Your skill will only appear if the user has this language selected
- Select the model as `Custom` and hosting method as `Provision your own`
- Click `Create skill` button on top right of the screen
- Select the skill template as `Start from scratch` and then click `Choose`
- Click `Invocation` from the left hand navigation
- Specify a Skill Invocation Name e.g. `drone pilot`
- Click `Save Model` button at the top of the page
- Click `JSON Editor` on the left hand navigation
- Copy and paste the contents of the `skill.json` file you downloaded as part of this repository into the editor surface
- Click `Save Model` button at the top of the page
- Feel free to go through the list of intents from the left hand navigation. Every intent represents a command the user can invoke
- Click `Endpoint` from the left hand navigation
- Select `AWS Lambda ARN`
- In the Default Region textbox paste the `ARN` of the Lambda function you noted in the previous section
- Click `Save Endpoints` button at the top of the page
- Click `Invocation` from the left hand navigation
- Click `Build Model` button at the top of the page and wait for the skill build process to complete

#### Test Alexa Skill
Now is the time to put your skill to test!!! 

There are multiple ways to test your skill. The easiest one is by using the Alexa simulator provided in the  Alexa Skills Developer Console
- On the top navigation bar, click `Test`
- Select `Skill testing is enabled in:` as `Development`
- Press the microphone button an speak _`Alexa, open drone pilot`_
- You should receive a voice feedback as _`To start, you should say: Alexa, ask drone pilot to take off.`_
- You can try other commands e.g. _`Alexa, ask drone pilot to take off`_ and alexa should respond back with the command acknowledgement
<img src="/images/skill_card_image.png" alt="Alexa Skill Card" width="400" height="274" border="10" />
<br/>

You can also [Test your Alexa Skill on a Alexa Device with Your Developer Account](https://developer.amazon.com/en-US/docs/alexa/devconsole/test-your-skill.html#h2_register). 
Or you add and test your skill to the companion app on Android and iOS smartphones.

Congratulations!! You have successfully created an alexa skill to fly your drone!!

Now the last step is to setup Raspberry Pi and make it to talk to AWS IoT thing to receive commands.

### Setting up Raspberry Pi

#### Setting up Raspbian Buster Lite
We will setup Raspberry Pi in headless mode to get the optimal usage of RAM and CPU. There are many good posts on how to setup Raspbian Buster Lite on the Raspberry Pi Zero in [Headless Mode](https://desertbot.io/blog/setup-pi-zero-w-headless-wifi/) 

At this point in time, we should be able to SSH into out Pi using the Wifi onboard. Also the Pi will be most likely have access to the internet (dependeing on your WIFI network settings).

#### Connecting Raspberry Pi to Tello

When you turn on Tello, it configures itself as an AP allowing the clients to connect and control to it. Once a client is connected to Tello, it looses internet connectivity. 
To avoid this we'll configure the Raspberry Pi with dual WIFI interfaces. 

The Raspberry Pi onboard WIFI connects to the internet (via my home network) and the WIFI Adapter connects to Tello's WIFI.

Here are the steps:
- Ensure the WIFI dongle is connected to the Raspberry Pi Zero micro usb port
- Power on Raspberry Pi
- SSH into Raspberry Pi Zero
- Type `lsusb`. Ensure you see the WIFI USB adapter listed on the console output
- Type `sudo nano /etc/network/interfaces` to edit the network interfaces file
- Add the text below towards the end of the file. 
Replace the `TELLO_NETWORK_NAME` with the WIFI AP name of Tello followed by its password.

```c
auto lo

iface lo inet loopback
iface eth0 inet dhcp

allow-hotplug wlan0
iface wlan0 inet manual
wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf

allow-hotplug wlan1
iface wlan1 inet dhcp
wpa-ssid "<TELLO_NETWORK_NAME>"
wpa-psk "<PASSWORD>"

iface default inet dhcp
```
- Save your changes to the interfaces file
- Shutdown Raspberry Pi `sudo shutdown now`
- Turn on Tello
- Power on Raspberry Pi and SSH into it
- Type `ifconfig` to list the Raspberry Pi network interfaces
- You should see 2 interfaces `wlan0` and `wlan1` connected to their network respectively
- __In case you don't see an IP address acquired for `wlan1`__, then reset the `wlan1` interface using the command
 `sudo dhclient -v wlan1`

#### Installing Required Packages on Raspberry Pi
SSH into Raspberry Pi and follow the steps below.
##### Installing Python

- `sudo apt-get install python3-dev`
- `sudo apt install python3-pip`

##### Installing Other Packages
- `pip3 install tellopy`
- `pip3 install AWSIoTPythonSDK`

### Setting up the Source Code
- Clone this Repository on Raspberry Pi
  `git clone https://github.com/erviveksoni/alexa-controlled-drone`
- `cd` into the `alexa-controlled-drone/pi-alexa-code` directory
- Copy the [certs folder](#software) which has all the certificates from your development machine into `pi-alexa-code`
- Open `start.py` file in your preferred text editor 
- Update the config section at the top of this file with the cert names and Rest API Endpoint details you noted earlier 
````python
config = { 
         'host': '<REST API Endpoint>',
         'rootCAName': '<Root certificate file name>',
         'certificateName': '<Certificate file name>',
         'privateKeyName' : '<Private key file name>',
         'clientId': 'drone_alexa_client',
         'port' : 8883
}
````
- Save changes and close the file

## Running the Application

Now its time to run the application!

- SSH into Raspberry Pi
- __Ensure that the drone is powered on and your Raspberry Pi is connected to it's WIFI network using the secondary WLAN interface. Check the [above](#Connecting Raspberry Pi to Tello) section to verify and troubleshoot.__
- `cd` into the `alexa-controlled-drone/pi-alexa-code` directory
- Type `python3 start.py`
- You should see the drone telemetry getting displayed on the console
- Now open your Alexa app or Alexa device with your skill enabled on it
- Say a command from the list below..

### Available Alexa Commands
**_Alexa, ask drone pilot to take off_** <br/>
**_Alexa, ask drone pilot to go left_** Other possible values (`up/down/back/forward/left/right`)<br/>
**_Alexa, ask drone pilot to rotate left_** Other possible values (`left/right`)<br/>
**_Alexa, ask drone pilot to flip_**<br/>
**_Alexa, ask drone pilot to land_**<br/>
