# Batch 50 上游代码考古

## 固定版本

```text
path: research/upstream/storyai-3d-director-desk
commit: 8c8bd361790be4d37158a7430365e65546e358fe
```

## 1. Shell collapse

上游的壳层把 sidebars collapse 当作 viewport UI state：

```text
ViewportToolbar “全屏”
  -> toggleViewportPanelsCollapsed()
  -> DirectorDeskShell class is-sidebars-collapsed
  -> left/right sidebar display:none
  -> viewport-column owns the freed space
```

这不是 browser fullscreen，也不是 camera/scene mutation。上游
`ViewportToolbar.test.tsx` 直接验证点击“全屏”后 state 为 true；
`styles/index.css.test.ts` 验证 collapsed selector 和 sidebar geometry。

## 2. Keyboard boundary

上游 `App.tsx` 的 global handler 在检查 `defaultPrevented` 后，先调用
`isEditableShortcutTarget`。因此文本编辑、select 和 contenteditable 不会
触发 copy/paste/undo 等 Director global shortcut。

当前 clone 的 page handler 属于 LibTV 普通画布，Director workspace 是
同一 document 内的 fixed island。最小可迁移决策是 page handler 在
`activeDirectorNodeId` 存在时直接返回；Director 自己继续维护
Escape、path drawing、model library、phone vcam 和 capture viewer 的局部
处理。

## 3. 不直接复制的部分

- 上游的 standalone app shell 与 clone 的 `DirectorDesk` 不是同一组件树；
- 上游的 `viewportPanelsCollapsed` 会进入其 project persistence，而当前
  clone 没有同等 Director project schema；
- 上游的完整 toolbar/menu/focus CSS 不能直接覆盖当前 Tailwind shell；
- 上游测试证明的是上游行为，不是 LibTV authenticated source 行为。

## 4. 迁移后的验证重点

- collapsed/un-collapsed 的 DOM visibility、main viewport bounds 和 gizmo
  placement；
- mobile drawer open/close 与 collapsed state 的关系；
- page shortcut 在 Director active 时不改普通 canvas state；
- editable Director field 的 Delete/Space/Tab 不改变 graph；
- Escape 对内部 viewer/menu/drawer/export/workspace 的分层关闭。
