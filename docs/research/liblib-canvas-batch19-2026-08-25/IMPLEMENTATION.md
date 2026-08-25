# Batch 19 实施结果：缩略图锚点与视觉校准

## 1. 实施内容

### `src/app/page.tsx`

- `MiniMap.position` 从 `bottom-right` 改为 `bottom-left`。
- 增加稳定 class `liblib-minimap` 和中文 `ariaLabel`。
- 使用 source-shaped 参数：
  - `150x110px`
  - `#262626` background
  - `rgba(20,20,20,0.56)` mask
  - `#747474` viewport outline
  - `#626262` node fill
  - `#707070` node stroke
- 保留 React Flow 默认的非 pannable、非 zoomable、无 click command 行为。
- width/height 继续通过 inline `style` 提供，因为 xyflow 会读取该 prop 计算 minimap viewBox；这不是普通静态布局捷径。

### `src/app/globals.css`

- 建立 `.react-flow__panel.react-flow__minimap.liblib-minimap` 合同：
  - desktop `left: 152px; bottom: 54px`
  - mobile `left: 128px; bottom: 107px`
  - `10px` radius、低对比 border 和 shadow
- 使用高于 xyflow `.react-flow__panel.left/.bottom` 的 specificity，避免第三方基础样式覆盖锚点。

### `scripts/verify-liblib-batch19.py`

- 覆盖初始隐藏、toggle pressed state、桌面几何、颜色和 10 个 minimap node。
- 执行 fit-view 并确认 zoom 落在 `20-35%`、viewport mask path 更新。
- 验证 asset drawer 后 minimap 和 trigger 同步右移 `240px`。
- 验证 390px 下与主工具条保留至少 `4px` 间距且无页面溢出。

## 2. 证据边界

### Source fact

- 原站 `929x874`、`28%` 截图直接支持 minimap 的约 `150x110px` 尺寸、按钮上方锚点、深灰面板、灰色节点块和 viewport outline。

### Inference

- minimap 相对 React Flow canvas 左偏移，因此 asset drawer 改变 canvas 起点时会和底部工具条同步右移。

### Clone-only decision

- 390px 下使用 `bottom: 107px` 避让双工具条。
- 不开放 minimap pan/zoom/click 能力。

## 3. 专项验证

```bash
python3 scripts/verify-liblib-batch19.py
```

结果：通过。

- Desktop：`x=152, y=710, w=150, h=110`。
- Asset drawer：minimap 与 trigger 均右移 `240px`。
- Mobile：`x=128, y=627, w=150, h=110`，与主工具条间距 `6px`。
- fit-view 后 viewport outline 更新。
- toggle、颜色、节点数、overflow、console/page error 全部通过。

截图：

- [desktop](../../design-references/liblib-clone-batch19-minimap-desktop-929-2026-08-25.png)
- [asset drawer](../../design-references/liblib-clone-batch19-minimap-asset-drawer-929-2026-08-25.png)
- [mobile](../../design-references/liblib-clone-batch19-minimap-mobile-390-2026-08-25.png)

一次性识图结论见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。

## 4. 最终回归

跨批命令：

```bash
python3 scripts/verify-liblib-batch9.py
for script in scripts/verify-liblib-batch{11..19}.py; do
  python3 "$script" || exit 1
done
```

结果：全部通过。

- Batch 9 节点浮层锚点、拖动、平移、缩放和多选生命周期通过。
- Batch 11-18 overlay、资产、分镜、Agent/分享、添加节点、画布导航、资产上下文和 zoom menu 全部通过。
- Batch 19 minimap 专项在跨批序列中再次通过。

工程命令：

```bash
npm run check
npm run docs:check
git diff --check
```

结果：

- ESLint：`0 error`，保留仓库已有的 9 条 FrameOS warning。
- TypeScript：通过。
- Next.js production build：通过。
- 文档链接：161 个 Markdown 文件、354 个本地目标，全部通过。
- diff whitespace：通过。

回归脚本生成的旧批次截图已恢复，只保留本批三张新证据图。
