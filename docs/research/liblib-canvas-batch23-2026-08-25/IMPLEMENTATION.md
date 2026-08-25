# Batch 23 实施结果：片段重拍时间带与 Prompt 编辑器

> 状态：已完成并通过专项、跨批和生产构建验证。

## 1. 实施内容

### `src/components/SegmentReshootPanel.tsx`

- lower editor 重构为独立 filmstrip + Prompt editor 两层：
  - stack：`660x316`
  - filmstrip：`660x56`
  - gap：`8px`
  - editor：`660x252`
- 移除没有源证据的“片段重拍”标题栏。
- filmstrip 使用时长比例表达 7 个 `4.0s` 区间和最后 disabled `2.0s` remainder。
- 保留最多五段，selected range 增加 cyan outline、check 和 duration badge。
- editor 增加：
  - `参考 / 标记 / 角色库`
  - 源视频 reference tile
  - 视频 token
  - range chips
  - editable intent
  - source-shaped footer hierarchy
- 未选择区间时显示整段编辑 helper，并允许空意图提交。
- submit 只产生本地整段重跑、片段重拍或续写状态。

### `src/components/nodes/VideoNode.tsx`

- `SegmentReshootPanel` 不再依赖 clone-only 内部关闭按钮。
- active processing toolbar 继续负责重拍/生成器切换。

### `scripts/verify-liblib-batch23.py`

- 从添加节点入口创建 ready video。
- lower stack、filmstrip、editor、节点锚点与 `16 * zoom` gap。
- 连续时间带比例和 disabled remainder。
- `0/5 -> 1/5 -> 5/5` 与第六段拒绝。
- 视频 token、range chips、空意图整段重跑、输入意图提交。
- 回到生成器、390px 自然裁切、页面 overflow、console/page error。

## 2. 证据边界

### Source fact

- 独立 filmstrip、无标题栏 editor、四个流程状态、视频/range token 和 footer 层级来自文章流程图。
- 4 秒下限、最多五段、未选择编辑整段和“留空 = 原样重跑一次”来自当前线上 bundle 文案。

### Inference

- 文章截图是缩放后的四状态拼图，不能提供 source DOM rect。
- `660px` 宽度和节点间距沿用已验证的视频 lower-panel 锚定合同。
- `56 + 8 + 252` 是基于截图比例和当前画布密度的 source-shaped clone geometry。

### Clone-only decision

- 连续 filmstrip 使用本地静态素材，不是视频逐帧提取。
- editor expand 只调整本地可编辑高度。
- 不执行视频裁剪、真人校验、模型调用、积分扣除或结果节点创建。
- `智能续写` 继续共享组件，但不属于本批 source fidelity 结论。

## 3. 专项验证

```bash
python3 scripts/verify-liblib-batch23.py
```

结果：通过。

- stack：`660x316`
- filmstrip/editor：`660x56` / `660x252`
- 4 秒区间宽度约为 2 秒 remainder 的两倍
- 五段上限、视频/range token、两类本地 submit feedback：通过
- generator handoff、390px 裁切、页面 overflow：通过
- console/page error：0

截图：

- [whole rerun](../../design-references/liblib-clone-batch23-segment-reshoot-default-929-2026-08-25.png)
- [five ranges + intent](../../design-references/liblib-clone-batch23-segment-reshoot-selected-929-2026-08-25.png)
- [mobile](../../design-references/liblib-clone-batch23-segment-reshoot-mobile-390-2026-08-25.png)
- [contact sheet](../../design-references/liblib-clone-batch23-segment-reshoot-contact-sheet-2026-08-25.png)

## 4. 跨批与工程回归

```bash
for script in scripts/verify-liblib-batch{9..23}.py; do
  python3 "$script" || exit 1
done

npm run check
npm run docs:check
git diff --check
```

结果：

- Batch 9-23 全部通过。
- ESLint：`0 error`，保留仓库已有 9 条 FrameOS warning。
- TypeScript：通过。
- Next.js production build：通过。
- 文档链接和 diff whitespace：通过。

旧批次回归脚本重写的 PNG 已恢复，只保留 Batch 23 四张新证据图。

## 5. 实施历史

| Commit | 内容 |
|---|---|
| `bcd9b66` | Batch 23 原站流程图识图、bundle 证据、计划和规格 |
| `c349cd5` | filmstrip/editor 实现、专项 Playwright、clone screenshots 与识图台账 |
| 本文档提交 | 回归结果、组件规格、Big Picture、Harness 和 Changelog |
