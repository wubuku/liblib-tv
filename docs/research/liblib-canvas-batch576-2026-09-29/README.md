# Batch 576 — 运动轨迹页签关键帧选中态编辑字段（WIP，构建通过）

> 状态：`WIP_BUILDABLE`（构建通过、563/36 回归绿；收尾指令下留档，
> 交互断言留待后续批次验收）。源站证据：batch 571 续2（截图 64）——
> 运动轨迹页签在关键帧选中态展示编辑字段组（时长/位置/旋转/缩放/
> 统一缩放，镜像选中关键帧值）。

## 已实现

- DirectorCameraMotionTab 读 store：selectedObjectId + timeline →
  定位摄像机变换/相机轨道上 `selectedKeyframeId` 对应的关键帧；
- 关键帧选中时渲染「关键帧 {time}s」编辑字段组：位置/旋转/缩放
  三轴输入（镜像 `keyframe.value`，相机轨道值取 `.transform`），
  onChange 经 `updateObjectTransform` 在当前播头提交（autoKeyframe 开
  时更新该关键帧）；统一缩放只读显示；无选中时该 section 不渲染。

## 待后续批次

- 交互断言 verifier（选中→字段镜像→编辑→关键帧更新的往返）；
- 时长滑杆语义（运动路径时长 vs 关键帧时间）；
- batch 563 verifier 扩展运动页签编辑断言。

## 回归现状

- batch 563（17 检查）/36 全绿；typecheck 净；lint 0 error；
  `next build` ✓ Compiled successfully。
