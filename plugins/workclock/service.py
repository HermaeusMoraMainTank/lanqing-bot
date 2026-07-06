# -*- coding: utf-8 -*-
"""上下班打卡，移植自 NcatBot/plugins/WorkClock/WorkClock.py"""
from __future__ import annotations

import io
import json
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage, ImageDraw, ImageFont

from bot.utils.group_track import get_group_tracker
from bot.utils.temp_image import save_temp_png

PLUGIN_DIR = Path(__file__).resolve().parent
DATA_PATH = PLUGIN_DIR / "data" / "data.json"

_CLOCK_IN = ("群上班", "打卡", "补卡", "上班")
_CLOCK_OUT = ("群下班", "下班")
_MIN_SHIFT = 6 * 3600
_MAX_SHIFT = 18 * 3600

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


def _forget_timeout() -> timedelta:
    return timedelta(hours=24)


def _parse_dt(value: str) -> datetime:
    if "T" in value:
        return datetime.fromisoformat(value)
    return datetime.combine(date.today(), datetime.strptime(value, "%H:%M:%S").time())


def _fmt_display(value: str) -> str:
    return _parse_dt(value).strftime("%m-%d %H:%M")


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
    start = _parse_dt(shift["clock_in"])
    end = _parse_dt(shift["clock_out"])
    return max(0, int((end - start).total_seconds()))


