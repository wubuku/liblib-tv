# LibTV Seedance 2.5 原站复核

> 复核日期：2026-08-25  
> 登录项目：`spaceId=670983` / `projectId=5f2550d0036944e2b618f494276fa1dd`  
> 视口：`929x874`  
> 结构化数据：[`live-audit.json`](live-audit.json)  
> 前端静态字符串：[`live-script-string-evidence.json`](live-script-string-evidence.json)

## 1. 结论

第三方文章列出的五项能力在当前产品中仍能得到不同等级的支持：

| 能力 | 当前证据 | 判断 |
|---|---|---|
| Seedance 2.5 最长 30 秒 | 登录原站模型菜单、参数菜单 | 当前事实 |
| Auto Link | 当前视频生成面板中的开关、3 份参考图和 Prompt 引用 token | 当前事实 |
| 超长视频 300 秒 | 当前模式菜单、`30-300s` 滑块、`300s / 14700` 实测状态 | 当前事实 |
| 逐帧拉片 | 当前添加节点入口和独立 `shot-breakdown` 节点空态 | 当前事实；结果态来自文章截图 |
| 片段重拍 | 文章流程截图 + 当前线上 bundle 的完整文案键 | 功能仍在代码中；本项目没有可用视频，未执行结果任务 |

最重要的结构修正是：**逐帧拉片是独立节点类型，视频生成参数是视频节点下方的编辑面板，二者不能合并成通用视频侧栏。**

## 2. Seedance 2.5 生成面板

选择当前失败视频 `v-UGQZzZOpbv` 后，原站仍展示节点下方的生成面板：

- 面板 `660x273.8`，与图片编辑面板使用相同的节点内绝对定位和 `1 / zoom` 反缩放策略。
- 当前面板有 3 张参考图，以及“参考 / 标记 / 特效 / 角色库 / 运镜”五个输入命令。
- Prompt 中的引用是结构化可视 token，例如 `@陈默 (图片 1)`、`镜头右摇`、`@咖啡 (图片 2)`。
- 高级设置包含“联网搜索”“自动校验素材”“智能引用 AutoLink”，采样时三者均开启。

模型菜单当前可直接验证：

```text
Seedance 2.5
预计 2min
最强视频模型，全能参考，30s音画同步
```

证据截图：

- `docs/design-references/liblib-original-seedance-video-selected-2026-08-25.png`
- `docs/design-references/liblib-original-seedance-model-menu-2026-08-25.png`

## 3. 模式与参数

选择 Seedance 2.5 后，模式菜单显示：

| 模式 | 当前状态 |
|---|---|
| 文生视频 | disabled |
| 全能参考 | enabled |
| 图生视频 | disabled |
| 首尾帧 | disabled |
| 图片参考 | enabled |
| 视频编辑 | disabled |
| 超长视频 Beta | enabled |

普通模式参数：

- 比例：`Auto / 16:9 / 4:3 / 1:1 / 3:4 / 9:16 / 21:9`
- 清晰度：`480P / 720P / 1080P`
- 时长：`4-30s`，采样值 `6s`
- 生成音频：开启/关闭
- 数量：1/2/4 个

超长视频模式把时长范围切换为 `30-300s`。拖到 `300s` 后，底栏显示：

```text
2.5 · 超长视频 · 16:9 · 720P · 300s · 1个 · 14700
```

这与文章截图一致，说明 `300s / 14700` 不是仅存于旧宣传材料的数字。

证据截图：

- `docs/design-references/liblib-original-seedance-mode-menu-2026-08-25.png`
- `docs/design-references/liblib-original-seedance-params-menu-2026-08-25.png`
- `docs/design-references/liblib-original-seedance-long-params-2026-08-25.png`
- `docs/design-references/liblib-original-seedance-long-video-300s-current-2026-08-25.png`

## 4. 逐帧拉片节点

“添加节点”中的入口名称为“逐帧拉片”，徽标为 `SD 2.5`。点击后创建专用 React Flow 类型：

