# dashboard/app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time, io, os, json
from datetime import datetime, timedelta
from paho.mqtt import client as mqtt_client
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ----------------- CONFIG -----------------
ALERT_INTERVAL_MIN = 10  # Minutes between repeated alerts
# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "data_log.csv")   # dashboard reads this CSV
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/tilapia/data"

SIM_PUBLISH_INTERVAL = 5


# ----------------- EMAIL ALERT -----------------
def send_email_alert(to_email, subject, message, sender_email, sender_password):
    """
    Send email alert via Gmail SMTP
    Returns: (success: bool, error_message: str or None)
    """
    try:
        # Validate inputs
        if not all([to_email, sender_email, sender_password]):
            return False, "Missing email credentials (sender, receiver, or password)"
        
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True, None

    except smtplib.SMTPAuthenticationError:
        error = "Authentication failed. Check:\n1. Use Gmail App Password (not regular password)\n2. Enable 2-Step Verification in Google Account"
        return False, error
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Email send error: {str(e)}"


# ----------------- UTIL -----------------
def safe_read_csv(path):
    try:
        df = pd.read_csv(path)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except:
        return pd.DataFrame()


def get_latest(df):
    if df.empty:
        return {}
    return df.iloc[-1].to_dict()


# Simulator functionality was moved to external scripts under `simulator/`.
# Embedded simulator (previously here) was removed to avoid Streamlit thread
# and rerun issues. To run simulated data, use the scripts in the top-level
# `simulator/` folder (see README for examples).


# ----------------- PDF REPORT -----------------
def generate_pdf_report(df_tail, out_path="report_generated.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "Tilapia Water Quality - Auto Report", ln=True)

    if not df_tail.empty:
        latest = df_tail.iloc[-1]

        lines = [
            f"Time: {latest['timestamp']}",
            f"Temperature: {latest['temp']} °C",
            f"pH: {latest['ph']}",
            f"DO: {latest['do']} mg/L",
            f"Turbidity: {latest['turbidity']} NTU",
            f"Status: {latest['status']}"
        ]
        for line in lines:
            pdf.cell(0, 8, line, ln=True)

    else:
        pdf.cell(0, 8, "No data available.", ln=True)

    pdf.output(out_path)
    return out_path


# ----------------- STREAMLIT UI -----------------
st.set_page_config(page_title="Tilapia Dashboard", layout="wide", page_icon="🐟")
st.title("🐟 Tilapia Smart Water Quality Dashboard (IoT + AI)")


# ---------- SIDEBAR ----------
st.sidebar.header("Controls & Settings")
nav = st.sidebar.radio("Navigation", ["Realtime", "Prediction", "Risk Analysis", "Devices", "Reports"])

refresh = st.sidebar.slider("Auto refresh (sec)", 3, 30, 5)
# Simulator control moved out of the dashboard for stability (run simulator scripts in simulator/)
st.sidebar.markdown("**Simulator:** moved to external scripts (see `simulator/` folder)")

st.sidebar.markdown("---")
st.sidebar.subheader("MQTT Broker")
broker_input = st.sidebar.text_input("Host", value=MQTT_BROKER)
port_input = st.sidebar.number_input("Port", value=MQTT_PORT)
topic_input = st.sidebar.text_input("Topic", value=MQTT_TOPIC)

st.sidebar.markdown("---")
st.sidebar.subheader("📧 Email Alerts")

email_sender = st.sidebar.text_input("Sender Gmail")
email_pass = st.sidebar.text_input("App Password", type="password")
email_receiver = st.sidebar.text_input("Receiver Email")

if st.sidebar.button("Test Send Email"):
    ok, error = send_email_alert(
        to_email=email_receiver,
        subject="Tilapia System Test Email",
        message="This is a test email alert.",
        sender_email=email_sender,
        sender_password=email_pass
    )
    if ok:
        st.sidebar.success("✅ Email sent successfully!")
    else:
        st.sidebar.error(f"❌ Email failed!\n{error}")


# -------- LOAD DATA --------
df = safe_read_csv(DATA_FILE)

if df.empty and nav != "Devices":
    st.warning("No data yet — start gateway or run simulator!")
    st.stop()

# ===================== NAVIGATION PAGES =====================

# -----------------------------------------------------------
#                      REALTIME PAGE
# -----------------------------------------------------------
if nav == "Realtime":
    if df.empty:
        st.info("No real-time data yet. Go to Devices to start simulator.")
    else:
        latest = get_latest(df)

        # ---- TOP GAUGE CARDS ----
        c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])

        # Temperature
        fig_t = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest.get("temp", 0),
            title={"text":"Temperature (°C)"},
            gauge={"axis":{"range":[0,40]}, "bar":{"color":"#2196F3"}}
        ))
        c1.plotly_chart(fig_t, use_container_width=True)

        # pH
        fig_ph = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest.get("ph", 0),
            title={"text":"pH"},
            gauge={"axis":{"range":[0,14]}, "bar":{"color":"#9C27B0"}}
        ))
        c2.plotly_chart(fig_ph, use_container_width=True)

        # DO
        fig_do = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest.get("do", 0),
            title={"text":"DO (mg/L)"},
            gauge={"axis":{"range":[0,10]}, "bar":{"color":"#009688"}}
        ))
        c3.plotly_chart(fig_do, use_container_width=True)

        # Turbidity
        fig_tu = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest.get("turbidity", 0),
            title={"text":"Turbidity (NTU)"},
            gauge={"axis":{"range":[0,100]}, "bar":{"color":"#795548"}}
        ))
        c4.plotly_chart(fig_tu, use_container_width=True)

        # STATUS CARD
        status_color = {
            "Safe":"#4CAF50",
            "Warning":"#FFC107",
            "Danger":"#F44336"
        }.get(latest.get("status","N/A"), "gray")

        c5.markdown(
            f"<div style='background:{status_color};padding:20px;border-radius:10px;text-align:center;color:white'>"
            f"<h3>Status</h3><h2>{latest.get('status','N/A')}</h2></div>",
            unsafe_allow_html=True
        )

        # ---------- EMAIL ALERT (ONLY WHEN DANGER) ----------
