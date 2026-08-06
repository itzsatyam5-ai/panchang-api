from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
from calculator import PanchangCalculatorService

app = FastAPI(title="MithilaWorld Panchang API", version="1.0.1")

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
    lat: float = Query(26.1542, description="Latitude (Default: Darbhanga)"),
    lon: float = Query(85.8918, description="Longitude (Default: Darbhanga)"),
    date_str: str = Query(None, alias="date", description="Date in YYYY-MM-DD or DD-MM-YYYY format")
):
    target_date = date.today()
    
    # Flexible Date Parsing (Handles both YYYY-MM-DD and DD-MM-YYYY)
    if date_str:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                target_date = datetime.strptime(date_str.strip(), fmt).date()
                break
            except ValueError:
                continue

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
            "sunrise": sun_data["sunrise"].strftime("%I:%M %p") if isinstance(sun_data["sunrise"], datetime) else str(sun_data["sunrise"]),
            "sunset": sun_data["sunset"].strftime("%I:%M %p") if isinstance(sun_data["sunset"], datetime) else str(sun_data["sunset"]),
            "moonrise": moon_data.get("moonrise", "N/A"),
            "moonset": moon_data.get("moonset", "N/A")
        },
        "muhurat_and_kaal": special_kaals,
        "choghadiya": choghadiya_data
    }
