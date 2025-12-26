# database/db_config.py
"""
SQLite Database Configuration & Helper Functions
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
import threading

# Database path
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "iot_data.db"

# Thread-safe lock for concurrent access
db_lock = threading.Lock()


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_database():
    """Initialize database schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create sensor_logs table
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
    
    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON sensor_logs(timestamp DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status 
        ON sensor_logs(status)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at 
        ON sensor_logs(created_at DESC)
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized at: {DB_PATH}")


def insert_sensor_data(data: dict):
    """
    Insert sensor data with predictions
    
    Args:
        data: Dictionary containing sensor readings and predictions
    """
    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sensor_logs (
                timestamp, temp, ph, do, turbidity,
                pred_temp, pred_ph, pred_do, pred_turb,
                sensor_risk, pred_risk, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('timestamp'),
            data.get('temp'),
            data.get('ph'),
            data.get('do'),
            data.get('turbidity'),
            data.get('pred_temp'),
            data.get('pred_ph'),
            data.get('pred_do'),
            data.get('pred_turb'),
            data.get('sensor_risk'),
            data.get('pred_risk'),
            data.get('status')
        ))
        
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        
        return row_id


def get_latest_data(limit=100):
    """Get latest N records"""
    conn = get_connection()
    df = pd.read_sql_query(f"""
        SELECT * FROM sensor_logs 
        ORDER BY timestamp DESC 
        LIMIT {limit}
    """, conn)
    conn.close()
    return df


def get_data_by_timerange(start_time, end_time):
    """Get data within time range"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM sensor_logs 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """, conn, params=(start_time, end_time))
    conn.close()
    return df


def get_all_data():
    """Get all data (use with caution for large datasets)"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM sensor_logs 
        ORDER BY timestamp DESC
    """, conn)
    conn.close()
    return df


def get_risk_statistics():
    """Get risk distribution statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = cursor.execute("""
        SELECT 
            status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM sensor_logs), 2) as percentage
        FROM sensor_logs
        GROUP BY status
        ORDER BY count DESC
    """).fetchall()
    
    conn.close()
    return [dict(row) for row in stats]


def get_latest_24h():
    """Get data from last 24 hours"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT * FROM sensor_logs 
        WHERE timestamp >= datetime('now', '-24 hours')
        ORDER BY timestamp ASC
    """, conn)
    conn.close()
    return df


def delete_old_data(days=30):
    """Delete data older than N days"""
    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM sensor_logs 
            WHERE timestamp < datetime('now', ? || ' days')
        """, (f'-{days}',))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted


def export_to_csv(output_path, limit=None):
    """Export database to CSV"""
    conn = get_connection()
    
    query = "SELECT * FROM sensor_logs ORDER BY timestamp DESC"
    if limit:
        query += f" LIMIT {limit}"
    
    df = pd.read_sql_query(query, conn)
    df.to_csv(output_path, index=False)
    conn.close()
    
    print(f"✅ Exported {len(df)} records to {output_path}")


def get_table_info():
    """Get database statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total records
    total = cursor.execute("SELECT COUNT(*) FROM sensor_logs").fetchone()[0]
    
    # First and last timestamp
    first = cursor.execute("SELECT MIN(timestamp) FROM sensor_logs").fetchone()[0]
    last = cursor.execute("SELECT MAX(timestamp) FROM sensor_logs").fetchone()[0]
    
    # Database size
    db_size = DB_PATH.stat().st_size / (1024 * 1024)  # MB
    
    conn.close()
    
    return {
        'total_records': total,
        'first_timestamp': first,
        'last_timestamp': last,
        'db_size_mb': round(db_size, 2)
    }


if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Show info
    info = get_table_info()
    print("\n📊 Database Info:")
    print(f"   Total records: {info['total_records']}")
    print(f"   First record: {info['first_timestamp']}")
    print(f"   Last record: {info['last_timestamp']}")
    print(f"   Size: {info['db_size_mb']} MB")
