from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import IntEnum

from kniferpy.verr import ValidationError

CHINA_ID_MIN_LENGTH = 15
CHINA_ID_MAX_LENGTH = 18

_ID_CARD_POWER = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
_CHECK_CODES = "10X98765432"

_CITY_CODES = {
    "11": "北京",
    "12": "天津",
    "13": "河北",
    "14": "山西",
    "15": "内蒙古",
    "21": "辽宁",
    "22": "吉林",
    "23": "黑龙江",
    "31": "上海",
    "32": "江苏",
    "33": "浙江",
    "34": "安徽",
    "35": "福建",
    "36": "江西",
    "37": "山东",
    "41": "河南",
    "42": "湖北",
    "43": "湖南",
    "44": "广东",
    "45": "广西",
    "46": "海南",
    "50": "重庆",
    "51": "四川",
    "52": "贵州",
    "53": "云南",
    "54": "西藏",
    "61": "陕西",
    "62": "甘肃",
    "63": "青海",
    "64": "宁夏",
    "65": "新疆",
    "71": "台湾",
    "81": "香港",
    "82": "澳门",
    "83": "台湾",
    "91": "国外",
}

_TW_FIRST_CODE = {
    "A": 10, "B": 11, "C": 12, "D": 13, "E": 14, "F": 15, "G": 16, "H": 17,
    "J": 18, "K": 19, "L": 20, "M": 21, "N": 22, "P": 23, "Q": 24, "R": 25,
    "S": 26, "T": 27, "U": 28, "V": 29, "X": 30, "Y": 31, "W": 32, "Z": 33,
    "I": 34, "O": 35,
}  # fmt: skip

_RX_DIGITS = re.compile(r"^\d+$")
_RX_TW_CARD = re.compile(r"^[a-zA-Z][0-9]{9}$")
_RX_MACAU_ID = re.compile(r"^[157][0-9]{6}\(?[0-9A-Z]\)?$")
_RX_HK_ID = re.compile(r"^[A-Z]{1,2}[0-9]{6}\(?[0-9A]\)?$")

_CREDIT_CODE_LENGTH = 18
_CREDIT_CODE_CHARSET = "0123456789ABCDEFGHJKLMNPQRTUWXY"
_CREDIT_CODE_WEIGHTS = (1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28)


class Gender(IntEnum):
    UNKNOWN = -1
    FEMALE = 0
    MALE = 1


@dataclass(slots=True, frozen=True)
class IDCardInfo:
    province_code: str
    province: str
    city_code: str
    district_code: str
    birth: date
    gender: Gender
    age: int


@dataclass(slots=True, frozen=True)
class RegionCardInfo:
    region: str
    gender: str
    valid: bool


@dataclass(slots=True, frozen=True)
class CreditCodeInfo:
    raw: str
    admin_dept: str
    org_category: str
    region_code: str
    org_code: str
    check_digit: str


def _is_digits(value: str) -> bool:
    return _RX_DIGITS.match(value) is not None


def check_code18(code17: str) -> str:
    if len(code17) != len(_ID_CARD_POWER) or not _is_digits(code17):
        return " "
    total = sum(int(code17[i]) * _ID_CARD_POWER[i] for i in range(len(code17)))
    return _CHECK_CODES[total % 11]


def is_valid_birthday(s: str) -> bool:
    if len(s) != 8 or not _is_digits(s):
        return False
    try:
        parsed = datetime.strptime(s, "%Y%m%d")
    except ValueError:
        return False
    return parsed.strftime("%Y%m%d") == s


def convert_15_to_18(id_card: str) -> str | None:
    if len(id_card) != CHINA_ID_MIN_LENGTH or not _is_digits(id_card):
        return None
    id18 = id_card[:6] + "19" + id_card[6:]
    return id18 + check_code18(id18[:17])


def convert_18_to_15(id_card: str) -> str | None:
    if not is_valid_id_card18(id_card):
        return None
    return id_card[:6] + id_card[8:17]


