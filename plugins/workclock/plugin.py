# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply, PluginResult
from bot.utils.async_util import run_sync
from bot.utils.group_track import get_group_tracker

from .service import _CLOCK_IN, _CLOCK_OUT, get_service


class WorkClockPlugin(BasePlugin):
    name = "workclock"
    version = "1.0.0"
    description = "上下班打卡"
    triggers = list(_CLOCK_IN) + list(_CLOCK_OUT) + ["群上班列表"]

    def match(self, text: str) -> bool:
        cmd = text.strip()
        if cmd == "群上班列表":
            return True
        for trigger in _CLOCK_OUT + _CLOCK_IN:
            if cmd == trigger or cmd.startswith(trigger):
                return True
        return False

    async def on_message(self, ctx: MessageContext) -> PluginReply:
        tracker = get_group_tracker()
        nickname = tracker.display_name(ctx.group_openid, ctx.user_key)
        text, img = await run_sync(
            get_service().handle,
            ctx.text.strip(),
            ctx.user_key,
            ctx.group_openid,
            nickname=nickname,
        )
        if img:
            return PluginResult(text=text, image_path=img)
        return text
