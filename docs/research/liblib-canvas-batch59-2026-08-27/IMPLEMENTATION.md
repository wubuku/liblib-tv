# Batch 59 实施记录：Director 资源库浏览与加入场景

> 状态：`SCRIPT_RECORDED_PASS`（focused verifier、Batch 47/48
> 兼容回归和实现已完成；全量质量门禁与 checkpoint 在本轮 closeout 后补记）。

## 变更历史

| 时间 | 变更 | 结果 |
|---|---|---|
| 2026-08-27 | 建立 Batch 59 研究目录和接力入口 | 已完成 |
| 2026-08-27 | 记录源站重定向与登录弹窗边界 | 已完成 |
| 2026-08-27 | 规划资源库 query/preview/add-object slice | 已完成 |
| 2026-08-27 | 新增 typed query/selection helper、搜索、预览和显式加入场景 | 已完成 |
| 2026-08-27 | 首次兼容回归 | 发现预览区重复资源名破坏 Batch 47 文本计数 |
| 2026-08-27 | 去除预览区重复标题并保留现有资源卡文案 | Batch 47 恢复通过 |
| 2026-08-27 | 第二次兼容回归 | 发现预览按钮替代卡片主体命中，破坏旧快速加入路径 |
| 2026-08-27 | 分离卡片主体快速加入与右上角预览按钮 | Batch 47/48 恢复通过 |
| 2026-08-27 | focused Playwright | 已通过；见 `runtime-audit.json` |
| 2026-08-27 | `npm run lint`、`npm run typecheck`、`git diff --check` | 已通过；lint 仅保留 9 条既有 warning |
| 待补 | `npm run check`、文档校验和相邻回归 closeout | 待本轮执行 |
| 待补 | commit/push checkpoint | 待本轮执行 |

## 实际代码范围

- `src/components/director/directorModelLibrary.ts`
  - 新增 `DirectorModelLibraryQuery` 和
    `DirectorModelLibrarySelection`；
  - 新增按 category/search 过滤的纯 helper；
  - 新增稳定的分类显示名查询。
- `src/components/director/DirectorViewport.tsx`
  - 在现有资源库 surface 中加入搜索状态；
  - 加入独立 preview selection，不修改 scene objects；
  - 加入 preview panel、显式“加入场景”和搜索空结果；
  - 保留历史资源卡主体“点击即加入”的兼容路径。
- `scripts/verify-liblib-batch59.py`
  - 覆盖 desktop/mobile、搜索、preview-only、显式插入、
    对象树/Inspector continuity、graph isolation 和 diagnostics。

本批没有修改 `directorStore` 或普通 `canvasStore`。对象插入继续复用已有
`addLibraryObject` contract；query/preview 是 Director viewport 局部 UI
状态，不进入普通画布 graph/history。

## 实施结果

完成后的工作流是：

```text
打开资源库
  -> 切换五个已有分类
  -> 搜索资源
  -> 右上角预览按钮只改变 preview selection
  -> 显式加入场景
  -> 新 proxy object 成为对象树与 Inspector 当前选择
```

关键兼容决策：

- 卡片主体继续执行既有快速加入，避免改变 Batch 47 的历史操作合同；
- 预览按钮拥有独立事件边界，点击后资源库保持打开且场景对象不变；
- 搜索结果变化时，preview selection 收敛到首个可见资源；无结果时卸载
  preview panel 并显示稳定空态；
- 插入对象保留 `libraryAssetId`，加入后可直接在 Inspector 编辑 transform；
- 资源库操作不改变普通画布 nodes、edges 或 history 长度。

## 验证记录

`scripts/verify-liblib-batch59.py` 已记录：

```json
{
  "initial_director_object_count": 5,
  "final_director_object_count": 6,
  "added_asset_id": "proxy-home-lamp",
  "graph_unchanged": true,
  "status": "SCRIPT_RECORDED_PASS"
}
```

Focused 覆盖：

- 五个既有资源分类和资源卡数量；
- 搜索“台灯”、preview-only selection 和显式插入
  `proxy-home-lamp`；
- 对象树选中、Inspector `prop` 分支和 transform fields；
- 搜索无结果、清空恢复和 Escape 关闭；
- desktop/mobile panel bounds、WebGL nonblank 和 no-overflow；
- console/page/request errors 为空；
- 普通画布 graph/history 不变。

相邻兼容回归：

- `python3 scripts/verify-liblib-batch47.py`：通过；
- `python3 scripts/verify-liblib-batch48.py`：通过。

质量门禁在本轮最终 closeout 后补写，不能仅以 focused verifier 代替
`npm run check` 和文档链接校验。

## 保留边界

本批不实现真实 FBX/OBJ mesh loading、远程资源、账户状态、普通画布 graph
transaction 或 source-exact LibTV resource library。当前资源分类、卡片视觉
和 proxy object 都是 clone-owned bounded contract；本轮源站只证明首页有
Director 入口且登录门槛阻止了认证后资源库取证。

## Checkpoint

规划 checkpoint：`35d3100`（已 push）。
实施 checkpoint、最终质量门禁、push 和工作区状态在完成后补写。
