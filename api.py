import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:
    from tensorflow.keras.models import load_model
    from xgboost import XGBRegressor
except ImportError:
    pass

app = FastAPI(title="Pollution Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# Load models
lstm_model = None
xgb_model = None
meta_learner = None
scaler_x = None
scaler_y = None

try:
    lstm_model = load_model(os.path.join(MODEL_DIR, 'air_lstm.h5'))
    xgb_model = XGBRegressor()
    xgb_model.load_model(os.path.join(MODEL_DIR, 'air_xgb.json'))
    meta_learner = joblib.load(os.path.join(MODEL_DIR, 'meta_learner.pkl'))
    scaler_x = joblib.load(os.path.join(MODEL_DIR, 'scaler_x.pkl'))
    scaler_y = joblib.load(os.path.join(MODEL_DIR, 'scaler_y.pkl'))
    print("Ensemble models loaded successfully.")
except Exception as e:
    print(f"Warning: Could not load all ensemble models. Error: {e}")

class PredictionInput(BaseModel):
    pm25: float
    pm10: float
    no2: float
    co: float
    temperature: float
    humidity: float
    vehicle_count: int
    speed: float

def get_risk_level(aqi):
    if aqi <= 50: return "Good"
    elif aqi <= 100: return "Moderate"
    elif aqi <= 150: return "Unhealthy for Sensitive Groups"
    elif aqi <= 200: return "Unhealthy"
    elif aqi <= 300: return "Very Unhealthy"
    else: return "Hazardous"

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ML Service is running."}

@app.get("/debug")
def debug_models():
    return {
        "lstm": str(type(lstm_model)),
        "xgb": str(type(xgb_model)),
        "meta": str(type(meta_learner)),
        "sx": str(type(scaler_x)),
        "sy": str(type(scaler_y)),
        "all_true": bool(all([lstm_model, xgb_model, meta_learner, scaler_x, scaler_y]))
    }

@app.post("/predict")
def predict(data: PredictionInput):
    # Fix the boolean evaluation for custom objects
    if lstm_model is None or xgb_model is None or meta_learner is None or scaler_x is None or scaler_y is None:
        # Heuristic fallback calculation if models are not loaded
        predicted_pm25 = data.pm25 * 0.95
        sub_pm25 = (predicted_pm25 * 2.5) if predicted_pm25 < 60 else (150 + (predicted_pm25 - 60) * 1.5)
        sub_pm10 = (data.pm10 * 0.8)
        sub_co = (data.co * 15.0)
        
        base_aqi = max(sub_pm25, sub_pm10, sub_co)
        
        traffic_factor = (data.vehicle_count / 1000.0) ** 1.5
        wind_factor = 1.0 / (data.speed + 0.1)
        
        aqi_1hr = round(base_aqi + (traffic_factor * wind_factor * 30.0), 2)
        aqi_24hr = round(aqi_1hr * 1.15, 2)
        
        risk_level = get_risk_level(aqi_1hr)

        return {
            "aqi_1hr": aqi_1hr,
            "aqi_24hr": aqi_24hr,
            "risk_level": risk_level,
            "fallback": True
        }

    try:
        current_hour = datetime.datetime.now().hour
        pm2_5_log = np.log1p(data.pm25)
        wind_speed = data.speed
        pm_ratio = data.pm25 / (data.pm10 + 1)
        stagnation = data.co * (1 / (wind_speed + 0.1))
        hour_sin = np.sin(2 * np.pi * current_hour / 24)
        hour_cos = np.cos(2 * np.pi * current_hour / 24)
        
        feature_row = [
            pm2_5_log, data.pm10, data.co, wind_speed, hour_sin, hour_cos, 
            pm2_5_log, pm2_5_log, pm_ratio, stagnation, pm2_5_log
        ]
        
        seq_data = np.array([feature_row for _ in range(6)])
        seq_scaled = scaler_x.transform(seq_data)
        
        X_lstm = seq_scaled.reshape(1, 6, 11)
        X_xgb = seq_scaled.reshape(1, -1)
        
        pred_lstm = lstm_model.predict(X_lstm, verbose=0)
        pred_xgb = xgb_model.predict(X_xgb).reshape(-1, 1)
        
        meta_X = np.hstack([pred_lstm, pred_xgb])
        pred_scaled = meta_learner.predict(meta_X)
        
        final_pred_log = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0][0]
        predicted_pm25 = float(np.expm1(final_pred_log))
        
        # Non-linear AQI calculation based on multiple pollutants and traffic
        sub_pm25 = (predicted_pm25 * 2.5) if predicted_pm25 < 60 else (150 + (predicted_pm25 - 60) * 1.5)
        sub_pm10 = (data.pm10 * 0.8)
        sub_co = (data.co * 15.0)
        
        base_aqi = max(sub_pm25, sub_pm10, sub_co)
        
        traffic_factor = (data.vehicle_count / 1000.0) ** 1.5
        wind_factor = 1.0 / (wind_speed + 1.0)
        
        aqi_1hr = round(base_aqi + (traffic_factor * wind_factor * 30.0), 2)
        aqi_24hr = round(aqi_1hr * 1.15, 2)
        
        risk_level = get_risk_level(aqi_1hr)

        return {
            "aqi_1hr": aqi_1hr,
            "aqi_24hr": aqi_24hr,
            "risk_level": risk_level
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