```text
react-flow__node-shot-breakdown
```

空态世界尺寸约 `320x389`，屏幕尺寸约 `90.5x110`（当前 zoom 约 28%）。节点包含：

- 标题“逐帧拉片”和 `SD 2.5` 标记；
- “视频素材”上传区，文案“上传视频后开始”；
- “拆解维度”的“分镜 / 动态 / 音乐”三个按钮，默认均为选中视觉；
- disabled 的“开始拉片”按钮。

线上 bundle 还明确列出状态：“拉片中”“拉片失败，请重试”“上游视频未就绪”，并提供“从画布选择”“画布上暂无可用视频”“替换素材”。这说明节点同时支持上传与连接/选择画布视频。

文章结果截图显示结果不是长篇报告，而是三类媒体卡：

- `S01...S08` 分镜关键帧，带景别、机位、运镜或内容描述；
- `M01...M03` 动态视频片段，带时长和运动摘要；
- BGM 波形卡，带时长和播放控制。

证据：

- `docs/design-references/liblib-original-seedance-frame-analysis-node-2026-08-25.png`
- [`evidence/frame-analysis-entry.png`](evidence/frame-analysis-entry.png)
- [`evidence/frame-analysis-output.png`](evidence/frame-analysis-output.png)

## 5. 片段重拍与就绪视频工具栏

当前项目只有生成失败的视频，没有可播放源视频，因此不能安全走完片段重拍和逐帧分析任务。以下内容按证据等级保留：

### 当前 bundle 可确认

- 入口文案“片段重拍”。
- 源视频时长至少 4 秒。
- 选片提示“点击可截取新片段”，剩余区间不足 4 秒时提示不可选。
- 修改输入提示“描述这段视频要如何修改”。
- 未选区间时编辑整段视频。
- Prompt 投影支持“把 {video} 中 {start}-{end}”和“将 {video} 的第 {start} 秒到第 {end} 秒：{intent}”。
- Seedance 2.5 不可用、源视频丢失、片段处理失败和真人校验失败均有独立状态。

### 文章截图可确认

- 横向缩略时间带以 `4.0s` 为可选片段。
- 选择计数为 `0/5`、`1/5`，截图上限为 5。
- 选择后 Prompt 自动插入 `视频 1` 与 `00:00-00:04`，用户继续填写局部修改。
- 就绪视频的顶部工具栏包含高清、逐帧拉片、智能续写、智能去字幕、音频分离、画面编辑、下载和展开。

这些是实现前端交互的充分证据，但不能声称本轮真实提交过重拍或拉片任务。

## 6. 智能剪辑节点

“视频编辑 Beta”当前创建另一个专用类型 `react-flow__node-video-clip`，世界尺寸约 `350x350`。空态标题为“智能剪辑 1”，包含：

- 讲解视频 / 批量广告 / 口播视频 / 素材混剪四个模式；
- 参考入口；
- Prompt 空态“描述想剪成什么效果”；
- 默认模式和 `16:9 · 720P · 30s`；
- 无输入时 disabled 的发送按钮。

它说明 LibTV 把“通用智能剪辑”和“逐帧拉片”作为不同节点类型。本轮复刻 Seedance 主推能力时不应把两者混在一起。

证据：`docs/design-references/liblib-original-seedance-video-edit-node-2026-08-25.png`。

## 7. 对实现计划的修订

1. 新增专用 `ShotBreakdownNode`，并让 AddNode 的入口创建该类型；这是最高置信度改动。
2. 为视频节点补 `660px` 生成编辑面板，复用图片面板的反缩放定位合同，但使用视频专属命令、模型、模式和参数。
3. Seedance 参数菜单按当前原站实现普通 `4-30s` 与超长 `30-300s` 两套范围，`300s` 显示 `14700` 本地预计积分。
4. 片段重拍作为就绪视频工具栏动作和节点下方面板实现；由于没有当前项目结果态，只实现截图与 bundle 能确认的选择/Prompt 闭环。
5. 拉片结果用结构化媒体卡展示，并明确为本地示例结果；不伪造真实分析任务。
6. `VideoClipNode` 只在不拖慢上述主线时实现基本空态，优先级低于逐帧拉片和 Seedance 生成面板。

