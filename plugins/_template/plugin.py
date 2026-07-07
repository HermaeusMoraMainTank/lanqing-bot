# -*- coding: utf-8 -*-
from typing import Optional

from bot.plugin.base import BasePlugin, MessageContext


class TemplatePlugin(BasePlugin):
    """复制此目录并重命名以创建新插件。"""

    name = "template"
    version = "0.0.0"
    description = "插件模板"
    triggers = ["示例指令"]

    async def on_message(self, ctx: MessageContext) -> PluginReply:
        return f"收到：{ctx.text}"
