from kniferpy import vhash

# Reference values generated from the knifer-go internal/hash implementation.
_EXPECTED = {
    "knifer-go": {
        "rs": 1673183854, "js": 228748314, "pjw": 265044383, "elf": 265044383,
        "bkdr": 405017996, "sdbm": 360816744, "djb": 777868615, "ap": -1212426820,
        "fnvs": 1574034316, "hf": 10437, "hfip": 115, "tianl": 135597577,
        "java": 27007048, "fnv": 151374985, "add": 8,
    },
    "abc": {
        "rs": 822160044, "js": 895805535, "pjw": 26499, "elf": 26499,
        "bkdr": 1677554, "sdbm": 807794786, "djb": 193485963, "ap": -25651485,
        "fnvs": 33957123, "hf": 888, "hfip": 0, "tianl": 33734718,
        "java": 96354, "fnv": 1134309195, "add": 18,
    },
    "a": {
        "rs": 97, "js": 1359675315, "pjw": 97, "elf": 97,
        "bkdr": 97, "sdbm": 97, "djb": 177670, "ap": 97,
        "fnvs": 649420593, "hf": 0, "hfip": 0, "tianl": 29786,
        "java": 97, "fnv": 84696446, "add": 5,
    },
    "Hello, 世界": {
        "rs": 777705368, "js": 754737335, "pjw": 214561948, "elf": 214561948,
        "bkdr": 565320992, "sdbm": 983753916, "djb": 1754260455, "ap": -1691230952,
        "fnvs": 689752963, "hf": 1144953, "hfip": 50234, "tianl": 149768895,
        "java": -1094917604, "fnv": 3336909233, "add": 15,
    },
}  # fmt: skip


def test_algorithms_match_knifer_go() -> None:
    for s, want in _EXPECTED.items():
        assert vhash.rs_hash(s) == want["rs"], s
        assert vhash.js_hash(s) == want["js"], s
        assert vhash.pjw_hash(s) == want["pjw"], s
        assert vhash.elf_hash(s) == want["elf"], s
        assert vhash.bkdr_hash(s) == want["bkdr"], s
        assert vhash.sdbm_hash(s) == want["sdbm"], s
        assert vhash.djb_hash(s) == want["djb"], s
        assert vhash.ap_hash(s) == want["ap"], s
        assert vhash.fnv_hash_string(s) == want["fnvs"], s
        assert vhash.hf_hash(s) == want["hf"], s
        assert vhash.hf_ip_hash(s) == want["hfip"], s
        assert vhash.tianl_hash(s) == want["tianl"], s
        assert vhash.java_default_hash(s) == want["java"], s
        assert vhash.fnv_hash(s) == want["fnv"], s
        assert vhash.additive_hash(s, 31) == want["add"], s


def test_masked_hashes_non_negative() -> None:
    s = "knifer-go"
    assert vhash.rs_hash(s) >= 0
    assert vhash.js_hash(s) >= 0
    assert vhash.pjw_hash(s) >= 0
    assert vhash.elf_hash(s) >= 0
    assert vhash.bkdr_hash(s) >= 0
    assert vhash.sdbm_hash(s) >= 0
    assert vhash.djb_hash(s) >= 0
    assert vhash.fnv_hash_string(s) >= 0


def test_edge_cases() -> None:
    assert vhash.java_default_hash("a") == 97
    assert vhash.tianl_hash("") == 0
    assert vhash.tianl_hash("abc") > 0
    assert vhash.additive_hash("abc", 0) == vhash.additive_hash("abc", 31)
    assert vhash.fnv_hash("abc") != 0
