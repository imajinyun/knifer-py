from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from kniferpy.verr import ValidationError

_X_PI = math.pi * 3000.0 / 180.0
_EARTH_A = 6378245.0
_EARTH_EE = 0.00669342162296594323
_EARTH_RADIUS_M = 6371000.0


@dataclass(slots=True, frozen=True)
class Coord:
    lng: float
    lat: float


class CoordType(str, Enum):
    WGS84 = "WGS84"
    GCJ02 = "GCJ02"
    BD09 = "BD09"
    BD09MC = "BD09MC"


def in_china(lng: float, lat: float) -> bool:
    return 72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271


def _transform_lat(x: float, y: float) -> float:
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y
    ret += 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(x: float, y: float) -> float:
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y
    ret += 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(coord: Coord) -> Coord:
    if not in_china(coord.lng, coord.lat):
        return coord
    d_lat = _transform_lat(coord.lng - 105.0, coord.lat - 35.0)
    d_lng = _transform_lng(coord.lng - 105.0, coord.lat - 35.0)
    rad_lat = coord.lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1 - _EARTH_EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((_EARTH_A * (1 - _EARTH_EE)) / (magic * sqrt_magic) * math.pi)
    d_lng = (d_lng * 180.0) / (_EARTH_A / sqrt_magic * math.cos(rad_lat) * math.pi)
    return Coord(lng=coord.lng + d_lng, lat=coord.lat + d_lat)


def gcj02_to_wgs84(coord: Coord) -> Coord:
    if not in_china(coord.lng, coord.lat):
        return coord
    gcj = wgs84_to_gcj02(coord)
    return Coord(lng=coord.lng * 2 - gcj.lng, lat=coord.lat * 2 - gcj.lat)


def gcj02_to_bd09(coord: Coord) -> Coord:
    z = math.sqrt(coord.lng * coord.lng + coord.lat * coord.lat)
    z += 0.00002 * math.sin(coord.lat * _X_PI)
    theta = math.atan2(coord.lat, coord.lng) + 0.000003 * math.cos(coord.lng * _X_PI)
    return Coord(lng=z * math.cos(theta) + 0.0065, lat=z * math.sin(theta) + 0.006)


def bd09_to_gcj02(coord: Coord) -> Coord:
    x = coord.lng - 0.0065
    y = coord.lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * _X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * _X_PI)
    return Coord(lng=z * math.cos(theta), lat=z * math.sin(theta))


def wgs84_to_bd09(coord: Coord) -> Coord:
    return gcj02_to_bd09(wgs84_to_gcj02(coord))


def bd09_to_wgs84(coord: Coord) -> Coord:
    return gcj02_to_wgs84(bd09_to_gcj02(coord))


_CONVERTERS = {
    (CoordType.WGS84, CoordType.GCJ02): wgs84_to_gcj02,
    (CoordType.WGS84, CoordType.BD09): wgs84_to_bd09,
    (CoordType.GCJ02, CoordType.WGS84): gcj02_to_wgs84,
    (CoordType.GCJ02, CoordType.BD09): gcj02_to_bd09,
    (CoordType.BD09, CoordType.GCJ02): bd09_to_gcj02,
    (CoordType.BD09, CoordType.WGS84): bd09_to_wgs84,
}


def convert(coord: Coord, from_type: CoordType, to_type: CoordType) -> Coord:
    if from_type == to_type:
        return coord
    converter = _CONVERTERS.get((from_type, to_type))
    if converter is None:
        raise ValidationError(
            message=f"unsupported coordinate conversion {from_type.value} to {to_type.value}",
            code="knifer.geo.unsupported_conversion",
            context={"from": from_type.value, "to": to_type.value},
        )
    return converter(coord)


def distance(a: Coord, b: Coord) -> float:
    lat1 = a.lat * math.pi / 180
    lat2 = b.lat * math.pi / 180
    d_lat = (b.lat - a.lat) * math.pi / 180
    d_lng = (b.lng - a.lng) * math.pi / 180
    sin_lat = math.sin(d_lat / 2)
    sin_lng = math.sin(d_lng / 2)
    h = sin_lat * sin_lat + math.cos(lat1) * math.cos(lat2) * sin_lng * sin_lng
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(h))
