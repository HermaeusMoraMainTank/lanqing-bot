# -*- coding: utf-8 -*-
"""PIL 绘图公共工具（对齐 NcatBot 样式）。"""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image as PILImage, ImageDraw, ImageFont

from bot.config import get_ncatbot_data_dir, load_config

_FONT_REGULAR = (
    Path(r"C:/Windows/Fonts/msyh.ttc"),
    Path(r"C:/Windows/Fonts/simhei.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
)

_FONT_BOLD = (
    Path(r"C:/Windows/Fonts/msyhbd.ttc"),
    Path(r"C:/Windows/Fonts/msyh.ttc"),
    Path(r"C:/Windows/Fonts/simhei.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
)


def load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = _FONT_BOLD if bold else _FONT_REGULAR
    for path in candidates:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def load_ncatbot_font(filename: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    root = get_ncatbot_data_dir(load_config())
    path = root / "font" / filename
    if path.is_file():
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            pass
    return load_font(size)


def text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    return int(draw.textbbox((0, 0), text, font=font)[2])


def fit_text(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> str:
    if text_width(draw, text, font) <= max_w:
        return text
    trimmed = text
    while trimmed and text_width(draw, trimmed + "…", font) > max_w:
        trimmed = trimmed[:-1]
    return (trimmed + "…") if trimmed else "…"


def truncate_line(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    if not text:
        return text
    if text_width(draw, text, font) <= max_width:
        return text
    ellipsis = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        probe = text[:mid] + ellipsis
        if text_width(draw, probe, font) <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ellipsis if lo > 0 else ellipsis


def placeholder_avatar(openid: str, size: int = 48) -> PILImage.Image:
    """无 QQ 头像 API 时的圆形占位图（按 openid 着色）。"""
    digest = hashlib.md5(openid.encode()).digest()
    color = tuple(120 + b % 100 for b in digest[:3])
    img = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size - 1, size - 1), fill=color + (255,))
    label = openid[-2:].upper() if openid else "?"
    font = load_font(max(12, size // 3), bold=True)
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) // 2, (size - th) // 2 - 1), label, font=font, fill=(255, 255, 255))
    return img
