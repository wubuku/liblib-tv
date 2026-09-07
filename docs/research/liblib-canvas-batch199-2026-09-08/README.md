# Batch 199 — Agent 抽屉重采 + 第四句 Skill 标题

## 源站事实（窗口 rAF ~31fps；`source-agent-drawer.json` / `source-empty-chips.json` / 截图已存档）

- 点击顶栏 Agent 按钮打开右侧抽屉（今日视口 1920 下宽约 427）。
- **Skill 就位区**：标题「Skill 就位，ready when you are」+ 换一批按钮
  （68×24）+ 2×2 Skill 卡（180×62，缩略图 + 名称 20px + 路径 15px）。
  四张卡与 clone Batch 97 记录的第一批**完全一致**（皮克斯动画广告/
  pixar-animated-ad-creator、爆款拉片复刻/viral-video-replicator、
  新中式美学TVC/neo-chinese-aesthetic-tvc、古典武侠电影全流程导演/
  hujinquanwuxia）——97 记录互证复验。
- 浏览器通知横幅「开启浏览器通知，及时获取最新消息 开启 ×」——clone
  文案已一致。
- **第四句标题**：「Skill 就位，ready when you are」不在 Batch 107 的
  三句轮换中——本次直采加入。
- 空画布快捷芯片（同屏直采）：故事脚本生成 / 角色三视图（240×56）；
  全能参考视频 / 音频生成视频带 SD 2.5 徽标（截图可见）。

## 实施

- `AgentDrawer` skillHeadlines 轮换加入第四句；batch107 的 HEADLINES
  同步（轮换机制合同：换一批推进 + 环绕）。
- 抽屉宽度：源站 1920 视口下约 427 vs clone 固定 340——单样本不足以
  断定流式规则，记开放问题。

## 验收

- `verify-liblib-batch199.py`：9 checks（抽屉打开/横幅文案/第四句在
  轮换中/换一批收集到 ≥3 句/四张 Skill 卡文案/0 page error）。
- 回归绿：22 / 107（轮换两跑）/ 121 / 172 / 198。
- `npm run check`：0 errors（8 warnings 基线）。
- 不证明：抽屉宽度的流式规则；第四句之外的更多标题变体；Skill 卡
  点击后的会话行为。
- 源站测试残留清理：0 残留。
