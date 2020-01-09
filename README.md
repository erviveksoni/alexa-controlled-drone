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
- Copy the contents of the `aws-iot-policy.txt` file from the cloned repository code 
- Paste the policy text into the text box and click `Create`

#### Creating a Thing
- On the left hand navigation, click to expand `Manage` and then select `Thing`
- Click `Create` in the top right corner of the screen
- Click `Create a single thing` button in the next screen
- Provide a name for the things e.g.Tello
- Click `Next`
- Click `Create certificate` in front of One-click certificate creation (recommended)
- Download all the 3 certificate files for your thing (public, private and certificate) and save them into `certs` folder
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
         'host': '<REST API Endpoint of Thing>',
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

### Setting up Raspberry Pi Operating System
We will setup Raspberry Pi in headless mode to get the optimal usage of RAM and CPU. There are many good posts on how to setup Raspbian Buster Lite on the Raspberry Pi Zero in [Headless Mode](https://desertbot.io/blog/setup-pi-zero-w-headless-wifi/) 

At this point in time, we should be able to SSH into out Pi using the Wifi onboard. Also the Pi will be most likey have access to the internet (dependeing on your WIFI network settings).

### Connecting Raspberry Pi to Tello

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

### Installing Required Packages on Raspberry Pi
SSH into Raspberry Pi and follow the steps below.
#### Installing Python

- `sudo apt-get install python3-dev`
- `sudo apt install python3-pip`

#### Installing Other Packages
- `pip3 install tellopy`
- `pip3 install AWSIoTPythonSDK`

