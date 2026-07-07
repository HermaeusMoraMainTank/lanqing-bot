# -*- coding: utf-8 -*-
from botpy import logging
from botpy.message import C2CMessage, GroupMessage, Message

from bot.handlers.context import (
    from_c2c_message,
    from_group_message,
    from_guild_message,
)
from bot.media.group import reply_with_image
from bot.plugin.registry import get_registry
from bot.plugin.result import PluginResult

_log = logging.get_logger()
_FALLBACK = "发送「帮助」查看可用指令。"


async def _reply(message, reply, robot_name: str) -> None:
    if reply is None:
        await message.reply(content=f"你好，我是 {robot_name}！{_FALLBACK}")
        return

    if isinstance(reply, PluginResult):
        images = []
        if reply.image_path and reply.image_path.exists():
            images.append(reply.image_path)
        for path in reply.image_paths:
            if path.exists() and path not in images:
                images.append(path)
        if images:
            msg_seq = 1
            try:
                await reply_with_image(message, reply.text, images[0], msg_seq=msg_seq)
                msg_seq += 1
                for idx, extra in enumerate(images[1:], start=2):
                    await reply_with_image(message, f"图 {idx}", extra, msg_seq=msg_seq)
                    msg_seq += 1
                return
            except Exception as exc:
                _log.error("发送图片失败，降级为纯文字: %s", exc)
                if msg_seq > 1:
                    return
        await message.reply(content=reply.text, msg_seq=1)
        return

    await message.reply(content=reply or f"你好，我是 {robot_name}！{_FALLBACK}")


async def handle_at_message(client, message: Message) -> None:
    ctx = from_guild_message(client, message)
    _log.info("[频道] %s: %s", ctx.display_name, ctx.text)
    await _reply(message, get_registry().dispatch(ctx), client.robot.name)


async def handle_group_at_message(client, message: GroupMessage) -> None:
    ctx = from_group_message(client, message)
    _log.info("[群聊] %s: %s", ctx.user_key, ctx.text)
    await _reply(message, get_registry().dispatch(ctx), client.robot.name)


async def handle_c2c_message(client, message: C2CMessage) -> None:
    ctx = from_c2c_message(client, message)
    _log.info("[单聊] %s: %s", ctx.user_key, ctx.text)
    await _reply(message, get_registry().dispatch(ctx), client.robot.name)
