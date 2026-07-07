# QQ 官方 Bot · 用户头像（隐藏接口）

> **未在 QQ 开放平台公开文档中列出**，实测可用。  
> 记录日期：2026-07-07

## URL 格式

```
https://thirdqq.qlogo.cn/qqapp/{appid}/{openid}/0
```

| 占位符 | 说明 |
|--------|------|
| `appid` | 机器人 AppID（`config.yaml` → `appid`） |
| `openid` | 用户 openid（群聊 `member_openid`，单聊 `user_openid`） |
| `/0` | 尺寸参数（末尾数字，实测 `0` 可用） |

### 示例

```
https://thirdqq.qlogo.cn/qqapp/102149693/9660CACF968538D1AB9F5C08DAEDC05F/0
```

## 代码调用

```python
from bot.utils.avatar import avatar_url, load_avatar, download_avatar

url = avatar_url(member_openid)          # 仅拼 URL
path = download_avatar(member_openid)    # 下载到 data/avatar_cache/
img = load_avatar(member_openid, 48)     # PIL 圆形头像，失败自动占位
```

## 限制

- ✅ **用户**头像（member_openid / user_openid）
- ❌ **群**头像（无对应接口）
- ❌ 无法替代 NcatBot 时代基于 QQ 号的 `q1.qlogo.cn` 群成员批量拉取

## 使用场景

- WorkClock 打卡卡片左上角头像
- 今日老婆 抽签结果配图
- 其他需要展示群友头像的 PIL 合成

缓存目录：`data/avatar_cache/`（已 gitignore）
