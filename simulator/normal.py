# normal.py
import json, time, random
from datetime import datetime
from paho.mqtt import client as mqtt_client
import argparse

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/tilapia/data"

def normal_condition():
    # Optimal ranges for tilapia (matching SAFE thresholds)
    # 80% SAFE, 20% WARNING (lâu lâu có biến động nhẹ)
    r = random.random()
    
    if r < 0.70:  # 80% SAFE - điều kiện lý tưởng
        temp = random.uniform(28.5, 31.5)   # 28-32 SAFE zone
        ph   = random.uniform(7.0, 8.0)     # 6.5-8.5 SAFE zone
        do   = random.uniform(6.5, 7.5)     # >= 6.0 SAFE zone
        turb = random.uniform(10, 25)       # <= 30 SAFE zone
    else:  # 20% WARNING - biến động nhẹ (vẫn an toàn nhưng cần theo dõi)
        temp = random.uniform(26.5, 33.5)   # Hơi lệch khỏi SAFE zone
        ph   = random.uniform(6.3, 8.7)     # Gần ngưỡng SAFE
        do   = random.uniform(5.5, 6.2)     # Dưới ngưỡng SAFE một chút
        turb = random.uniform(28, 40)       # Hơi đục
    
    return temp, ph, do, turb

def run(interval=5, total=30):
    client = mqtt_client.Client()
    client.connect(BROKER, PORT)

    print("🌤️  Starting NORMAL scenario")

    for i in range(total):
        temp, ph, do, turb = normal_condition()
        payload = {
            "Temperature": round(temp,2),
            "pH": round(ph,2),
            "Dissolved_Oxygen": round(do,2),
            "Turbidity": round(turb,2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "demo_mode": True  # Flag để Gateway không dùng prediction risk
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"[NORMAL] step {i+1}/{total} → {payload}")
        time.sleep(interval)

    print("✅ NORMAL scenario finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--total", type=int, default=30)
    args = parser.parse_args()
    run(interval=args.interval, total=args.total)
