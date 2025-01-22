import board
import adafruit_si7021
import time
from datetime import datetime
import config_test
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
        logging.error(f'Error polling DHT11 Sensor: {e}')
        time.sleep(1)
        return get_sensor_data()

def send_response():
    filename = str(uuid.uuid4())

    with open(f"{config_test.queue_dir}{filename}.json", "w") as outputjson:
        json.dump(POST_DATA, outputjson)

if __name__ == "__main__":
    if not os.path.isdir(config_test.log_dir):
        os.mkdir(config_test.log_dir)
    logging.basicConfig(filename=config_test.log_dir+"client.log", format='%(asctime)s %(levelname)s %(process)d %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)

    humidity, temperature = get_sensor_data()
    
    for i in range(100000):
        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    
        # format post json
        POST_DATA = {'DeviceID':f'{config_test.deviceID}', 'hash':'pw_test', 'CurrentDateTime':f'{dt_string}', 'Temperature':f'{temperature}','Humidity':f'{humidity}'}
        send_response()