#         if latest.get("status") == "Danger":
#             if email_sender and email_receiver and email_pass:
#                 send_email_alert(
#                     to_email=email_receiver,
#                     subject="[DANGER] Tilapia Water Quality Alert!",
#                     message=f"""
# ⚠️ DANGER WATER CONDITION DETECTED!

# Timestamp: {latest['timestamp']}
# Temperature: {latest['temp']} °C
# pH: {latest['ph']}
# DO: {latest['do']} mg/L
# Turbidity: {latest['turbidity']} NTU
# """,
#                     sender_email=email_sender,
#                     sender_password=email_pass
#                 )
#                 st.error("⚠️ Email alert sent!")

        # ---------- EMAIL ALERT (ANTI-SPAM, 2 LẦN GỬI) ----------
        
        # Initialize session state for email tracking
        if 'last_alert_time' not in st.session_state:
            st.session_state.last_alert_time = None
        if 'last_status' not in st.session_state:
            st.session_state.last_status = "Safe"

        current_time = datetime.now()
        danger_now = latest.get("status") == "Danger"
        should_send = False

        # CASE 1: Danger mới xuất hiện → gửi lần 1
        if danger_now and st.session_state.last_status != "Danger":
            should_send = True

        # CASE 2: Danger kéo dài → gửi lại lần 2 sau X phút
        elif danger_now and st.session_state.last_alert_time is not None:
            elapsed_min = (current_time - st.session_state.last_alert_time).total_seconds() / 60
            if elapsed_min >= ALERT_INTERVAL_MIN:
                should_send = True

        # SEND EMAIL IF NEEDED

        if danger_now and should_send:
            if email_sender and email_receiver and email_pass:
                print(f"\n{'='*60}")
                print(f"[EMAIL ALERT] Attempting to send email...")
                print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Status: {latest.get('status')}")
                print(f"Previous Status: {st.session_state.last_status}")
                print(f"Alert Type: {'FIRST ALERT' if st.session_state.last_status != 'Danger' else 'REPEATED ALERT'}")
                print(f"To: {email_receiver}")
                print(f"{'='*60}\n")
                
                ok, error = send_email_alert(
                    to_email=email_receiver,
                    subject="[DANGER] Tilapia Water Quality Alert!",
                    message=f"""
⚠️ DANGER WATER CONDITION DETECTED!

Timestamp: {latest['timestamp']}
Temperature: {latest['temp']} °C
pH: {latest['ph']}
DO: {latest['do']} mg/L
Turbidity: {latest['turbidity']} NTU

Message Type:
- {'FIRST ALERT' if st.session_state.last_status != 'Danger' else 'REPEATED ALERT AFTER INTERVAL'}
""",
                    sender_email=email_sender,
                    sender_password=email_pass
                )
                if ok:
                    st.session_state.last_alert_time = current_time
                    print(f"✅ [EMAIL SUCCESS] Email sent successfully at {current_time.strftime('%H:%M:%S')}\n")
                    st.error("⚠️ Email alert sent successfully!")
                else:
                    print(f"❌ [EMAIL FAILED] {error}\n")
                    st.warning(f"❌ Email alert failed!\n{error}")

        # CASE 3: Chỉ reset khi trở về Safe (không reset khi Warning)
        if latest.get("status") == "Safe":
            st.session_state.last_alert_time = None

        # Update trạng thái cuối
        st.session_state.last_status = latest.get("status")



        # ----------- RAW DATA TREND -----------
        st.markdown("### 📉 Raw Sensor Trends (Last 200 records)")
        fig = px.line(
            df.tail(200),
            x="timestamp",
            y=["temp","ph","do","turbidity"],
            labels={"value":"Measurement"},
        )
        st.plotly_chart(fig, use_container_width=True)


