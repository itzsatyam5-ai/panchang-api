import swisseph as swe
from datetime import datetime, timedelta
import pytz

# Use Lahiri Ayanamsa strictly as specified in Master Prompt
swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

TITHI_NAMES = [
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी",
    "नवमी", "दशमी", "एकादशी", "द्वाद्शी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी",
    "नवमी", "दशमी", "एकादशी", "द्वाद्शी", "त्रयोदशी", "चतुर्दशी", "अमावस्या"
]

NAKSHATRA_NAMES = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य",
    "अश्लेषा", "मघा", "पूर्वाफाल्गुनी", "उत्तराफाल्गुनी", "हस्त", "चित्रा", "स्वाती",
    "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण",
    "धनिष्ठा", "शतभिषा", "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती"
]

YOGA_NAMES = [
    "विष्कम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन", "अतिगण्ड", "सुकर्मा", "धृति",
    "शूल", "गण्ड", "वृद्धि", "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धि",
    "व्यतीपात", "वरीयान", "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ", "शुक्ल",
    "ब्रह्म", "ऐन्द्र", "वैधृति"
]

KARANA_NAMES = [
    "बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि (भद्रा)",
    "शकुनि", "चतुष्पाद", "नाग", "किंस्तुघ्न"
]

CHOGHADIYA_DAY_TYPES = [
    {"hi": "उद्वेग", "nature": "अशुभ"},
    {"hi": "चर", "nature": "शुभ"},
    {"hi": "लाभ", "nature": "शुभ"},
    {"hi": "अमृत", "nature": "शुभ"},
    {"hi": "काल", "nature": "अशुभ"},
    {"hi": "शुभ", "nature": "शुभ"},
    {"hi": "रोग", "nature": "अशुभ"},
    {"hi": "उद्वेग", "nature": "अशुभ"}
]

WEEKDAYS_HI = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]

def datetime_to_jd(dt):
    utc_dt = dt.astimezone(pytz.utc)
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)

def jd_to_datetime(jd, timezone_str="Asia/Kolkata"):
    year, month, day, hour_decimal = swe.revjul(jd)
    hours = int(hour_decimal)
    minutes = int((hour_decimal - hours) * 60)
    seconds = int((((hour_decimal - hours) * 60) - minutes) * 60)
    
    dt_utc = datetime(year, month, day, hours, minutes, seconds, tzinfo=pytz.utc)
    return dt_utc.astimezone(pytz.timezone(timezone_str))

def get_planet_lon(jd, planet):
    res = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)
    return res[0][0] % 360

def format_time_12h(dt):
    return dt.strftime("%I:%M %p").lstrip("0")

def get_sun_rise_set(dt, lat, lon):
    tz = pytz.timezone("Asia/Kolkata")
    local_midnight = tz.localize(datetime(dt.year, dt.month, dt.day, 0, 0, 1))
    jd_midnight = datetime_to_jd(local_midnight)

    # Sunrise
    res_rise = swe.rise_trans(jd_midnight, swe.SUN, geopos=(lon, lat, 0), rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)
    sunrise_jd = res_rise[1][0]
    sunrise_dt = jd_to_datetime(sunrise_jd)

    # Sunset
    res_set = swe.rise_trans(jd_midnight, swe.SUN, geopos=(lon, lat, 0), rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)
    sunset_jd = res_set[1][0]
    sunset_dt = jd_to_datetime(sunset_jd)

    # Next Sunrise
    res_next_rise = swe.rise_trans(jd_midnight + 1.0, swe.SUN, geopos=(lon, lat, 0), rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)
    next_sunrise_dt = jd_to_datetime(res_next_rise[1][0])

    return sunrise_dt, sunset_dt, next_sunrise_dt

def find_boundary_time(start_dt, end_dt, calc_func, target_val):
    low = start_dt.timestamp()
    high = end_dt.timestamp()
    
    for _ in range(15):  # High precision binary search
        mid = (low + high) / 2
        mid_dt = datetime.fromtimestamp(mid, tz=start_dt.tzinfo)
        val = calc_func(mid_dt)
        
        if (target_val == 0 and val > 28) or (val < target_val and not (target_val == 0 and val > 28)):
            low = mid
        else:
            high = mid
            
    return datetime.fromtimestamp(high, tz=start_dt.tzinfo)

