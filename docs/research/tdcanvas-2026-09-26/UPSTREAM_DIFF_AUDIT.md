# TDCanvas ← basketikun/infinite-canvas 归属审计

> 目的：回答「TDCanvas 的画布机制哪些承自上游 `basketikun/infinite-canvas`、哪些是 TDCanvas 原创/改造」（REPORT.md §6 的未决问题）。
> 方法：浅克隆上游 `main` 至 /tmp（审计基准 `dab19adc0847e32e39b7fc8ff90cb392561fb826`，2026-09-23，**v0.19.0**——注意上游比 TDCanvas 的 v0.14.0 更新，两边是**同源分叉、双向演化**，非简单父子差异）；对关键文件做 `cmp`/`diff`/符号 grep。
> 证据等级：文件级 `cmp` IDENTICAL / diff 行数 / 符号在两仓的出现次数，均为可复核的机械事实；「继承/原创」判断据此得出。

## 1. 总体关系

- TDCanvas README 自述「基于 `basketikun/infinite-canvas` 二次开发」；上游约 7k star、官网 canvas.best、MIT。
- 顶层骨架同构：`web/ + canvas-agent/ + plugins/ + docker-compose + nginx.conf + render.yaml + vercel.json + SECURITY.md + skills-lock.json`。上游多出 `assets/`、`canvas-proxy/`（服务端代理，TDCanvas 已删）；TDCanvas 多出 `modules/`、`CLA.md`、`CONTRIBUTING.md`。
- `web/src` 顶层差异极小：TDCanvas 多 `integrations/`（comfyui-local）与 `splashscreen.ts`。
- 两仓**都在活跃演进**（上游 2026-09-23 仍在提交），因此「上游无 = TDCanvas 原创」的判断对 v0.19.0 时点成立，不排除上游后来也实现了同类机制。

## 2. 机制归属表（对照 PATTERN_CARDS TD-01..15）

