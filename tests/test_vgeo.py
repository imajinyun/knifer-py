import pytest

from kniferpy import vgeo
from kniferpy.internal import geox
from kniferpy.verr import ValidationError
from kniferpy.vgeo import Coord, CoordType


def test_wgs84_to_gcj02_and_back() -> None:
    wgs = Coord(lng=116.397389, lat=39.908722)
    gcj = vgeo.wgs84_to_gcj02(wgs)
    want_gcj = Coord(lng=116.403632, lat=39.910125)
    assert vgeo.distance(gcj, want_gcj) < 1
    back = vgeo.gcj02_to_wgs84(gcj)
    assert vgeo.distance(wgs, back) < 1


def test_bd09_round_trip() -> None:
    wgs = Coord(lng=116.397389, lat=39.908722)
    bd = vgeo.wgs84_to_bd09(wgs)
    round_trip = vgeo.bd09_to_wgs84(bd)
    assert vgeo.distance(wgs, round_trip) < 2


def test_convert_dispatch_and_identity() -> None:
    wgs = Coord(lng=116.397389, lat=39.908722)
    assert vgeo.convert(wgs, CoordType.WGS84, CoordType.WGS84) == wgs
    gcj = vgeo.convert(wgs, CoordType.WGS84, CoordType.GCJ02)
    assert vgeo.distance(gcj, vgeo.wgs84_to_gcj02(wgs)) < 1e-9


def test_convert_unsupported() -> None:
    # All CoordType pairs are now supported, so unsupported conversion
    # raises only when the converter is missing from the registry.
    # We test that all same-type conversions are identity.
    coord = Coord(lng=116.404, lat=39.915)
    for ct in CoordType:
        assert vgeo.convert(coord, ct, ct) == coord


def test_outside_china_is_identity() -> None:
    outside = Coord(lng=-73.9857, lat=40.7484)
    assert vgeo.wgs84_to_gcj02(outside) == outside
    assert vgeo.gcj02_to_wgs84(outside) == outside


def test_in_china_boundary() -> None:
    assert vgeo.in_china(116.3, 39.9)
    assert not vgeo.in_china(-73, 40)


def test_distance_one_degree_latitude() -> None:
    d = vgeo.distance(Coord(lng=0, lat=0), Coord(lng=0, lat=1))
    assert abs(d - 111195) < 200


def test_bd09mc_round_trips() -> None:
    wgs = Coord(lng=116.397389, lat=39.908722)
    gcj = vgeo.wgs84_to_gcj02(wgs)
    bd = vgeo.gcj02_to_bd09(gcj)

    bdmc_from_wgs = vgeo.wgs84_to_bd09mc(wgs)
    bdmc_from_gcj = vgeo.gcj02_to_bd09mc(gcj)
    bdmc_from_bd = vgeo.bd09_to_bd09mc(bd)

    assert isinstance(vgeo.bd09mc_to_wgs84(bdmc_from_wgs), Coord)
    assert isinstance(vgeo.bd09mc_to_gcj02(bdmc_from_gcj), Coord)
    assert isinstance(vgeo.bd09mc_to_bd09(bdmc_from_bd), Coord)


def test_convert_dispatch_for_bd09mc() -> None:
    coord = Coord(lng=116.397389, lat=39.908722)
    bd = vgeo.wgs84_to_bd09(coord)
    bdmc = vgeo.convert(coord, CoordType.WGS84, CoordType.BD09MC)

    assert vgeo.convert(bdmc, CoordType.BD09MC, CoordType.WGS84)
    assert vgeo.convert(vgeo.wgs84_to_gcj02(coord), CoordType.GCJ02, CoordType.BD09MC)
    assert vgeo.convert(bdmc, CoordType.BD09MC, CoordType.GCJ02)
    assert vgeo.convert(bd, CoordType.BD09, CoordType.BD09MC)
    assert vgeo.convert(bdmc, CoordType.BD09MC, CoordType.BD09)


def test_internal_mercator_helpers_and_matrix_edges() -> None:
    assert geox._lat_mercator(geox._y_mercator(30.0)) == pytest.approx(30.0)
    assert geox._convert_mct(0.0) != 0.0
    assert -90 <= geox._bd09mc_to_lat(0.0) <= 90


def test_convert_unsupported_registry_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    coord = Coord(lng=116.0, lat=39.0)
    original = dict(geox._CONVERTERS)
    monkeypatch.setattr(geox, "_CONVERTERS", {})

    with pytest.raises(ValidationError) as exc_info:
        vgeo.convert(coord, CoordType.WGS84, CoordType.GCJ02)

    assert exc_info.value.code == "knifer.geo.unsupported_conversion"
    monkeypatch.setattr(geox, "_CONVERTERS", original)


def test_geo_error_alias() -> None:
    assert vgeo.GeoError is ValidationError
