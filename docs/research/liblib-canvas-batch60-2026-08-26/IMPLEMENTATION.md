# Batch 60 实施记录：图片双浮层选择切换与 owner 一致性

> 状态：`SCRIPT_RECORDED_PASS`（2026-08-27 focused verifier、质量门禁、
> 当前合同回归和 closeout 记录完成）。

## 1. 实施范围

本批围绕普通 LibTV 图片节点的标准双浮层：

```text
selected image
  -> ImageToolbar
  -> ImageEditPanel
```

已有 `10 + 24 * zoom`、`16 * zoom`、node-center、`1092.5x49` 和 `660px`
合同不变。本批只补充 owner identity 和 panel hit-testing boundary。

## 2. 代码变更

| 文件 | 变更 |
|---|---|
| `src/components/ImageToolbar.tsx` | 接收 `ownerNodeId`，输出 `data-owner-node-id` |
| `src/components/ImageEditPanel.tsx` | 标准/全景 panel 接收 owner；wrapper/section 对非交互区域透传，控件显式恢复命中 |
| `src/components/nodes/ImageNode.tsx` | 将 node id 传给两个标准 surface |
| `scripts/verify-liblib-batch60.py` | 新增 desktop/mobile focused Playwright 和结构化 audit |

没有修改 `canvasStore`、`uiStore`、React Flow selection/history 数据模型，
也没有改变 toolbar/panel 的几何公式。

## 3. 行为决策

- 标准态最多挂载一个 toolbar 和一个 panel；
- 两者必须带同一 `data-owner-node-id`；
- selection 切换后旧 surface 卸载，新 surface 迁移到新 owner；
- panel 的非交互 wrapper/section 不做 blanket pointer capture；
- textarea、button 和现有弹出交互显式恢复 `pointer-events: auto`；
- active annotate 仍替换标准双浮层，不新增第三层；
- panel 覆盖可编辑区域时，浏览器不能同时把同一像素交给 textarea 和
  下方节点，因此本批不宣称“任意覆盖像素均可穿透”。这是真实的 UI
  命中冲突，后续只有取得源站证据或产品决策后才能继续调整。

## 4. 验证记录

Focused：

```text
python3 scripts/verify-liblib-batch60.py
```

覆盖：

- desktop/mobile standard pair；
- toolbar/panel owner identity；
- node-center、top/bottom gap、屏幕尺寸；
- panel pointer boundary 与 textarea/button interaction；
- 相邻图片节点选择迁移；
- annotate replacement 与 Escape 恢复；
- 空白点击卸载双浮层；
- graph/history 不变；
- desktop/mobile no-overflow；
- console/page/request diagnostics。

相邻回归结果：

| 命令 | 结果 | 说明 |
|---|---|---|
| `python3 scripts/verify-liblib-batch51.py` | `EXPECTED_HISTORICAL_MISMATCH` | 该脚本仍断言旧 `900.5px` toolbar；当前 Batch 52+ 合同为 `1092.5px`，实际测得 `1092.499969px`。不回退当前实现，也不将其记为 Batch 60 回归。 |
| `python3 scripts/verify-liblib-batch52.py` | `PASS` | 当前 13-action toolbar、Preview、geometry、keyboard、graph isolation 和 mobile。 |
| `python3 scripts/verify-liblib-batch53.py` | `PASS` | annotate replacement、DPR2 canvas、controls、Escape 和 graph immutability。 |
| `python3 scripts/verify-liblib-batch54.py` | `PASS` | element-edit replacement、stage/record panel、controls、Escape 和 graph immutability。 |
| `python3 scripts/verify-liblib-batch56.py` | `PASS` | rotate graph slice、media gate、metadata、atomic undo/redo 和 mobile。 |
| `python3 scripts/verify-liblib-batch59.py` | `PASS` | Director asset library、preview/add-object、Inspector continuity 和 isolation。 |
| `python3 scripts/verify-liblib-batch10.py` | `PASS` | 历史五态图片面板和 AutoLink compatibility。 |
| `python3 scripts/verify-liblib-batch11.py` | `PASS` | 历史 top-level overlay lifecycle 和 mobile。 |

质量与文档门禁：

| 命令 | 结果 |
|---|---|
| `python3 scripts/verify-liblib-batch60.py` | `PASS` |
| `npm run check` | `PASS`；lint 0 errors、9 条既有 warnings；typecheck/build 通过 |
| `npm run docs:check` | `PASS`；492 Markdown files、2300 local targets |
| `python3 -m py_compile scripts/verify-liblib-batch60.py` | `PASS` |
| `git diff --check` | `PASS` |

本批沿用目录 `liblib-canvas-batch60-2026-08-26/`，与此前 Batch 51-56 的
日期命名保持一致；本次 closeout 日期为 2026-08-27。

## 5. 证据边界

`10 + 24 * zoom`、`16 * zoom`、center 和 natural clipping 继续来自既有
source-backed contract。pointer hit-testing 与 `data-owner-node-id` 是
clone-owned runtime contract，不把当前浏览器无法取得的认证后源站行为写成
事实。

## 6. 未完成项

- 源站重叠 panel 对相邻 node 的真实 pointer routing；
- 真实 bitmap editor、dirty/save、provider 和 remote task；
- 多层 overlay 的统一 focus manager；
- 任意被 textarea 覆盖的像素无法同时支持编辑和下层 node click，这需要
  产品交互取舍或源站新证据。

## 7. Checkpoint

Batch 59 实施 checkpoint：`bfdc918`（已 push）。
Batch 60 focused verifier、质量门禁和当前合同回归已完成。
最终 checkpoint 由本批 closeout commit 记录；push 后工作区必须保持 clean。
