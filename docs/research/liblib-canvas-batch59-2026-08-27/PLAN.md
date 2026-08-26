# Batch 59 计划：Director 资源库浏览与加入场景

> 建档：2026-08-27  
> 领域：Director Desk，clone-owned bounded prototype  
> 风险：中。只改 Director store/UI 和本地 verifier，不改普通画布 graph
> transaction，不引入真实远程资源或生产持久化。

## 1. 缺口与价值

| 候选 | 用户价值 | 现有基础 | 风险 | 决策 |
|---|---:|---|---:|---|
| 资源库浏览/筛选/加入场景 | 5 | 已有 model library cards、proxy objects、Inspector | 2 | 本批实施 |
| 真实 FBX/OBJ mesh loading | 4 | 只有描述符和 proxy | 5 | 保持 blocked |
| 远程资源同步/权限 | 4 | 无后端合同 | 5 | out of scope |
| Director capture 后续细节 | 3 | Batch 46 已成熟 | 2 | 暂不扩展 |
| 普通画布双浮层进一步复核 | 5 | 证据强但不属于本批 Director 最高优先级 | 3 | 下一候选 |

## 2. 本批目标

实现一个可重复验证的 clone-owned 资源库切片：

```text
library trigger
  -> category tabs
  -> search/filter
  -> selected preview
  -> add object
  -> object-tree selection + Inspector continuity
```

覆盖：

- Director viewport/library 入口；
- `模型 / 环境 / 我的模型` 分类；
- 文本搜索和空结果状态；
- 资源卡片的选中/预览反馈；
- 将 catalog item 加入场景，保留 stable asset identity；
- 加入后对象树选中，Inspector 能继续编辑 transform/visibility/color；
- desktop/mobile drawer bounds 和 no-overflow。

## 3. 明确不做

- 真实 FBX/OBJ 解析、GLTF/纹理加载或 WebGL asset pipeline；
- 远程 API、上传、账号、会员、积分、权限和协作；
- 把上游项目的具体 CSS 尺寸写成 LibTV 事实；
- 修改普通 LibTV route、FrameOS route、React Flow graph/history；
- 把资源库筛选结果写入普通画布 persistence；
- 未经 source evidence 支持的批量摆放、拖放、收藏和排序。

## 4. 实施顺序

1. 固化 source access boundary 和既有证据；
2. 定义 typed library query/selection/preview contract；
3. 接入 Director store 的本地 query state 和 proxy insertion；
4. 在 Inspector/viewport 中提供入口和响应式 surface；
5. 新增 focused Playwright，覆盖模型/环境/我的模型、搜索、预览、加入和
   Inspector continuity；
6. 运行 Director 相邻回归、`npm run check`、文档检查和 diff 检查；
7. 更新实施/成熟度/行为文档并 commit/push。

## 5. 验收标准

### Pure/store

- catalog item 具备稳定 `assetId`、category、display name 和 visual；
- query 按 category 和 case-insensitive text 过滤；
- 空 query 结果产生稳定 empty state；
- preview selection 不改变 scene objects；
- add 操作只新增一个 serializable object，并选中它；
- 同一 catalog item 可重复加入为不同 object ID；
- object 的 `libraryAssetId` 与 `libraryCategoryId` 保持不变。

### Browser

- 三类资源 tab 可切换；
- 搜索可缩小结果，清空可恢复；
- 点击卡片显示预览态，预览关闭不改变场景；
- 加入场景后 object tree/Inspector 同步；
- 既有 transform/visibility/color 编辑仍有效；
- desktop/mobile 无横向溢出，无 console/page/request error；
- 不改变 React Flow graph/history。

## 6. 停止条件

- 需要真实资产解析或远端同步时停止在 proxy boundary；
- source 重新验证出不同的信息架构时，只更新证据与计划，不猜测覆盖；
- 若 library UI 引发 Director timeline/selection 破坏，优先修复 ownership；
- 不新增截图，除非新的布局问题无法由 DOM/geometry assertion 证明。

