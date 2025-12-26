# config.py - Centralized Configuration Management
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)

# ==================== MQTT Configuration ====================
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/tilapia/data")

# ==================== Database Configuration ====================
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "database/iot_data.db")

# ==================== Email Configuration ====================
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")
ALERT_INTERVAL_MIN = int(os.getenv("ALERT_INTERVAL_MIN", "10"))

# ==================== Thresholds Configuration ====================
class Thresholds:
    # Temperature (°C)
    TEMP_MIN_SAFE = float(os.getenv("TEMP_MIN_SAFE", "28.0"))
    TEMP_MAX_SAFE = float(os.getenv("TEMP_MAX_SAFE", "32.0"))
    TEMP_MIN_DANGER = float(os.getenv("TEMP_MIN_DANGER", "22.0"))
    TEMP_MAX_DANGER = float(os.getenv("TEMP_MAX_DANGER", "37.0"))
    
    # pH
    PH_MIN_SAFE = float(os.getenv("PH_MIN_SAFE", "6.5"))
    PH_MAX_SAFE = float(os.getenv("PH_MAX_SAFE", "8.5"))
    PH_MIN_DANGER = float(os.getenv("PH_MIN_DANGER", "5.5"))
    PH_MAX_DANGER = float(os.getenv("PH_MAX_DANGER", "9.5"))
    
    # Dissolved Oxygen (mg/L)
    DO_MIN_SAFE = float(os.getenv("DO_MIN_SAFE", "6.0"))
    DO_MIN_WARNING = float(os.getenv("DO_MIN_WARNING", "4.0"))
    DO_MIN_DANGER = float(os.getenv("DO_MIN_DANGER", "2.0"))
    
    # Turbidity (NTU)
    TURB_MAX_SAFE = float(os.getenv("TURB_MAX_SAFE", "30.0"))
    TURB_MAX_WARNING = float(os.getenv("TURB_MAX_WARNING", "50.0"))

# ==================== Logging Configuration ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = LOGS_DIR
LOG_FILE_MAX_BYTES = int(os.getenv("LOG_FILE_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# ==================== Dashboard Configuration ====================
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))
DASHBOARD_REFRESH_SEC = int(os.getenv("DASHBOARD_REFRESH_SEC", "5"))
DASHBOARD_MAX_RECORDS = int(os.getenv("DASHBOARD_MAX_RECORDS", "500"))

# ==================== Model Configuration ====================
MODEL_PATHS = {
    "temperature": MODELS_DIR / "temp_model.pkl",
    "ph": MODELS_DIR / "ph_model.pkl",
    "do": MODELS_DIR / "do_model.pkl",
    "turbidity": MODELS_DIR / "turb_model.pkl"
}

# ==================== Helper Functions ====================
def get_config_summary():
    """Return configuration summary for logging"""
    return {
        "mqtt_broker": MQTT_BROKER,
        "mqtt_port": MQTT_PORT,
        "mqtt_topic": MQTT_TOPIC,
        "database": str(DATABASE_PATH),
        "log_level": LOG_LEVEL,
        "dashboard_port": DASHBOARD_PORT
    }

def validate_config():
    """Validate critical configuration"""
    errors = []
    
    if not DATABASE_PATH.parent.exists():
        errors.append(f"Database directory does not exist: {DATABASE_PATH.parent}")
    
    for name, path in MODEL_PATHS.items():
        if not path.exists():
            errors.append(f"Model file missing: {name} at {path}")
    
    if EMAIL_SENDER and not EMAIL_PASSWORD:
        errors.append("EMAIL_SENDER provided but EMAIL_PASSWORD is missing")
    
    return errors

if __name__ == "__main__":
    print("=== Configuration Summary ===")
    for key, value in get_config_summary().items():
        print(f"{key}: {value}")
    
    print("\n=== Validation ===")
    errors = validate_config()
    if errors:
        print("⚠️ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid")
