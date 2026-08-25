# Batch 12 计划：资产管理抽屉的画布/资产视图

## 1. 缺口与价值

| 缺口 | 当前状态 | 影响 | 价值 | 决策 |
|---|---|---|---:|---|
| 资产页签死按钮 | 只有“画布”列表可用 | 抽屉暴露了无法操作的入口 | 4 | 实现 |
| 资产来源不明确 | 当前没有服务端账户资产 | 容易伪装成真实资产库 | 3 | 明确为本地派生视图 |
| 节点选择重复实现 | 画布页签已有选择逻辑 | 两个视图可能选择行为不一致 | 4 | 抽成同一列表行为 |

## 2. 实施步骤

1. 在 `AssetManagerPanel` 增加 `activeTab: "canvas" | "assets"`。
2. 将当前节点行抽成复用的本地列表渲染逻辑。
3. 为资产视图过滤 `image` 和 `video` 节点，并展示空态。
4. 增加稳定的 tab/list/item selectors。
5. 不改变 store 数据结构；使用现有 `selectNode`。
6. 添加 Batch 12 Playwright，验证页签、过滤、选择、关闭和移动端边界。

## 3. 非目标

- 不实现真实上传、账户资产、搜索、排序、下载或持久化。
- 不新增服务端 API。
- 不改变 Batch 11 顶层 overlay 互斥规则。
- 不重新识别已有原站截图。

## 4. 验证

- `python3 scripts/verify-liblib-batch12.py`
- Batch 4-12 回归
- `npm run docs:check`
- `npm run check`
