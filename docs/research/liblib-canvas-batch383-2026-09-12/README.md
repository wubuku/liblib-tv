# Batch 383 — PAR-004 phase 1 并入权威目录（`DOC_RECORDED`）

> 状态：batch 374 的键盘/焦点清单合并进
> `LIBTV_UI_OVERLAY_RUNTIME_CATALOG.md` §4.3b——PAR-004 的 clone 侧
> 研究成果并入权威目录。无 src 变更。源站恢复重测：
> `RECOVERY: still-broken` 维持（第九次探测）。

## §4.3b 内容（Keyboard 与焦点所有权列）

12 个 surface 的局部键盘与焦点所有权两列：

- 全部 LibTV surface：无局部键盘（页级 handler 承担），页级
  focus-root；
- 两个例外：History（容器 mousedown stopPropagation 隔离
  outside-close）、Zoom（capture-phase pointerdown outside）；
- Agent：内部 menu Escape stopPropagation（menu 级隔离）；
  **无 focus trap——PAR-004 待决项**；
- Director（独立 island）：Escape→closeMobilePanel、Delete/
  Backspace、zoom preset stopPropagation；
  `useDirectorFocusContainment` + `data-director-focus-scope` 双
  aside + inert 互斥。

## 验收

- docs check 通过（939 Markdown）；无 src 变更。

## 后续候选

- 源站恢复后：BLOCKED_SOURCE 补采、PAR-004 phase 2 源站对照、
  DEC-048 采样裁决、CLONE_DECISION 替换；
- Agent focus trap 的产品裁决（PAR-004 待决项）。
