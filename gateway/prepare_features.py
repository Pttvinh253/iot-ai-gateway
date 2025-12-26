import pandas as pd
import numpy as np
import joblib
from datetime import datetime

# Load danh sách feature và scaler_X
MODEL_DIR = "../models/"
feature_cols = joblib.load(MODEL_DIR + "feature_columns.pkl")
scaler_X = joblib.load(MODEL_DIR + "scaler_features.pkl")

TARGET_COLS = ["Temperature", "pH", "Dissolved_Oxygen", "Turbidity"]

def build_feature_row(history_df, new_data):
    """
    new_data = {
        "Temperature": float,
        "pH": float,
        "Dissolved_Oxygen": float,
        "Turbidity": float,
        "timestamp": "YYYY-MM-DD HH:MM:SS"
    }
    """

    df = history_df.copy()
    df.loc[len(df)] = new_data

    # LAG features
    for col in TARGET_COLS:
        for lag in [1, 3, 6, 12, 24]:
            df[f"{col}_lag{lag}h"] = df[col].shift(lag)

        # Rolling window
        for win in [6, 12, 24]:
            df[f"{col}_mean{win}h"] = df[col].rolling(win).mean()
            df[f"{col}_std{win}h"] = df[col].rolling(win).std()

    ts = pd.to_datetime(new_data["timestamp"])
    df.loc[len(df)-1, "hour"] = ts.hour
    df.loc[len(df)-1, "dow"] = ts.dayofweek
    df.loc[len(df)-1, "hour_sin"] = np.sin(2*np.pi*ts.hour/24)
    df.loc[len(df)-1, "hour_cos"] = np.cos(2*np.pi*ts.hour/24)

    # Lấy dòng cuối có đầy đủ feature
    df_feat = df.tail(1).dropna()

    if df_feat.empty:
        return None, df   # cần thêm lịch sử

    X = df_feat[feature_cols]
    X_scaled = scaler_X.transform(X)

    return X_scaled, df
