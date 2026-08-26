# Batch 54 计划：图片元素编辑空态

> 建档日期：2026-08-26
> 对应 backlog：`LIBTV-PAR-002` Element Edit empty

## 1. 缺口与价值

| 项目 | Batch 53 后 clone | 当前源站合同 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 元素编辑入口 | `88px` action 存在但 disabled | 点击后进入独立 authoring mode | 5 | 启用 |
| toolbar 替换 | 只有 standard/annotate 两路 | 标准条被 `272x44` 专用条替换 | 5 | 增加第三路互斥状态 |
| generation panel | active element edit 未表达 | 标准 `660px` panel 不存在 | 5 | active 时卸载 |
| edit stage | 无 | 图片节点上覆盖 stage、mask 和 guide | 5 | 实施空态 surface |
| record panel | 无 | stage 下方 `400x50`，显示 `编辑内容待添加` | 5 | 实施空态 panel |
| 退出与键盘 | 只覆盖 Preview/Annotate | Escape/关闭恢复标准双浮层 | 5 | 纳入 active image guard |
| 有效 record/生成 | 无安全 live 证据 | 有效 record 后才允许生成 | 2 | 明确不实现 |

`Preview -> Annotate empty -> Element Edit empty` 是当前证据最完整、风险最低
的一组图片 active-surface 纵向 slice。完成本批后，`LIBTV-PAR-002` 的三个
低风险子项可以闭环；旋转和图层分离仍保留独立高风险 fixture 门槛。

## 2. Source Fact / Inference / Clone Decision

### Source fact

- 入口 test id 为 `image-toolbar-interactive-edit`，文字为 `元素编辑`；
- active 时 standard `1092.5x49` toolbar 和 `660x191` generation panel 卸载；
- 专用 toolbar 为 `272x44`，中心与 selected image node 中心对齐；
- mode root 约 `250.852x203.711`；
- edit stage 约 `250.211x141.711`，初始 mask 覆盖 stage；
- guide 文案为 `标记你想要修改的对象`；
- record panel 为 `400x50`，文案为 `编辑内容待添加`；
- 工具为关闭、点选、框选、画笔和撤销，默认点选 active，空态撤销 disabled；
- bundle 还确认画笔尺寸 control，以及只有有效 edit records 时生成才可用；
- Escape 后 active mode 卸载，标准 toolbar/panel 恢复；
- live 空态没有点选、框选、绘制、生成、上传、保存或 graph mutation。

### Inference

- stage 与图片节点属于同一 flow-space authoring surface，应随节点 zoom/pan；
- `250.211x141.711 + 12px gap + 50px panel = 203.711px`，说明 live mode
  root 的纵向结构是 stage、约 `12px` screen gap 和固定尺寸 record panel；
- toolbar 与 stage 的 live gap 为 `52px`，本批按独立 active-tool host 处理，
  不套用 standard toolbar 的 `10 + 24 * zoom` 公式；
- active state 属于 UI/session 层，不应进入 graph snapshot 或 history。

### Clone-only decision

- `uiStore.imageElementEdit` 保存当前 active node 和媒体 identity；
- `ImageNode` 使用 `standard / annotate / element-edit` 三路互斥渲染；
- toolbar 固定 `272x44`，使用 node-centered `NodeToolbar` 和 `52px` offset；
- edit stage 覆盖当前 clone 图片 media rect，不强改现有 fixture 的 `2:1` 数据；
- record panel 固定 `400x50`，用 inverse zoom 保持 screen size，并与 stage
  保持约 `12px` screen gap；
- point/box/brush 和 brush size 只维护组件本地状态；
- 空态撤销、生成保持 disabled；关闭/Escape 只清 session；
- 未获直接像素证据的 icon 采用当前 lucide 近似，并在规格中保留证据边界。

## 3. 实施步骤

1. 在 `uiStore` 增加 typed `ImageElementEditState`、open/close actions 和 overlay
   mutual exclusion；
2. 启用标准图片工具条的 `元素编辑` action；
3. 新增 `ImageElementEditToolbar`，实现 close、point、box、brush、brush size
   和 empty undo；
4. 新增 `ImageElementEditSurface`，实现 node-local mask/guide 和空 record panel；
5. 在 `ImageNode` 建立 standard/annotate/element-edit 三路互斥渲染；
6. 在 page selection cleanup 和 capture-phase keyboard guard 中纳入元素编辑；
7. 新增 `scripts/verify-liblib-batch54.py`，覆盖 desktop/mobile 几何、状态、
   快捷键隔离、恢复和 graph immutability；
8. 生成本地截图、runtime audit 和一次性 `SCREENSHOT_ANALYSIS.md`；
9. 更新组件/研究索引、backlog、verification ledger、Harness 和 changelog；
10. 运行 Batch 54、53、52、10、11、`npm run check`、docs check 和 diff check。

## 4. 验收标准

### Desktop

- standard selected image 初始仍只有 current toolbar + generation panel；
- 点击 `元素编辑` 后二者均卸载；
- 出现一个 `272x44` node-centered 专用 toolbar；
- toolbar 到 edit stage 顶部约 `52px`；
- stage 覆盖 image media，显示 mask 和 `标记你想要修改的对象`；
- record panel 为 `400x50`，居中于 stage，纵向 gap 约 `12px`；
- `点选`默认 active，point/box/brush 可切换，brush size 可修改；
- 空态撤销和生成 disabled；
- Delete/Backspace/Tab/Space/undo/redo/duplicate 不穿透到 graph；
- Escape 和 close 恢复 standard toolbar/panel；
- graph、selection、Prompt、viewport 和 history 不变。

### Mobile

- toolbar 和 record panel 保持 node center anchor，并允许自然裁切；
- stage 随缩放后的 node media，不提升为 page-level fixed overlay；
- document/body 不产生横向滚动；
- 视口外 control 可由 DOM 生命周期验证，不为测试增加产品 clamp；
- close 后 standard state 恢复。

### Repository

- Batch 54 focused verifier 通过并生成结构化 audit；
- Batch 53/52/10/11 相邻回归通过；
- `npm run check`、`python3 scripts/verify-docs.py`、`git diff --check` 通过；
- 计划、代码、closeout 在关键进展分别 commit/push；
- 最终工作区干净。

## 5. 不做事项

- 不创建 point/box/brush edit record；
- 不实现 mask segmentation、对象识别、真实笔迹或 undo stack；
- 不实现生成、上传、保存、费用、任务轮询或 output node；
- 不根据未知源站 CSS 猜测 hover animation、popover 或非空 record layout；
- 不把 element edit 与 annotate 合并成通用状态；
- 不修改旋转、图层分离、下载和 provider。

