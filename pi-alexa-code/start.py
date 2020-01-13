import json
import logging
import threading
import time
import tellopy
import queue
from command import command

from iot_client import awsIoTClient

logger = logging.getLogger()
logger.setLevel(logging.INFO)
aws_client = None

speed = 80
drone = None
prev_flight_data = None
flight_data = None
log_data = None
is_drone_connected = False
command_queue = None
initial_data = 'ALT:  0 | SPD:  0 | BAT: 0 | WIFI: 0 | CAM:  0 | MODE:  0'

##############################
# Configurations
##############################

config = {
    'host': '<REST API Endpoint>',
    'rootCAName': '<Root certificate file name>',
    'certificateName': '<Certificate file name>',
    'privateKeyName': '<Private key file name>',
    'clientId': 'drone_alexa_client',
    'port': 8883
}

thing_name = "<THING_NAME>"

device_shadow_update_topic = "$aws/things/" + thing_name + "/shadow/update"
device_shadow_update_accepted_topic = "$aws/things/" + thing_name + "/shadow/update/accepted"
device_shadow_update_rejected_topic = "$aws/things/" + thing_name + "/shadow/update/rejected"


##############################
# Drone connection
##############################

def connect_drone():
    my_drone = tellopy.Tello()
    my_drone.subscribe(my_drone.EVENT_CONNECTED, drone_event_handler)
    my_drone.subscribe(my_drone.EVENT_DISCONNECTED, drone_event_handler)
    my_drone.subscribe(my_drone.EVENT_FLIGHT_DATA, drone_event_handler)
    my_drone.subscribe(my_drone.EVENT_LOG_DATA, drone_event_handler)
    my_drone.connect()
    # my_drone.wait_for_connection(60.0)
    return my_drone


def drone_event_handler(event, sender, data, **args):
    global prev_flight_data, flight_data, log_data, is_drone_connected
    my_drone = sender
    if event is my_drone.EVENT_CONNECTED:
        logging.info("Connected to drone!...")
        is_drone_connected = True
    elif event is my_drone.EVENT_DISCONNECTED:
        logging.warning("Disconnected from drone!...")
        is_drone_connected = False
    elif event is my_drone.EVENT_FLIGHT_DATA:
        if prev_flight_data != str(data):
            logging.info(data)
            prev_flight_data = str(data)
        flight_data = data
    elif event is my_drone.EVENT_LOG_DATA:
        if log_data != str(data):
            logging.debug(data)
            log_data = str(data)
    else:
        logging.debug('event="%s" data=%s' % (event.getname(), str(data)))


##############################
# Telemetry
##############################


def compute_telemetry(raw_data, drone_connected):
    message = {}

    # flight_data= 'ALT:  0 | SPD:  0 | BAT: 94 | WIFI: 90 | CAM:  0 | MODE:  1'
    if raw_data is None or len(raw_data) < 1:
        return message

    telemetry = {}
    tele_arr = raw_data.split('|')
    for element in tele_arr:
        element = element.replace(" ", "")
        kv = element.split(':')
        telemetry[kv[0]] = int(kv[1])
        pass

    message['state'] = {}
    message['state']['reported'] = {}
    for key in telemetry:
        message['state']['reported'][key] = telemetry[key]
        pass
    message['state']['reported']['ISONLINE'] = drone_connected

    return message


def send_telemetry_loop():
    logging.info("Starting telemetry loop " + str(is_drone_connected))
    while is_drone_connected:
        try:
            send_telemetry(prev_flight_data, True)
            time.sleep(500e-3)  # 500ms
        except Exception as e:
            logging.error("Error occurred while sending telemetry " + str(e))
    logging.info("Exiting telemetry loop " + str(is_drone_connected))


def send_telemetry(raw_data, drone_connected):
    message_json = json.dumps(compute_telemetry(raw_data, drone_connected))
    aws_client.publish_message(device_shadow_update_topic, message_json)


##############################
# Callback
##############################

def message_callback(client, userdata, message):
    try:
        topic = message.topic
        rawdata = str(message.payload.decode("utf-8"))
        jsondata = json.loads(rawdata)
        if topic == device_shadow_update_rejected_topic:
            logging.warning("Telemetry message got rejected...")
        else:
            logging.info("Topic: " + message.topic + "\nMessage: " + rawdata)
            create_commands(jsondata, topic)

    except Exception as e:
        logging.error("Error occurred " + str(e))


