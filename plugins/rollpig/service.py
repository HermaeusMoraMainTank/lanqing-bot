# -*- coding: utf-8 -*-
"""今日小猪逻辑，移植自 NcatBot/plugins/RollPig/RollPig.py"""
from __future__ import annotations

import json
import random
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

from PIL import Image as PILImage, ImageDraw, ImageFont

from bot.config import get_ncatbot_data_dir, load_config

PLUGIN_DIR = Path(__file__).resolve().parent
CACHE_PATH = PLUGIN_DIR / "data" / "rollpig_today.json"

COMMANDS = {"今日小猪", "抽小猪", "我的小猪", "rollpig"}
LIST_COMMANDS = {"小猪列表", "小猪图鉴", "猪列表"}


class RollPigService:
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 800
    AVATAR_SIZE = 280
    SPACING_AVATAR_NAME = 20
    SPACING_NAME_DESC = 25
    SPACING_DESC_ANALYSIS = 30
    DESC_FONT_SIZE = 32
    ANALYSIS_FONT_SIZE = 28
    ANALYSIS_LINE_HEIGHT_FACTOR = 1.6
    ANALYSIS_WIDTH_RATIO = 0.85
    NAME_FONT_SIZE = 66
    LIST_COLS = 8
    LIST_CANVAS_WIDTH = 920
    LIST_PADDING = 20
    LIST_HEADER_HEIGHT = 52
    LIST_CELL_GAP = 6
    LIST_CELL_IMAGE_SIZE = 64
    LIST_CELL_NAME_HEIGHT = 20
    LIST_NAME_FONT_SIZE = 14
    LIST_TITLE_FONT_SIZE = 24

    def __init__(self) -> None:
        root = get_ncatbot_data_dir(load_config())
        self.image_dir = root / "image" / "rollpig"
        self.font_dir = root / "font"
        self.piginfo_path = root / "json" / "pig.json"
        self.pig_list = self._load_json(self.piginfo_path, [])
        self.font_regular = self._init_regular_font()
        self.font_bold = self._init_bold_font()
        self.font_list_name = self._load_font(
            [
                self.font_dir / "可爱字体.ttf",
                self.font_dir / "SourceHanSansCN-Regular.otf",
                Path(r"C:/Windows/Fonts/msyh.ttc"),
            ],
            self.LIST_NAME_FONT_SIZE,
        )
        self.font_list_title = self._load_font(
            [
                self.font_dir / "荆南麦圆体.otf",
                self.font_dir / "SourceHanSansCN-Bold.otf",
                Path(r"C:/Windows/Fonts/msyhbd.ttc"),
            ],
            self.LIST_TITLE_FONT_SIZE,
        )

    @staticmethod
    def _load_json(path: Path, default):
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text("utf-8"))
        except json.JSONDecodeError:
            return default

    @staticmethod
    def _save_json(path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_font(self, candidates: list, size: int) -> ImageFont.FreeTypeFont:
        for font_path in candidates:
            if Path(font_path).exists():
                try:
                    return ImageFont.truetype(str(font_path), size)
                except OSError:
                    continue
        return ImageFont.load_default()

    def _init_regular_font(self):
        return self._load_font(
            [
                self.font_dir / "可爱字体.ttf",
                self.font_dir / "SourceHanSansCN-Regular.otf",
                Path(r"C:/Windows/Fonts/msyh.ttc"),
            ],
            self.DESC_FONT_SIZE,
        )

    def _init_bold_font(self):
        return self._load_font(
            [
                self.font_dir / "荆南麦圆体.otf",
                self.font_dir / "SourceHanSansCN-Bold.otf",
                Path(r"C:/Windows/Fonts/msyhbd.ttc"),
            ],
            self.NAME_FONT_SIZE,
        )

    @staticmethod
    def _text_size(text: str, font) -> tuple[int, int]:
        draw = ImageDraw.Draw(PILImage.new("RGB", (1, 1)))
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _truncate_text(self, draw, text: str, font, max_width: int) -> str:
        if not text:
            return text
        if self._text_size(text, font)[0] <= max_width:
            return text
        ellipsis = "…"
        for end in range(len(text) - 1, 0, -1):
            probe = text[:end] + ellipsis
            if self._text_size(probe, font)[0] <= max_width:
                return probe
        return ellipsis

    def _analysis_font(self):
        try:
            return self.font_regular.font_variant(size=self.ANALYSIS_FONT_SIZE)
        except Exception:
            return self._load_font(
                [
                    self.font_dir / "可爱字体.ttf",
                    self.font_dir / "SourceHanSansCN-Regular.otf",
                    Path(r"C:/Windows/Fonts/msyh.ttc"),
                ],
                self.ANALYSIS_FONT_SIZE,
            )

    def _desc_font(self):
        try:
            return self.font_regular.font_variant(size=self.DESC_FONT_SIZE)
        except Exception:
            return self.font_regular

    @staticmethod
    def _draw_bold_text(draw, pos, text, font, fill):
        x, y = pos
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            draw.text((x + ox, y + oy), text, fill=fill, font=font)
        draw.text((x, y), text, fill=fill, font=font)

    def find_image_file(self, pig_id: str) -> Optional[Path]:
        for ext in ("png", "jpg", "jpeg", "webp", "gif"):
            file = self.image_dir / f"{pig_id}.{ext}"
            if file.exists():
                return file
        return None

    def _load_thumbnail(self, pig_id: str, size: int) -> Optional[PILImage.Image]:
        path = self.find_image_file(pig_id)
        if not path:
            return None
        try:
            with PILImage.open(path) as img:
                if getattr(img, "is_animated", False):
                    img.seek(0)
                frame = img.convert("RGBA")
                frame.thumbnail((size, size), PILImage.Resampling.LANCZOS)
                if frame.size != (size, size):
                    left = (frame.width - size) // 2
                    top = (frame.height - size) // 2
                    frame = frame.crop((left, top, left + size, top + size))
                return frame.copy()
        except OSError:
            return None

    def render_pig_image(self, pig_data: dict) -> Optional[Path]:
        pig_id = pig_data.get("id", "")
        pig_name = pig_data.get("name", "未知小猪")
        pig_desc = pig_data.get("description", "无描述")
        pig_analysis = pig_data.get("analysis", "无解析")

        canvas = PILImage.new("RGB", (self.CANVAS_WIDTH, self.CANVAS_HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        avatar = None
        avatar_path = self.find_image_file(pig_id)
        if avatar_path:
            try:
                avatar = PILImage.open(avatar_path)
                avatar.thumbnail((self.AVATAR_SIZE, self.AVATAR_SIZE))
                if avatar.size != (self.AVATAR_SIZE, self.AVATAR_SIZE):
                    cx, cy = avatar.width // 2, avatar.height // 2
                    half = self.AVATAR_SIZE // 2
                    avatar = avatar.crop((cx - half, cy - half, cx + half, cy + half))
            except OSError:
                avatar = None

        name_font = self.font_bold
        name_w, name_h = self._text_size(pig_name, name_font)
        desc_font = self._desc_font()
        desc_w, desc_h = self._text_size(pig_desc, desc_font)
        analysis_font = self._analysis_font()
        line_height = int(self.ANALYSIS_FONT_SIZE * self.ANALYSIS_LINE_HEIGHT_FACTOR)
        max_w = int(self.CANVAS_WIDTH * self.ANALYSIS_WIDTH_RATIO)

        lines: list[str] = []
        current = ""
        for char in pig_analysis:
            current += char
            if self._text_size(current, analysis_font)[0] > max_w:
                lines.append(current[:-1])
                current = char
        if current:
            lines.append(current)
        analysis_total_h = len(lines) * line_height

        total_h = (
            self.AVATAR_SIZE
            + self.SPACING_AVATAR_NAME
            + name_h
            + self.SPACING_NAME_DESC
            + desc_h
            + self.SPACING_DESC_ANALYSIS
            + analysis_total_h
        )
        start_y = (self.CANVAS_HEIGHT - total_h) // 2
        avatar_x = (self.CANVAS_WIDTH - self.AVATAR_SIZE) // 2
        avatar_y = start_y

        if avatar:
            canvas.paste(
                avatar,
                (avatar_x, avatar_y),
                mask=avatar if avatar.mode == "RGBA" else None,
            )
        else:
            err_font = self._load_font([Path(r"C:/Windows/Fonts/msyh.ttc")], 24)
            err_text = "图片加载失败"
            ew, _ = self._text_size(err_text, err_font)
            draw.text(((self.CANVAS_WIDTH - ew) // 2, avatar_y + 120), err_text, fill=(255, 0, 0), font=err_font)

        name_y = avatar_y + self.AVATAR_SIZE + self.SPACING_AVATAR_NAME
        self._draw_bold_text(
            draw,
            ((self.CANVAS_WIDTH - name_w) // 2, name_y),
            pig_name,
            name_font,
            (0, 0, 0),
        )
        desc_y = name_y + name_h + self.SPACING_NAME_DESC
        draw.text(
            ((self.CANVAS_WIDTH - desc_w) // 2, desc_y),
            pig_desc,
            fill=(85, 85, 85),
            font=desc_font,
        )
        ay = desc_y + desc_h + self.SPACING_DESC_ANALYSIS
        for line in lines:
            lw, _ = self._text_size(line, analysis_font)
            draw.text(((self.CANVAS_WIDTH - lw) // 2, ay), line, fill=(51, 51, 51), font=analysis_font)
            ay += line_height

        fd, name = tempfile.mkstemp(suffix=".png", prefix="rollpig_")
        path = Path(name)
        with open(fd, "wb"):
            pass
        canvas.save(path, format="PNG", quality=95)
        return path

    def render_pig_list_image(self) -> Optional[Path]:
        if not self.pig_list:
            return None
        pigs = self.pig_list
        width = self.LIST_CANVAS_WIDTH
        padding = self.LIST_PADDING
        cols = self.LIST_COLS
        gap = self.LIST_CELL_GAP
        img_size = self.LIST_CELL_IMAGE_SIZE
        name_h = self.LIST_CELL_NAME_HEIGHT
        inner_w = width - padding * 2
        cell_w = (inner_w - gap * (cols - 1)) // cols
        row_h = img_size + name_h + gap
        rows = (len(pigs) + cols - 1) // cols
        height = padding * 2 + self.LIST_HEADER_HEIGHT + rows * row_h

        canvas = PILImage.new("RGB", (width, height), (255, 252, 248))
        draw = ImageDraw.Draw(canvas)
        title = f"小猪图鉴 · 共 {len(pigs)} 只"
        tw, _ = self._text_size(title, self.font_list_title)
        draw.text(((width - tw) // 2, padding), title, fill=(255, 120, 80), font=self.font_list_title)
        draw.line(
            [(padding, padding + self.LIST_HEADER_HEIGHT - 12), (width - padding, padding + self.LIST_HEADER_HEIGHT - 12)],
            fill=(240, 220, 210), width=2,
        )

        start_y = padding + self.LIST_HEADER_HEIGHT
        for idx, pig in enumerate(pigs):
            col, row = idx % cols, idx // cols
            x = padding + col * (cell_w + gap)
            y = start_y + row * row_h
            draw.rounded_rectangle(
                (x, y, x + cell_w, y + img_size + name_h + 4),
                radius=8, fill=(255, 255, 255), outline=(235, 225, 220), width=1,
            )
            thumb_x = x + (cell_w - img_size) // 2
            thumb_y = y + 3
            thumb = self._load_thumbnail(pig.get("id", ""), img_size)
            if thumb:
                canvas.paste(thumb, (thumb_x, thumb_y), thumb)
            else:
                draw.rectangle(
                    (thumb_x, thumb_y, thumb_x + img_size, thumb_y + img_size),
                    fill=(245, 240, 238), outline=(220, 210, 205),
                )
            name = pig.get("name", "未知")
            name_font = self.font_list_name
            max_name_w = cell_w - 6
            name_w, _ = self._text_size(name, name_font)
            if name_w > max_name_w:
                name = self._truncate_text(draw, name, name_font, max_name_w)
                name_w, _ = self._text_size(name, name_font)
            draw.text((x + (cell_w - name_w) // 2, y + img_size + 4), name, fill=(80, 70, 65), font=name_font)

        fd, name = tempfile.mkstemp(suffix=".png", prefix="rollpig_list_")
        path = Path(name)
        with open(fd, "wb"):
            pass
        canvas.save(path, format="PNG", optimize=True)
        return path

    def draw_pig(self, user_key: str, target_key: str) -> tuple[str, Optional[Path]]:
        if not self.pig_list:
            return "小猪信息加载失败，请检查后台资源！", None

        today_str = date.today().isoformat()
        cache = self._load_json(CACHE_PATH, {"date": "", "records": {}})
        if cache.get("date") != today_str:
            cache = {"date": today_str, "records": {}}

        records = cache["records"]
        if target_key in records:
            pig = records[target_key]
        else:
            pig = random.choice(self.pig_list)
            records[target_key] = pig
            cache["records"] = records
            self._save_json(CACHE_PATH, cache)

        img = self.render_pig_image(pig)
        text = f"这是你的今日小猪：\n【{pig.get('name', '未知')}】"
        return text, img


_service: Optional[RollPigService] = None


def get_service() -> RollPigService:
    global _service
    if _service is None:
        _service = RollPigService()
    return _service
