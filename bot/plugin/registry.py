# -*- coding: utf-8 -*-
import importlib.util
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from bot.utils.event_log import ctx_log_fields, format_ctx_summary, format_reply_summary
from bot.utils.logger import get_log
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply

_log = get_log("lanqing.plugin")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PLUGINS_DIR = ROOT_DIR / "plugins"


@dataclass(frozen=True)
class DispatchResult:
    reply: PluginReply
    plugin: str | None = None
    elapsed_ms: float = 0.0


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: list[BasePlugin] = []

    @property
    def plugins(self) -> list[BasePlugin]:
        return list(self._plugins)

    def load_all(self, plugins_dir: Path = PLUGINS_DIR) -> None:
        self._plugins.clear()
        if not plugins_dir.is_dir():
            _log.warning("插件目录不存在: %s", plugins_dir)
            return

        for folder in sorted(plugins_dir.iterdir()):
            if not folder.is_dir() or folder.name.startswith("_"):
                continue
            manifest_path = folder / "manifest.yaml"
            if not manifest_path.exists():
                _log.warning("跳过无 manifest 的目录: %s", folder.name)
                continue
            plugin = self._load_plugin(folder, manifest_path)
            if plugin:
                self._plugins.append(plugin)
                _log.info("已加载插件 %s v%s", plugin.name, plugin.version)

    def _load_plugin(self, folder: Path, manifest_path: Path) -> Optional[BasePlugin]:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f) or {}

        module_name = manifest.get("main", "plugin.py")
        class_name = manifest.get("class", "Plugin")
        module_path = folder / module_name

        spec = importlib.util.spec_from_file_location(
            f"plugins.{folder.name}",
            module_path,
            submodule_search_locations=[str(folder)],
        )
        if spec is None or spec.loader is None:
            _log.error("无法加载插件模块: %s", module_path)
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin_cls = getattr(module, class_name)
        plugin = plugin_cls()
        plugin.name = manifest.get("name", plugin.name)
        plugin.version = manifest.get("version", plugin.version)
        plugin.description = manifest.get("description", plugin.description)
        return plugin

    async def dispatch(self, ctx: MessageContext) -> DispatchResult:
        for plugin in self._plugins:
            if not plugin.match(ctx.text):
                continue
            plog = _log.bind(plugin=plugin.name, **ctx_log_fields(ctx))
            plog.info("开始处理 | %s", format_ctx_summary(ctx))
            started = time.perf_counter()
            try:
                reply = await plugin.on_message(ctx)
            except Exception:
                plog.exception("插件处理异常 | %s", format_ctx_summary(ctx))
                raise
            elapsed_ms = (time.perf_counter() - started) * 1000
            plog.info(
                "处理完成 elapsed=%.0fms | %s",
                elapsed_ms,
                format_reply_summary(reply, plugin=plugin.name),
            )
            return DispatchResult(reply=reply, plugin=plugin.name, elapsed_ms=elapsed_ms)
        return DispatchResult(reply=None)


_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.load_all()
    return _registry
