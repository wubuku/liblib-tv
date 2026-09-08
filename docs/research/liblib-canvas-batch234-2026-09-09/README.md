# Batch 234 — Agent 抽屉模型选择器完整目录

## 源站事实（窗口 rAF ~31fps；`source-agent-models-full.json` / 截图存档）

- Agent 抽屉模型选择器弹出 **15 项模型目录**（370×384 弹窗）：
  - **图片模型（7 项）**：Lib Image / General image Pro / General image V2 / Seedream 5.0 Pro / Style Image V8.2 / Style Image V8.1 / Style Image V7
  - **视频模型（8 项）**：Seedance 2.5 / Seedance 2.0 VIP / Minimax H3 / Seedance 2.0 Fast VIP / Wan 3.0 Prime / Wan 3.0 / Kling O3 / Kling 3.0
  - 每项含缩略图（远端 CDN）+ 名称 + 描述
- 选择模型按钮位于 Agent 抽屉 footer（32×32，aria-label=选择模型）
- 弹窗 370×384，从 footer 上方弹出

## 验收

- `verify-liblib-batch234.py`：12 checks
- 采样数据 JSON/截图存档于本目录
- 源站测试节点清理：待清理
