# LibTV 画布 Batch 8 计划：视频组父子语义

> 建档日期：2026-08-25
> 原则：用原站 DOM class、坐标和当前依赖源码形成闭合证据链；修正数据关系时同时保护现有编辑事务。

## 1. 缺口盘点

| 缺口 | 当前 clone | 原站/依赖证据 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 视频组 parent 关系 | 组与视频都是顶层节点 | 原站组有 `.parent`；xyflow 仅在有 child 时添加 | 5 | 修正 |
| child 相对坐标 | 视频为绝对 `(2436,50)` | 组为 `(2374,-12)`，差值为 `(62,62)` | 5 | 修正 |
| 拖动组 | 视频不会跟随 | parent-child 是 React Flow 的原生移动语义 | 5 | 验证 |
| 整理组 | 依靠两个独立绝对坐标靠近 | Batch7 已支持 child 保留相对坐标 | 5 | 接入 |
| 重新成组 | 只接受无 `parentId` 的顶层节点 | 视频成为 child 后会破坏 Batch4/5 既有事务 | 4 | 兼容 |
| 删除组 | 当前只删 group，会留下 dangling child | 真实 parent-child 后是图完整性问题 | 5 | 级联 descendants |
| 派生节点定位 | 直接使用 source 的相对 position | child source 会把派生节点放到错误世界位置 | 4 | 改用绝对位置 |
| child 单独复制 | 代码已支持脱离旧 parent | Batch5 已有明确 clone 契约 | 4 | 回归 |
| group 复制 | 代码已自动带 children 并重映射 parentId | Batch5 已有明确 clone 契约 | 4 | 回归 |
| `extent: "parent"` | 当前未设置 | 原站保存数据没有直接记录 | 2 | 不做 |
| 图片组 parent | 原站图片组没有 `.parent` | 直接 DOM class 对比 | 3 | 保持空组 |

## 2. 实施范围

### P0

1. 初始失败视频：
   - `parentId: "g-EFbbHpwq5w"`；
   - `position: { x: 62, y: 62 }`；
2. 初始屏幕绝对位置仍为 `(2436,50)`；
3. 视频组获得 React Flow `.parent` class；
4. 拖动视频组时失败视频获得相同屏幕位移；
5. group drag 仍是一个 undo/redo history step；
6. Batch7 整理后 child 仍保持相对 `(62,62)`；
7. 删除 group 时级联删除 descendants 和相关 edges。

### P1

1. 已 parented child 可以与另一个普通节点重新成组：
   - 先按当前 hierarchy 计算绝对位置；
   - 再换算为新 group 的相对位置；
2. 从 child 创建派生节点时使用 child 的绝对世界坐标；
3. 单独复制 child 时副本成为顶层节点；
4. 复制 group 时副本带 child，child 的 `parentId` 重映射到新 group；
5. 复制画布继续重映射 parentId；
6. 解组 source video group 后 child 恢复原绝对坐标。

## 3. 不做

- 不设置 `extent: "parent"`；
- 不限制 child 在 group 内拖动；
- 不给空图片组虚构 child；
- 不改变视频组尺寸、颜色或标题；
- 不实现 `Option/Alt+G` 合并分镜组；
- 不把 clone 的级联删除和重新成组规则声称为原站实测命令；
- 不修改 FrameOS。

## 4. 验收标准

### 初始与拖动

- 节点 `10`、边 `11`；
- 视频组有 `.parent`，图片组没有；
- group 与 video 的屏幕位置差等于 `62 * zoom`；
- 拖动 group 后两者屏幕 delta 相同；
- undo/redo 同时恢复 group 与 child 的绝对位置。

### 编辑事务

- 单独复制 group：新增 1 group + 1 child，parentId 重映射；
- 单独复制 child：新增 1 顶层 video，复制其关联边；
- 选择 parented video 与普通 image 后 `G` 仍可创建新 group；
- `Shift+G` 恢复两个顶层节点；
- 删除 source video group 后 group 与 child 都消失，相关 edges 删除；
- undo 恢复完整 hierarchy。

### 整理与工程

- Batch7 `929x874` 整理仍为约 `28%`；
- 整理后视频相对视频组保持 `(62,62)`；
- Batch4-Batch8 自动化全部通过；
- `npm run check` 通过；
- 控制台 error 为 0。

