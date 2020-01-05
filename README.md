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

### Installing Required Packages
SSH into Raspberry Pi and follow the steps below.
#### Installing Python

- `sudo apt-get install python3-dev`
- `sudo apt install python3-pip`

#### Installing Other Packages
- `pip3 install tellopy`
- `pip3 install AWSIoTPythonSDK`