# -----------------------------------------------------------
#                      PREDICTION PAGE
# -----------------------------------------------------------
elif nav == "Prediction":
    if df.empty:
        st.info("No data to show predictions.")
    else:
        st.subheader("🤖 AI Prediction vs Actual (Overlay)")

        for sensor, actual_col, pred_col, title in [
            ("Temperature","temp","pred_temp","Temperature (°C)"),
            ("pH","ph","pred_ph","pH"),
            ("Dissolved Oxygen","do","pred_do","Dissolved Oxygen (mg/L)"),
            ("Turbidity","turbidity","pred_turb","Turbidity (NTU)")
        ]:
            if pred_col in df.columns:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["timestamp"], y=df[actual_col],
                    mode="lines", name="Actual"
                ))
                fig.add_trace(go.Scatter(
                    x=df["timestamp"], y=df[pred_col],
                    mode="lines", name="Predicted"
                ))
                fig.update_layout(title=title, height=300)
                st.plotly_chart(fig, use_container_width=True)

        # SUMMARY
        st.markdown("### 📊 Prediction Statistical Summary")
        
        # Show statistics for all sensors that have predictions
        pred_cols = []
        if "pred_temp" in df.columns:
            pred_cols.extend(["temp", "pred_temp"])
        if "pred_ph" in df.columns:
            pred_cols.extend(["ph", "pred_ph"])
        if "pred_do" in df.columns:
            pred_cols.extend(["do", "pred_do"])
        if "pred_turb" in df.columns:
            pred_cols.extend(["turbidity", "pred_turb"])
        
        if pred_cols:
            st.write(df[pred_cols].tail(20).describe())
        else:
            st.info("No prediction data available yet.")


