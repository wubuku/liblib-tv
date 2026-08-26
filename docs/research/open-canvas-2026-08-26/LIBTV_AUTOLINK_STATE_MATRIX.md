# LibTV AutoLink 状态与数据契约矩阵

> 定位：记录 2026-08-26 当前 LibTV 生产前端中“智能引用 AutoLink”实际有什么、如何呈现、如何接受以及如何写入 Prompt。本文是源站研究，不代表已经授权修改 clone 代码。

## 1. 结论先行

当前 AutoLink 不是 clone 中的“固定候选弹窗 + 一次性引用按钮”。它由四层协作：

```text
高级设置中的全局开关
  -> 从已连接/可引用素材构造候选池
  -> 在 contenteditable 中注入不改写正文的 ghost suggestion
  -> 点击 / Tab / Shift+Tab 接受后写入带稳定 node ID 的 mention badge
```

最关键的源站合同是：

1. `智能引用 AutoLink` 位于图片/视频生成面板的“高级设置”折叠区，不是 Prompt 顶部 pill，也不是仅在无参考图时出现的 footer 图标。
2. 开关使用全局本地偏好 `libtv:promptMentionEnabled`，默认开启；图片和视频不是两套独立布尔值。
3. 自动检测只产生 ghost suggestion；在用户接受前不改写 Prompt、不新增正式 mention。
4. 单个建议可点击或按 `Tab` 接受；`Shift+Tab` 接受当前全部建议；`Escape`、编辑、blur 会拒绝/清理建议。
5. 正式媒体 mention 保存稳定 `data-mention-node-id`、媒体类型和当前序号；“图片 1/2”是展示投影，不是素材身份。
6. 同一素材在 Prompt 中重复出现时复用相同 node ID 和 ordinal；当前视频 Prompt 中 `i-1FQ9tErTcC` 两次都投影为“图片 1”。
7. 当前实现没有证据支持 clone 的独立“匹配到陈默、咖啡 2 个画布素材”确认 popover。

## 2. 证据范围

### 2.1 现场观察

- 页面：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`
- 观察日期：2026-08-26
- viewport：`929x874`
- 画布 zoom：现场两个样本约 `28%`；几何数字只用于当前 viewport，不外推移动端
- 安全边界：只切换节点选择、展开/收起高级设置并读取 DOM；没有输入 Prompt、接受建议、切换 AutoLink、生成、上传、下载或保存

结构化现场数据见 [`libtv-autolink-audit-2026-08-26.json`](../liblib-seedance-2.5-2026-08-25/libtv-autolink-audit-2026-08-26.json)。

### 2.2 当前生产 chunks

| Chunk | 直接可见内容 |
|---|---|
| `3_ztchafem3jb.js` | toggle store、候选构造、ghost suggestion、接受/拒绝、mention commit、canvas reference connect |
| `32_oy6xm14gsz.js` | 上述实现的同内容加载副本 |
| `2axsluxmmf6m6.js` | Prompt reference dropdown / 手动插入相关实现 |
| `0_o2gxip5splz.js` | AutoLink、Tab 提示、空态和帮助文案 |

静态 URL 均记录在原始 JSON。chunk 名是当前部署证据，不应当成为 clone 运行依赖。

## 3. 可见状态矩阵

### 3.1 图片生成面板

以 `i-1FQ9tErTcC` 为样本：

| 状态 | Panel | 折叠容器 | AutoLink row | Switch |
|---|---|---|---|---|
| 高级设置收起 | `660x191` | `grid-rows-[0fr]`, `0px` | DOM 存在但被 `overflow-hidden` 裁切 | checked `true`, disabled `false` |
| 高级设置展开 | `660x275.5` | `grid-rows-[1fr]`, `76.5px` | `627x36`，位于“高级设置”标题下 | `38x20`, checked `true`, disabled `false` |

展开按钮是 footer 中的 sliders 图标；当前按钮序列里它位于翻译按钮之前。面板展开后仍保持 `660px` 屏幕宽度和原 node-center anchor，负 x 继续被画布自然裁切。

折叠容器从 `0` 增至 `76.5px`，同时原先的负 margin 被取消，因此 panel 总高从 `191` 增至 `275.5px`，净增 `84.5px`。这是一种内容展开态，不是 page-level popover。

### 3.2 图片参考缩略条

`分镜 #2` 当前显示两个已有引用：

- 每项 `48x48`，外层 `draggable=true`；
- 左上角编号分别为 `1`、`2`；
- 右下角有 `12x12`、默认透明的 `@` 按钮；
- reference row 与 Prompt editor 分层；单凭 reference thumbnail 不能证明 Prompt 中已存在 mention。

这个结构把“参与本次生成的参考素材”和“Prompt 中某一次文本 mention”分开。二者可以关联，但不是同一个 DOM 元素或同一个状态。

