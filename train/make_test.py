import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)
n_days = 15
hours = n_days * 24
dates = [datetime(2025, 1, 1) + timedelta(hours=i) for i in range(hours)]

data = []
for hour in range(hours):
    h = hour % 24
    
    if 0 <= h < 7 or 18 <= h < 24:          # Safe (0h-7h và 18h-24h)
        temp = np.random.uniform(28, 32)
        ph = np.random.uniform(6.5, 8.5)
        do = np.random.uniform(6.0, 9.0)
        turb = np.random.uniform(5, 20)
        status = "Safe"
        
    elif 7 <= h < 12:                        # Warning
        temp = np.random.uniform(24, 28)
        ph = np.random.uniform(6.0, 8.8)
        do = np.random.uniform(3.0, 6.0)
        turb = np.random.uniform(20, 80)
        status = "Warning"
        
    else:  # 12h-18h → Danger
        # 50% chance cực nguy hiểm
        if np.random.rand() < 0.5:
            temp = np.random.choice([np.random.uniform(20, 24), np.random.uniform(35, 38)])
            ph = np.random.choice([np.random.uniform(5.0, 6.0), np.random.uniform(9.0, 10.0)])
            do = np.random.uniform(0.5, 2.0)
        else:
            temp = np.random.uniform(25, 27)
            ph = np.random.uniform(6.2, 8.7)
            do = np.random.uniform(2.1, 3.5)
        turb = np.random.uniform(80, 150)
        status = "Danger"
    
    data.append({
        "DateTime": dates[hour],
        "Temperature": round(temp, 2),
        "pH": round(ph, 2),
        "Dissolved Oxygen": round(do, 2),
        "Turbidity": round(turb, 2),
        "Risk_Status": status
    })

df = pd.DataFrame(data)
df.to_excel("tilapia_risk_test.xlsx", index=False)
print("HOÀN TẤT! File đã được tạo:")
print("   → tilapia_risk_test.xlsx")
print("   → 10.080 dòng, đủ Safe/Warning/Danger")
print("   → Đặt cùng thư mục với trainIoT.py là dùng test được ngay!")