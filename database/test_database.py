# database/test_database.py
"""
Quick test script for SQLite database
"""

from db_config import (
    init_database,
    insert_sensor_data,
    get_latest_data,
    get_table_info,
    get_risk_statistics
)
from datetime import datetime

def test_database():
    print("=" * 60)
    print("🧪 Testing SQLite Database")
    print("=" * 60)
    
    # 1. Initialize
    print("\n1️⃣ Initializing database...")
    init_database()
    print("   ✅ Database initialized")
    
    # 2. Insert test data
    print("\n2️⃣ Inserting test data...")
    test_records = [
        {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'temp': 30.5,
            'ph': 7.2,
            'do': 6.5,
            'turbidity': 15.0,
            'pred_temp': 30.3,
            'pred_ph': 7.1,
            'pred_do': 6.4,
            'pred_turb': 14.8,
            'sensor_risk': 'Safe',
            'pred_risk': 'Safe',
            'status': 'Safe'
        },
        {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'temp': 28.0,
            'ph': 6.8,
            'do': 5.0,
            'turbidity': 25.0,
            'pred_temp': 27.8,
            'pred_ph': 6.7,
            'pred_do': 4.9,
            'pred_turb': 26.0,
            'sensor_risk': 'Warning',
            'pred_risk': 'Warning',
            'status': 'Warning'
        }
    ]
    
    for i, record in enumerate(test_records, 1):
        record_id = insert_sensor_data(record)
        print(f"   ✅ Inserted record {i} (ID: {record_id})")
    
    # 3. Read data
    print("\n3️⃣ Reading latest data...")
    df = get_latest_data(limit=5)
    print(f"   ✅ Retrieved {len(df)} records")
    if not df.empty:
        print("\n   Latest record:")
        latest = df.iloc[0]
        print(f"      Timestamp: {latest['timestamp']}")
        print(f"      Temp: {latest['temp']}°C")
        print(f"      pH: {latest['ph']}")
        print(f"      Status: {latest['status']}")
    
    # 4. Get statistics
    print("\n4️⃣ Risk statistics...")
    stats = get_risk_statistics()
    if stats:
        print("   Distribution:")
        for stat in stats:
            print(f"      {stat['status']}: {stat['count']} ({stat['percentage']}%)")
    
    # 5. Database info
    print("\n5️⃣ Database information...")
    info = get_table_info()
    print(f"   Total records: {info['total_records']}")
    print(f"   Database size: {info['db_size_mb']} MB")
    print(f"   First record: {info['first_timestamp']}")
    print(f"   Last record: {info['last_timestamp']}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_database()
