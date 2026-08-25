# Batch 11 计划：画布壳层浮层互斥与生命周期

## 1. 缺口

| 缺口 | 当前状态 | 影响 | 价值 | 决策 |
|---|---|---|---:|---|
| 主入口面板状态分散 | `LeftSidebar` 使用局部 `activePanel`，其余入口在 `uiStore` | `closeAllPanels` 不完整，连续点击会残留覆盖层 | 5 | 实现 |
| 顶层 overlay 不互斥 | Agent、分享、资产、快捷键、画布下拉各自 toggle | 画布可同时被多个浮层覆盖 | 5 | 实现 |
| 模式切换与面板生命周期不统一 | 分镜自动打开 Agent，但其他 panel 可能仍在 | 模式切换后出现旧上下文 | 4 | 实现 |
| Escape 关闭范围不完整 | 页面只调用 `closeAllPanels` | 局部底部面板可能残留 | 4 | 实现 |
| 面板内部业务行为 | 多数已是本地 mock | 不属于本批高价值范围 | 2 | 暂缓 |

## 2. 方案

1. 在 `uiStore` 增加 `activePrimaryPanel` 和 `togglePrimaryPanel`。
2. 将 `LeftSidebar` 的 `activePanel` 改为 store 状态。
3. 为添加节点、快捷键、画布下拉、资产、分享和 Agent 建立互斥开关。
4. 让 `closeAllPanels` 清理所有顶层状态。
5. 为当前可见 overlay 增加稳定 `data-liblib-overlay` 选择器，供 Batch 11 Playwright 使用。
6. 保持现有面板几何和内容不变。

## 3. 非目标

- 不重新识别原站截图；
- 不修改节点、边、React Flow viewport 或生成面板内容；
- 不实现真实分享、Agent、上传、账户和持久化；
- 不调整 FrameOS 的 store 或 overlay。

## 4. 验证

- 新增 `scripts/verify-liblib-batch11.py`；
- 验证 desktop `929x874` 和 mobile `390x844` 的 overlay 生命周期；
- 运行 Batch 4-11 回归、`npm run docs:check` 和 `npm run check`。
