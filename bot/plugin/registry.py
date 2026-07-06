# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
from typing import Optional

import yaml
from botpy import logging

from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply

_log = logging.get_logger()
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PLUGINS_DIR = ROOT_DIR / "plugins"


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

    def dispatch(self, ctx: MessageContext) -> PluginReply:
        for plugin in self._plugins:
            if plugin.match(ctx.text):
                _log.info("[插件:%s] 处理 %s", plugin.name, ctx.text)
                return plugin.on_message(ctx)
        return None


_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.load_all()
    return _registry
