# Batch 251 — 源站「成组」全行为采样 (2026-09-27)

来源: frameos.cn 测试画布 (`01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`)。
采样方法: 合成 pointer 事件完成框选 (4 节点) → `.group-toolbar` 成组按钮 `el.click()` +
MutationObserver + fetch/XHR 监听; 之后逐按钮点击观察 DOM/样式/网络。
证据截图: `docs/design-references/frameos/source-batch251-group-created-toolbar-2026-09-27.png`、
`source-batch251-group-red-arranged-2026-09-27.png`。

## 事实 (source fact)

### 成组创建
- 多选 (≥2) → `.group-toolbar` [成组 | 批量下载] → 点击「成组」:
  - 发出 `FETCH /api/canvas/ops` (持久化)。
  - 新增 `.canvas-group.is-selected`, 文本「组1」(自动编号)。
  - 同时存在 `.canvas-batch-selection-chrome` (兄弟层, 用途未采样)。
  - 节点全部取消选中; 节点不重挂载 (分组是独立覆盖层, 非父容器)。
  - 分组容器在 `.canvas-groups-layer` 内 (layer index 0, 渲染在节点层之前 → 分组在节点后方)。
- 分组矩形 = 成员包围盒四边各 +28px 内边距 (实测: 成员 bbox (176,194)-(1275,705) →
  分组 (148,166) 1155×567.308, 恰为 +28)。

### 分组外观 (computed style + inline style)
- 容器: `position:absolute` (flow 坐标), `background: rgba(c, 0.16)`,
  `border: 1.5px solid rgba(c, 0.9)`, `border-radius: 12px`。
- 标签 `.canvas-group__label`: absolute `top:-24px`, 含 `ri-folder-2-line` 图标 +
  `.canvas-group__name` (12px, `rgb(163,163,163)`)。
- 选中态四角手柄 `--nw/ne/sw/se`: 12×12, border 1.5px, radius 3px, 外偏 -6px,
  border-color `rgb(c)` (非选中时不渲染 — 截图对比确认)。
- 默认色 `rgb(100,116,139)` (#64748b)。

### 选中分组后的展开工具栏 (`.group-toolbar` 复用, 高 36)
- 位置: 分组包围盒上方 15px, 水平居中 (实测 y=115 = 分组 top 166 - 36 - 15)。
- 按钮: [切换背景色 (aria, 色点 16px)] [排列方式 (ri-layout-grid-line)] │
  整组执行 (ri-play-line, w88) 存为模板 (自绘 svg, w88) 解组 (ri-collage-line, w63)
  批量下载 (ri-download-2-line, w88, `title="打包下载 3 个文件"` = 有媒体成员数)。
- 宽 421, 居中于分组。

### 切换背景色
- 点击弹出 `.gt-popover.gt-color-pop` (156×66, bg `rgba(24,24,24,0.95)`,
  border `1px solid rgba(255,255,255,0.08)`, radius 10, padding 6, 阴影
  `0 25px 50px -12px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)`)。
- 10 个圆形色板 22×22 (radius 9999px): 默认色 #64748b (`aria-label="默认色"`,
  `is-current` 时 border 2px `rgb(59,130,246)`) + #ef4444 #f97316 #eab308 #22c55e
  #14b8a6 #3b82f6 #6366f1 #ec4899 #9ca3af (`aria-label="背景色 #xxx"`)。
- 选中色 c 后: 分组 bg `rgba(c,0.16)`、border `rgba(c,0.9)`、手柄 `rgb(c)`、
  色点 `rgb(c)` 同步更新; 弹层自动关闭; 标签颜色不变。

### 排列方式
- 点击弹出 `.gt-popover.gt-menu` (宽 140, 同弹层样式): 宫格排列 (ri-layout-grid-line) /
  水平排列 (ri-layout-row-line) / 垂直排列 (ri-layout-column-line)。
- 水平排列实测 (5 成员含同步回来的残留节点): 成员按原 Y 排序 (top→bottom) 一行排开,
  内容左上角对齐 `分组左上角 + 28` (originX = -341.868+28 = -313.868 ✓,
  originY = -223.308+28 = -195.308 ✓), 节点间距 40 (300 宽节点相邻 x 差 340)。
  分组盒重算 = 新内容 bbox + 28 (实测 w 1716 = 5×300+4×40+56, h 356 = 300+56)。
- 宫格/垂直参数未点击 (限制画布变更), 垂直按对称推断, 宫格列数取 ceil(√n) (克隆决策)。

### 分组交互
- 选中: 分组元素上的 pointerdown → `is-selected` + 展开工具栏 (padding 空白带即可命中)。
- 拖拽: pointerdown+move → 分组矩形与全部成员同步位移 (实测 +60,+40 一致), 非成员不动。
- 解组: 移除 `.canvas-group` 与 `.canvas-batch-selection-chrome`; 成员保持当前位置;
  无 toast。**源站 bug**: 解组后展开工具栏残留不消失 (克隆应正确隐藏)。
- 撤销: 头部 ↺ (ri-arrow-go-back-line) 逐步撤销 (实测先恢复解组→分组回来, 再恢复拖拽→
  回到排列后位置, 之后按钮 disabled — 历史深度有限)。

## 未采样 / 边界 (evidence-backed inference / clone decision)
- 整组执行 (疑似付费生成)、存为模板 (改账号状态): 未点击。克隆: 整组执行 no-op,
  存为模板 mock toast。
- 宫格排列列数: 克隆决策 ceil(√n) 行优先 (按原 Y 排序)。
- 分组不进克隆撤销栈 (克隆 undo 快照仅 nodes/edges) — 克隆简化, 文档记录。
- 分组计数「组N」取当前分组数 +1 (与源站组1 编号一致, 多组编号未采样)。
- 采样期间画布已复原: 解组 + 逐节点拖回原位 (≤3px 误差), 刷新确认服务端持久化 ✓。
