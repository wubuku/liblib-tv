# LibTV 画布 Batch 10 实施记录

> 状态：规划已完成，实施中
> 最后更新：2026-08-25

## 1. 规划与证据

- 复核同一登录态原站五个图片节点的 DOM 状态；
- 将高度、Prompt、参考图、顶部入口、placeholder 和 footer 控件矩形固化为状态矩阵；
- 确认 `咖啡馆` 是“有 Prompt 但仍为 191px”的直接反例；
- 确认只有带 references 的 `分镜 #2` 显示“参考”入口；
- 确认顶部没有 AutoLink 文字 pill；
- 复用 Batch 9 原站识图记录，没有重复打开整张原站截图；
- 定义每个节点使用独立 Playwright page，防止派生状态污染。

## 2. 待实施

- 图片节点显式 `editorHeight`；
- 完整 Prompt 和 placeholder；
- 顶部入口与控件尺寸；
- footer 图标、AutoLink 入口和稳定 selector；
- Batch 10 专项验证与截图；
- 跨批回归、工程检查、文档更新、commit/push。

## 3. 提交记录

待本批完成后补充。

