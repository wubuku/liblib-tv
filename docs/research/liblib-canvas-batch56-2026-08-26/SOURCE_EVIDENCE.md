# Batch 56 源站证据与 clone 决策

## 1. 直接证据

当前可复用的源站观察来自共享画布上的一次安全恢复操作：

```text
点击 image-toolbar-rotate
  -> 新增图片节点
  -> 节点名称：旋转与镜像
  -> 新节点被选中
Meta+Z
  -> 新节点消失
  -> graph 恢复
```

完整记录见：

- [`../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md#34-旋转与镜像)
- [`../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md#13-元素编辑与旋转入口的安全边界)
- [`../open-canvas-2026-08-26/EVIDENCE_MATRIX.md`](../open-canvas-2026-08-26/EVIDENCE_MATRIX.md#3-1-当前-libtv-源站补充声明)

## 2. 证据分层

### Source fact

- 入口 test id：`image-toolbar-rotate`；
- 点击后的可见名称：`旋转与镜像`；
- 点击后存在新增并选中的节点；
- 一次撤销可回到操作前 graph；
- 角度、水平翻转、垂直翻转、natural size 和保存上传路径只由 bundle
  静态审计或未完成 live 路径提示，不能作为本批交互事实。

### Inference

- 源站至少有一条入口路径会把旋转工作流投影为 graph-visible node；
- 新节点与 source 的关系应使用 edge 表达，而不是只改当前 node CSS；
- selection 是该入口动作的可见结果之一。

### Clone decision

本地最小复刻使用：

```text
ImageNode
  -> addDerivedNode("image", data.rotateMirror)
  -> source edge
  -> select derived
  -> atomic undo/redo
```

派生节点本地复用 source `imageUrl`，只是为了让 clone verifier 有可见媒体和
稳定 DOM；它不表示旋转、镜像或真实 bitmap 已完成。

## 3. 明确未知

- source 派生节点是否立即包含真实处理 bitmap；
- source 派生节点的最终 width/height；
- 旋转面板的控件、默认角度和镜像按钮；
- 无修改退出是否直接关闭；
- dirty 状态 modal 的精确文案和 focus；
- 保存是更新当前节点还是创建/复用输出节点；
- 是否上传、是否需要任务、是否产生费用；
- 无媒体、权限不足、失败任务和重复入口的处理。

这些未知不在本批中用猜测填充。
