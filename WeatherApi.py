import requests

def get_general_weather(latitude: float, longitude: float, location_name: str = "") -> dict:
    """Gets everyday weather info for a regular person's daily planning.
 
    Use this for general questions like "what's the weather today",
    "will it rain", "should I carry an umbrella", or "is it hot today" —
    when the user hasn't identified themselves as a farmer, fisherman, or
    aviation professional.
 
    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
        location_name: Optional human-readable name, e.g. "Mumbai".
 
    Returns:
        A dictionary with:
        - location_name: the location passed in (or coordinates if empty)
        - current: temperature (C), "feels like" temperature (C), humidity
          (%), and a plain-language condition label
        - today: high/low temp (C), rain chance (%), UV index, and a
          plain-language condition label
        - advice: simple suggestions (carry_umbrella, wear_sunscreen,
          stay_hydrated) as booleans based on today's conditions
        - alert: a warning string if today has an extreme weather alert
          (heavy rain, heatwave, storm), else None
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,"
                  "precipitation_probability_max,uv_index_max",
        "forecast_days": 1,
        "timezone": "auto",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
 
    condition_labels = {
        0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "foggy",
        51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "moderate rain", 65: "heavy rain",
        80: "rain showers", 81: "rain showers", 82: "violent rain showers",
        95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
    }
 
    def label(code: int) -> str:
        return condition_labels.get(code, "changing conditions")
 
    current = data["current"]
    daily = data["daily"]
    rain_chance = daily["precipitation_probability_max"][0]
    uv_index = daily["uv_index_max"][0]
    temp_max = daily["temperature_2m_max"][0]
 
    alert = None
    if daily["weather_code"][0] in (95, 96, 99):
        alert = "Thunderstorms expected — avoid unnecessary outdoor travel."
    elif rain_chance >= 70:
        alert = "Heavy rain likely today — plan for delays if commuting."
    elif temp_max >= 40:
        alert = "Very hot today — avoid prolonged sun exposure, drink plenty of water."
 
    return {
        "location_name": location_name or f"{latitude}, {longitude}",
        "current": {
            "temperature_c": current["temperature_2m"],
            "feels_like_c": current["apparent_temperature"],
            "humidity_pct": current["relative_humidity_2m"],
            "condition": label(current["weather_code"]),
        },
        "today": {
            "high_c": temp_max,
            "low_c": daily["temperature_2m_min"][0],
            "rain_chance_pct": rain_chance,
            "uv_index": uv_index,
            "condition": label(daily["weather_code"][0]),
        },
        "advice": {
            "carry_umbrella": rain_chance >= 40,
            "wear_sunscreen": uv_index >= 6,
            "stay_hydrated": temp_max >= 35,
        },
        "alert": alert,
    }


def get_farmer_weather(latitude: float, longitude: float, location_name: str = "") -> dict:
    """
    Gets weather and soil data relevant to farming decisions for a location.

    Use this whenever a farmer asks about rain, temperature, spraying,
    irrigation, sowing, or harvest timing. Returns today's and the next
    few days' forecast plus soil moisture and soil temperature, which are
    needed for irrigation and pesticide-spraying decisions.

    Args:
        latitude: Latitude of the farm/location.
        longitude: Longitude of the farm/location.
        location_name: Optional human-readable name of the location, e.g.
            "Karnal, Haryana", to include in the response for context.

    Returns:
        A dictionary with:
        - location_name: the location passed in (or coordinates if empty)
        - current: current temperature (C), humidity (%), wind speed (km/h),
        and a plain-language weather condition label
        - today: high/low temp (C), rain chance (%), rain amount (mm)
        - next_3_days: list of daily forecasts (date, high, low, rain chance,
        rain amount, condition) for near-term planning
        - soil: surface soil moisture (m3/m3) and soil temperature (C)
        - alert: a warning string if today's weather crosses a farming-
        relevant threshold (heavy rain, heatwave, high wind), else None
    """
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,"
                "precipitation_probability_max,precipitation_sum,"
                "wind_gusts_10m_max",
        "hourly": "soil_moisture_0_to_1cm,soil_temperature_0cm",
        "forecast_days": 4,
        "timezone": "auto",
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    condition_labels = {
        0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "foggy",
        51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "moderate rain", 65: "heavy rain",
        80: "rain showers", 81: "rain showers", 82: "violent rain showers",
        95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
    }

    def label(code: int) -> str:
        return condition_labels.get(code, "changing conditions")
    
    daily = data["daily"]
    current = data["current"]

    next_days = []
    for i in range(len(daily["time"])):
        next_days.append({
            "date": daily["time"][i],
            "high_c": daily["temperature_2m_max"][i],
            "low_c": daily["temperature_2m_min"][i],
            "rain_chance_pct": daily["precipitation_probability_max"][i],
            "rain_mm": daily["precipitation_sum"][i],
            "condition": label(daily["weather_code"][i]),
        })

    # Simple farmer-relevant alert check for today
    alert = None
    if daily["precipitation_sum"][0] >= 50:
        alert = "Heavy rain expected today, avoid spraying and delay irrigation."
    elif daily["temperature_2m_max"][0] >= 40:
        alert = "Heatwave expected today , protect crops and livestock, avoid midday fieldwork."
    elif daily["wind_gusts_10m_max"][0] >= 50:
        alert = "Strong winds expected today , avoid spraying, secure loose structures."

    return {
        "location_name": location_name or f"{latitude}, {longitude}",
        "current": {
            "temperature_c": current["temperature_2m"],
            "humidity_pct": current["relative_humidity_2m"],
            "wind_speed_kmh": current["wind_speed_10m"],
            "condition": label(current["weather_code"]),
        },
        "today": next_days[0],
        "next_3_days": next_days[1:],
        "soil": {
            "moisture_m3_per_m3": data["hourly"]["soil_moisture_0_to_1cm"][0],
            "surface_temperature_c": data["hourly"]["soil_temperature_0cm"][0],
        },
        "alert": alert,
    }
    
def get_fisherman_weather(latitude: float, longitude: float, location_name: str = "") -> dict:
    """Gets weather and sea condition data relevant to fishing safety for a coastal location.
 
    Use this whenever a fisherman asks about going out to sea, wave
    conditions, wind, storms, or whether it's safe to fish today. Combines
    wind/storm forecast with wave height and swell data. Only meaningful
    for coastal or ocean coordinates — inland locations will return empty
    or null marine data.
 
    Args:
        latitude: Latitude of the coastal location or fishing spot.
        longitude: Longitude of the coastal location or fishing spot.
        location_name: Optional human-readable name of the location, e.g.
            "Kochi coast, Kerala", to include in the response for context.
 
    Returns:
        A dictionary with:
        - location_name: the location passed in (or coordinates if empty)
        - current: current wind speed (km/h), wind direction (degrees),
          and a plain-language weather condition label
        - today: high/low temp (C), rain chance (%), max wind gusts (km/h)
        - sea: current wave height (m), swell height (m), and wave
          direction (degrees) — None if marine data is unavailable for
          this location (e.g. it's inland)
        - alert: a warning string if conditions are unsafe for fishing
          today (rough seas, storm, high wind), else None
    """
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    forecast_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "wind_speed_10m,wind_direction_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,"
                  "precipitation_probability_max,wind_gusts_10m_max",
        "forecast_days": 2,
        "timezone": "auto",
    }
    forecast_resp = requests.get(forecast_url, params=forecast_params, timeout=10)
    forecast_resp.raise_for_status()
    forecast = forecast_resp.json()
 
    condition_labels = {
        0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "foggy",
        51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "moderate rain", 65: "heavy rain",
        80: "rain showers", 81: "rain showers", 82: "violent rain showers",
        95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
    }
 
    def label(code: int) -> str:
        return condition_labels.get(code, "changing conditions")
 
    current = forecast["current"]
    daily = forecast["daily"]
 
    # Marine data — may fail or be null for inland coordinates
    sea = None
    try:
        marine_url = "https://marine-api.open-meteo.com/v1/marine"
        marine_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "wave_height,wave_direction,swell_wave_height",
            "timezone": "auto",
        }
        marine_resp = requests.get(marine_url, params=marine_params, timeout=10)
        marine_resp.raise_for_status()
        marine = marine_resp.json()["current"]
        if marine.get("wave_height") is not None:
            sea = {
                "wave_height_m": marine["wave_height"],
                "swell_height_m": marine["swell_wave_height"],
                "wave_direction_deg": marine["wave_direction"],
            }
    except requests.exceptions.RequestException:
        sea = None
 
    # Fishing-safety alert check
    alert = None
    wind_gust = daily["wind_gusts_10m_max"][0]
    wave_height = sea["wave_height_m"] if sea else None
 
    if daily["weather_code"][0] in (95, 96, 99):
        alert = "Thunderstorms expected — do not go out to sea today."
    elif wave_height is not None and wave_height >= 2.5:
        alert = "Rough seas expected — high waves make it unsafe to go far out."
    elif wind_gust >= 50:
        alert = "Strong winds expected — stay close to shore or postpone the trip."
 
    return {
        "location_name": location_name or f"{latitude}, {longitude}",
        "current": {
            "wind_speed_kmh": current["wind_speed_10m"],
            "wind_direction_deg": current["wind_direction_10m"],
            "condition": label(current["weather_code"]),
        },
        "today": {
            "high_c": daily["temperature_2m_max"][0],
            "low_c": daily["temperature_2m_min"][0],
            "rain_chance_pct": daily["precipitation_probability_max"][0],
            "max_wind_gust_kmh": wind_gust,
            "condition": label(daily["weather_code"][0]),
        },
        "sea": sea,
        "alert": alert,
    }
    
def get_aviation_weather(latitude: float, longitude: float, location_name: str = "") -> dict:
    """Gets weather data relevant to flight safety and briefings for a location.
 
    Use this whenever someone asks about flight conditions, visibility,
    fog, turbulence risk, or whether it's safe to fly today near an
    airport or airfield.
 
    Args:
        latitude: Latitude of the airport/airfield.
        longitude: Longitude of the airport/airfield.
        location_name: Optional human-readable name, e.g. "IGI Airport, Delhi".
 
    Returns:
        A dictionary with:
        - location_name: the location passed in (or coordinates if empty)
        - current: temperature (C), wind speed (km/h), wind direction
          (degrees), visibility (meters), cloud cover (%), and a
          plain-language condition label
        - today: max wind gusts (km/h), min visibility expected (meters),
          thunderstorm risk (True/False)
        - alert: a warning string if conditions are unsafe for flying
          today (low visibility, high wind, thunderstorms), else None
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,wind_direction_10m,"
                    "visibility,cloud_cover,weather_code",
        "hourly": "visibility,weather_code",
        "daily": "wind_gusts_10m_max",
        "forecast_days": 1,
        "timezone": "auto",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
 
    condition_labels = {
        0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "foggy",
        51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "moderate rain", 65: "heavy rain",
        80: "rain showers", 81: "rain showers", 82: "violent rain showers",
        95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
    }
 
    def label(code: int) -> str:
        return condition_labels.get(code, "changing conditions")
 
    current = data["current"]
    hourly_visibility = data["hourly"]["visibility"]
    hourly_codes = data["hourly"]["weather_code"]
    wind_gust = data["daily"]["wind_gusts_10m_max"][0]
 
    min_visibility = min(v for v in hourly_visibility if v is not None)
    thunderstorm_risk = any(c in (95, 96, 99) for c in hourly_codes)
 
    alert = None
    if thunderstorm_risk:
        alert = "Thunderstorms possible today — expect delays or diversions."
    elif min_visibility < 1000:
        alert = "Very low visibility expected (fog) — flight delays likely."
    elif wind_gust >= 55:
        alert = "Strong wind gusts expected — turbulence and crosswind risk."
 
    return {
        "location_name": location_name or f"{latitude}, {longitude}",
        "current": {
            "temperature_c": current["temperature_2m"],
            "wind_speed_kmh": current["wind_speed_10m"],
            "wind_direction_deg": current["wind_direction_10m"],
            "visibility_m": current["visibility"],
            "cloud_cover_pct": current["cloud_cover"],
            "condition": label(current["weather_code"]),
        },
        "today": {
            "max_wind_gust_kmh": wind_gust,
            "min_visibility_m": min_visibility,
            "thunderstorm_risk": thunderstorm_risk,
        },
        "alert": alert,
    }
    
    
def get_disaster_risk_weather(latitude: float, longitude: float, location_name: str = "") -> dict:
    """Gets extreme weather and disaster risk data for a location.
 
    Use this whenever someone asks about flood risk, cyclone/storm
    warnings, heatwave risk, disaster preparedness, or early warnings for
    an area — typically disaster management officials or anyone asking
    about danger/safety rather than everyday conditions.
 
    Args:
        latitude: Latitude of the location/region.
        longitude: Longitude of the location/region.
        location_name: Optional human-readable name, e.g. "Puri, Odisha".
 
    Returns:
        A dictionary with:
        - location_name: the location passed in (or coordinates if empty)
        - today: high/low temp (C), total rainfall expected (mm), max wind
          gusts (km/h), and a plain-language condition label
        - next_3_days: list of daily forecasts (date, rainfall mm, max wind
          gusts km/h, condition) to track an approaching system
        - risk_level: one of "normal", "watch", "warning", "severe" — the
          highest risk level found across today and the next 3 days
        - risk_reasons: list of strings explaining what's driving the risk
          level (e.g. "65mm rainfall expected Thursday")
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,"
                  "precipitation_sum,wind_gusts_10m_max",
        "forecast_days": 4,
        "timezone": "auto",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    daily = data["daily"]
 
    condition_labels = {
        0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "foggy",
        51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "moderate rain", 65: "heavy rain",
        80: "rain showers", 81: "rain showers", 82: "violent rain showers",
        95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
    }
 
    def label(code: int) -> str:
        return condition_labels.get(code, "changing conditions")
 
    days = []
    for i in range(len(daily["time"])):
        days.append({
            "date": daily["time"][i],
            "high_c": daily["temperature_2m_max"][i],
            "low_c": daily["temperature_2m_min"][i],
            "rainfall_mm": daily["precipitation_sum"][i],
            "max_wind_gust_kmh": daily["wind_gusts_10m_max"][i],
            "condition": label(daily["weather_code"][i]),
            "weather_code": daily["weather_code"][i],
        })
 
    # Determine overall risk level across today + next 3 days
    risk_level = "normal"
    risk_reasons = []
 
    for day in days:
        day_risk = "normal"
        if day["weather_code"] in (95, 96, 99):
            day_risk = "severe"
            risk_reasons.append(f"Thunderstorm risk on {day['date']}")
        if day["rainfall_mm"] >= 100:
            day_risk = "severe"
            risk_reasons.append(f"{day['rainfall_mm']}mm rainfall expected on {day['date']} — flood risk")
        elif day["rainfall_mm"] >= 50:
            day_risk = max(day_risk, "warning", key=["normal", "watch", "warning", "severe"].index)
            risk_reasons.append(f"{day['rainfall_mm']}mm rainfall expected on {day['date']}")
        if day["max_wind_gust_kmh"] >= 80:
            day_risk = "severe"
            risk_reasons.append(f"Wind gusts up to {day['max_wind_gust_kmh']}km/h on {day['date']} — cyclone-level winds")
        elif day["max_wind_gust_kmh"] >= 50:
            day_risk = max(day_risk, "watch", key=["normal", "watch", "warning", "severe"].index)
        if day["high_c"] >= 45:
            day_risk = max(day_risk, "warning", key=["normal", "watch", "warning", "severe"].index)
            risk_reasons.append(f"Extreme heat ({day['high_c']}°C) expected on {day['date']}")
 
        levels = ["normal", "watch", "warning", "severe"]
        if levels.index(day_risk) > levels.index(risk_level):
            risk_level = day_risk
 
    return {
        "location_name": location_name or f"{latitude}, {longitude}",
        "today": days[0],
        "next_3_days": days[1:],
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
    }
