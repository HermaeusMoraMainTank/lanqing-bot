# -*- coding: utf-8 -*-
import os
from pathlib import Path

from botpy.ext.cog_yaml import read

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        example = ROOT_DIR / "config" / "config.example.yaml"
        raise FileNotFoundError(
            f"未找到配置文件 {CONFIG_PATH}，"
            f"请复制 {example} 为 config.yaml 并填入 AppID / AppSecret。"
        )
    return read(os.fspath(CONFIG_PATH))


def build_intents(config: dict) -> "botpy.Intents":
    import botpy

    scenes = config.get("scenes", {})
    intents = botpy.Intents.none()

    if scenes.get("guild", True):
        intents.public_guild_messages = True

    if scenes.get("group", False) or scenes.get("c2c", False):
        intents.public_messages = True

    return intents