| 机制（模式卡） | 归属 | 机械证据 |
|---|---|---|
| node-registry 注册表（TD-04） | **继承（逐字节相同）** | `cmp` IDENTICAL（61 行） |
| plugin-loader 插件加载（TD-12 基座） | **继承（逐字节相同）** | `cmp` IDENTICAL（170 行） |
| 小地图纯 div（TD-01 附属） | **继承（逐字节相同）** | `cmp` IDENTICAL（137 行） |
| canvas-agent 整个 Agent 通道（TD-11） | **继承（结构相同，小改）** | `canvas-agent/src` 目录 diff 仅上游多 `config.test.ts`；schemas 75 处 `canvas_` 工具；`canvas-agent-ops.ts` 仅差 15 行 |
| wheel=zoom 公式（TD-02） | **继承** | 上游 `infinite-canvas.tsx:91-92` 同为 `pow(1.1, delta/100)` |
| 项目文档含 chatSessions/viewport/backgroundMode（TD-10 部分） | **继承** | 上游 `use-canvas-store.ts:17-21` 同三字段；上游默认背景 `"lines"`（TDCanvas 迁移为 dots 的动因） |
| 几何式分组 groupId（TD-15） | **继承** | 上游有 `canvas-node-geometry.ts` 且含 `groupId`；上游 builtin-nodes 注册 Group |
| 主题系统 canvasThemes（SOURCE_ANALYSIS §2.8） | **继承** | 上游同路径 `web/src/lib/canvas-theme.ts:4` 同名导出 |
| i18n 双语 | **继承** | 上游有 `web/src/i18n/`（index+locales） |
| 图片快捷工具自定义（`image-quick-tools`） | **继承** | 两仓各 1 个文件引用同 key |
| 连线渲染贝塞尔+命中层（TD-01 附属） | **继承（小改）** | `canvas-connections.tsx` 仅差 42 行 |
| 画布 surface 文件 | **改造（改名+重写）** | 上游 `infinite-canvas.tsx` → TDCanvas `td-canvas-surface.tsx`（315 行新文件）；上游 Space=临时工具（`temporaryTool = ctrlKey \|\| isSpacePressed`，`infinite-canvas.tsx:114,206`），TDCanvas 改为禁用 Space |
| 对齐辅助线 + 网格吸附（TD-15） | **TDCanvas 原创** | 上游无 `canvas-alignment-guides.*`；`snapToGrid` 上游 0 文件 vs TDCanvas 6 |
| 氛围网格/视差/指针 focus 层（TD-14） | **TDCanvas 原创** | 上游 surface 与 globals.css 中 parallax/depth/focus 变量 0 命中 |
| 图片历史 imageHistory + pinned（TD-09 部分） | **TDCanvas 原创** | `imageHistory` 上游 0 文件 vs TDCanvas 13 |
| 批量堆叠 batchChildIds（TD-08） | **TDCanvas 原创** | 上游 0 vs 3 |
| providerTask 任务状态机（TD-07 壳） | **TDCanvas 原创** | 上游 0 vs 13（上游生成走 OpenAI 兼容 `image.ts/video.ts/audio.ts + local-proxy.ts + model-plugin.ts + prompt-source-runtime`，无任务轮询状态机） |
| objectReferences 无线引用（TD-06 部分） | **TDCanvas 原创** | 上游 0 vs 16；上游用 Group-作为资源集合 + `canvas-node-reference-bar.tsx`（`getGroupResourceNodes`）表达引用，该组件 TDCanvas 已删 |
| Aitudou 生成后端 | **TDCanvas 原创** | 上游无 `aitudou*.ts`（TDCanvas 1003 行） |
| Tauri 桌面壳 + media_cache + comfyui-local + modules/ | **TDCanvas 原创** | 上游无 `src-tauri`、无 `integrations/`、无 `modules/`；上游另有 `canvas-proxy/` 服务端组件（TDCanvas 移除，改 Rust 中继） |
| 上游独有：`canvas-selection-toolbar.tsx`（多选浮动工具条）、`canvas-node-reference-bar.tsx` | **上游独有（TDCanvas 移除）** | 文件仅存在于上游 |

## 3. 对本项目结论的影响

1. **归属修正**：REPORT.md/PATTERN_CARDS 中 TD-04/05/11/12/15 与主题系统、Group、i18n 应读作「infinite-canvas 生态机制（TDCanvas 继承）」；TD-07/08/09（任务状态机、批量堆叠、图片历史）、TD-02 的 Space 禁用与框选改造、TD-14 氛围层、对齐辅助线、连线/objects 双模式是 **TDCanvas 层的增量**。若引用本调研，请按此归属表述。
2. **上游本身值得独立调研**：infinite-canvas 的 `canvas-selection-toolbar`（多选浮动工具条）、`canvas-proxy`（服务端代理与 BYOK 渠道：chatgpt2api/grok2api/newapi）、Group-资源集合引用模型、prompt-source 的 OpenAI 兼容 provider 层，是与 TDCanvas 不同的另一组可迁移机制；上游 v0.19.0 比 TDCanvas 新，可能还有 TDCanvas 未曾有的新能力。是否立项为独立研究包（如 `infinite-canvas-2026-09-26/`）等待用户决定。
3. **审计时效**：本审计基准为上游 `dab19ad`（浅克隆 /tmp，非 submodule）；上游演进后需重跑（见 ITERATION_LOG Q1 停止条件已满足的部分）。

## 4. 逐文件语义分类（v4，`project.tsx` 3456 行 / `canvas-node.tsx` 955 行差异）

方法：`diff -U0` 全量 hunk + 关键词粗分类（比例仅供参考）+ 最大连续块人工判读。

**project.tsx** 分类比例（TD新增/上游删除行）：连接与端口 252、i18n 文案 215、Aitudou 管线 201（纯新增）、尺寸几何 179、生成通用 148、UI 弹窗 90、批量 60、无线引用 54（纯新增）、分组 50（删 37>增 13：简化上游 Group 逻辑）、媒体缓存 38、选择 46、对齐 19、图片历史 6。最大连续块判读：

