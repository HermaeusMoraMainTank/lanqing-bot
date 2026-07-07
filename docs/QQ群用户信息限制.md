# QQ 群 · 用户信息 API 调研结论

> 调研日期：2026-07-07  
> 官方文档：https://bot.q.qq.com/wiki/develop/api-v2/

## 结论：**QQ 群聊无法通过官方 API 获取群友昵称**

与 NcatBot（OneBot / go-cqhttp）的 `get_group_member_list` / `get_group_member_info` 不同，**QQ 官方 Bot 的群聊模块没有提供**：

- 群成员列表接口
- 按 `member_openid` 查询用户资料接口
- 消息事件里的昵称 / 群名片字段

### 群消息 `author` 仅有 3 个字段

来源：[事件 · 群聊@机器人](https://bot.q.qq.com/wiki/develop/api-v2/server-inter/message/send-receive/event.html)

| 字段 | 说明 |
|------|------|
| `member_openid` | 用户在本群的唯一 ID（换群会变） |
| `member_role` | `owner` / `admin` / `member` |
| `bot` | 是否机器人 |

**没有** `nickname`、`card`、`username` 等字段。

### 群组模块文档

[群组模块](https://bot.q.qq.com/wiki/develop/api-v2/server-inter/group/) 目前仅列出破冰消息等配置项，**无 REST 查询成员资料**。

### botpy 已实现的群相关 API

仅消息发送与文件上传：

- `POST /v2/groups/{group_openid}/messages`
- `POST /v2/groups/{group_openid}/files`

### 频道 vs 群聊（勿混淆）

| 场景 | 用户标识 | 昵称 API |
|------|----------|----------|
| **QQ 群聊** | `member_openid` | ❌ 无 |
| **QQ 频道** | `user.id` | ✅ `GET /guilds/{guild_id}/members/{user_id}` 含 `nick` |

频道成员模型见：[Member 对象](https://bot.q.qq.com/wiki/develop/api-v2/server-inter/channel/role/member/model.html)

---

## 蓝晴-bot 采用的替代方案

因官方不提供昵称，项目内使用以下方式：

### 1. 用户自助：`@机器人 设置昵称 某某某`

写入 `data/nickname_map.json`，在本群显示为自定义昵称。

### 2. 配置文件：`config.yaml` → `nickname_overrides`

```yaml
nickname_overrides:
  "9660CACF968538D1AB9F5C08DAEDC05F": "小明"
```

键为 **member_openid**（本群内 ID）。

### 3. 身份兜底

未设置昵称时，按 `member_role` 显示：

- `owner` → 群主
- `admin` → 管理员
- 其他 → `群友xxxx`（openid 末 4 位）

### 4. 头像（隐藏接口，与昵称无关）

见 [QQ头像API.md](./QQ头像API.md) — 可拉用户头像，**不能**拉昵称。

---

## 与 NcatBot 功能差异

| 功能 | NcatBot | 官方 Bot |
|------|---------|----------|
| 今日老婆随机群友 | 全群成员列表 | 仅 `@` 过机器人的成员 |
| 群老婆列表昵称 | QQ 昵称/群名片 | 自建昵称 / 身份兜底 |
| 上班列表昵称 | 群成员昵称 | 同上 |

若需完全对齐 NcatBot 体验，只能继续用 OneBot 协议机器人，或等待腾讯开放群成员资料 API。
