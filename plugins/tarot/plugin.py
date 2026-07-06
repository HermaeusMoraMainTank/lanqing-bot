# -*- coding: utf-8 -*-
from bot.config import load_config
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult

from .service import draw_tarot


class TarotPlugin(BasePlugin):
    name = "tarot"
    version = "1.2.0"
    description = "塔罗占卜（NcatBot 同款）"
    triggers = ["占卜"]

    def match(self, text: str) -> bool:
        return text.strip() == "占卜"

    def on_message(self, ctx: MessageContext) -> PluginReply:
        config = load_config()
        vip_openids = set(config.get("tarot_vip_openids", []))
        result = draw_tarot(vip_boost=ctx.user_key in vip_openids)
        if result.image_path:
            return PluginResult(text=result.text, image_path=result.image_path)
        return result.text
