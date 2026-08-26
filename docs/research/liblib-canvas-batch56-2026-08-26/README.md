# Batch 56：图片旋转入口的最小派生节点复刻

> 状态：计划中。
> 对应 backlog：`LIBTV-PAR-002` 图片高风险动作中的旋转入口。
> 本批只复刻已直接观察到的 graph delta，不声称完成旋转编辑器或保存链路。

## 目标

把当前 clone 图片工具条中的 `旋转` 从 disabled placeholder 提升为一个有界
本地 prototype 入口：

```text
selected image
  -> click 旋转
  -> create image node named 旋转与镜像
  -> create source -> derived edge
  -> select derived node
```

## 证据边界

源站直接观察已记录：

- 点击 `image-toolbar-rotate` 后新增一个图片节点；
- 新节点名称为 `旋转与镜像`；
- 新节点被选中；
- 一次 `Meta+Z` 可撤销该新增节点；
- 没有继续进入角度、水平/垂直镜像、dirty modal、保存、上传或生成路径。

证据入口：

- [`../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md#34-旋转与镜像)
- [`../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#13-元素编辑与旋转入口的安全边界)
- [`../components/ImageNode.spec.md`](../components/ImageNode.spec.md)

## 本批不做

- 不把旋转实现成 CSS `transform`；
- 不创建 angle/flip/rotate editor；
- 不实现 dirty/save/discard modal；
- 不上传、下载、生成、轮询或调用真实 provider；
- 不推断源站派生节点的最终 bitmap、watermark、尺寸或处理状态；
- 不修改图层分离、标注非空态、元素编辑非空态或 Auto Link。

## 预期本地合同

clone-only decision：

- 使用 `addDerivedNode` 的单事务 node + edge 创建路径；
- 派生节点类型为 `image`，名称为 `旋转与镜像`；
- 派生节点保留源图引用，使用本地图片作为 prototype 可见媒体；
- 派生节点的 `data.rotateMirror` 只记录 source identity 和原型状态，不伪造
  真实角度或镜像结果；
- 新节点创建后自动成为唯一选中节点；
- 一次 undo 删除 node 和 edge，一次 redo 恢复；
- action 在当前本地图片有 `imageUrl` 时可用，无媒体时保持 no-op；
- 本地 UI 反馈明确标注为 prototype，不把本地派生图写成真实处理结果。

## 接力入口

- [`PLAN.md`](PLAN.md)：实施步骤和验收门；
- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)：source fact、inference 和 clone decision；
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)：代码、验证和提交历史；
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：本批截图首次识别结果。
