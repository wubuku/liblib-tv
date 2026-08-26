# Batch 54 源站证据与 clone 决策

## 1. 证据来源

本批复用 2026-08-26 已归档的当前登录态源站观察，不重复识别截图，也不在
共享画布创建 edit record 或提交任务：

- [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md#31-元素编辑)
- [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#13-元素编辑与旋转入口的安全边界)
- [`LIBTV_UI_STATE_HIERARCHY.md`](../liblib-seedance-2.5-2026-08-25/LIBTV_UI_STATE_HIERARCHY.md)
- [`EVIDENCE_MATRIX.md`](../open-canvas-2026-08-26/EVIDENCE_MATRIX.md)
- [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)

这些文档包含当前 production bundle 静态审计和 live DOM rect。Batch 53 的
clone 截图不作为本批源站证据。

## 2. 已确认的空态合同

在源站约 `0.407229` zoom、图片节点 `i-1FQ9tErTcC` 上进入元素编辑：

| 元素 | Source rect / state |
|---|---|
| dedicated toolbar | `-142.852,89.734,272,44` |
| toolbar center | `-6.852`，与 node center 约 `-6.853` 对齐 |
| mode root | `-132.273,185.734,250.852,203.711` |
| edit stage | `-131.961,185.734,250.211,141.711` |
| initial layer | mask 覆盖 stage；guide 为 `标记你想要修改的对象` |
| record panel | `-206.844,339.445,400,50`；`编辑内容待添加` |
| standard panel | 不存在 |
| active tool | point / `点选` |
| local history | 空态 undo disabled |

直接几何关系：

```text
toolbarCenterX ~= stageCenterX ~= recordPanelCenterX
stageTop - toolbarBottom = 52px
recordPanelTop - stageBottom = 12px
modeRootHeight = stageHeight + 12px + recordPanelHeight
```

Escape 后 dedicated toolbar、mode root 和 stage 均卸载，standard
`1092.5x49` toolbar 与 `660x191` generation panel 恢复。

## 3. Bundle 支持的行为边界

- 入口设置 `ElementTool.EditElements`；
- `InteractiveImageEditMode` mount/unmount 对应 session open/close；
- authoring tools 包括 point、box、brush 和 brush size；
- session 具备 undo/redo，但空态无可撤销记录；
- 只有存在有效 edit records 时生成入口才可用；
- 提交阶段才会创建或复用 `源图名称--元素编辑` 输出节点，并调用 task gateway。

因此，本批只能复刻**提交前空态**。入口点击本身不能直接映射到
`addDerivedNode`，空态工具切换也不能写入 graph history。

## 4. 状态与坐标映射

```text
uiStore.imageElementEdit = {
  nodeId,
  filename,
  imageUrl,
  width,
  height
} | null
```

- dedicated toolbar：screen-sized、node-centered；
- edit stage：node-local flow surface，覆盖当前 media；
- record panel：node-linked，但 screen-sized；
- standard toolbar/panel：active 时不挂载；
- page keyboard guard：持有 active image surface 的命令 ownership。

clone 的本地图片 fixture 是 `2:1`，源站审计节点约为 `16:9`。本批保持
fixture 自身比例，只复刻 stage 跟随 media 的空间合同，不伪造 source 节点尺寸。

## 5. 风险边界

- point/box/brush 在本批只改变 active visual state；
- brush size 只改变本地 control value；
- undo 和 generate 在空态 disabled；
- 不创建 record，不显示成功选择或笔迹；
- 不生成、不上传、不保存、不创建 output node；
- 不推断非空 record 文案、Prompt、模型参数、费用或任务状态；
- 未来非空态必须使用 disposable fixture 和独立合同。

