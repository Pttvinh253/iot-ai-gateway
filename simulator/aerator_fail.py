# aerator_fail.py
import json, time, random
from datetime import datetime
from paho.mqtt import client as mqtt_client
import argparse

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/tilapia/data"

def aerator_sequence(cycle_index, total):
    # Start from normal DO ~6-7 then drop quickly to ~0.5-2
    base_temp = random.uniform(28,32)
    base_ph = random.uniform(6.5,8.3)
    # linear drop
    do = max(0.4, 6 - (cycle_index/total) * 8)  # will drop below 2 quickly
    turb = random.uniform(10,30)
    return base_temp, base_ph, do, turb

def run(interval=3, total=40):
    client = mqtt_client.Client()
    client.connect(BROKER, PORT)
    print("⚠️  Starting AERATOR FAILURE scenario")
    for i in range(total):
        temp, ph, do, turb = aerator_sequence(i, total)
        payload = {
            "Temperature": round(temp,2),
            "pH": round(ph,2),
            "Dissolved_Oxygen": round(do,2),
            "Turbidity": round(turb,2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"[AERATOR_FAIL] step {i+1}/{total} → {payload}")
        time.sleep(interval)
    print("✅ AERATOR FAILURE scenario finished.")

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=3)
    parser.add_argument("--total", type=int, default=40)
    args=parser.parse_args()
    run(interval=args.interval, total=args.total)
