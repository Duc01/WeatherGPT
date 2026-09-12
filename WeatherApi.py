import requests


def get_weather(latitude: float, longitude: float) -> dict:
    """Gets the current weather and today's forecast for a specific location.

    Args:
    
    latitude: Latitude of the location (e.g. 28.6139 for Delhi).
    longitude: Longitude of the location (e.g. 77.2090 for Delhi).

    returns:
    A dictionary with current temperature, conditions, and today's forecast.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "timezone": "auto",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


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