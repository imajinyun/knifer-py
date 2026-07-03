"""Form validation utilities.

Ports knifer-go's vform/validator surface with Python-idiomatic mappings.

Supports:
- Email, mobile, URL, IPv4, IPv6, ID card, Chinese, and number string validation
- WithOptions variants for custom matchers
- With*Matcher options for per-call customization
"""
from __future__ import annotations

from kniferpy.internal.formx import (
    is_email,
    is_email_with_options,
    is_mobile,
    is_mobile_with_options,
    is_url,
    is_ipv4,
    is_ipv6,
    is_id_card,
    is_id_card_with_options,
    is_chinese,
    is_chinese_with_options,
    is_number_str,
    is_number_str_with_options,
    with_email_matcher,
    with_mobile_matcher,
    with_id_card_matcher,
    with_chinese_matcher,
    with_number_matcher,
)

__all__ = [
    "is_email",
    "is_email_with_options",
    "is_mobile",
    "is_mobile_with_options",
    "is_url",
    "is_ipv4",
    "is_ipv6",
    "is_id_card",
    "is_id_card_with_options",
    "is_chinese",
    "is_chinese_with_options",
    "is_number_str",
    "is_number_str_with_options",
    "with_email_matcher",
    "with_mobile_matcher",
    "with_id_card_matcher",
    "with_chinese_matcher",
    "with_number_matcher",
]