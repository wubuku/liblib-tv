# Batch 53 实施记录

> 状态：已完成（2026-08-26）。本批完成 selected image 的空标注 active
> tool 替换态。代码与运行证据 checkpoint 为 `7055776`，active image
> keyboard isolation 修正为 `8f468eb`，均已 push。

## 1. 实施清单

- [x] `uiStore` 增加 typed `ImageAnnotateState` 和 open/close actions。
- [x] 标准图片工具条启用 `标注` 入口。
- [x] 新增 `ImageAnnotateToolbar`，固定 `536x49`、8 按钮。
- [x] 新增 `ImageAnnotateSurface`，覆盖节点媒体并建立 DPR2 canvas backing。
- [x] active annotate 替换 standard toolbar，卸载 standard bottom panel。
- [x] 空态 `撤销`/`重做` disabled；`保存` 保持 enabled 但不执行真实保存；
  `画笔`/`矩形`/`文字`/颜色/线宽只切换本地视觉状态。颜色板和线宽范围
  按当前 production chunk 的静态审计落地。
- [x] Escape/close 恢复同一 selected image 的标准双浮层。
- [x] selection 切换或清空时自动退出 active annotate。
- [x] Preview/annotate 共享窄的 capture-phase shortcut guard，阻断 React Flow
  Escape 清 selection 和底层 Delete/Space/Tab/undo/redo/duplicate。
- [x] focused Playwright、runtime audit 和 desktop/mobile 截图。

## 2. 代码边界

| 文件 | 责任 |
|---|---|
| `src/store/uiStore.ts` | active annotate identity 和 top-level surface mutual exclusion |
| `src/components/ImageAnnotateToolbar.tsx` | source-sized 专用 toolbar 与空态 controls |
| `src/components/ImageAnnotateSurface.tsx` | node-local canvas、DPR2 backing 和 pointer isolation |
| `src/components/nodes/ImageNode.tsx` | standard/active render branch 和 action dispatch |
| `src/app/page.tsx` | selection cleanup 和 active image shortcut capture guard |
| `scripts/verify-liblib-batch53.py` | desktop/mobile focused contract |

本批未修改 `canvasStore` graph data，也没有新增 node/edge/history transaction。

## 3. 专项验证

```text
python3 scripts/verify-liblib-batch53.py
```

结果：

```text
Batch 53 Playwright verification passed: annotate toolbar replacement,
standard panel removal, node-centered geometry, DPR2 canvas backing,
    empty-state undo/redo state, tool toggle, keyboard isolation,
Escape/close recovery, graph immutability and mobile overflow.
```

结构化测量：

```text
desktop node       48,176.717,198.671,99.336
desktop toolbar   -120.664,117.717,536,49
desktop media      48.284,177.001,198.104,98.768
desktop backing    396x198

mobile node        48,94.077,70.119,35.060
mobile toolbar   -184.940,35.077,536,49
mobile media       48.100,94.177,69.919,34.859
mobile backing     140x70
```

完整值见 [`runtime-audit.json`](runtime-audit.json)。

## 4. 实施中发现并修复的问题

### 4.1 Graph signature 误把 UI 文本算作 graph

验证器最初把 node `textContent` 纳入 graph signature。active toolbar 替换会
改变 node DOM 文本，但不代表 nodes/edges 改变。已将 signature 收窄到 node
id/transform、edges、selection 和 viewport。

### 4.2 Escape 被 React Flow 后续 handler 清 selection

普通 bubble-phase `preventDefault`/`stopPropagation` 不能阻止同事件链中的
React Flow listener。最终实现增加窄的 capture-phase active image surface
guard：

- 只在 Preview 或 annotate active 时拦截；
- Escape 关闭当前 surface；
- Delete/Backspace/Tab/Space/Ctrl/Meta+Z/Y/D 不穿透；
- 普通画布快捷键继续使用原有 bubble-phase handler。

Batch 53 和 Batch 52 均在该修正后重新通过。

### 4.3 固定宽工具条的自然裁切

desktop/mobile 上 `536px` toolbar 的关闭按钮可能位于 viewport 外。验证器
先保留 rect 事实，再通过 DOM click 验证关闭生命周期；产品没有为测试增加
clamp 或 page-center 重定位。

## 5. 回归与静态检查

已通过：

```text
python3 scripts/verify-liblib-batch52.py
python3 scripts/verify-liblib-batch10.py
python3 scripts/verify-liblib-batch11.py
npx tsc --noEmit
npx eslint <Batch 53 touched files>
python3 -m py_compile scripts/verify-liblib-batch53.py
git diff --check
```

Batch 10/11 和 Batch 52 运行产生的历史 PNG/JSON 变化已恢复；它们不被
Batch 53 结果改写。

## 6. 截图与识图

- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批唯一识图记录；
- [`../../design-references/liblib-clone-batch53-image-annotate-standard-929-2026-08-26.png`](../../design-references/liblib-clone-batch53-image-annotate-standard-929-2026-08-26.png)
- [`../../design-references/liblib-clone-batch53-image-annotate-active-929-2026-08-26.png`](../../design-references/liblib-clone-batch53-image-annotate-active-929-2026-08-26.png)
- [`../../design-references/liblib-clone-batch53-image-annotate-mobile-390-2026-08-26.png`](../../design-references/liblib-clone-batch53-image-annotate-mobile-390-2026-08-26.png)

## 7. 结果边界

本批闭环的是**空标注替换态**，不是完整标注工具：

- 无 stroke/path 数据；
- 无 dirty state、真实保存、上传或结果图；`保存` 只是 enabled 的 source-shaped 空态控件；
- 无本地/远程 history；
- 无 provider、计费或权限；
- 未确认的 toolbar icon SVG/CSS、非空 stroke、dirty/save/upload/result 语义
  不作为 source fact。

下一批可进入 Batch 54：元素编辑空态，目标是 `272x44` toolbar、node-local
stage/guide、`400x50` record panel、standard L2 replacement 和 Escape
恢复；不创建 edit record 或提交生成。
