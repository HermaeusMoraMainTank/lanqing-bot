# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

from bot.plugin.result import PluginReply


Scene = Literal["group", "guild", "c2c"]


@dataclass
class MessageContext:
    """插件处理上下文。"""

    text: str
    raw_text: str
    user_key: str
    display_name: str
    scene: Scene
    client: Any
    message: Any
    group_openid: str = ""
    mentioned_openids: list[str] = field(default_factory=list)


class BasePlugin(ABC):
    """插件基类。每个功能模块继承此类并放入 plugins/ 目录。"""

    name: str = "unnamed"
    version: str = "0.0.0"
    description: str = ""
    triggers: list[str] = []

    def match(self, text: str) -> bool:
        normalized = text.strip().lower()
        for trigger in self.triggers:
            if trigger.isascii():
                if normalized == trigger.lower():
                    return True
            elif text.strip() == trigger:
                return True
        return False

    @abstractmethod
    def on_message(self, ctx: MessageContext) -> PluginReply:
        """匹配成功时返回 str / PluginResult，未处理返回 None。"""