# -----------------------------------------------------------
#                    RISK ANALYSIS PAGE
# -----------------------------------------------------------
elif nav == "Risk Analysis":
    st.subheader("📌 Risk Level Timeline")

    fig = px.scatter(
        df, x="timestamp", y=[1]*len(df),
        color="status",
        color_discrete_map={"Safe":"green","Warning":"orange","Danger":"red"}
    )
    fig.update_yaxes(visible=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🔢 Risk Count Summary")
    st.write(df["status"].value_counts().to_frame("count"))

    st.markdown("### 📅 Daily Statistics (mean/std)")
    df_stats = df.set_index("timestamp").resample("D").agg({
        "temp":["mean","std"],
        "ph":["mean","std"],
        "do":["mean","std"],
        "turbidity":["mean","std"],
    })
    st.dataframe(df_stats.tail(14))


# -----------------------------------------------------------
#                        DEVICES PAGE
# -----------------------------------------------------------
elif nav == "Devices":
    st.subheader("🛠️ Devices")

    st.write("MQTT Broker:", broker_input)
    st.write("Port:", port_input)
    st.write("Topic:", topic_input)

    st.markdown("---")
    st.subheader("Simulator (external)")
    st.markdown(
        "Simulator has been moved out of the dashboard for stability. "
        "Run one of the scripts in the `simulator/` folder from a terminal to publish test data to MQTT."
    )
    st.code(
        "python simulator/normal.py --interval 2 --total 30\n"
        "python simulator/sensor_drift.py --interval 2 --total 30\n"
        "python simulator/overfeeding.py --interval 2 --total 30",
        language="bash"
    )

    st.markdown("---")
    st.subheader("📡 Gateway Status")

    try:
        mtime = os.path.getmtime(DATA_FILE)
        last = datetime.fromtimestamp(mtime)
        st.write("Last data received:", last.strftime("%Y-%m-%d %H:%M:%S"))
    except:
        st.write("No data file found.")

    st.markdown("### ESP32 Code & Flashing Help")

    esp32_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "esp32_mqtt_sim"))
    st.write("ESP32 code folder:", esp32_dir)

    # List available .ino files for download
    try:
        ino_files = [f for f in os.listdir(esp32_dir) if f.endswith('.ino')]
    except Exception:
        ino_files = []

    if ino_files:
        st.markdown("**Available ESP32 sketches:**")
        for fname in ino_files:
            fpath = os.path.join(esp32_dir, fname)
            try:
                with open(fpath, 'rb') as fh:
                    content = fh.read()
                st.write(fname)
                st.download_button(label=f"Download {fname}", data=content, file_name=fname, mime='text/x-csrc')
            except Exception as e:
                st.write(f"Cannot read {fname}: {e}")
    else:
        st.info("No .ino files found in the repository. Put your ESP32 sketch in `esp32_mqtt_sim/` or upload manually.")

    with st.expander("ESP32 quick checklist (what to edit before flashing)"):
        st.markdown("- Set `WIFI_SSID` and `WIFI_PASS` to your Wi‑Fi credentials.")
        st.markdown("- Set `MQTT_SERVER`, `MQTT_PORT` and `MQTT_TOPIC` to match the gateway (default: broker.hivemq.com, 1883, iot/tilapia/data).")
        st.markdown("- If using CSV-over-HTTP mode, set `SERVER_IP`/`CSV_URL` to the machine serving the CSV.")
        st.markdown("- Flash using Arduino IDE or PlatformIO; open Serial Monitor (115200) for logs.")
        st.markdown("- After flashing: run Gateway (`python gateway/gateway_full_model.py`) and verify messages arrive.")


# -----------------------------------------------------------
#                        REPORTS PAGE
# -----------------------------------------------------------
elif nav == "Reports":
    st.subheader("📦 Export Data & Reports")

    if not df.empty:
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button("📥 Download CSV", csv_bytes, "tilapia_data.csv", "text/csv")

        if st.button("📝 Generate PDF Report"):
            path = generate_pdf_report(df.tail(1))
            with open(path, "rb") as f:
                st.download_button("📄 Download PDF", f, "report.pdf", "application/pdf")


# ----------------- AUTO REFRESH -----------------
time.sleep(refresh)
st.rerun()


