# Batch 345 — lint 基线收敛与工作流 chrome 几何巡检（`HYGIENE_RECORDED`）

> 状态：lint 基线 **8 warnings → 0**（0 errors 不变）；工作流底部
> 双簇几何对照完成（与源站 2026-09-11 直证对齐，仅 16px 级偏移与
> 一个 SOURCE_UNKNOWN 返回箭头）；维护集 46 项全绿。

## 几何巡检结论（源站 2026-09-11 直证坐标 vs clone 实测 1920px）

- 中簇（添加节点@800 → 教程@1088）与源站（816 → 1105+28）对齐，
  顺序一致，~16px 居中偏移在容差内；
- 左簇（资产管理@16 → 缩放@259）顺序与源站一致（源站 69 起始的
  前置差异源于源站左缘有一个语义未知的「←」返回箭头
  （SOURCE_UNKNOWN，不做伪造）；
- 空画布空态（双击画布/自由生成节点 + 4 chips）与 2026-09-11
  直证逐字一致（batch 100/207 覆盖，无漂移）。

## Lint 收敛明细（8 → 0）

- frameos page：未用 `DeletableEdge` 导入移除；onNodeContextMenu
  依赖数组移除未用的 `removeNode`（onClick 走 requestConfirm）；
- CustomHandle：未用 `useCallback` 移除；
- FrameosContextMenu：未用 `useFrameosStore` 移除；
- FrameosGenerationOverlay：失效的 eslint-disable 移除；
- DirectorInspector：DOM 回填 effect 的故意收窄依赖加归档注释的
  定向 disable（disable 指向依赖数组行）；
- FrameosImage/VideoNode：`<img>` 保留（画布节点位图动态缩放，
  FrameOS 路线），加归档注释的定向 disable。

## 验收

- `npm run check`：编译成功，**0 errors / 0 warnings**；
- 维护集 46 项全绿（DirectorInspector 变更无回归）；
- docs check 通过（904 Markdown）。

## 后续候选

- 源站恢复后 BLOCKED_SOURCE 补采与 CLONE_DECISION 替换；
- 源站左缘返回箭头身份采样（恢复后）；
- 新表面随源站更新巡检。
