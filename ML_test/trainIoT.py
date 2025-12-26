# # ============================================================
# #  TILAPIA WATER QUALITY – MACHINE LEARNING MODULE (TRAIN)
# #  Predict 6-hour future water quality & classify risk levels
# # ============================================================

# import pandas as pd
# import numpy as np
# import joblib
# from sklearn.model_selection import TimeSeriesSplit
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
# from xgboost import XGBRegressor
# import matplotlib.pyplot as plt
# import seaborn as sns
# from matplotlib.patches import Patch
# import warnings
# from pathlib import Path
# from lightgbm import LGBMRegressor

# warnings.filterwarnings("ignore")

# # ------------------------------------------------------------
# # 1. CONFIGURATION
# # ------------------------------------------------------------

# CSV_PATH     = Path(__file__).resolve().parent / "tilapia_wq.csv"
# TIME_COL     = "timestamp"
# TARGETS      = ["Temperature", "pH", "DO", "Turbidity"]
# HORIZON_H    = 1      # Predict 6 hours ahead

# if not CSV_PATH.exists():
#     raise FileNotFoundError(f"Không tìm thấy file CSV: {CSV_PATH}")

# # ------------------------------------------------------------
# # 2. LOAD & PREPROCESS DATA
# # ------------------------------------------------------------

# df = pd.read_csv(CSV_PATH)
# df = df.drop(columns=["Date", "Hour"], errors="ignore")


# df = df.rename(columns={c: c.strip().replace(" ", "_") for c in df.columns})
# df = df.rename(columns={"DateTime": "timestamp", "date_time": "timestamp", "datetime": "timestamp",
#                         "Dissolved_Oxygen": "DO", "Dissolved-Oxygen": "DO"})

# if TIME_COL not in df.columns:
#     # thử tìm cột tương đương (case-insensitive)
#     matches = [c for c in df.columns if c.lower() == "timestamp" or "date" in c.lower()]
#     if matches:
#         df = df.rename(columns={matches[0]: "timestamp"})
#     else:
#         raise KeyError("Không tìm thấy cột timestamp trong CSV")

# df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
# if df["timestamp"].isna().all():
#     raise ValueError("Không thể chuyển đổi cột timestamp sang datetime")
# df = df.sort_values("timestamp").reset_index(drop=True)

# # ------------------------------------------------------------
# # 🔥 FIX LỖI: CHỈ RESAMPLE CỘT SỐ, KHÔNG RESAMPLE CHUỖI
# # ------------------------------------------------------------
# # df = df.set_index("timestamp")


# # numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
# # if not numeric_cols:
# #     raise ValueError("Không tìm thấy cột số nào để resample trong CSV")

# # df[numeric_cols] = (
# #     df[numeric_cols]
# #     .resample("H")
# #     .mean()
# #     .interpolate("linear")
# # )

# # df = df.reset_index()

# # ------------------------------------------------------------
# # 3. FEATURE ENGINEERING
# # ------------------------------------------------------------

# def create_features(data, targets, horizon=6):

#     df_feat = data.copy()

#     # Tạo delta cho TẤT CẢ cột số
#     for col in df_feat.select_dtypes(include=[np.number]).columns:
#         df_feat[f"{col}_delta1h"] = df_feat[col].diff(1)
#         df_feat[f"{col}_delta3h"] = df_feat[col].diff(3)

#     # Feature: lag + rolling + target horizon
#     for col in targets:
#         # mục tiêu dự đoán (t + horizon)
#         df_feat[f"{col}_t+{horizon}h"] = df_feat[col].shift(-horizon)

#         # lag features
#         for lag in [1, 2, 3, 6]:
#             df_feat[f"{col}_lag{lag}h"] = df_feat[col].shift(lag)

#         # rolling stats
#         for w in [6, 12]:
#             df_feat[f"{col}_roll{w}_mean"] = df_feat[col].rolling(w).mean()
#             df_feat[f"{col}_roll{w}_std"]  = df_feat[col].rolling(w).std()

#     # Time-based features
#     df_feat["hour"] = df_feat["timestamp"].dt.hour
#     df_feat["dow"]  = df_feat["timestamp"].dt.dayofweek

#     df_feat["hour_sin"] = np.sin(2 * np.pi * df_feat["hour"] / 24)
#     df_feat["hour_cos"] = np.cos(2 * np.pi * df_feat["hour"] / 24)
#     df_feat["dow_sin"]  = np.sin(2 * np.pi * df_feat["dow"] / 7)
#     df_feat["dow_cos"]  = np.cos(2 * np.pi * df_feat["dow"] / 7)

#     return df_feat.dropna().reset_index(drop=True)

