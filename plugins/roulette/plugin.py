# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult
from bot.utils.async_util import run_sync

from .service import get_service


class RoulettePlugin(BasePlugin):
    name = "roulette"
    version = "1.0.0"
    description = "轮盘赌（无禁言）"
    triggers = ["轮盘赌", "午时已到"]

    def match(self, text: str) -> bool:
        cmd = text.strip()
        return cmd == "午时已到" or cmd.startswith("轮盘赌")

    async def on_message(self, ctx: MessageContext) -> PluginReply:
        cmd = ctx.text.strip()
        svc = get_service()
        group_key = ctx.group_openid or ctx.user_key
        name = ctx.display_name

        if cmd == "午时已到":
            rounds = await run_sync(svc.shoot_until_death, group_key, name)
            if not rounds:
                return None
            text = "\n\n".join(t for t, _ in rounds)
            last_img = next((img for _, img in reversed(rounds) if img), None)
            if last_img:
                return PluginResult(text=text, image_path=last_img)
            return text

        if cmd.startswith("轮盘赌"):
            text, img = await run_sync(svc.shoot, group_key, name)
            if img:
                return PluginResult(text=text, image_path=img)
            return text

        return None
