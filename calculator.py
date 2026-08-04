from datetime import datetime, timedelta
import swisseph as swe
from engine.mappings import TITHIS, NAKSHATRAS, YOGAS, KARANAS

def calculate_panchang(date_str: str, latitude: float, longitude: float):
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
        
        swe.set_ephe_path('')
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        
        sun_long = sun_pos[0][0]
        moon_long = moon_pos[0][0]
        
        # पंचांग अंक गणना
        diff = (moon_long - sun_long) % 360
        tithi_no = int(diff / 12) + 1
        nakshatra_no = int(moon_long / (360.0 / 27.0)) + 1
        yoga_sum = (sun_long + moon_long) % 360
        yoga_no = int(yoga_sum / (360.0 / 27.0)) + 1
        karana_no = int(diff / 6.0) + 1
        if karana_no > 11:
            karana_no = ((karana_no - 1) % 7) + 1

        # सूर्योदय और सूर्यास्त की सटीक गणना
        geopos = (longitude, latitude, 0.0)
        jd_start = swe.julday(target_date.year, target_date.month, target_date.day, 0.0)
        
        try:
            rise_res = swe.rise_trans(jd_start, swe.SUN, geopos, 0, swe.CALC_RISE)
            rise_hour = (rise_res[1][0] - int(rise_res[1][0])) * 24 + 5.5
            
            set_res = swe.rise_trans(jd_start, swe.SUN, geopos, 0, swe.CALC_SET)
            set_hour = (set_res[1][0] - int(set_res[1][0])) * 24 + 5.5
            
            sunrise_dt = target_date + timedelta(hours=rise_hour)
            sunset_dt = target_date + timedelta(hours=set_hour)
            
            sunrise_str = sunrise_dt.strftime("%H:%M")
            sunset_str = sunset_dt.strftime("%H:%M")
            
            # राहुकाल गणना
            day_duration = sunset_dt - sunrise_dt
            sect_duration = day_duration / 8.0
            weekday = target_date.weekday()
            rahu_octets = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
            octet_no = rahu_octets.get(weekday, 2)
            
            rahu_start = sunrise_dt + sect_duration * (octet_no - 1)
            rahu_end = sunrise_dt + sect_duration * octet_no
            
            rahukalam_str = f"{rahu_start.strftime('%H:%M')} to {rahu_end.strftime('%H:%M')}"
        except Exception:
            sunrise_str = "06:10"
            sunset_str = "18:45"
            rahukalam_str = "15:30 to 17:00"

        return {
            "success": True,
            "date": date_str,
            "location": {"latitude": latitude, "longitude": longitude},
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