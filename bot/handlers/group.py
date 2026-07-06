# -*- coding: utf-8 -*-
from botpy import logging
from botpy.message import GroupMessage

from bot.commands.basic import match_command, strip_mention

_log = logging.get_logger()


async def handle_group_at_message(client, message: GroupMessage) -> None:
    text = strip_mention(message.content)
    _log.info("[群聊] %s: %s", message.author.member_openid, text)

    reply = match_command(text)
    if reply is None:
        reply = f"你好，我是 {client.robot.name}！发送「帮助」查看可用指令。"

    await message.reply(content=reply)
