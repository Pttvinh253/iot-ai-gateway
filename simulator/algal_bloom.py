# algal_bloom.py
import json, time, random
from datetime import datetime
from paho.mqtt import client as mqtt_client
import argparse

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/tilapia/data"

def algal_step(step):
    hour = datetime.now().hour
    temp = random.uniform(28,33)
    ph = random.uniform(7.5,9.0)
    if 8 <= hour <= 16:
        do = random.uniform(7.5, 12.0)  # photosynthesis
    else:
        do = random.uniform(1.0, 3.5)   # respiration at night
    turb = random.uniform(30,75)
    return temp, ph, do, turb

def run(interval=5, total=80):
    client = mqtt_client.Client()
    client.connect(BROKER, PORT)
    print("⚠️  Starting ALGAL BLOOM scenario")
    for i in range(total):
        temp, ph, do, turb = algal_step(i)
        payload = {
            "Temperature": round(temp,2),
            "pH": round(ph,2),
            "Dissolved_Oxygen": round(do,2),
            "Turbidity": round(turb,2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"[ALGAL_BLOOM] step {i+1}/{total} → {payload}")
        time.sleep(interval)
    print("✅ ALGAL BLOOM scenario finished.")

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--total", type=int, default=80)
    args=parser.parse_args()
    run(interval=args.interval, total=args.total)
