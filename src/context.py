import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TOMTOM_API_KEY  = os.getenv("TOMTOM_API_KEY")


# ─── 1. WEATHER ───────────────────────────────────────────
def get_weather_data(lat: float, lon: float) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon,
              "appid": WEATHER_API_KEY, "units": "metric"}
    return requests.get(url, params=params).json()

def weather_score(lat: float, lon: float) -> float:
    data       = get_weather_data(lat, lon)
    condition  = data["weather"][0]["main"].lower()
    visibility = data.get("visibility", 10000)

    condition_map = {
        "clear": 0.0, "clouds": 0.1, "drizzle": 0.4,
        "rain": 0.6,  "thunderstorm": 0.9, "snow": 0.8,
        "fog": 0.7,   "mist": 0.5, "haze": 0.4,
    }
    base = condition_map.get(condition, 0.3)

    if visibility < 1000:   base = min(base + 0.3,  1.0)
    elif visibility < 4000: base = min(base + 0.15, 1.0)

    return round(base, 3)


# ─── 2. NIGHT SCORE ───────────────────────────────────────
def night_score() -> float:
    hour = datetime.now().hour
    if 0 <= hour <= 5:     return 1.0
    elif 6 <= hour <= 7:   return 0.4
    elif 18 <= hour <= 20: return 0.4
    elif 21 <= hour <= 23: return 0.7
    else:                  return 0.0


# ─── 3. TOMTOM TRAFFIC ────────────────────────────────────

def get_tomtom_flow(lat: float, lon: float) -> dict:
    """
    TomTom Flow API — returns real-time speed vs free flow speed.
    zoom=10 gives segment-level granularity around the point.
    """
    url = (
        f"https://api.tomtom.com/traffic/services/4/flowSegmentData/"
        f"absolute/10/json"
    )
    params = {
        "key":   TOMTOM_API_KEY,
        "point": f"{lat},{lon}",
    }
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"TomTom Flow error: {e}")
        return {}


def get_tomtom_incidents(lat: float, lon: float,
                         radius_m: int = 2000) -> dict:
    """
    TomTom Incidents API — returns real accidents, closures, hazards.
    bbox format: minLon,minLat,maxLon,maxLat
    """
    deg_offset = radius_m / 111000   # meters → degrees

    min_lat = lat - deg_offset
    max_lat = lat + deg_offset
    min_lon = lon - deg_offset
    max_lon = lon + deg_offset

    url = (
        f"https://api.tomtom.com/traffic/services/5/incidentDetails"
    )
    params = {
        "key":      TOMTOM_API_KEY,
        "bbox":     f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "fields":   "{incidents{type,properties{iconCategory,magnitudeOfDelay,events{description,code}}}}",
        "language": "en-GB",
    }
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"TomTom Incidents error: {e}")
        return {}


def flow_speed_score(flow_data: dict) -> float:
    """
    Actual speed vs free flow speed.
    TomTom returns currentSpeed and freeFlowSpeed directly.
    """
    try:
        segment = flow_data.get("flowSegmentData", {})
        current_speed  = segment.get("currentSpeed", None)    # km/h
        freeflow_speed = segment.get("freeFlowSpeed", None)   # km/h

        if current_speed is None or freeflow_speed is None:
            return 0.2

        if current_speed >= 70:   return 0.0
        elif current_speed >= 50: return 0.2
        elif current_speed >= 30: return 0.5
        elif current_speed >= 15: return 0.75
        else:                     return 1.0

    except Exception:
        return 0.2


def congestion_score(flow_data: dict) -> float:
    """
    Speed ratio = currentSpeed / freeFlowSpeed.
    Closer to 1.0 = free flow, closer to 0.0 = gridlock.
    """
    try:
        segment = flow_data.get("flowSegmentData", {})
        current  = segment.get("currentSpeed", None)
        freeflow = segment.get("freeFlowSpeed", None)

        if not current or not freeflow or freeflow == 0:
            return 0.2

        ratio = current / freeflow   # 1.0 = no congestion

        if ratio >= 0.9:   return 0.0    # Free flow
        elif ratio >= 0.7: return 0.2    # Light
        elif ratio >= 0.5: return 0.5    # Moderate
        elif ratio >= 0.3: return 0.75   # Heavy
        else:              return 1.0    # Standstill

    except Exception:
        return 0.2


