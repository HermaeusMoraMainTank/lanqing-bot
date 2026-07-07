# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult
from bot.utils.async_util import run_sync

from .service import build_list, pick_wife


class WaifuPlugin(BasePlugin):
    name = "waifu"
    version = "1.0.0"
    description = "今日老婆"
    triggers = ["今日老婆", "群老婆列表"]

    def match(self, text: str) -> bool:
        return text.strip() in {"今日老婆", "群老婆列表"}

    async def on_message(self, ctx: MessageContext) -> PluginReply:
        cmd = ctx.text.strip()
        group = ctx.group_openid or "default"

        if cmd == "群老婆列表":
            text, img = await run_sync(build_list, group)
            if img:
                return PluginResult(text=text, image_path=img)
            return text

        if cmd == "今日老婆":
            text, img = await run_sync(pick_wife, group, ctx.user_key)
            if img:
                return PluginResult(text=text, image_path=img)
            return text

        return None
