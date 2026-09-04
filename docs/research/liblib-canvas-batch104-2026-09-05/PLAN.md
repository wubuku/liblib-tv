# Batch 104 Plan：故事板空态三组对齐 2026-09-05 源站

> 状态：`PLANNED`
>
> 建档日期：2026-09-05。
>
> 上一批 checkpoint：Batch 103（`batch/103-mode-toggle-source`）。
>
> 源站证据：[`../liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §5（故事板模式空画布 DOM：文本/图片/视频 三组 banner + 暂无文案 + 放大图片/放大视频 按钮）。

## 1. 范围

### 包含

1. **主区三列**（`SOURCE_FACT`）：故事板主区列顺序 文本/图片/视频；新增 文本 列（script 节点投影，与关键元素同源数据）。
2. **放大按钮**（`SOURCE_FACT` 按钮 + `CLONE_DECISION` 行为）：图片/视频列头新增 `放大图片`/`放大视频` 按钮；点击行为源站未采样，本批不加 handler（可见入口，行为 `SOURCE_UNKNOWN`）。
3. **空态文案**（`SOURCE_FACT`）：列空态 `当前画布暂无X素材` → `暂无文本/暂无图片/暂无视频`。
4. **空画布隐藏关键元素侧栏**（`SOURCE_FACT`+`CLONE_DECISION`）：源站空画布故事板只有三组 banner、无侧栏；clone 在 图片+文本 关键元素均为空时隐藏侧栏，非空时保留既有侧栏（非空源站行为未采样）。

### 不包含

- 放大按钮真实行为、非空画布源站布局、卡片视觉重设计；
- StoryboardMediaCard / 关键元素卡片内部结构。

## 2. 证据边界

| 标签 | 内容 |
|---|---|
| `SOURCE_FACT` | 三组顺序 文本/图片/视频、`暂无文本/暂无图片/暂无视频`、`放大图片/放大视频` 按钮存在、空画布无侧栏 |
| `CLONE_DECISION` | 侧栏隐藏阈值（图片+文本均空）、文本列数据投影复用 script 节点 |
| `SOURCE_UNKNOWN` | 放大按钮点击行为、非空画布源站是否有关键元素侧栏、banner 几何 |

## 3. 影响面与兼容

- 仅 `src/components/StoryboardBoard.tsx`；
- batch13 断言 demo 画布 key-groups/columns 卡片计数（5/1/5/1）不受影响（复跑确认）；batch14 断言 board 可见性不受影响。

## 4. 验证

- 新增 `scripts/verify-liblib-batch104.py`：desktop `1440x900`，demo 画布断言三列与放大按钮、侧栏可见、卡片计数不变；切 `canvas-1` 断言侧栏隐藏 + 三个暂空文案；返回工作流 graph 保持；零诊断。
- 复跑 `verify-liblib-batch13.py`、`verify-liblib-batch14.py`。
- `npm run check`、`npm run docs:check`。

## 5. 完成定义

1. 空画布故事板与源站三组结构一致；demo 画布投影不变。
2. 相邻 verifier 与全量检查通过；特性分支 commit/push。
