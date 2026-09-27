# Batch 534 — 自写会话 ↔ 脚本生成器卡转换（生命周期联动）

> 状态：`SCRIPT_RECORDED_PASS`（commit 本批）。源站实测（截图 39 + 画布
> DOM 巡检）：自写分镜会话后，脚本生成器卡持久转为进度卡形态（画布在
> 浏览器重启后仍显示进度卡，证明跨会话持久）。本批把 batch 531-533 家族
> 收敛为完整生命周期：三入口卡 → 自写会话 → 进度卡 → 重入编辑器。

## 合同

- 会话前：三入口卡（batch 116/528 形态），生成入口跟随可用；
- 单击「自己编写分镜脚本」→ `setStoryboardSessionNode(id)` 记录会话节点
  + 打开全屏编辑器（batch 531/532 合同不变）；
- 会话后本卡渲染进度形态：①确认镜头—②准备资产—③合成提示词
  （batch 533 同款步进条）+「打开脚本节点 →」（重入编辑器）；三入口/
  参考图/提示词/GVLM 徽标不再显示（与源站进度卡一致）；
- 转换持久：`storyboardSessionNodeId` 有意不进 closedOverlayState——
  工具箱等其他面板开合不回退（CLONE_DECISION：源站跨浏览器重启仍持久，
  clone 以页面会话内持久近似）；
- 531 verifier 重入步骤改为进度卡按钮（对齐源站流程），合同其余不变。

## 内容

- `src/store/uiStore.ts`（storyboardSessionNodeId + setter；主初始态含
  null，closedOverlayState 不重置并留注释）；
- `src/components/nodes/ScriptGeneratorNode.tsx`（inStoryboardSession
  分支渲染进度形态）；
- `scripts/verify-liblib-batch534.py`（11 检查：会话前跟随、转换、
  持久性、重入往返）；
- `scripts/verify-liblib-batch531.py`（重入步骤对齐源站流程）；
- 回归：batch 531/528/116 全绿；lint 0 error。
- `runtime-audit.json`：本目录。
