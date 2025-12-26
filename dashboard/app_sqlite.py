# dashboard/app_sqlite.py
"""
Streamlit Dashboard with SQLite Database Support
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time, io, os, json, sys
from datetime import datetime, timedelta
from pathlib import Path
from paho.mqtt import client as mqtt_client
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add database module to path
SCRIPT_DIR = Path(__file__).resolve().parent
DB_DIR = SCRIPT_DIR.parent / "database"
DB_CONFIG_FILE = DB_DIR / "db_config.py"

# Verify file exists
if not DB_CONFIG_FILE.exists():
    st.error(f"❌ Database config not found: {DB_CONFIG_FILE}")
    st.stop()

# Import database functions
import importlib.util
spec = importlib.util.spec_from_file_location("db_config", str(DB_CONFIG_FILE))
db_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(db_config)

get_latest_data = db_config.get_latest_data
get_all_data = db_config.get_all_data
get_latest_24h = db_config.get_latest_24h
get_risk_statistics = db_config.get_risk_statistics
get_table_info = db_config.get_table_info
export_to_csv = db_config.export_to_csv
init_database = db_config.init_database

# ----------------- CONFIG -----------------
ALERT_INTERVAL_MIN = 10  # Minutes between repeated alerts
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/tilapia/data"

# Initialize database
init_database()

# ----------------- EMAIL ALERT -----------------
def send_email_alert(to_email, subject, message, sender_email, sender_password):
    """
    Send email alert via Gmail SMTP
    Returns: (success: bool, error_message: str or None)
    """
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

    except smtplib.SMTPAuthenticationError:
        error = "Authentication failed. Use Gmail App Password"
        return False, error
    except Exception as e:
        return False, f"Email error: {str(e)}"


# ----------------- UTIL -----------------
def get_latest(df):
    if df.empty:
        return {}
    return df.iloc[-1].to_dict()


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
            pdf.cell(0, 10, line, ln=True)

    pdf.output(out_path)


# ========================================
# STREAMLIT UI
# ========================================

st.set_page_config(page_title="Tilapia IoT Monitor", layout="wide")

# Sidebar
with st.sidebar:
    st.title("🐟 Tilapia Water Monitor")
    st.markdown("**IoT + AI Dashboard (SQLite)**")
    
    # Database info
    st.markdown("---")
    st.subheader("📊 Database Info")
    try:
        info = get_table_info()
        st.metric("Total Records", f"{info['total_records']:,}")
        st.metric("DB Size", f"{info['db_size_mb']} MB")
        if info['last_timestamp']:
            st.info(f"Last update:\n{info['last_timestamp']}")
    except:
        st.warning("Database not initialized")
    
    # Data range selector
    st.markdown("---")
    st.subheader("📅 Data Range")
    data_range = st.selectbox(
        "Select range",
        ["Last 100", "Last 500", "Last 24h", "All Data"],
        index=0
    )
    
    # Export option
    st.markdown("---")
    if st.button("📥 Export to CSV"):
        try:
            export_path = "export_data.csv"
            export_to_csv(export_path, limit=1000)
            st.success(f"Exported to {export_path}")
        except Exception as e:
            st.error(f"Export failed: {e}")
    
    # Auto refresh
    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Auto Refresh (5s)", value=True)
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()

# Main content
st.title("🌊 Tilapia Water Quality Monitoring Dashboard")
st.markdown("Real-time monitoring with AI prediction (SQLite Backend)")

# Load data based on selection
try:
    if data_range == "Last 100":
        df = get_latest_data(100)
    elif data_range == "Last 500":
        df = get_latest_data(500)
    elif data_range == "Last 24h":
        df = get_latest_24h()
    else:  # All Data
        df = get_all_data()
    
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    
except Exception as e:
    st.error(f"❌ Database error: {e}")
    df = pd.DataFrame()

# Check if data exists
if df.empty:
    st.warning("⚠️ No data available. Start the gateway to collect data.")
    st.stop()

# Latest reading
latest = get_latest(df)
st.markdown("---")
st.subheader("📡 Latest Reading")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Temperature",
        f"{latest.get('temp', 0):.1f} °C",
        f"{latest.get('pred_temp', 0):.1f} (6h)" if latest.get('pred_temp') else None
    )

with col2:
    st.metric(
        "pH",
        f"{latest.get('ph', 0):.2f}",
        f"{latest.get('pred_ph', 0):.2f} (6h)" if latest.get('pred_ph') else None
    )

with col3:
    st.metric(
        "DO",
        f"{latest.get('do', 0):.2f} mg/L",
        f"{latest.get('pred_do', 0):.2f} (6h)" if latest.get('pred_do') else None
    )

with col4:
    st.metric(
        "Turbidity",
        f"{latest.get('turbidity', 0):.1f} NTU",
        f"{latest.get('pred_turb', 0):.1f} (6h)" if latest.get('pred_turb') else None
    )

with col5:
    status = latest.get('status', 'Unknown')
    color = {"Safe": "🟢", "Warning": "🟡", "Danger": "🔴"}.get(status, "⚪")
    st.metric("Status", f"{color} {status}")

# Risk Statistics
st.markdown("---")
st.subheader("📊 Risk Distribution")

try:
    risk_stats = get_risk_statistics()
    if risk_stats:
        risk_df = pd.DataFrame(risk_stats)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_pie = px.pie(
                risk_df,
                values='count',
                names='status',
                title='Risk Distribution',
                color='status',
                color_discrete_map={
                    'Safe': 'green',
                    'Warning': 'orange',
                    'Danger': 'red'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.dataframe(risk_df, hide_index=True)
except Exception as e:
    st.error(f"Could not load risk statistics: {e}")

# Time Series Charts
st.markdown("---")
st.subheader("📈 Time Series Data")

if len(df) > 0:
    # Temperature
    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['temp'],
        name='Actual',
        line=dict(color='blue', width=2)
    ))
    if 'pred_temp' in df.columns and df['pred_temp'].notna().any():
        fig_temp.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['pred_temp'],
            name='Predicted (6h)',
            line=dict(color='red', dash='dash')
        ))
    fig_temp.update_layout(title='Temperature (°C)', xaxis_title='Time', yaxis_title='°C')
    st.plotly_chart(fig_temp, use_container_width=True)
    
    # pH
    fig_ph = go.Figure()
    fig_ph.add_trace(go.Scatter(x=df['timestamp'], y=df['ph'], name='Actual'))
    if 'pred_ph' in df.columns and df['pred_ph'].notna().any():
        fig_ph.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['pred_ph'],
            name='Predicted (6h)',
            line=dict(dash='dash')
        ))
    fig_ph.update_layout(title='pH', xaxis_title='Time', yaxis_title='pH')
    st.plotly_chart(fig_ph, use_container_width=True)
    
    # DO
    fig_do = go.Figure()
    fig_do.add_trace(go.Scatter(x=df['timestamp'], y=df['do'], name='Actual'))
    if 'pred_do' in df.columns and df['pred_do'].notna().any():
        fig_do.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['pred_do'],
            name='Predicted (6h)',
            line=dict(dash='dash')
        ))
    fig_do.update_layout(title='Dissolved Oxygen (mg/L)', xaxis_title='Time', yaxis_title='mg/L')
    st.plotly_chart(fig_do, use_container_width=True)
    
    # Turbidity
    fig_turb = go.Figure()
    fig_turb.add_trace(go.Scatter(x=df['timestamp'], y=df['turbidity'], name='Actual'))
    if 'pred_turb' in df.columns and df['pred_turb'].notna().any():
        fig_turb.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['pred_turb'],
            name='Predicted (6h)',
            line=dict(dash='dash')
        ))
    fig_turb.update_layout(title='Turbidity (NTU)', xaxis_title='Time', yaxis_title='NTU')
    st.plotly_chart(fig_turb, use_container_width=True)

# Data Table
st.markdown("---")
st.subheader("📋 Recent Data")
st.dataframe(df.tail(50).iloc[::-1], use_container_width=True, hide_index=True)

# Download button
csv_bytes = df.to_csv(index=False).encode()
st.download_button(
    "📥 Download Full Data as CSV",
    csv_bytes,
    "tilapia_data.csv",
    "text/csv"
)

# Footer
st.markdown("---")
st.caption("🐟 Tilapia Smart Water Quality Monitoring System | SQLite Backend")
