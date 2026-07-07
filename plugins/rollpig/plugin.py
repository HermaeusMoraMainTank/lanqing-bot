# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult
from bot.utils.async_util import run_sync

from .service import LIST_COMMANDS, COMMANDS, get_service


class RollPigPlugin(BasePlugin):
    name = "rollpig"
    version = "1.0.0"
    description = "今日小猪（NcatBot 同款）"
    triggers = list(COMMANDS | LIST_COMMANDS)

    def match(self, text: str) -> bool:
        cmd = text.strip()
        if cmd.lower() == "rollpig":
            return True
        return cmd in COMMANDS or cmd in LIST_COMMANDS

    async def on_message(self, ctx: MessageContext) -> PluginReply:
        cmd = ctx.text.strip()
        if cmd.lower() == "rollpig":
            cmd = "rollpig"

        svc = get_service()

        if cmd in LIST_COMMANDS:
            img = await run_sync(svc.render_pig_list_image)
            if img:
                return PluginResult(text="小猪图鉴", image_path=img)
            return "图鉴渲染失败，请检查资源文件。"

        if cmd not in COMMANDS and cmd != "rollpig":
            return None

        others = [m for m in ctx.mentioned_openids if m != ctx.user_key]
        if len(others) > 1:
            return "一次只能抽取一个小猪哦！"
        target = others[0] if others else ctx.user_key

        text, img = await run_sync(svc.draw_pig, ctx.user_key, target)
        if img:
            return PluginResult(text=text, image_path=img)
        return text
