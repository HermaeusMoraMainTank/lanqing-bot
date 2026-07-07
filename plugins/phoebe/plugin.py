# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult

from .service import get_service

COMMAND = "菲比搜索"


class PhoebePlugin(BasePlugin):
    name = "phoebe"
    version = "1.0.0"
    description = "菲比搜索（带参）"
    triggers = [COMMAND]

    def match(self, text: str) -> bool:
        return text.strip().startswith(COMMAND)

    def on_message(self, ctx: MessageContext) -> PluginReply:
        cmd = ctx.text.strip()
        if not cmd.startswith(COMMAND):
            return None
        query = cmd[len(COMMAND) :].strip()
        if query.lower() in ("help", "?", "帮助"):
            query = ""
        try:
            text, images = get_service().handle_query(query)
        except Exception as exc:
            return f"[Phoebe] 菲比数据加载失败，请稍后再试: {exc}"
        if images:
            return PluginResult(text=text, image_path=images[0])
        return text