| 块大小 | 位置（TD 行） | 内容 |
|---|---|---|
| 495 行 | ~1935-2407 | Aitudou 原生生成配置/运行管线（`applyNodeConfigPatch` 重写区） |
| 256 行 | ~3984+ | 尾部辅助：结果写回、输出节点、phase 映射 |
| 253 行 | ~2651 | 上传/替换素材与参考素材流重写 |
| 158 行 | ~3160 | 文本流式生成（`streamed` 增量回写） |
| 115/107 行 | ~1869/1365 | 批量展开重写；`finishNodeDrag` 集成对齐吸附 |
| 105 行 | ~899 | `disconnectNodeReference` → objectReferences 体系替换上游连线引用 |

**canvas-node.tsx**：批量 143、主题 85、i18n 48、连接端口 43、尺寸几何 40、图片历史 20（纯新增）、分组 19、历史 11。最大块：ErrorContent/生成中遮罩重构 228 行；批量 UI（计数按钮/堆叠帧/空图态）共约 425 行；`ImageHistoryControl` 集成 64 行（纯新增）；透明背景条件重构 35 行。

> 方法局限：关键词分类对「其他」（project.tsx 2014 行）分辨率不足；上表最大块为人工判读，未逐行归类。

## 5. 上游独有机制深度分析（v5 深化；行号对齐上游基准 `dab19ad`）

### 5.1 canvas-selection-toolbar：多选浮动工具条与分组操作族

**组件本体**（`web/src/components/canvas/canvas-selection-toolbar.tsx`，85 行，全文精读）：
- Props：`nodes/viewport/showToolbar/canGroup/canUngroup/onGroup/onUngroup`（`:13-29`）；选中 <2 节点直接返回 null（`:32`）。
- 双重视觉：① 选中包围盒轮廓——`nodeBounds + SELECTION_PAD(14)` 换算屏幕坐标，SVG 圆角矩形（rx=16、虚线 `7 5`、`theme.canvas.selectionFill/Stroke`、z-[65]）（`:11, 34-58`）；② 浮动工具条——白色胶囊（h-12、rounded-18、投影），水平居中于包围盒、`-translate-y-full` 悬于其上 8px（z-[70]），`onMouseDown/PointerDown` stopPropagation 防拖穿（`:59-68`）。
- **按钮全集只有 2 个**：Group（lucide `Group` 图标，`canGroup` 时）与 Ungroup（`Ungroup` 图标，`canUngroup` 时）；各带 antd Tooltip（top、0.2s 延迟、白底自定义样式）（`:66-67`）；`SelectionAction` 按钮结构（icon+label+hover 灰底）（`:74-85`）。没有对齐/分布/删除等多选操作——上游多选工具条只做分组。

**接线与入口**（`web/src/pages/canvas/project.tsx`）：
- `canGroupSelection/canUngroupSelection` 由 `canGroupSelectedNodes/canUngroupSelectedNodes` 计算（`:735-736`）；组件渲染于 `:3282-3290`，`showToolbar={!isNodeDragging && !isNodeResizing}`（拖拽/缩放中隐藏按钮、保留包围盒轮廓）（`:3284`）；**右键菜单**在 `contextMenu.type==="node"` 时暴露同两个动作（`:3325-3326`）；**键盘** Cmd/Ctrl+G 分组、+Shift 解组（含 canX 守卫 + preventDefault，`:1593-1606`）。

