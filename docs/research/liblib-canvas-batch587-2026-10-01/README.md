# Batch 587 — 「收起」语义对齐源站（结清 586 记录项）

> 状态：`SCRIPT_RECORDED_PASS`（27 检查）。源站证据：**2026-10-01 实时 CDP
> 受控对照**（1920×1150，展开 / 收起 / 恢复三态采样）。

## 源站实测（SOURCE_FACT）

`收起` 在顶栏，紧贴 `3D导演台` 标题右侧（x=240, y=6, 40×40,
`aria="收起"`），是浮层内**唯一**的折叠入口。

受控对照三态：

| | 收起前 | 收起后 | 点图标栏「场景」后 |
|---|---|---|---|
| 顶栏 header | 280×52 | **DOM 移除** | 280×52 |
| 左侧场景面板 | 280×1098 | **DOM 移除** | 280×1098 |
| 图标栏 7 入口 | x=8 32×32 | **保留** | 保留 |
| 右侧属性面板 | 1639,0 281×1150 | **保留** | 保留 |
| 3D 视口 canvas | 0,0 1920×1150 | 保留 | 保留 |
| 视角切换 / gizmo / 重置视角 | 有 | **保留** | 有 |

**恢复入口是图标栏的「场景」条目**——收起后顶栏已不存在，浮层内没有第二个
恢复按钮。

## clone 原状与本批改动（CLONE_DECISION）

此前 clone 在**视口底栏**挂了一个 clone 独有的「全屏 / 恢复侧栏」按钮，
`viewportPanelsCollapsed` 为真时**同时隐藏左右两侧面板**并把视口撑到
`inset-x-0`。这在源站没有对应物，语义也相反。

本批：

1. **移除**视口底栏的「全屏 / 恢复侧栏」（连同随之失效的 `Expand` /
   `Minimize2` 导入与 `toggleViewportPanelsCollapsed` 订阅）。
2. **顶栏新增**「收起」按钮，`aria-label` / `title` 逐字为 `收起`，
   携带 `data-director-panels-toggle`。
3. `viewportPanelsCollapsed` 语义改为「左侧场景面板已收起」：
   - 左侧 `<aside aria-label="场景对象">` 照旧 `min-[900px]:hidden`；
   - 右侧 `<aside aria-label="属性">` **不再**受该状态影响（去掉
     `display:none` / `aria-hidden` / `inert` 三处联动）；
   - 视口 `main` 左边界 `left-[266px]` → `left-[46px]`，右边界保持
     `right-[288px]`（让出的正是 220px 场景面板宽度）。
4. 「收起」按钮在收起态**卸载**（源站收起后 header 整条从 DOM 移除），
   避免留下无反应的单击控件。
5. 图标栏 `场景` 条目接 `setViewportPanelsCollapsed(false)`，成为恢复入口。

### 保留的已知差异（有意为之）

源站收起时顶栏整条消失；clone 顶栏保留。原因是 **clone 的视角切换
（导演视角 / 机位视角）就放在顶栏里**，而源站的视角切换是浮在视口上的
独立控件（x=878, y=10），不随 header 消失。跟着删 header 会连带删掉视角
切换，反而制造新的不一致。已记为已知差异，不臆造源站没有的结构。

## 断言迁移（合同演进，沿 42/166/190/556/581/582/583 先例）

| 文件 | 处置 |
|---|---|
| `verify-liblib-batch50.py` | `收起` 取代 `全屏`；收起态断言右侧面板**仍在**；`+450` 宽度增长改为 `+200`（只让出 220px 场景面板）；恢复改点图标栏 `场景`；`data-director-panels-toggle` 的源码断言从 `DirectorViewport` 移到 `DirectorDesk` |
| `verify-liblib-batch93.py` | 恢复不再二次点 toggle（按钮已卸载），改点图标栏 `场景`，并断言按钮数量 0 → 1 |
| `verify-liblib-batch74.py` / `batch89.py` | **无需迁移**：二者只断言 `viewportPanelsCollapsed` 不进入持久化信封、且重载后为 `false`，与语义变更无关 |

### batch 50 的两处既有失败（基线对照后解除）

基线复现：把 5 个文件还原到 HEAD 重跑，batch 50 **在折叠按钮点击处就 30s
超时**——即改动前该脚本已完全跑不通。587 让它越过折叠段后又撞上第二个既有
失败。两处均按「不改被测合同、最小解除」处理：

1. `[data-director-inspector] input` `.first` 在 batch 582 于面板顶部新增
   「场景缩放」range 后解析到 range，报 `Malformed value` → 改为先点
   `[data-director-object-id]` 选中对象，再用 `[data-director-object-name]`
   定位名称框。被测合同（文本框内 Space / Delete / Tab 不得触发画布平移
   或新增节点浮层）不变，且真正落到了对象名输入框上。
2. 末尾 `assert errors == []` 撞上长期已知的 `TransformControls: The
   attached 3D object must be a part of the scene graph.`（batch
   36/553/558/89/96/85/580 同样显式过滤）→ 按同一约定过滤，命中数打印为
   `Known transient filtered`，不静默吞掉。

## 内容

- `src/components/director/DirectorDesk.tsx`（顶栏收起按钮 + 面板语义）
- `src/components/director/DirectorIconRail.tsx`（`场景` 作恢复入口）
- `src/components/director/DirectorViewport.tsx`（移除 clone 独有的全屏按钮）
- `scripts/verify-liblib-batch587.py`（27 检查，新）
- `scripts/verify-liblib-batch50.py` / `batch93.py`（断言迁移）
- `docs/design-references/liblib-clone-batch50-*.png`（参考图随收起语义
  实质变化，一并更新；收起态可见左面板消失而右侧属性面板保留）

## 回归与门禁

- 回归：587（27）/ 586（18）/ 93 / 89 / 50 全绿；
- `tsc --noEmit` 净；`eslint` 0 error（导演台目录唯一 warning 是他人遗留的
  `DirectorCameraMotionTab` 未使用 `RefreshCw`）；`verify-docs.py` ✓；
  `next build` ✓。
  （期间一次 build 失败是他人正在写 `frameosStore.ts` 的瞬态竞态，复跑即过。）

## 待后续批次

- 场景缩放读数为百分比（值 3 → `300%`）、球形半径读数无单位；
- 开关行结构：整宽 button 280×56，轨道 24×14 + 旋钮 10×10，开关联动色；
- 搜索框真实 `placeholder` 是「请输入搜索内容」（「搜索场景对象」是另一个
  1×1 span 的无障碍标签）；
- 顶栏收起按钮的位置：源站在 280px 宽的左列 header 内（x=240 即该列右缘），
  clone 顶栏是整窗宽，按钮落在标题旁。是否对齐到左列右缘待定；
- `directorPmx*` 触发条件仍未确认。
