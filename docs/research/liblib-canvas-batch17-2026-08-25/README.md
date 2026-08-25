# Batch 17：资产管理上下文与层级浏览

> 日期：2026-08-25
> 范围：LibTV clone 左侧资产管理抽屉及其与项目/当前画布的上下文关系。
> 目标：修复扁平、硬编码的资产抽屉，使其成为可辨认当前项目和画布的节点导航器。

## 当前缺口

- 抽屉列表标题硬编码为 `画布 2`，切换 active canvas 后显示错误。
- 原站抽屉顶部展示 `项目名 | 当前画布`，clone 没有项目上下文。
- 原站节点区标题为 `画布元素`，并显示排序、`全部` 筛选和搜索；clone 只显示一行标题。
- 原站画布元素按组呈现，视频组下缩进失败视频；clone 把 parent/child 全部扁平化。
- 空画布在“画布”页签也显示“暂无媒体资产”，语义错误。

## 证据入口

- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)：原站和旧 clone 资产管理截图的一次性识图。
- [`ASSET_CONTEXT_TREE.spec.md`](ASSET_CONTEXT_TREE.spec.md)：本批结构和行为合同。
- [`../liblib-canvas-batch12-2026-08-25/`](../liblib-canvas-batch12-2026-08-25/)：资产页签与节点选择的既有合同。
- [`../../design-references/liblib-original-asset-manager-2026-08-25.png`](../../design-references/liblib-original-asset-manager-2026-08-25.png)：原站抽屉证据。

## 边界

- 节点树、筛选和搜索只基于当前 active canvas 的 Zustand 数据。
- `资产` 仍是当前画布图片/视频的本地派生视图，不连接账户资产。
- 原站筛选菜单展开态没有保存证据；具体筛选选项属于保守的 clone-only 原型。
- 不重写节点缩略图素材，不新增上传、下载或服务端排序。

## 导航

- [`PLAN.md`](PLAN.md)
- [`ASSET_CONTEXT_TREE.spec.md`](ASSET_CONTEXT_TREE.spec.md)
- [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
