# sensor_drift.py
import json, time, random
from datetime import datetime
from paho.mqtt import client as mqtt_client
import argparse

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/tilapia/data"

bias_temp = 0.0
bias_ph = 0.0
bias_do = 0.0

def drift_step(step):
    global bias_temp, bias_ph, bias_do
    # drift increases slowly each step
    bias_temp += 0.01 * random.random()
    bias_ph += 0.005 * random.random()
    bias_do += 0.02 * random.random()

    temp = random.uniform(27,32) + bias_temp
    ph = random.uniform(6.5,8.4) + bias_ph
    do = random.uniform(5.5,8.0) - bias_do  # drift tends to bias DO downward
    turb = random.uniform(5,25)
    return temp, ph, do, turb

def run(interval=5, total=200):
    client = mqtt_client.Client()
    client.connect(BROKER, PORT)
    print("⚠️  Starting SENSOR DRIFT scenario")
    for i in range(total):
        temp, ph, do, turb = drift_step(i)
        payload = {
            "Temperature": round(temp,2),
            "pH": round(ph,2),
            "Dissolved_Oxygen": round(do,2),
            "Turbidity": round(turb,2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"[SENSOR_DRIFT] step {i+1}/{total} → {payload}")
        time.sleep(interval)
    print("✅ SENSOR DRIFT scenario finished.")

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--total", type=int, default=200)
    args=parser.parse_args()
    run(interval=args.interval, total=args.total)
