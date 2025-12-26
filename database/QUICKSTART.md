# 🚀 Quick Start - SQLite Migration

## Các bước thực hiện nhanh:

### 1. Test database (5 giây)

```powershell
cd database
python test_database.py
```

### 2. Migrate dữ liệu cũ (nếu có)

```powershell
python migrate_csv_to_db.py
```

### 3. Chạy gateway mới

```powershell
cd ..\gateway
python gateway_sqlite.py
```

### 4. Chạy dashboard mới (terminal mới)

```powershell
cd dashboard
streamlit run app_sqlite.py
```

## ✅ Xong! Hệ thống đã dùng SQLite

---

## 📊 So sánh nhanh

|                  | CSV (Cũ) | SQLite (Mới)         |
| ---------------- | -------- | -------------------- |
| **Tốc độ ghi**   | Chậm     | ⚡ Nhanh hơn 3-5x    |
| **Tốc độ query** | Rất chậm | ⚡ Nhanh hơn 10-100x |
| **Thread-safe**  | ❌       | ✅                   |
| **File size**    | Lớn      | Nhỏ hơn 30-50%       |

---

## 🔧 Commands hữu ích

```powershell
# Xem thông tin database
python -c "from database.db_config import get_table_info; print(get_table_info())"

# Export sang CSV
python -c "from database.db_config import export_to_csv; export_to_csv('backup.csv')"

# Xóa data cũ hơn 30 ngày
python -c "from database.db_config import delete_old_data; print(f'Deleted {delete_old_data(30)} records')"

# Benchmark hiệu suất
python database\benchmark.py
```

---

Đọc **README_SQLITE.md** để biết chi tiết đầy đủ!
