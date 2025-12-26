# heavy_rain.py
import json, time, random
from datetime import datetime
from paho.mqtt import client as mqtt_client
import argparse

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/tilapia/data"

def rain_pattern(step, total):
    # strong turbidity spike, temp drop, pH jitter
    temp = random.uniform(22.5, 27.0)
    ph = round(random.uniform(5.6, 7.4) + random.uniform(-0.3, 0.3), 2)
    do = random.uniform(4.0, 7.0)
    # turbidity high initially then taper
    turb = 60 - (step/total)*25 + random.uniform(-5,5)
    return temp, ph, do, turb

def run(interval=4, total=50):
    client = mqtt_client.Client()
    client.connect(BROKER, PORT)
    print("⚠️  Starting HEAVY RAIN scenario")
    for i in range(total):
        temp, ph, do, turb = rain_pattern(i, total)
        payload = {
            "Temperature": round(temp,2),
            "pH": round(ph,2),
            "Dissolved_Oxygen": round(do,2),
            "Turbidity": round(turb,2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"[HEAVY_RAIN] step {i+1}/{total} → {payload}")
        time.sleep(interval)
    print("✅ HEAVY RAIN scenario finished.")

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=4)
    parser.add_argument("--total", type=int, default=50)
    args=parser.parse_args()
    run(interval=args.interval, total=args.total)
