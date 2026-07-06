# -*- coding: utf-8 -*-
from botpy import logging
from botpy.message import C2CMessage

from bot.commands.basic import match_command

_log = logging.get_logger()


async def handle_c2c_message(client, message: C2CMessage) -> None:
    text = (message.content or "").strip()
    _log.info("[单聊] %s: %s", message.author.user_openid, text)

    reply = match_command(text)
    if reply is None:
        reply = f"你好，我是 {client.robot.name}！发送「帮助」查看可用指令。"

    await message.reply(content=reply)
