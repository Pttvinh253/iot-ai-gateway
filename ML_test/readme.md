````
🐟 Tilapia Smart Water Quality Monitoring
IoT + AI Prediction + Streamlit Dashboard
ESP32 / MQTT / XGBoost / Python / Streamlit

📌 1. Giới thiệu dự án

Hệ thống giám sát chất lượng nước nuôi cá rô phi (Tilapia) sử dụng:

- ESP32 gửi dữ liệu cảm biến (thật hoặc giả lập)
- MQTT (mặc định kết nối tới `broker.hivemq.com`; có thể cấu hình dùng broker cục bộ như Mosquitto)
- Gateway AI (Python) xử lý & dự đoán 6 giờ tới
- Mô hình Machine Learning (XGBoost) đã huấn luyện từ bộ dữ liệu:
  Water Quality Monitoring Dataset for Tilapia Aquaculture – Montería, Colombia (2024)
- Streamlit Dashboard để hiển thị dữ liệu realtime + dự báo

Hệ thống hỗ trợ:

- Giám sát nhiệt độ, pH, DO, độ đục
- Dự báo 6 giờ tới theo mô hình ML
- Phân loại nguy cơ: Safe – Warning – Danger
- Hỗ trợ cảnh báo sớm tránh chết cá hàng loạt
 - Gửi cảnh báo qua Email (cấu hình trong `dashboard/app.py` sidebar)
 - Dashboard Streamlit hiển thị realtime, biểu đồ, và xuất báo cáo (PDF/CSV)
 - Hỗ trợ MQTT (ESP32 hoặc script mô phỏng). Mặc định dùng `broker.hivemq.com`, topic `iot/tilapia/data`.
 - Lưu dữ liệu lịch sử vào `dashboard/data_log.csv` để phân tích sau này
 - Hệ thống mặc định kết nối tới `broker.hivemq.com`; bạn có thể cấu hình để sử dụng broker cục bộ (ví dụ: Mosquitto) nếu muốn


📁 2. Cấu trúc thư mục
iot_ai_gateway/
│
├── models/                       # chứa toàn bộ model & scaler
│     ├── model_Temperature_6h.pkl
│     ├── model_pH_6h.pkl
│     ├── model_Dissolved_Oxygen_6h.pkl
│     ├── model_Turbidity_6h.pkl
│     ├── scaler_features.pkl
│     ├── scaler_Temperature.pkl
│     ├── scaler_pH.pkl
│     ├── scaler_Dissolved_Oxygen.pkl
│     ├── scaler_Turbidity.pkl
│     ├── feature_columns.pkl
│     └── model_config.pkl
│
├── gateway/
│     ├── prepare_features.py     # tạo lại feature engineering đầy đủ
│     ├── gateway_full_model.py   # AI Gateway xử lý MQTT -> CSV -> Dashboard
│     ├── simulator_publish.py    # mô phỏng dữ liệu (không cần ESP32)
│     └── history.csv (tự sinh)
│
├── dashboard/
│     ├── app.py                  # Streamlit dashboard realtime
│     └── data_log.csv            # dữ liệu lưu lại theo thời gian
│
├── data/
│     └── Monteria_Aquaculture_Data.xlsx
│
├── train/
│     └── trainIoT.py             # code huấn luyện XGBoost
│
└── esp32/
      └── esp32_tilapia_sim.ino   # chạy trên ESP32


🔧 3. Cài đặt môi trường Python
3.1. Tạo venv (khuyến khích)
python -m venv venv
venv\Scripts\activate     # Windows

3.2. Cài thư viện
pip install -r requirements.txt

Nếu chưa có file requirements.txt, có thể tự tạo:

- paho-mqtt
- streamlit
- pandas
- numpy
- joblib
- xgboost
- plotly


🚀 4. Chạy Simulator (thay ESP32)

## **Tilapia Smart Water Quality Monitoring**
IoT + AI Prediction + Streamlit Dashboard

### **Tổng quan**
Hệ thống này demo một luồng IoT → AI → Dashboard cho giám sát chất lượng nước nuôi cá rô phi (Tilapia):

- Thiết bị: ESP32 (thực tế) hoặc các script mô phỏng (trên laptop) gửi dữ liệu cảm biến qua MQTT.
- Gateway (Python): nhận MQTT, tiền xử lý, chạy mô hình ML (XGBoost) để dự báo 6 giờ tới.
- Dashboard (Streamlit): hiển thị dữ liệu realtime, dự báo và phân loại rủi ro (Safe / Warning / Danger).