### 3.3 视频 Prompt 的正式 mention badge

当前失败视频节点 `v-UGQZzZOpbv` 的 contenteditable 中有四个正式 badge：

| 顺序 | 可见标签 | `data-mention-type` | `data-mention-node-id` | `data-mention-index` | 媒体类型 |
|---:|---|---|---|---:|---|
| 1 | 图片 1 | `mixed` | `i-1FQ9tErTcC` | 1 | image |
| 2 | 镜头右摇 | `camerapreset` | 空 | 1 | 空 |
| 3 | 图片 1 | `mixed` | `i-1FQ9tErTcC` | 1 | image |
| 4 | 图片 2 | `mixed` | `i-dnwoZQ7jsG` | 2 | image |

每个 badge 都是 `contenteditable=false`、`draggable=true`，并含 `data-mention-thumb` 和 `data-mention-label`。这直接证明：

- 正式 token 是结构化 inline object，不是 textarea 中拼接出的普通字符串；
- 同一 source node 可以被多次 mention；
- ordinal 是同一参考集合中的显示编号；
- camera preset 也复用 mention badge 视觉，但不伪造媒体 node ID。

## 4. 静态状态链

### 4.1 Toggle 生命周期

```text
首次挂载
  -> 从 localStorage 读取 libtv:promptMentionEnabled
  -> 无值时默认 true
  -> PromptMentionToggle 在高级设置显示当前值
  -> 用户切换后写回同一个全局偏好
```

因此未来 clone 若要复刻，图片和视频面板应共享一个偏好来源。当前图片组件局部 `showAutoLink` 和视频组件局部 `autoLink` 是两种不同含义，不能继续都叫 AutoLink 状态。

### 4.2 候选池

当前 bundle 的候选池来自 connected/reference assets，并会：

- 展开素材名称、变体和 tags；
- 排除不可用名称、纯数字、停用词和重复项；
- 按 image/video 等媒体分组建立 ordinal targets；
- 合并名称 occurrence 与 ordinal reference occurrence；
- 在 Prompt 为空、候选池为空、光标不在 editor、IME composing 或功能 suspended 时退出。

它不是固定的全画布二元数组，也不是看到任意“咖啡”文本就直接把两张图片一起引用。

### 4.3 检测与竞态

检测以当前 editor text 和 selection 为输入，异步构造 name/ordinal occurrences。实现会中止过期检测，并在返回前再次检查：

- Prompt 是否仍是同一文本；
- 当前 cursor 是否仍在 editor；
- AutoLink 是否仍开启；
- editor 是否因其他 popover/dropdown 暂停；
- 用户是否正在 IME composition。

这组 guard 是中文输入和快速编辑下避免“旧建议写回新文本”的必要行为，不是可省略的优化。

### 4.4 Ghost suggestion

检测命中后，源站在 contenteditable 内注入带 `data-mention-suggest` 的 ghost spans。它们只表达推荐，不是正式 mention：

| 动作 | 结果 |
|---|---|
| 点击 active ghost | 接受该 suggestion |
| `Tab` | 接受 active suggestion |
| `Shift+Tab` | 接受当前全部 ghost suggestions |
| `Escape` | 拒绝并清理 ghost |
| 用户编辑或 blur | 拒绝/剥离 ghost，保留真实正文 |
| 其他 Prompt popover 打开 | suspend suggestion，避免键盘和浮层冲突 |

“点击 或 按Tab键插入”和“Shift Tab 插入全部”提示按 caret/batch 模式分别记忆，localStorage key 前缀为 `libtv:promptMentionTabTipSeen:`。

### 4.5 接受与连接

正式 commit 通过 option/reference identity 插入 mention badge。手动 canvas mention 选择还有一条重要分支：

```text
目标已连接
  -> 直接按 option 插入 mention

目标未连接
  -> 先尝试建立 node connection
  -> 成功后插入 mention
  -> 连接失败则返回 connectFailed，不伪造引用
```

文本 reference 可只建立连接；非文本 reference 找不到可插入 option 时会返回 connected-without-mention。由此可见，graph connection、reference list 和 Prompt mention 是相关但独立的三层状态。

## 5. Source / Clone 差异