def _load_font(size: int, bold: bool = False):
    names = ("msyhbd.ttc", "msyh.ttc", "simhei.ttf") if bold else ("msyh.ttc", "simhei.ttf")
    for name in names:
        path = Path(rf"C:/Windows/Fonts/{name}")
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _render_card(title: str, rows: list[tuple[str, str]], note: str = "", tail: str = "") -> Path:
    W, M, pad = 500, 16, 24
    row_h = 46
    body_h = max(40, len(rows) * row_h + 20) if rows else 108
    H = M + 84 + 1 + body_h + (26 if note else 0) + (28 if tail else 0) + 22 + M
    canvas = PILImage.new("RGB", (W, H), (240, 243, 248))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((M, M, W - M, H - M), radius=16, fill=(255, 255, 255), outline=(220, 226, 236))
    draw.rounded_rectangle((M, M, M + 5, H - M), radius=16, fill=(255, 106, 48))
    f_title = _load_font(20, bold=True)
    f_label = _load_font(17)
    f_value = _load_font(22, bold=True)
    draw.text((M + 24, M + 46), title, font=f_title, fill=(48, 48, 56))
    y = M + 84 + 18
    left = M + 24
    right = W - M - pad
    if len(rows) == 1 and rows[0][0] in ("签到时间", "首次上班"):
        label, value = rows[0]
        display = _fmt_display(value) if "T" in value else value
        f_hero = _load_font(36, bold=True)
        draw.text((left, y + 8), display, font=f_hero, fill=(255, 106, 48))
        draw.text((left, y + 58), label, font=f_label, fill=(120, 108, 100))
    else:
        for label, value in rows:
            display = value if "工时" in label else _fmt_display(value)
            draw.text((left, y + 10), label.replace("今日", ""), font=f_label, fill=(120, 108, 100))
            vw = draw.textbbox((0, 0), display, font=f_value)[2]
            draw.text((right - vw, y + 8), display, font=f_value, fill=(255, 106, 48))
            y += row_h
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return save_temp_png(buf.getvalue(), prefix="workclock_")


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
    def handle(self, cmd: str, user_key: str, group_openid: str) -> tuple[str, Optional[Path]]:
        if cmd == "群上班列表":
            return self._group_list(group_openid)
        for trigger in _CLOCK_OUT:
            if cmd == trigger:
                return self._clock_out(user_key, None, manual_flag=False)
            if cmd.startswith(trigger):
                rest = cmd[len(trigger) :].strip()
                if rest and _looks_like_time(rest):
                    t = parse_clock_time(rest)
                    if t is None:
                        return "补卡时间无法识别", _render_card("补卡时间无法识别", [], note="示例：下班 6点")
                    return self._clock_out(user_key, t, manual_flag=True)
                if not rest:
                    return self._clock_out(user_key, None, manual_flag=False)
        for trigger in _CLOCK_IN:
            if cmd == trigger:
                return self._clock_in(user_key, None, manual_flag=False)
            if cmd.startswith(trigger):
                rest = cmd[len(trigger) :].strip()
                if rest and _looks_like_time(rest):
                    t = parse_clock_time(rest)
                    if t is None:
                        return "补卡时间无法识别", _render_card("补卡时间无法识别", [], note="示例：打卡 9点")
                    return self._clock_in(user_key, t, manual_flag=True)
                if not rest:
                    return self._clock_in(user_key, None, manual_flag=False)
        return "未知指令", None

    def _clock_in(self, uid: str, manual: time | None, *, manual_flag: bool) -> tuple[str, Optional[Path]]:
        data = _load_data()
        now = _now()
        clock_in = _combine_manual(manual, now) if manual else now
        shift = _open_shift(data, uid)
        if shift:
            existing = _parse_dt(shift["clock_in"])
            if clock_in < existing:
                shift["clock_in"] = clock_in.isoformat(timespec="seconds")
                shift["work_date"] = _work_date(clock_in)
                _save_data(data)
                title = "补卡成功" if manual_flag else "签到时间已更新"
                return title, _render_card(title, [("首次上班", shift["clock_in"])], tail="今天也要加油呀～")
            title = "本班次已签到"
            return title, _render_card(title, [("首次上班", shift["clock_in"])], note="以最早为准")
        shift = {
            "work_date": _work_date(clock_in),
            "clock_in": clock_in.isoformat(timespec="seconds"),
            "clock_out": None,
        }
        _user_state(data, uid)["active"] = shift
        _save_data(data)
        title = "补卡成功" if manual_flag else "上班打卡成功"
        return title, _render_card(title, [("签到时间", shift["clock_in"])], tail="今天也要加油呀～")

    def _clock_out(self, uid: str, manual: time | None, *, manual_flag: bool) -> tuple[str, Optional[Path]]:
        data = _load_data()
        now = _now()
        clock_out = _combine_manual(manual, now) if manual else now
        shift = _open_shift(data, uid)
        if shift:
            if clock_out < _parse_dt(shift["clock_in"]):
                return "下班时间无效", _render_card("下班时间无效", [], note="不能早于上班时间")
            closed = dict(shift)
            closed["clock_out"] = clock_out.isoformat(timespec="seconds")
            return self._finalize(data, uid, closed, manual_flag)
        closed = _today_closed(data, uid, now)
        if not closed:
            return "还没打上班卡哦", _render_card("还没打上班卡哦", [], note="请先发送「打卡」或「上班」")
        if clock_out < _parse_dt(closed["clock_in"]):
            return "下班时间无效", _render_card("下班时间无效", [], note="不能早于上班时间")
        updated = dict(closed)
        updated["clock_out"] = clock_out.isoformat(timespec="seconds")
        return self._finalize(data, uid, updated, manual_flag)

    def _finalize(self, data: dict, uid: str, closed: dict, manual_flag: bool) -> tuple[str, Optional[Path]]:
        sec = _shift_seconds(closed)
        wd = closed.get("work_date") or _work_date()
        if sec < _MIN_SHIFT:
            st = _user_state(data, uid)
            if st.get("active", {}).get("work_date") == wd:
                st.pop("active", None)
            if st.get("last_closed", {}).get("work_date") == wd:
                st.pop("last_closed", None)
            _save_data(data)
            return "就上这么点时间", _render_card("就上这么点时间", [], tail="别上了")
        if sec > _MAX_SHIFT:
            st = _user_state(data, uid)
            st.pop("active", None)
            st.pop("last_closed", None)
            _save_data(data)
            return "上这么久 工资一定很高吧", _render_card("上这么久 工资一定很高吧", [])
        _user_state(data, uid)["last_closed"] = closed
        _user_state(data, uid).pop("active", None)
        _save_data(data)
        title = "补卡成功" if manual_flag else "下班打卡成功"
        rows = [
            ("上班时间", closed["clock_in"]),
            ("下班时间", closed["clock_out"]),
            ("今日工时", _fmt_duration(sec)),
        ]
        tail = "加班也要注意身体哦" if sec >= 9 * 3600 else "辛苦啦，早点休息～"
        return title, _render_card(title, rows, tail=tail)

    def _group_list(self, group_openid: str) -> tuple[str, Optional[Path]]:
        data = _load_data()
        tracker = get_group_tracker()
        members = tracker.members(group_openid)
        today = _work_date()
        rows: list[str] = []
        for uid, state in data.get("by_user", {}).items():
            if uid not in members:
                continue
            shift = state.get("active")
            if isinstance(shift, dict) and shift.get("clock_in") and not shift.get("clock_out"):
                dur = max(0, int((_now() - _parse_dt(shift["clock_in"])).total_seconds()))
                rows.append(f"{uid[:8]}… { _parse_dt(shift['clock_in']).strftime('%H:%M')} 上班中 · {_fmt_duration(dur)}")
                continue
            closed = state.get("last_closed")
            if isinstance(closed, dict) and closed.get("work_date") == today and closed.get("clock_out"):
                dur = _fmt_duration(_shift_seconds(closed))
                cin = _parse_dt(closed["clock_in"]).strftime("%H:%M")
                cout = _parse_dt(closed["clock_out"]).strftime("%H:%M")
                rows.append(f"{uid[:8]}… {cin}-{cout} 已下班 · {dur}")
        if not rows:
            return "今天还没有人打卡哦~", None
        img = PILImage.new("RGB", (980, 80 + len(rows) * 42), (255, 248, 242))
        draw = ImageDraw.Draw(img)
        font = _load_font(20)
        draw.text((28, 20), "群上班列表", font=_load_font(28, bold=True), fill=(255, 106, 48))
        y = 70
        for line in rows:
            draw.text((28, y), line, font=font, fill=(48, 48, 56))
            y += 42
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "群上班列表", save_temp_png(buf.getvalue(), prefix="workclock_list_")


_service: Optional[WorkClockService] = None


def get_service() -> WorkClockService:
    global _service
    if _service is None:
        _service = WorkClockService()
    return _service
