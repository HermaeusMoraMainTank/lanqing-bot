# -*- coding: utf-8 -*-
"""塔罗占卜逻辑，移植自 NcatBot/plugins/Tarot/Tarot.py"""
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from PIL import Image as PILImage

from bot.config import get_ncatbot_data_dir, load_config

FORMAT = "%牌名%\n%描述%"
REPEATABLE = False
ROTATE = True

TAROT_LIBRARIES = [
    "image/Tarot/Tarot3",
    "image/Tarot/Tarot5",
    "image/Tarot/Tarot6",
    "image/Tarot/Tarot7",
    "image/Tarot/Tarot8",
    "image/Tarot/Tarot9",
    "image/Tarot/Tarot9",
    "image/Tarot/Tarot10",
]

PLUGIN_DIR = Path(__file__).resolve().parent
TEMP_DIR = PLUGIN_DIR / "data" / "temp"


@dataclass
class TarotCard:
    name: str
    positive: str
    negative: str
    image_name: str


@dataclass
class TarotDraw:
    text: str
    image_path: Optional[Path]


def _data_root() -> Path:
    return get_ncatbot_data_dir(load_config())


def load_tarot_data() -> list[TarotCard]:
    path = _data_root() / "yml" / "tarot.yml"
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    cards = []
    for item in data.get("tarot", []):
        cards.append(
            TarotCard(
                name=item["name"],
                positive=item["positive"],
                negative=item["negative"],
                image_name=item["imageName"],
            )
        )
    return cards


def load_blacksouls_tarot_data() -> list[TarotCard]:
    path = _data_root() / "yml" / "blacksouls_tarot.yml"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    cards = []
    for item in data.get("tarot", []):
        cards.append(
            TarotCard(
                name=item["name"],
                positive=item["positive"],
                negative=item["negative"],
                image_name=item["imageName"],
            )
        )
    return cards


def get_tarot_message(card: TarotCard, upright: bool) -> str:
    desc = f"正位\n{card.positive}" if upright else f"逆位\n{card.negative}"
    return FORMAT.replace("%牌名%", card.name).replace("%描述%", desc)


def _rotate_image(file: Path) -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    with PILImage.open(file) as img:
        rotated = img.rotate(180)
        out = TEMP_DIR / f"rotated_{file.name}"
        rotated.convert("RGB").save(out, format="JPEG")
        return out


def get_tarot_image(image_name: str, upright: bool) -> Optional[Path]:
    current_date = datetime.now().strftime("%Y%m%d")
    library_index = abs(hash(current_date)) % len(TAROT_LIBRARIES)
    folder = _data_root() / TAROT_LIBRARIES[library_index]
    if not folder.is_dir():
        return None
    for file in folder.iterdir():
        if file.name == image_name:
            if upright or not ROTATE:
                return file.resolve()
            return _rotate_image(file).resolve()
    return None


def get_random_tarots(count: int) -> list[TarotCard]:
    tarots: list[TarotCard] = []
    pool = load_tarot_data()
    while len(tarots) < count and len(tarots) < len(pool):
        card = random.choice(pool)
        if REPEATABLE or card not in tarots:
            tarots.append(card)
    return tarots


def _try_blacksouls() -> Optional[TarotDraw]:
    folder = _data_root() / "image" / "Tarot" / "Blacksouls"
    if not folder.is_dir():
        return None
    files = [
        f for f in folder.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg")
    ]
    if not files:
        return None
    image = random.choice(files)
    for card in load_blacksouls_tarot_data():
        if card.image_name == image.name:
            return TarotDraw(text=card.positive, image_path=image.resolve())
    return None


def draw_tarot(vip_boost: bool = False) -> TarotDraw:
    probability = 0.05
    if vip_boost:
        probability += 0.5
    if random.random() < probability:
        special = _try_blacksouls()
        if special:
            return special

    card = get_random_tarots(1)[0]
    upright = random.randint(0, 1) == 0
    text = get_tarot_message(card, upright)
    image_path = get_tarot_image(card.image_name, upright)
    return TarotDraw(text=text, image_path=image_path)
