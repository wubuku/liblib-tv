# LibTV 画布 Batch 4 实施记录

> 状态：源码实施、构建和跨尺寸回归完成
> 最后更新：2026-08-25

## 已完成

- 复核 Batch3 的证据纠偏和遗留候选；
- 确认当前原站快捷键面板仍有成组、解组、合并分镜组、连线和 Option+拖动文案；
- 确认当前 LibTV 克隆已经打开 React Flow 框选基础，但 store/render 仍强制单选；
- 建立本目录的计划、状态契约和分组数据契约。

## 已实施

- `canvasStore` 新增 `selectedNodeIds`，保留 `selectedNodeId` 作为单节点面板兼容字段；
- `page.tsx` 接入 React Flow `onSelectionChange` 和框选状态；
- 支持 Meta/Control 多选、空白取消选择和 `SelectionMode.Partial` 框选；
- `G` 对至少两个普通顶层节点创建 `storyboard-group`；
- group 与子节点通过 `parentId` 建立 React Flow 父子关系；
- `Shift+G` 将选中 group 或其子节点解组并恢复绝对坐标；
- `Delete` 支持批量删除多选节点及其关联边；
- 成组、解组、批量删除均进入现有 per-canvas history；
- 多选时隐藏图片/视频的单节点编辑浮层；
- 快捷键面板加入已经闭环的 `G`、`Shift+G`，未实现的 `Option+G`、`L` 和 Option+拖动仍不展示；
- 修复受控选择回写导致的 React update-depth 循环，并为选择写回增加幂等保护。

## 当前验证结果

已通过桌面与移动交互回归：

- 初始节点数：`10`；
- Meta 多选图片和视频：选中数 `2`；
- 多选时图片工具条、图片编辑面板、视频生成面板均不出现；
- `G` 后节点数 `11`，group 节点数 `3`；
- `Shift+G` 后节点数 `10`，group 节点数 `2`；
- 批量删除后节点数 `8`，`Meta+Z` 恢复为 `10`，`Meta+Shift+Z` 重做为 `8`；
- `390x844` 下节点数 `10`，`document` 和 `body` 均无横向溢出；
- 控制台错误数：`0`。

完整工程检查：

- `npm run check` 通过；
- lint 保留仓库既有 9 个 warning，无 error；
- build 通过；
- `/frameos/canvas/demo` 随同生产构建通过。

可复用脚本：

```bash
python3 scripts/verify-liblib-batch4.py
```

脚本还会验证批量删除、`Meta+Z` 恢复和 `390x844` 横向溢出，并生成：

- `docs/design-references/liblib-clone-batch4-grouped-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch4-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch4-mobile-390-2026-08-25.png`
- `docs/design-references/liblib-clone-batch4-initial-2026-08-25.png`
- `docs/design-references/liblib-clone-batch4-grouping-desktop-2026-08-25.png`

## 后续候选

- 重新取得原站实时证据后，再评估 `Option/Alt+G` 合并分镜组；
- 重新取得原站端点选择流程后，再评估 `L` 连线快捷键；
- 重新取得原站拖动状态后，再评估 `Option/Alt+拖动` 节点复制；
- 不要根据本批的 `parentId` 原型实现反推原站的组内视觉。

## 证据边界

这轮实施记录不得把 `parentId` 的具体转换、`32px` 外扩、组标题“组合节点”或默认组壳层称为原站实时事实。它们是为前端原型闭环选取的可逆实现决策。
