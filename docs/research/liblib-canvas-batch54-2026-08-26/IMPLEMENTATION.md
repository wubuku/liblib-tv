# Batch 54 实施记录：图片元素编辑空态

> 状态：已完成（2026-08-26）。本批复刻 selected image 的空元素编辑
> authoring state。提交前不创建有效 edit record，不上传、不生成、不保存，
> 不改变 graph。

## 1. 实施结果

- [x] `uiStore` 增加 typed `ImageElementEditState`、open/close actions 和
  overlay mutual exclusion。
- [x] `ImageToolbar` 启用 `元素编辑` 入口，并保持其他高风险动作有界。
- [x] 新增 `ImageElementEditMode`，将专用 toolbar 与 node-local surface
  作为一个互斥 active state 挂载。
- [x] 新增 `ImageElementEditToolbar`：关闭、点选、框选、画笔、画笔尺寸和
  空态撤销；默认工具为点选。
- [x] 新增 `ImageElementEditSurface`：图片 media 上方的 mask、guide 和
  `400x50` 空 record panel。
- [x] `ImageNode` 建立 standard / annotate / element-edit 三路互斥渲染；
  active element edit 时卸载标准 toolbar 和 generation panel。
- [x] Escape、关闭按钮和 selection 切换恢复或清理 active state。
- [x] active element edit 持有 Delete、Backspace、Tab、Space、undo、redo、
  duplicate 等快捷键，避免 graph 命令穿透。
- [x] 增加 Batch 54 focused Playwright verifier、结构化 runtime audit 和
  desktop/mobile clone 截图。

## 2. 代码边界

| 文件 | 责任 |
|---|---|
| `src/store/uiStore.ts` | active element-edit identity、媒体描述和互斥关闭 |
| `src/components/ImageElementEditMode.tsx` | active tool local state 与 surface 组合 |
| `src/components/ImageElementEditToolbar.tsx` | `272x44` 专用 toolbar 和空态 controls |
| `src/components/ImageElementEditSurface.tsx` | node-local stage、mask、guide、record panel |
| `src/components/nodes/ImageNode.tsx` | standard/annotate/element-edit 分支和入口 dispatch |
| `src/app/page.tsx` | selection cleanup、Escape 和 active-image shortcut guard |
| `scripts/verify-liblib-batch54.py` | desktop/mobile 几何、生命周期和不变性断言 |

本批没有修改 `canvasStore` 的 graph data、edges、selection、Prompt、
viewport 或 history；也没有触碰 FrameOS、Director、AutoLink、真实 provider
或共享源站项目。

## 3. 专项验证

```bash
python3 scripts/verify-liblib-batch54.py
```

结果：

```text
Batch 54 Playwright verification passed: element-edit toolbar replacement,
stage/record geometry, tool switching, brush size, empty-state guards,
keyboard isolation, Escape/close recovery, graph immutability and mobile
overflow.
```

结构化测量摘要：

| 状态 | Node | Toolbar | Stage | Record panel |
|---|---|---|---|---|
| Desktop `929x874` | `48,176.717,198.671,99.336` | `11.336,80.717,272,44` | `48.284,177.001,198.104,98.768` | `-52.664,287.760,400,50` |
| Mobile `390x844` | `48,94.077,70.119,35.060` | `-52.940,-1.923,272,44` | `48.100,94.177,69.919,34.858` | `-116.940,141.033,400,50` |

两种 viewport 都确认：

- toolbar center、stage center 和 record panel center 对齐；
- toolbar 到 stage 顶部约 `52px`；
- stage 到 record panel 顶部约 `12px`；
- mobile 允许固定宽 surface 自然裁切，但不产生横向滚动；
- empty undo/generate disabled，point/box/brush 和 brush size 可切换；
- Escape/close 后标准图片双浮层恢复；
- nodes、edges、selection、Prompt、viewport 和 history signature 不变。

完整值见 [`runtime-audit.json`](runtime-audit.json)。

## 4. 实施中发现并修复的问题

