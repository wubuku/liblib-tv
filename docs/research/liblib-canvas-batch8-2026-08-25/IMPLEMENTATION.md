# LibTV 画布 Batch 8 实施记录

> 状态：已完成
> 最后更新：2026-08-25

## 1. 规划与证据

- 复核原站视频组与图片组 class；
- 读取 xyflow v12 `NodeWrapper` 与 `parentLookup` 源码；
- 确认 `.parent` 只由真实 child 关系产生；
- 计算原站视频相对组位置为 `(62,62)`；
- 审计 duplicate canvas、selection duplicate、group/ungroup、delete、derived node 和 organize；
- 建立 Batch8 计划与父子关系规格。

规划已提交并推送：

```text
57880db docs: plan LibTV video group parenting batch
```

## 2. 源码实施

### 初始 hierarchy

`src/store/canvasStore.ts`：

- `v-UGQZzZOpbv.parentId = "g-EFbbHpwq5w"`；
- video 的 store position 从绝对 `(2436,50)` 改为相对 `(62,62)`；
- group 仍为绝对 `(2374,-12)`；
- React Flow 计算后的 video DOM transform 仍为 `(2436,50)`；
- parent 在 nodes 数组中先于 child，满足 xyflow v12 adoption 顺序；
- 没有设置 `extent: "parent"`。

### hierarchy 辅助

新增两个 store 内部 helper：

- `getAbsoluteNodePosition()`：沿 `parentId` 向上累加相对位置，并用 visited set 防止异常循环；
- `withDescendantIds()`：递归扩展请求节点的全部 descendants。

它们用于：

- child 单独复制时计算顶层副本位置；
- child 创建派生节点时计算世界位置；
- parented child 重新成组时计算绝对包围盒；
- 单节点删除与批量删除时级联 descendants。

### 编辑事务

- `groupSelectedNodes()` 不再拒绝已有 parentId 的普通节点；
- 新 group 的包围盒基于当前绝对位置；
- child 换 parent 时重新计算相对位置；
- 选中的旧 group 不会被误设为新 group 的 child；
- 删除 parent 时同时删除 descendants 和所有相关 edges；
- 删除 child 不自动删除已空 parent；
- duplicate canvas 与 selection duplicate 的既有 parentId 重映射逻辑继续使用。

### 整理

`src/lib/liblibOrganize.ts` 删除失败视频的独立绝对位置映射：

- video 作为 child 保留相对 `(62,62)`；
- 整理只移动顶层视频组；
- bounds 继续通过 hierarchy 计算 video 的绝对位置。

实现和专项验证已提交并推送：

```text
0cba141 feat: model LibTV video group parenting
```

## 3. 专项验证

```bash
python3 scripts/verify-liblib-batch8.py
```

验证通过：

- 初始视频组有 `.parent`，图片组没有；
- group/video 屏幕差值等于 `62 * zoom`；
- 拖动 parent 后 group/video 屏幕 delta 相同；
- parent drag undo/redo 同时恢复 hierarchy 的绝对位置；
- 拖动 child 时 parent 不移动，undo 恢复；
- 复制视频组后节点 `10 -> 12`，两个视频组都各有 child；
- 单独复制 child 后节点 `10 -> 11`、边 `11 -> 14`；
- 拖动原 parent 时原 child 跟随，顶层副本保持不动；
- 删除 source video group 后节点 `10 -> 8`、边 `11 -> 7`；
- 删除 undo 恢复 `10` 节点、`11` 边和 `.parent`；
- `929x874` 整理仍为 `28%`，child offset 保持；
- 控制台 error 为 0。

截图：

- `docs/design-references/liblib-clone-batch8-video-group-drag-2026-08-25.png`
- `docs/design-references/liblib-clone-batch8-child-copy-detached-2026-08-25.png`
- `docs/design-references/liblib-clone-batch8-organize-parenting-929-2026-08-25.png`

## 4. 跨批与工程验证

以下全部通过：

```bash
python3 scripts/verify-liblib-batch4.py
python3 scripts/verify-liblib-batch5.py
python3 scripts/verify-liblib-batch6.py
python3 scripts/verify-liblib-batch7.py
python3 scripts/verify-liblib-batch8.py
npm run check
```

- Batch4：parented video 与 image 重新成组、解组、批量删除和 undo 通过；
- Batch5：group drag、group duplicate、child copy 和多选事务通过；
- Batch6：框选与导航手势通过；
- Batch7：整理拓扑、确认卡、还原/保留和 undo/redo 通过；
- lint：0 error，保留仓库既有 9 个 warning；
- TypeScript：通过；
- Next.js production build：通过。

## 5. 接力边界

- `.parent` 与 `(62,62)` 是强原站证据；
- 级联删除、重新成组和派生节点定位是 clone 的图完整性规则；
- 当前没有证据确认原站是否用 `extent: "parent"`，不要自行添加；
- 当前没有证据确认拖动 child 离开 group 后原站如何处理；
- 图片组没有 `.parent`，不要为了对称而给它虚构 child；
- 若重新获得原站浏览器控制，优先复测 child drag、group delete 和 `Shift+G` 的真实行为。

