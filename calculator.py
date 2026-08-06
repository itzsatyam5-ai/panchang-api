import swisseph as swe
from datetime import datetime, timedelta, date
import pytz
from typing import Dict, Any

# Lahiri Ayanamsa Set for Accurate Vedic Panchang
swe.set_sid_mode(swe.SIDM_LAHIRI)

# Hindi Mappings & Hindi Natures for Choghadiya
CHOGHADIYA_TYPES = {
    "Shubh": {"hi": "शुभ", "nature": "शुभ"},
    "Labh": {"hi": "लाभ", "nature": "शुभ"},
    "Amrit": {"hi": "अमृत", "nature": "शुभ"},
    "Char": {"hi": "चर", "nature": "सामान्य"},
    "Roga": {"hi": "रोग", "nature": "अशुभ"},
    "Kala": {"hi": "काल", "nature": "अशुभ"},
    "Udveg": {"hi": "उद्वेग", "nature": "अशुभ"}
}

# Weekday-wise Day Choghadiya Order (0=Monday, 6=Sunday)
DAY_CHOGHADIYA_PATTERN = {
    0: ["Amrit", "Kala", "Shubh", "Roga", "Udveg", "Char", "Labh", "Amrit"],      # Mon
    1: ["Roga", "Udveg", "Char", "Labh", "Amrit", "Kala", "Shubh", "Roga"],      # Tue
    2: ["Labh", "Amrit", "Kala", "Shubh", "Roga", "Udveg", "Char", "Labh"],      # Wed
    3: ["Shubh", "Roga", "Udveg", "Char", "Labh", "Amrit", "Kala", "Shubh"],      # Thu
    4: ["Char", "Labh", "Amrit", "Kala", "Shubh", "Roga", "Udveg", "Char"],      # Fri
    5: ["Kala", "Shubh", "Roga", "Udveg", "Char", "Labh", "Amrit", "Kala"],      # Sat
    6: ["Udveg", "Char", "Labh", "Amrit", "Kala", "Shubh", "Roga", "Udveg"]       # Sun
}

