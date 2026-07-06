# -*- coding: utf-8 -*-
from botpy import logging
from botpy.message import Message

from bot.commands.basic import match_command, strip_mention

_log = logging.get_logger()


async def handle_at_message(client, message: Message) -> None:
    text = strip_mention(message.content)
    _log.info("[频道] %s: %s", message.author.username, text)

    reply = match_command(text)
    if reply is not None:
        await message.reply(content=reply)
        return

    await message.reply(
        content=f"你好，我是 {client.robot.name}！发送「帮助」查看可用指令。"
    )
