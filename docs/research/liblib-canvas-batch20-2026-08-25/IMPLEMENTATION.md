# Batch 20 实施结果：720° 全景派生节点

> 状态：已完成并通过专项、跨批和生产构建验证。

## 1. 实施内容

### `src/store/canvasStore.ts`

- `addDerivedNode` 增加可选 `DerivedNodeOptions`：
  - `dimensions`
  - `offset`
- 默认尺寸和 `{ x: 120, y: 0 }` 偏移保持不变，因此 `VideoNode` 和未专项采样的图片动作不受影响。
- 派生节点继续使用 source 的 absolute position，parented source 也会创建顶层 derived node。
- 新节点和 source-to-derived edge 在一次 store update 中写入，同用一个 history snapshot。

### `src/components/nodes/ImageNode.tsx`

- `imageUrl` 允许 `null`，增加 `placeholderKind: "panorama"` 和 `editorVariant: "panorama"`。
- `全景` 现在创建：
  - filename `720°全景图`
  - node/style/data dimensions `700x350`
  - offset `{ x: 120, y: -110 }`
  - 空媒体 placeholder
  - 唯一 source image reference
  - `2:1 · 标准画质 · 2K · 1张`
- 其他五个图片动作仍走原有通用 prototype，不把本批 panorama 合同错误推广过去。

### `src/components/ImageEditPanel.tsx`

- 标准 image editor 与 panorama editor 拆成两个内部组件，避免用条件 hooks 混合生命周期。
- panorama branch 复用节点内 absolute anchor 和 `scale(1 / zoom)`：
  - `660x252`
  - `+参考`
  - 一个 `47x47` 编号 reference
  - 紫色 `720` 标识与 `720全景`
  - source-observed helper copy
  - `Lib Image`
  - `2:1 · 标准画质 · 2K · 1张`
- submit 只切换 `已创建本地全景任务`，不向节点填入伪生成结果。

### `scripts/verify-liblib-batch20.py`

- 覆盖 graph `10/11 -> 11/12`、selection、node/edge identity、geometry 和 source offset。
- 验证 placeholder 不包含源媒体，reference 指向源图片。
- 验证 panel size、中心、gap、copy、model、settings 和本地 submit。
- 验证 undo/redo 是单事务。
- 验证 desktop fit-view 和 390px 自然裁切、页面 overflow 与 console/page error。
- 生成 desktop/mobile 截图和一次性 contact sheet。

## 2. 证据边界

见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md) 和 [`PANORAMA_DERIVATION.spec.md`](PANORAMA_DERIVATION.spec.md)。

### Source fact

- “全景”创建空 `720°全景图` 节点、source edge 和专用单参考图 panel。
- panel 文案包含 `720全景`、转换说明、`Lib Image` 和 `2:1 · 标准画质 · 2K · 1张`。

### Inference

- `700x350` world dimensions、`+120/-110` world offset、`660x252` panel 来自截图与 zoom 反推。

### Clone-only decision

- `addDerivedNode` 的 options API 是本仓库表达几何差异的实现方式。
- submit 只保留本地反馈。
- 未采样的多角度、打光、九宫格、高清、宫格切分继续标记为未验证 prototype。

## 3. 专项验证

```bash
python3 scripts/verify-liblib-batch20.py
```

结果：通过。

- graph：`10 nodes / 11 edges -> 11 nodes / 12 edges`
- derived：selected `720°全景图`，world size `700x350`
- edge：`i-YDfWhFlthe -> <derived id>`
- panel：`660x252`，中心与节点一致，gap 为 `16 * zoom`
- reference：1 张 source image，`47x47`
- history：一次 undo 同时移除 node/edge，一次 redo 同时恢复
- mobile：panel 和 toolbar 自然裁切，无页面级横向溢出
- console/page error：0

截图：

- [desktop](../../design-references/liblib-clone-batch20-panorama-desktop-929-2026-08-25.png)
- [mobile](../../design-references/liblib-clone-batch20-panorama-mobile-390-2026-08-25.png)
- [contact sheet](../../design-references/liblib-clone-batch20-panorama-contact-sheet-2026-08-25.png)

## 4. 跨批与工程回归

```bash
for script in scripts/verify-liblib-batch{9..20}.py; do
  python3 "$script" || exit 1
done

npm run check
npm run docs:check
git diff --check
```

结果：

- Batch 9-20 全部通过。
- ESLint：`0 error`，保留仓库已有 9 条 FrameOS warning。
- TypeScript：通过。
- Next.js production build：通过。
- 文档链接和 diff whitespace：通过。

回归脚本重写的旧批次 PNG 已恢复，只保留 Batch 20 三张新证据图。

## 5. 实施历史

| Commit | 内容 |
|---|---|
| `f5ed480` | Batch 20 计划、原站截图分析和组件合同 |
| `1c04ce0` | panorama 派生流程、专项 Playwright 和 clone screenshots |
| 本文档提交 | 回归结果、组件规格、Big Picture、Harness 和 Changelog |