##################################
# Queue Based Command processing
##################################


def create_commands(jsondata, topic):
    command_delay = 1
    stop_delay = 100e-3  # 100ms
    data = jsondata["value"]
    if topic == "drone/takeoff":
        enqueue_command(lambda: drone.takeoff(), 0)
    elif topic == "drone/land":
        enqueue_command(lambda: drone.land(), 0)
    elif topic == "drone/direction":
        if data == "right":
            enqueue_command(lambda: drone.right(speed), command_delay)
            enqueue_command(lambda: drone.right(0), stop_delay)
        elif data == "left":
            enqueue_command(lambda: drone.left(speed), command_delay)
            enqueue_command(lambda: drone.left(0), stop_delay)
        elif data == "forward":
            enqueue_command(lambda: drone.forward(speed), command_delay)
            enqueue_command(lambda: drone.forward(0), stop_delay)
        elif data == "back":
            enqueue_command(lambda: drone.backward(speed), command_delay)
            enqueue_command(lambda: drone.backward(0), stop_delay)
        elif data == "up":
            enqueue_command(lambda: drone.up(speed), command_delay)
            enqueue_command(lambda: drone.up(0), stop_delay)
        elif data == "down":
            enqueue_command(lambda: drone.down(speed), command_delay)
            enqueue_command(lambda: drone.down(0), stop_delay)
        else:
            pass
    elif topic == "drone/flip":
        enqueue_command(lambda: drone.flip_forward(), 0)
    elif topic == "drone/rotate":
        if data == "left":
            enqueue_command(lambda: drone.counter_clockwise(speed), command_delay)
            enqueue_command(lambda: drone.counter_clockwise(0), stop_delay)
        elif data == "right":
            enqueue_command(lambda: drone.clockwise(speed), command_delay)
            enqueue_command(lambda: drone.clockwise(0), stop_delay)
        else:
            pass
    else:
        pass


# Enqueuing commands
def enqueue_command(command_callback, delay):
    command_object = command(command_callback, delay)
    command_queue.put(command_object)


def process_command():
    while True:
        try:
            command_item = command_queue.get_nowait()
            if command_item is None:
                break
            command_item.command_function()
            time.sleep(command_item.delay)
            command_queue.task_done()
        except queue.Empty:  # ignore empty queue exceptions
            pass
        except Exception as ex:
            logging.error(str(ex))
    logging.info("Command loop finished")


def create_wait_threads():
    global command_queue
    command_queue = queue.Queue()
    command_processor_thread = threading.Thread(target=process_command)  # Define a thread
    command_processor_thread.setDaemon(
        True)  # 'True' means it is a front thread,it would close when the mainloop() closes
    command_processor_thread.start()

    drone_telemetry_thread = threading.Thread(target=send_telemetry_loop)  # Define a thread
    drone_telemetry_thread.setDaemon(
        True)  # 'True' means it is a front thread,it would close when the mainloop() closes
    drone_telemetry_thread.start()
    # Block the thread
    drone_telemetry_thread.join()
    # Block the queue
    command_queue.join()

##############################
# Entry point
##############################


if __name__ == "__main__":

    try:
        aws_client = awsIoTClient(config)
        drone = connect_drone()
        aws_client.subscribe([
            'drone/takeoff',
            'drone/land',
            'drone/direction',
            'drone/rotate',
            'drone/flip'
            # device_shadow_update_rejected_topic
        ],
            message_callback)

        send_telemetry(initial_data, False)
        logging.info('Initial telemetry sent...')

        # Waiting for drone connection...
        while is_drone_connected is False:
            print("Waiting for connection...", end="\r")
            time.sleep(100e-3)
            pass

        create_wait_threads()

        # cancelling command loop
        command_queue.put(None)

        logging.warning('Sending final telemetry sent...')
        send_telemetry(initial_data, False)

    except KeyboardInterrupt:
        logging.warning('KeyboardInterrupt...')
        logging.warning('Sending final telemetry sent...')
        send_telemetry(initial_data, False)
        time.sleep(1)
    except Exception as e:
        # exc_type, exc_value, exc_traceback = sys.exc_info()
        # traceback.print_exception(exc_type, exc_value, exc_traceback)
        logging.error(str(e))
    finally:
        if drone is not None:
            drone.land()
            drone.quit()
        if aws_client is not None:
            aws_client.disconnect()
        logging.info('Exiting program...')
        exit(1)
