from datetime import datetime, timedelta
import swisseph as swe
from mappings import TITHIS, NAKSHATRAS, YOGAS, KARANAS

# Performance Optimization
swe.set_ephe_path('')
swe.set_sid_mode(swe.SIDM_LAHIRI)

def get_first_float(res):
    """Safely extracts the first float value from any deeply nested tuple/list."""
    if isinstance(res, float):
        return res
    if isinstance(res, (tuple, list)):
        for item in res:
            val = get_first_float(item)
            if val is not None:
                return val
    return None

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

        geopos = (longitude, latitude, 0.0)
        jd_start = swe.julday(target_date.year, target_date.month, target_date.day, 0.0)
        
        try:
            # Reverted to your original working arguments
            rise_res = swe.rise_trans(jd_start, swe.SUN, geopos, 0, swe.CALC_RISE)
            set_res = swe.rise_trans(jd_start, swe.SUN, geopos, 0, swe.CALC_SET)
            
            # Smart extraction to avoid 'tuple' object error
            rise_jd = get_first_float(rise_res)
            set_jd = get_first_float(set_res)
            
            if rise_jd is None or set_jd is None:
                raise ValueError("Could not extract Time from rise_trans output.")

            # Convert JD to Hours properly
            rise_frac = (rise_jd + 0.5) % 1.0
            set_frac = (set_jd + 0.5) % 1.0
            
            rise_hour = (rise_frac * 24) + tz_offset
            set_hour = (set_frac * 24) + tz_offset
            
            def format_time(hours):
                h = int(hours)
                m = int((hours - h) * 60)
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