**分组操作族**（`web/src/lib/canvas/canvas-node-geometry.ts`）：
- `collectGroupMemberNodes`：选中节点 + 选中组的成员（剔除组壳本身）（`:58`）；`getGroupWrapRect`：成员包围盒 + 双侧/底部 GROUP_WRAP_PADDING、**顶部更大 padding**（供标题）（`:63-71`）。
- 守卫：`canGroupSelectedNodes` 需 ≥2 成员且不全属同一组（`:73-78`）；`canUngroupSelectedNodes` 需选中含组壳或组成员（`:80-82`）；`emptyGroupIds` 回收空组（`:87-91`）。
- `applyGroupSelection`：给成员写 `groupId` → **扁平化被选中的组壳** → 组节点插入到首个成员的下标处 → 连同空组一起清理连接与组壳 → 返回选中组壳（`:96-106`）；`applyUngroupSelection`：清除选中组壳与成员的 groupId → 清理空壳 → 选中还原为释放的成员（`:108-125`）。
- **TDCanvas 对比**：组件文件删除（grep 0 命中）、Cmd+G 删除（`key==="g"` 0 命中）；分组创建方式从「选中→自动包裹矩形」改为「先建空 Group 节点→拖入成员（中心点包含判定）」，解组能力整体移除，仅保留拖入/拖出的 `findGroupDropTarget/snapNodesIntoGroup/findContainingGroupId`。

### 5.2 canvas-proxy：本地 CORS 转发协议（`canvas-proxy/index.js`，132 行，全文精读）

- **部署形态**：零依赖 Node `http` 服务的 npm bin（`npx @basketikun/canvas-proxy@latest`）；默认 `127.0.0.1:23210`，`--port/--host` 或 `PORT/HOST` 覆盖（`:120-132`）。
- **目标解析 `readTarget`**（`:35-47`）：取首字符后的整个路径作为目标 URL；`decodeURI` 还原浏览器对路径的转义但保留刻意的 `encodeURIComponent`；正则 `^(https?:)\/*/` 修复被合并的 `//`；必须通过 `^https?:\/\/[^/]` 校验否则视为版本查询。
- **头策略**：请求侧剥离逐跳头与代理特征头 host/connection/content-length/accept-encoding/origin/referer/sec-fetch-*（`:17, 49-56`）；响应侧剥离框架头 content-encoding/content-length/transfer-encoding/connection/keep-alive 与既有 access-control-*（`:19, 58-65`）；注入宽松 CORS `*`（max-age 86400，`:8-14`）；OPTIONS 直接 204（`:94-98`）。
- **转发行为**：非 GET/HEAD 先缓冲 body（`:26-33, 77`）；`fetch(target, {redirect:"follow"})`（`:78`）；响应体经 `Readable.fromWeb` + pipe **逐块透传**（SSE 文本生成不缓冲），客户端断开即 destroy（`:85-89`）；状态行到达即打一行转发日志（时间/方法/目标/状态码/耗时，`:72-74, 79, 107`）；失败返回 502 JSON，若头已发出则 destroy（`:108-116`）；根路径返回 `{app, proxy, version, usage}` 版本 JSON（`:100-103`）。
- **客户端挂接**：`withLocalProxy(url)`（`web/src/stores/use-config-store.ts:490`）在配置启用本地代理时包裹绝对 URL；model-plugin 的 `pluginUrl` 对 `^https?:` 路径强制走它（`model-plugin.ts:43-45`）；视频 blob 拉取同样包裹（`video.ts:199, 267`）。
- **TDCanvas 替代**：删除该组件；桌面端以 Tauri http 插件（`platformFetch`）直连 + `/tdtv-api` 开发代理 + Rust `media_cache` 下载中继（含 SSRF 校验）组合替代。

### 5.3 Group 资源集合：`getGroupResourceNodes` 数据流（`web/src/lib/canvas/canvas-resource-references.ts`，147 行，全文精读）

