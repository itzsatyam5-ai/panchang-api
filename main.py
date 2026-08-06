from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
from calculator import PanchangCalculatorService

app = FastAPI(title="MithilaWorld Panchang API", version="1.0.0")

# Enable CORS for WordPress access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "active", "message": "MithilaWorld Panchang API is running"}

@app.get("/api/v1/panchang")
def get_panchang(
    lat: float = Query(26.1522, description="Latitude"),
    lon: float = Query(85.8971, description="Longitude"),
    date_str: str = Query(None, alias="date", description="Date in YYYY-MM-DD format")
):
    # Parse date
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    calc = PanchangCalculatorService(lat=lat, lon=lon)
    
    # Astronomical Calculations
    sun_data = calc.get_sun_rise_set(target_date)
    next_sunrise = calc.get_next_sunrise(target_date)
    moon_data = calc.get_moon_rise_set(target_date)
    
    weekday = target_date.weekday()  # 0 = Monday, 6 = Sunday
    special_kaals = calc.calculate_special_kaals(sun_data["sunrise"], sun_data["sunset"], weekday)
    choghadiya_data = calc.calculate_choghadiya(sun_data["sunrise"], sun_data["sunset"], next_sunrise, weekday)

    return {
        "status": "success",
        "date": target_date.strftime("%d-%m-%Y"),
        "location": {
            "latitude": lat,
            "longitude": lon
        },
        "sun_moon": {
            "sunrise": sun_data["sunrise"].strftime("%I:%M %p"),
            "sunset": sun_data["sunset"].strftime("%I:%M %p"),
            "moonrise": moon_data["moonrise"],
            "moonset": moon_data["moonset"]
        },
        "muhurat_and_kaal": special_kaals,
        "choghadiya": choghadiya_data
    }
