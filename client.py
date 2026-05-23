import board
import time
from datetime import datetime
import config
import requests
import json
import logging
import uuid
import os
from logging.handlers import RotatingFileHandler

headers = {'Content-Type': 'application/json'}
sensor = None
sensor_name = None

log_name = "client.log"

def init_sensor():
    i2c = board.I2C()
    global sensor, sensor_name
    
    try:
        import adafruit_si7021
        sensor = adafruit_si7021.SI7021(i2c)
        sensor_name = 'SI7021'
        return
    except Exception:
        pass

    try:
        import adafruit_sht31d
        sensor = adafruit_sht31d.SHT31D(i2c)
        sensor_name = 'SHT31D'
        return
    except Exception:
        pass

    raise RuntimeError("No supported sensor (SI7021 or SHT31D) found on I2C bus")

def get_sensor_data():
    try:
        humidity, temperature = sensor.relative_humidity, sensor.temperature
        tempF = round(temperature * (9/5) + 32, 2)
        return humidity, tempF
    except Exception as e:
        logging.error(f"Error polling {sensor_name} sensor: {e}")
        time.sleep(1)
        return get_sensor_data()

def send_response():
    try:
        response = requests.post(config.httpserverip, data=json.dumps(POST_DATA), headers=headers)

        if response.text != "Received data value: 0\n":
            logging.warning(f'failed - |{response.text}|')
            return 1
        else:
            logging.info('Successfully posted data')

            for json_file in os.listdir(config.queue_dir):
                if os.path.getsize(config.queue_dir + json_file) == 0:
                    logging.warning(f'Removing empty queue file {config.queue_dir + json_file}')
                    os.remove(config.queue_dir + json_file)
                    continue
                logging.info(f'Attempting to post queue data {config.queue_dir + json_file}')
                with open(config.queue_dir + json_file, "r") as open_json:
                    json_obj = json.load(open_json)

                response = requests.post(config.httpserverip, data=json.dumps(json_obj), headers=headers)
                if response.text != "Received data value: 0\n":
                    logging.warning(f'failed - |{response.text}|')
                    return 1
                else:
                    logging.info('Successfully posted queue data')
                    os.remove(config.queue_dir + json_file)
            return 0

    except FileNotFoundError:
        os.mkdir(config.queue_dir)
    except Exception as e:
        filename = str(uuid.uuid4())
        logging.error(f'Error posting request: {e}, saving to {config.queue_dir}{filename}.json')

        if not os.path.isdir(config.queue_dir):
            os.mkdir(config.queue_dir)

        with open(f"{config.queue_dir}{filename}.json", "w") as outputjson:
            json.dump(POST_DATA, outputjson)

if __name__ == "__main__":
    if not os.path.isdir(config.log_dir):
        os.mkdir(config.log_dir)
    handler = RotatingFileHandler(config.log_dir + f"{log_name}", maxBytes=1024 * 1024, backupCount=5)
    if os.path.getsize(config.log_dir + f"{log_name}") > 1024 * 1024 if os.path.exists(config.log_dir + "gen.log") else False:
        handler.doRollover()
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(process)d %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8',
        level=logging.INFO,
        handlers=[handler]
    )

    init_sensor()
    logging.info(f'Using sensor: {sensor_name}')

    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

    humidity, temperature = get_sensor_data()

    POST_DATA = {'DeviceID': f'{config.deviceID}', 'hash': 'pw_test', 'CurrentDateTime': f'{dt_string}', 'Temperature': f'{temperature}', 'Humidity': f'{humidity}'}
    send_response()