## 8. 2026-08-26 浏览器现场几何抽查

本次使用已打开的登录态 LibTV 画布进行只读交互：

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

操作仅包括读取当前 DOM、选中现有失败视频节点、再选中现有图片节点；没有提交任务、上传媒体、修改参数或写入远端画布。

### 图片节点选中态

在视口 `929x874`、设备像素比 `2`、React Flow viewport transform 为：

```text
matrix(0.278112, 0, 0, 0.278112, 17.9639, 131.434)
```

选中的图片节点和两个浮层矩形如下，单位为 CSS px：

| 元素 | x | y | width | height | 备注 |
|---|---:|---:|---:|---:|---|
| 图片节点 | 54.675 | 207.358 | 171.873 | 97.339 | 屏幕左侧节点 |
| 顶部工具条外层 | -405.641 | 141.680 | 1092.500 | 49.000 | 节点中心对齐，左侧被裁切 |
| 底部编辑面板外框 | -189.389 | 309.148 | 660.000 | 191.000 | 节点中心对齐，左侧被裁切 |

可复核关系：

- 节点中心 `x=140.611`；工具条中心 `x=140.609`，误差约 `0.002px`；编辑面板中心 `x=140.611`；
- 工具条底部到节点顶部约 `16.679px`，符合源站 `16px` 级别的屏幕间距；
- 节点底部 `304.698px` 到编辑面板外框顶部 `309.148px` 约 `4.450px`，与 `16 * 0.278112 = 4.450px` 一致；
- 两个浮层均保留节点中心作为锚点，因节点靠近画布左侧而出现负 x；源站没有把浮层强行移到浏览器中心。

现场 DOM 还确认顶部图片工具条的当前可见动作顺序为：

```text
人像质感调节 / 全景 / 多角度 / 打光 / 九宫格 / 高清 / 元素编辑 / 图层分离 / 宫格切分
```

### 失败视频节点选中态

同一视口下选中现有失败视频节点时，节点与生成面板为：

| 元素 | x | y | width | height | 备注 |
|---|---:|---:|---:|---:|---|
| 失败视频节点 | 695.446 | 145.339 | 172.986 | 97.339 | 节点底部 `242.679` |
| 视频生成面板外框 | 451.939 | 247.129 | 660.000 | 273.797 | 节点中心对齐，底部 gap 约 `4.450px` |

节点中心为 `781.939`，面板中心同为 `781.939`；面板顶端与节点底部的间距仍为 `16 * 0.278112`。失败节点当前仍能打开下方生成面板，面板内可见 `参考 / 标记 / 特效 / 角色库 / 运镜` 五个输入命令，以及模型、模式、参数和 AutoLink 状态。

本次失败状态没有观察到“就绪视频”的顶部处理工具条，因此不能用该节点推断高清、逐帧拉片、智能续写、智能去字幕、音频分离和画面编辑等就绪态动作的实际位置。文章截图和 bundle 文案仍作为独立证据保存。

### 证据解释

这是一次当前登录态的现场抽查，不代表所有图片尺寸、zoom、工具条折叠状态和移动端布局。它足以把以下内容从待测假设提升为当前场景的 `SOURCE_FACT`：

1. 源站顶部工具条的当前外层屏幕宽度为 `1092.5px`，不是浏览器居中后的任意宽度；
2. 底部生成/编辑面板外框保持 `660px` 宽度和 `191px` 高度；
3. 底部间距以 viewport zoom 参与计算；
4. 左边缘裁切是源站可见行为，不应为了“完整显示”而擅自 clamp。

这组数据需要与先前的 `900.5x49` 工具条记录并列保存，不能直接覆盖。随后完成的五节点复测已在下一节把差异归因为源站动作集合的时间版本更新，而不是图片节点或 panel 内容态分支。

