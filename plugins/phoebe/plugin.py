# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult
from bot.utils.async_util import run_sync
from bot.utils.logger import get_log

from .service import get_service

COMMAND = "菲比搜索"
_log = get_log("lanqing.plugin.phoebe")


class PhoebePlugin(BasePlugin):
    name = "phoebe"
    version = "1.0.0"
    description = "菲比搜索（带参）"
    triggers = [COMMAND]

    def match(self, text: str) -> bool:
        return text.strip().startswith(COMMAND)

    async def on_message(self, ctx: MessageContext) -> PluginReply:
        cmd = ctx.text.strip()
        if not cmd.startswith(COMMAND):
            return None
        query = cmd[len(COMMAND) :].strip()
        if query.lower() in ("help", "?", "帮助"):
            query = ""
        try:
            text, images = await run_sync(get_service().handle_query, query)
        except Exception as exc:
            _log.exception("菲比数据加载失败 query=%r", query)
            return f"[Phoebe] 菲比数据加载失败，请稍后再试: {exc}"
        if images:
            return PluginResult(text=text, image_path=images[0])
        return text