def travel_delay_score(flow_data: dict) -> float:
    """
    TomTom provides currentTravelTime vs freeFlowTravelTime directly.
    delay_ratio = currentTravelTime / freeFlowTravelTime
    """
    try:
        segment  = flow_data.get("flowSegmentData", {})
        current  = segment.get("currentTravelTime", None)    # seconds
        freeflow = segment.get("freeFlowTravelTime", None)   # seconds

        if not current or not freeflow or freeflow == 0:
            return 0.2

        ratio = current / freeflow

        if ratio <= 1.1:   return 0.0
        elif ratio <= 1.3: return 0.2
        elif ratio <= 1.6: return 0.5
        elif ratio <= 2.0: return 0.75
        else:              return 1.0

    except Exception:
        return 0.2


def incident_score(incident_data: dict) -> float:
    """
    TomTom incident magnitudeOfDelay: 0=Unknown, 1=Minor, 2=Moderate,
                                      3=Major, 4=Undefined (used for closures)
    iconCategory maps to incident type.
    """
    try:
        incidents = incident_data.get("incidents", [])
        if not incidents:
            return 0.0

        # TomTom magnitude of delay → risk
        magnitude_map = {
            0: 0.1,   # Unknown
            1: 0.3,   # Minor
            2: 0.6,   # Moderate
            3: 0.9,   # Major
            4: 1.0,   # Road closed
        }

        # TomTom icon category → type weight
        category_weight = {
            1:  1.0,   # Accident
            2:  0.5,   # Fog
            3:  0.6,   # Dangerous conditions
            4:  0.4,   # Rain
            5:  0.7,   # Ice
            6:  0.5,   # Jam
            7:  0.4,   # Lane closed
            8:  0.9,   # Road closed
            9:  0.5,   # Road works
            10: 0.3,   # Wind
            11: 0.4,   # Flooding
            14: 0.8,   # Broken down vehicle
        }

        scores = []
        for inc in incidents:
            props     = inc.get("properties", {})
            magnitude = props.get("magnitudeOfDelay", 0)
            category  = props.get("iconCategory", 6)

            mag_score = magnitude_map.get(magnitude, 0.3)
            cat_score = category_weight.get(category, 0.5)
            scores.append(mag_score * cat_score)

        if not scores:
            return 0.0

        base          = max(scores)
        count_penalty = min(len(scores) * 0.05, 0.2)
        return round(min(base + count_penalty, 1.0), 3)

    except Exception:
        return 0.0


def traffic_score(lat: float, lon: float) -> float:
    """
    Single function — one flow call + one incident call.
    Combines all 4 signals into one traffic risk score.
    """
    flow_data     = get_tomtom_flow(lat, lon)
    incident_data = get_tomtom_incidents(lat, lon)

    speed      = flow_speed_score(flow_data)
    congestion = congestion_score(flow_data)
    delay      = travel_delay_score(flow_data)
    incident   = incident_score(incident_data)

    w_speed      = 0.25
    w_congestion = 0.30
    w_delay      = 0.25
    w_incident   = 0.20

    return round(min(
        w_speed      * speed      +
        w_congestion * congestion +
        w_delay      * delay      +
        w_incident   * incident,
        1.0
    ), 3)


# ─── 4. FINAL CONTEXT SCORE ───────────────────────────────
def get_context_score(lat: float, lon: float) -> dict:
    """
    Single lat/lon — TomTom and OpenWeather both use normal lat, lon.
    """
    w_weather = 0.40
    w_night   = 0.25
    w_traffic = 0.35

    weather = weather_score(lat, lon)
    night   = night_score()
    traffic = traffic_score(lat, lon)

    final = (
        w_weather * weather +
        w_night   * night   +
        w_traffic * traffic
    )

    return {
        "context_score": round(min(final, 1.0), 3),
        "breakdown": {
            "weather_score":  weather,
            "night_score":    night,
            "traffic_score":  traffic,
        }
    }