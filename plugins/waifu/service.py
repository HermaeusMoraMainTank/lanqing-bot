# -*- coding: utf-8 -*-
"""今日老婆逻辑，移植自 NcatBot/plugins/TodayWaifu（适配官方 Bot openid）"""
from __future__ import annotations

import io
import random
from datetime import date
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage, ImageDraw

from bot.utils.group_track import get_group_tracker
from bot.utils.avatar import load_avatar
from bot.utils.pil_helpers import load_ncatbot_font, truncate_line
from bot.utils.temp_image import save_temp_png

allocated_by_group: dict[str, set[str]] = {}
user_to_wife_by_group: dict[str, dict[str, str]] = {}
_last_reset = date.today()


def _short_id(openid: str) -> str:
    return openid[-8:] if len(openid) > 10 else openid


def _reset_if_new_day() -> None:
    global _last_reset
    today = date.today()
    if today != _last_reset:
        allocated_by_group.clear()
        user_to_wife_by_group.clear()
        _last_reset = today


def render_wife_list(pairs: list[tuple[str, str, str, str]]) -> Path:
    """NcatBot TodayWaifu._generate_wife_list_image 同款。"""
    width, padding, row_height, title_height = 920, 28, 42, 56
    height = padding * 2 + title_height + len(pairs) * row_height + 16
    img = PILImage.new("RGB", (width, height), color=(248, 250, 255))
    draw = ImageDraw.Draw(img)
    title_font = load_ncatbot_font("sakura.ttf", 28)
    text_font = load_ncatbot_font("sakura.ttf", 20)
    meta_font = load_ncatbot_font("sakura.ttf", 15)

    y = padding
    title = "今日群老婆列表"
    tw = draw.textbbox((0, 0), title, font=title_font)[2]
    draw.text(((width - tw) // 2, y), title, font=title_font, fill=(255, 120, 160))
    y += title_height - 8
    draw.line([(padding, y), (width - padding, y)], fill=(220, 225, 235), width=2)
    y += 16

    inner_width = width - padding * 2
    for user_name, user_id, wife_name, wife_id in pairs:
        left = f"{user_name}（{user_id}）"
        line = truncate_line(draw, f"{left} →→→ {wife_name}（{wife_id}）", text_font, inner_width)
        draw.text((padding, y), line, font=text_font, fill=(51, 58, 72))
        y += row_height

    footer = f"共 {len(pairs)} 对"
    fw = draw.textbbox((0, 0), footer, font=meta_font)[2]
    draw.text((width - padding - fw, y - 6), footer, font=meta_font, fill=(126, 136, 156))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return save_temp_png(buf.getvalue(), prefix="waifu_list_")


def pick_wife(group_openid: str, user_key: str) -> tuple[str, Optional[Path]]:
    _reset_if_new_day()
    tracker = get_group_tracker()
    allocated = allocated_by_group.setdefault(group_openid, set())
    mapping = user_to_wife_by_group.setdefault(group_openid, {})

    rv = random.random()
    if rv < 0.05:
        return "你快醒醒 你没有老婆", None
    if 0.05 <= rv <= 0.15:
        return "今*老婆", None

    if user_key in mapping:
        wife_id = mapping[user_key]
        wife_name = tracker.display_name(group_openid, wife_id)
        avatar = load_avatar(wife_id, 200, circular=False)
        return f"你今天的群友老婆是：{wife_name}（{_short_id(wife_id)}）", save_temp_png(_pil_to_bytes(avatar), prefix="waifu_avatar_")

    pool = tracker.others(group_openid, exclude={user_key}, allocated=allocated)
    if len(pool) < 2:
        return (
            "群里互动的人还不够多，没法随机分配老婆～\n"
            "请让更多群友 @机器人 发消息后再试。",
            None,
        )

    wife_id = random.choice(pool)
    mapping[user_key] = wife_id
    allocated.add(wife_id)
    wife_name = tracker.display_name(group_openid, wife_id)
    avatar = load_avatar(wife_id, 200, circular=False)
    return f"你今天的群友老婆是：{wife_name}（{_short_id(wife_id)}）", save_temp_png(_pil_to_bytes(avatar), prefix="waifu_avatar_")


def build_list(group_openid: str) -> tuple[str, Optional[Path]]:
    _reset_if_new_day()
    tracker = get_group_tracker()
    mapping = user_to_wife_by_group.get(group_openid, {})
    if not mapping:
        return "今日还没有人抽到老婆哦~", None
    pairs = []
    for uid, wid in mapping.items():
        pairs.append((
            tracker.display_name(group_openid, uid),
            _short_id(uid),
            tracker.display_name(group_openid, wid),
            _short_id(wid),
        ))
    pairs.sort(key=lambda x: x[1])
    return "今日群老婆列表", render_wife_list(pairs)


def _pil_to_bytes(img: PILImage.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
