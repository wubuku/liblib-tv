# LibTV 画布 Batch 10 计划：图片编辑器五节点状态矩阵

> 建档日期：2026-08-25
> 原则：先逐节点列出原站事实，再实现；不得让 `editorVariant` 替代已知的节点状态数据。

## 1. 缺口与价值

| 审计项 | 当前 clone | 原站证据 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 五节点面板高度 | `empty=191`、`prompt=211`、其他 `274` | 实际为 `191/191/211/191/273.797` | 5 | 增加显式高度 |
| `咖啡` Prompt | 197 字 | 602 字 | 5 | 写入完整原文 |
| `咖啡馆` 高度 | 211 | 191 | 5 | 校准为 191 |
| “参考”入口 | 所有非 empty variant 显示 | 仅两张参考图的 `分镜 #2` 显示 | 5 | 由 references 决定 |
| placeholder | clone 自拟短句 | 原站固定长句 | 4 | 替换 |
| 顶部 chip 高度 | 28px | 26px | 4 | 校准 |
| footer 主控件 | 约 28px | 32px | 4 | 校准 |
| model/settings 前缀 | `⌘` / `▭` 字符 | 原站为图标，不是可见字符 | 4 | 使用 Lucide 图标 |
| AutoLink 顶部 pill | 可见文字 pill | 五个采样状态无顶部 AutoLink pill；面板文本仍含 AutoLink | 4 | 移到 footer 图标入口 |
| AutoLink 闭环 | 建议、确认、写入引用 | 原站该具体弹层未完整审计 | 3 | 保留为 clone 原型，不冒充原站事实 |
| 参考缩略图尺寸 | clone 48px | 原站矩形 47px | 3 | 校准为 47px |
| 派生图片状态 | tool 固定 274 | 原站派生节点未逐状态采样 | 2 | 保留 274，显式写数据 |

## 2. 实施顺序

### 阶段 A：数据与组件合同

1. 给 `ImageNodeData` 增加显式 `editorHeight`；
2. 为五个初始图片节点写入原站高度；
3. 写入 `咖啡` 的完整 602 字 Prompt；
4. 派生图片显式使用 `274px`，默认新图片使用 `191px`；
5. `ImageEditPanel` 不再从粗粒度 variant 单独推断高度。

### 阶段 B：面板内部忠实度

1. “参考”入口仅在 references 非空时出现；
2. 顶部 chip 高度改为 `26px`；
3. placeholder 替换为原站文案；
4. 参考图改为 `47x47`；
5. footer 的模型、参数和图标按钮统一为 `32px` 高；
6. 去掉脑补字符 `⌘`、`▭`，改用语义接近的 Lucide 图标；
7. AutoLink 入口改为 footer 链形图标，候选弹层和确认写入流程继续可用；
8. 增加稳定 data attribute，供逐状态验证。

### 阶段 C：专项验证

新增 `scripts/verify-liblib-batch10.py`，每个节点使用独立新 page：

- 页面加载后整理画布；
- 单独选中一个目标节点；
- 校验 panel 高度、Prompt、placeholder、参考图数量、顶部入口集合和 settings；
- 校验 chip `26px`、footer 主控件 `32px`；
- 校验无参考图时没有“参考”入口；
- 校验 AutoLink 不以顶部文字 pill 出现；
- 在 `咖啡` 节点点击 footer AutoLink，确认建议弹层和接受流程仍工作；
- 校验控制台 error 为 0；
- 保存五节点状态矩阵截图。

每个节点使用独立 page 是硬要求。旧面板或工具条点击状态可能创建派生节点，顺序复用页面会污染后续抽取。

### 阶段 D：回归与留档

- 运行 Batch 4-Batch 10；
- 运行 `npm run check`；
- 更新 `ImageEditPanel.spec.md`、`ImageNode.spec.md`、`BEHAVIORS.md` 和文档索引；
- 将新截图的识图结果记录到本批 `IMPLEMENTATION.md`，避免后续重复识别；
- 完成关键阶段后 commit 并 push。

## 3. 不做

- 不重新设计图片生成器；
- 不实现真实生成、模型选择、翻译或服务端持久化；
- 不把 clone 的 AutoLink 建议弹层描述成原站已验证的完整交互；
- 不修改图片工具条锚点；
- 不修改视频生成面板；
- 不修改 FrameOS；
- 不重复识别已有原站整图。

## 4. 验收标准

| 节点 | 高度 | Prompt 长度 | refs | 顶部入口 | settings |
|---|---:|---:|---:|---|---|
| 男性 `i-1FQ9tErTcC` | 191 | 0 | 0 | 标记 / 风格 | 16:9 · 标准画质 · 2K · 1张 |
| 女性 `i-lBzmo67AHv` | 191 | 0 | 0 | 标记 / 风格 | 16:9 · 标准画质 · 2K · 1张 |
| 咖啡 `i-dnwoZQ7jsG` | 211 | 602 | 0 | 标记 / 风格 | 2:1 · 低画质 · 1K · 1张 |
| 咖啡馆 `i-vxeeCnxySa` | 191 | 7 | 0 | 标记 / 风格 | 2:1 · 低画质 · 1K · 1张 |
| 分镜 `i-YDfWhFlthe` | 274 | 204 | 2 | 参考 / 标记 / 风格 | 16:9 · 低画质 · 1K · 1张 |

通用：

- placeholder 与原站完全一致；
- 顶部入口按钮高度 `26px ± 0.5px`；
- model/settings/footer 图标按钮高度 `32px ± 0.5px`；
- 无可见 `⌘`、`▭` 字符；
- 顶部区域没有可见“智能引用 AutoLink”文字 pill；
- footer AutoLink 可打开候选并接受，写入两张引用；
- Batch 9 锚定几何不回归；
- 控制台 error 为 0；
- TypeScript strict、lint 和 production build 通过。