## 9. 五图片节点复测与工具条版本归因

本轮在相同 `929x874` viewport、相同 `matrix(0.278112, 0, 0, 0.278112, 17.9639, 131.434)` 下依次清除选择并单选五个现有图片节点。清除选择是必要步骤：宽工具条可能覆盖其他节点，直接连续点击会命中前一节点的工具条而不是目标节点。

| 节点 | Toolbar | Panel | Toolbar center delta | Panel center delta | T gap / P gap |
|---|---|---|---:|---:|---:|
| `image_2026-06-15T11-22-00` | `1092.5x49` | `660x191` | `-0.002` | `0` | `16.678 / 4.450` |
| `咖啡` | `1092.5x49` | `660x211` | `-0.001` | `0` | `16.677 / 4.450` |
| `image_2026-06-15T11-22-15` | `1092.5x49` | `660x191` | `-0.005` | `0` | `16.682 / 4.450` |
| `图片4` | `1092.5x49` | `660x191` | `-0.001` | `0` | `16.679 / 4.450` |
| `分镜 #2` | `1092.5x49` | `660x273.797` | `-0.008` | `-0.001` | `16.680 / 4.450` |

结果确认当前动作集合与图片内容态无关：五个节点均显示 9 个文字动作和 4 个图标动作。与 2026-08-25 的 [`image-node-state-audit.json`](../liblib-live-2026-08-25/image-node-state-audit.json) 对照后，`900.5 -> 1092.5` 可以归因为源站在两次审计之间新增：

```text
元素编辑 88px + gap 8px + 图层分离 88px + gap 8px = 192px
```

当前外层 DOM 使用 `w-fit`，说明工具条宽度由动作集合决定。完整 rect、按钮 test id、宽度和 clone 差异见 [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_GEOMETRY_MATRIX.md)，结构化记录见 [`libtv-image-overlay-audit-2026-08-26.json`](libtv-image-overlay-audit-2026-08-26.json)。

这次归因修正了上一节的未决表达：`900.5` 和 `1092.5` 都是真实源站快照，但前者是历史动作集合，后者是当前动作集合；没有证据支持把它们解释成不同图片节点或不同 panel 内容态的宽度分支。

## 10. 图片工具态与预览浮层

本轮继续使用当前页面已加载的前端 chunks 做静态处理路径审计，并只 live 打开无任务风险的预览和空标注态。唯一命中六个当前工具动作 test id 的 chunk 为 `15epcn_e-6pl6.js`，当前长度 `1,563,088` bytes。

### 预览

`图片4` 的预览是 page-level `MediaPreviewOverlay`：

| 元素 | DOM rect |
|---|---|
| overlay | `0,0,929,874` |
| content | `69.67,87.40,789.65,699.20` |
| 图片 | `69.67,239.59,789.65,394.82` |
| 水印 | `79.67,249.59,48,23.31` |
| 关闭按钮 | `839.32,75.40,32,32` |

overlay 使用 `fixed inset-0` 和 `bg-black/80`，当前单输出节点没有 prev/next；bundle 表明多输出时会按 output/history index 提供翻页。关闭后节点选择、标准工具条和底部面板保持原状态。

### 空标注态

`图片4` 进入标注后：

- 标准 `1092.5x49` 工具条被 `536x49`、8 按钮的专用工具条替换；
- 专用工具条与节点中心误差 `-0.009px`，到节点顶部 gap `9.726px`；
- 标准底部 `660px` 生成面板卸载；
- 节点上叠加 CSS rect `194.117x97`、backing size `388x194` 的 canvas，符合 DPR `2`；
- 工具条可见 `标注 / 保存`，undo/redo 在空态 disabled；
- 按 Escape 后专用工具条和 canvas 卸载，标准双浮层恢复。

