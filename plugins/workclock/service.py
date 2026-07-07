# -*- coding: utf-8 -*-
"""上下班打卡，完整移植 NcatBot/plugins/WorkClock 卡片渲染与业务逻辑。"""
from __future__ import annotations

import io
import json
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage, ImageDraw

from bot.utils.group_track import get_group_tracker
from bot.utils.avatar import load_avatar
from bot.utils.pil_helpers import fit_text, load_font, text_width
from bot.utils.temp_image import save_temp_png

PLUGIN_DIR = Path(__file__).resolve().parent
DATA_PATH = PLUGIN_DIR / "data" / "data.json"

_CLOCK_IN = ("群上班", "打卡", "补卡", "上班")
_CLOCK_OUT = ("群下班", "下班")
_MIN_SHIFT = 6 * 3600
_MAX_SHIFT = 18 * 3600

_CARD_THEMES = {
    "in": {"accent": (255, 106, 48), "text": (48, 48, 56), "muted": (120, 108, 100)},
    "in_dup": {"accent": (130, 140, 160), "text": (48, 48, 56), "muted": (110, 118, 132)},
    "in_early": {"accent": (230, 120, 50), "text": (48, 48, 56), "muted": (120, 108, 100)},
    "out": {"accent": (58, 92, 180), "text": (48, 48, 56), "muted": (100, 110, 130)},
    "warn": {"accent": (200, 70, 60), "text": (48, 48, 56), "muted": (130, 100, 100)},
}

_CN = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_PERIODS = (("凌晨", 0), ("早上", 0), ("上午", 0), ("中午", 0), ("午后", 12), ("下午", 12), ("晚间", 12), ("晚上", 12), ("晚", 12))


def _load_data() -> dict:
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text("utf-8"))
        except json.JSONDecodeError:
            pass
    return {"by_user": {}}


