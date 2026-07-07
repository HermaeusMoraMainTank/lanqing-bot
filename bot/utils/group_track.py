# -*- coding: utf-8 -*-
"""群成员 openid 追踪与昵称管理（官方 Bot 无群成员昵称 API）。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from bot.config import ROOT_DIR, load_config

NICKNAME_PATH = ROOT_DIR / "data" / "nickname_map.json"

_ROLE_LABEL = {
    "owner": "群主",
    "admin": "管理员",
}


@dataclass
class GroupTracker:
    """记录群内出现过的 member_openid，并维护自建昵称。"""

    _members: dict[str, set[str]] = field(default_factory=dict)
    _names: dict[str, dict[str, str]] = field(default_factory=dict)
    _roles: dict[str, dict[str, str]] = field(default_factory=dict)
    _loaded: bool = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if NICKNAME_PATH.exists():
            try:
                data = json.loads(NICKNAME_PATH.read_text("utf-8"))
                for gid, mapping in (data.get("by_group") or {}).items():
                    if isinstance(mapping, dict):
                        self._names[gid] = {str(k): str(v) for k, v in mapping.items()}
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        NICKNAME_PATH.parent.mkdir(parents=True, exist_ok=True)
        NICKNAME_PATH.write_text(
            json.dumps({"by_group": self._names}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _config_override(self, member_openid: str) -> str | None:
        overrides = load_config().get("nickname_overrides") or {}
        if not isinstance(overrides, dict):
            return None
        name = overrides.get(member_openid)
        return str(name).strip() if name else None

    def record(
        self,
        group_openid: str,
        member_openid: str,
        *,
        member_role: str | None = None,
    ) -> None:
        self._ensure_loaded()
        if not group_openid or not member_openid:
            return
        self._members.setdefault(group_openid, set()).add(member_openid)
        if member_role:
            self._roles.setdefault(group_openid, {})[member_openid] = member_role

    def set_nickname(self, group_openid: str, member_openid: str, nickname: str) -> None:
        self._ensure_loaded()
        nickname = nickname.strip()
        if not group_openid or not member_openid or not nickname:
            return
        if len(nickname) > 20:
            nickname = nickname[:20]
        self._names.setdefault(group_openid, {})[member_openid] = nickname
        self._members.setdefault(group_openid, set()).add(member_openid)
        self._save()

    def display_name(self, group_openid: str, member_openid: str) -> str:
        self._ensure_loaded()
        custom = self._names.get(group_openid, {}).get(member_openid)
        if custom:
            return custom
        override = self._config_override(member_openid)
        if override:
            return override
        role = self._roles.get(group_openid, {}).get(member_openid)
        if role in _ROLE_LABEL:
            return _ROLE_LABEL[role]
        if len(member_openid) > 8:
            return f"群友{member_openid[-4:]}"
        return member_openid or "群友"

    def members(self, group_openid: str) -> set[str]:
        self._ensure_loaded()
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
        return [
            m
            for m in self.members(group_openid)
            if m not in exclude and m not in allocated
        ]


_tracker = GroupTracker()


def get_group_tracker() -> GroupTracker:
    return _tracker
