import json
import pandas as pd
import joblib
from datetime import datetime
from paho.mqtt import client as mqtt_client
from prepare_features import build_feature_row

BROKER = "broker.hivemq.com"
TOPIC = "iot/tilapia/data"

MODEL_DIR = "../models/"
LOG_FILE = "../dashboard/data_log.csv"

# ------------------ LOAD MODELS ------------------
models = {
    "Temperature": joblib.load(MODEL_DIR + "model_Temperature_6h.pkl"),
    "pH": joblib.load(MODEL_DIR + "model_pH_6h.pkl"),
    "Dissolved_Oxygen": joblib.load(MODEL_DIR + "model_Dissolved_Oxygen_6h.pkl"),
    "Turbidity": joblib.load(MODEL_DIR + "model_Turbidity_6h.pkl")
}

scalers_Y = {
    "Temperature": joblib.load(MODEL_DIR + "scaler_Temperature.pkl"),
    "pH": joblib.load(MODEL_DIR + "scaler_pH.pkl"),
    "Dissolved_Oxygen": joblib.load(MODEL_DIR + "scaler_Dissolved_Oxygen.pkl"),
    "Turbidity": joblib.load(MODEL_DIR + "scaler_Turbidity.pkl")
}

# Lịch sử 24h gần nhất
history = pd.DataFrame(columns=[
    "Temperature", "pH", "Dissolved_Oxygen", "Turbidity", "timestamp"
])


# ------------------ PHÂN LOẠI RỦI RO ------------------
def classify_risk(temp, ph, do, turb):
    """
    Risk classification for tilapia aquaculture.
    
    Danger: Any critical threshold violated
    Safe: All parameters in optimal range
    Warning: Between Safe and Danger
    """
    # DANGER: Critical thresholds for tilapia survival
    if do < 2 or ph < 6 or ph > 9 or temp < 24 or temp > 35 or turb > 100:
        return "Danger"
    
    # SAFE: Optimal conditions for tilapia growth
    if 28 <= temp <= 32 and 6.5 <= ph <= 8.5 and do >= 6 and turb <= 20:
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


# ------------------ MQTT HANDLE ------------------
def on_message(client, userdata, msg):
    global history

    data = json.loads(msg.payload.decode())

    # Sensor risk – REALTIME
    risk_sensor = classify_risk(
        data["Temperature"],
        data["pH"],
        data["Dissolved_Oxygen"],
        data["Turbidity"]
    )

    # Build X row for prediction
    X_scaled, history = build_feature_row(history, data)

    if X_scaled is None:
        print("⏳ Chưa đủ dữ liệu lịch sử để dự đoán...")
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

        # Merge IoT + AI
        final_risk = merge_risks(risk_sensor, risk_pred)

    # -------- LOG OUT ----------
    print("\n===========================")
    print("📡 RAW Sensor:", data)
    print("⚠ Sensor Risk:", risk_sensor)
    print("🤖 Prediction 6h:", predictions, "| Pred Risk:", risk_pred)
    print("🚨 FINAL RISK:", final_risk)
    print("===========================\n")

    # -------- Append to CSV ----------
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

    df = pd.DataFrame([row])
    df.to_csv(LOG_FILE, mode="a",
              header=not pd.io.common.file_exists(LOG_FILE),
              index=False)


# ------------------ MQTT ------------------
def connect_mqtt():
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1)
    client.connect(BROKER)
    return client


def run():
    client = connect_mqtt()
    client.subscribe(TOPIC)
    client.on_message = on_message
    print("🚀 Gateway is running... waiting for MQTT data")
    client.loop_forever()


if __name__ == "__main__":
    run()
