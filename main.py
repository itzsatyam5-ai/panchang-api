from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime
from calculator import calculate_full_panchang  # Fixed path

app = FastAPI(
    title="MithilaWorld Panchang API Engine",
    version="1.0.0",
    description="Production Ready Vedic Panchang Engine using PySwissEph"
)

# Enable CORS for WordPress Requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Local District Coordinates Database
DISTRICTS_FILE = os.path.join(os.path.dirname(__file__), "data", "districts.json")
districts_db = []
if os.path.exists(DISTRICTS_FILE):
    with open(DISTRICTS_FILE, "r", encoding="utf-8") as f:
        districts_db = json.load(f)

# Master Prompt Standard Response Format
def standard_response(success: bool, data: dict = None, message: str = "", error_code: int = None):
    if success:
        return {"success": True, "data": data}
    return JSONResponse(
        status_code=error_code or 400,
        content={"success": False, "message": message, "error_code": error_code or 400}
    )

@app.get("/")
def root():
    return standard_response(True, {"message": "MithilaWorld Panchang API Engine Active"})

@app.get("/api/v1/districts")
def get_districts():
    """Returns list of pre-configured Indian districts"""
    return standard_response(True, districts_db)

@app.get("/api/v1/panchang")
def get_panchang(
    date: str = Query(..., description="Date format DD-MM-YYYY or YYYY-MM-DD"),
    lat: float = Query(26.1542, description="Latitude"),
    lon: float = Query(85.8918, description="Longitude")
):
    try:
        if "-" in date:
            parts = date.split("-")
            if len(parts[0]) == 4:
                formatted_date = date
            else:
                formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
        else:
            return standard_response(False, message="Invalid date format", error_code=400)

        result = calculate_full_panchang(formatted_date, lat, lon)
        return standard_response(True, result)

    except Exception as e:
        return standard_response(False, message=str(e), error_code=500)

@app.get("/api/v1/today")
def get_today_panchang(
    lat: float = Query(26.1542),
    lon: float = Query(85.8918)
):
    today_str = datetime.now().strftime("%Y-%m-%d")
    result = calculate_full_panchang(today_str, lat, lon)
    return standard_response(True, result)

@app.get("/api/v1/rahukal")
def get_rahukal(
    date: str = Query(...),
    lat: float = Query(26.1542),
    lon: float = Query(85.8918)
):
    try:
        if "-" in date:
            parts = date.split("-")
            if len(parts[0]) == 4:
                formatted_date = date
            else:
                formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
        else:
            return standard_response(False, message="Invalid date format", error_code=400)

        panchang = calculate_full_panchang(formatted_date, lat, lon)
        return standard_response(True, {
            "date": formatted_date,
            "rahu_kaal": panchang["muhurat_and_kaal"]["rahu_kaal"]
        })
    except Exception as e:
        return standard_response(False, message=str(e), error_code=500)
