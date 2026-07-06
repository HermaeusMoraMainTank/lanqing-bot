# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult

from .service import TRIGGER_COMMANDS, build_list, draw_waifu


class AnimeWaifuPlugin(BasePlugin):
    name = "anime_waifu"
    version = "1.0.0"
    description = "今日二次元老婆"
    triggers = list(TRIGGER_COMMANDS) + ["群二次元老婆列表"]

    def match(self, text: str) -> bool:
        cmd = text.strip()
        return cmd in TRIGGER_COMMANDS or cmd == "群二次元老婆列表"

    def on_message(self, ctx: MessageContext) -> PluginReply:
        cmd = ctx.text.strip()
        group = ctx.group_openid or "default"

        if cmd == "群二次元老婆列表":
            text, img = build_list(group)
            if img:
                return PluginResult(text=text, image_path=img)
            return text

        if cmd in TRIGGER_COMMANDS:
            text, img = draw_waifu(group, ctx.user_key)
            if img:
                return PluginResult(text=text, image_path=img)
            return text

        return None
