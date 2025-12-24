import math
import random
from datetime import timedelta
from django.utils import timezone


def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula (km)"""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def generate_otp():
    return str(random.randint(100000, 999999))


def otp_expiry_time(minutes):
    return timezone.now() + timedelta(minutes=minutes)
