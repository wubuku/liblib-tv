# LibTV 画布 Batch 3：命令基础

> 建档日期：2026-08-25  
> 目标：在已有 LibTV 画布壳层、节点体系和 Seedance 2.5 工作流之上，补齐高频画布命令的前端闭环。  
> 范围：只做画布 UI/UX 原型，不接入后端、账户、真实剪贴板协议或生成服务。

## 本批结论

已有研究已经覆盖了 LibTV 的主壳层、节点拓扑、图片/视频上下文面板、Seedance 2.5 能力和入口面板。本批继续评估后，最高价值的缺口不在更多单一模型参数，而在用户对节点图进行重复编辑时缺少稳定的命令基础：

1. 画布操作不能统一撤销/重做；
2. 节点只能通过添加面板创建，缺少节点级复制；
3. 画布没有节点/空白处的上下文菜单；
4. 快捷键面板展示的命令与实际行为不一致；
5. 在画布指定位置添加节点的操作闭环缺失。

## 证据边界

本批使用的原站证据来自既有登录态审计和截图，尤其是：

- [`../liblib-live-2026-08-25/README.md`](../liblib-live-2026-08-25/README.md)
- [`../liblib-live-2026-08-25/panel-audit.json`](../liblib-live-2026-08-25/panel-audit.json)
- [`../liblib-live-2026-08-25/BATCH_1_PANELS.md`](../liblib-live-2026-08-25/BATCH_1_PANELS.md)
- [`../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)

本轮没有把无法安全接管的有头浏览器写成新的实时实测。实现前事实以已有证据、当前源码和已有截图为准；完成后新增的截图只证明克隆行为。

## 文档索引

| 文档 | 内容 |
|---|---|
| [`PLAN.md`](PLAN.md) | 缺口盘点、价值排序、批次范围、验收标准 |
| [`COMMAND_HISTORY.spec.md`](COMMAND_HISTORY.spec.md) | 每画布历史栈和命令边界 |
| [`CONTEXT_MENU.spec.md`](CONTEXT_MENU.spec.md) | 暂缓的节点/画布空白处右键菜单候选 |
| [`KEYBOARD_SHORTCUTS.spec.md`](KEYBOARD_SHORTCUTS.spec.md) | 快捷键展示与实际行为对照 |
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | 实施文件、验证记录、已知差异和后续接力 |

## 与既有批次的关系

- Batch 1：主工具栏入口面板和锚点关系。
- Seedance 批次：图片、视频、逐帧拉片、智能剪辑和 Seedance 2.5 工作流。
- Batch 3：不改变这些节点的视觉合同，重点补充跨节点的编辑命令。