# Weekday-wise Night Choghadiya Order
NIGHT_CHOGHADIYA_PATTERN = {
    0: ["Char", "Roga", "Kala", "Labh", "Udveg", "Shubh", "Amrit", "Char"],      # Mon
    1: ["Kala", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Roga", "Kala"],      # Tue
    2: ["Amrit", "Char", "Roga", "Kala", "Labh", "Udveg", "Shubh", "Amrit"],      # Wed
    3: ["Udveg", "Shubh", "Amrit", "Char", "Roga", "Kala", "Labh", "Udveg"],      # Thu
    4: ["Shubh", "Amrit", "Char", "Roga", "Kala", "Labh", "Udveg", "Shubh"],      # Fri
    5: ["Labh", "Udveg", "Shubh", "Amrit", "Char", "Roga", "Kala", "Labh"],      # Sat
    6: ["Shubh", "Amrit", "Char", "Roga", "Kala", "Labh", "Udveg", "Shubh"]       # Sun
}

class PanchangCalculatorService:
    def __init__(self, lat: float, lon: float, tz_name: str = "Asia/Kolkata"):
        self.lat = lat
        self.lon = lon
        self.tz = pytz.timezone(tz_name)

    def _julian_day(self, dt: datetime) -> float:
        utc_dt = dt.astimezone(pytz.utc)
        return swe.julday(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0
        )

    def _jd_to_datetime(self, jd: float) -> datetime:
        year, month, day, hour_float = swe.revjul(jd)
        hours = int(hour_float)
        minutes = int((hour_float - hours) * 60)
        seconds = int((((hour_float - hours) * 60) - minutes) * 60)
        utc_dt = datetime(year, month, day, hours, minutes, seconds, tzinfo=pytz.utc)
        return utc_dt.astimezone(self.tz)

    def get_sun_rise_set(self, date_obj: date) -> Dict[str, datetime]:
        """
        Fix: Search from LOCAL MIDNIGHT (00:00:00) so that today's sunrise 
        and today's sunset are returned properly without date crossing bugs.
        """
        local_midnight = self.tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
        jd_midnight = self._julian_day(local_midnight)
        geopos = (self.lon, self.lat, 0.0)

        # Standard Sunrise (Upper limb visible with atmospheric refraction)
        res_rise = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_RISE, geopos)
        sunrise_jd = res_rise[1][0]

        # Standard Sunset
        res_set = swe.rise_trans(jd_midnight, swe.SUN, swe.CALC_SET, geopos)
        sunset_jd = res_set[1][0]

        return {
            "sunrise": self._jd_to_datetime(sunrise_jd),
            "sunset": self._jd_to_datetime(sunset_jd)
        }

    def get_next_sunrise(self, date_obj: date) -> datetime:
        next_date = date_obj + timedelta(days=1)
        return self.get_sun_rise_set(next_date)["sunrise"]

    def get_moon_rise_set(self, date_obj: date) -> Dict[str, Any]:
        """Calculates Moonrise and Moonset for given date."""
        local_midnight = self.tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
        jd_midnight = self._julian_day(local_midnight)
        geopos = (self.lon, self.lat, 0.0)

        try:
            res_rise = swe.rise_trans(jd_midnight, swe.MOON, swe.CALC_RISE, geopos)
            moonrise = self._jd_to_datetime(res_rise[1][0]).strftime("%I:%M %p")
        except Exception:
            moonrise = "चंद्रोदय नहीं"

        try:
            res_set = swe.rise_trans(jd_midnight, swe.MOON, swe.CALC_SET, geopos)
            moonset = self._jd_to_datetime(res_set[1][0]).strftime("%I:%M %p")
        except Exception:
            moonset = "चंद्रास्त नहीं"

        return {"moonrise": moonrise, "moonset": moonset}

    def calculate_special_kaals(self, sunrise: datetime, sunset: datetime, weekday: int) -> Dict[str, str]:
        """Calculates Rahu Kaal, Yamaganda, Gulika, Abhijit & Brahma Muhurat safely."""
        day_duration = (sunset - sunrise).total_seconds()
        part_8 = day_duration / 8.0

        # Segments index (1-based) for Weekdays (Mon=0, Tue=1 ... Sun=6)
        rahu_map = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
        yamaganda_map = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
        gulika_map = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

        def get_time_range(part_idx: int):
            start = sunrise + timedelta(seconds=(part_idx - 1) * part_8)
            end = sunrise + timedelta(seconds=part_idx * part_8)
            return f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"

        # Abhijit Muhurat (8th Muhurat out of 15 parts of daytime)
        part_15 = day_duration / 15.0
        abhijit_start = sunrise + timedelta(seconds=7 * part_15)
        abhijit_end = sunrise + timedelta(seconds=8 * part_15)

        # Brahma Muhurat (Begins 96 mins before Sunrise, lasts 48 mins)
        brahma_start = sunrise - timedelta(minutes=96)
        brahma_end = sunrise - timedelta(minutes=48)

        return {
            "rahu_kaal": get_time_range(rahu_map[weekday]),
            "yamaganda": get_time_range(yamaganda_map[weekday]),
            "gulika": get_time_range(gulika_map[weekday]),
            "abhijit_muhurat": f"{abhijit_start.strftime('%I:%M %p')} - {abhijit_end.strftime('%I:%M %p')}",
            "brahma_muhurat": f"{brahma_start.strftime('%I:%M %p')} - {brahma_end.strftime('%I:%M %p')}"
        }

    def calculate_choghadiya(self, sunrise: datetime, sunset: datetime, next_sunrise: datetime, weekday: int) -> Dict[str, list]:
        """Calculates Day and Night Choghadiya intervals with Hindi translation."""
        day_part = (sunset - sunrise).total_seconds() / 8.0
        night_part = (next_sunrise - sunset).total_seconds() / 8.0

        day_list = []
        night_list = []

        # Day Choghadiya
        for i, c_name in enumerate(DAY_CHOGHADIYA_PATTERN[weekday]):
            start = sunrise + timedelta(seconds=i * day_part)
            end = sunrise + timedelta(seconds=(i + 1) * day_part)
            day_list.append({
                "name_en": c_name,
                "name_hi": CHOGHADIYA_TYPES[c_name]["hi"],
                "nature": CHOGHADIYA_TYPES[c_name]["nature"],
                "time": f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
            })

        # Night Choghadiya
        for i, c_name in enumerate(NIGHT_CHOGHADIYA_PATTERN[weekday]):
            start = sunset + timedelta(seconds=i * night_part)
            end = sunset + timedelta(seconds=(i + 1) * night_part)
            night_list.append({
                "name_en": c_name,
                "name_hi": CHOGHADIYA_TYPES[c_name]["hi"],
                "nature": CHOGHADIYA_TYPES[c_name]["nature"],
                "time": f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
            })

        return {
            "day_choghadiya": day_list,
            "night_choghadiya": night_list
        }
