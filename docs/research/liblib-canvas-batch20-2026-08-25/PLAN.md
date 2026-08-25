# Batch 20 计划：720° 全景派生节点

## 1. 缺口与价值

| 缺口 | 当前 clone | 原站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 交互模型错误 | 点击全景后复制当前图片 | 创建空的 `720°全景图` 节点 | 5 | 修复 |
| 节点内容错误 | 派生节点直接显示源图片 | 新节点是深色占位态 | 5 | 增加 panorama placeholder |
| 面板内容泛化 | 通用 tool Prompt | 单参考图、`720全景` 专用提示 | 5 | 增加专用 panel variant |
| 输出参数错误 | 沿用源节点或通用设置 | `2:1 · 标准画质 · 2K · 1张` | 4 | 使用源站文案 |
| 派生几何粗略 | 默认 image 为 `512x288`、同 y | 截图反推约 `700x350`，且略高于 source | 4 | 支持可选派生 geometry |
| 其他五个动作 | 统一立即创建派生节点 | 本批没有逐动作截图 | 3 | 不扩展、不声明忠实 |

## 2. 实施步骤

1. 扩展 `canvasStore.addDerivedNode`，允许调用方提供可选 dimensions 和 world offset；现有调用保持默认行为。
2. `ImageNodeData` 增加 panorama placeholder / editor variant。
3. 点击 `全景` 时创建：
   - `700x350` image node；
   - filename `720°全景图`；
   - 空 media placeholder；
   - source image 作为唯一 reference；
   - `2:1 · 标准画质 · 2K · 1张`；
   - source 右侧并向上偏移的顶层节点。
4. `ImageEditPanel` 增加专用 panorama branch：
   - `+参考`
   - 一个 `47x47` reference
   - `720全景`
   - 原站 helper copy
   - Lib Image / output settings / local submit
5. 保留其他 toolbar action 当前行为，但在规格中明确它们没有逐动作原站合同。
6. 新增 Batch 20 Playwright：
   - graph `10/11 -> 11/12`
   - 新节点选中、空 placeholder、标题和 geometry
   - 新 edge source/target
   - panel anchor、尺寸、reference、文案和参数
   - undo/redo 单事务
   - 390px 自然裁切、无页面溢出
   - console/page error
7. 更新图片组件规格、行为、Harness、Big Picture 和 CHANGELOG。

## 3. 事实边界

### Source fact

- 原站截图 viewport 为 `929x874`，zoom 文案为 `28%`。
- 点击“全景”后出现标题为 `720°全景图` 的新空图片节点。
- 源图片与新节点之间有一条新 edge。
- 新节点下方出现专用面板，面板中有：
  - `+参考`
  - 一张编号 `1` 的源图缩略图
  - `720全景`
  - `点击生成，直接将场景图像转为720全景图，支持文生/参考...`
  - `Lib Image`
  - `2:1 · 标准画质 · 2K · 1张`

### Inference

- 由截图屏幕矩形和 `28%` zoom 反推，新节点约为 `700x350` world units。
- 新节点约位于 source right `+120` world units，并向上约 `110` world units。
- 专用面板约 `660x252px`，水平中心与新节点中心一致。

### Clone-only decision

- `addDerivedNode` 使用可选 geometry 参数表达该差异，不改变其他派生动作默认值。
- 生成按钮只显示本地提交状态，不替换空节点媒体。
- 未采样的其他图片动作暂不改写为 panorama 流程。

## 4. 验收标准

- 点击“全景”新增且选中一个空 `720°全景图` image node。
- 新节点 world size 为 `700x350`，screen size 与当前 zoom 一致。
- source-to-derived edge 与节点添加属于一个 undo/redo 事务。
- 新 panel 中只有一个源图片 reference，并显示专用 720 copy 与 `2:1` 参数。
- panel 保持节点锚定和反缩放，不使用页面固定定位。
- desktop 截图与原站同为 fit-view `28%` 状态。
- mobile 不产生页面级横向溢出，panel 按既有规则自然裁切。

