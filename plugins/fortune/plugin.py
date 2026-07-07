# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult
from bot.utils.async_util import run_sync

from .service import get_service


class FortunePlugin(BasePlugin):
    name = "fortune"
    version = "1.0.0"
    description = "今日运势（NcatBot 同款）"
    triggers = ["今日运势", "运势", "今日doro"]

    def match(self, text: str) -> bool:
        return text.strip() in {"今日运势", "运势", "今日doro"}

    async def on_message(self, ctx: MessageContext) -> PluginReply:
        cmd = ctx.text.strip()
        svc = get_service()

        if cmd == "运势":
            img = await run_sync(svc.pick_amm_image, ctx.user_key)
            text = "✨今日运势✨"
            if img:
                return PluginResult(text=text, image_path=img)
            return text + "\n（图片资源未找到）"

        if cmd == "今日doro":
            img = await run_sync(svc.pick_doro_image, ctx.user_key)
            text = "✨今日doro结局✨"
            if img:
                return PluginResult(text=text, image_path=img)
            return text + "\n（图片资源未找到）"

        if cmd == "今日运势":
            text, img = await run_sync(svc.today_fortune, ctx.user_key)
            if img:
                return PluginResult(text=text, image_path=img)
            return text

        return None
