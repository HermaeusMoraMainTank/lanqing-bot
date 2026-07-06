# -*- coding: utf-8 -*-
import hashlib
from datetime import date


def current_day_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def bytes_to_long(data: bytes) -> int:
    return int.from_bytes(data, byteorder="big")


def daily_hash_value(user_key: str, *extra: str) -> int:
    digest = hashlib.sha256()
    digest.update(user_key.encode())
    for part in extra:
        digest.update(part.encode())
    return abs(bytes_to_long(digest.digest()))