- **资源资格** `resourceKind`（`:140-147`）：Image/Video/Audio 需 `metadata.content`、Text 需 `content||prompt`；插件节点经 `definition.resource(node).kind` 声明。
- **组=资源包**：`getGroupResourceNodes(groupId, nodes)` = `metadata.groupId===groupId` 且有资源的成员（`:96-98`）；`hasGroupResources`（`:83-85`）→ `isCanvasReferenceNode`（`:87-89`）——**Group 节点只有持有资源成员时才算"可引用节点"**，才能被连线当作上游。
- **展平**：`expandGroupResourceNodes` 把输入列表中的 Group 替换为其资源成员并按 id 去重（`:91-94`）。
- **解析管线** `getMentionResourceNodes`（`:53-60`）：① 若节点连向 Config 节点 → 改用 Config 的输入（剔除自身）（`getConnectedConfigInputNodes :77-81`）；② 否则用自身入边的上游（`getContextInputNodes :70-75`，经 isCanvasReferenceNode 过滤）；③ 都没有则用自身；①② 每层都做组展平。`getGenerationResourceNodes`（`:62-68`）同管线但不展平（原始输入）。
- **标签与序列化**：`labelResourceNodes` 按 image/video/audio/text 各自计数生成「图片 N」类标签（`labelForKind :123-128`，图片用 `imageReferenceLabel`）；`resolveCanvasReferenceImages`（`:29-51`）把图片引用解析为 `{id:"canvas:<nodeId>", dataUrl, width, height, ...}` 供生成 payload。
- **TDCanvas 对比**：Config 路由保留（TD `canvas-resource-references.ts:72, 86, 110` 的 `getConnectedConfigResourceInputs`）；**组展平删除**（TD 中 `getGroupResourceNodes/expandGroupResourceNodes` 0 命中），引用打包职责由 TD 原创的 `objectReferences`（16 个文件）承担；TD 的 Group 恢复为纯视觉容器（无 port、禁与组建连）。

### 5.4 model-plugin：用户自建模型脚本层（`web/src/services/api/model-plugin.ts`，993 行）

- **定位**：把「任意 OpenAI/Gemini 兼容模型」以**用户可编辑的 JS 脚本**接入四种能力（image/video/audio/text）；消费方为 `image.ts/video.ts/audio.ts` 生成服务与 `components/layout/model-script-editor.tsx` 脚本编辑器。
- **执行模型**（`runModelPlugin :113-164`）：`new Function` 注入 17 个位置参数 + `"use strict"` 异步 IIFE 包裹用户脚本（`:117-135`）——**主线程执行、无沙箱，apiKey 直接进入脚本作用域**；AbortError/axios 取消透传，其余错误包装为 i18n 消息（`:136-145`）。
- **注入运行时**：`http {url,post,get}`（axios 实现，支持 json/blob/text/arraybuffer responseType 与 FormData，`:8-18, 50-77`）；绝对 URL 经 `withLocalProxy` 强制走本地代理（`:43-45`）；`request` 通用 axios；`poll {intervalMs,timeoutMs}` 轮询助手（`:20`）；`sleep/signal/onDelta`（流式文本回调）。
- **变量文档** `getPluginVariables`（`:166-190`）：17 个变量按能力 scoping（如 `reasoningEffort/onDelta/messages` 仅 text，`videos/audios` 仅 video）。
- **模板库** `getPluginTemplates`（`:224-975`）：**8 个模板 = 4 能力 × {OpenAI, Gemini}**（`:230, :325, :439, :560, :722, :779, :850, :907`）；OpenAI 图像模板结构：JSDoc `@returns {Promise<string[]>}` → `request({method:"post",...})` → 遍历 `data.data[]` 取 url；i2i 分支把参考图转 FormData（`image[]` 字段，多图/单图字段名切换）（`:230-330` 区域）。`normalizePluginImages`（`:977`）归一化返回值。
- **TDCanvas 对比**：整层被移除，以固定 Aitudou 后端替代（`aitudou.ts` 1003 行 + 静态 `AITUDOU_MODEL_PROFILES` 目录）；TD 失去了 BYOK 脚本扩展能力，换来统一的任务状态机与计费守护。

## 6. 上游其余机制补遗（v7；行号对齐上游基准 `dab19ad`）

