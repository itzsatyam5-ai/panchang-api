from datetime import datetime
import swisseph as swe
from mappings import TITHIS, NAKSHATRAS, YOGAS, KARANAS

# Performance Optimization
swe.set_ephe_path('')
swe.set_sid_mode(swe.SIDM_LAHIRI)

def calculate_panchang(date_str: str, latitude: float, longitude: float, tz_offset: float = 5.5):
    try:
        # Input Validation & Julian Day Setup
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        
        # Sun and Moon position calculations
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        
        sun_long = sun_pos[0][0]
        moon_long = moon_pos[0][0]
        
        # पंचांग अंक गणना (Tithi, Nakshatra, Yoga, Karana)
        diff = (moon_long - sun_long) % 360
        tithi_no = int(diff / 12) + 1
        nakshatra_no = int(moon_long / (360.0 / 27.0)) + 1
        yoga_sum = (sun_long + moon_long) % 360
        yoga_no = int(yoga_sum / (360.0 / 27.0)) + 1
        
        karana_no = int(diff / 6.0) + 1
        if karana_no > 11:
            karana_no = ((karana_no - 1) % 7) + 1

        # सूर्योदय और सूर्यास्त की सटीक गणना (Fixed Tuple Error)
        geopos = (longitude, latitude, 0.0)
        jd_start = swe.julday(target_date.year, target_date.month, target_date.day, 0.0)
        
        try:
            # Correct parameter order for Python Swisseph
            rise_res = swe.rise_trans(jd_start, swe.SUN, "", swe.FLG_SWIEPH, swe.CALC_RISE, geopos)
            set_res = swe.rise_trans(jd_start, swe.SUN, "", swe.FLG_SWIEPH, swe.CALC_SET, geopos)
            
            # Safely extract Julian Day float value avoiding the 'tuple' error
            rise_jd = rise_res[0][0] if isinstance(rise_res, tuple) and isinstance(rise_res[0], tuple) else (rise_res[0] if isinstance(rise_res, tuple) else rise_res)
            set_jd = set_res[0][0] if isinstance(set_res, tuple) and isinstance(set_res[0], tuple) else (set_res[0] if isinstance(set_res, tuple) else set_res)

            # Convert JD to Hours properly
            rise_frac = (rise_jd + 0.5) % 1.0
            set_frac = (set_jd + 0.5) % 1.0
            
            rise_hour = (rise_frac * 24) + tz_offset
            set_hour = (set_frac * 24) + tz_offset
            
            # Helper function to format decimal hours into HH:MM
            def format_time(hours):
                h = int(hours)
                m = int((hours - h) * 60)
                return f"{h % 24:02d}:{m:02d}"
                
            sunrise_str = format_time(rise_hour)
            sunset_str = format_time(set_hour)
            
            # राहुकाल गणना (Rahukalam using accurate float times)
            day_duration = set_hour - rise_hour
            if day_duration < 0:
                day_duration += 24 # Handle midnight crossover
                
            sect_duration = day_duration / 8.0
            weekday = target_date.weekday()
            rahu_octets = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
            octet_no = rahu_octets.get(weekday, 2)
            
            rahu_start_hr = rise_hour + (sect_duration * (octet_no - 1))
            rahu_end_hr = rise_hour + (sect_duration * octet_no)
            
            rahukalam_str = f"{format_time(rahu_start_hr)} to {format_time(rahu_end_hr)}"
            
        except Exception as calc_err:
            raise ValueError(f"Could not calculate sunrise/sunset for given coordinates: {str(calc_err)}")

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
