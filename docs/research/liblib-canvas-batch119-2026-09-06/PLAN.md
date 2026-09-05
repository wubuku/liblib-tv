# Batch 119 Plan：/project 项目列表页落地

> 状态：`IN_PROGRESS`
>
> 建档日期：2026-09-06。
>
> 上一批 checkpoint：Batch 118。
>
> 源站证据：[`../liblib-projects-page-2026-09-06/README.md`](../liblib-projects-page-2026-09-06/README.md)。

## 1. 范围

### 包含

1. **新路由 `src/app/project/page.tsx`**（`SOURCE_FACT` 结构）：`返回` 按钮（回 `/`）、`全部项目` 标题、`回收站`/`新建文件夹` 按钮（本地 status）、`开始创作 / 创建新的视频项目` 创建卡（`addCanvas()` 后回画布）、画布卡列表（名称+当日日期，点击 `setActiveCanvas` 并回 `/`）。
2. **logo 菜单接线**：`全部项目` → `router.push("/project")`（替换 Batch 106 的本地 status no-op）。
3. 页面读取 canvasStore 真实状态（projectName/canvases），不引入持久化。

### 不包含

- 回收站/新建文件夹真实功能、项目卡封面图、分页「没有更多了」之外的分页、
  服务端项目数据。

## 2. 证据边界

`SOURCE_FACT`：页面分区与文案（返回/全部项目/回收站/新建文件夹/开始创作/创建新的视频项目/没有更多了）；
`CLONE_DECISION`：画布卡映射（clone 单项目多画布 → 每画布一卡）、status no-op、日期取当日；
`SOURCE_UNKNOWN`：项目卡操作入口、回收站行为。

## 3. 验证

- `scripts/verify-liblib-batch119.py`：直开 `/project` 断言结构 → 点画布卡回画布且激活 → logo 菜单 全部项目 导航 → 创建卡新建画布 → 零诊断。
- 复跑 batch106（logo 菜单）、batch65（画布切换）；`npm run check`、`npm run docs:check`。

## 4. 完成定义

页面结构与采样一致、logo 菜单真实导航、相邻回归与全量门通过；master commit/push。