> 本章补齐 §2 归属表未单列的三个上游机制。归属标注：prompt-source 与 local-proxy 为**两仓同源的继承机制**（非上游独有），selection/tool 体系为**上游形态（TDCanvas 重写）**。

### 6.1 prompt-source 运行时（继承，两仓同源）

- **JSON 约定**（`web/src/services/api/prompt-source-runtime.ts`，119 行）：`RawPrompt` 18 字段，含生成提示 `imageMode/imageModel/imageSize/imageCount`（`:4-18`）；`runPromptSource`（`:31-50`）：URL 必填 → `fetch(no-store)` → `parseJsonSource` 要求**根为数组**，builtIn 源为空即报错；`normalizeItems`（`:52-119`）：`title+prompt` 必填否则丢弃，id 缺省 `${source.id}-${leftPad(index+1)}`，按 id 去重。
- **服务层**（`web/src/services/api/prompts.ts`）：`Prompt = RawPrompt & {sourceId,...}`（`:8`）；`fetchPrompts` 关键字/tag/分类/分页（`:139`）；`refreshSource/refreshAllSources/refreshDueSources`（`:162-185`）与状态查询（`:187`）；每源 localforage 缓存 TTL 1h（TDCanvas 侧同源实现，`prompts.ts:48-49` 已核）。
- **归属证据**：TDCanvas 保留同名机制（`use-prompt-source-store`、`prompt-source-presets`、`prompts.ts`），差异仅在 TDCanvas 的 `DEFAULT_PROMPT_SOURCES=[]` 无内置预设；上游挂接 model-plugin 的 imageMode/imageModel 提示与外部源 CORS 场景（见 §6.2）。

### 6.2 local-proxy 挂接（继承，两仓同源；上游深度更高）

- **连通性探测**（`web/src/services/api/local-proxy.ts`，12 行）：`testLocalProxy` 请求代理根路径，读取其身份 JSON（`{proxy, version}`，即 canvas-proxy `:100-103` 的版本响应）作为可达性校验（`:4-11`）。
- **URL 包装**（`web/src/stores/use-config-store.ts`）：`normalizeLocalProxyUrl`（trim、去尾斜杠、缺省补 `http://`，`:483-487`）；`withLocalProxy`（`:490-496`）——仅当 `proxyEnabled` 且目标为 `^https?://` 时前缀代理地址，且 `url.startsWith(base)` 时防双重包装；**`buildApiUrl`（`:474-479`）对所有 OpenAI 兼容调用先补 `/v1` 再过 withLocalProxy**——即启用代理后全部模型流量走本地转发。
- **消费点**：model-plugin 绝对路径 `pluginUrl`（`model-plugin.ts:43-45`）、视频 blob 拉取（`video.ts:199, 267`）以及一切 `buildApiUrl` 调用。
- **TDCanvas 形态**：机制保留但角色弱化——桌面端 Tauri http 插件绕过 CORS 使代理非必需，`/tdtv-api` 仅服务 Web 开发态；proxy 配置面收窄。

### 6.3 selection/tool 体系其余部分（上游形态，TDCanvas 重写）

- **显式工具模式**：`InfiniteCanvas` props 声明 `tool: "select" | "pan"`（`infinite-canvas.tsx:11`），事件回调全部注入（onCanvasMouseDown/Deselect/DoubleClick/ContextMenu/Drop，`:12-17`）——surface 是纯表现层。
- **临时工具反转**：`temporaryTool = event.ctrlKey || isSpacePressed`，`activeTool = temporaryTool ? (tool==="select" ? "pan" : "select") : tool`（`:114-115` 渲染分支、`:206-207` 手势分支）——**按住 Space 或 Ctrl 把当前工具反转**（select 态下 Space+拖=平移；pan 态下 Ctrl+拖=选择），与 TDCanvas「Space 完全禁用 + ctrl 固定框选」的硬编码语义不同。
- **按键状态机**：Space/Control 的 keydown/keyup 维护 `isSpacePressed/isControlPressed`，带 input/textarea/contenteditable 守卫与 window blur 复位（`:52-74`）。
- **TDCanvas 重写对照**：`td-canvas-surface.tsx` 移除 `tool` prop 与反转逻辑，手势语义固定（wheel=zoom、空白左键=平移、ctrl+空白=框选、Space 只 preventDefault，见 SOURCE_ANALYSIS §1.2）；上游的 select/pan 双模式 UI（工具切换器）随之消失。