def is_valid_id_card18(id_card: str, ignore_case: bool = True) -> bool:
    if len(id_card) != CHINA_ID_MAX_LENGTH:
        return False
    province_code = id_card[1:3] if id_card.startswith("9") else id_card[:2]
    if province_code not in _CITY_CODES:
        return False
    if not is_valid_birthday(id_card[6:14]):
        return False
    code17 = id_card[:17]
    if not _is_digits(code17):
        return False
    check = check_code18(code17)
    actual = id_card[17]
    if ignore_case:
        return check.upper() == actual.upper()
    return check == actual


def is_valid_id_card15(id_card: str) -> bool:
    if len(id_card) != CHINA_ID_MIN_LENGTH or not _is_digits(id_card):
        return False
    if id_card[:2] not in _CITY_CODES:
        return False
    return is_valid_birthday("19" + id_card[6:12])


def is_valid_tw_id_card(id_card: str) -> bool:
    if _RX_TW_CARD.match(id_card) is None or len(id_card) != 10:
        return False
    start = _TW_FIRST_CODE.get(id_card[0].upper())
    if start is None:
        return False
    total = start // 10 + (start % 10) * 9
    weight = 8
    for i in range(1, 9):
        if not id_card[i].isdigit():
            return False
        total += int(id_card[i]) * weight
        weight -= 1
    if not id_card[9].isdigit():
        return False
    check = 0
    mod = total % 10
    if mod != 0:
        check = 10 - mod
    return check == int(id_card[9])


def is_valid_hk_id_card(id_card: str) -> bool:
    if _RX_HK_ID.match(id_card) is None:
        return False
    card = id_card.replace("(", "").replace(")", "")
    if len(card) == 9:
        total = (ord(card[0]) - 55) * 9 + (ord(card[1]) - 55) * 8
        card = card[1:]
    else:
        total = 522 + (ord(card[0]) - 55) * 8
    weight = 7
    for i in range(1, 7):
        if not card[i].isdigit():
            return False
        total += int(card[i]) * weight
        weight -= 1
    end = card[7]
    if end in ("A", "a"):
        total += 10
    elif end.isdigit():
        total += int(end)
    else:
        return False
    return total % 11 == 0


def parse_region_card(id_card: str) -> RegionCardInfo | None:
    if id_card.strip() == "":
        return None
    normalized = id_card.replace("（", "(").replace("）", ")")
    card = normalized.replace("(", "").replace(")", "")
    if len(card) != 8 and len(card) != 9 and len(normalized) != 10:
        return None
    if _RX_TW_CARD.match(normalized) is not None:
        second = normalized[1]
        if second == "1":
            gender = "M"
        elif second == "2":
            gender = "F"
        else:
            return RegionCardInfo(region="台湾", gender="N", valid=False)
        return RegionCardInfo(region="台湾", gender=gender, valid=is_valid_tw_id_card(normalized))
    if _RX_MACAU_ID.match(normalized) is not None:
        return RegionCardInfo(region="澳门", gender="N", valid=True)
    if _RX_HK_ID.match(normalized) is not None:
        return RegionCardInfo(region="香港", gender="N", valid=is_valid_hk_id_card(normalized))
    return None


def is_valid_id_card(id_card: str) -> bool:
    if id_card.strip() == "":
        return False
    length = len(id_card)
    if length == CHINA_ID_MAX_LENGTH:
        return is_valid_id_card18(id_card)
    if length == CHINA_ID_MIN_LENGTH:
        return is_valid_id_card15(id_card)
    if length == 10:
        info = parse_region_card(id_card)
        return info is not None and info.valid
    return False


def _normalized_18(id_card: str) -> str | None:
    if len(id_card) == CHINA_ID_MIN_LENGTH:
        return convert_15_to_18(id_card)
    if len(id_card) == CHINA_ID_MAX_LENGTH:
        return id_card
    return None


def birth_string(id_card: str) -> str | None:
    normalized = _normalized_18(id_card)
    if normalized is None:
        return None
    birth = normalized[6:14]
    return birth if is_valid_birthday(birth) else None


def birth_date(id_card: str) -> date | None:
    birth = birth_string(id_card)
    if birth is None:
        return None
    try:
        return datetime.strptime(birth, "%Y%m%d").date()
    except ValueError:
        return None


