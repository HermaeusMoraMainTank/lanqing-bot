# -*- coding: utf-8 -*-
from botpy.message import C2CMessage, GroupMessage, Message

from bot.handlers.context import (
    from_c2c_message,
    from_group_message,
    from_guild_message,
)
from bot.media.group import reply_with_image
from bot.plugin.registry import get_registry
from bot.plugin.result import PluginResult
from bot.utils.async_util import run_sync
from bot.utils.event_log import ctx_log_fields, format_ctx_summary, format_reply_summary
from bot.utils.logger import get_log

_log = get_log("lanqing.handler")
_FALLBACK = "发送「帮助」查看可用指令。"


async def _safe_error_reply(message, log) -> None:
    try:
        await message.reply(content="处理失败，请稍后再试。")
        log.warning("已发送错误提示给用户")
    except Exception:
        log.exception("发送错误提示失败")


async def _reply(message, reply, robot_name: str, log) -> None:
    if reply is None:
        log.info("无匹配插件，发送默认问候")
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
                log.info("回复已发送 type=media image=%s text_len=%d", images[0].name, len(reply.text or ""))
                msg_seq += 1
                for idx, extra in enumerate(images[1:], start=2):
                    await reply_with_image(message, f"图 {idx}", extra, msg_seq=msg_seq)
                    log.info("回复已发送 type=media extra_image=%s seq=%d", extra.name, msg_seq)
                    msg_seq += 1
                return
            except Exception:
                log.exception("发送图片失败，尝试降级纯文字")
                if msg_seq > 1:
                    return
        try:
            await message.reply(content=reply.text, msg_seq=1)
            log.info("回复已发送 type=text len=%d", len(reply.text or ""))
        except Exception:
            log.exception("发送纯文字回复失败")
            raise
        return

    try:
        await message.reply(content=reply or f"你好，我是 {robot_name}！{_FALLBACK}")
        log.info("回复已发送 type=text len=%d", len(str(reply or "")))
    except Exception:
        log.exception("发送文字回复失败")
        raise


async def _handle_message(build_ctx, message, robot_name: str) -> None:
    ctx = None
    try:
        ctx = await run_sync(build_ctx)
    except Exception:
        msg_id = getattr(message, "id", "?")
        _log.exception("构建消息上下文失败 msg_id=%s", msg_id)
        return

    log = _log.bind(**ctx_log_fields(ctx))
    log.info("收到消息 | %s", format_ctx_summary(ctx))

    try:
        result = await get_registry().dispatch(ctx)
        if result.plugin:
            log.info(
                "调度完成 | plugin=%s elapsed=%.0fms | %s",
                result.plugin,
                result.elapsed_ms,
                format_reply_summary(result.reply, plugin=result.plugin),
            )
        else:
            log.debug("无插件匹配指令=%r", ctx.text)
        await _reply(message, result.reply, robot_name, log)
    except Exception:
        log.exception("处理消息失败 | %s", format_ctx_summary(ctx))
        await _safe_error_reply(message, log)


async def handle_at_message(client, message: Message) -> None:
    await _handle_message(
        lambda: from_guild_message(client, message),
        message,
        client.robot.name,
    )


async def handle_group_at_message(client, message: GroupMessage) -> None:
    await _handle_message(
        lambda: from_group_message(client, message),
        message,
        client.robot.name,
    )


async def handle_c2c_message(client, message: C2CMessage) -> None:
    await _handle_message(
        lambda: from_c2c_message(client, message),
        message,
        client.robot.name,
    )
