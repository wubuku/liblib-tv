# Batch 13 实施结果：分镜模式数据绑定与故事板结构

## 1. 实施内容

- 重写 `StoryboardBoard`，从 `canvasStore` 当前画布读取图片、视频和脚本节点。
- 按原站截图的结构拆分：
  - 左侧“关键元素 · 全部”；
  - 关键元素中的“图片 / 文本”分组；
  - 中间“故事板”的“图片 / 视频”两列；
  - 右侧 Agent 继续由页面外层独立渲染。
- 图片卡、视频卡和关键元素卡均保留来源节点 ID。
- 点击卡片调用 `canvasStore.selectNode`，使用 `aria-pressed` 和青色边界反馈选中态。
- 增加“返回工作台”，切换模式时不清空选中节点。
- 空画布和空媒体列显示明确空态；故事板主体使用内部横向滚动，避免撑开页面。
- 增加稳定 `data-storyboard-*` 选择器，供浏览器回归和后续 agent 诊断。
- 更新 Batch 11 的模式生命周期回归断言，使其检查当前原站证据中的“关键元素 · 全部”而不是旧 clone 的静态“角色与物件”文案。

## 2. 证据边界

### Source fact

- 原站分镜模式截图显示关键元素栏、图片/视频故事板列和并列 Agent。
- 当前原站审计的画布基线包含 5 个图片节点、1 个视频节点和 1 个脚本节点。

### Clone-only decision

- 卡片点击选择节点和“返回工作台”是本地原型闭环，原站卡片深层点击目的未在本轮重新采样。
- “Lib Image / Lib Video”标签和来源尺寸使用现有节点数据做本地展示，不连接远端资源服务。
- 不实现故事板排序、删除、发布、拖拽或真实 Agent 任务。

## 3. 验证

专项脚本：

```bash
python3 scripts/verify-liblib-batch13.py
```

结果：

```text
Batch13 Playwright verification passed: storyboard data projection,
key elements, card selection, workbench round-trip, empty canvas,
mobile overflow, screenshots, console.
```

工程检查：

```bash
npm run typecheck
npm run docs:check
```

本批 `npm run typecheck` 已通过；`npm run docs:check` 在补齐本批文件后继续执行。

最终结果：

- `npm run check`：通过；9 个既有 lint warning，0 error。
- `npm run docs:check`：通过，130 个 Markdown 文件、266 个本地目标。
- `git diff --check`：通过。
- Batch 4-10 回归通过；Batch 11-13 回归通过。

## 4. 证据文件

- 原站识图台账：[SCREENSHOT_ANALYSIS.md](SCREENSHOT_ANALYSIS.md)
- 组件合同：[STORYBOARD_MODE.spec.md](STORYBOARD_MODE.spec.md)
- Desktop：[liblib-clone-batch13-storyboard-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch13-storyboard-desktop-929-2026-08-25.png)
- Empty desktop：[liblib-clone-batch13-storyboard-empty-desktop-929-2026-08-25.png](../../design-references/liblib-clone-batch13-storyboard-empty-desktop-929-2026-08-25.png)
- Mobile：[liblib-clone-batch13-storyboard-mobile-390-2026-08-25.png](../../design-references/liblib-clone-batch13-storyboard-mobile-390-2026-08-25.png)
