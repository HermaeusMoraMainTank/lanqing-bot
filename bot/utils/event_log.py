# -*- coding: utf-8 -*-
"""消息与回复日志摘要（参考 NcatBot event_log，适配 QQ 官方 Bot 字段）。"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bot.plugin.base import MessageContext
    from bot.plugin.result import PluginReply

_SCENE_LABEL = {
    "group": "群聊",
    "guild": "频道",
    "c2c": "单聊",
}

_ROLE_LABEL = {
    "owner": "群主",
    "admin": "管理员",
    "member": "成员",
}


def short_id(value: str, *, tail: int = 8) -> str:
    value = (value or "").strip()
    if not value or value == "unknown":
        return "unknown"
    if len(value) <= tail + 3:
        return value
    return f"...{value[-tail:]}"


def truncate_text(text: str, max_len: int = 120) -> str:
    text = (text or "").replace("\n", "\\n").replace("\r", "")
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def format_ctx_summary(ctx: MessageContext) -> str:
    """人类可读的消息摘要。官方 Bot 无群名/群号，用 openid 缩写。"""
    scene = _SCENE_LABEL.get(ctx.scene, ctx.scene)
    user = f"{ctx.display_name}({short_id(ctx.user_key)})"
    if ctx.member_role:
        role = _ROLE_LABEL.get(ctx.member_role, ctx.member_role)
        user = f"{user}[{role}]"

    text = truncate_text(ctx.text)
    meta = f"msg={short_id(ctx.msg_id, tail=10)}"
    if ctx.timestamp:
        meta += f" ts={ctx.timestamp}"

    if ctx.scene == "group":
        loc = f"群{short_id(ctx.group_openid, tail=12)}"
        return f"[{scene}] {loc} {user} | {meta} | {text}"

    if ctx.scene == "guild":
        loc = f"频道{short_id(ctx.guild_id)}/子频道{short_id(ctx.channel_id)}"
        return f"[{scene}] {loc} {user} | {meta} | {text}"

    return f"[{scene}] {user} | {meta} | {text}"


def ctx_log_fields(ctx: MessageContext) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "scene": ctx.scene,
        "user": ctx.display_name,
        "user_id": short_id(ctx.user_key),
        "msg_id": ctx.msg_id,
    }
    if ctx.group_openid:
        fields["group_id"] = short_id(ctx.group_openid, tail=12)
    if ctx.guild_id:
        fields["guild_id"] = short_id(ctx.guild_id)
    if ctx.channel_id:
        fields["channel_id"] = short_id(ctx.channel_id)
    if ctx.member_role:
        fields["role"] = ctx.member_role
    return fields


def format_reply_summary(reply: PluginReply, *, plugin: str | None = None) -> str:
    from bot.plugin.result import PluginResult

    parts: list[str] = []
    if plugin:
        parts.append(f"plugin={plugin}")
    if reply is None:
        parts.append("reply=fallback")
        return " ".join(parts)
    if isinstance(reply, PluginResult):
        parts.append("type=media")
        parts.append(f"text_len={len(reply.text or '')}")
        if reply.image_path:
            parts.append(f"image={reply.image_path.name}")
        extra = len(reply.image_paths or [])
        if extra:
            parts.append(f"extra_images={extra}")
        return " ".join(parts)
    parts.append("type=text")
    parts.append(f"len={len(str(reply))}")
    return " ".join(parts)
