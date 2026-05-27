import argparse
import json
import requests
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import config_test

headers = {'Content-Type': 'application/json'}

SAMPLE_PAYLOAD = {
    'DeviceID': str(config_test.deviceID),
    'hash': 'pw_test',
    'CurrentDateTime': '',
    'Temperature': '72.5',
    'Humidity': '45.0'
}

success_count = 0
fail_count = 0
lock = threading.Lock()
stop_event = threading.Event()

def post_request():
    global success_count, fail_count
    while not stop_event.is_set():
        payload = {**SAMPLE_PAYLOAD, 'CurrentDateTime': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        try:
            response = requests.post(config_test.httpserverip, data=json.dumps(payload), headers=headers, timeout=5)
            with lock:
                if response.text == "Received data value: 0\n":
                    success_count += 1
                else:
                    fail_count += 1
        except Exception:
            with lock:
                fail_count += 1

def main():
    parser = argparse.ArgumentParser(description='Load test the TNH tracker REST endpoint')
    parser.add_argument('--threads', type=int, default=10, help='Number of concurrent threads (default: 10)')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds (default: 30)')
    args = parser.parse_args()

    print(f"Starting load test: {args.threads} threads for {args.duration}s → {config_test.httpserverip}")
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        for _ in range(args.threads):
            executor.submit(post_request)
        time.sleep(args.duration)
        stop_event.set()

    elapsed = time.time() - start
    total = success_count + fail_count
    rps = total / elapsed if elapsed > 0 else 0

    print(f"\n--- Results ---")
    print(f"Duration:  {elapsed:.2f}s")
    print(f"Total:     {total}")
    print(f"Success:   {success_count}")
    print(f"Failed:    {fail_count}")
    print(f"Req/sec:   {rps:.1f}")

if __name__ == "__main__":
    main()
