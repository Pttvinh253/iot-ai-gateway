"""
Script để test email alert - Gửi dữ liệu DANGER qua MQTT
Chạy script này để tạo tình huống nguy hiểm và test email
"""

import json
import time
from datetime import datetime
from paho.mqtt import client as mqtt_client
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC

def send_danger_data():
    """Gửi dữ liệu DANGER để test email alert"""
    
    client = mqtt_client.Client()
    
    print(f"🔌 Connecting to MQTT: {MQTT_BROKER}:{MQTT_PORT}")
    client.connect(MQTT_BROKER, MQTT_PORT)
    
    # Dữ liệu DANGER - DO cực thấp (1.0 mg/L < 2.0)
    danger_data = {
        "Temperature": 24.5,  # Hơi thấp
        "pH": 5.8,            # pH thấp nguy hiểm
        "Dissolved_Oxygen": 1.0,  # DO cực thấp - NGUY HIỂM!
        "Turbidity": 65.0,    # Độ đục cao
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    payload = json.dumps(danger_data)
    
    print("\n🚨 SENDING DANGER DATA:")
    print(f"   Temperature: {danger_data['Temperature']}°C (Low)")
    print(f"   pH: {danger_data['pH']} (Too Low - Danger!)")
    print(f"   DO: {danger_data['Dissolved_Oxygen']} mg/L (Critical Low - Danger!)")
    print(f"   Turbidity: {danger_data['Turbidity']} NTU (High)")
    print(f"\n📤 Publishing to topic: {MQTT_TOPIC}")
    
    client.publish(MQTT_TOPIC, payload)
    
    print("✅ Danger data sent!")
    print("📧 Check Gateway logs for email sending status")
    print(f"📬 Email should be sent to: {danger_data['timestamp']}")
    
    client.disconnect()

if __name__ == "__main__":
    print("="*60)
    print("🧪 EMAIL ALERT TEST - DANGER SCENARIO")
    print("="*60)
    print("\n⚠️  This script will send DANGER data to trigger email alert")
    print("Make sure Gateway is running before executing!")
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")
    
    try:
        time.sleep(3)
        send_danger_data()
    except KeyboardInterrupt:
        print("\n❌ Test cancelled")
