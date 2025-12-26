"""
Đọc file test.csv và publish lên MQTT
Thay thế ESP32 fetch qua HTTP (tránh Firewall)
"""
import paho.mqtt.client as mqtt
import pandas as pd
import json
import time

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "iot/tilapia/data"
CSV_FILE = "test.csv"

def publish_csv():
    print(f"📖 Đọc {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    print(f"🔌 Kết nối MQTT broker: {BROKER}:{PORT}")
    client = mqtt.Client("laptop-csv-simulator")
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    
    print(f"📤 Bắt đầu publish {len(df)} dòng lên topic: {TOPIC}\n")
    
    for idx, row in df.iterrows():
        payload = {
            "Temperature": float(row['Temp']),
            "Dissolved_Oxygen": float(row['DO']),
            "pH": float(row['pH']),
            "Turbidity": float(row['Turbidity']),
            "timestamp": str(row['DateTime'])
        }
        
        msg = json.dumps(payload)
        result = client.publish(TOPIC, msg)
        
        if result.rc == 0:
            print(f"✅ [{idx+1}/{len(df)}] {msg}")
        else:
            print(f"❌ [{idx+1}/{len(df)}] Publish failed!")
        
        time.sleep(3)  # 3 giây mỗi dòng
    
    client.loop_stop()
    client.disconnect()
    
    print(f"\n✅ Hoàn thành! Đã gửi {len(df)} dòng.")
    print("⏳ Chờ 5 giây rồi lặp lại...\n")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CSV to MQTT Publisher (Thay thế ESP32 HTTP)")
    print("=" * 60)
    print("📝 Chức năng: Đọc test.csv và publish lên MQTT")
    print("🎯 Gateway sẽ nhận data như thể từ ESP32")
    print("=" * 60)
    print()
    
    while True:
        try:
            publish_csv()
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n\n🛑 Dừng chương trình")
            break
        except FileNotFoundError:
            print(f"❌ Không tìm thấy file {CSV_FILE}")
            print("💡 Đảm bảo chạy script trong thư mục data/")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            time.sleep(5)
