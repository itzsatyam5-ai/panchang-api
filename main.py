from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
from calculator import calculate_panchang

app = FastAPI(title="Panchang API Engine", version="1.1")

# API Documentation के लिए Response Model
class PanchangResponse(BaseModel):
    success: bool
    date: Optional[str] = None
    location: Optional[dict] = None
    panchang_details: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None

@app.get("/", response_model=dict)
def read_root():
    return {
        "success": True,
        "data": {
            "message": "Panchang API Engine is running smoothly!"
        }
    }

@app.get("/get-panchang", response_model=PanchangResponse)
def get_panchang(
    date: str = Query(..., description="Date in YYYY-MM-DD format (e.g. 2026-06-05)"),
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
    tz: float = Query(5.5, description="Timezone offset from UTC (default is 5.5 for IST)")
):
    """
    यह एंडपॉइंट यूजर से तारीख (date), अक्षांश (lat), देशांतर (lon) और टाइमज़ोन लेकर पंचांग डेटा देगा।
    इस्तेमाल का तरीका: /get-panchang?date=2026-06-05&lat=28.6139&lon=77.2090&tz=5.5
    """
    result = calculate_panchang(date, lat, lon, tz)
    return result
