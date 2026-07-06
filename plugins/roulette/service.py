# -*- coding: utf-8 -*-
"""轮盘赌逻辑（无禁言），移植自 NcatBot/plugins/RussianRoulette"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from bot.config import get_ncatbot_data_dir, load_config

CLIP_SIZE = 6
MALFUNCTION_PROBABILITY = 0.03
BOT_NAME = "蓝晴"


class RouletteService:
    def __init__(self) -> None:
        root = get_ncatbot_data_dir(load_config())
        self.kill_count_path = root / "txt" / "RussianRoulette.txt"
        self.image_dir = root / "image" / "RussianRoulette"
        self.trigger_position: dict[str, int] = {}
        self.bullet_position: dict[str, int] = {}
        self.kill_count = self._load_kill_count()

    def _load_kill_count(self) -> int:
        try:
            if self.kill_count_path.exists():
                line = self.kill_count_path.read_text(encoding="utf-8").splitlines()
                if line and line[0].strip():
                    return int(line[0].strip())
        except (OSError, ValueError):
            pass
        return 0

    def _save_kill_count(self) -> None:
        try:
            self.kill_count_path.parent.mkdir(parents=True, exist_ok=True)
            self.kill_count_path.write_text(str(self.kill_count), encoding="utf-8")
        except OSError:
            pass

    def _reload(self, group_key: str) -> None:
        self.bullet_position[group_key] = random.randint(0, CLIP_SIZE - 1)
        self.trigger_position[group_key] = 0

    def shoot(self, group_key: str, user_name: str) -> tuple[str, Optional[Path]]:
        trigger = self.trigger_position.get(group_key)
        bullet = self.bullet_position.get(group_key)
        if trigger is None or bullet is None:
            self._reload(group_key)
            trigger = self.trigger_position[group_key]
            bullet = self.bullet_position[group_key]

        lines: list[str] = []

        if trigger == CLIP_SIZE - 1:
            lines.append(f"{user_name}很清楚这是必死之局。")

        if random.random() < MALFUNCTION_PROBABILITY:
            self._reload(group_key)
            lines.append(f"左轮手枪突然炸膛了...\n{BOT_NAME}换了一把新的手枪。")
            return "\n".join(lines), None

        remaining = (CLIP_SIZE - trigger) - 1

        if trigger == bullet:
            self.kill_count += 1
            self._save_kill_count()
            lines.append(
                f"{user_name}的目光逐渐变得呆滞，他向后摔倒在地，看上去像是从来没有活过似的。\n"
                f"{BOT_NAME}枪下不幸的冤魂已有 {self.kill_count} 条，但他仍然重新装上了子弹。"
            )
            self._reload(group_key)
            img: Optional[Path] = None
            if random.randint(0, 99) <= 20:
                for name in ("开枪.jpg", "开枪.gif"):
                    path = self.image_dir / name
                    if path.exists():
                        img = path
                        break
                lines.append(f"{BOT_NAME}打出了暴击！")
            return "\n".join(lines), img

        self.trigger_position[group_key] = (trigger + 1) % CLIP_SIZE
        lines.append(
            f"{user_name}侥幸活过了一轮，但他终究难逃死亡的结局，每个人都会死。\n"
            f"{BOT_NAME}的左轮手枪还剩 {remaining} 发。"
        )
        return "\n".join(lines), None

    def shoot_until_death(self, group_key: str, user_name: str) -> list[tuple[str, Optional[Path]]]:
        results: list[tuple[str, Optional[Path]]] = []
        for _ in range(CLIP_SIZE):
            text, img = self.shoot(group_key, user_name)
            results.append((text, img))
            if "向后摔倒" in text:
                break
        return results


_service: Optional[RouletteService] = None


def get_service() -> RouletteService:
    global _service
    if _service is None:
        _service = RouletteService()
    return _service
