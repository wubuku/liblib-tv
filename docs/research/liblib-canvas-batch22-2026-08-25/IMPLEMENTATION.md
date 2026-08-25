# Batch 22 实施结果：Seedance Source-visible 模型菜单

> 状态：已完成并通过专项、跨批和生产构建验证。

## 1. 实施内容

### `src/components/VideoGenerationPanel.tsx`

- model popover 从约 `330x216` 调整为固定 `380x410`。
- 使用原站截图可见的七项集合，移除没有本批证据的 `Kling O3`。
- 前五项显示 premium icon；Wan 两项保持无 premium。
- 只有当前 selected row 展开已确认 description，其他行保持紧凑。
- menu 与 generation panel 左边缘对齐，并从 footer trigger 向上展开。
- 模型选择仍是 component-local state，不代表模型真实可用。

### `scripts/verify-liblib-batch22.py`

- menu 尺寸与相对 generation panel 几何。
- 七项顺序、title、estimate 和 premium matrix。
- `Kling O3` 缺席。
- 默认 2.5 与 Fast 选择后的 selected-only description。
- 参数 dialog handoff、390px viewport fit、页面 overflow、console/page error。
- desktop/mobile 截图和 contact sheet。

## 2. 证据边界

### Source fact

- 七项顺序、estimate、前五项 premium、Fast selected row 与两个已确认 description 来自登录原站截图和现有 live audit。

### Inference

- `380x410` 及相对 panel `left 0/top -176.7` 来自截图像素边界与 source generation panel rect 的联合反推。

### Clone-only decision

- model tile 与 premium 使用 Lucide/CSS icon 近似，不声称复刻原始 SVG path。
- 没有可靠文案的模型在选中时只显示高亮，不补写 description。
- 七项只称为 source-visible 集合，不声称是完整模型库或真实可调用列表。

## 3. 专项验证

```bash
python3 scripts/verify-liblib-batch22.py
```

结果：通过。

- menu：`380x410`
- relative to generation panel：`left 0`、`top -176.7`
- source-visible model rows：7
- premium：5
- selected row：`58px`；compact row：`48px`
- params handoff、390px fit、页面 overflow：通过
- console/page error：0

截图：

- [default 2.5](../../design-references/liblib-clone-batch22-model-menu-default-929-2026-08-25.png)
- [selected Fast](../../design-references/liblib-clone-batch22-model-menu-fast-929-2026-08-25.png)
- [mobile](../../design-references/liblib-clone-batch22-model-menu-mobile-390-2026-08-25.png)
- [contact sheet](../../design-references/liblib-clone-batch22-model-menu-contact-sheet-2026-08-25.png)

## 4. 跨批与工程回归

```bash
for script in scripts/verify-liblib-batch{9..22}.py; do
  python3 "$script" || exit 1
done

npm run check
npm run docs:check
git diff --check
```

结果：

- Batch 9-22 全部通过。
- ESLint：`0 error`，保留仓库已有 9 条 FrameOS warning。
- TypeScript：通过。
- Next.js production build：通过。
- 文档链接和 diff whitespace：通过。

旧批次回归脚本重写的 PNG 已恢复；Batch 22 四张新证据图保持为本批提交内容。

## 5. 实施历史

| Commit | 内容 |
|---|---|
| `8da8803` | Batch 22 原站聚焦识图、缺口量化、计划和规格 |
| `6420533` | 模型菜单实现、专项 Playwright、clone screenshots 与识图台账 |
| 本文档提交 | 回归结果、组件规格、Big Picture、Harness 和 Changelog |
