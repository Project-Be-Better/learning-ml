import requests
import json
import random
from datetime import datetime, timedelta

def test_api():
    url = "http://localhost:8000/score-trip"
    
    # Generate 10 points of sample telemetry
    telemetry = []
    for i in range(10):
        telemetry.append({
            "timestamp": (datetime.now() + timedelta(seconds=i*30)).isoformat(),
            "speed_kmh": 40 + random.uniform(-5, 5),
            "acceleration_ms2": random.uniform(-0.3, 0.3),
            "lat": 1.35,
            "lon": 103.8
        })
        
    payload = {
        "driver_id": 1,
        "truck_id": 42,
        "telemetry": telemetry
    }
    
    print("🚀 Sending trip to API...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("✅ Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

    # Test driver stats
    print("\n📊 Checking Driver Stats...")
    stats_response = requests.get("http://localhost:8000/driver/1")
    print(json.dumps(stats_response.json(), indent=2))

if __name__ == "__main__":
    test_api()
