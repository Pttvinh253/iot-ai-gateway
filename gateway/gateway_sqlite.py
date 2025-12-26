import json
import pandas as pd
import joblib
from datetime import datetime, timedelta
from paho.mqtt import client as mqtt_client
from prepare_features import build_feature_row
import sys
from pathlib import Path
import importlib.util
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add parent directory to path for config and logger
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import config and logger
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, DATABASE_PATH, 
    MODEL_PATHS, Thresholds, get_config_summary,
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, ALERT_INTERVAL_MIN
)
from logger import get_gateway_logger

# Setup logger
logger = get_gateway_logger()

# Import database module
DB_CONFIG_PATH = PROJECT_ROOT / "database" / "db_config.py"
spec = importlib.util.spec_from_file_location("db_config", DB_CONFIG_PATH)
db_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_config)

insert_sensor_data = db_config.insert_sensor_data
init_database = db_config.init_database

logger.info("=== Gateway Starting ===")
logger.info(f"Configuration: {get_config_summary()}")

# ------------------ LOAD MODELS ------------------
logger.info("Loading ML models...")
models = {}
scalers_Y = {}

# Mapping for model and scaler filenames
MODEL_FILE_MAP = {
    "temperature": ("model_Temperature_6h.pkl", "scaler_Temperature.pkl", "Temperature"),
    "ph": ("model_pH_6h.pkl", "scaler_pH.pkl", "pH"),
    "do": ("model_Dissolved_Oxygen_6h.pkl", "scaler_Dissolved_Oxygen.pkl", "Dissolved_Oxygen"),
    "turbidity": ("model_Turbidity_6h.pkl", "scaler_Turbidity.pkl", "Turbidity")
}

try:
    for param in MODEL_FILE_MAP.keys():
        model_file, scaler_file, display_name = MODEL_FILE_MAP[param]
        
        model_path = PROJECT_ROOT / "models" / model_file
        scaler_path = PROJECT_ROOT / "models" / scaler_file
        
        if model_path.exists():
            models[display_name] = joblib.load(str(model_path))
            logger.info(f"✓ Loaded model: {param} -> {display_name}")
        else:
            logger.warning(f"✗ Model not found: {model_path}")
        
        if scaler_path.exists():
            scalers_Y[display_name] = joblib.load(str(scaler_path))
            logger.info(f"✓ Loaded scaler: {param}")
        else:
            logger.warning(f"✗ Scaler not found: {scaler_path}")
    
    logger.info(f"Models loaded: {len(models)}/4")
except Exception as e:
    logger.error(f"Error loading models: {e}")
    raise

# Lịch sử 24h gần nhất
history = pd.DataFrame(columns=[
    "Temperature", "pH", "Dissolved_Oxygen", "Turbidity", "timestamp"
])

# Email alert tracking
last_email_sent = None


# ------------------ PHÂN LOẠI RỦI RO ------------------
def classify_risk(temp, ph, do, turb):
    """
    Risk classification for tilapia aquaculture using config thresholds.
    
    Danger: Any critical threshold violated
    Safe: All parameters in optimal range
    Warning: Between Safe and Danger
    """
    # DANGER: Critical thresholds
    if (do < Thresholds.DO_MIN_DANGER or 
        ph < Thresholds.PH_MIN_DANGER or ph > Thresholds.PH_MAX_DANGER or 
        temp < Thresholds.TEMP_MIN_DANGER or temp > Thresholds.TEMP_MAX_DANGER or 
        turb > Thresholds.TURB_MAX_WARNING):
        return "Danger"
    
    # SAFE: Optimal conditions for tilapia growth
    if (Thresholds.TEMP_MIN_SAFE <= temp <= Thresholds.TEMP_MAX_SAFE and 
        Thresholds.PH_MIN_SAFE <= ph <= Thresholds.PH_MAX_SAFE and 
        do >= Thresholds.DO_MIN_SAFE and 
        turb <= Thresholds.TURB_MAX_SAFE):
        return "Safe"
    
    # WARNING: Suboptimal but not critical
    return "Warning"


def merge_risks(sensor_risk, pred_risk):
    """Kết hợp cảm biến + dự đoán theo hướng C."""
    if sensor_risk == "Danger" or pred_risk == "Danger":
        return "Danger"
    if sensor_risk == "Warning" or pred_risk == "Warning":
        return "Warning"
    return "Safe"


