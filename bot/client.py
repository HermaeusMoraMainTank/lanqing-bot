# -*- coding: utf-8 -*-
import botpy
from botpy import logging
from botpy.message import C2CMessage, GroupMessage, Message

from bot.handlers import message as message_handler
from bot.plugin.registry import get_registry

_log = logging.get_logger()


class LanqingBot(botpy.Client):
    """蓝晴 QQ 机器人主 Client。"""

    async def on_ready(self):
        registry = get_registry()
        names = ", ".join(p.name for p in registry.plugins)
        _log.info("机器人「%s」已上线，已加载插件: %s", self.robot.name, names)

    async def on_at_message_create(self, message: Message):
        await message_handler.handle_at_message(self, message)

    async def on_group_at_message_create(self, message: GroupMessage):
        await message_handler.handle_group_at_message(self, message)

    async def on_c2c_message_create(self, message: C2CMessage):
        await message_handler.handle_c2c_message(self, message)
