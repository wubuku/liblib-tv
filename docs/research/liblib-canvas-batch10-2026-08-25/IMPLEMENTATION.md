# LibTV 画布 Batch 10 实施记录

> 状态：已完成
> 最后更新：2026-08-25

## 1. 规划与证据

- 复核同一登录态原站五个图片节点的 DOM 状态；
- 将高度、Prompt、参考图、顶部入口、placeholder 和 footer 控件矩形固化为状态矩阵；
- 确认 `咖啡馆` 是“有 Prompt 但仍为 191px”的直接反例；
- 确认只有带 references 的 `分镜 #2` 显示“参考”入口；
- 确认顶部没有 AutoLink 文字 pill；
- 复用 Batch 9 原站识图记录，没有重复打开整张原站截图；
- 定义每个节点使用独立 Playwright page，防止派生状态污染。

规划已提交并推送：

```text
8c54e98 docs: plan LibTV image editor state matrix
```

## 2. 实施

### 显式节点状态

- `ImageNodeData` 增加 `editorHeight: 191 | 211 | 274`；
- 五个初始节点写入 `191/191/211/191/274`；
- 新建空图片默认 `191`；
- 图片工具条生成的派生图片显式使用 `274`；
- `ImageEditPanel` 只在兼容旧数据时回退到 variant 高度映射。

这避免了“只要有 Prompt 就是 211px”的错误推断。`咖啡馆` 的 7 字 Prompt 与 `191px` 高度现在可以同时成立。

### 原站内容与入口

- `咖啡` Prompt 从 197 字补齐到原站 602 字；
- `分镜 #2` Prompt 校准为原站 204 字，并保留“孤立感。”后的空格；
- placeholder 替换为原站长句；
- “参考”入口由当前 references 数量控制；
- 无 references 的 `咖啡`、`咖啡馆` 只显示“标记 / 风格”；
- 两张 references 的 `分镜 #2` 显示“参考 / 标记 / 风格”。

### 控件几何与图标

- 顶部入口统一为 `54x26`，间距 `4px`；
- references 统一为 `47x47`，间距 `9px`；
- model、settings 和 footer icon 控件统一为 `32px` 高；
- 移除脑补的 `⌘` / `▭` 可见字符；
- model 使用链形图标，settings 使用矩形图标；
- AutoLink 从顶部文字 pill 移到 footer 链形图标。

AutoLink 候选、确认和写入 references/Prompt token 的现有本地闭环继续可用。入口位置和图标是受现有证据约束的 clone 选择，不声称复刻了原站 SVG 路径或完整弹层。

### 稳定测试接口

新增：

```text
data-image-editor-top-controls
data-image-editor-control
data-image-editor-model
data-image-editor-settings
data-image-editor-footer-icon
data-image-editor-autolink
data-image-editor-autolink-popover
data-image-editor-reference
```

实现与专项测试已提交并推送：

```text
23fbe80 fix: align LibTV image editor states
```

## 3. Batch 10 专项验证

```bash
python3 scripts/verify-liblib-batch10.py
```

脚本直接读取原站 `image-node-state-audit.json`，每个节点创建独立 page，避免旧选择或派生节点污染后续状态。

验证通过：

| 节点 | panel | Prompt | refs | 顶部入口 |
|---|---:|---:|---:|---|
| 男性 | 191 | 0 | 0 | 标记 / 风格 |
| 女性 | 191 | 0 | 0 | 标记 / 风格 |
| 咖啡 | 211 | 602 | 0 | 标记 / 风格 |
| 咖啡馆 | 191 | 7 | 0 | 标记 / 风格 |
| 分镜 #2 | 274 | 204 | 2 | 参考 / 标记 / 风格 |

同时验证：

- 原站 placeholder 完全一致；
- 顶部入口 `54x26`；
- references `47x47`；
- footer 主控件和图标按钮为 `32px`；
- 面板无 `⌘` / `▭` 字符；
- 顶部区域无 AutoLink 文字 pill；
- `咖啡` footer AutoLink 可打开候选，接受后写入两张引用与 token；
- 接受 AutoLink 后 panel 仍保持 `211px`；
- 控制台 error 为 0。

截图：

- `docs/design-references/liblib-clone-batch10-{male,female,coffee,cafe,storyboard}-929-2026-08-25.png`
- `docs/design-references/liblib-clone-batch10-image-editor-state-matrix-2026-08-25.png`

详细识图结果见 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)。Batch 4-Batch 9 的脚本在回归时重新生成了各自已登记的自动化截图，因此实现提交包含若干旧截图基线刷新；本批没有重新识别这些旧图。

## 4. 跨批与工程验证

以下全部通过：

```bash
python3 scripts/verify-liblib-batch4.py
python3 scripts/verify-liblib-batch5.py
python3 scripts/verify-liblib-batch6.py
python3 scripts/verify-liblib-batch7.py
python3 scripts/verify-liblib-batch8.py
python3 scripts/verify-liblib-batch9.py
python3 scripts/verify-liblib-batch10.py
npm run check
```

- lint：0 error，保留仓库既有 9 个 warning；
- TypeScript strict：通过；
- Next.js 16.2.1 production build：通过；
- Batch 9 的工具条/面板锚点、自然裁切和视频 parent-child 跟随未回归。

## 5. 接力边界

- 五节点状态矩阵是同一登录态原站 DOM 直接事实；
- `273.797px` 在 clone 中按 CSS 像素取整为 `274px`；
- `editorHeight` 是对已知状态的显式数据表达，不应重新退化为 Prompt 长度推断；
- Prompt 或 references 在面板内变化时不自动改变高度，因为原站缺少该动态跳高证据；
- AutoLink 本地建议弹层仍是原型闭环，不是完整原站交互声明；
- footer 的 Lucide 图标是语义近似；若后续取得原站 SVG，应单独建批替换并记录路径证据；
- 后续修改 footer 高度时必须重跑 Batch 9 和 Batch 10。

