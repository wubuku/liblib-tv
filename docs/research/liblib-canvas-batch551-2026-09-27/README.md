# Batch 551 — 高斯地面吸附语义（角色落地约束）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站采样（截图 45，
> 3D 场景面板）：「高斯地面吸附」开关默认开；源站语义为高斯溅射模型
> 底面贴地。clone 本地等效：角色对象 Y 不低于地面（y=0）。

## 合同

- `scene.gaussianGroundSnap`（默认开）+ `updateObjectTransform` 提交时：
  角色对象（kind === "character"）`position[1] < 0` 被夹紧为 0（持久层
  authoredObjects 落地为 0）；正值不受影响；
- **机位不参与**——截图 45 实证：吸附开启时机位 Y 仍 2.2（源站机位
  悬浮观察），且相机 runtime 位置由注视关系解算派生；
- 开关关闭 → 自由 Y（-1.5 保持）；重新开启恢复约束；
- 运行时投影说明：runtime objects 由时间线采样派生，可能覆盖
  authored 值——夹紧的持久合同以 authoredObjects 为准（verifier 按
  此断言）。

## 内容

- `src/store/directorStore.ts`（updateObjectTransform 角色落地夹紧）；
- `scripts/verify-liblib-batch551.py`（6 检查：负值夹紧、正值保留、
  关闭自由、重开约束）；
- 回归：batch 70/548/550 全绿；typecheck 净；lint 0 error。
- `runtime-audit.json`：本目录。
