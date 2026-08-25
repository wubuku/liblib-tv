# LibTV 画布 Batch 5 实施记录

> 状态：源码实施、专项验证和完整 `npm run check` 完成  
> 最后更新：2026-08-25

## 1. 实施内容

### 1.1 移动事务

`src/app/page.tsx` 的 drag transaction 现在记录：

- 拖动开始时的 graph snapshot；
- 本次拖动的节点集合；
- 以当前 `canvasStore` 中的最终节点位置作为 drag stop 结果。

drag stop 行为：

- 多选节点拖动时不再只显式覆盖最后一个 `node`；
- group 拖动时保留 React Flow 写回的 group/child 关系；
- 有实际位移时只写入一个 history snapshot；
- 没有实际位移时不产生空 history step；
- undo/redo 不把 selection 或 viewport 写入 graph history。

### 1.2 选择集合复制

`src/store/canvasStore.ts` 新增 `duplicateSelectedNodes()`：

- 单选和多选均从 `selectedNodeIds` 读取，兼容 `selectedNodeId`；
- 每个副本沿用现有 `{ x: 40, y: 40 }` 画布偏移；
- 多选只复制选择集合内部的边；单选普通节点保留已有的所有关联边复制语义；group 选择遵循结构复制规则；
- 复制边时将 source/target 映射到对应副本；
- 选择 group 时自动复制直接 children；
- group children 使用新的 `parentId`；
- 只选择 child 而未选择 group 时，副本解除旧 parent，转换为顶层绝对坐标；
- 整个复制动作只进入一个 history step；
- 复制完成后只选中用户原本选择的对应副本根节点。

`Cmd/Ctrl+D` 已切换到 `duplicateSelectedNodes()`。原有 `duplicateNode()` API 保留，避免影响其他潜在调用。

## 2. 验证结果

### Batch4 回归

```bash
python3 scripts/verify-liblib-batch4.py
```

通过：

- 10 节点、11 边基线；
- 多选、成组、解组；
- 批量删除；
- undo；
- 桌面与移动；
- 控制台错误为 0。

### Batch5 专项

```bash
python3 scripts/verify-liblib-batch5.py
```

通过：

- 多选图片/视频拖动后两者屏幕位移一致；
- 多选拖动一次 undo 恢复、一次 redo 重做；
- group 拖动后 group、图片 child、视频 child 屏幕位移一致；
- group 拖动 undo 恢复；
- 多选复制从 10 节点/11 边变为 12 节点/12 边；
- 单选复制保持原有兼容结果，从 10 节点/11 边变为 11 节点/14 边；
- 多选复制后副本整体 selected，图片/视频单节点浮层不出现；
- 复制 undo/redo 是单个 graph history step；
- 复制 group 从 11 节点/3 group 变为 14 节点/4 group；
- group 副本与 child 副本的屏幕位移一致，说明 child 未回挂原 group；
- 移动端 `390x844` 无横向溢出；
- 控制台错误为 0。

### 完整工程检查

```bash
npm run check
```

通过：

- lint：0 error，保留仓库既有 9 个 warning；
- `tsc --noEmit`：通过；
- Next.js production build：通过；
- `/`、`/frameos` 和 `/frameos/canvas/[id]` 均完成构建。

验证脚本还生成：

- `docs/design-references/liblib-clone-batch5-multi-drag-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch5-group-drag-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch5-multi-duplicate-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch5-group-duplicate-desktop-2026-08-25.png`
- `docs/design-references/liblib-clone-batch5-mobile-390-2026-08-25.png`

## 3. 重要行为边界

- 当前项目已有的 `undo` / `redo` 会在恢复 graph 后清空 selection；因此复制完成后的即时 selection 已验证，redo 后不把旧 selection 作为验收条件。
- group 的 parent/child 复制规则是当前 clone 为了避免孤儿引用而做的可逆实现决策，不是原站已提取的内部算法。
- `Option/Alt+拖动`、`L`、`Option/Alt+G` 仍不实现；原站快捷键文案存在，但流程证据不足。
- 没有引入系统剪贴板，不宣称跨应用复制。

## 4. 关键文件

- [`src/app/page.tsx`](../../../src/app/page.tsx)
- [`src/store/canvasStore.ts`](../../../src/store/canvasStore.ts)
- [`scripts/verify-liblib-batch5.py`](../../../scripts/verify-liblib-batch5.py)
- [`PLAN.md`](PLAN.md)
- [`MULTI_MOVE.spec.md`](MULTI_MOVE.spec.md)
- [`DUPLICATE_SELECTION.spec.md`](DUPLICATE_SELECTION.spec.md)

## 5. 下一批候选

在取得新的原站实时交互证据前，暂缓：

- `Option/Alt+拖动` 复制；
- `L` 快捷键连线；
- `Option/Alt+G` 合并分镜组；
- LibTV 专属对齐辅助线；
- 节点锁定/隐藏；
- 真实系统剪贴板。

优先级较高但需要重新观察原站的方向：

1. 右键节点/空白画布的真实菜单；
2. 节点 hover、按住和拖动中的浮层/Handle 状态；
3. group 真实视觉边界、标题和组内关系；
4. 画布视口与 history 的真实关联。

## 6. 提交接力

本批提交并推送后，以本文、`PLAN.md` 和验证脚本作为下一会话的恢复入口。提交哈希在推送后回填到 git 历史，不在提交前手写易失值。