def age_at(id_card: str, at: date) -> int | None:
    birth = birth_date(id_card)
    if birth is None:
        return None
    age = at.year - birth.year
    if (at.month, at.day) < (birth.month, birth.day):
        age -= 1
    return age


def age(id_card: str) -> int | None:
    return age_at(id_card, date.today())


def year(id_card: str) -> int | None:
    birth = birth_string(id_card)
    return int(birth[0:4]) if birth is not None else None


def month(id_card: str) -> int | None:
    birth = birth_string(id_card)
    return int(birth[4:6]) if birth is not None else None


def day(id_card: str) -> int | None:
    birth = birth_string(id_card)
    return int(birth[6:8]) if birth is not None else None


def gender_of(id_card: str) -> Gender | None:
    normalized = _normalized_18(id_card)
    if normalized is None:
        return None
    seq = normalized[16]
    if not seq.isdigit():
        return None
    return Gender.MALE if int(seq) % 2 != 0 else Gender.FEMALE


def province_code(id_card: str) -> str | None:
    if len(id_card) in (CHINA_ID_MIN_LENGTH, CHINA_ID_MAX_LENGTH):
        return id_card[:2]
    return None


def province(id_card: str) -> str | None:
    code = province_code(id_card)
    if code is None:
        return None
    return _CITY_CODES.get(code)


def city_code(id_card: str) -> str | None:
    if len(id_card) in (CHINA_ID_MIN_LENGTH, CHINA_ID_MAX_LENGTH):
        return id_card[:4]
    return None


def district_code(id_card: str) -> str | None:
    if len(id_card) in (CHINA_ID_MIN_LENGTH, CHINA_ID_MAX_LENGTH):
        return id_card[:6]
    return None


def parse_id_card(id_card: str) -> IDCardInfo | None:
    if not is_valid_id_card18(id_card) and not is_valid_id_card15(id_card):
        return None
    birth = birth_date(id_card)
    gender = gender_of(id_card)
    card_age = age(id_card)
    if birth is None or gender is None or card_age is None:
        return None
    return IDCardInfo(
        province_code=province_code(id_card) or "",
        province=province(id_card) or "",
        city_code=city_code(id_card) or "",
        district_code=district_code(id_card) or "",
        birth=birth,
        gender=gender,
        age=card_age,
    )


def hide(id_card: str, start: int, end: int) -> str:
    chars = list(id_card)
    start = max(start, 0)
    end = min(end, len(chars))
    if start >= end:
        return id_card
    for i in range(start, end):
        chars[i] = "*"
    return "".join(chars)


def is_valid_credit_code(code: str) -> bool:
    try:
        parse_credit_code(code)
    except ValidationError:
        return False
    return True


def parse_credit_code(code: str) -> CreditCodeInfo:
    normalized = code.strip().upper()
    if len(normalized) != _CREDIT_CODE_LENGTH:
        raise ValidationError(
            message="credit code length must be 18",
            code="knifer.ident.credit_code_length",
            context={"value": code},
        )
    total = 0
    for i in range(_CREDIT_CODE_LENGTH - 1):
        idx = _CREDIT_CODE_CHARSET.find(normalized[i])
        if idx < 0:
            raise ValidationError(
                message="credit code contains unsupported character",
                code="knifer.ident.credit_code_charset",
                context={"value": code},
            )
        total += idx * _CREDIT_CODE_WEIGHTS[i]
    if _CREDIT_CODE_CHARSET.find(normalized[-1]) < 0:
        raise ValidationError(
            message="credit code contains unsupported character",
            code="knifer.ident.credit_code_charset",
            context={"value": code},
        )
    check = 31 - total % 31
    if check == 31:
        check = 0
    if normalized[-1] != _CREDIT_CODE_CHARSET[check]:
        raise ValidationError(
            message="credit code check digit mismatch",
            code="knifer.ident.credit_code_check",
            context={"value": code},
        )
    return CreditCodeInfo(
        raw=normalized,
        admin_dept=normalized[:1],
        org_category=normalized[1:2],
        region_code=normalized[2:8],
        org_code=normalized[8:17],
        check_digit=normalized[17:],
    )
