# -*- coding: utf-8 -*-
import re

from bot.utils.group_track import get_group_tracker
from bot.utils.text import normalize_command
from bot.plugin.base import MessageContext, Scene
from botpy.message import C2CMessage, GroupMessage, Message

_MENTION_RE = re.compile(r"<@!?([^>]+)>")


def from_guild_message(client, message: Message) -> MessageContext:
    text = normalize_command(message.content or "")
    return MessageContext(
        text=text,
        raw_text=message.content or "",
        user_key=message.author.id or "unknown",
        display_name=message.author.username or "你",
        scene="guild",
        client=client,
        message=message,
        msg_id=message.id or "",
        timestamp=message.timestamp or "",
        event_id=message.event_id or "",
        guild_id=message.guild_id or "",
        channel_id=message.channel_id or "",
    )


def _extract_mentions(content: str) -> list[str]:
    return _MENTION_RE.findall(content or "")


def from_group_message(client, message: GroupMessage) -> MessageContext:
    raw = message.content or ""
    text = normalize_command(raw)
    author = message.author
    openid = getattr(author, "member_openid", None) or "unknown"
    role = getattr(author, "member_role", None) or ""
    group_openid = message.group_openid or ""
    mentions = _extract_mentions(raw)
    tracker = get_group_tracker()
    tracker.record(group_openid, openid, member_role=role or None)
    display = tracker.display_name(group_openid, openid)
    return MessageContext(
        text=text,
        raw_text=raw,
        user_key=openid,
        display_name=display,
        scene="group",
        client=client,
        message=message,
        group_openid=group_openid,
        mentioned_openids=mentions,
        msg_id=message.id or "",
        timestamp=message.timestamp or "",
        member_role=role,
        event_id=message.event_id or "",
    )


def from_c2c_message(client, message: C2CMessage) -> MessageContext:
    text = normalize_command(message.content or "")
    openid = message.author.user_openid or "unknown"
    return MessageContext(
        text=text,
        raw_text=message.content or "",
        user_key=openid,
        display_name=f"用户{openid[-4:]}" if len(openid) > 4 else "用户",
        scene="c2c",
        client=client,
        message=message,
        msg_id=message.id or "",
        timestamp=message.timestamp or "",
        event_id=message.event_id or "",
    )