| 维度 | 当前源站 | 当前 clone | 影响 |
|---|---|---|---|
| 入口 | 高级设置内 switch | 图片 footer 条件图标；视频 top “3 个匹配” pill + advanced switch | 信息层级和状态含义不一致 |
| 偏好 | `libtv:promptMentionEnabled` 全局本地偏好 | 图片/视频各自组件局部 state | 跨节点切换会分叉 |
| 候选 | connected/reference assets 的名称、tag、ordinal | 固定 `陈默`、`咖啡` 两项 | 不能反映 graph 和真实素材 |
| 建议 UI | contenteditable inline ghost | 独立 56px popover | 键盘、光标和文本位置语义丢失 |
| 接受 | click / Tab 单项，Shift+Tab 批量 | 单个“引用”按钮接受全部 | 用户无法逐项审核 |
| 正文写回 | 在 occurrence 位置插入结构化 badge | 在 Prompt 前拼接 `@陈默（图片 1）、@咖啡（图片 2）。` | 改变原文且 token 不可追踪 |
| 身份 | stable node ID + media type + ordinal projection | image URL + 固定显示名 | 重排/替换后容易失配 |
| 竞态 | abort、text/cursor recheck、IME guard、suspend | 无 | 快速输入时可能接受陈旧候选 |
| graph | 未连接时可先 connect，失败有结果分支 | 图片只更新组件局部 references | 画布关系和 Prompt 不一致 |

对应 clone 代码：

- [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx#L34)：固定候选；
- [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx#L93)：一次接受两项并前缀写回；
- [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx#L131)：独立确认 popover；
- [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx#L184)：仅在有 Prompt 且无 references 时显示 footer 图标；
- [`VideoGenerationPanel.tsx`](../../../src/components/VideoGenerationPanel.tsx#L136)：视频局部开关；
- [`VideoGenerationPanel.tsx`](../../../src/components/VideoGenerationPanel.tsx#L227)：无候选计算支持的固定“3 个匹配”入口。

## 6. 价值排序与待授权实施顺序

### P0：纠正状态和入口

1. 共享 AutoLink preference，而不是图片/视频各持一份局部布尔值。
2. 将 switch 放入现有高级设置展开区；删除没有 source 依据的图片 footer 入口和视频固定匹配数。
3. 在用户接受前保持 Prompt 字符内容不变。

### P0：建立 mention 数据合同

至少需要保存：

```ts
type PromptMention = {
  nodeId: string;
  mediaType: "image" | "video" | "audio";
  ordinal: number;
  start: number;
  end: number;
  sourceName: string;
};
```

这是后续实现建议，不是源站类型声明。`ordinal` 必须由当前有序 reference projection 得出，不能替代 `nodeId`。

### P1：候选、ghost 和键盘闭环

- 先从当前 node 的 graph-connected/reference assets 建池；
- 先实现名称 occurrence，再增加 tag/ordinal；
- ghost 与正式 badge 使用不同 DOM/data 标记；
- 支持 click、Tab、Shift+Tab、Escape；
- 接入 IME composition、selection 和 stale-result guard。

### P1：graph/reference/mention 一致性

- 接受未连接素材时，以一次可撤销 transaction 连接并插入；
- 连接失败不能留下 badge；
- 删除/重排 references 后重算 ordinal，但保留 stable node ID；
- 同一素材的重复 mentions 应共同投影到相同 ordinal。

### P2：提示、analytics 和低置信状态

在核心闭环稳定后，再复刻一次性 Tab 提示、接受/拒绝 analytics、候选空态和低置信解释。不要先做装饰 popover。

本轮没有授权编码，以上仅是实施队列。

## 7. 后续验证合同

获得编码授权后，最小回归矩阵应包括：

| 场景 | 必须成立 |
|---|---|
| 图片节点切换到视频节点 | AutoLink 开关值一致 |
| 高级设置收起/展开 | Panel 高度和 node center anchor 正确；无独立 page popover |
| Prompt 命中一个素材 | 仅出现 ghost；原始字符内容未被改写 |
| Prompt 命中多个素材 | Tab 只接受 active；Shift+Tab 批量接受 |
| `Escape` / blur / 普通编辑 | ghost 清理；正式 badge 和正文不丢失 |
| 中文 IME composition | composition 中不接受陈旧 suggestion |
| 同一素材出现两次 | 两个 badge 共享 node ID 和 ordinal |
| references 重排 | badge 显示 ordinal 更新，node ID 不变 |
| 未连接候选 | connect 与 mention 同一 transaction；失败不残留 badge |
| 其他 Prompt 菜单打开 | AutoLink suggestion 暂停，不抢 Tab/Escape |

## 8. 未决问题

- 本轮为避免编辑源站 Prompt，没有 live 触发 ghost suggestion，因此 ghost 的精确颜色、动画、tip anchor 和多行换行仍需专门空白项目取证。
- 当前 chunk 可证明候选池包含名称变体、tags 和 ordinal，但尚未把全部中文 stop-word/边界规则整理成可移植词法规格。
- 没有切换生产站 AutoLink 开关，因此只证明当前 checked 状态和静态持久化路径，不证明跨 tab 的实时同步策略。
- 没有接受新引用、创建连接或提交任务；graph mutation 的最终 API payload 仍属待验证项。

这些未知项不影响本轮核心修正：当前 clone 的固定候选确认 popover、全量接受和字符串前缀写回不是源站现行 AutoLink 交互。
