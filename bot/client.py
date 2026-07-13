# -*- coding: utf-8 -*-
import botpy
from botpy.message import C2CMessage, GroupMessage, Message

from bot.handlers import message as message_handler
from bot.plugin.registry import get_registry
from bot.utils.logger import get_log

_log = get_log("lanqing.client")


class LanqingBot(botpy.Client):
    """蓝晴 QQ 机器人主 Client。"""

    async def on_ready(self):
        registry = get_registry()
        names = ", ".join(p.name for p in registry.plugins)
        _log.info("机器人「%s」已上线 | plugins=%s", self.robot.name, names)

    async def on_at_message_create(self, message: Message):
        try:
            await message_handler.handle_at_message(self, message)
        except Exception:
            _log.exception(
                "频道消息未捕获异常 | msg_id=%s guild=%s channel=%s",
                message.id,
                message.guild_id,
                message.channel_id,
            )

    async def on_group_at_message_create(self, message: GroupMessage):
        try:
            await message_handler.handle_group_at_message(self, message)
        except Exception:
            _log.exception(
                "群聊消息未捕获异常 | msg_id=%s group=%s",
                message.id,
                message.group_openid,
            )

    async def on_c2c_message_create(self, message: C2CMessage):
        try:
            await message_handler.handle_c2c_message(self, message)
        except Exception:
            _log.exception(
                "单聊消息未捕获异常 | msg_id=%s user=%s",
                message.id,
                getattr(message.author, "user_openid", "?"),
            )
