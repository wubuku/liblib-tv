# Batch 298 — 资产抽屉「展示设置」视图布局菜单实施（源站 2026-09-10 采样落地）

> 状态：`IMPLEMENTED`（batch 297 采样 → 实施 → 295/268/102/205 验证器
> 与维护集回归绿）。
>
> 源站证据：`../liblib-canvas-batch297-2026-09-10/display-menu.png`
> （180×167 视图布局菜单四项）。

## 复刻内容（batch 297 采样事实）

1. **展示设置按钮改为视图布局菜单**（`data-asset-manager-viewmenu`，
   180 宽）：列表展示 / 宫格展示（互斥 aria-pressed）+ 展开全部分组 /
   收起全部分组；
2. **行为**：`viewMode` list|grid（宫格为 144px 卡片两列流）+
   `groupsExpanded`（false 时隐藏 depth-1 分组子行）；
3. **类型筛选菜单（batch 204 的 10 项）迁至 筛选 按钮**
   （`data-asset-manager-filter`，aria-label 筛选：{类型}）——源站
   2026-09-10 对照：筛选 图标管类型筛选、展示设置 管视图布局；
4. **附带清理**：旧 5 项 filterOptions 下拉随迁移移除（被 10 项类型
   菜单功能覆盖）；条目悬停操作与 320px 宽度（batch 264）不变。

## 验收

- `verify-liblib-batch295.py`：7 checks；`verify-liblib-batch268.py`：
  11 checks；`verify-liblib-batch281.py`：14 checks；
- **batch102（14 checks）/batch205（8 checks）迁移后全绿**（类型菜单
  触发器迁至 筛选 按钮）；
- 其余维护集（21–268 主体）全绿；`npm run check`：0 errors（8
  warnings 基线）；docs check 通过；源站画布 0 残留。

## 不证明

- 源站 宫格展示 的卡片布局细节（仅记录为栅格两列近似）；
- 展开全部分组 在无分组画布的表现（clone 无分组时行为等同全列表）。
