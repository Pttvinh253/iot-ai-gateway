import numpy as np
import pandas as pd

def risk_label(temp, ph, do_pred):
    if do_pred < 2.0:
        return "Danger"
    if ph < 6.0 or ph > 9.0:
        return "Warning"
    if temp < 24 or temp > 35:
        return "Warning"
    return "Safe"

def prepare_input(data_dict):
    ts = pd.to_datetime(data_dict["timestamp"])
    X = pd.DataFrame([{
        "temperature": data_dict["temperature"],
        "pH": data_dict["ph"],
        "turbidity": data_dict["turbidity"],
        "hour": ts.hour,
        "dayofweek": ts.dayofweek,
        "hour_sin": np.sin(2*np.pi*ts.hour/24),
        "hour_cos": np.cos(2*np.pi*ts.hour/24)
    }])
    return X
