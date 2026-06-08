import pandas as pd
import requests
import time

csv_file = r"C:\Users\suhas\Desktop\CHIRARANGA FAREWELL\master_pollution_MICE_imputed"
url = "http://127.0.0.1:5001/api/pollution/add"

print("Reading CSV...")
df = pd.read_csv(csv_file)

# Get unique stations
latest_data = df.drop_duplicates(subset=['station_id'], keep='last')

print(f"Found {len(latest_data)} unique locations. Pushing to backend...")

for index, row in latest_data.iterrows():
    # Construct payload for backend
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
            print(f"Added {payload['zone']}")
        else:
            print(f"Failed to add {payload['zone']}: {response.text}")
    except Exception as e:
        print(f"Error for {payload['zone']}: {e}")
    time.sleep(0.1) # Small delay to ensure order and avoid overwhelming backend

print("Done seeding from dataset.")
