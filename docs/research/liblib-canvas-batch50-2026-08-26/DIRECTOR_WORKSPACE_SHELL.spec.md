# Director 工作区壳层契约

## 1. DOM 结构

```text
[data-director-workspace]
  [data-director-workspace-focus-owner]
  [data-director-panels-collapsed="false|true"]
    [aria-label="场景对象"]
    [data-director-viewport]
      [data-director-panels-toggle]
    [aria-label="属性"]
```

## 2. 状态

| 状态 | desktop rails | mobile drawer | viewport |
|---|---|---|---|
| `expanded` | 左/右显示 | 现有互斥 drawer | `left:220px; right:288px` |
| `collapsed` | 不占位/隐藏 | 不强制打开 | `inset-x:0` |
| `mobile tree` | CSS mobile drawer open | tree open | full width behind drawer |
| `mobile inspector` | CSS mobile drawer open | Inspector open | full width behind drawer |

## 3. 交互

- `全屏` 只折叠 Director sidebars，不调用 Browser Fullscreen API；
- `恢复侧栏` 恢复 desktop rails；
- mobile tree/Inspector trigger 在 collapsed 状态下先恢复 panel availability；
- tree 和 Inspector 仍保持 mutually exclusive；
- collapse command 不改变 graph、object、selection、timeline 或 active camera；
- workspace mount 后 focus owner 可通过 `document.activeElement` 查询；
- workspace active 时普通 LibTV page keyboard handler 不执行；
- editable target 上的 Delete、Backspace、Space、Tab 不穿透到普通画布；
- Escape 顺序：capture viewer/local menu/mobile drawer/export panel/
  workspace close，具体 surface 已处理的 Escape 不再向后传播。

## 4. 可访问性

- workspace root 使用 `role="dialog"`、`aria-modal="true"` 和可读 label；
- root 使用 `tabIndex=-1`，只在 mount 时作为 keyboard owner；
- icon-only collapse command 使用稳定 `aria-label`、`title` 和
  `aria-pressed`；
- collapsed sidebars 具有 `aria-hidden="true"`，避免隐藏内容进入可访问
  树；
- 不在本批声称完整 focus trap 或 source exact ARIA。

## 5. 非目标

- 浏览器 fullscreen、持久化 panel preference、拖动调整 rail 宽度；
- source exact shell geometry；
- 普通画布快捷键新增或 Director 专用新快捷键；
- capture/export payload 加入 shell chrome。
