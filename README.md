# 🐟 IoT AI Gateway - Tilapia Water Quality Monitoring System

**Môn học:** Công nghệ Internet of things hiện đại - NT532.Q11  
**Dự án:** Hệ thống giám sát chất lượng nước nuôi cá rô phi thông qua IoT + AI  
**Công nghệ:** ESP32 / MQTT / XGBoost / Python / Streamlit / SQLite

---

## 📌 1. Giới thiệu dự án

### Tổng quan
Hệ thống giám sát và dự báo chất lượng nước nuôi cá rô phi (Tilapia) sử dụng:
- **Thiết bị IoT (ESP32)**: Thu thập dữ liệu từ cảm biến hoặc mô phỏng
- **MQTT Broker (HiveMQ)**: Truyền tải dữ liệu real-time
- **AI Gateway**: Xử lý dữ liệu & dự đoán 6 giờ tới bằng XGBoost
- **Streamlit Dashboard**: Hiển thị real-time, dự báo và cảnh báo
- **SQLite Database**: Lưu trữ dữ liệu lâu dài

### Chức năng chính
| Chức năng | Mô tả |
|-----------|-------|
| 📊 **Giám sát real-time** | Temperature, pH, DO (Dissolved Oxygen), Turbidity |
| 🤖 **Dự báo AI** | Dự đoán 6 giờ tới cho mỗi thông số |
| ⚠️ **Phân loại rủi ro** | SAFE / WARNING / DANGER |
| 📧 **Cảnh báo email** | Tự động gửi email khi phát hiện nguy hiểm |
| 📈 **Lịch sử dữ liệu** | Lưu log vào CSV và SQLite database |
| 🎮 **Mô phỏng** | 6 kịch bản khác nhau (Overfeeding, Algal Bloom, Sensor Drift, v.v.) |

