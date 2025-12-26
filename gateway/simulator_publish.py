import json
import random
import time
from datetime import datetime
from paho.mqtt import client as mqtt_client
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, Thresholds
from logger import get_simulator_logger

logger = get_simulator_logger()

# ----- Hàm tạo dữ liệu giả sensor -----
def generate_data():
    """Tạo dữ liệu giả lập đa trạng thái:
    - SAFE: DO 6-8 mg/L, temp 28-32, pH 6.5-8.5 (khoảng 40%)
    - WARNING: giá trị trung gian (khoảng 50%)
    - DANGER: DO thấp <2 hoặc temp lệch nhiều (khoảng 10%)
    """
    r = random.random()

    if r < 0.10:  # Danger scenario
        temperature = round(random.uniform(22.0, 37.0), 2)
        ph = round(random.uniform(5.5, 9.5), 2)
        do = round(random.uniform(0.4, 1.8), 2)
    elif r < 0.50:  # Safe scenario
        temperature = round(random.uniform(Thresholds.TEMP_MIN_SAFE, Thresholds.TEMP_MAX_SAFE), 2)
        ph = round(random.uniform(Thresholds.PH_MIN_SAFE, Thresholds.PH_MAX_SAFE), 2)
        do = round(random.uniform(Thresholds.DO_MIN_SAFE, 7.8), 2)
    else:  # Warning scenario
        temperature = round(random.uniform(26.0, 34.0), 2)
        ph = round(random.uniform(6.2, 8.7), 2)
        do = round(random.uniform(2.0, 6.1), 2)

    turb = round(random.uniform(5.0, 40.0), 2)

    payload = {
        "Temperature": temperature,
        "pH": ph,
        "Dissolved_Oxygen": do,
        "Turbidity": turb,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return payload

# ----- MQTT -----
client = mqtt_client.Client()

def connect_mqtt():
    logger.info(f"🔌 Connecting to MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    client.connect(MQTT_BROKER, MQTT_PORT)
    logger.info("✅ Connected to MQTT!")
    return client

def run():
    logger.info("=== Simulator Starting ===")
    logger.info(f"Publishing to topic: {MQTT_TOPIC}")
    connect_mqtt()

    message_count = 0
    while True:
        msg = generate_data()
        payload = json.dumps(msg)

        client.publish(MQTT_TOPIC, payload)
        message_count += 1
        logger.info(f"📤 Published #{message_count}: T={msg['Temperature']}°C pH={msg['pH']} DO={msg['Dissolved_Oxygen']} Turb={msg['Turbidity']}")

        time.sleep(3)  # Publish every 3 seconds

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info("❌ Simulator stopped by user")
    except Exception as e:
        logger.critical(f"💥 Simulator crashed: {e}")
        raise