## 7. 基线后增量：TDCanvas `16b3127..d05cf612`（v20，2026-09-26 探测并落档）

> 维护态探测发现 TDCanvas upstream 已前移至 `d05cf612`（2026-09-25，Merge PR #2），基线后 3 个提交、51 文件、+1392/-150。以下为增量调研结论（行号对齐 `upstream/main` 树）。包内其余引用仍对齐锁定基线 `16b3127`，不受影响。

### 7.1 c7a0364 preserve canvas inputs and workflow run history（2026-09-15）

- **运行历史持久化（Rust）**：`run_result_path(directory, filename, prompt_id, item_index)` 为每次运行的每个输出按 `prompt_id + item_index` 生成独立结果文件（video 走专门分支），运行结果不再互相覆盖（`tauri-plugin/src/lib.rs`）。
- **结果节点绑定（web）**：`result-nodes.ts` 新增 `ComfyResultBinding {sourceNodeId, workflowId, outputId, resourceType, itemIndex}` 与 `createComfyResultNodes`——按工作流输出口逐一生成结果节点并按 `fromPortId` 连线，携带 `promptId/itemIndexes`。
- **复制泛化**：新文件 `canvas-node-duplication.ts` 把复制抽为纯函数并返回 `idMap`，`remapDuplicatedMetadata` 经 idMap 重映射 `batchChildIds`（含测试）——批量堆叠模型（TD-08）从此在复制/粘贴路径存活。
- **右键菜单新增「清除输入」**（Unplug 图标，`canClearInputs/onClearInputs`）。
- **工程过程**：引入 openspec 目录（specs/changes/tasks），变更走提案-规范-任务流。

### 7.2 7e2142e restore ComfyUI combo dropdowns（2026-09-16）

- `workflow-inspector.ts` 新增 `inputEnumValues(spec)`：此前仅在 `spec[0]` 为数组时判定枚举；现在同时解析 `COMBO` 字符串型声明的 `spec[1].options`——修复工作流节点 combo 下拉丢失（`inferInputValueType` 的 enum 判定同步改走该函数），新增 68 行测试。

### 7.3 422dff6 share ComfyUI queue across canvas tabs（2026-09-16）

- **Rust**：新增 `attach_environment` 命令（含权限清单），第二标签页可挂接运行中环境；读取 `/queue` 并以 `cancel_action` 区分 `queue_pending/queue_running` 决定中断动作；重排队走 `POST /queue`（`tauri-plugin/src/lib.rs` +155）。
- **Web**：`canvas-workspace-tabs-model.ts` 增加每 tab 挂接状态（+10），`canvas-workspace-tabs.tsx` 挂接 UI（+63）；`web/src-tauri/src/lib.rs` 注册命令（+19）。

### 7.4 对包内结论的影响

1. **TD-08 批量堆叠**：上游已在复制路径补 idMap 重映射——PATTERN_CARDS TD-08 卡已加演化注记；ADOPTION #5 的评估基础不变。
2. **ADOPTION #19（comfyui 方法借鉴）**：队列跨 tab 共享 + 运行历史持久化使该方法借鉴的价值上调（多标签/多会话场景的队列编排与结果溯源有现成范式）。
3. **SOURCE_ANALYSIS §6.3**：comfyui-local 机制描述仍成立（基线态）；上述三点为基线后增量，若重定基线至 `d05cf612` 需增补。
4. **无需改写包内既有 file:line 引用**：全部引用对齐锁定基线 `16b3127`，本地工作副本未动。

