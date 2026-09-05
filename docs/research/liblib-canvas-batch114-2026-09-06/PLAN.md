# Batch 114 Plan：多画布下拉对齐 2026-09-06 丢弃式采样

> 状态：`IN_PROGRESS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 113。
>
> 源站证据：[`../liblib-canvas-sampling-2026-09-06/README.md`](../liblib-canvas-sampling-2026-09-06/README.md) §1（丢弃式测试项目内完成的多画布 CRUD 全流程）。

## 1. 范围

### 包含

1. **行结构**（`SOURCE_FACT`）：每行 = `切换到画布 {名称}` 按钮（点击切换，触发器同步）+ hover 门控 `更多操作` 按钮（aria-label=更多操作）。
2. **行级菜单**（`SOURCE_FACT`）：`在新窗口打开 / 重命名画布 / 复制画布 / 删除画布` 四项（精确文案）。
3. **删除确认框**（`SOURCE_FACT`）：`删除画布` 标题 + `确定要删除画布「X」吗？此操作不可恢复。` + `取消/确认`；确认后删除；删活动画布自动切到剩余画布（store 已有 fallback）。
4. **副本命名**（`SOURCE_FACT`）：复制画布命名 `{名称}副本{序号}`（替换现 `(副本)`），保持自动切换。
5. **排序**（`SOURCE_FACT`）：下拉按创建时间倒序（最新在前），不再活动画布置顶。
6. `在新窗口打开` 在 clone 中无对应路由语义：菜单项存在、点击仅关闭菜单（诚实边界，`SOURCE_UNKNOWN`）。

### 不包含

- 在新窗口打开的真实行为、多用户会话、画布下拉的 Mantine 视觉复刻。

## 2. 证据边界

`SOURCE_FACT`：§1.1-1.4 全部；`CLONE_DECISION`：clamp/排序实现、在新窗口打开 no-op、序号计算规则；
`SOURCE_UNKNOWN`：复制副本再复制的命名、排序在更多画布时的表现。

## 3. 影响面

- `src/components/CanvasTabDropdown.tsx`、`src/store/canvasStore.ts`（duplicate 命名）；
- batch13/64/65 依赖 `data-canvas-row`/`data-canvas-trigger`/switch button（保留，复跑确认）。

## 4. 验证

- `scripts/verify-liblib-batch114.py`：开下拉断言结构/排序 → + 新建 → 行菜单四项 → 重命名 → 复制副本命名与自动切换 → 删除确认框文案与 fallback → 零诊断。
- 复跑 batch13/64/65；`npm run check`、`npm run docs:check`。

## 5. 完成定义

对齐 §1 全部采样事实；相邻回归与全量门通过；master commit/push。
