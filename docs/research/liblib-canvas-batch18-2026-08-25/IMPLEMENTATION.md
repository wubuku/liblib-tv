# Batch 18 实施结果：缩放菜单结构与生命周期

## 1. 实施内容

- `uiStore` 新增：
  - `isZoomMenuOpen`
  - `toggleZoomMenu`
  - `closeZoomMenu`
- zoom menu 进入 `closedOverlayState`：
  - `Escape / closeAllPanels` 可清理；
  - 打开资产、画布、分享、Agent、添加节点等 overlay 会关闭 zoom；
  - 打开 zoom 会清理其他顶层 overlay。
- `BottomToolbar` 删除局部 `isZoomOpen`。
- 菜单按原站截图重排：
  - 当前百分比状态行；
  - 放大、缩小、适合屏幕与快捷键；
  - 50%、100%、800%。
- 移除缩放菜单内的 `点阵网格`。
- zoom 命令后菜单保持打开，兼容连续操作和 Batch 9 节点浮层观察。
- 外部关闭使用 capture-phase `pointerdown`，避免 React Flow 事件层停止冒泡后菜单残留。
- Batch 11 overlay 检查加入 `zoom-menu`。
- Batch 9 节点浮层回归改用 `data-zoom-action="in"`，避免菜单从旧图标按钮重构为命令行后测试仍依赖过时的 role/name 定位。

## 2. 证据边界

### Source fact

- 原站截图直接支持状态行、6 个命令、顺序、快捷键、锚点和无网格项。

### Inference

- zoom 与其他局部菜单应共享 Escape/互斥生命周期。

### Clone-only decision

- zoom 命令执行后菜单保持打开。
- 外部点击通过 capture-phase pointer listener 关闭。

## 3. 验证

专项命令：

```bash
python3 scripts/verify-liblib-batch18.py
```

结果：通过。

- 6 个命令、当前百分比和无网格项通过。
- 放大/缩小、50/100/800、适合屏幕通过。
- zoom 后菜单保持打开。
- Escape、React Flow 区域外部点击关闭通过。
- zoom 与资产抽屉双向互斥通过。
- 390px 无页面级横向溢出。
- 浏览器 console/page error 为空。

跨批命令：

```bash
python3 scripts/verify-liblib-batch9.py
for script in scripts/verify-liblib-batch{11..18}.py; do
  python3 "$script" || exit 1
done
```

结果：全部通过。

- Batch 9 图片/视频节点浮层锚点、拖动、缩放、平移和多选生命周期通过。
- Batch 11-17 overlay、资产、分镜、Agent/分享、添加节点、画布导航和资产上下文全部通过。
- Batch 18 缩放菜单专项再次通过。

工程命令：

```bash
npm run check
npm run docs:check
git diff --check
```

结果：

- ESLint：`0 error`，保留仓库已有的 9 条 FrameOS warning。
- TypeScript：通过。
- Next.js production build：通过。
- 文档链接：156 个 Markdown 文件、342 个本地目标，全部通过。
- diff whitespace：通过。

## 4. 证据文件

- 原站识图：[SCREENSHOT_ANALYSIS.md](SCREENSHOT_ANALYSIS.md)
- 结构合同：[ZOOM_MENU.spec.md](ZOOM_MENU.spec.md)
- Desktop：[liblib-clone-batch18-zoom-menu-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch18-zoom-menu-desktop-929-2026-08-25.png)
- Mobile：[liblib-clone-batch18-zoom-menu-mobile-390-2026-08-25.png](../../design-references/liblib-clone-batch18-zoom-menu-mobile-390-2026-08-25.png)
