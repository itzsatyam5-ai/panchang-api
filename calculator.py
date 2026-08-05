from datetime import datetime
import math
import swisseph as swe
from mappings import TITHIS, NAKSHATRAS, YOGAS, KARANAS

# Performance Optimization for Swiss Ephemeris
swe.set_ephe_path('')
swe.set_sid_mode(swe.SIDM_LAHIRI)

def get_first_float(res):
    """Safely extracts the first float value."""
    if isinstance(res, float):
        return res
    if isinstance(res, (tuple, list)):
        for item in res:
            val = get_first_float(item)
            if val is not None:
                return val
    return None

def calc_sunrise_sunset(year, month, day, lat, lon, tz_offset):
    """
    100% Native Python Sunrise/Sunset Calculator.
    Bypasses the pyswisseph C-extension bug.
    """
    dt = datetime(year, month, day)
    N = dt.timetuple().tm_yday
    lngHour = lon / 15.0
    
    t_rise = N + ((6 - lngHour) / 24)
    t_set = N + ((18 - lngHour) / 24)
    
    M_rise = (0.9856 * t_rise) - 3.289
    M_set = (0.9856 * t_set) - 3.289
    
    L_rise = (M_rise + (1.916 * math.sin(math.radians(M_rise))) + (0.020 * math.sin(math.radians(2 * M_rise))) + 282.634) % 360
    L_set = (M_set + (1.916 * math.sin(math.radians(M_set))) + (0.020 * math.sin(math.radians(2 * M_set))) + 282.634) % 360
    
    RA_rise = math.degrees(math.atan(0.91764 * math.tan(math.radians(L_rise)))) % 360
    RA_set = math.degrees(math.atan(0.91764 * math.tan(math.radians(L_set)))) % 360
    
    RA_rise = (RA_rise + (math.floor(L_rise/90) * 90) - (math.floor(RA_rise/90) * 90)) / 15.0
    RA_set = (RA_set + (math.floor(L_set/90) * 90) - (math.floor(RA_set/90) * 90)) / 15.0
    
    sinDec_rise = 0.39782 * math.sin(math.radians(L_rise))
    cosDec_rise = math.cos(math.asin(sinDec_rise))
    sinDec_set = 0.39782 * math.sin(math.radians(L_set))
    cosDec_set = math.cos(math.asin(sinDec_set))
    
    zenith = 90.8333
    cosH_rise = (math.cos(math.radians(zenith)) - (sinDec_rise * math.sin(math.radians(lat)))) / (cosDec_rise * math.cos(math.radians(lat)))
    cosH_set = (math.cos(math.radians(zenith)) - (sinDec_set * math.sin(math.radians(lat)))) / (cosDec_set * math.cos(math.radians(lat)))
    
    H_rise = (360 - math.degrees(math.acos(cosH_rise))) / 15.0
    H_set = (math.degrees(math.acos(cosH_set))) / 15.0
    
    T_rise = H_rise + RA_rise - (0.06571 * t_rise) - 6.622
    T_set = H_set + RA_set - (0.06571 * t_set) - 6.622
    
    UT_rise = (T_rise - lngHour) % 24
    UT_set = (T_set - lngHour) % 24
    
    localT_rise = (UT_rise + tz_offset) % 24
    localT_set = (UT_set + tz_offset) % 24
    
    return localT_rise, localT_set

def calculate_panchang(date_str: str, latitude: float, longitude: float, tz_offset: float = 5.5):
    try:
        # Input Validation
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        
        # Sun and Moon position calculations
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        
        sun_long = get_first_float(sun_pos)
        moon_long = get_first_float(moon_pos)
        
        # पंचांग अंक गणना
        diff = (moon_long - sun_long) % 360
        tithi_no = int(diff / 12) + 1
        nakshatra_no = int(moon_long / (360.0 / 27.0)) + 1
        yoga_sum = (sun_long + moon_long) % 360
        yoga_no = int(yoga_sum / (360.0 / 27.0)) + 1
        
        karana_no = int(diff / 6.0) + 1
        if karana_no > 11:
            karana_no = ((karana_no - 1) % 7) + 1

        try:
            # BUG FIX: Use Pure Python Math for Sunrise 
            rise_hour, set_hour = calc_sunrise_sunset(
                target_date.year, target_date.month, target_date.day, 
                latitude, longitude, tz_offset
            )
            
            def format_time(hours):
                h = int(hours)
                m = int(round((hours - h) * 60))
                if m == 60:
                    h += 1
                    m = 0
                return f"{h % 24:02d}:{m:02d}"
                
            sunrise_str = format_time(rise_hour)
            sunset_str = format_time(set_hour)
            
            # राहुकाल गणना
            day_duration = set_hour - rise_hour
            if day_duration < 0:
                day_duration += 24
                
            sect_duration = day_duration / 8.0
            weekday = target_date.weekday()
            rahu_octets = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
            octet_no = rahu_octets.get(weekday, 2)
            
            rahu_start_hr = rise_hour + (sect_duration * (octet_no - 1))
            rahu_end_hr = rise_hour + (sect_duration * octet_no)
            
            rahukalam_str = f"{format_time(rahu_start_hr)} to {format_time(rahu_end_hr)}"
            
        except Exception as calc_err:
            raise ValueError(f"Sunrise Calc Error: {str(calc_err)}")

        return {
            "success": True,
            "date": date_str,
            "location": {"latitude": latitude, "longitude": longitude, "timezone": tz_offset},
            "panchang_details": {
                "sunrise": sunrise_str,
                "sunset": sunset_str,
                "tithi": TITHIS.get(tithi_no, "Unknown"),
                "nakshatra": NAKSHATRAS.get(nakshatra_no, "Unknown"),
                "yoga": YOGAS.get(yoga_no, "Unknown"),
                "karana": KARANAS.get(karana_no, "Unknown"),
                "rahukalam": rahukalam_str
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
