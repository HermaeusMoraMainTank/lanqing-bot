# -*- coding: utf-8 -*-
import botpy
from botpy import logging
from botpy.message import C2CMessage, GroupMessage, Message

from bot.handlers import c2c as c2c_handler
from bot.handlers import group as group_handler
from bot.handlers import guild as guild_handler

_log = logging.get_logger()


class LanqingBot(botpy.Client):
    """蓝晴 QQ 机器人主 Client。"""

    async def on_ready(self):
        _log.info("机器人「%s」已上线", self.robot.name)

    async def on_at_message_create(self, message: Message):
        await guild_handler.handle_at_message(self, message)

    async def on_group_at_message_create(self, message: GroupMessage):
        await group_handler.handle_group_at_message(self, message)

    async def on_c2c_message_create(self, message: C2CMessage):
        await c2c_handler.handle_c2c_message(self, message)
