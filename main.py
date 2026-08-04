from fastapi import FastAPI
from calculator import calculate_panchang

app = FastAPI(title="Panchang API Engine", version="1.0")

@app.get("/")
def read_root():
    return {
        "success": True,
        "data": {
            "message": "Panchang API Engine is running smoothly!"
        }
    }

@app.get("/get-panchang")
def get_panchang(date: str, lat: float, lon: float):
    """
    यह एंडपॉइंट यूजर से तारीख (date), अक्षांश (lat) और देशांतर (lon) लेकर पंचांग डेटा देगा।
    इस्तेमाल का तरीका: /get-panchang?date=2026-06-05&lat=28.6139&lon=77.2090
    """
    result = calculate_panchang(date, lat, lon)
    return result
