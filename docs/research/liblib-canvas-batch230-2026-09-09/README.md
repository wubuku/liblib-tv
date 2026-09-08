# Batch 230 — 画布节点与 storyboard-group 结构采样（源站测试项目已清空）

## 发现

- 源站测试项目（disposable）在多轮清理后画布为空（0 节点、0 边）。
- 预设分镜图/视频组 storyboard-group 节点属于**原始项目**而非测试项目，
  需在原始项目中采样（涉及在用户原始项目中操作的风险）。
- clone 的 StoryboardGroupNode 已通过 canvas-2 预设节点的面板级对齐
  （batch 149–218）充分覆盖。

## 处置

- 证据批（部分完成），零代码改动。
- 源站测试项目已清零。
- storyboard-group 源站结构留待后续在原始项目中采样（需用户确认）。

## 验收

- `npm run check`：0 errors（8 warnings 基线）
- 源站画布 0 残留
