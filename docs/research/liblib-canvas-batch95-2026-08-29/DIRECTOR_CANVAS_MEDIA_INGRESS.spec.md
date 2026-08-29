# Director 画布媒体入口合同

> 状态：`CLONE_RELIABILITY_CONTRACT` / `SESSION_ONLY`
>
> 本文不描述 LibTV 原站 exact 实现。

## 1. Typed input

```ts
interface DirectorCanvasMediaInputV1 {
  sourceNodeId: string;
  sourceKind: "panorama" | "image";
  filename: string;
  imageUrl: string;
  width: number;
  height: number;
}
```

输入生产规则：

1. `canvas.id` 必须等于 Director owner 的 `canvasId`；
2. edge 的 `target` 必须等于当前 Director `sourceNodeId`；
3. source node 的 `type` 必须是 `image`；
4. `data.imageUrl` 必须是非空字符串；
5. `filename`、`width`、`height` 从节点数据读取并进行安全默认；
6. `editorVariant === "panorama"` 或 `placeholderKind === "panorama"` 时标记
   `sourceKind="panorama"`，否则标记为 `image`；
7. 不接受只含 placeholder 的 panorama node。

## 2. Session projection

DirectorDesk 持有当前 `selectedSourceNodeId`。它是 UI session state，不是
Director project document：

- 初始值：第一个可用 input 的 `sourceNodeId`；
- 当前 source 从候选列表消失：清除；
- 用户切换：更新当前 viewport projection；
- 清除：viewport 回到纯色背景；
- Director close：丢弃选择；
- Director project export/import：不包含该选择。

这样保持三层边界：

```text
canvas graph node/edge
  -> typed host input
  -> Director session-only projection
  -> Three.js Texture/Object3D runtime
```

## 3. Runtime behavior

- 有效 input：加载 URL，`[data-director-panorama-state]` 从 `loading` 变为
  `ready`，存在 `[data-director-panorama-runtime]`；
- 加载失败：state 为 `error`，显示短反馈，普通 Director scene 仍可用；
- 清除或 URL 变化：旧 texture dispose；旧 runtime surface 不再存在；
- 环境球使用 `BackSide`/反向几何语义，不参与对象 selection；
- `isCapturing` 时仍作为场景内容参与 capture，但不显示 Inspector helper。

## 4. Failure and stale handling

- 没有候选：`empty`，不创建 placeholder 资产；
- 当前候选被删除或换画布：`empty`；
- 浏览器纹理失败：`error`，不修改 graph/history/document；
- source node data URL 变更：当前 input descriptor 更新，旧 texture 清理；
- 任何异常都不得破坏 Director close、project export、camera 或 timeline。

## 5. Verification assertions

- static：helper、DirectorDesk、DirectorInspector、DirectorViewport 和 verifier
  都有明确入口；
- desktop/mobile：输入选择器与状态 surface 可发现；
- runtime：默认/切换/清除/stale/error；
- diagnostics：console errors、page errors、request failures 均为零；
- persistence：导出 JSON 不包含 `panorama` session selector；
- screenshot recognition：本批不执行。

