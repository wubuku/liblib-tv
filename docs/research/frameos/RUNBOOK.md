# FrameOS 画布 — 操作手册 / Runbook

> 给**未来的开发者 / agents** 的一份"如何开发、调试、扩展 FrameOS 画布"指南。
> 与 `IMPLEMENTATION.md` 互补 — 那是"设计决策"，这是"动手步骤"。

## 快速开始

```bash
# 1. 启动 dev server
npm run dev

# 2. 打开浏览器
# 主画布（liblib-tv clone）: http://localhost:3000
# FrameOS 画布:                  http://localhost:3000/frameos/canvas/demo

# 3. 从主页右上角 "FrameOS" 按钮也可进入
```

## 调试技巧

### 在浏览器控制台调用 store

dev server 启动后，store 已暴露在 `window.__frameos_store` 上：

```js
// 选中第一个文本节点
__frameos_store.getState().selectNode('text-1')

// 移动节点
const newNodes = __frameos_store.getState().nodes.map(n =>
  n.id === 'text-1' ? { ...n, position: { x: 100, y: 200 } } : n
)
__frameos_store.getState().setNodes(newNodes)

// 添加节点
__frameos_store.getState().addNode('image')

// 触发 toast
// (导入 showToast — 不直接暴露，use FrameosToast 内部逻辑)
```

### 启用 DEBUG 面板

点击画布**右下角**的 **DEBUG** 按钮（默认深色，激活后变橙色）。
激活后，点击节点会显示**右侧"节点详情"面板**——用来检查节点 ID / 坐标 / 参数 / 操作。

> ⚠️ 这是**仅供开发者**的便利功能。原站 frameos.cn **没有**这个面板。

### 强制缩放/重置

- 顶部菜单 (右侧偏右) **撤销/重做** 按钮 — 接入 store 的 history stack
- 底部 dock 中间 **100% / 缩小 / 放大 / 适应画布**
- 键盘：`+` `-` `0` `Cmd+Z` `Cmd+Shift+Z`

## 关键文件位置

| 文件 | 作用 |
|---|---|
| `src/app/frameos/canvas/[id]/page.tsx` | 画布主页面（路由入口） |
| `src/components/frameos/` | 所有 frameos 专用组件 |
| `src/store/frameosStore.ts` | Zustand store（所有状态来源） |
| `src/app/frameos-canvas.css` | frameos 画布专用 CSS（动画、handle 样式、拖拽视觉） |
| `docs/research/frameos/` | 探索文档（设计令牌、行为、组件清单） |

## 如何加新节点类型

1. 在 `src/types/frameos.ts` 加类型
2. 在 `src/store/frameosStore.ts` 的 `addNode` switch 加 case
3. 在 `src/components/frameos/nodes/FrameosMyNode.tsx` 创建组件
4. 在 `src/app/frameos/canvas/[id]/page.tsx` 的 `nodeTypes` map 注册
5. 在 `FrameosToolRail.tsx` 添加节点菜单加选项
6. 在 `FrameosNodeFloatingToolbar.tsx` 加节点类型对应的工具按钮

## 常见问题

### Q: 我改了组件但页面没更新？
A: Next.js dev server 应该自动热重载。如果不行，按 `Ctrl+R` 刷新，或在终端按 `Ctrl+C` 重启 `npm run dev`。

### Q: 节点拖动时 panel 不跟随？
A: 检查 `FrameosPromptEditor.tsx` / `FrameosNodeFloatingToolbar.tsx` / `FrameosNodeEditPanel.tsx` —— 它们必须用 `useViewport()` 拿 pan+zoom，并用 `position: fixed` 定位。

### Q: 选中节点但 handle 不显示？
A: 检查 `selectNode` action 是否有同步 `selected: true` 到 nodes array。xyflow v12 不会自动同步，需要在 selectNode 中写回。

### Q: 边是灰色实线而不是蓝色虚线？
A: 确认 `page.tsx` 的 `edgeTypes: { default: FrameosEdge }` 而不是 `DeletableEdge`。

### Q: 添加节点时点击空白处关闭菜单？
A: `FrameosToolRail.tsx` 的添加节点菜单使用 fixed 遮罩 + onClick 关闭。检查 `closeAddNodeMenu` 是否被调用。

## E2E 测试

`e2e/frameos.spec.ts` 包含 6 个 Playwright 测试用例。

要跑 e2e 需要：
1. `npm install -D @playwright/test`
2. `npx playwright install chromium`
3. `npm run test:e2e` (需加进 package.json)

当前未跑（避免引入未安装的依赖），但**测试用例已经写好**。

## 提交规范

```bash
git add <files>
git commit -m "feat/fix(scope): 简短描述

更详细说明...
- 关键变更点 1
- 关键变更点 2

Co-Authored-By: Claude <noreply@anthropic.com>"
```

- `feat(frameos):` 新功能
- `fix(frameos):` bug 修复
- `docs:` 仅文档
- `refactor(frameos):` 重构（不改行为）