### 4.1 旧 dev server 造成的假失败

验证器首次运行连接到了没有加载最新源码的长期 dev server，导致 record
panel 的高度仍被测成 `52px`。重启当前工作树 server 后确认实现实际生效。

### 4.2 record panel 外框尺寸

`box-sizing` 与边框叠加使 record panel 实际外框比合同多 `2px`。已固定
`400x50` 为包含边框的最终几何。

### 4.3 stage/tool selector 冲突

toolbar 和 stage 初始共用 `data-image-element-edit-tool`，严格 selector
会得到两个匹配项。已区分为 toolbar tool selector 与
`data-image-element-edit-active-tool` stage selector。

### 4.4 移动端自然裁切验证

固定 `272px` toolbar 在 mobile 可能被顶部导航遮挡或裁出视口。产品保留
source-shaped node-centered 布局；verifier 对视口外控件使用 DOM click
fallback 验证生命周期，不通过产品 clamp 改变几何。

## 5. 回归与静态检查

本批 closeout 已实际通过以下门禁。Batch 52 verifier 在回归时发现其旧的
`元素编辑=disabled` 断言已被本批实现取代，已将该断言更新为当前可进入的
空态入口；`图层分离`、`旋转`、`下载` 仍保持 disabled。

```text
PASS python3 scripts/verify-liblib-batch54.py
PASS python3 scripts/verify-liblib-batch53.py
PASS python3 scripts/verify-liblib-batch52.py
PASS python3 scripts/verify-liblib-batch10.py
PASS python3 scripts/verify-liblib-batch11.py
PASS npm run check
PASS python3 scripts/verify-docs.py
PASS git diff --check
```

`npm run check` 保留 9 个既有 lint warnings、0 errors；typecheck 和
production build 均通过。回归脚本曾重写历史视觉产物，已在提交前恢复，
因此本批没有把旧截图或 Batch 52 runtime audit 改成新的证据。

Batch 53/52/10/11 仍分别保护其自身合同；历史 Batch 10 的 AutoLink 断言
不被解释成当前 source AutoLink parity。

## 6. 证据与截图

- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：源站事实、bundle 边界和 clone 决策；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批唯一截图识别台账；
- [`../../design-references/liblib-clone-batch54-image-element-edit-active-929-2026-08-26.png`](../../design-references/liblib-clone-batch54-image-element-edit-active-929-2026-08-26.png)
- [`../../design-references/liblib-clone-batch54-image-element-edit-mobile-390-2026-08-26.png`](../../design-references/liblib-clone-batch54-image-element-edit-mobile-390-2026-08-26.png)

截图是 clone 运行证据，不是源站截图。后续回答本批截图内容时应先读
`SCREENSHOT_ANALYSIS.md`，除非截图或问题范围发生变化，不重复做视觉识别。

## 7. 结果边界与接力

本批闭环的是**空元素编辑替换态**，不声称完成：

- 对象识别、point/box/brush 真实标记或 record persistence；
- 非空记录卡、Prompt、dirty/save/discard 语义；
- 生成、上传、任务轮询、费用、权限或结果节点；
- 旋转、图层分离、下载和真实 provider；
- 源站 exact icon SVG/CSS 或非空状态的最终合同。

下一步优先级回到 `docs/research/LIBTV_UIUX_PARITY_BACKLOG.md`：先补
`PAR-005` 当前源站 page shell/top-level 只读 freshness，或在有安全 fixture
时推进 Auto Link/ready-video；不把本批空态扩展成真实生成链。

## 8. 提交历史

| Commit | 内容 | 状态 |
|---|---|---|
| `7b84010` | Batch 54 计划、源站证据和组件规格 | 已 push |
| `b593c6b` | 元素编辑空态实现 | 已 push |
| `834a637` | 专项 verifier、runtime audit、截图和验证修复 | 已 push |
| `4a43bde` | 实施记录、截图台账和全局索引 | 已 push |
| 后续 checkpoint | Batch 52 断言迁移和实际回归结果 | 待提交 |
