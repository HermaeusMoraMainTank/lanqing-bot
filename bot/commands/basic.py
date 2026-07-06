# -*- coding: utf-8 -*-
import re
from typing import Optional

COMMANDS: dict[str, str] = {
    "帮助": "可用指令：\n· 帮助 — 显示本消息\n· ping — 测试连通性\n· 你好 / hello — 打招呼",
    "ping": "pong！",
    "你好": "你好呀～",
    "hello": "Hello!",
}


def strip_mention(content: str) -> str:
    """去掉 @机器人 等 mention 标记，保留纯文本。"""
    if not content:
        return ""
    text = re.sub(r"<@!\d+>", "", content)
    text = re.sub(r"<@\d+>", "", text)
    return text.strip()


def match_command(text: str) -> Optional[str]:
    normalized = text.strip().lower()
    for keyword, reply in COMMANDS.items():
        if normalized == keyword.lower():
            return reply
    return None
