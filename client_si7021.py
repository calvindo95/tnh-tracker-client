import board
import adafruit_si7021
import time
from datetime import datetime
import config
import requests
import json
import logging
import uuid
import os

sensor = adafruit_si7021.SI7021(board.I2C())
headers = {'Content-Type': 'application/json'}

def get_sensor_data():
    try:
        humidity, temperature = sensor.relative_humidity, sensor.temperature
        tempF = round(temperature*(9/5)+32, 2)

        return humidity, tempF
    except Exception as e:
        logging.error(f"Error polling SI7021 Sensor: {e}")
        time.sleep(1)
        return get_sensor_data()

def send_response():
    response = ''
    
    try:
        response = requests.post(config.httpserverip, data=json.dumps(POST_DATA), headers=headers)
        
        if response.text != "Received data value: 0":
            logging.warning(f'failed - |{response.text}|')
            return 1
        else:
            logging.info(f'Successfully posted data')

            for json_file in os.listdir(config.queue_dir):
                logging.info(f'Attempting to post queue data {config.queue_dir+json_file}')
                with open(config.queue_dir+json_file, "r") as open_json:
                    json_obj = json.load(open_json)

                response = requests.post(config.httpserverip, data=json.dumps(json_obj), headers=headers)
                if response.text != "Received data value: 0":
                    logging.warning(f'failed - |{response.text}|')
                    return 1
                else:
                    logging.info(f'Successfully posted queue data')
                    os.remove(config.queue_dir+json_file)
            return 0
        
    except FileNotFoundError as e:
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
    logging.basicConfig(filename=config.log_dir+"client.log", format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', encoding='utf-8', level=logging.INFO)
    
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")

    humidity, temperature = get_sensor_data()
    
    # format post json
    POST_DATA = {'DeviceID':f'{config.deviceID}', 'hash':'pw_test', 'CurrentDateTime':f'{dt_string}', 'Temperature':f'{temperature}','Humidity':f'{humidity}'}
    send_response()