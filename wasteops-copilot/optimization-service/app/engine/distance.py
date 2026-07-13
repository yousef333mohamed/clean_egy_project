from math import asin, cos, radians, sin, sqrt
from app.schemas.plans import Location


def haversine_meters(a: Location, b: Location) -> int:
    dlat = radians(b.latitude - a.latitude)
    dlon = radians(b.longitude - a.longitude)
    value = sin(dlat / 2) ** 2 + cos(radians(a.latitude)) * cos(radians(b.latitude)) * sin(dlon / 2) ** 2
    return round(6371000 * 2 * asin(sqrt(value)))
