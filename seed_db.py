import os
import sys
import pandas as pd
import requests
import time
import random

# Find CSV path
possible_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imputation', 'master_pollution_MICE_imputed.csv'),
    r"imputation\master_pollution_MICE_imputed.csv",
    r"C:\Users\suhas\Desktop\CHIRARANGA FAREWELL\master_pollution_MICE_imputed.csv",
    r"C:\Users\suhas\Desktop\CHIRARANGA FAREWELL\master_pollution_MICE_imputed",
    r"C:\Users\suhas\Desktop\mini-pro\ml_model-\imputation\master_pollution_MICE_imputed.csv"
]

csv_file = None
for p in possible_paths:
    if os.path.exists(p):
        csv_file = p
        break

if not csv_file:
    print("Error: master_pollution_MICE_imputed.csv not found!")
    sys.exit(1)

# Backend URL (Check port 5000 first, fallback to 5001)
url = "http://127.0.0.1:5000/api/pollution/add"
try:
    # Quick check
    requests.get("http://127.0.0.1:5000/api/pollution/live", timeout=1)
except Exception:
    url = "http://127.0.0.1:5001/api/pollution/add"

print(f"Reading CSV from {csv_file}...")
df = pd.read_csv(csv_file)

# Get unique stations
latest_data = df.drop_duplicates(subset=['station_id'], keep='last')

print(f"Found {len(latest_data)} unique locations. Pushing initial seed to backend...")
for index, row in latest_data.iterrows():
    payload = {
        "zone": str(row['station_id']),
        "pm25": float(row['pm2_5']),
        "pm10": float(row['pm10']),
        "no2": float(row['no2']),
        "co": float(row['co']),
        "temperature": 28.0, 
        "humidity": float(row['rh']) if 'rh' in row else 55.0,
        "vehicle_count": 800,
        "speed": float(row['wind_speed']) if 'wind_speed' in row else 20.0
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            print(f"Seed: Added {payload['zone']}")
        else:
            print(f"Seed: Failed for {payload['zone']}: {response.text}")
    except Exception as e:
        print(f"Seed: Error for {payload['zone']}: {e}")
    time.sleep(0.1)

print("\nStarting live data stream... (Press Ctrl+C to stop)")
try:
    while True:
        # Choose a random row from dataset to simulate live stream
        row = df.sample(1).iloc[0]
        payload = {
            "zone": f"Station {row['station_id']}",
            "pm25": float(row['pm2_5']),
            "pm10": float(row['pm10']),
            "no2": float(row['no2']),
            "co": float(row['co']),
            "temperature": round(random.uniform(22.0, 35.0), 1),
            "humidity": float(row['rh']) if 'rh' in row else round(random.uniform(40.0, 70.0), 1),
            "vehicle_count": random.randint(100, 1500),
            "speed": float(row['wind_speed']) if 'wind_speed' in row else round(random.uniform(5.0, 30.0), 1)
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 201:
                print(f"Stream: Pushed {payload['zone']} - PM2.5: {payload['pm25']}, AQI: {response.json().get('prediction', {}).get('aqi_1hr', 'N/A')}")
            else:
                print(f"Stream: Failed to push {payload['zone']}: {response.text}")
        except Exception as e:
            print(f"Stream: Error: {e}")
        time.sleep(2.0) # wait 2 seconds between updates
except KeyboardInterrupt:
    print("\nLive data stream stopped.")
