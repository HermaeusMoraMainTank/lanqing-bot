# -*- coding: utf-8 -*-
import re


def strip_mention(content: str) -> str:
    """去掉 @机器人 等 mention 标记，保留纯文本。"""
    if not content:
        return ""
    text = re.sub(r"<@!\d+>", "", content)
    text = re.sub(r"<@\d+>", "", text)
    return text.strip()


def normalize_command(content: str) -> str:
    """去掉 @ 与指令面板前缀 `/`，得到纯指令文本。"""
    text = strip_mention(content)
    if text.startswith("/"):
        text = text[1:]
    return text.strip()
