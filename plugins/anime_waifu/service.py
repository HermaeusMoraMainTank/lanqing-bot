# -*- coding: utf-8 -*-
"""今日二次元老婆，移植自 NcatBot/plugins/TodayAnimeWaifu"""
from __future__ import annotations

import io
import os
import random
from datetime import date
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage, ImageDraw

from bot.config import get_admin_openids, get_anime_waifu_dir, load_config
from bot.utils.group_track import get_group_tracker
from bot.utils.pil_helpers import load_ncatbot_font, truncate_line
from bot.utils.temp_image import save_temp_png

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
PREFERRED_WAIFU_DIR = "img1"
PREFERRED_DIR_CHANCE = 0.30
HMMT_WAIFU_DIR = "img3"

TRIGGER_COMMANDS = {
    "今日二次元老婆", "今日二刺猿老婆", "今日二刺螈老婆",
    "今日2次元老婆", "今日二次元", "今日二刺猿", "今日二刺螈",
}

allocated_by_group: dict[str, set[str]] = {}
user_to_waifu_by_group: dict[str, dict[str, dict]] = {}
_last_reset = date.today()
_images_by_dir: dict[str, list[str]] = {}


def _base_dir() -> Path:
    return get_anime_waifu_dir(load_config())


def _load_images() -> dict[str, list[str]]:
    base = _base_dir()
    result: dict[str, list[str]] = {}
    if not base.is_dir():
        return result
    for name in sorted(os.listdir(base)):
        path = base / name
        if path.is_dir() and not name.startswith("."):
            files = [f for f in os.listdir(path) if f.lower().endswith(IMAGE_EXTS)]
            if files:
                result[name] = files
    return result


def _ensure_loaded() -> None:
    global _images_by_dir
    if not _images_by_dir:
        _images_by_dir = _load_images()


def _reset_if_new_day() -> None:
    global _last_reset, _images_by_dir
    today = date.today()
    if today != _last_reset:
        allocated_by_group.clear()
        user_to_waifu_by_group.clear()
        _images_by_dir = _load_images()
        _last_reset = today


def _slot(directory: str, filename: str) -> str:
    return f"{directory}/{filename}"


def _waifu_path(directory: str, filename: str) -> Path:
    return _base_dir() / directory / filename


def _available(group_id: str, *, include_dirs: list[str] | None = None) -> list[tuple[str, str]]:
    allocated = allocated_by_group.setdefault(group_id, set())
    candidates: list[tuple[str, str]] = []
    for directory, filenames in _images_by_dir.items():
        if include_dirs is not None and directory not in include_dirs:
            continue
        for filename in filenames:
            slot = _slot(directory, filename)
            if slot not in allocated and _waifu_path(directory, filename).is_file():
                candidates.append((directory, filename))
    return candidates


def _pick_random(group_id: str, candidates: list[tuple[str, str]]) -> Optional[dict]:
    if not candidates:
        total = sum(len(v) for v in _images_by_dir.values())
        if total and len(allocated_by_group.get(group_id, set())) >= total:
            allocated_by_group[group_id].clear()
        candidates = _available(group_id)
    if not candidates:
        return None
    directory, filename = random.choice(candidates)
    data = {"directory": directory, "filename": filename}
    allocated_by_group.setdefault(group_id, set()).add(_slot(directory, filename))
    return data


def get_random_waifu(group_id: str, user_key: str) -> Optional[dict]:
    _ensure_loaded()
    if not _images_by_dir:
        return None
    preferred_dir = (
        HMMT_WAIFU_DIR if user_key in get_admin_openids(load_config()) else PREFERRED_WAIFU_DIR
    )
    preferred = _available(group_id, include_dirs=[preferred_dir])
    others = _available(group_id, include_dirs=[d for d in _images_by_dir if d != preferred_dir])
    if random.random() < PREFERRED_DIR_CHANCE:
        pool = preferred if preferred else others
    else:
        pool = others if others else preferred
    return _pick_random(group_id, pool)


