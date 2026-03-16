from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
import json
from scoring import ScoringService

app = FastAPI(title="ExploreSG ML Scoring Service")
service = ScoringService()
DB_NAME = "telemetry.db"

class TelemetryPoint(BaseModel):
    timestamp: str
    speed_kmh: float
    acceleration_ms2: float
    lat: float
    lon: float

class TripTelemetryRequest(BaseModel):
    driver_id: int
    truck_id: int
    telemetry: List[TelemetryPoint]

@app.get("/")
def read_root():
    return {"status": "online", "service": "ML Scoring Engine"}

@app.post("/score-trip")
def score_trip_endpoint(request: TripTelemetryRequest):
    """
    Receives raw telemetry, stores it, scores it, and returns the result.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 1. Create Trip Entry
        telemetry_list = [p.dict() for p in request.telemetry]
        start_t = telemetry_list[0]["timestamp"]
        end_t = telemetry_list[-1]["timestamp"]
        dist = (len(telemetry_list) * 30 * 50) / 3600
        
        cursor.execute("""
            INSERT INTO trips (driver_id, start_time, end_time, distance_km)
            VALUES (?, ?, ?, ?)
        """, (request.driver_id, start_t, end_t, dist))
        trip_id = cursor.lastrowid
        
        # 2. Store Raw Telemetry (Row-oriented)
        cursor.executemany("""
            INSERT INTO telemetry_points (trip_id, timestamp, speed_kmh, acceleration_ms2, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (trip_id, p.timestamp, p.speed_kmh, p.acceleration_ms2, p.lat, p.lon)
            for p in request.telemetry
        ])
        
        conn.commit()
        conn.close()

        # 3. Score the trip
        scores = service.score_trip(trip_id)
        
        if not scores:
            raise HTTPException(status_code=500, detail="Scoring failed")
            
        return {
            "trip_id": trip_id,
            "scores": scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/driver/{driver_id}")
def get_driver_scores(driver_id: int):
    """Retrieves current scores and history for a driver."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, smoothness_avg, safety_avg, overall_avg, trip_count, fairness_metadata_json 
        FROM drivers WHERE driver_id = ?
    """, (driver_id,))
    driver = cursor.fetchone()
    conn.close()
    
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
        
    return {
        "name": driver[0],
        "smoothness_avg": round(driver[1], 2),
        "safety_avg": round(driver[2], 2),
        "overall_avg": round(driver[3], 2),
        "trip_count": driver[4],
        "fairness_metadata": json.loads(driver[5]) if driver[5] else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
