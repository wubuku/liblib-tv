# Batch 215 — 参考/标记前置采样（素材连线后仍惰性）+ 特效 pill「替换」对齐

## 源站事实（窗口 rAF ~31fps；`source-pill-material-precondition.json` / 截图存档）

- 以特效卡流程建立素材连线（素材节点 → 视频节点，edges=1）后：
  - **特效 pill 文案变「替换」**（工具条读
    参考/标记/角色库/运镜/特效替换——特效已应用即变更为替换语义）；
  - 参考/标记点击**仍惰性**（无弹层——真实前置仍需上传/生成内容）。
- 画布出现「取消选择」圈选 UI（525×525，特效应用态的一部分）。

## 实施

- `VideoGenerationPanel`：新增 `effectApplied` / `onEffectApplied` props；
  特效卡点击 → `onEffectApplied()`；工具条特效 pill 文案
  `特效` → `effectApplied ? "替换" : "特效"`（替换语义直采自源站）。
- `VideoNode`：持 `effectApplied` 状态并下传；`onEffectApplied` 接
  `setEffectApplied(true)`。
- `verify-liblib-batch215.py`（4 checks）：应用前特效 pill 存在 → 点
  特效卡 → 替换出现且特效消失。

## 验收

- `verify-liblib-batch215.py`：4 checks 全绿。
- 回归绿：213 / 191 / 192 / 22 / 172。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：源站替换点击后的再次选用流程；取消选择的完整圈选交互。
- 源站测试残留清理：采样节点已删（0 残留）。
