# overfeeding.py
import json, time, random
from datetime import datetime
from paho.mqtt import client as mqtt_client
import argparse

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/tilapia/data"

def overfeeding_step(step):
    temp = random.uniform(27,32)
    ph = random.uniform(6.4,8.3)
    do = max(1.0, 7 - step*0.08)  # slow decline
    turb = 15 + step * 0.8 + random.uniform(-1,2)
    return temp, ph, do, turb

def run(interval=5, total=60):
    client = mqtt_client.Client()
    client.connect(BROKER, PORT)
    print("⚠️  Starting OVERFEEDING scenario")
    for i in range(total):
        temp, ph, do, turb = overfeeding_step(i)
        payload = {
            "Temperature": round(temp,2),
            "pH": round(ph,2),
            "Dissolved_Oxygen": round(do,2),
            "Turbidity": round(turb,2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"[OVERFEEDING] step {i+1}/{total} → {payload}")
        time.sleep(interval)
    print("✅ OVERFEEDING scenario finished.")

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--total", type=int, default=60)
    args=parser.parse_args()
    run(interval=args.interval, total=args.total)
