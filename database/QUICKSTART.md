# 🚀 SQLite Quick Start

## 3 bước chạy nhanh:

### 1️⃣ Test database
```powershell
cd database
python test_database.py
```

### 2️⃣ Chạy Gateway (SQLite)
```powershell
cd ..\gateway
python gateway_sqlite.py
```

### 3️⃣ Chạy Dashboard (terminal mới)
```powershell
cd dashboard
streamlit run app_sqlite.py
```

✅ **Done!** Hệ thống sử dụng SQLite

---

## 📊 CSV vs SQLite

| Tính năng | CSV | SQLite |
|-----------|-----|--------|
| Tốc độ ghi | Chậm | ⚡ Nhanh 3-5x |
| Tốc độ đọc | Rất chậm | ⚡ Nhanh 10-100x |
| Thread-safe | ❌ | ✅ |
| Dung lượng | Lớn | -30-50% |

---

## 🔧 Các lệnh hữu ích

Xem chi tiết tại [README_SQLITE.md](README_SQLITE.md)
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