没有绘制或点击保存。其他四个动作的 bundle 状态、潜在任务和 clone 差异见 [`LIBTV_IMAGE_ACTION_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_IMAGE_ACTION_MATRIX.md)。图层分离存在任务提交路径，下载存在水印偏好和文件副作用，旋转保存可能上传/更新节点，均未 live 点击。

## 11. AutoLink 高级设置与正式 mention

本轮对 AutoLink 只做节点选择、高级设置 disclosure 和 DOM 读取，没有编辑 Prompt、切换开关或接受新 mention。

### 图片高级设置

在约 `28%` zoom 下，`i-1FQ9tErTcC` 的默认图片面板为 `660x191`。高级设置收起时，AutoLink row 虽存在于 DOM，但其祖先为 `grid-rows-[0fr]`、实际高度 `0px`，由 `overflow-hidden` 裁切。

点击 footer 的 sliders 按钮后：

| 元素 | rect / state |
|---|---|
| Panel | `660x275.5` |
| Advanced grid | `643x76.5`, `grid-rows-[1fr]` |
| AutoLink row | `627x36` |
| Switch | `38x20`, checked, enabled |

面板仍保持 node-center anchor，靠近左边缘时负 x 不做 clamp。bundle 表明开关使用 `libtv:promptMentionEnabled` 全局本地偏好，默认 `true`。

### Reference 与 mention 不是同一层

`分镜 #2` 当前有两个 `48x48` draggable reference thumbnails，左上角编号 `1/2`，右下角各有 `12x12` 的 `@` 入口；其 Prompt editor 当前没有正式 mention badge。reference list 可以存在而 Prompt 不包含 mention。

失败视频 `v-UGQZzZOpbv` 的 Prompt 则有四个 `contenteditable=false`、`draggable=true` badge：

| 可见标签 | type | node ID | index |
|---|---|---|---:|
| 图片 1 | `mixed` | `i-1FQ9tErTcC` | 1 |
| 镜头右摇 | `camerapreset` | 空 | 1 |
| 图片 1 | `mixed` | `i-1FQ9tErTcC` | 1 |
| 图片 2 | `mixed` | `i-dnwoZQ7jsG` | 2 |

同一素材在两处都保留同一 stable node ID 和 ordinal，证明“图片 1”只是当前 reference order 的 UI 投影。

### Bundle 状态链

当前生产实现从 connected/reference assets 构造名称、tag 和媒体 ordinal 候选，在 contenteditable 内注入 `data-mention-suggest` ghost spans。click/`Tab` 接受 active suggestion，`Shift+Tab` 接受全部；`Escape`、普通编辑和 blur 清理 ghost。检测还会避开 IME composition、其他 Prompt popover 和 stale async result。

完整 source/clone 矩阵见 [`LIBTV_AUTOLINK_STATE_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md)，原始 rect 和 token 字段见 [`libtv-autolink-audit-2026-08-26.json`](libtv-autolink-audit-2026-08-26.json)。

## 12. 多 zoom 顶部 host 源码复核

在继续保持只读边界的情况下，从当前页面加载的生产 chunk [`0jf40wzwc66-8.js`](https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/0jf40wzwc66-8.js) 定位到带 `data-image-editor-toolbar` 的标准图片工具条 host。其定位形态为：

```text
left = nodeScreenLeft + nodeScreenWidth / 2
top = nodeScreenTop - 24 * zoom - 10
transform = translateX(-50%) translateY(-100%)
```

因此，`10 + 24 * zoom` 不再只是 live rect 的拟合，而是当前 production chunk 的源码事实。继续补测的 41% 样本为 toolbar `1092.5x49`、top gap `19.778px`、panel gap `6.516px`，分别与该 host 公式和 `16 * zoom` 对齐。当前四个直接可见档位的 top gap 为 `16.794/18.152/19.778/22px`，panel gap 为 `4.525/5.430/6.516/8px`。

这段源码同时存在 active image tool 的其他定位分支，所以标准公式不能外推到标注、旋转、元素编辑或图层分离专用工具条。完整矩阵与结构化证据见 [`LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md) 和 [`libtv-overlay-multizoom-audit-2026-08-26.json`](libtv-overlay-multizoom-audit-2026-08-26.json)。
