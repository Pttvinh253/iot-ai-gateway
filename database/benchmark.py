# database/benchmark.py
"""
Benchmark: CSV vs SQLite performance comparison
"""

import time
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime

# Paths
CSV_PATH = Path(__file__).parent.parent / "dashboard" / "data_log.csv"
DB_PATH = Path(__file__).parent / "iot_data.db"


def benchmark_write_csv(num_records=100):
    """Benchmark CSV append performance"""
    print(f"\n📝 Testing CSV write ({num_records} records)...")
    
    start = time.time()
    
    for i in range(num_records):
        row = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'temp': 30.0 + i * 0.1,
            'ph': 7.0,
            'do': 6.0,
            'turbidity': 15.0,
            'status': 'Safe'
        }
        df = pd.DataFrame([row])
        df.to_csv(CSV_PATH, mode='a', header=False, index=False)
    
    elapsed = time.time() - start
    print(f"   Time: {elapsed:.3f}s ({num_records/elapsed:.1f} records/sec)")
    return elapsed


def benchmark_write_sqlite(num_records=100):
    """Benchmark SQLite insert performance"""
    print(f"\n💾 Testing SQLite write ({num_records} records)...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    start = time.time()
    
    for i in range(num_records):
        cursor.execute("""
            INSERT INTO sensor_logs (timestamp, temp, ph, do, turbidity, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            30.0 + i * 0.1,
            7.0,
            6.0,
            15.0,
            'Safe'
        ))
    
    conn.commit()
    elapsed = time.time() - start
    conn.close()
    
    print(f"   Time: {elapsed:.3f}s ({num_records/elapsed:.1f} records/sec)")
    return elapsed


def benchmark_read_csv():
    """Benchmark CSV read performance"""
    print(f"\n📖 Testing CSV read...")
    
    if not CSV_PATH.exists():
        print("   ⚠️  CSV file not found")
        return None
    
    start = time.time()
    df = pd.read_csv(CSV_PATH)
    elapsed = time.time() - start
    
    print(f"   Records: {len(df)}")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   File size: {CSV_PATH.stat().st_size / 1024:.1f} KB")
    return elapsed


def benchmark_read_sqlite():
    """Benchmark SQLite read performance"""
    print(f"\n💿 Testing SQLite read...")
    
    if not DB_PATH.exists():
        print("   ⚠️  Database not found")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    
    start = time.time()
    df = pd.read_sql_query("SELECT * FROM sensor_logs", conn)
    elapsed = time.time() - start
    
    conn.close()
    
    print(f"   Records: {len(df)}")
    print(f"   Time: {elapsed:.3f}s")
    print(f"   DB size: {DB_PATH.stat().st_size / 1024:.1f} KB")
    return elapsed


def benchmark_query_sqlite():
    """Benchmark SQLite query with WHERE clause"""
    print(f"\n🔍 Testing SQLite query (last 100 records)...")
    
    if not DB_PATH.exists():
        print("   ⚠️  Database not found")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    
    start = time.time()
    df = pd.read_sql_query("""
        SELECT * FROM sensor_logs 
        ORDER BY timestamp DESC 
        LIMIT 100
    """, conn)
    elapsed = time.time() - start
    
    conn.close()
    
    print(f"   Records: {len(df)}")
    print(f"   Time: {elapsed:.3f}s")
    return elapsed


def run_benchmark():
    """Run all benchmarks"""
    print("=" * 60)
    print("⚡ CSV vs SQLite Performance Benchmark")
    print("=" * 60)
    
    # Write benchmarks
    print("\n" + "─" * 60)
    print("📊 WRITE PERFORMANCE")
    print("─" * 60)
    
    csv_write_time = benchmark_write_csv(100)
    sqlite_write_time = benchmark_write_sqlite(100)
    
    if csv_write_time and sqlite_write_time:
        speedup = csv_write_time / sqlite_write_time
        print(f"\n   🏆 SQLite is {speedup:.1f}x faster at writing")
    
    # Read benchmarks
    print("\n" + "─" * 60)
    print("📊 READ PERFORMANCE (Full Table)")
    print("─" * 60)
    
    csv_read_time = benchmark_read_csv()
    sqlite_read_time = benchmark_read_sqlite()
    
    if csv_read_time and sqlite_read_time:
        speedup = csv_read_time / sqlite_read_time
        print(f"\n   🏆 SQLite is {speedup:.1f}x faster at reading")
    
    # Query benchmark (SQLite only)
    print("\n" + "─" * 60)
    print("📊 QUERY PERFORMANCE (with filtering)")
    print("─" * 60)
    
    benchmark_query_sqlite()
    print("\n   ℹ️  CSV requires loading entire file to filter")
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)
    print("\n✅ SQLite Advantages:")
    print("   • Faster writes (especially with transactions)")
    print("   • Much faster queries (indexes + WHERE clauses)")
    print("   • Smaller file size (binary format)")
    print("   • Thread-safe (no race conditions)")
    print("   • ACID compliance")
    
    print("\n⚠️  CSV Disadvantages:")
    print("   • Slow for large files")
    print("   • Must load entire file to query")
    print("   • Race conditions on concurrent writes")
    print("   • No indexing")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_benchmark()