def calculate_full_panchang(date_str, lat, lon):
    tz = pytz.timezone("Asia/Kolkata")
    dt = datetime.strptime(date_str, "%Y-%m-%d")

    sunrise_dt, sunset_dt, next_sunrise_dt = get_sun_rise_set(dt, lat, lon)
    sunrise_jd = datetime_to_jd(sunrise_dt)

    # Sun & Moon Longitudes at Sunrise
    sun_lon = get_planet_lon(sunrise_jd, swe.SUN)
    moon_lon = get_planet_lon(sunrise_jd, swe.MOON)

    # 1. Tithi Calculation
    diff = (moon_lon - sun_lon) % 360
    tithi_index = int(diff / 12)
    tithi_num = tithi_index + 1
    paksha = "शुक्ल पक्ष" if tithi_index < 15 else "कृष्ण पक्ष"
    tithi_name = TITHI_NAMES[tithi_index]

    # Boundary for Tithi End
    next_target_tithi = (tithi_index + 1) % 30
    calc_tithi_fn = lambda d: int(((get_planet_lon(datetime_to_jd(d), swe.MOON) - get_planet_lon(datetime_to_jd(d), swe.SUN)) % 360) / 12)
    tithi_end_dt = find_boundary_time(sunrise_dt, next_sunrise_dt, calc_tithi_fn, next_target_tithi)

    # 2. Nakshatra Calculation
    nak_index = int(moon_lon / (360 / 27))
    nak_name = NAKSHATRA_NAMES[nak_index]
    next_target_nak = (nak_index + 1) % 27
    calc_nak_fn = lambda d: int(get_planet_lon(datetime_to_jd(d), swe.MOON) / (360 / 27))
    nak_end_dt = find_boundary_time(sunrise_dt, next_sunrise_dt, calc_nak_fn, next_target_nak)

    # 3. Yoga Calculation
    yoga_diff = (moon_lon + sun_lon) % 360
    yoga_index = int(yoga_diff / (360 / 27))
    yoga_name = YOGA_NAMES[yoga_index]

    # 4. Karana Calculation
    karana_index = int(diff / 6)
    if karana_index == 0:
        karana_name = KARANA_NAMES[10]
    elif karana_index >= 57:
        karana_name = KARANA_NAMES[7 + (karana_index - 57)]
    else:
        karana_name = KARANA_NAMES[(karana_index - 1) % 7]

    # 5. Muhurat & Kaal Timings
    day_duration = (sunset_dt - sunrise_dt).total_seconds()
    segment = day_duration / 8

    rahu_order = [1, 6, 4, 4, 5, 2, 7] # Day offset
    weekday_idx = sunrise_dt.weekday()
    
    rahu_start = sunrise_dt + timedelta(seconds=segment * rahu_order[weekday_idx])
    rahu_end = rahu_start + timedelta(seconds=segment)

    # Abhijit Muhurat
    one_fifth = day_duration / 15
    abhijit_start = sunrise_dt + timedelta(seconds=one_fifth * 7)
    abhijit_end = sunrise_dt + timedelta(seconds=one_fifth * 8)

    # Brahma Muhurat
    brahma_start = sunrise_dt - timedelta(minutes=96)
    brahma_end = sunrise_dt - timedelta(minutes=48)

    # Day Choghadiya
    chog_part = day_duration / 8
    day_choghadiya = []
    day_start_offsets = [0, 5, 3, 1, 6, 4, 2]
    start_offset = day_start_offsets[weekday_idx]

    for i in range(8):
        c_info = CHOGHADIYA_DAY_TYPES[(start_offset + i) % 8]
        p_start = sunrise_dt + timedelta(seconds=chog_part * i)
        p_end = sunrise_dt + timedelta(seconds=chog_part * (i + 1))
        day_choghadiya.append({
            "name_hi": c_info["hi"],
            "nature": c_info["nature"],
            "time": f"{format_time_12h(p_start)} से {format_time_12h(p_end)}"
        })

    return {
        "status": "success",
        "location": {"latitude": lat, "longitude": lon},
        "basic_info": {
            "date": dt.strftime("%d-%m-%Y"),
            "day_hi": WEEKDAYS_HI[weekday_idx],
            "paksha": paksha,
            "ritu": "वर्षा ऋतु",
            "ayana": "दक्षिणायन"
        },
        "sun_moon": {
            "sunrise": format_time_12h(sunrise_dt),
            "sunset": format_time_12h(sunset_dt)
        },
        "panchang": {
            "tithi": f"{tithi_name} (समाप्ति: {format_time_12h(tithi_end_dt)})",
            "tithi_number": tithi_num,
            "nakshatra": f"{nak_name} (समाप्ति: {format_time_12h(nak_end_dt)})",
            "yoga": yoga_name,
            "karana": karana_name
        },
        "muhurat_and_kaal": {
            "rahu_kaal": f"{format_time_12h(rahu_start)} से {format_time_12h(rahu_end)}",
            "abhijit_muhurat": f"{format_time_12h(abhijit_start)} से {format_time_12h(abhijit_end)}",
            "brahma_muhurat": f"{format_time_12h(brahma_start)} से {format_time_12h(brahma_end)}"
        },
        "choghadiya": {
            "day_choghadiya": day_choghadiya
        }
    }