def _save_data(data: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


def _day_boundary() -> time:
    return time(4, 0)


def _work_date(dt: datetime | None = None) -> str:
    dt = dt or _now()
    d = dt.date()
    if dt.time() < _day_boundary():
        d -= timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def _short_date(work_date: str | None = None) -> str:
    if work_date:
        return datetime.strptime(work_date, "%Y-%m-%d").strftime("%m-%d")
    return _now().strftime("%m-%d")


def _forget_timeout() -> timedelta:
    return timedelta(hours=24)


def _is_forgotten(clock_in: datetime, now: datetime) -> bool:
    return now - clock_in >= _forget_timeout()


def _parse_dt(value: str) -> datetime:
    if "T" in value:
        return datetime.fromisoformat(value)
    return datetime.combine(date.today(), datetime.strptime(value, "%H:%M:%S").time())


def _fmt_display(value: str) -> str:
    return _parse_dt(value).strftime("%m-%d %H:%M")


def _fmt_list_time(value: str) -> str:
    return _parse_dt(value).strftime("%H:%M")


def _fmt_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    parts = []
    if h:
        parts.append(f"{h}小时")
    if m:
        parts.append(f"{m}分")
    if s or not parts:
        parts.append(f"{s}秒")
    return "".join(parts)


def _user_state(data: dict, uid: str) -> dict:
    return data.setdefault("by_user", {}).setdefault(uid, {})


def _open_shift(data: dict, uid: str) -> dict | None:
    shift = _user_state(data, uid).get("active")
    if isinstance(shift, dict) and shift.get("clock_in") and not shift.get("clock_out"):
        return shift
    return None


def _today_closed(data: dict, uid: str, now: datetime | None = None) -> dict | None:
    now = now or _now()
    closed = _user_state(data, uid).get("last_closed")
    if not isinstance(closed, dict):
        return None
    if not closed.get("clock_in") or not closed.get("clock_out"):
        return None
    if closed.get("work_date") != _work_date(now):
        return None
    return closed


def _shift_seconds(shift: dict) -> int:
    return max(0, int((_parse_dt(shift["clock_out"]) - _parse_dt(shift["clock_in"])).total_seconds()))


def _draw_divider(draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int, color: tuple) -> None:
    draw.line([(x1, y), (x2, y)], fill=color, width=1)


def _render_card(
    user_openid: str,
    nickname: str,
    kind: str,
    title: str,
    rows: list[tuple[str, str]],
    note: str | None = None,
    tail: str | None = None,
    work_date: str | None = None,
) -> Path:
    """NcatBot WorkClock._render_card 同款布局。"""
    theme = _CARD_THEMES.get(kind, _CARD_THEMES["in"])
    W, M, accent_w, pad_x = 500, 16, 5, 24
    card_x1 = M + accent_w
    content_left = card_x1 + pad_x
    content_right = W - M - pad_x
    content_w = content_right - content_left

    font_name = load_font(16)
    font_title = load_font(20, bold=True)
    font_date = load_font(15)
    font_label = load_font(17)
    font_value = load_font(22, bold=True)
    font_hero = load_font(36, bold=True)
    font_note = load_font(15)
    font_tail = load_font(16)

    avatar_size = 48
    header_h = 84
    row_h = 46
    if len(rows) == 1:
        body_h = 108
    elif rows:
        body_h = len(rows) * row_h + 20
    else:
        body_h = 40
    note_h = 26 if note else 0
    tail_h = 28 if tail else 0
    H = M + header_h + 1 + body_h + note_h + tail_h + 22 + M

    canvas = PILImage.new("RGB", (W, H), (240, 243, 248))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((M, M, W - M, H - M), radius=16, fill=(255, 255, 255), outline=(220, 226, 236))
    draw.rounded_rectangle((M, M, M + accent_w, H - M), radius=16, fill=theme["accent"])
    draw.rectangle((M + accent_w // 2, M, M + accent_w, H - M), fill=theme["accent"])

    avatar = load_avatar(user_openid, avatar_size, circular=True)
    avatar_y = M + (header_h - avatar_size) // 2
    canvas.paste(avatar, (content_left, avatar_y), avatar)

    text_x = content_left + avatar_size + 14
    date_text = _short_date(work_date)
    date_w = text_width(draw, date_text, font_date)
    date_x = content_right - date_w
    name_max_w = max(60, date_x - text_x - 12)
    nickname = fit_text(draw, nickname, font_name, name_max_w)
    title_fit = fit_text(draw, title, font_title, content_right - text_x)
    draw.text((text_x, M + 22), nickname, font=font_name, fill=theme["muted"])
    draw.text((date_x, M + 22), date_text, font=font_date, fill=theme["muted"])
    draw.text((text_x, M + 46), title_fit, font=font_title, fill=theme["text"])

    divider_y = M + header_h
    _draw_divider(draw, card_x1 + 12, divider_y, W - M - 12, (235, 239, 245))
    body_y = divider_y + 18

    if len(rows) == 1:
        label, value = rows[0]
        display = _fmt_display(value) if ("T" in value or ":" in value) else value
        display = fit_text(draw, display, font_hero, content_w)
        hero_w = text_width(draw, display, font_hero)
        draw.text((content_left + (content_w - hero_w) // 2, body_y + 8), display, font=font_hero, fill=theme["accent"])
        label_fit = fit_text(draw, label, font_label, content_w)
        label_w = text_width(draw, label_fit, font_label)
        draw.text((content_left + (content_w - label_w) // 2, body_y + 58), label_fit, font=font_label, fill=theme["muted"])
    elif rows:
        for i, (label, value) in enumerate(rows):
            y = body_y + i * row_h
            short = (
                label.replace("（最晚）", "")
                .replace("上班时间", "上班")
                .replace("下班时间", "下班")
                .replace("今日工时", "工时")
            )
            display = value if "工时" in label else _fmt_display(value)
            label_fit = fit_text(draw, short, font_label, content_w // 2)
            value_fit = fit_text(draw, display, font_value, content_w // 2)
            draw.text((content_left, y + 10), label_fit, font=font_label, fill=theme["muted"])
            val_w = text_width(draw, value_fit, font_value)
            draw.text((content_right - val_w, y + 8), value_fit, font=font_value, fill=theme["accent"])
            if i < len(rows) - 1:
                _draw_divider(draw, content_left, y + row_h - 4, content_right, (243, 246, 250))

    y = body_y + body_h
    if note:
        note_text = fit_text(draw, note, font_note, content_w)
        note_w = text_width(draw, note_text, font_note)
        draw.text((content_left + (content_w - note_w) // 2, y), note_text, font=font_note, fill=theme["muted"])
        y += note_h
    if tail:
        tail_text = fit_text(draw, tail, font_tail, content_w)
        tail_w = text_width(draw, tail_text, font_tail)
        draw.text((content_left + (content_w - tail_w) // 2, y), tail_text, font=font_tail, fill=theme["text"])

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return save_temp_png(buf.getvalue(), prefix="workclock_")


def _render_group_list(rows: list[tuple[str, str, bool, str, str | None, int]]) -> Path:
    theme = _CARD_THEMES["in"]
    width, padding, row_height, title_height = 980, 28, 42, 56
    height = padding * 2 + title_height + len(rows) * row_height + 16
    img = PILImage.new("RGB", (width, height), color=(255, 248, 242))
    draw = ImageDraw.Draw(img)
    title_font = load_font(28, bold=True)
    text_font = load_font(20)
    meta_font = load_font(15)
    inner_width = width - padding * 2

    y = padding
    title = "群上班列表"
    title_w = text_width(draw, title, title_font)
    draw.text(((width - title_w) // 2, y), title, font=title_font, fill=theme["accent"])
    y += title_height - 8
    draw.line([(padding, y), (width - padding, y)], fill=(220, 225, 235), width=2)
    y += 16

    active_count = 0
    for name, uid, is_active, clock_in, clock_out, duration_sec in rows:
        duration = _fmt_duration(duration_sec)
        left = f"{name}（{uid}）"
        if is_active:
            active_count += 1
            right = f"{_fmt_list_time(clock_in)} 上班中 · {duration}"
            color = theme["text"]
        else:
            right = f"{_fmt_list_time(clock_in)}-{_fmt_list_time(clock_out or clock_in)} 已下班 · {duration}"
            color = theme["muted"]
        line = fit_text(draw, f"{left} →→→ {right}", text_font, inner_width)
        draw.text((padding, y), line, font=text_font, fill=color)
        y += row_height

    closed_count = len(rows) - active_count
    if active_count and closed_count:
        footer = f"上班中 {active_count} 人 · 已下班 {closed_count} 人"
    elif active_count:
        footer = f"共 {active_count} 人在上班"
    else:
        footer = f"共 {closed_count} 人已下班"
    footer_w = text_width(draw, footer, meta_font)
    draw.text((width - padding - footer_w, y - 6), footer, font=meta_font, fill=theme["muted"])

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return save_temp_png(buf.getvalue(), prefix="workclock_list_")


def _normalize_time_text(text: str) -> str:
    text = text.strip()
    for fw, hw in zip("０１２３４５６７８９：．", "0123456789:."):
        text = text.replace(fw, hw)
    return re.sub(r"\s+", "", text)


def _parse_cn(s: str) -> int | None:
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + (_CN.get(s[1:], 0) if len(s) > 1 else 0)
    if "十" in s:
        i = s.index("十")
        tens = _CN.get(s[:i], 1) if s[:i] else 1
        ones = _CN.get(s[i + 1 :], 0) if s[i + 1 :] else 0
        return tens * 10 + ones
    return _CN.get(s)


def _build_time(hour: int, minute: int, period_add: int) -> time | None:
    if period_add and hour < 12:
        hour += period_add
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return time(hour, minute)
    return None


def _looks_like_time(text: str) -> bool:
    text = _normalize_time_text(text)
    if not text:
        return False
    if re.fullmatch(r"\d{1,2}", text):
        return True
    if re.search(r"[\d.:：．]", text):
        return True
    return any(x in text for x in ("点", "半", "整")) or any(text.startswith(p) for p, _ in _PERIODS)


def parse_clock_time(text: str) -> time | None:
    text = _normalize_time_text(text)
    if not text:
        return None
    period_add = 0
    for prefix, add in _PERIODS:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            period_add = add
            break
    text = text.removesuffix("钟").removesuffix("分")
    m = re.fullmatch(r"(\d{1,2})[:.](\d{2})", text)
    if m:
        return _build_time(int(m.group(1)), int(m.group(2)), period_add)
    m = re.fullmatch(r"(\d{1,2})点(?:(\d{1,2})|半|整)?", text)
    if m:
        hour = int(m.group(1))
        minute = 30 if "半" in text else (int(m.group(2)) if m.group(2) else 0)
        return _build_time(hour, minute, period_add)
    m = re.fullmatch(r"(\d{1,2})", text)
    if m:
        return _build_time(int(m.group(1)), 0, period_add)
    m = re.fullmatch(r"([零一二两三四五六七八九十]+)点(半|整|([零一二两三四五六七八九十]+))?", text)
    if m:
        hour = _parse_cn(m.group(1))
        if hour is None:
            return None
        minute = 30 if m.group(2) == "半" else (_parse_cn(m.group(3)) or 0 if m.group(3) else 0)
        return _build_time(hour, minute, period_add)
    return None


def _combine_manual(manual: time, now: datetime) -> datetime:
    candidates = [datetime.combine(now.date() + timedelta(days=o), manual) for o in (-1, 0, 1)]
    past = [dt for dt in candidates if dt <= now]
    return max(past) if past else min(candidates)


class WorkClockService:
    def handle(
        self,
        cmd: str,
        user_key: str,
        group_openid: str,
        nickname: str = "群友",
    ) -> tuple[str, Optional[Path]]:
        if cmd == "群上班列表":
            return self._group_list(group_openid)
        for trigger in _CLOCK_OUT:
            if cmd == trigger:
                return self._clock_out(user_key, nickname, None, manual_flag=False)
            if cmd.startswith(trigger):
                rest = cmd[len(trigger) :].strip()
                if rest and _looks_like_time(rest):
                    t = parse_clock_time(rest)
                    if t is None:
                        return "补卡时间无法识别", _render_card(
                            user_key, nickname, "warn", "补卡时间无法识别", [],
                            note="示例：下班 6点 / 下班 18:00",
                        )
                    return self._clock_out(user_key, nickname, t, manual_flag=True)
                if not rest:
                    return self._clock_out(user_key, nickname, None, manual_flag=False)
        for trigger in _CLOCK_IN:
            if cmd == trigger:
                return self._clock_in(user_key, nickname, None, manual_flag=False)
            if cmd.startswith(trigger):
                rest = cmd[len(trigger) :].strip()
                if rest and _looks_like_time(rest):
                    t = parse_clock_time(rest)
                    if t is None:
                        return "补卡时间无法识别", _render_card(
                            user_key, nickname, "warn", "补卡时间无法识别", [],
                            note="示例：补卡 9点 / 打卡 9:00 / 打卡 九点半",
                        )
                    return self._clock_in(user_key, nickname, t, manual_flag=True)
                if not rest:
                    return self._clock_in(user_key, nickname, None, manual_flag=False)
        return "未知指令", None

    def _clock_in(
        self, uid: str, nickname: str, manual: time | None, *, manual_flag: bool
    ) -> tuple[str, Optional[Path]]:
        data = _load_data()
        now = _now()
        clock_in = _combine_manual(manual, now) if manual else now
        shift = _open_shift(data, uid)
        auto_note: str | None = None

        if shift:
            existing = _parse_dt(shift["clock_in"])
            if _is_forgotten(existing, clock_in):
                end = (existing + _forget_timeout()).replace(second=0, microsecond=0)
                closed = dict(shift)
                closed["clock_out"] = end.isoformat(timespec="seconds")
                _user_state(data, uid)["last_closed"] = closed
                _user_state(data, uid).pop("active", None)
                hours = int(_forget_timeout().total_seconds() // 3600)
                auto_note = f"上一班次超过{hours}小时未下班，已自动结班"
                shift = None
            elif clock_in < existing:
                shift["clock_in"] = clock_in.isoformat(timespec="seconds")
                shift["work_date"] = _work_date(clock_in)
                _save_data(data)
                delta = int((existing - clock_in).total_seconds() / 60)
                title = "补卡成功" if manual_flag else "签到时间已更新"
                note = (
                    f"已按补卡时间录入，比上次提前 {delta} 分钟"
                    if manual_flag
                    else f"比上次提前了 {delta} 分钟"
                )
                return title, _render_card(
                    uid, nickname, "in_early", title, [("首次上班", shift["clock_in"])],
                    note=note, tail="今天也要加油呀～", work_date=shift["work_date"],
                )
            else:
                note = (
                    f"补卡时间 {_fmt_display(clock_in.isoformat(timespec='seconds'))} 晚于已记录 {_fmt_display(shift['clock_in'])}，未更新"
                    if manual_flag
                    else f"本次 {_fmt_display(now.isoformat(timespec='seconds'))} 不计入，以最早为准"
                )
                return "本班次已签到", _render_card(
                    uid, nickname, "in_dup", "本班次已签到", [("首次上班", shift["clock_in"])],
                    note=note, work_date=shift["work_date"],
                )

        shift = {
            "work_date": _work_date(clock_in),
            "clock_in": clock_in.isoformat(timespec="seconds"),
            "clock_out": None,
        }
        _user_state(data, uid)["active"] = shift
        _save_data(data)
        title = "补卡成功" if manual_flag else "上班打卡成功"
        note = "已按指定时间录入" if manual_flag else auto_note
        if manual_flag and auto_note:
            note = f"{auto_note}；已按指定时间录入"
        return title, _render_card(
            uid, nickname, "in", title, [("签到时间", shift["clock_in"])],
            note=note, tail="今天也要加油呀～", work_date=shift["work_date"],
        )

    def _clock_out(
        self, uid: str, nickname: str, manual: time | None, *, manual_flag: bool
    ) -> tuple[str, Optional[Path]]:
        data = _load_data()
        now = _now()
        clock_out = _combine_manual(manual, now) if manual else now
        shift = _open_shift(data, uid)

        if shift:
            if clock_out < _parse_dt(shift["clock_in"]):
                return "下班时间无效", _render_card(
                    uid, nickname, "warn", "下班时间无效", [], note="下班时间不能早于上班时间",
                )
            closed = dict(shift)
            cap_note: str | None = None
            clock_in_dt = _parse_dt(shift["clock_in"])
            if _is_forgotten(clock_in_dt, clock_out):
                end = (clock_in_dt + _forget_timeout()).replace(second=0, microsecond=0)
                closed["clock_out"] = end.isoformat(timespec="seconds")
                hours = int(_forget_timeout().total_seconds() // 3600)
                cap_note = f"已超过{hours}小时未下班，工时按{hours}小时计"
            else:
                closed["clock_out"] = clock_out.isoformat(timespec="seconds")
            title = "补卡成功" if manual_flag else "下班打卡成功"
            if manual_flag and not cap_note:
                cap_note = "已按指定时间录入"
            return self._finalize(data, uid, nickname, closed, title, cap_note, manual_flag)

        closed = _today_closed(data, uid, now)
        if not closed:
            return "还没打上班卡哦", _render_card(
                uid, nickname, "warn", "还没打上班卡哦", [],
                note="请先发送「打卡」「上班」或「补卡」",
            )
        if clock_out < _parse_dt(closed["clock_in"]):
            return "下班时间无效", _render_card(
                uid, nickname, "warn", "下班时间无效", [], note="下班时间不能早于上班时间",
            )
        existing_out = _parse_dt(closed["clock_out"])
        if clock_out == existing_out:
            dur = _fmt_duration(_shift_seconds(closed))
            return "本班次已下班", _render_card(
                uid, nickname, "in_dup", "本班次已下班",
                [("上班时间", closed["clock_in"]), ("下班时间", closed["clock_out"]), ("今日工时", dur)],
                note="与已记录时间一致，未更新", work_date=closed["work_date"],
            )
        updated = dict(closed)
        if manual_flag or clock_out > existing_out:
            updated["clock_out"] = clock_out.isoformat(timespec="seconds")
            delta = int(abs((clock_out - existing_out).total_seconds()) / 60)
            direction = "提前" if clock_out < existing_out else "延后"
            title = "补卡成功" if manual_flag else ("下班时间已更新" if clock_out > existing_out else "下班打卡成功")
            note = None
            if manual_flag:
                note = f"已按补卡时间录入，比上次{direction} {delta} 分钟"
            elif clock_out > existing_out:
                note = f"比上次延后了 {delta} 分钟"
            return self._finalize(data, uid, nickname, updated, title, note, manual_flag)

        return "本班次已下班", _render_card(
            uid, nickname, "in_dup", "本班次已下班",
            [
                ("上班时间", closed["clock_in"]),
                ("下班时间", closed["clock_out"]),
                ("今日工时", _fmt_duration(_shift_seconds(closed))),
            ],
            note=f"本次 {_fmt_display(now.isoformat(timespec='seconds'))} 不计入，以最晚为准",
            work_date=closed["work_date"],
        )

    def _finalize(
        self, data: dict, uid: str, nickname: str, closed: dict,
        title: str, note: str | None, manual_flag: bool,
    ) -> tuple[str, Optional[Path]]:
        sec = _shift_seconds(closed)
        wd = closed.get("work_date") or _work_date()
        if sec < _MIN_SHIFT:
            st = _user_state(data, uid)
            if st.get("active", {}).get("work_date") == wd:
                st.pop("active", None)
            if st.get("last_closed", {}).get("work_date") == wd:
                st.pop("last_closed", None)
            _save_data(data)
            return "就上这么点时间", _render_card(uid, nickname, "warn", "就上这么点时间", [], tail="别上了", work_date=wd)
        if sec > _MAX_SHIFT:
            st = _user_state(data, uid)
            st.pop("active", None)
            st.pop("last_closed", None)
            _save_data(data)
            return "上这么久 工资一定很高吧", _render_card(uid, nickname, "warn", "上这么久 工资一定很高吧", [], work_date=wd)
        _user_state(data, uid)["last_closed"] = closed
        _user_state(data, uid).pop("active", None)
        _save_data(data)
        tail = "加班也要注意身体哦" if sec >= 9 * 3600 else "辛苦啦，早点休息～"
        return title, _render_card(
            uid, nickname, "out", title,
            [
                ("上班时间", closed["clock_in"]),
                ("下班时间", closed["clock_out"]),
                ("今日工时", _fmt_duration(sec)),
            ],
            note=note, tail=tail, work_date=closed["work_date"],
        )

    def _group_list(self, group_openid: str) -> tuple[str, Optional[Path]]:
        data = _load_data()
        tracker = get_group_tracker()
        members = tracker.members(group_openid)
        today = _work_date()
        now = _now()
        table: list[tuple[str, str, bool, str, str | None, int]] = []

        for uid, state in data.get("by_user", {}).items():
            if uid not in members:
                continue
            name = tracker.display_name(group_openid, uid)
            short_uid = uid[-8:] if len(uid) > 8 else uid
            shift = state.get("active")
            if isinstance(shift, dict) and shift.get("clock_in") and not shift.get("clock_out"):
                cin = _parse_dt(shift["clock_in"])
                if not _is_forgotten(cin, now):
                    dur = max(0, int((now - cin).total_seconds()))
                    table.append((name, short_uid, True, shift["clock_in"], None, dur))
                    continue
            closed = state.get("last_closed")
            if isinstance(closed, dict) and closed.get("work_date") == today and closed.get("clock_out"):
                table.append((name, short_uid, False, closed["clock_in"], closed["clock_out"], _shift_seconds(closed)))

        if not table:
            return "今天还没有人打卡哦~", None
        table.sort(key=lambda r: (0 if r[2] else 1, r[3]))
        return "群上班列表", _render_group_list(table)


_service: Optional[WorkClockService] = None


def get_service() -> WorkClockService:
    global _service
    if _service is None:
        _service = WorkClockService()
    return _service
