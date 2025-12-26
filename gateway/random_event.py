"""
===========================================================
       TILAPIA SMART AQUACULTURE – EVENT SIMULATOR
       (Professional Version for Research & Demo)
===========================================================

Mô phỏng 5 kịch bản ảnh hưởng đến cá rô phi:
 - Aerator Failure      → DO giảm về 0.5–2 mg/L
 - Heavy Rain           → Temp giảm, pH biến động, Turb tăng
 - Overfeeding          → Turb tăng từ từ, DO giảm dần
 - Algal Bloom          → DO tăng mạnh ban ngày, giảm mạnh ban đêm
 - Sensor Drift         → Giá trị lệch dần theo thời gian

Cấu trúc mô phỏng:
 - Bình thường chạy NORMAL MODE
 - Có 12% cơ hội kích hoạt event đặc biệt
 - Mỗi event kéo dài: EVENT_DURATION = 40 cycles (≈ 200s)
===========================================================
"""

import json
import random
import time
from datetime import datetime
from paho.mqtt import client as mqtt_client

# ==============================
# MQTT CONFIG
# ==============================
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/tilapia/data"

# ==============================
# SIMULATION CONFIG
# ==============================
EVENT_PROB = 0.0               # 0% cơ hội kích hoạt event (chỉ SAFE)
EVENT_DURATION = 40            # 40 chu kỳ → ~200 giây
current_event = None
event_step = 0

sensor_bias = 0.0              # cho sensor drift


# =========================================================
#                NORMAL ENVIRONMENT (Tilapia)
# =========================================================
def normal_condition():
    """Điều kiện lý tưởng cá rô phi."""
    temp = random.uniform(27, 32)
    ph = random.uniform(6.5, 8.4)
    do = random.uniform(5.5, 8.0)
    turb = random.uniform(5, 25)
    return temp, ph, do, turb


# =========================================================
#                   E V E N T   M O D E S
# =========================================================
def event_aerator_fail(step):
    """Sục khí hỏng → DO giảm nguy hiểm."""
    temp = random.uniform(28, 32)
    ph = random.uniform(6.5, 8.3)
    do = max(0.5, 6 - step * 0.15)  # giảm dần 6 → ~1 mg/L
    turb = random.uniform(10, 30)
    return temp, ph, do, turb


def event_heavy_rain(step):
    """Mưa lớn → Temp giảm, Turb tăng mạnh, pH dao động."""
    temp = random.uniform(22.5, 27.0)
    ph = random.uniform(5.8, 7.2) + random.uniform(-0.4, 0.4)
    do = random.uniform(4.0, 7.0)
    turb = random.uniform(25, 60)
    return temp, ph, do, turb


def event_overfeeding(step):
    """Cho ăn quá mức → Turb tăng từ từ, DO giảm dần."""
    temp = random.uniform(27, 32)
    ph = random.uniform(6.4, 8.5)
    do = max(1.5, 7 - step * 0.1)
    turb = 20 + step * 1.2     # tăng tuyến tính
    return temp, ph, do, turb


def event_algal_bloom(step):
    """Tảo nở hoa → DO tăng mạnh ban ngày, giảm mạnh ban đêm."""
    hour = datetime.now().hour
    temp = random.uniform(28, 33)
    ph = random.uniform(7.5, 9.2)

    if 8 <= hour <= 16:        # Ban ngày
        do = random.uniform(7, 12)
    else:                      # Ban đêm
        do = random.uniform(1.2, 3.5)

    turb = random.uniform(30, 70)
    return temp, ph, do, turb


def event_sensor_drift(step):
    """Cảm biến bị lệch dần theo thời gian."""
    global sensor_bias
    sensor_bias += 0.01
    temp, ph, do, turb = normal_condition()
    return temp + sensor_bias, ph, do, turb


EVENTS = {
    "aerator_fail": event_aerator_fail,
    "heavy_rain": event_heavy_rain,
    "overfeeding": event_overfeeding,
    "algal_bloom": event_algal_bloom,
    "sensor_drift": event_sensor_drift
}


# =========================================================
#             EVENT HANDLING & STATE MACHINE
# =========================================================
def generate_data():
    global current_event, event_step

    # If currently running an event
    if current_event:
        print(f"🔥 EVENT ACTIVE → {current_event.upper()} | step {event_step}/{EVENT_DURATION}")
        func = EVENTS[current_event]
        values = func(event_step)
        event_step += 1

        if event_step > EVENT_DURATION:
            print(f"✅ EVENT ENDED → {current_event}\n")
            current_event = None
            event_step = 0

        return values

    # No event → maybe trigger new one?
    if random.random() < EVENT_PROB:
        current_event = random.choice(list(EVENTS.keys()))
        event_step = 0
        print(f"\n⚠️ EVENT STARTED → {current_event.upper()} !!!\n")
        return EVENTS[current_event](event_step)

    # Default mode
    print("🌿 Normal environment – no events...")
    return normal_condition()


# =========================================================
#                     MQTT SETUP
# =========================================================
client = mqtt_client.Client()

def connect_mqtt():
    print("🔌 Connecting to MQTT Broker...")
    client.connect(BROKER, PORT)
    print("✅ MQTT Connected!")
    return client


# =========================================================
#                     MAIN LOOP
# =========================================================
def run():
    connect_mqtt()

    while True:
        temp, ph, do, turb = generate_data()

        payload = {
            "Temperature": round(temp, 2),
            "pH": round(ph, 2),
            "Dissolved_Oxygen": round(do, 2),
            "Turbidity": round(turb, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        client.publish(TOPIC, json.dumps(payload))
        print("📤 Published:", payload)
        print("---------------------------------------------------\n")

        time.sleep(5)   # 5s mỗi data point


if __name__ == "__main__":
    run()
