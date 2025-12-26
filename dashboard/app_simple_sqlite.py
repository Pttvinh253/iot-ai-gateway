# dashboard/app_simple_sqlite.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
from pathlib import Path
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
import io
import time
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC,
    DATABASE_PATH,
    EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, ALERT_INTERVAL_MIN,
    Thresholds
)
from logger import get_dashboard_logger

logger = get_dashboard_logger()

st.set_page_config(page_title="Tilapia Monitor", layout="wide", page_icon="🐟")

# Database path from config
DB_PATH = Path(DATABASE_PATH)

# ESP32 path
ESP32_DIR = PROJECT_ROOT / "esp32_mqtt_sim"

logger.info("=== Dashboard Started ===")
logger.info(f"Database: {DB_PATH}")

# Email alert function
def send_email_alert(to_email, subject, message, sender_email, sender_password):
    try:
        if not all([to_email, sender_email, sender_password]):
            return False, "Missing email credentials"
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
    except Exception as e:
        return False, str(e)

# PDF Report
def generate_pdf_report(df_tail):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Tilapia Water Quality Report", ln=True)
    if not df_tail.empty:
        latest = df_tail.iloc[-1]
        pdf.cell(0, 10, f"Time: {latest['timestamp']}", ln=True)
        pdf.cell(0, 10, f"Temperature: {latest['temp']} C", ln=True)
        pdf.cell(0, 10, f"pH: {latest['ph']}", ln=True)
        pdf.cell(0, 10, f"DO: {latest['do']} mg/L", ln=True)
        pdf.cell(0, 10, f"Turbidity: {latest['turbidity']} NTU", ln=True)
        pdf.cell(0, 10, f"Status: {latest['status']}", ln=True)
    return pdf.output(dest='S').encode('latin1')

def get_db_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

def init_db_if_needed():
    """Initialize database if table doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            temp REAL,
            ph REAL,
            do REAL,
            turbidity REAL,
            pred_temp REAL,
            pred_ph REAL,
            pred_do REAL,
            pred_turb REAL,
            sensor_risk TEXT,
            pred_risk TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def load_data(limit=100):
    conn = get_db_connection()
    query = f"SELECT * FROM sensor_logs ORDER BY timestamp DESC LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df.sort_values('timestamp')

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    total = cursor.execute("SELECT COUNT(*) FROM sensor_logs").fetchone()[0]
    conn.close()
    return {'total': total}

# Initialize database
try:
    init_db_if_needed()
except Exception as e:
    st.error(f"❌ Database error: {e}")
    st.error(f"Expected path: {DB_PATH}")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("🐟 Tilapia Monitor")
    st.markdown("**SQLite Database**")
    st.info(f"DB: {DB_PATH.name}")
    
    try:
        stats = get_stats()
        st.metric("Total Records", f"{stats['total']:,}")
    except Exception as e:
        st.error(f"Cannot read database: {e}")
        st.stop()
    
    # Navigation
    st.markdown("---")
    nav = st.radio("Navigation", ["Realtime", "Analytics", "History", "Devices", "Settings"], index=0)
    
    st.markdown("---")
    limit = st.selectbox("Show records", [50, 100, 200, 500], index=1)
    
    # Auto refresh
    st.markdown("---")
    refresh = st.slider("Auto refresh (sec)", 3, 30, 5)
    
    # MQTT Config
    st.markdown("---")
    st.subheader("MQTT Broker")
    st.info(f"**Host**: {MQTT_BROKER}")
    st.info(f"**Port**: {MQTT_PORT}")
    st.info(f"**Topic**: {MQTT_TOPIC}")
    st.caption("ℹ️ Configure in `.env` file")
    
    # Email Alerts
    st.markdown("---")
    st.subheader("📧 Email Alerts")
    
    if EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER:
        st.success("✅ Email configured")
        
        if st.button("📤 Send Test Email"):
            ok, error = send_email_alert(
                to_email=EMAIL_RECEIVER,
                subject="🧪 Test - Tilapia Monitoring System",
                message=f"""This is a test email from Dashboard.

System is working properly!

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Gateway automatically sends alerts on Danger detection.

