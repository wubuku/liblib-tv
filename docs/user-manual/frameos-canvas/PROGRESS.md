# FrameOS 画布用户手册进度

## 基线

- 日期：2026-09-22
- 源站 URL：`https://www.frameos.cn/#/canvas/01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`
- 登录态：用户已登录，当前画布为 `画布 1`。
- 初始可访问性快照：页面为空态，显示“选择一种方式开始创作”，提供“文本”“图片”“视频”“音频”“3D导演台”“上传文件”六项入口。
- 初始控制：左上 breadcrumb、右侧“使用教程”、顶部“撤销/重做”、左侧工具栏、左下缩放/小地图/搜索/整理工具。
- 初始网络/console：console 有 2 条 warning，无 error；尚未把 warning 归因为产品缺陷。
- 获授权测试媒体：10 张 PNG、2 个 WAV、2 个 MP4，完整清单见 [`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)。
- 成本红线：允许上传和挂载测试媒体，不触发真实图片或视频生成。

## 阶段

| 阶段 | 状态 | 产出 |
|---|---|---|
| 方法论移植 | 已完成 | `.agents/skills/web-studio-user-manual/` |
| 候选任务确认 | 已完成 | `task-inventory.yml`，用户授权 Agent 自行定级 |
| 真实浏览器取证 | 准备就绪 | `SOURCE_OBSERVATIONS.md` readiness smoke；正式逐任务取证尚未开始 |
| 正式正文与截图 | 未开始 | `10-tasks/`、`screenshots/manifest.yml` |
| Gate A 机械审计 | 未开始 | `audit_manual.py --phase gate-a` |
| Gate B 回走审计 | 未开始 | `AUDIT.md`、`audit_manual.py --phase final` |

## 恢复入口

从本文件读取当前阶段，再打开 [`task-inventory.yml`](task-inventory.yml) 和 [`AUDIT.md`](AUDIT.md)；不要依赖会话记忆恢复任务状态。

## 准备就绪检查

- 方法论、优先级规则、浏览器取证、截图和 Gate A/Gate B 规则均已随技能自包含落地。
- 任务库存、成本红线、测试媒体路径、截图 hash 和观察证据均已留档。
- 下一步从 `create-first-node` 开始逐任务探索；在获得新指令前停止。