def send_danger_email(data, sensor_risk, pred_risk, final_risk):
    """Send email alert when Danger detected"""
    global last_email_sent
    
    # Check if email is configured
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        logger.warning("📧 Email not configured, skipping alert")
        return False
    
    # Check alert interval (avoid spam)
    now = datetime.now()
    if last_email_sent:
        time_since_last = (now - last_email_sent).total_seconds() / 60
        if time_since_last < ALERT_INTERVAL_MIN:
            logger.debug(f"📧 Skipping email (sent {time_since_last:.1f}min ago, interval: {ALERT_INTERVAL_MIN}min)")
            return False
    
    try:
        # Create email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = "🚨 CẢNH BÁO NGUY HIỂM - Hệ Thống Nuôi Cá Rô Phi"
        
        # Email body
        body = f"""
🚨 CẢNH BÁO: Phát hiện tình trạng NGUY HIỂM!

📍 Thời gian: {data['timestamp']}
🎯 Trạng thái cuối: {final_risk}

📊 Dữ Liệu Cảm Biến Hiện Tại:
  • Nhiệt độ: {data['Temperature']}°C
  • pH: {data['pH']}
  • Oxy hòa tan (DO): {data['Dissolved_Oxygen']} mg/L
  • Độ đục: {data['Turbidity']} NTU
  • Đánh giá: {sensor_risk}

⚠️ Khuyến Nghị Hành Động:
  1. Kiểm tra ngay thiết bị sục khí (DO thấp)
  2. Kiểm tra pH và điều chỉnh nếu cần
  3. Kiểm tra nhiệt độ nước
  4. Xem dashboard: http://localhost:8501

---
Email tự động từ IoT Gateway
        """
        
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # Send via Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        
        last_email_sent = now
        logger.info(f"📧 Email alert sent to {EMAIL_RECEIVER}")
        return True
        
    except Exception as e:
        logger.error(f"📧 Failed to send email: {e}")
        return False


# ------------------ MQTT HANDLE ------------------
def on_message(client, userdata, msg):
    global history

    try:
        data = json.loads(msg.payload.decode())
        logger.debug(f"Received MQTT message: {data}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return

    # Sensor risk – REALTIME
    risk_sensor = classify_risk(
        data["Temperature"],
        data["pH"],
        data["Dissolved_Oxygen"],
        data["Turbidity"]
    )
    
    # Kiểm tra demo_mode (không dùng prediction risk)
    demo_mode = data.get("demo_mode", False)

    # Build X row for prediction
    X_scaled, history = build_feature_row(history, data)

    if X_scaled is None:
        logger.info("⏳ Insufficient history (need 24h) for predictions")
        predictions = {
            "Temperature": None,
            "pH": None,
            "Dissolved_Oxygen": None,
            "Turbidity": None
        }
        risk_pred = "Unknown"
        final_risk = risk_sensor  # chỉ đánh giá bằng sensor
    else:
        # Make predictions
        predictions = {}
        for col, model in models.items():
            scaled_pred = model.predict(X_scaled).reshape(-1, 1)
            real_pred = scalers_Y[col].inverse_transform(scaled_pred)[0][0]
            predictions[col] = round(float(real_pred), 3)

        # Risk from prediction
        risk_pred = classify_risk(
            predictions["Temperature"],
            predictions["pH"],
            predictions["Dissolved_Oxygen"],
            predictions["Turbidity"]
        )

        # Merge IoT + AI (hoặc chỉ dùng sensor risk nếu demo_mode)
        if demo_mode:
            final_risk = risk_sensor  # Demo mode: chỉ dùng sensor risk
            logger.info("🎯 DEMO MODE: Using sensor risk only")
        else:
            final_risk = merge_risks(risk_sensor, risk_pred)

    # -------- LOG OUT ----------
    logger.info(f"📡 Sensor: T={data['Temperature']}°C pH={data['pH']} DO={data['Dissolved_Oxygen']} Turb={data['Turbidity']} | Risk={risk_sensor}")
    if predictions["Temperature"]:
        logger.info(f"🤖 Pred(6h): T={predictions['Temperature']} pH={predictions['pH']} DO={predictions['Dissolved_Oxygen']} | Risk={risk_pred}")
    logger.info(f"🚨 FINAL: {final_risk}")
    
    # -------- Send Email Alert if Danger ----------
    if final_risk == "Danger":
        logger.warning("⚠️ DANGER detected! Sending email alert...")
        send_danger_email(data, risk_sensor, risk_pred, final_risk)

    # -------- Save to SQLite Database ----------
    row = {
        "timestamp": data["timestamp"],
        "temp": data["Temperature"],
        "ph": data["pH"],
        "do": data["Dissolved_Oxygen"],
        "turbidity": data["Turbidity"],
        "pred_temp": predictions["Temperature"],
        "pred_ph": predictions["pH"],
        "pred_do": predictions["Dissolved_Oxygen"],
        "pred_turb": predictions["Turbidity"],
        "sensor_risk": risk_sensor,
        "pred_risk": risk_pred,
        "status": final_risk
    }

    try:
        record_id = insert_sensor_data(row)
        print(f"💾 Saved to database (ID: {record_id})")
    except Exception as e:
        logger.error(f"❌ Database error: {e}")


# ------------------ MQTT ------------------
def connect_mqtt():
    logger.info(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1)
    client.connect(MQTT_BROKER, MQTT_PORT)
    logger.info(f"✅ Connected to {MQTT_BROKER}:{MQTT_PORT}")
    return client


def run():
    # Initialize database on startup
    logger.info("🔧 Initializing database...")
    init_database()
    logger.info(f"✅ Database ready: {DATABASE_PATH}")
    
    client = connect_mqtt()
    client.subscribe(MQTT_TOPIC)
    client.on_message = on_message
    logger.info(f"🚀 Gateway running | Topic: {MQTT_TOPIC}")
    logger.info("💾 Data will be saved to SQLite database")
    logger.info("⏳ Waiting for MQTT messages...")
    client.loop_forever()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info("⏹️ Gateway stopped by user")
    except Exception as e:
        logger.critical(f"💥 Gateway crashed: {e}", exc_info=True)