### Thông số mặc định
- **MQTT Broker:** `broker.hivemq.com:1883` (Public - không cần đăng ký)
- **Topic:** `iot/tilapia/data`
- **Dữ liệu huấn luyện:** [Tilapia Water Quality Monitoring Dataset](https://data.mendeley.com/datasets/dgdr2kfbyt/1) - Montería, Colombia (2024)

---

## 📁 2. Cấu trúc dự án

```
iot_ai_gateway/
│
├── 📄 config.py              # Configuration centralized (từ .env)
├── 📄 logger.py              # Logging system với màu sắc
├── 📄 utils.py               # Utility functions
├── 📄 validate_system.py      # Validate config & dependencies
├── .env                       # Environment variables (YOUR config)
├── .env.example               # Template for .env
├── requirements.txt           # Python dependencies
│
├── 📂 models/                 # ML Models (4 XGBoost models)
│   ├── model_Temperature_6h.pkl
│   ├── model_pH_6h.pkl
│   ├── model_Dissolved_Oxygen_6h.pkl
│   ├── model_Turbidity_6h.pkl
│   ├── scaler_features.pkl
│   └── feature_columns.pkl
│
├── 📂 gateway/                # AI Processing Engine
│   ├── gateway_sqlite.py      # Main gateway (recommended)
│   ├── gateway_full_model.py  # Alternative version
│   ├── prepare_features.py    # Feature engineering
│   ├── simulator_publish.py   # MQTT simulator
│   └── random_event.py        # Event generator
│
├── 📂 simulator/              # 6 Simulation Scenarios
│   ├── normal.py              # Normal operation
│   ├── overfeeding.py         # Overfeeding scenario
│   ├── heavy_rain.py          # Heavy rain impact
│   ├── algal_bloom.py         # Algal bloom scenario
│   ├── aerator_fail.py        # Aerator failure
│   └── sensor_drift.py        # Sensor drift
│
├── 📂 dashboard/              # Streamlit Web Dashboard
│   ├── app.py                 # Main dashboard
│   ├── app_simple_sqlite.py   # SQLite version
│   ├── app_sqlite.py          # Enhanced SQLite version
│   └── data_log.csv           # Data logs
│
├── 📂 database/               # Database Management
│   ├── db_config.py           # Database config
│   ├── migrate_csv_to_db.py   # CSV → Database migration
│   ├── test_database.py       # Database tests
│   └── iot_data.db            # SQLite database
│
├── 📂 data/                   # Data Processing
│   ├── csv_to_mqtt.py         # CSV → MQTT publisher
│   ├── http_server.py         # HTTP server
│   └── test.csv, test_small.csv
│
├── 📂 train/                  # Model Training
│   ├── trainIoT.py            # Training script
│   └── make_test.py           # Test data generator
│
├── 📂 ML_test/                # ML Testing & Conversion
│   ├── trainIoT.py            # ML training test
│   ├── convert.py             # Model conversion
│   ├── tilapia_wq.csv         # Training dataset
│   └── test_data_for_simulation.csv
│
├── 📂 esp32_mqtt_sim/         # ESP32 Arduino Code
│   └── esp32_mqtt_sim.ino     # Firmware simulator
│
└── 📂 logs/                   # Auto-created Log Folder
    ├── gateway.log            # Gateway logs (rotated)
    ├── dashboard.log          # Dashboard logs
    └── simulator.log          # Simulator logs
```

---

## 🔧 3. Cài đặt & Cấu hình

### 3.1 Cài đặt Python Environment

**Tạo virtual environment:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Cài thư viện:**
```powershell
pip install -r requirements.txt
```
Xem chi tiết tại [requirements.txt](requirements.txt)

### 3.2 Cấu hình Environment Variables

**Copy template:**
```powershell
cp .env.example .env
```

**Chỉnh sửa `.env`:**
```env
# === MQTT Settings ===
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_TOPIC=iot/tilapia/data

# === Database ===
DATABASE_PATH=database/iot_data.db

# === Email Alerts (Optional) ===
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=receiver@gmail.com
ALERT_INTERVAL_MIN=10

# === Water Quality Thresholds ===
TEMP_MIN_SAFE=28.0
TEMP_MAX_SAFE=32.0
PH_MIN_SAFE=6.5
PH_MAX_SAFE=8.5
DO_MIN_SAFE=5.0
TURBIDITY_MAX_SAFE=25.0
```

---

## 🚀 4. Chạy hệ thống (Chi tiết)

**Bước 1 - Khởi chạy AI Gateway:**
```powershell
cd gateway
python gateway_sqlite.py
```

**Bước 2 - Chạy mô phỏng dữ liệu (terminal khác):**
```powershell
cd simulator
python normal.py
# Hoặc các scenario khác:
# python overfeeding.py
# python algal_bloom.py
# python sensor_drift.py
```

**Bước 3 - Khởi chạy Dashboard (terminal khác):**
```powershell
cd dashboard
streamlit run app_sqlite.py
```
✅ Dashboard sẽ mở tại: `http://localhost:8501`

---

## 📊 5. Kiến trúc hệ thống

### Luồng xử lý

```
IoT Device → MQTT Broker → Gateway (AI) → SQLite → Dashboard
```

**Quy trình chính:**
1. IoT publish JSON: `{"temperature": 30.5, "pH": 7.2, "dissolved_oxygen": 6.8, ...}`
2. Gateway parse, validate, feature engineering
3. ML prediction (4 XGBoost models) → Risk assessment
4. Save to SQLite + Email alert (nếu DANGER)
5. Dashboard visualize real-time + forecast

### Các mô hình ML

| Mô hình | Input | Output | File |
|---------|-------|--------|------|
| Temperature Prediction | 50+ features | +6h forecast | `model_Temperature_6h.pkl` |
| pH Prediction | 50+ features | +6h forecast | `model_pH_6h.pkl` |
| DO Prediction | 50+ features | +6h forecast | `model_Dissolved_Oxygen_6h.pkl` |
| Turbidity Prediction | 50+ features | +6h forecast | `model_Turbidity_6h.pkl` |

### Ngưỡng cảnh báo

| Thông số | ✅ An toàn | 🔴 Nguy hiểm |
|----------|-----------|-------------|
| Temperature (°C) | 28–32 | <20 hoặc >35 |
| pH | 6.5–8.5 | <6 hoặc >9 |
| DO (mg/L) | 5+ | <3 |
| Turbidity (NTU) | 0–25 | >50 |

---

## 🧪 6. Các lệnh thường dùng

### Validate hệ thống
```powershell
python validate_system.py
```
Kiểm tra: Python version, dependencies, config, models, database

### Huấn luyện lại mô hình
```powershell
cd train
python trainIoT.py
```

### Migrate dữ liệu CSV → SQLite
```powershell
cd database
python migrate_csv_to_db.py
```

### Chạy Database Tests
```powershell
cd database
python test_database.py
```

### Kiểm tra logs
```powershell
# Xem logs realtime
Get-Content logs/gateway.log -Wait

# Hoặc dùng tail
tail -f logs/gateway.log
```

---

## ⚠️ 7. Troubleshooting

### Problem: Connection refused to MQTT
**Solution:**
```
✓ Kiểm tra internet connection
✓ Verify MQTT_BROKER in .env: broker.hivemq.com
✓ Port: 1883 (not 8883 which is SSL)
```

### Problem: Models not loading
**Solution:**
```
✓ Verify models folder exists: models/
✓ Models must be in PKL format
✓ Run: python validate_system.py
```

### Problem: Dashboard không hiển thị dữ liệu
**Solution:**
```
✓ Ensure gateway đang chạy
✓ Ensure simulator đang publish dữ liệu
✓ Check SQLite database exists: database/iot_data.db
✓ Review logs: logs/dashboard.log
```

### Problem: Email không gửi được
**Solution:**
```
✓ Verify EMAIL_SENDER in .env
✓ Use Gmail App Password (16 ký tự từ Google Account)
✓ Check logs: logs/gateway.log
```

---

## 📚 8. Tài liệu tham khảo

- [database/QUICKSTART.md](database/QUICKSTART.md) — Hướng dẫn nhanh database
- [database/README_SQLITE.md](database/README_SQLITE.md) — SQLite guide

---

## 👥 Thông tin dự án

- **Môn học:** Công nghệ Internet of things hiện đại (NT532.Q11)
- **Dữ liệu:** Tilapia Water Quality Monitoring - Montería, Colombia (2024)
- **Tech Stack:** Python 3.8+ | MQTT | XGBoost | Streamlit | SQLite

---

## 🚀 Quick Start (Tóm tắt)

### Setup môi trường
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### Chạy các component (3 terminal riêng)

**Terminal 1 - Gateway AI:**
```powershell
cd gateway
python gateway_sqlite.py
```

**Terminal 2 - Simulator dữ liệu:**
```powershell
cd simulator
python normal.py
```

**Terminal 3 - Dashboard:**
```powershell
cd dashboard
streamlit run app_sqlite.py
```

✅ Dashboard mở tại: http://localhost:8501

---

## 📡 Các kịch bản mô phỏng

| Kịch bản | Mô tả | Kỳ vọng |
|----------|-------|---------|
| 🟢 **normal.py** | Hoạt động bình thường | SAFE |
| 🔴 **aerator_fail.py** | Hỏng thiết bị sục khí | DANGER |
| 🟡 **heavy_rain.py** | Mưa lớn, pH dao động | WARNING |
| 🔴 **overfeeding.py** | Cho quá nhiều thức ăn | WARNING → DANGER |
| 🟡 **algal_bloom.py** | Tảo phát triển dày đặc | WARNING/DANGER |
| 🟠 **sensor_drift.py** | Cảm biến bị trôi giá trị | Ảnh hưởng dự báo |

---

## ✉️ Cảnh báo Email (tùy chọn)

Sử dụng Gmail SMTP:
- Server: `smtp.gmail.com:587`
- Cần App Password từ Google Account
- Cấu hình trong `.env`

---

## 📝 Phân công công việc 

Điền thông tin thành viên và tỷ lệ đóng góp vào bảng dưới đây.

| STT | MSSV     | Họ và tên             | Công việc phụ trách                                                       | Tỷ lệ (%) |
|:---:|:--------:|:----------------------|:--------------------------------------------------------------------------|:---------:|
| 1   | 22521680 | Phạm Thị Thanh Vinh   | Mô phỏng và xử lý dữ liệu, thiết kế IoT, logic AI, dashboard, chạy demo  |   100%    |
| 2   | 22521201 | Ngô Anh Quang         | Huấn luyện và xuất mô hình .pkl                                          |   100%    |
| 3   | 22521297 | Hà Ngọc Tân           | Viết báo cáo và làm slide thuyết trình                                   |   100%    |








# 🐟 IoT AI Gateway - Tilapia Water Quality Monitoring System (ENGLISH VERSION)

**Subject:** Modern Internet of Things Technology - NT532.Q11

**Project:** Tilapia Water Quality Monitoring System via IoT + AI

**Technologies:** ESP32 / MQTT / XGBoost / Python / Streamlit / SQLite

---
## 📌 1. Project Introduction

### Overview
The tilapia water quality monitoring and forecasting system uses:

- **IoT Device (ESP32)**: Collects data from sensors or simulations
- **MQTT Broker (HiveMQ)**: Transmits real-time data
- **AI Gateway**: Processes data & predicts the next 6 hours using XGBoost
- **Streamlit Dashboard**: Displays real-time, forecasts and alerts
- **SQLite Database**: Stores data long-term Long

### Main Functions
| Function | Description |

|-----------|-------|

| 📊 **Real-time Monitoring** | Temperature, pH, DO (Dissolved Oxygen), Turbidity |

| 🤖 **AI Forecasting** | 6-hour forecast for each parameter |

| ⚠️ **Risk Classification** | SAFE / WARNING / DANGER |

| 📧 **Email Alerts** | Automatically sends emails when hazards are detected |

| 📈 **Data History** | Saves logs to CSV and SQLite database |

| 🎮 **Simulation** | 6 different scenarios (Overfeeding, Algal Bloom, Sensor Drift, etc.) |

### Default Parameters
- **MQTT Broker:** `broker.hivemq.com:1883` (Public - no registration required)
- **Topic:** `iot/tilapia/data`
- **Training Data:** [Tilapia Water Quality Monitoring Dataset](https://data.mendeley.com/datasets/dgdr2kfbyt/1) - Montería, Colombia (2024)

---

## 📁 2. Cấu trúc dự án

```
iot_ai_gateway/
│
├── 📄 config.py              # Configuration centralized (từ .env)
├── 📄 logger.py              # Logging system với màu sắc
├── 📄 utils.py               # Utility functions
├── 📄 validate_system.py      # Validate config & dependencies
├── .env                       # Environment variables (YOUR config)
├── .env.example               # Template for .env
├── requirements.txt           # Python dependencies
│
├── 📂 models/                 # ML Models (4 XGBoost models)
│   ├── model_Temperature_6h.pkl
│   ├── model_pH_6h.pkl
│   ├── model_Dissolved_Oxygen_6h.pkl
│   ├── model_Turbidity_6h.pkl
│   ├── scaler_features.pkl
│   └── feature_columns.pkl
│
├── 📂 gateway/                # AI Processing Engine
│   ├── gateway_sqlite.py      # Main gateway (recommended)
│   ├── gateway_full_model.py  # Alternative version
│   ├── prepare_features.py    # Feature engineering
│   ├── simulator_publish.py   # MQTT simulator
│   └── random_event.py        # Event generator
│
├── 📂 simulator/              # 6 Simulation Scenarios
│   ├── normal.py              # Normal operation
│   ├── overfeeding.py         # Overfeeding scenario
│   ├── heavy_rain.py          # Heavy rain impact
│   ├── algal_bloom.py         # Algal bloom scenario
│   ├── aerator_fail.py        # Aerator failure
│   └── sensor_drift.py        # Sensor drift
│
├── 📂 dashboard/              # Streamlit Web Dashboard
│   ├── app.py                 # Main dashboard
│   ├── app_simple_sqlite.py   # SQLite version
│   ├── app_sqlite.py          # Enhanced SQLite version
│   └── data_log.csv           # Data logs
│
├── 📂 database/               # Database Management
│   ├── db_config.py           # Database config
│   ├── migrate_csv_to_db.py   # CSV → Database migration
│   ├── test_database.py       # Database tests
│   └── iot_data.db            # SQLite database
│
├── 📂 data/                   # Data Processing
│   ├── csv_to_mqtt.py         # CSV → MQTT publisher
│   ├── http_server.py         # HTTP server
│   └── test.csv, test_small.csv
│
├── 📂 train/                  # Model Training
│   ├── trainIoT.py            # Training script
│   └── make_test.py           # Test data generator
│
├── 📂 ML_test/                # ML Testing & Conversion
│   ├── trainIoT.py            # ML training test
│   ├── convert.py             # Model conversion
│   ├── tilapia_wq.csv         # Training dataset
│   └── test_data_for_simulation.csv
│
├── 📂 esp32_mqtt_sim/         # ESP32 Arduino Code
│   └── esp32_mqtt_sim.ino     # Firmware simulator
│
└── 📂 logs/                   # Auto-created Log Folder
├── gateway.log            # Gateway logs (rotated)
├── dashboard.log          # Dashboard logs
└── simulator.log          # Simulator logs
```

---

## 🔧 3. Cài đặt & Cấu hình

### 3.1 Cài đặt Python Environment

**Tạo virtual environment:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Cài thư viện:**
```powershell
pip install -r requirements.txt
```
Xem chi tiết tại [requirements.txt](requirements.txt)

### 3.2 Cấu hình Environment Variables

**Copy template:**
```powershell
cp .env.example .env
```

**Chỉnh sửa `.env`:**
```env
# === MQTT Settings ===
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_TOPIC=iot/tilapia/data

# === Database ===
DATABASE_PATH=database/iot_data.db

# === Email Alerts (Optional) ===
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECEIVER=receiver@gmail.com
ALERT_INTERVAL_MIN=10

# === Water Quality Thresholds ===
TEMP_MIN_SAFE=28.0
TEMP_MAX_SAFE=32.0
PH_MIN_SAFE=6.5
PH_MAX_SAFE=8.5
DO_MIN_SAFE=5.0
TURBIDITY_MAX_SAFE=25.0
```

---

## 🚀 4. Running the System (Details)

**Step 1 - Launch AI Gateway:**
```powershell
cd gateway
python gateway_sqlite.py
```

**Step 2 - Run data simulation (different terminal):**
```powershell
cd simulator
python normal.py
# Or other scenarios:
# python overfeeding.py
# python algal_bloom.py
# python sensor_drift.py
```

**Step 3 - Launch Dashboard (different terminal):**
```powershell
cd dashboard
streamlit run app_sqlite.py
```
✅ Dashboard will open at: `http://localhost:8501`

---
## 📊 5. System Architecture

### Processing Flow

```
IoT Device → MQTT Broker → Gateway (AI) → SQLite → Dashboard
```

**Main process:**
1. IoT publish JSON: `{"temperature": 30.5, "pH": 7.2, "dissolved_oxygen": 6.8, ...}`
2. Gateway parsing, validation, feature engineering
3. ML prediction (4 XGBoost models) → Risk assessment
4. Save to SQLite + Email alert (if DANGER)
5. Dashboard visualize real-time + forecast

### ML models

| Model | Input | Output | File |
|--------|-------|--------|-------|
| Temperature Prediction | 50+ features | +6h forecast | `model_Temperature_6h.pkl` |
| pH Prediction | 50+ features | +6h forecast | `model_pH_6h.pkl` |
| DO Prediction | 50+ features | +6h forecast | `model_Dissolved_Oxygen_6h.pkl` |

| Turbidity Prediction | 50+ features | +6h forecast | `model_Turbidity_6h.pkl` |

### Warning Thresholds

| Parameters | ✅ Safe | 🔴 Dangerous |

|----------|-----------|-------------|

| Temperature (°C) | 28–32 | <20 or >35 |

| pH | 6.5–8.5 | <6 or >9 |

| DO (mg/L) | 5+ | <3 |

| Turbidity (NTU) | 0–25 | >50 |

---

## 🧪 6. Commonly Used Commands

### Validate System
```powershell
python validate_system.py
```
Check: Python version, dependencies, config, models, database

### Retrain Model
```powershell
cd train
python trainIoT.py
```

### Migrate CSV Data to SQLite
```powershell
cd database
python migrate_csv_to_db.py
```

### Run Database Tests
```powershell
cd database
python test_database.py
```

### Check Logs
```powershell
# View Realtime Logs
Get-Content logs/gateway.log -Wait

# Or use tail
tail -f logs/gateway.log
```

---

## ⚠️ 7. Troubleshooting

### Problem: Connection refused to MQTT
**Solution:**
```
✓ Check internet connection
✓ Verify MQTT_BROKER in .env: broker.hivemq.com
✓ Port: 1883 (not 8883 which is SSL)
```

### Problem: Models not loading
**Solution:**
```
✓ Verify models folder exists: models/
✓ Models must be in PKL format
✓ Run: python validate_system.py
```

### Problem: Dashboard does not display data
**Solution:**
```
✓ Ensure gateway is running
✓ Ensure simulator is publishing data
✓ Check SQLite database exists: database/iot_data.db
✓ Review logs: logs/dashboard.log

```
### Problem: Email failed to send
**Solution:**

``` ✓ Verify EMAIL_SENDER in .env
✓ Use Gmail App Password (16 characters from Google Account)
✓ Check logs: logs/gateway.log

```

---
## 📚 8. References

- [database/QUICKSTART.md](database/QUICKSTART.md) — Database Quick Guide

- [database/README_SQLITE.md](database/README_SQLITE.md) — SQLite guide

---

## 👥 Project Information

- **Subject:** Modern Internet of Things Technology (NT532.Q11)

- **Data:** Tilapia Water Quality Monitoring - Monterícola, Colombia (2024)

- **Tech Stack:** Python 3.8+ | MQTT | XGBoost | Streamlit | SQLite

---

## 🚀 Quick Start (Summary)

### Environment Setup
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### Running Components (3 separate terminals)

**Terminal 1 - Gateway AI:**
```powershell
cd gateway
python gateway_sqlite.py
```

**Terminal 2 - Data Simulator:**
```powershell
cd simulator
python normal.py
```

**Terminal 3 - Dashboard:**
```powershell
cd dashboard
streamlit run app_sqlite.py
```

✅ Dashboard opens at: http://localhost:8501

---
## 📡 Simulation Scenarios

| Scenario | Description | Expectations |

|----------|-------|---------|

| 🟢 **normal.py** | Normal operation | SAFE |

| 🔴 **aerator_fail.py** | Aeration failure | DANGER |

| 🟡 **heavy_rain.py** | Heavy rain, pH fluctuation | WARNING |

| 🔴 **overfeeding.py** | Overfeeding | WARNING → DANGER |

| 🟡 **algal_bloom.py** | Algal bloom | WARNING/DANGER |

| 🟠 **sensor_drift.py** | Sensor drift | Affects forecast |

---

## ✉️ Email Alerts (Optional)

Using Gmail SMTP:

- Server: `smtp.gmail.com:587`
- Requires App Password from Google Account

- Configure in `.env`

---
## 📝 Work Assignment

Fill in member information and contribution percentage in the table below.

| No. | Student ID | Full Name | Responsibilities | Percentage (%) |

|:---:|:--------:|:----------------------|:--------------------------------------------------------------------------|:---------:|

| 1 | 22521680 | Pham Thi Thanh Vinh | Simulation and data processing, IoT design, AI logic, dashboard, demo running | 100% |

| 2 | 22521201 | Ngo Anh Quang | Training and exporting .pkl models | 100% |

| 3 | 22521297 | Ha Ngoc Tan | Report writing and presentation slide creation | 100% |