## **Cấu trúc dự án (tóm tắt)**
- `models/` : file model và scaler (pickle)
- `gateway/` : `gateway_full_model.py`, `prepare_features.py`, `simulator_publish.py`
- `dashboard/` : `app.py` (Streamlit), `data_log.csv` (tạo/ghi bởi gateway)
- `data/` : dữ liệu nguồn và tiện ích (ví dụ `http_server.py`)
- `esp32_mqtt_sim/` : sketch `.ino` cho ESP32
- `requirements.txt` : thư viện Python cần cài

## **Cài đặt môi trường**
1. Tạo và kích hoạt virtualenv (khuyến nghị):

```powershell
python -m venv venv
venv\Scripts\activate
````

2. Cài dependencies:

```powershell
pip install -r requirements.txt
```

Gói chính có trong `requirements.txt`: `paho-mqtt`, `pandas`, `numpy`, `joblib`, `xgboost`, `streamlit`, `plotly`, `scikit-learn`, `fpdf2`.

## **Chạy hệ thống (quy trình khuyến nghị)**

Luồng test nhanh (không cần ESP32 thực):

1. Mở terminal, chạy AI Gateway:

```powershell
cd gateway
python gateway_full_model.py
```

2. Ở terminal khác, chạy script mô phỏng (một trong các lựa chọn):

```powershell
cd gateway
python simulator_publish.py
# Hoặc nếu có các script mô phỏng khác, chạy tương tự
```

3. Mở Dashboard (terminal khác):

```powershell
cd dashboard
streamlit run app.py
```

Mở trình duyệt: `http://localhost:8501`

Lưu ý: luôn chạy Gateway trước khi khởi động simulator hoặc ESP32 để dữ liệu được ghi vào `dashboard/data_log.csv`.

## **Chạy HTTP server để ESP32 fetch CSV (tùy chọn)**

Nếu muốn ESP32 tải file CSV từ máy tính thay vì publish MQTT, dùng `data/http_server.py`:

```powershell
cd data
python http_server.py
```

Script sẽ in ra địa chỉ local IP để bạn cập nhật vào sketch ESP32 (nếu dùng chế độ fetch CSV).

## **ESP32 (.ino)**

- Sketch mẫu: `esp32_mqtt_sim/esp32_mqtt_sim.ino`
- Trước khi flash, chỉnh `WIFI_SSID`, `WIFI_PASS`, và `MQTT_SERVER` trong file `.ino`.
- Nếu ESP32 trả về HTTP code -1 khi fetch, nguyên nhân thường do mạng (AP isolation / firewall). Thử dùng mobile hotspot hoặc chạy `http_server.py` và kiểm tra IP.

## **Email Alerts (Cảnh báo Email)**

- **Vị trí mã:** hàm `send_email_alert` trong `dashboard/app.py` — sử dụng SMTP của Gmail (`smtp.gmail.com`), cổng `587` với STARTTLS.
- **Cấu hình khi chạy Dashboard:** mở `dashboard/app.py` bằng Streamlit, vào sidebar và điền:
  - `Sender Gmail`: địa chỉ Gmail gửi (ví dụ `you@gmail.com`)
  - `App Password`: mật khẩu ứng dụng (Google App Password) — KHÔNG dùng mật khẩu chính tài khoản
  - `Receiver Email`: địa chỉ nhận cảnh báo
- **Hướng dẫn nhanh để lấy App Password (Gmail):**
  1. Bật xác thực 2 bước (2-Step Verification) cho tài khoản Google của bạn.

2.  Vào `Security` → `App passwords` → tạo mật khẩu ứng dụng mới cho `Mail`/`Other` và copy 16 ký tự đó vào trường `App Password` ở sidebar.

- **Bảo mật:** không lưu mật khẩu trực tiếp trong mã nguồn; dùng entry sidebar hoặc biến môi trường nếu triển khai. KHÔNG commit thông tin nhạy cảm.
- **Test:** trong sidebar có nút `Test Send Email` — ấn để gửi thử email.
- **Sự cố phổ biến:** lỗi đăng nhập SMTP → kiểm tra App Password / 2FA; kết nối mạng / firewall chặn cổng 587; lỗi cấu hình sender/receiver.

## **Các kịch bản mô phỏng (demo)**

Phần này liệt kê các kịch bản mô phỏng phổ biến (một số file có thể nằm trong `gateway/` hoặc trong thư mục `simulator/` tùy cách bạn lưu). Mục đích là kiểm tra phản ứng của mô hình AI với các tình huống khác nhau.

