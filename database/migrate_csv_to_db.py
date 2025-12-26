# database/migrate_csv_to_db.py
"""
Migrate existing CSV data to SQLite database
"""

import pandas as pd
from pathlib import Path
from db_config import init_database, insert_sensor_data, get_table_info
from tqdm import tqdm

# CSV file path
CSV_PATH = Path(__file__).parent.parent / "dashboard" / "data_log.csv"


def migrate_csv_to_sqlite():
    """Migrate all data from CSV to SQLite"""
    
    print("🔄 Starting migration from CSV to SQLite...")
    
    # Initialize database
    init_database()
    
    # Check if CSV exists
    if not CSV_PATH.exists():
        print(f"⚠️  CSV file not found: {CSV_PATH}")
        print("   No data to migrate.")
        return
    
    # Read CSV
    print(f"📂 Reading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"   Found {len(df)} records")
    
    if len(df) == 0:
        print("   No data to migrate.")
        return
    
    # Validate columns
    required_cols = ['timestamp', 'temp', 'ph', 'do', 'turbidity', 'status']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"❌ Missing columns: {missing}")
        return
    
    # Insert data
    print("\n💾 Inserting data into SQLite...")
    success = 0
    failed = 0
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Migrating"):
        try:
            data = {
                'timestamp': row['timestamp'],
                'temp': row.get('temp'),
                'ph': row.get('ph'),
                'do': row.get('do'),
                'turbidity': row.get('turbidity'),
                'pred_temp': row.get('pred_temp'),
                'pred_ph': row.get('pred_ph'),
                'pred_do': row.get('pred_do'),
                'pred_turb': row.get('pred_turb'),
                'sensor_risk': row.get('sensor_risk'),
                'pred_risk': row.get('pred_risk'),
                'status': row.get('status')
            }
            insert_sensor_data(data)
            success += 1
        except Exception as e:
            failed += 1
            if failed <= 5:  # Only show first 5 errors
                print(f"\n❌ Error at row {idx}: {e}")
    
    print(f"\n✅ Migration completed!")
    print(f"   Success: {success}")
    print(f"   Failed: {failed}")
    
    # Show database info
    info = get_table_info()
    print(f"\n📊 Database Statistics:")
    print(f"   Total records: {info['total_records']}")
    print(f"   Database size: {info['db_size_mb']} MB")
    print(f"   Time range: {info['first_timestamp']} → {info['last_timestamp']}")


if __name__ == "__main__":
    migrate_csv_to_sqlite()
