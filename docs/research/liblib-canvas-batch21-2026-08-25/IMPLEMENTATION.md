# Batch 21 实施结果：Seedance 视频参数 Dialog

> 状态：已完成并通过专项、跨批和生产构建验证。

## 1. 实施内容

### `src/components/VideoGenerationPanel.tsx`

- footer 增加 model/mode/params/advanced/credits 稳定 selectors。
- `ParamsMenu` 改为显式 normal/long 两种 geometry：
  - normal：`341x445`, trigger-relative `left -68`, `bottom 32`
  - long：`341x397`, trigger-relative `left -60`, `bottom 32`
- ratio 改为 7 个 `52px` 图标卡，按 5+2 grid 排列。
- resolution 改为三段整宽 control。
- duration 增加当前值框，保留 `onInput` slider。
- audio 和 count 改为整宽 segmented controls。
- long 模式隐藏 count，并增加时长 helper。
- 参数与积分仍为 component-local state。

### `scripts/verify-liblib-batch21.py`

- normal/long dialog 尺寸与相对 generation panel 几何。
- 7 ratios、3 resolutions、duration、2 audio、normal 3 count。
- 模式 disabled/enabled matrix。
- normal 参数交互和积分更新。
- long `30-300s`、无 count、helper、`300s / 14700`。
- desktop/mobile 截图、自然裁切、overflow、console/page error。

## 2. 证据边界

### Source fact

- normal/long rect、参数集合、long 无数量、模式 disabled 状态来自登录原站 DOM 与截图。

### Inference

- trigger-relative `left -68/-60`, `bottom 32` 是根据 source panel-relative rect 和 clone trigger 布局反推的实现参数。

### Clone-only decision

- CSS ratio outline 代替未提取的原站 SVG。
- long helper 是保守语义改写。
- 不扩充模型菜单，不实现生成或计费后端。

## 3. 专项验证

```bash
python3 scripts/verify-liblib-batch21.py
```

结果：通过。

- normal：`341x445`, relative `+81.828/-211.500`
- long：`341x397`, relative `+89.828/-163.500`
- controls、mode matrix、`300s / 14700`：通过
- 390px 裁切与页面 overflow：通过
- console/page error：0

截图：

- [normal](../../design-references/liblib-clone-batch21-video-params-normal-929-2026-08-25.png)
- [long](../../design-references/liblib-clone-batch21-video-params-long-929-2026-08-25.png)
- [mobile](../../design-references/liblib-clone-batch21-video-params-mobile-390-2026-08-25.png)
- [contact sheet](../../design-references/liblib-clone-batch21-video-params-contact-sheet-2026-08-25.png)

## 4. 跨批与工程回归

```bash
for script in scripts/verify-liblib-batch{9..21}.py; do
  python3 "$script" || exit 1
done

npm run check
npm run docs:check
git diff --check
```

结果：

- Batch 9-21 全部通过。
- ESLint：`0 error`，保留仓库已有 9 条 FrameOS warning。
- TypeScript：通过。
- Next.js production build：通过。
- 文档链接和 diff whitespace：通过。

旧批次回归脚本重写的 PNG 已恢复，只保留 Batch 21 四张新证据图。

## 5. 实施历史

| Commit | 内容 |
|---|---|
| `44a0cec` | Batch 21 原站识图、缺口量化、计划和规格 |
| `fefa35e` | 参数 dialog 实现、专项 Playwright 和 clone screenshots |
| 本文档提交 | 回归结果、组件规格、Big Picture、Harness 和 Changelog |
