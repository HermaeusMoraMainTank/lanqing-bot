---
name: lanqing-bot-dev
description: >-
  Develop plugins for 蓝晴-bot QQ official robot (botpy). Use when adding
  features, writing plugins, configuring QQ open platform commands/services,
  or working in the lanqing-bot project.
---

# 蓝晴-bot 开发规范

## 项目架构

```
plugins/{name}/
  plugin.py        # 继承 BasePlugin
  manifest.yaml    # 插件元数据
  platform.yaml    # QQ 开放平台配置文档（必写）
bot/plugin/        # 插件基类与注册器
bot/handlers/      # 消息入口（勿改业务逻辑）
config/config.yaml # 凭证（gitignore，勿提交）
```

## 新增插件流程（必须逐步完成）

1. **复制模板**：`plugins/_template/` → `plugins/{your_plugin}/`
2. **实现 plugin.py**：继承 `BasePlugin`，定义 `triggers` 和 `on_message()`
3. **填写 manifest.yaml**：name / version / description / main / class
4. **填写 platform.yaml**：字段与官网表单一一对应（见 `docs/官网配置清单.md`）
5. **更新 `docs/官网配置清单.md`**：追加汇总表格
6. **更新 basic 插件**：在 `plugins/basic/plugin.py` 的 `_HELP` 中追加新指令
7. **验证**：`python -m py_compile plugins/{name}/plugin.py` 后重启 `python main.py`
8. **交付用户**：将 `platform.yaml` 及 `docs/官网配置清单.md` 对应段落发给用户

## 插件代码规范

```python
from bot.plugin.base import BasePlugin, MessageContext
from typing import Optional

class MyPlugin(BasePlugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "一句话描述"
    triggers = ["触发词", "alias"]

    def on_message(self, ctx: MessageContext) -> Optional[str]:
        # ctx.text      去 @ 后的纯文本
        # ctx.user_key  用户 openid（人品等每日计算用）
        # ctx.scene     group | guild | c2c
        # ctx.message   原始消息，富媒体回复时用
        return "回复文本"
```

约束：

- 业务逻辑只写在 `plugins/`，不要改 `bot/handlers/message.py`
- 插件数据放 `plugins/{name}/data/`，不要放根目录
- 中文触发词精确匹配；英文别名大小写不敏感
- 纯文字回复用 `return str`；富媒体在 handler 层扩展（暂不支持在插件内直接 reply 图片）
- 每个插件**必须**有 `platform.yaml`

## platform.yaml 规范（与官网表单一一对应）

每个插件的 `platform.yaml` **必须**使用官网表单字段名，方便直接复制：

```yaml
服务配置: 无需配置          # 或有小程序时写 服务列表

指令列表:
  - ID: 1
    指令名: 今日人品        # 不带斜杠
    指令介绍: 查看今日人品值
    权限菜单: 所有人
    使用场景:
      - QQ群
    是否传参: 否
```

新增插件后 **同步更新** `docs/官网配置清单.md` 汇总表。

### 服务配置字段（功能配置 → 服务配置）

| 字段 | 填写说明 |
|------|---------|
| ID | 序号 |
| 名称 | ≤5 字 |
| 介绍 | ≤15 字 |
| appID | 小程序 ID |
| path | 小程序路径 |
| extendData | 群聊留空 |
| 权限菜单 | 所有人 |
| 使用场景 | 勾选 QQ群 等 |

### 指令配置字段（功能配置 → 指令配置）

| 字段 | 填写说明 |
|------|---------|
| ID | 序号 |
| 指令名 | 不带 `/` |
| 指令介绍 | ≤15 字 |
| 权限菜单 | 所有人 |
| 使用场景 | 勾选 QQ群 等 |
| 是否传参 | 否（无参数指令） |

**文字指令 vs 服务配置**：

- `@机器人 今日人品` → 只填 **指令配置**，服务配置跳过
- 跳转小程序 → 才填 **服务配置**

## 现有插件

| 插件 | 触发词 | platform.yaml |
|------|--------|----------------|
| basic | 帮助 / ping / 你好 | `plugins/basic/platform.yaml` |
| jrrp | 今日人品 / jrrp | `plugins/jrrp/platform.yaml` |
| tarot | 占卜 | `plugins/tarot/platform.yaml` |
| rollpig | 今日小猪 / 抽小猪 / 小猪图鉴 | `plugins/rollpig/platform.yaml` |
| roulette | 轮盘赌 / 午时已到 | `plugins/roulette/platform.yaml` |
| waifu | 今日老婆 / 群老婆列表 | `plugins/waifu/platform.yaml` |
| anime_waifu | 今日二次元老婆 | `plugins/anime_waifu/platform.yaml` |
| phoebe | 菲比搜索（带参） | `plugins/phoebe/platform.yaml` |
| fortune | 今日运势 / 运势 / 今日doro | `plugins/fortune/platform.yaml` |
| workclock | 打卡 / 上班 / 下班 | `plugins/workclock/platform.yaml` |

## 官网配置文档

- 汇总清单（直接复制填写）：`docs/官网配置清单.md`
- 各插件独立配置单：`plugins/{name}/platform.yaml`
