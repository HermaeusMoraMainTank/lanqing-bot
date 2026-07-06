# -*- coding: utf-8 -*-
"""群成员 openid 追踪（官方 Bot 无群成员列表 API 时的替代方案）。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GroupTracker:
    """记录群内出现过（发过 @ 消息）的成员 openid。"""

    _members: dict[str, set[str]] = field(default_factory=dict)

    def record(self, group_openid: str, member_openid: str) -> None:
        if not group_openid or not member_openid:
            return
        self._members.setdefault(group_openid, set()).add(member_openid)

    def members(self, group_openid: str) -> set[str]:
        return set(self._members.get(group_openid, set()))

    def others(
        self,
        group_openid: str,
        *,
        exclude: set[str] | None = None,
        allocated: set[str] | None = None,
    ) -> list[str]:
        exclude = exclude or set()
        allocated = allocated or set()
        pool = [
            m
            for m in self.members(group_openid)
            if m not in exclude and m not in allocated
        ]
        return pool


_tracker = GroupTracker()


def get_group_tracker() -> GroupTracker:
    return _tracker