# df_feat = create_features(df, TARGETS, HORIZON_H)

# # ------------------------------------------------------------
# # 4. TRAIN / TEST SPLIT (80/20)
# # ------------------------------------------------------------

# split_idx = int(len(df_feat) * 0.8)
# df_train = df_feat.iloc[:split_idx]
# df_test  = df_feat.iloc[split_idx:]

# df_test.to_csv("test_data_for_simulation.csv", index=False)
# print(f"\nSaved test_data_for_simulation.csv ({len(df_test)} rows) for realtime demo.\n")

# # ------------------------------------------------------------
# # 5. BUILD DATA FOR TRAINING
# # ------------------------------------------------------------

# feature_cols = [
#     c for c in df_feat.columns
#     if c not in ["timestamp"] + TARGETS + [f"{t}_t+{HORIZON_H}h" for t in TARGETS]
# ]

# X = df_feat[feature_cols].values

# scaler_X = MinMaxScaler()
# X_scaled = scaler_X.fit_transform(X)

# scalers_Y = {t: MinMaxScaler() for t in TARGETS}
# Y_scaled = {}

# for t in TARGETS:
#     y = df_feat[f"{t}_t+{HORIZON_H}h"].values.reshape(-1, 1)
#     Y_scaled[t] = scalers_Y[t].fit_transform(y).ravel()

# # ------------------------------------------------------------
# # 6. TRAINING WITH TimeSeriesSplit
# # ------------------------------------------------------------

# tscv = TimeSeriesSplit(n_splits=5)
# models = {}
# metrics = {t: {"r2": [], "mae": [], "rmse": []} for t in TARGETS}

# for target in TARGETS:
#     print(f"\nTraining model for {target}...")

#     model = LGBMRegressor(
#         n_estimators=500,
#         learning_rate=0.05,
#         max_depth=-1
#     )

#     for train_idx, test_idx in tscv.split(X_scaled):

#         model.fit(X_scaled[train_idx], Y_scaled[target][train_idx])

#         pred_scaled = model.predict(X_scaled[test_idx])
#         pred = scalers_Y[target].inverse_transform(pred_scaled.reshape(-1, 1)).ravel()
#         true = scalers_Y[target].inverse_transform(Y_scaled[target][test_idx].reshape(-1, 1)).ravel()

#         metrics[target]["r2"].append(r2_score(true, pred))
#         metrics[target]["mae"].append(mean_absolute_error(true, pred))
#         mse = mean_squared_error(true, pred)
#         rmse = np.sqrt(mse)
#         metrics[target]["rmse"].append(rmse)

#     model.fit(X_scaled, Y_scaled[target])
#     models[target] = model

# # ------------------------------------------------------------
# # 7. MODEL PERFORMANCE
# # ------------------------------------------------------------

# print("\n================ MODEL PERFORMANCE ================")
# for t in TARGETS:
#     print(
#         f"{t:12s} | "
#         f"R² = {np.mean(metrics[t]['r2']):.3f} | "
#         f"MAE = {np.mean(metrics[t]['mae']):.3f} | "
#         f"RMSE = {np.mean(metrics[t]['rmse']):.3f}"
#     )

# # ------------------------------------------------------------
# # 8. SAVE TRAINED MODELS & METADATA
# # ------------------------------------------------------------

# print("\nSaving models...")

# for t in TARGETS:
#     joblib.dump(models[t], f"xgb_{t}_t+6h.pkl")

# joblib.dump(scaler_X, "scaler_X.pkl")
# joblib.dump(feature_cols, "feature_columns.pkl")

# for t in TARGETS:
#     joblib.dump(scalers_Y[t], f"scaler_Y_{t}.pkl")

# print("Models saved successfully.")

# # ------------------------------------------------------------
# # 9. VISUALIZATION
# # ------------------------------------------------------------

# sns.set_style("whitegrid")

# _, last_test = list(tscv.split(X_scaled))[-1]
# X_test = X_scaled[last_test]
# time_test = df_feat.iloc[last_test]["timestamp"]

# y_true = {
#     t: scalers_Y[t].inverse_transform(Y_scaled[t][last_test].reshape(-1, 1)).ravel()
#     for t in TARGETS
# }

# y_pred = {
#     t: scalers_Y[t].inverse_transform(models[t].predict(X_test).reshape(-1, 1)).ravel()
#     for t in TARGETS
# }

# def classify_risk(temp, ph, do, turb):
#     if do < 2 or ph < 6 or ph > 9 or temp < 24 or temp > 35 or turb > 100:
#         return "Danger"
#     if 28 <= temp <= 32 and 6.5 <= ph <= 8.5 and do >= 6 and turb <= 20:
#         return "Safe"
#     return "Warning"