- Normal (bình thường)
  - Mô tả: môi trường ổn định, các thông số trong ngưỡng an toàn.
  - Mong đợi từ AI: báo `SAFE`.
  - Lệnh chạy:

```powershell
cd gateway
python normal.py --interval 2 --total 30
```

- Aerator fail (hỏng máy sục khí)
  - Mô tả: DO (Dissolved Oxygen) giảm nhanh do aerator ngừng hoạt động.
  - Mong đợi từ AI: cảnh báo `DANGER` khi DO tụt sâu.
  - Lệnh chạy:

```powershell
cd gateway
python aerator_fail.py --interval 2 --total 30
```

- Heavy rain (mưa lớn)
  - Mô tả: nhiệt độ và pH biến động, độ đục (turbidity) tăng do nước mưa và bùn vào ao.
  - Mong đợi từ AI: `WARNING` (biến động khiến rủi ro tăng nhưng chưa nhất thiết là chết hàng loạt).
  - Lệnh chạy:

```powershell
cd gateway
python heavy_rain.py --interval 2 --total 30
```

- Overfeeding (cho ăn quá mức)
  - Mô tả: độ đục tăng và DO giảm dần do thức ăn thừa phân hủy, gây thiếu oxy.
  - Mong đợi từ AI: dần dần chuyển từ `SAFE` → `WARNING` → có thể `DANGER` tùy mức độ và thời lượng.
  - Lệnh chạy:

```powershell
cd gateway
python overfeeding.py --interval 2 --total 30
```

- Algal bloom (nở hoa tảo)
  - Mô tả: DO tăng mạnh ban ngày (quang hợp) và giảm mạnh ban đêm (hô hấp tảo), kèm biến động nhiệt/pH.
  - Mong đợi từ AI: dao động rủi ro theo chu kỳ ngày/đêm, có thể `WARNING`/`DANGER` vào ban đêm.
  - Lệnh chạy:

```powershell
cd gateway
python algal_bloom.py --interval 2 --total 30
```

- Sensor drift (cảm biến trôi giá trị)
  - Mô tả: cảm biến dần dần lệch (drift) — dùng để kiểm tra độ bền của pipeline và khả năng chống nhiễu của mô hình.
  - Mong đợi từ AI: thường vẫn ổn nếu mô hình/feature engineering đủ mạnh, nhưng drift lớn có thể khiến cảnh báo sai.
  - Lệnh chạy:

```powershell
cd gateway
python sensor_drift.py --interval 2 --total 30
```

Ghi chú:

- Nếu các script không nằm trực tiếp trong `gateway/`, thay `cd gateway` bằng thư mục chứa các script mô phỏng (ví dụ `simulator/`).
- Tham số `--interval` (giây) điều khiển tần suất gửi mẫu; `--total` là tổng số mẫu sẽ phát. Bạn có thể điều chỉnh để chạy dài hơn hoặc ngắn hơn.
- Luôn đảm bảo `gateway_full_model.py` đang chạy trước khi khởi động các script mô phỏng để dữ liệu được xử lý và ghi vào `dashboard/data_log.csv`.

Nếu bạn muốn, tôi có thể tạo các file script mẫu (`normal.py`, `aerator_fail.py`, ...) trong thư mục `gateway/` hoặc `simulator/` để bạn chạy trực tiếp.

## **Ghi chú kỹ thuật & khắc phục sự cố**

- Nếu dashboard luôn hiện "No data yet": kiểm tra rằng `gateway_full_model.py` đang chạy và ghi `dashboard/data_log.csv`.
- Nếu dashboard luôn báo "Danger": kiểm tra dữ liệu input (schema / giá trị) từ simulator hoặc ESP32; chạy `simulator_publish.py` để xem mẫu payload.
- Lỗi MQTT client callback API: nếu gặp ValueError liên quan `callback API version`, đã cập nhật mã nguồn trong `gateway/gateway_full_model.py` để tương thích; đảm bảo cài phiên bản `paho-mqtt` tương thích.
- Lỗi mạng ESP32 fetch CSV (HTTP code -1): kiểm tra router AP isolation, Windows firewall, hoặc thử mobile hotspot.

## **Phát triển & mở rộng**

- Có thể thêm: cảnh báo Telegram, điều khiển aerator (actuator), multi-site dashboard, lưu trữ thời gian dài.

## **Tác giả**

Nhóm 11 – Đồ án IoT + AI (UIT) — 2024–2025

---
