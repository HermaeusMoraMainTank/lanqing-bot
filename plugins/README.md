# 插件目录

每个功能以独立插件形式放在此目录，启动时自动加载（跳过 `_` 开头的目录）。

## 结构

```
plugins/{name}/
  plugin.py       # 业务逻辑
  manifest.yaml   # 元数据
  platform.yaml   # QQ 开放平台配置说明（给开发者对照官网填写）
  data/           # 可选，插件私有数据
```

## 现有插件

| 目录 | 功能 | 触发词 |
|------|------|--------|
| basic | 基础指令 | 帮助 / ping / 你好 |
| jrrp | 今日人品 | 今日人品 / jrrp |
| tarot | 塔罗占卜 | 占卜 |

## 新增插件

1. 复制 `plugins/_template/`
2. 阅读 `.cursor/skills/lanqing-bot-dev/SKILL.md`

## 官网配置

每个插件的 `platform.yaml` 说明该功能在 QQ 开放平台需要填写的指令、服务和事件。

**可直接复制填写的汇总表：** `docs/官网配置清单.md`