# true_labels = [
#     classify_risk(y_true["Temperature"][i], y_true["pH"][i], y_true["DO"][i], y_true["Turbidity"][i])
#     for i in range(len(last_test))
# ]

# pred_labels = [
#     classify_risk(y_pred["Temperature"][i], y_pred["pH"][i], y_pred["DO"][i], y_pred["Turbidity"][i])
#     for i in range(len(last_test))
# ]

# plt.figure(figsize=(7, 6))
# cm = pd.crosstab(true_labels, pred_labels, rownames=["Actual"], colnames=["Predicted"])
# sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
# plt.title("Confusion Matrix – 6-hour Risk Classification")
# plt.tight_layout()
# plt.savefig("Confusion_Matrix.png", dpi=300)
# plt.close()

# plt.figure(figsize=(12, 5))
# colors = {"Safe": "#27ae60", "Warning": "#f39c12", "Danger": "#c0392b"}
# plt.scatter(time_test, [1]*len(time_test), c=[colors[l] for l in true_labels], s=40)
# plt.title("Risk Timeline – Last 30 Days")
# plt.yticks([])
# plt.tight_layout()
# plt.savefig("Risk_Timeline.png", dpi=300)
# plt.close()

# print("Training complete!")


# trainIoT.py

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, accuracy_score, f1_score
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch
import warnings
warnings.filterwarnings('ignore')

# ========= CẤU HÌNH – KHÔNG ĐỔI TÊN GÌ CẢ =========
EXCEL_FILE = "Monteria_Aquaculture_Data.xlsx"
HOURLY_SHEET = "Hourly Data"
DAILY_SHEET = "Daily Averages"

# Tên cột nguyên bản trong file
TIME_COL_ORIG = "DateTime"
TEMP_COL = "Temperature"
PH_COL = "pH"
DO_COL = "Dissolved_Oxygen"
TURB_COL = "Turbidity"

TARGETS_ORIG = [TEMP_COL, PH_COL, DO_COL, TURB_COL]
HORIZON_H = 6

# ========= 1) ĐỌC DỮ LIỆU HOURLY (DÙNG ĐỂ TRAIN) =========
print("Đang tải dữ liệu hourly (dùng để huấn luyện)...")
df_hourly = pd.read_excel(EXCEL_FILE, sheet_name=HOURLY_SHEET)

# Chỉ lấy các cột cần thiết + bỏ dòng thiếu
df_hourly = df_hourly[[TIME_COL_ORIG, TEMP_COL, PH_COL, DO_COL, TURB_COL]].dropna()
df_hourly[TIME_COL_ORIG] = pd.to_datetime(df_hourly[TIME_COL_ORIG])
df_hourly = df_hourly.sort_values(TIME_COL_ORIG).reset_index(drop=True)

print(f"→ Đã tải {len(df_hourly):,} dòng hourly từ {df_hourly[TIME_COL_ORIG].min().date()} đến {df_hourly[TIME_COL_ORIG].max().date()}")

# ========= 2) FEATURE ENGINEERING (DÙNG NGUYÊN TÊN CỘT) =========
def create_features(df, time_col, targets, horizon=6):
    data = df.copy()
    step = horizon
    
    for col in targets:
        data[f"{col}_future"] = data[col].shift(-step)
        for lag in [1, 3, 6, 12, 24]:
            data[f"{col}_lag{lag}h"] = data[col].shift(lag)
        for win in [6, 12, 24]:
            data[f"{col}_mean{win}h"] = data[col].rolling(win).mean()
            data[f"{col}_std{win}h"]  = data[col].rolling(win).std()
    
    data["hour"] = data[time_col].dt.hour
    data["dow"]  = data[time_col].dt.dayofweek
    data["hour_sin"] = np.sin(2 * np.pi * data["hour"] / 24)
    data["hour_cos"] = np.cos(2 * np.pi * data["hour"] / 24)
    
    return data.dropna().reset_index(drop=True)

df_feat = create_features(df_hourly, TIME_COL_ORIG, TARGETS_ORIG, HORIZON_H)

# ========= 3) CHUẨN BỊ DỮ LIỆU =========
feature_cols = [c for c in df_feat.columns if c not in [TIME_COL_ORIG] + TARGETS_ORIG + [f"{c}_future" for c in TARGETS_ORIG]]
X = df_feat[feature_cols].values

scaler_X = MinMaxScaler()
X_scaled = scaler_X.fit_transform(X)

scalers_Y = {col: MinMaxScaler() for col in TARGETS_ORIG}
Y_scaled = {}
for col in TARGETS_ORIG:
    y = df_feat[f"{col}_future"].values.reshape(-1, 1)
    Y_scaled[col] = scalers_Y[col].fit_transform(y).ravel()