def waifu_name(filename: str) -> str:
    return os.path.splitext(filename)[0]


def render_waifu_list(pairs: list[tuple[str, str, str]]) -> Path:
    """NcatBot TodayAnimeWaifu._generate_waifu_list_image 同款。"""
    width, padding, row_height, title_height = 920, 28, 42, 56
    height = padding * 2 + title_height + len(pairs) * row_height + 16
    img = PILImage.new("RGB", (width, height), color=(255, 248, 252))
    draw = ImageDraw.Draw(img)
    title_font = load_ncatbot_font("sakura.ttf", 28)
    text_font = load_ncatbot_font("sakura.ttf", 20)
    meta_font = load_ncatbot_font("sakura.ttf", 15)

    y = padding
    title = "今日群二次元老婆列表"
    tw = draw.textbbox((0, 0), title, font=title_font)[2]
    draw.text(((width - tw) // 2, y), title, font=title_font, fill=(180, 120, 220))
    y += title_height - 8
    draw.line([(padding, y), (width - padding, y)], fill=(230, 220, 240), width=2)
    y += 16

    inner_width = width - padding * 2
    for user_name, user_id, waifu_name_text in pairs:
        left = f"{user_name}（{user_id}）"
        line = truncate_line(draw, f"{left} →→→ {waifu_name_text}", text_font, inner_width)
        draw.text((padding, y), line, font=text_font, fill=(51, 58, 72))
        y += row_height

    footer = f"共 {len(pairs)} 人"
    fw = draw.textbbox((0, 0), footer, font=meta_font)[2]
    draw.text((width - padding - fw, y - 6), footer, font=meta_font, fill=(126, 136, 156))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return save_temp_png(buf.getvalue(), prefix="anime_waifu_list_")


def _short_id(openid: str) -> str:
    return openid[-8:] if len(openid) > 10 else openid


def _assign_random_waifu(group_id: str, user_key: str, mapping: dict, *, map_key: str | None = None) -> tuple[dict, Path] | None:
    target_key = map_key if map_key is not None else user_key
    for _ in range(5):
        data = get_random_waifu(group_id, user_key)
        if not data:
            return None
        path = _waifu_path(data["directory"], data["filename"])
        if path.is_file():
            mapping[target_key] = data
            return data, path
        allocated_by_group.get(group_id, set()).discard(_slot(data["directory"], data["filename"]))
    return None


def draw_waifu(group_id: str, user_key: str) -> tuple[str, Optional[Path]]:
    _reset_if_new_day()
    _ensure_loaded()
    mapping = user_to_waifu_by_group.setdefault(group_id, {})

    if user_key in mapping:
        data = mapping[user_key]
        path = _waifu_path(data["directory"], data["filename"])
        if path.is_file():
            return f"你今天的二次元老婆是：{waifu_name(data['filename'])}", path
        allocated_by_group.get(group_id, set()).discard(_slot(data["directory"], data["filename"]))
        mapping.pop(user_key, None)

    assigned = _assign_random_waifu(group_id, user_key, mapping)
    if not assigned:
        return "获取二次元老婆失败，请检查图片目录或稍后再试。", None
    data, path = assigned
    return f"你今天的二次元老婆是：{waifu_name(data['filename'])}", path


def build_list(group_id: str) -> tuple[str, Optional[Path]]:
    _reset_if_new_day()
    tracker = get_group_tracker()
    mapping = user_to_waifu_by_group.get(group_id, {})
    if not mapping:
        return "今日还没有人抽到二次元老婆哦~", None
    pairs = [
        (tracker.display_name(group_id, uid), _short_id(uid), waifu_name(d["filename"]))
        for uid, d in mapping.items()
    ]
    pairs.sort(key=lambda x: x[1])
    return "今日群二次元老婆列表", render_waifu_list(pairs)
