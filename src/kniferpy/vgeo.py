from __future__ import annotations

from kniferpy.internal import geox
from kniferpy.internal.geox import Coord, CoordType

__all__ = [
    "Coord",
    "CoordType",
    "convert",
    "wgs84_to_gcj02",
    "gcj02_to_wgs84",
    "gcj02_to_bd09",
    "bd09_to_gcj02",
    "wgs84_to_bd09",
    "bd09_to_wgs84",
    "wgs84_to_bd09mc",
    "bd09mc_to_wgs84",
    "gcj02_to_bd09mc",
    "bd09mc_to_gcj02",
    "bd09_to_bd09mc",
    "bd09mc_to_bd09",
    "distance",
    "in_china",
]


def convert(coord: Coord, from_type: CoordType, to_type: CoordType) -> Coord:
    return geox.convert(coord, from_type, to_type)


def wgs84_to_gcj02(coord: Coord) -> Coord:
    return geox.wgs84_to_gcj02(coord)


def gcj02_to_wgs84(coord: Coord) -> Coord:
    return geox.gcj02_to_wgs84(coord)


def gcj02_to_bd09(coord: Coord) -> Coord:
    return geox.gcj02_to_bd09(coord)


def bd09_to_gcj02(coord: Coord) -> Coord:
    return geox.bd09_to_gcj02(coord)


def wgs84_to_bd09(coord: Coord) -> Coord:
    return geox.wgs84_to_bd09(coord)


def bd09_to_wgs84(coord: Coord) -> Coord:
    return geox.bd09_to_wgs84(coord)


def wgs84_to_bd09mc(coord: Coord) -> Coord:
    return geox.wgs84_to_bd09mc(coord)


def bd09mc_to_wgs84(coord: Coord) -> Coord:
    return geox.bd09mc_to_wgs84(coord)


def gcj02_to_bd09mc(coord: Coord) -> Coord:
    return geox.gcj02_to_bd09mc(coord)


def bd09mc_to_gcj02(coord: Coord) -> Coord:
    return geox.bd09mc_to_gcj02(coord)


def bd09_to_bd09mc(coord: Coord) -> Coord:
    return geox.bd09_to_bd09mc(coord)


def bd09mc_to_bd09(coord: Coord) -> Coord:
    return geox.bd09mc_to_bd09(coord)


def distance(a: Coord, b: Coord) -> float:
    return geox.distance(a, b)


def in_china(lng: float, lat: float) -> bool:
    return geox.in_china(lng, lat)