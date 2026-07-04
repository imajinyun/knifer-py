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


# ---------------------------------------------------------------------------
# BD09MC (Baidu Mercator) conversions
# ---------------------------------------------------------------------------

_BD09MC_MATRIX = [
    [-0.0015702102444, 111320.7020616939, 1704480524535203.0, -10338987376042340.0,
     33512635187859060000.0, -35185669149653720000000.0, 11903781936193200000000000.0,
     -7961514359482190000000000000.0, 6023788526453200000000000000000.0],
    [8277.8470561775, 11155.9491188847, 2005425243107.0, -15210473022923.0,
     60419156845112000.0, -132040194914895000000.0, 128318418023823000000000.0,
     -39917944935083800000000000.0, 10369281734160300000000000000.0],
    [0.00337398766765, 11169.5536963581, 668127391268.0, -4725343180083.0,
     17682608746320000.0, -36475055673750000000.0, 333537436298020000000.0,
     -96685116438842000000000.0, 23396937574427000000000000.0],
    [0.00220636496208, 11128.0514420274, 440702398863.0, -3008259180562.0,
     10815903281580000.0, -213083866453080000.0, 185294835477750000000.0,
     -51059693845887000000000.0, 11829813564878000000000000.0],
    [-34448.96389906, 107092.6012808980, 12845196447047.0, -109670852225630.0,
     520960308346240000.0, -1443695776624200000.0, 2359804742352000000000.0,
     -2123513403225190000000000.0, 817135779460077000000000000.0],
]


def _y_mercator(lat: float) -> float:
    return math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)


def _lat_mercator(y: float) -> float:
    return math.atan(math.exp(y * math.pi / 180)) / math.pi * 360 - 90


def _convert_mct(lat: float) -> float:
    c_f = _BD09MC_MATRIX
    t = abs(lat) / 180.0 * math.pi
    cs = math.cos(t)
    cs2 = cs * cs
    cs3 = cs2 * cs
    cs4 = cs3 * cs
    cs5 = cs4 * cs
    cs6 = cs5 * cs
    cs7 = cs6 * cs
    result = 0
    for i in range(len(c_f)):
        row = c_f[i]
        term = row[0]
        term += row[1] * t
        term += row[2] * cs
        term += row[3] * cs2
        term += row[4] * cs3
        term += row[5] * cs4
        term += row[6] * cs5
        term += row[7] * cs6
        term += row[8] * cs7
        result += term * (lat ** i)
    return result


def _bd09mc_to_lat(y: float) -> float:
    low = -90.0
    high = 90.0
    for _ in range(20):
        mid = (low + high) / 2
        if _convert_mct(mid) < y:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def wgs84_to_bd09mc(coord: Coord) -> Coord:
    gcj = wgs84_to_gcj02(coord)
    return gcj02_to_bd09mc(gcj)


def bd09mc_to_wgs84(coord: Coord) -> Coord:
    gcj = bd09mc_to_gcj02(coord)
    return gcj02_to_wgs84(gcj)


def gcj02_to_bd09mc(coord: Coord) -> Coord:
    bd = gcj02_to_bd09(coord)
    return bd09_to_bd09mc(bd)


def bd09mc_to_gcj02(coord: Coord) -> Coord:
    bd = bd09mc_to_bd09(coord)
    return bd09_to_gcj02(bd)


def bd09_to_bd09mc(coord: Coord) -> Coord:
    x = _convert_mct(coord.lng)
    y = _y_mercator(coord.lat)
    return Coord(lng=x, lat=y)


def bd09mc_to_bd09(coord: Coord) -> Coord:
    lng = _bd09mc_to_lat(coord.lng)
    lat = _lat_mercator(coord.lat)
    return Coord(lng=lng, lat=lat)


# Register BD09MC converters
_CONVERTERS.update({
    (CoordType.WGS84, CoordType.BD09MC): wgs84_to_bd09mc,
    (CoordType.BD09MC, CoordType.WGS84): bd09mc_to_wgs84,
    (CoordType.GCJ02, CoordType.BD09MC): gcj02_to_bd09mc,
    (CoordType.BD09MC, CoordType.GCJ02): bd09mc_to_gcj02,
    (CoordType.BD09, CoordType.BD09MC): bd09_to_bd09mc,
    (CoordType.BD09MC, CoordType.BD09): bd09mc_to_bd09,
})
