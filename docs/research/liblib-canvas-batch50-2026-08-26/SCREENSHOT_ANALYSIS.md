# Batch 50 截图识别台账

> 识别日期：2026-08-26  
> 识别对象：当前 clone 的 Director workspace shell  
> 识别方法：先由专项 Playwright 生成四张状态截图，再只对 contact sheet 做一次视觉识别。后续维护优先阅读本文件，不重复识别同一组截图。

## 1. 证据清单

| 状态 | 截图 | viewport | 交互状态 | 来源 |
|---|---|---:|---|---|
| desktop expanded | [`liblib-clone-batch50-director-workspace-expanded-1440-2026-08-26.png`](../../design-references/liblib-clone-batch50-director-workspace-expanded-1440-2026-08-26.png) | `1440 × 900` | Director 默认展开，左右 rails 可见 | clone focused verifier |
| desktop collapsed | [`liblib-clone-batch50-director-workspace-collapsed-1440-2026-08-26.png`](../../design-references/liblib-clone-batch50-director-workspace-collapsed-1440-2026-08-26.png) | `1440 × 900` | 点击“全屏”，两侧 rails 隐藏，viewport 占满 | clone focused verifier |
| mobile tree | [`liblib-clone-batch50-director-workspace-mobile-tree-390-2026-08-26.png`](../../design-references/liblib-clone-batch50-director-workspace-mobile-tree-390-2026-08-26.png) | `390 × 844` | 对象树 drawer 打开，Inspector drawer 关闭 | clone focused verifier |
| mobile collapsed | [`liblib-clone-batch50-director-workspace-mobile-collapsed-390-2026-08-26.png`](../../design-references/liblib-clone-batch50-director-workspace-mobile-collapsed-390-2026-08-26.png) | `390 × 844` | collapsed state，移动 drawer 关闭，viewport 保持完整宽度 | clone focused verifier |
| contact sheet | [`liblib-clone-batch50-director-workspace-contact-sheet-2026-08-26.png`](../../design-references/liblib-clone-batch50-director-workspace-contact-sheet-2026-08-26.png) | `1488 × 1345` | 以上四态的单次识别拼图 | 本批派生证据 |

## 2. 视觉事实

以下是 contact sheet 可直接确认的 clone 视觉事实；不是 LibTV authenticated source 的事实：

- desktop expanded 是固定全屏黑色工作区，顶部 `48px` header，下方是左对象树、中央 R3F viewport、右属性面板，底部 timeline 横跨整个工作区；
- desktop collapsed 隐藏左右 rails，中央 viewport 从 `x=220` 扩展到 `x=0`，顶部 gizmo、画幅框和底部 viewport toolbar 保持在 viewport 内；
- desktop collapsed 的“全屏”图标切换为恢复侧栏图标，工具条仍位于画幅框下方，不因 shell collapse 变成 browser fullscreen；
- mobile tree 状态显示左侧对象树 drawer，中央 viewport 仍可见其余区域，drawer 与 viewport toolbar 没有横向溢出；
- mobile collapsed 状态不保留打开的 drawer，顶部左侧出现两个 drawer 入口，底部工具条仍完整落在 `390px` viewport 内；
- Director 场景 WebGL、方向 gizmo、画幅框、网格、时间轴均有可见内容，四态不是空白或 loading 截图。

## 3. 可复核几何

几何来自浏览器 `bounding_box()`，不是截图像素估计：

| 状态 | workspace | viewport | 左 rail | 右 rail |
|---|---|---|---|---|
| desktop expanded | `1440 × 900` | `x=220, width=932, y=48, height=656` | `x=0, width=220` | `x=1152, width=288` |
| desktop collapsed | `1440 × 900` | `x=0, width=1440, y=48, height=656` | `display:none` | `display:none` |
| mobile default | `390 × 844` | `x=0, width=390, y=48, height=620` | closed drawer at `x=-220` | closed drawer at `x=390` |

移动端工具条为 `x=12, width=366, y=604, height=44`；tree/Inspector 是互斥 drawer，打开一个后另一个保持 `data-director-mobile-panel-state="closed"`。

## 4. 交互事实

- desktop 点击 `[data-director-panels-toggle]` 后，workspace 和 viewport 的
  `data-director-panels-collapsed` 变为 `true`，两侧 aside 为
  `display:none` 且 `aria-hidden="true"`；
- 再次点击恢复后，viewport 的 `x/width` 回到展开值；
- mobile 打开 tree 后按 Escape 关闭，再打开 Inspector；二者不同时 open；
- collapsed state 下打开 mobile tree 会先恢复 `viewportPanelsCollapsed=false`，
  然后打开 tree drawer；
- workspace mount 后 `document.activeElement` 是带
  `data-director-workspace-focus-owner` 的 root；
- Director active 时，普通 LibTV page handler 不触发 Tab 添加节点、Space
  临时 pan、Delete 删除 underlying node 或 Ctrl/Cmd+Z 普通画布操作；
- Inspector input 接收 Delete/Space/Tab 时，不产生普通画布快捷键副作用；
- Escape 的已验证顺序包括：mobile drawer -> export panel -> workspace close。

## 5. 边界与未识别区域

- 本次没有重新打开 LibTV authenticated Director shell，因此不能从这些图
  推出源站 exact CSS、ARIA、宽度、动画或“全屏”语义；
- contact sheet 中的中文小字只作布局/层级识别，不作为逐字 source copy；
- 没有重复放大识别 header、timeline、gizmo 或场景材质，因为当前问题只涉及
  workspace shell；
- 截图只证明本批 clone 状态，不证明真实导出、远端持久化或源站一致性。

## 6. 重复识别规则

后续 agent 先读本文件和 [`DIRECTOR_WORKSPACE_SHELL.spec.md`](DIRECTOR_WORKSPACE_SHELL.spec.md)。
只有出现新 viewport、布局改变、截图文件替换、或本文件明确标注
`UNKNOWN` 的问题，才重新做局部截图识别。
