# Director Focus Containment Spec

> 类型：`CLONE_OWNED_UIUX_CONTRACT`
>
> 关联批次：[Batch 94 PLAN](PLAN.md)。

## 1. Problem

`DirectorDesk` 已经声明顶层 dialog 并在 mount 时聚焦 workspace，但这两项本身
不能阻止浏览器 Tab 进入被 transform 移出视口的移动抽屉，也不能保证关闭后焦点
回到触发 Director 的画布节点按钮。

## 2. Scope Model

```text
document
└── LibTV canvas
    └── DirectorDesk [workspace focus scope]
        ├── header
        ├── mobile tree [optional nested focus scope]
        ├── viewport
        ├── mobile inspector [optional nested focus scope]
        └── timeline
```

Workspace 是唯一顶层 scope。移动 tree/Inspector 是可选的 nested scope；它们
打开时只约束当前移动 surface 的 Tab，关闭时必须退出 tabbable 集合。

## 3. Tabbable Definition

包含：

- enabled `button`、`a[href]`、`input`、`select`、`textarea`；
- `[contenteditable="true"]`；
- 明确 `tabIndex >= 0` 的元素。

排除：

- `disabled`；
- `aria-hidden="true"` 或位于 `[inert]` subtree；
- `tabIndex < 0`；
- `display:none`、`visibility:hidden`、不可渲染祖先；
- `type="hidden"`。

对于 jsdom/无 layout 测试环境，不依赖 `getClientRects()` 判断可见性；浏览器
verifier 使用真实 DOM 和 computed style 复核。

## 4. Open / Close Contract

### Open

1. mount 时记录当前 document active element（只接受仍在 document 中的 HTMLElement）；
2. `requestAnimationFrame` 后把焦点放到 workspace 内第一个可操作元素；
3. 若没有可操作元素，workspace 自身作为安全焦点节点；
4. 写入 `data-director-focus-state="workspace"`。

### Close

1. 关闭前记住 return target；
2. 在 workspace 卸载后用 `requestAnimationFrame` 回焦；
3. 目标必须仍 connected、未 disabled、未 `aria-hidden`、未 inert；
4. 目标不可用时，聚焦 `[data-libtv-canvas-focus-root]`，再失败聚焦 workspace
   的安全节点；
5. close 原因写入 `data-director-focus-return` 只用于诊断，不作为业务数据。

## 5. Keyboard Contract

- `Tab` / `Shift+Tab` 在 scope 内首尾循环，并 `preventDefault()`；
- 没有可操作子元素时，scope 自身保持焦点；
- 输入元素仍可正常输入；焦点 containment 不拦截字符和浏览器默认文本编辑；
- Director command shortcut 只在 workspace 作用域内处理，且继续尊重
  editable/composition/忙碌/嵌套 viewer guard；
- Escape 继续由已有优先级处理：capture viewer → active gesture/mobile drawer/
  local overlay → workspace close。

## 6. Mobile Drawer Contract

- inactive tree/Inspector 设置 `inert` 和 `aria-hidden=true`；
- active drawer 设置 `data-director-focus-scope` 并在 open transition 后聚焦关闭
  按钮；
- backdrop close、drawer close button 和 Escape 都返回打开前的 trigger；
- 从 tree 切换到 Inspector 时，tree return target 不覆盖 Inspector trigger。

## 7. Evidence Boundary

这份合同描述当前 clone 的可访问性和交互可靠性目标。现有 LibTV authenticated
source evidence 没有证明完全相同的 focus implementation；不能将专项 verifier
通过解释为 LibTV source parity。
