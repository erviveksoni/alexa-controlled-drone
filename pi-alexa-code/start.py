import json
import logging
import time

import tellopy

from iot_receive_client import awsIoTClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)
awsclient = None

speed = 100
drone = None
prev_flight_data = None
flight_data = None
log_data = None

##############################
# Configurations
##############################

config = { 
         'host': '<REST API Endpoint>',
         'rootCAName': '<Root certificate file name>',
         'certificateName': '<Certificate file name>',
         'privateKeyName' : '<Private key file name>',
         'clientId': 'drone_alexa_client',
         'port' : 8883
}


##############################
# Drone connection
##############################

def connect_drone():
    mydrone = tellopy.Tello()
    mydrone.subscribe(mydrone.EVENT_CONNECTED, drone_event_handler)
    mydrone.subscribe(mydrone.EVENT_DISCONNECTED, drone_event_handler)
    mydrone.subscribe(mydrone.EVENT_FLIGHT_DATA, drone_event_handler)
    mydrone.subscribe(mydrone.EVENT_LOG, drone_event_handler)
    mydrone.connect()
    mydrone.wait_for_connection(60.0)
    return mydrone


##############################
# Message callack
##############################

def drone_event_handler(event, sender, data, **args):
    global prev_flight_data, flight_data, log_data
    mydrone = sender
    if event is mydrone.EVENT_CONNECTED:
        is_drone_connected = True
    elif event is mydrone.EVENT_DISCONNECTED:
        logging.warning("Disconnected from drone!...")
        drone.quit()
    elif event is mydrone.EVENT_FLIGHT_DATA:
        if prev_flight_data != str(data):
            logging.info(data)
            prev_flight_data = str(data)
        flight_data = data
    elif event is mydrone.EVENT_LOG:
        log_data = data
        # print(self.log_data)
    else:
        logging.info('event="%s" data=%s' % (event.getname(), str(data)))


##############################
# Callback
##############################

def message_callback(client, userdata, message):
    try:
        topic = message.topic
        rawdata = str(message.payload.decode("utf-8"))
        logging.info("Topic: " + message.topic + "\nMessage: " + rawdata)
        jsondata = json.loads(rawdata)
        data = jsondata["value"]
        
        if topic == "drone/takeoff":
            drone.takeoff()
        elif topic == "drone/land":
            drone.land()
        elif topic == "drone/direction":
            if data == "right":
                execute_command(lambda: drone.right(speed), lambda: drone.right(0))
            elif data == "left":
                execute_command(lambda: drone.left(speed), lambda: drone.left(0))
            elif data == "forward":
                execute_command(lambda: drone.forward(speed), lambda: drone.forward(0))
            elif data == "back":
                execute_command(lambda: drone.backward(speed), lambda: drone.backward(0))
            elif data == "up":
                execute_command(lambda: drone.up(speed), lambda: drone.up(0))
            elif data == "down":
                execute_command(lambda: drone.down(speed), lambda: drone.down(0))
            else:
                pass
        elif topic == "drone/flip":
            drone.flip_forward()
        elif topic == "drone/rotate":
            if data == "left":
                execute_command(lambda: drone.counter_clockwise(speed), lambda: drone.counter_clockwise(0))
            elif data == "right":
                execute_command(lambda: drone.clockwise(speed), lambda: drone.clockwise(0))
            else:
                pass
        else:
            pass

    except Exception as e:
        logging.error("Error occurred " + str(e))

# Executing the command for 1 second
def execute_command(command_callback, stop_callback):
    t_end = time.time()
    while (time.time() - t_end) < 1:
        #print(time.time() - t_end)
        command_callback()
        time.sleep(300e-3) #300ms
    
    if stop_callback is not None:
        stop_callback()

##############################
# Entry point
##############################

if __name__ == "__main__":

    try:
        awsclient = awsIoTClient(config)
        drone = connect_drone()
        awsclient.suscribe(['drone/takeoff', 'drone/land', 'drone/direction', 'drone/rotate', 'drone/flip'],
                           message_callback)
    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt...')
    except Exception as e:
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # traceback.print_exception(exc_type, exc_value, exc_traceback)
        logging.error(str(e))
    finally:
        if drone is not None:
            drone.land()
            drone.quit()
        if awsclient is not None:
            awsclient.disconnect()
        logging.info('Exiting program...')
