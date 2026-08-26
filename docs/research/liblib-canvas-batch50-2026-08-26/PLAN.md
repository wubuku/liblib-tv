# Batch 50 计划：导演台工作区折叠与键盘边界

## 1. 选择理由

Batch 49 已补齐视口方向反馈。当前 Director 的下一项高价值缺口不是再加
一个低频资产入口，而是让用户在构图与时间轴工作时获得更多连续视口空间，
并防止普通画布快捷键穿透全屏 Director workspace。

这是一项低 graph 风险、可在当前 clone 确定性验证的 shell slice：

```text
desktop sidebars -> collapsible workspace chrome
keyboard events -> Director-local ownership
```

## 2. Provenance

| 结论 | Provenance | 等级 |
|---|---|---|
| upstream `全屏` action 折叠两侧 panel | fixed checkout `8c8bd36`, `ViewportToolbar.tsx` | `UPSTREAM_FACT` |
| upstream shell 在 collapsed 状态隐藏 left/right sidebar | `DirectorDeskShell.tsx`, `styles/index.css` | `UPSTREAM_FACT` |
| upstream editable input 不接收全局复制/粘贴/undo shortcut | `App.tsx` | `UPSTREAM_FACT` |
| clone 有三栏 Director workspace 和移动 drawer | current clone, Batch 35 | `CLONE_FACT` |
| clone 没有桌面侧栏折叠命令 | current clone audit | `CLONE_FACT` |
| LibTV authenticated source 的 Director shell exact keyboard/CSS | 本批未重新取得 | `UNKNOWN` |

## 3. 实施范围

### 包含

- `directorStore` 新增 typed session-local `viewportPanelsCollapsed` 和
  toggle action；
- Director 视口工具条新增 icon-only `全屏 / 恢复侧栏` command；
- desktop 折叠时隐藏两个 rails，中央 viewport 改为占满工作区；
- mobile 保留现有 mutually-exclusive drawers；从 mobile 打开 drawer 时
  自动恢复侧栏状态；
- workspace root 增加 `role="dialog"`、accessible label、`tabIndex=-1`
  和打开后的 focus ownership；
- page-level LibTV keyboard handler 在 Director active 时完全跳过普通画布
  graph/tool shortcut；
- Director Escape 优先处理 capture viewer、local menu、mobile drawer、
  export panel，再关闭 workspace；editable target 不直接关闭 workspace；
- 记录 desktop/mobile geometry、focus、shortcut isolation 和 state side effects。

### 不包含

- 浏览器原生 fullscreen、屏幕方向锁定或系统级沉浸模式；
- 侧栏宽度动画、拖动调整宽度或持久化用户偏好；
- 普通画布 graph、selection、history、active camera、timeline mutation；
- 全局 modal manager、复杂 focus trap、源站未证实的快捷键；
- LibTV source exact shell/CSS 结论。

## 4. 状态与副作用合同

| 动作 | `directorStore` | graph/history | viewport | selection |
|---|---|---|---|---|
| 全屏/恢复侧栏 | 仅 `viewportPanelsCollapsed` | 不变 | desktop 宽度变化 | 不变 |
| mobile 打开对象树/Inspector | 恢复 collapsed flag，再设 drawer | 不变 | mobile 不溢出 | 不变 |
| Director 内部快捷键 | 只作用于 Director 已有 surface | 不穿透到普通画布 | 按 surface 变化 | 按既有 surface 语义 |
| workspace Escape 关闭 | session close | 不新增 graph action | 返回原画布 | 由既有 close contract 恢复 source node |

## 5. 选择器

```text
[data-director-workspace]
[data-director-workspace-focus-owner]
[data-director-panels-collapsed]
[data-director-panels-toggle]
[data-director-viewport]
[data-director-mobile-panel-state]
```

## 6. 验收门

### 行为

- 默认 desktop rails 可见，折叠后两侧 rails 不占布局且 viewport 扩展；
- 再次点击恢复侧栏，原有 rails 和 viewport 几何恢复；
- 折叠状态不改变 objects、selection、timeline、active camera 或 graph；
- mobile 仍能分别打开 tree/Inspector，二者互斥且无水平溢出；
- Director 内聚焦输入框按 Delete/Backspace/Space/Tab 不触发普通画布
  graph/tool handler；
- workspace 外部 page handler 不在 Director active 时执行；
- Escape 关闭顺序和 workspace close contract 稳定；
- workspace 打开后具有可查询的 focus owner。

### 工程

- `verify-liblib-batch50.py` focused Playwright 通过；
- Batch 35-50 serial regression 通过；
- `npm run docs:check`、`npm run check` 和 `git diff --check` 通过；
- 不提交本批之外的 screenshots 或用户已有改动。

## 7. 停止条件

- 若可访问性实现要求重写所有 Director 子面板 focus trap，则退回只做
  collapsed shell；
- 若移动 drawer 与 collapsed state 产生 source-unknown 冲突，则保留现有
  mobile drawer 行为并只验证 desktop；
- 若发现当前 LibTV source 对“全屏”有明确不同语义，停止 clone 扩展并
  追加 source evidence，不猜测。

## 8. 后续队列

Batch 50 完成后重新评估：

1. Director shell 面板 focus/keyboard 精确 source refresh；
2. gizmo 与 collapsed sidebars 的 panel-aware offset；
3. 只有 Director shell 已足够稳定或被 source evidence 阻断后，才回到
   普通画布图片双浮层 parity。
