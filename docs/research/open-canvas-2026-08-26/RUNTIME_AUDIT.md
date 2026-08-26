# Open Canvas 官网运行态审计

## 1. 审计元数据

| 项目 | 记录 |
|---|---|
| 官网 | [https://open-canvas.cyberbara.com/zh](https://open-canvas.cyberbara.com/zh) |
| 画布入口 | [https://open-canvas.cyberbara.com/zh/canvas](https://open-canvas.cyberbara.com/zh/canvas) |
| 观察日期 | 2026-08-26（Asia/Shanghai） |
| 工具 | Codex in-app Browser，DOM 文本/可访问树、截图、不同 viewport |
| 登录 | 未登录；官网公开页可访问 |
| 外部副作用 | 未输入 Key、未创建/删除画布、未上传文件、未触发生成、未调用分享 |
| 相关源码版本 | submodule `cf3a906bb8c35bb940d3267497e7f394b8f42582` |

本页只记录官网“呈现了什么”和公开入口如何引导用户，不把营销描述直接当成后端已实现能力。源码事实与运行事实分开记录。

## 2. 中文落地页

### 2.1 首屏信息架构

页面标题为 `Open Canvas - 开源 BYOK AI 工作流画布`。导航包含：

- Open Canvas 品牌入口；
- 工作方式；
- 模型提供方；
- 快速开始；
- GitHub；
- English；
- 打开应用。

H1 是 `无限 AI 画布，完全开放。`，副文案强调：摆脱 TapNow、LibTV、Higgsfield 等封闭生态，带上自己的 API Key，在空间化工作区中生成、编辑和串联图片/视频。

CTA 为 `开始创作` 与 `在 GitHub 点星`。这说明 Open Canvas 的公开品牌层把“开放、BYOK、空间化多模态工作流”作为第一认知，而不是把单一模型或单一模板作为主叙事。

### 2.2 预览画面传达的工作台语义

首屏预览不是抽象插图，而是一个可读的画布工作台片段。可见标签/控件包括：

- `画布工作台`；
- `群像 FPV 镜头模板`；
- 计数 `2927`；
- `保存中` 状态；
- `分享` 按钮；
- 缩放 `101%`；
- 两个 `图片节点` 和一个 `视频节点`；
- 视频时间轴 `0:00 / 0:15`。

由此可作一个有依据的产品推断：落地页预览刻意展示“节点图 + 保存状态 + 画布控制 + 媒体播放”的组合，让用户在进入应用前理解它是可编辑的工作区，不是单次生成表单。这个推断不能替代真实 studio 的精确布局测量。

### 2.3 Provider 与快速开始

页面展示的 provider marquee 包含 OpenAI、Gemini、OpenRouter、Replicate、Cyberbara。快速开始被拆成三步：

1. 带上自己的 Key；
2. 添加节点；
3. 连接并生成。

页面还提供托管 Web App 和 AI 自托管两种入口。FAQ 的首要问题围绕 BYOK、是否免费、是否支持自托管、托管模式如何处理 key。

这里需要保留事实边界：marquee 是官网信息架构的一部分；它不能单独证明固定 commit 中每个 provider 的 current studio execution 都已可用。源码对比见 [`SOURCE_ANALYSIS.md`](SOURCE_ANALYSIS.md#7-provider-事实与关键缺口)。

## 3. 中文画布入口

访问 `/zh/canvas` 时，未登录且没有已创建画布的页面显示：

- 标题 `AI 画布`；
- 描述 `创建画布，用可视化方式分支思路，把文本、图片和视频节点串联到同一个工作区。`；
- `设置`、`设置向导`、`导入 JSON`、`新建画布` 操作；
- 空状态标题 `还没有画布`；
- 空状态描述 `从一块空白画布开始，搭建你的第一个多模态工作流。`；
- CTA `创建第一个画布`。

页面首次打开会主动弹出 `设置 Open Canvas` 向导。向导有三步：

1. `选择 Key`；
2. `添加存储`；
3. `开始创作`。

首步文案说明至少需要一个 provider key；示例定位为 OpenRouter 负责文本、Replicate 负责图片/视频、Cyberbara 负责媒体生成/上传。

可见输入项包括：

| 分组 | 字段 |
|---|---|
| OpenRouter | OpenRouter API Key、OpenRouter Base URL |
| Replicate | Replicate API Token |
| Cyberbara | Cyberbara API Key、Cyberbara Base URL |
| 操作 | 跳过、继续、关闭 |

本次审计关闭了向导，没有写入任何值，也没有新建画布。这一状态足以审计空状态和 onboarding，不足以审计真实节点菜单、选中节点上下浮层、模型设置、连接校验或生成轮询。

## 4. 证据截图

以下文件由本次浏览器审计保存到仓库 `docs/design-references/`：

- [中文落地页桌面截图](../../design-references/open-canvas-official-landing-zh-2026-08-26.png)
- [中文落地页移动截图（390px）](../../design-references/open-canvas-official-landing-zh-mobile-390-2026-08-26.png)
- [中文画布空状态截图](../../design-references/open-canvas-official-canvas-empty-zh-2026-08-26.png)

截图用途是保留布局、层级、文案和首屏视觉证据。它们不是当前 LibTV clone 的实现素材，也不授权直接复制品牌图片或第三方媒体。

## 5. 官网与源码的交叉核对

| 观察项 | 官网运行态 | 固定源码的对应点 | 结论 |
|---|---|---|---|
| BYOK | 首屏和向导反复强调自带 Key | ProviderSettingsDialog、provider settings cookie | 方向一致 |
| 多 provider | marquee 和向导列出 OpenAI/Gemini/OpenRouter/Replicate/Cyberbara | registry 更广，但实际 runner 当前偏 Cyberbara | 宣传面宽于已核实执行面 |
| 画布列表 | 空状态、创建入口、JSON 导入 | `CanvasListPage` + local canvas store | 一致 |
| 多模态节点 | 落地页预览图片/视频节点 | graph 支持 text/note/image/video/audio | 一致，但真实 studio 节点细节未在本次未登录审计中操作 |
| 保存/分享 | 预览展示保存中与分享按钮 | store 有自动保存/冲突状态，README 声称暂无分享链接 | 预览可能代表主产品/目标状态，不能直接当成 alpha 能力 |
| 模板 | 预览写有模板名 | graph 有 template 类型和 API 文件，但 README known limits 写暂无模板库 | 固定版本存在代码与文档漂移，需在实施前单独复核 |

## 6. 仍需后续取证的交互

本次没有登录，也没有 API key，因此以下高价值区域应列为“待获得可执行条件后再审计”：

1. 创建一张空画布后，节点添加菜单、节点默认位置和初始选中态；
2. 点击图片节点后，上方工具条、下方编辑面板的锚点、z-index、缩放行为和移动端布局；
3. Image/Video 节点的 generate/upload 切换、模型选项和引用输入；
4. 节点连线时的 handle 方向、非法连接反馈和边上的操作入口；
5. 运行中、成功、失败、轮询、重试和保存冲突状态；
6. JSON 导入/导出与画布列表的实际互通；
7. 分享按钮到底是 UI 预览装饰还是公开模板/链接能力。

这些项目应在浏览器中记录 DOM rect、截图和操作前后 graph/API 请求，继续遵守“源站事实、证据推断、clone-only 决策”分栏规则。
