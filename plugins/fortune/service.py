# -*- coding: utf-8 -*-
"""今日运势逻辑，移植自 NcatBot/plugins/Fortune/Fortune.py"""
from __future__ import annotations

import hashlib
import json
import os
import random
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage, ImageDraw, ImageFont

from bot.config import get_ncatbot_data_dir, load_config

LUCK_DESC_LIST = [
    "amazing_grace", "arknights", "asoul", "azure", "dc4", "einstein", "genshin",
    "hoshizora", "liqingge", "onmyoji", "pcr", "pretty_derby", "punishing", "sakura",
    "summer_pockets", "sweet_illusion", "touhou", "touhou_lostword", "touhou_old",
    "warship_girls_r",
]

_last_invocation: dict[str, date] = {}
_last_reset = date.today()


class FortuneService:
    def __init__(self) -> None:
        self.root = get_ncatbot_data_dir(load_config())

    def _path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    @staticmethod
    def _luck_value(user_key: str) -> int:
        digest = hashlib.sha256()
        digest.update(user_key.encode())
        digest.update(str(date.today()).encode())
        digest.update(b"42")
        return abs(int.from_bytes(digest.digest(), byteorder="big")) % 6

    def pick_amm_image(self, user_key: str) -> Optional[Path]:
        folder = self._path("image", "amm")
        if not folder.is_dir():
            return None
        files = os.listdir(folder)
        if not files:
            return None
        return folder / files[self._luck_value(user_key) % len(files)]

    def pick_doro_image(self, user_key: str) -> Optional[Path]:
        folder = self._path("image", "doro结局")
        if not folder.is_dir():
            return None
        files = os.listdir(folder)
        if not files:
            return None
        return folder / files[self._luck_value(user_key) % len(files)]

    def draw_fortune_image(self) -> Path:
        font_title = self._path("font", "Mamelon.otf")
        font_text = self._path("font", "sakura.ttf")
        luck_desc = random.choice(LUCK_DESC_LIST)
        base_dir = self._path("image", "fortune", luck_desc)
        files = os.listdir(base_dir) if base_dir.is_dir() else []
        base_path = base_dir / random.choice(files) if files else None
        if not base_path or not base_path.exists():
            raise FileNotFoundError(f"运势背景不存在: {base_dir}")

        img = PILImage.open(base_path)
        draw = ImageDraw.Draw(img)
        title, content = self._luck_info()
        self._draw_text(draw, title, str(font_title))
        lines = self._split_content(content)
        if lines:
            self._draw_vertical_text(draw, lines, str(font_text))

        fd, name = tempfile.mkstemp(suffix=".png", prefix="fortune_")
        out = Path(name)
        with open(fd, "wb"):
            pass
        img.save(out)
        return out

    def _luck_info(self) -> tuple[str, str]:
        path = self._path("json", "copywriting.json")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        copywriting = random.choice(data["copywriting"])
        return copywriting["good-luck"], random.choice(copywriting["content"])

    @staticmethod
    def _draw_text(draw: ImageDraw.Draw, text: str, font_path: str) -> None:
        font = ImageFont.truetype(font_path, 45)
        text_width = draw.textlength(text, font=font)
        draw.text((140 - text_width / 2, 80), text, font=font, fill="#F5F5F5")

    @staticmethod
    def _draw_vertical_text(draw: ImageDraw.Draw, text_lines: list[str], font_path: str) -> None:
        font = ImageFont.truetype(font_path, 25)
        for i, line in enumerate(text_lines):
            font_height = len(line) * (25 + 4)
            draw_x = (
                140
                + (len(text_lines) - 2) * 25 / 2
                + (len(text_lines) - 1) * 4
                - i * (25 + 4)
            )
            draw_y = 300 - font_height / 2
            for j, char in enumerate(line):
                draw.text((draw_x, draw_y + j * 25), char, font=font, fill="#323232")

    @staticmethod
    def _split_content(text: str) -> list[str]:
        length = len(text)
        cardinality = 9
        if length > 4 * cardinality:
            raise ValueError("Text is too long")
        col_num = 1
        while length > cardinality:
            col_num += 1
            length -= cardinality
        result: list[str] = []
        if col_num == 2:
            if len(text) % 2 == 0:
                result = [text[: len(text) // 2], text[len(text) // 2 :]]
            else:
                mid = (len(text) + 1) // 2
                result = [text[:mid], " " + text[mid:]]
        else:
            for i in range(col_num):
                start = i * cardinality
                end = (i + 1) * cardinality if i < col_num - 1 else None
                result.append(text[start:end])
        return result

    def today_fortune(self, user_key: str) -> tuple[str, Optional[Path]]:
        global _last_reset, _last_invocation
        today = date.today()
        if today != _last_reset:
            _last_reset = today
            _last_invocation.clear()
        if _last_invocation.get(user_key) == today:
            return "你今天已经获取过运势了，请明天再来吧。", None
        try:
            img = self.draw_fortune_image()
            _last_invocation[user_key] = today
            return "✨今日运势✨", img
        except (OSError, ValueError, KeyError) as exc:
            return f"生成运势失败：{exc}", None


_service: Optional[FortuneService] = None


def get_service() -> FortuneService:
    global _service
    if _service is None:
        _service = FortuneService()
    return _service