Check gateway logs for alert history.
""",
                sender_email=EMAIL_SENDER,
                sender_password=EMAIL_PASSWORD
            )
            if ok:
                st.success("✅ Test email sent!")
            else:
                st.error(f"❌ Failed: {error}")
    else:
        st.warning("⚠️ Email not configured")
        st.info("Configure EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER in `.env` file")

# Main
st.title("🌊 Tilapia Water Quality Dashboard")
st.markdown("Real-time monitoring with SQLite backend")

try:
    df = load_data(limit)
except Exception as e:
    st.error(f"❌ Database error: {e}")
    st.stop()

if df.empty:
    st.warning("⚠️ No data. Start gateway to collect data.")
    st.stop()

# Latest reading
latest = df.iloc[-1]

# ==================== NAVIGATION ====================

if nav == "Realtime":
    st.subheader("📡 Real-time Monitoring")
    
    # Gauge charts + Status card
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
    
    with c1:
        fig_t = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest['temp'],
            title={"text": "Temperature (°C)"},
            gauge={"axis": {"range": [0, 40]}, "bar": {"color": "#2196F3"}}
        ))
        st.plotly_chart(fig_t, use_container_width=True)
    
    with c2:
        fig_ph = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest['ph'],
            title={"text": "pH"},
            gauge={"axis": {"range": [0, 14]}, "bar": {"color": "#9C27B0"}}
        ))
        st.plotly_chart(fig_ph, use_container_width=True)
    
    with c3:
        fig_do = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest['do'],
            title={"text": "DO (mg/L)"},
            gauge={"axis": {"range": [0, 10]}, "bar": {"color": "#009688"}}
        ))
        st.plotly_chart(fig_do, use_container_width=True)
    
    with c4:
        fig_turb = go.Figure(go.Indicator(
            mode="gauge+number",
            value=latest['turbidity'],
            title={"text": "Turbidity (NTU)"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#795548"}}
        ))
        st.plotly_chart(fig_turb, use_container_width=True)
    
    # Status card - BEAUTIFUL VERSION
    with c5:
        status = latest['status']
        status_color = {
            "Safe": "#4CAF50",
            "Warning": "#FFC107",
            "Danger": "#F44336"
        }.get(status, "gray")
        
        st.markdown(
            f"""<div style='background:{status_color};padding:20px;border-radius:10px;text-align:center;color:white;height:250px;display:flex;flex-direction:column;justify-content:center;'>
            <h3 style='margin:0;font-size:24px;'>Status</h3>
            <h2 style='margin:10px 0 0 0;font-size:32px;font-weight:bold;'>{status}</h2>
            </div>""",
            unsafe_allow_html=True
        )
    
    # Alert banner based on status
    st.markdown("---")
    if status == "Danger":
        st.error("🔴 **DANGER**: Critical water quality detected! Immediate action required!")
    elif status == "Warning":
        st.warning("🟡 **WARNING**: Suboptimal conditions. Monitor closely.")
    else:
        st.success("🟢 **SAFE**: Water quality is optimal for tilapia.")
    
    # Predictions with nice cards
    st.markdown("---")
    st.subheader("🔮 6-Hour Predictions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pred = latest.get('pred_temp')
        if pd.notna(pred):
            delta = pred - latest['temp']
            color = "🔴" if delta > 2 else "🔵" if delta < -2 else "🟢"
            st.markdown(f"""
            <div style='background:#f0f2f6;padding:15px;border-radius:8px;text-align:center;'>
                <p style='margin:0;color:#666;font-size:14px;'>Temperature (6h)</p>
                <h2 style='margin:5px 0;color:#2196F3;'>{pred:.1f}°C</h2>
                <p style='margin:0;color:{"red" if delta > 0 else "blue"};font-size:16px;'>{color} {delta:+.1f}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Insufficient data")
    
    with col2:
        pred = latest.get('pred_ph')
        if pd.notna(pred):
            delta = pred - latest['ph']
            color = "🔴" if abs(delta) > 0.5 else "🟢"
            st.markdown(f"""
            <div style='background:#f0f2f6;padding:15px;border-radius:8px;text-align:center;'>
                <p style='margin:0;color:#666;font-size:14px;'>pH (6h)</p>
                <h2 style='margin:5px 0;color:#9C27B0;'>{pred:.2f}</h2>
                <p style='margin:0;color:{"red" if abs(delta) > 0.3 else "green"};font-size:16px;'>{color} {delta:+.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Insufficient data")
    
    with col3:
        pred = latest.get('pred_do')
        if pd.notna(pred):
            delta = pred - latest['do']
            color = "🔴" if pred < 4 else "🟡" if pred < 6 else "🟢"
            st.markdown(f"""
            <div style='background:#f0f2f6;padding:15px;border-radius:8px;text-align:center;'>
                <p style='margin:0;color:#666;font-size:14px;'>DO (6h)</p>
                <h2 style='margin:5px 0;color:#009688;'>{pred:.2f}</h2>
                <p style='margin:0;color:{"red" if delta < 0 else "green"};font-size:16px;'>{color} {delta:+.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Insufficient data")
    
    with col4:
        pred = latest.get('pred_turb')
        if pd.notna(pred):
            delta = pred - latest['turbidity']
            color = "🔴" if pred > 50 else "🟡" if pred > 30 else "🟢"
            st.markdown(f"""
            <div style='background:#f0f2f6;padding:15px;border-radius:8px;text-align:center;'>
                <p style='margin:0;color:#666;font-size:14px;'>Turbidity (6h)</p>
                <h2 style='margin:5px 0;color:#795548;'>{pred:.1f}</h2>
                <p style='margin:0;color:{"red" if delta > 0 else "green"};font-size:16px;'>{color} {delta:+.1f}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Insufficient data")

elif nav == "Analytics":
    st.subheader("📊 Analytics & Statistics")
    
    # Risk distribution
    conn = get_db_connection()
    risk_df = pd.read_sql_query("""
        SELECT status, COUNT(*) as count 
        FROM sensor_logs 
        GROUP BY status
    """, conn)
    conn.close()
    
    if not risk_df.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            fig_pie = px.pie(risk_df, values='count', names='status',
                             title='Risk Distribution',
                             color='status',
                             color_discrete_map={'Safe': 'green', 'Warning': 'orange', 'Danger': 'red'})
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.dataframe(risk_df, hide_index=True)
    
    # Risk Timeline
    st.markdown("---")
    st.subheader("📌 Risk Level Timeline")
    fig_risk = px.scatter(
        df, x="timestamp", y=[1]*len(df),
        color="status",
        color_discrete_map={"Safe":"green","Warning":"orange","Danger":"red"},
        title="Risk Events Over Time"
    )
    fig_risk.update_yaxes(visible=False)
    st.plotly_chart(fig_risk, use_container_width=True)
    
    # Time series charts with predictions
    st.markdown("---")
    st.subheader("📈 Parameter Trends (Actual vs Predicted)")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Temperature", "pH", "DO", "Turbidity"])
    
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temp'], name='Actual', line=dict(color='blue', width=2)))
        if df['pred_temp'].notna().any():
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['pred_temp'], name='Predicted (6h)', line=dict(dash='dash', color='red', width=2)))
        fig.update_layout(title='Temperature (°C)', xaxis_title='Time', yaxis_title='°C', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ph'], name='Actual', line=dict(color='purple', width=2)))
        if df['pred_ph'].notna().any():
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['pred_ph'], name='Predicted (6h)', line=dict(dash='dash', color='red', width=2)))
        fig.update_layout(title='pH', xaxis_title='Time', yaxis_title='pH', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['do'], name='Actual', line=dict(color='teal', width=2)))
        if df['pred_do'].notna().any():
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['pred_do'], name='Predicted (6h)', line=dict(dash='dash', color='red', width=2)))
        fig.update_layout(title='Dissolved Oxygen (mg/L)', xaxis_title='Time', yaxis_title='mg/L', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['turbidity'], name='Actual', line=dict(color='orange', width=2)))
        if df['pred_turb'].notna().any():
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['pred_turb'], name='Predicted (6h)', line=dict(dash='dash', color='red', width=2)))
        fig.update_layout(title='Turbidity (NTU)', xaxis_title='Time', yaxis_title='NTU', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Prediction accuracy statistics
    st.markdown("---")
    st.subheader("🎯 Prediction Accuracy")
    
    pred_cols = []
    if df['pred_temp'].notna().any():
        pred_cols.extend(["temp", "pred_temp"])
    if df['pred_ph'].notna().any():
        pred_cols.extend(["ph", "pred_ph"])
    if df['pred_do'].notna().any():
        pred_cols.extend(["do", "pred_do"])
    if df['pred_turb'].notna().any():
        pred_cols.extend(["turbidity", "pred_turb"])
    
    if pred_cols:
        st.write(df[pred_cols].tail(50).describe())
    else:
        st.info("No prediction data available yet. Wait for 24h of data.")
    
    # Statistics
    st.markdown("---")
    st.subheader("📉 Statistical Summary")
    
    summary = df[['temp', 'ph', 'do', 'turbidity']].describe().T
    summary.columns = ['Count', 'Mean', 'Std', 'Min', '25%', '50%', '75%', 'Max']
    st.dataframe(summary, use_container_width=True)
    
    # Daily statistics
    st.markdown("---")
    st.subheader("📅 Daily Statistics")
    
elif nav == "Devices":
    st.subheader("🛠️ Devices & System")
    
    # MQTT Info
    st.markdown("### 📡 MQTT Broker Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Host**: {MQTT_BROKER}")
        st.info(f"**Port**: {MQTT_PORT}")
    with col2:
        st.info(f"**Topic**: {MQTT_TOPIC}")
    
    # Gateway Status
    st.markdown("---")
    st.subheader("🔧 Gateway Status")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    last_record = cursor.execute("SELECT timestamp FROM sensor_logs ORDER BY timestamp DESC LIMIT 1").fetchone()
    conn.close()
    
    if last_record:
        last_time = pd.to_datetime(last_record[0])
        time_diff = (datetime.now() - last_time).total_seconds() / 60
        
        if time_diff < 5:
            st.success(f"✅ Gateway ONLINE - Last data: {last_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff:.1f} min ago)")
        elif time_diff < 30:
            st.warning(f"⚠️ Gateway IDLE - Last data: {last_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff:.1f} min ago)")
        else:
            st.error(f"❌ Gateway OFFLINE - Last data: {last_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff:.1f} min ago)")
    else:
        st.error("❌ No data received yet")
    
    # Simulator Instructions
    st.markdown("---")
    st.subheader("🎮 Simulator")
    
    st.markdown("""
    Simulator scripts are in the `simulator/` folder. Run from terminal to generate test data:
    """)
    
    st.code("""
# Normal operation
python simulator/normal.py --interval 2 --total 30

# Sensor drift scenario
python simulator/sensor_drift.py --interval 2 --total 30

# Overfeeding scenario
python simulator/overfeeding.py --interval 2 --total 30

# Or use the simple publisher
python gateway/simulator_publish.py
    """, language="bash")
    
    # ESP32 Section
    st.markdown("---")
    st.subheader("📱 ESP32 Setup")
    
    if ESP32_DIR.exists():
        st.success(f"✅ ESP32 code folder found: `{ESP32_DIR.name}`")
        
        try:
            ino_files = list(ESP32_DIR.glob("*.ino"))
            if ino_files:
                st.markdown("**Available ESP32 sketches:**")
                for ino_file in ino_files:
                    with open(ino_file, 'rb') as f:
                        st.download_button(
                            f"📥 {ino_file.name}",
                            f.read(),
                            file_name=ino_file.name,
                            mime='text/plain'
                        )
        except Exception as e:
            st.error(f"Error reading ESP32 files: {e}")
        
        with st.expander("📋 ESP32 Setup Checklist"):
            st.markdown("""
            **Before flashing:**
            1. Set `WIFI_SSID` and `WIFI_PASS` to your WiFi credentials
            2. Set `MQTT_SERVER` to broker address (default: broker.hivemq.com)
            3. Set `MQTT_PORT` to 1883
            4. Set `MQTT_TOPIC` to `iot/tilapia/data`
            
            **Flashing:**
            - Use Arduino IDE or PlatformIO
            - Select board: ESP32 Dev Module
            - Upload speed: 921600
            - Open Serial Monitor (115200 baud) to see logs
            
            **Verification:**
            - Check Serial Monitor for WiFi connection
            - Verify MQTT broker connection
            - Watch dashboard for incoming data
            """)
    else:
        st.warning(f"⚠️ ESP32 code folder not found at: {ESP32_DIR}")

elif nav == "Settings":
    st.subheader("⚙️ System Settings")
    
    # Database Information
    st.markdown("### 💾 Database Information")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Location**: {DB_PATH.name}")
        st.info(f"**Size**: {DB_PATH.stat().st_size / 1024:.2f} KB")
    
    with col2:
        conn = get_db_connection()
        cursor = conn.cursor()
        first = cursor.execute("SELECT MIN(timestamp) FROM sensor_logs").fetchone()[0]
        last = cursor.execute("SELECT MAX(timestamp) FROM sensor_logs").fetchone()[0]
        total = cursor.execute("SELECT COUNT(*) FROM sensor_logs").fetchone()[0]
        conn.close()
        st.info(f"**Records**: {total:,}")
        st.info(f"**Range**: {first} → {last}")
    
    # Email Alert System Info
    st.markdown("---")
    st.markdown("### 📧 Email Auto-Alert System")
    
    st.markdown("""
    **Gateway automatically sends email alerts when Danger is detected!**
    
    **Features:**
    - 🚨 Auto-send on Danger detection
    - ⏰ Anti-spam interval: {interval} minutes
    - ✅ Configured in `.env` file
    - 📝 Check gateway logs for alert history
    
    **Current Configuration:**
    """.format(interval=ALERT_INTERVAL_MIN))
    
    if EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER:
        st.success("✅ Email alerts enabled in Gateway")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Sender**: {EMAIL_SENDER}")
            st.info(f"**Alert Interval**: {ALERT_INTERVAL_MIN} min")
        with col2:
            st.info(f"**Receiver**: {EMAIL_RECEIVER}")
            st.info(f"**Status**: Active")
        
        st.markdown("""
        **How it works:**
        1. Gateway monitors water quality 24/7
        2. When Danger detected → Email sent automatically
        3. Won't spam - waits {interval} min between alerts
        4. Email includes sensor data + recommendations
        
        **To test**: Check sidebar for "Send Test Email" button
        """.format(interval=ALERT_INTERVAL_MIN))
    else:
        st.warning("⚠️ Email alerts not configured")
        st.info("To enable: Configure EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER in `.env` file")
    
    # Data Management
    st.markdown("---")
    st.markdown("### 🗄️ Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Export Full Database"):
            conn = get_db_connection()
            full_df = pd.read_sql_query("SELECT * FROM sensor_logs ORDER BY timestamp DESC", conn)
            conn.close()
            csv = full_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "full_database.csv", "text/csv")
    
    with col2:
        if st.button("📊 Generate PDF Report"):
            pdf_bytes = generate_pdf_report(df.tail(20))
            st.download_button("📥 Download PDF", pdf_bytes, "tilapia_report.pdf", "application/pdf")
    
    with col3:
        days_to_keep = st.number_input("Keep last N days", min_value=1, max_value=365, value=30)
        if st.button(f"🗑️ Delete data older than {days_to_keep} days"):
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                # Sử dụng parameterized query an toàn hơn
                cursor.execute("""
                    DELETE FROM sensor_logs 
                    WHERE timestamp < datetime('now', ? || ' days')
                """, (f'-{days_to_keep}',))
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                
                if deleted > 0:
                    st.success(f"✅ Deleted {deleted} old records")
                else:
                    st.info(f"ℹ️ No records older than {days_to_keep} days found")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error deleting data: {str(e)}")
    
    # Danger zone
    st.markdown("---")
    st.markdown("### ⚠️ Danger Zone")
    
    # Checkbox phải ở ngoài và được check trước
    confirm_delete = st.checkbox("⚠️ I understand this will delete ALL data permanently")
    
    if st.button("🗑️ Clear ALL Data", type="primary"):
        if confirm_delete:
            conn = get_db_connection()
            conn.execute("DELETE FROM sensor_logs")
            conn.commit()
            conn.close()
            st.success("✅ All data cleared!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Please confirm by checking the box above!")

elif nav == "History":
    st.subheader("📋 Historical Data")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect("Filter by status", ['Safe', 'Warning', 'Danger'], default=['Safe', 'Warning', 'Danger'])
    with col2:
        date_range = st.date_input("Date range", value=(df['timestamp'].min().date(), df['timestamp'].max().date()))
    
    # Apply filters
    filtered_df = df[df['status'].isin(status_filter)]
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df['timestamp'].dt.date >= start_date) & (filtered_df['timestamp'].dt.date <= end_date)]
    
    st.write(f"Showing {len(filtered_df)} of {len(df)} records")
    
    # Display table
    display_cols = ['timestamp', 'temp', 'ph', 'do', 'turbidity', 'pred_temp', 'pred_ph', 'pred_do', 'pred_turb', 'status']
    st.dataframe(filtered_df[display_cols].iloc[::-1], use_container_width=True, hide_index=True)
    
    # Download options
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "tilapia_data.csv", "text/csv")
    
    with col2:
        if st.button("📄 Generate PDF Report"):
            pdf_bytes = generate_pdf_report(filtered_df)
            st.download_button("📥 Download PDF", pdf_bytes, "tilapia_report.pdf", "application/pdf")

# Footer & Auto-refresh (only for Realtime page)
st.markdown("---")
st.caption(f"🐟 Tilapia Water Quality Monitoring | Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Only auto-refresh on Realtime page to reduce console errors and improve performance
if nav == "Realtime":
    time.sleep(refresh)
    st.rerun()
