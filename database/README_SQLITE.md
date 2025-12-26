# 🗄️ SQLite Database Guide

## 📌 Tại sao SQLite?

✅ **Hiệu suất**: Indexing, query optimization  
✅ **Thread-safe**: Nhiều process truy cập cùng lúc  
✅ **ACID compliance**: Đảm bảo tính toàn vẹn dữ liệu  
✅ **Dễ query**: SQL thay vì pandas filtering  
✅ **Không cần server**: File-based database  

---

## 🚀 Khởi chạy nhanh

**Xem [QUICKSTART.md](QUICKSTART.md)**

---

## 📊 Database Schema

```sql
CREATE TABLE sensor_logs (
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
);

CREATE INDEX idx_timestamp ON sensor_logs(timestamp DESC);
CREATE INDEX idx_status ON sensor_logs(status);
CREATE INDEX idx_created_at ON sensor_logs(created_at DESC);
```

---

## 🛠️ Sử dụng trong code

### Lấy dữ liệu mới nhất
```python
from database.db_config import get_latest_data

df = get_latest_data(limit=100)  # 100 records gần nhất
```

### Lấy theo khoảng thời gian
```python
from database.db_config import get_data_by_timerange

df = get_data_by_timerange('2025-12-01', '2025-12-04')
```

### Lấy 24h gần nhất
```python
from database.db_config import get_latest_24h

df = get_latest_24h()
```

---

## 📈 So sánh CSV vs SQLite

| Tính năng | CSV | SQLite |
|-----------|-----|--------|
| Ghi dữ liệu | Append | INSERT + transaction |
| Đọc dữ liệu | Load toàn bộ | Query điều kiện |
| Concurrent | ❌ | ✅ |
| SQL queries | ❌ | ✅ |
| Indexing | ❌ | ✅ |
| Size | Lớn | -30-50% |

---

## 📁 Files

- `db_config.py`: Database config & helper functions
- `migrate_csv_to_db.py`: Migration từ CSV
- `test_database.py`: Test script
- `benchmark.py`: So sánh hiệu suất
- `iot_data.db`: Database (auto-created)
from database.db_config import get_risk_statistics

stats = get_risk_statistics()
# Output: [{'status': 'Safe', 'count': 500, 'percentage': 60.5}, ...]
```

### **5. Xóa dữ liệu cũ**

```python
from database.db_config import delete_old_data

deleted = delete_old_data(days=30)  # Xóa data > 30 ngày
print(f"Deleted {deleted} old records")
```

### **6. Export sang CSV**

```python
from database.db_config import export_to_csv

export_to_csv('backup.csv', limit=1000)
```

---

## 🔄 Backup & Recovery

### **Backup database**

```powershell
# Simple copy
Copy-Item database\iot_data.db database\iot_data_backup_$(Get-Date -Format 'yyyyMMdd').db

# Or export to CSV
python -c "from database.db_config import export_to_csv; export_to_csv('backup.csv')"
```

### **Restore từ backup**

```powershell
# Restore .db file
Copy-Item database\iot_data_backup_20251204.db database\iot_data.db

# Import từ CSV
python database\migrate_csv_to_db.py
```

---

## 🧪 Testing

### **Test database connection**

```python
from database.db_config import get_table_info, init_database

init_database()
info = get_table_info()
print(info)
```

### **Test insert data**

```python
from database.db_config import insert_sensor_data

data = {
    'timestamp': '2025-12-04 10:00:00',
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
}

record_id = insert_sensor_data(data)
print(f"Inserted record ID: {record_id}")
```

---

## ⚠️ Lưu ý

1. **File CSV cũ vẫn được giữ nguyên** - Không tự động xóa
2. **Chạy gateway_sqlite.py** thay vì gateway_full_model.py
3. **Chạy app_sqlite.py** thay vì app.py
4. Database file: `database/iot_data.db` (~100KB cho 1000 records)
5. **Concurrent access**: SQLite tự động xử lý, không lo race condition

---

## 🚨 Troubleshooting

### **Lỗi: "database is locked"**

- Đợi vài giây và thử lại
- SQLite tự động retry với timeout

### **Lỗi: "no such table: sensor_logs"**

```powershell
python database\db_config.py
```

### **Database file quá lớn**

```python
from database.db_config import delete_old_data

# Xóa data cũ hơn 30 ngày
deleted = delete_old_data(days=30)

# Hoặc VACUUM để compact database
import sqlite3
conn = sqlite3.connect('database/iot_data.db')
conn.execute('VACUUM')
conn.close()
```

---

## 📈 Performance Tips

1. **Batch insert** (nếu có nhiều records):

```python
# Thay vì insert từng record
for data in records:
    insert_sensor_data(data)

# Dùng executemany (nhanh hơn)
conn.executemany("INSERT INTO ...", records)
```

2. **Index optimization**: Đã tạo sẵn indexes cho timestamp và status

3. **Query optimization**: Dùng LIMIT khi không cần toàn bộ data

---

## ✅ Checklist Migration

- [ ] Cài đặt `tqdm` nếu chưa có
- [ ] Chạy `python database/db_config.py` để init
- [ ] Chạy `python database/migrate_csv_to_db.py` để migrate
- [ ] Test gateway: `python gateway/gateway_sqlite.py`
- [ ] Test dashboard: `streamlit run dashboard/app_sqlite.py`
- [ ] Backup CSV cũ: `Copy-Item dashboard\data_log.csv dashboard\data_log_backup.csv`
- [ ] Update README.md với hướng dẫn mới

---

## 🎉 Hoàn tất!

Hệ thống đã được nâng cấp lên SQLite database!

**Next steps:**

- Có thể xóa file CSV cũ sau khi confirm SQLite hoạt động tốt
- Cân nhắc migrate lên PostgreSQL/MySQL cho production scale
- Thêm tính năng auto-cleanup old data
- Implement database replication cho high availability