# ========= 4) HUẤN LUYỆN =========
tscv = TimeSeriesSplit(n_splits=5)
models = {}

print("\nBắt đầu huấn luyện 4 mô hình (Temperature, pH, DO, Turbidity)...")
for col in TARGETS_ORIG:
    print(f"   → Đang train {col}...")
    model = XGBRegressor(
        n_estimators=1000,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=2.0,
        random_state=42,
        tree_method="hist",
        n_jobs=-1
    )
    y = Y_scaled[col]
    for tr, te in tscv.split(X_scaled):
        model.fit(X_scaled[tr], y[tr])
    model.fit(X_scaled, y)  # Final fit
    models[col] = model

# ========= 5) ĐÁNH GIÁ TRÊN FOLD CUỐI =========
_, last_te = list(tscv.split(X_scaled))[-1]
X_test = X_scaled[last_te]
time_test = df_feat[TIME_COL_ORIG].iloc[last_te].values

y_true = {col: scalers_Y[col].inverse_transform(Y_scaled[col][last_te].reshape(-1,1)).ravel() for col in TARGETS_ORIG}
y_pred = {col: scalers_Y[col].inverse_transform(models[col].predict(X_test).reshape(-1,1)).ravel() for col in TARGETS_ORIG}

# In kết quả regression
print("\n=== KẾT QUẢ DỰ BÁO 6 GIỜ TỚI ===")
for col in TARGETS_ORIG:
    r2 = r2_score(y_true[col], y_pred[col])
    mae = mean_absolute_error(y_true[col], y_pred[col])
    print(f"{col:20} → R² = {r2:.4f} | MAE = {mae:.3f}")

# ========= 6) PHÂN LOẠI RỦI RO (theo tiêu chuẩn nuôi cá rô phi) =========
def get_risk(temp, ph, do, turb=None):
    if do < 2.0 or temp < 24 or temp > 35 or ph < 6.0 or ph > 9.0:
        return "Danger"
    elif 28 <= temp <= 32 and 6.5 <= ph <= 8.5 and do >= 6.0:
        return "Safe"
    else:
        return "Warning"

true_risk = [get_risk(y_true[TEMP_COL][i], y_true[PH_COL][i], y_true[DO_COL][i]) for i in range(len(last_te))]
pred_risk = [get_risk(y_pred[TEMP_COL][i], y_pred[PH_COL][i], y_pred[DO_COL][i]) for i in range(len(last_te))]

acc = accuracy_score(true_risk, pred_risk)
f1 = f1_score(true_risk, pred_risk, average='macro')
print(f"\nPHÂN LOẠI RỦI RO (6h tới): Accuracy = {acc:.4f} ({acc*100:.1f}%) | Macro-F1 = {f1:.4f}")

# ========= 7) LƯU TẤT CẢ ĐỂ TRIỂN KHAI IoT =========
joblib.dump(scaler_X, "scaler_features.pkl")
for col in TARGETS_ORIG:
    joblib.dump(models[col], f"model_{col.replace(' ', '_')}_6h.pkl")
    joblib.dump(scalers_Y[col], f"scaler_{col.replace(' ', '_')}.pkl")
joblib.dump(feature_cols, "feature_columns.pkl")
joblib.dump({
    "time_col": TIME_COL_ORIG,
    "targets": TARGETS_ORIG,
    "horizon": HORIZON_H
}, "model_config.pkl")

print("\nHOÀN TẤT 100%!")
print("Đã xuất:")
print("   • 4 file model (*.pkl)")
print("   • 5 file scaler")
print("   • feature_columns.pkl + model_config.pkl")
print("   → Sẵn sàng tích hợp vào ESP32, Raspberry Pi, hoặc Flask API")

# ========= TÙY CHỌN: XUẤT 3 BIỂU ĐỒ (nếu muốn) =========
# Bỏ comment nếu cần

plt.figure(figsize=(12,5))
plt.subplot(1,2,1)
cm = pd.crosstab(true_risk, pred_risk, rownames=['Thực tế'], colnames=['Dự báo'])
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title('Confusion Matrix - Risk Classification')

plt.subplot(1,2,2)
plt.plot(time_test[-168:], y_true[TEMP_COL][-168:], label="Thực tế Nhiệt độ", alpha=0.8)
plt.plot(time_test[-168:], y_pred[TEMP_COL][-168:], '--', label="Dự báo Nhiệt độ")
plt.legend(); plt.title("7 ngày cuối - Nhiệt độ")
plt.tight_layout()
plt.savefig("results_demo.png", dpi=300, bbox_inches='tight')
# plt.show()
