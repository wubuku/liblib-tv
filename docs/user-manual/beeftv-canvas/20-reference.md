# 参考：快捷键全表、路由与端点

> 适用角色：所有用户。快捷键均已实际核对实现代码；展示文案与实现不一致处以实现为准。

## 画布快捷键全表

| 快捷键 | 行为 |
|---|---|
| Ctrl/Cmd + `+`/`=` / `-`/`_`（含小键盘） | 步进缩放 ±10% |
| 滚轮 | 缩放画布 |
| 缩放滑杆 | 精确调整缩放比例 |
| Ctrl/Cmd + `0`（含小键盘） | 适应整个画布 |
| Ctrl/Cmd + `0` / `1` / `2` / `3` | 0/2 适应画布 · 1 恢复 100% · 3 适应选择（快捷键中心运行时口径，已逐条核对） |
| 触控板双指 / 中键拖动 / `Space` + 拖动 | 平移视图 |
| Ctrl/Cmd + S | 保存画布 |
| Ctrl/Cmd + F | 搜索节点 |
| Ctrl/Cmd + Shift + F | 进入**或退出**专注模式 |
| Alt + Shift + F | 整理画布（快捷键中心里的字样；**同一个动作在画布空白处右键菜单里叫「自适应整理画布」**） |
| `V` / `H` | 移动工具（空白左键拖即框选）/ 抓手工具 |
| 空白处左键拖动 | 框选多个节点 |
| `Shift` + 拖动 / `Ctrl/Cmd` + 拖动 | 框选并**追加**到当前选择 |
| `Shift` + 点击 / `Ctrl/Cmd` + 点击 | **追加**选择节点 |
| Alt + 点击 / 框选 | 从当前选择中**移除** |
| Ctrl/Cmd + A | 全选节点 |
| Alt + L | 批量连线（需 >1 选中） |
| ? | 快捷键中心 |
| Ctrl/Cmd + Z | 撤销 |
| Ctrl/Cmd + Shift + Z / Ctrl/Cmd + Y | 重做 |
| Ctrl/Cmd + C / V | 复制 / 粘贴节点（粘贴时会读系统剪贴板：节点标记文本→还原节点；否则系统图片优先） |
| `Delete` / `Backspace` | 删除（选中连线时优先删连线） |
| `Esc` | 取消选择 / 关浮层 / 退出专注模式 |
| 拖入媒体 | 导入媒体 |
| 节点上右键 → 「创建参数变体」 | 复制一份参数变体，快捷键 ⌘D（**不在快捷键中心**，只在右键菜单里） |

> **口径**：上表已与界面上的「**快捷键中心**」逐条核对——该中心共 **24 条、4 个分类**（常用 4 / 视图与导航 7 / 选择与连接 6 / 编辑与文件 7）。表中 ⌘D 一行来自节点右键菜单，不计入这 24 条，故表行数与条数不相等。
>
> 快捷键中心里还有几条是**鼠标/触控板操作**而非按键（滚轮、缩放滑杆、触控板双指、拖入媒体、空白拖动框选），它们同样收在中心里，上表已一并列出。

**保护条件**：文本编辑框内按键原样放行；节点工具条上的按键被忽略；`data-canvas-no-zoom` 控件上只放行复制/粘贴。

## 导演台快捷键

| 按键 | 动作 |
|---|---|
| `V` / `R` / `F` | 移动（translate）/ 旋转（rotate）/ 缩放（scale）模式（v1.6.x 起为主键位，兼容旧 `W`=移动、`E`=旋转） |
| `Delete` / `Backspace` | 删除选中的对象或灯光 |
| Ctrl/Cmd + `Z` / Ctrl/Cmd + `Shift` + `Z` / Ctrl/Cmd + `Y` | 撤销 / 重做 / 重做 |
| `H` | 显隐切换（注意：与画布 `H`=抓手语义不同） |
| `Esc` | 取消选择 |
| 空格 | 播放 / 暂停 |

> **导演台也遵守同一条保护规则**：焦点落在输入框、按钮、链接、下拉或任何 role 型控件（textbox/button/switch/tab/menuitem…）上时，按键**不会**被解析成导演台快捷键。所以「在重命名输入框里按空格没暂停」是正确行为，不是失灵。
>
> 带 `Alt` 的组合一律不抢，留给浏览器/系统；`Ctrl/Cmd+R` 也不会被当成「旋转」。

## 主要页面路由

| 路由 | 页面 |
|---|---|
| `/` | 首页（项目工作区入口） |
| `/create` | 新建创作——见 [10-tasks/create-workspace.md](10-tasks/create-workspace.md) |
| `/projects`、`/project` | 画布工作区（两个路径指向同一页） |
| `/projects/:projectId`、`/projects/:projectId/:view` | 项目画布与其子视图 |
| `/projects/:projectId/chapters/:chapterId` | 章节视图——**已注册但访问不到**（见下） |
| `/projects/:projectId/workflow/:unitId/:stage` | 工作流单元 / 阶段——**已注册但访问不到**（见下） |
| `/canvas`、`/canvas/:id` | 画布页与指定画布；**画布库列表页就是 `/canvas`** |
| `/assets` | 资产页 / 素材库——见 [10-tasks/asset-library.md](10-tasks/asset-library.md) |
| `/settings`（`?section=channels`，`?continue=1`） | **模型配置 / 个人渠道**——见 [10-tasks/model-channels.md](10-tasks/model-channels.md) |
| `/plugins`、`/plugins/eagle` | 插件中心与 Eagle 素材库（需开启 `pluginCenterEnabled` 特性） |
| `/test-voice-recording` | **语音录制的开发测试页**——它挂在生产路由里、**侧栏没有任何入口**，只能手敲网址进入。页面用途写在源码注释里：「验证输入行内联波形录制和 STT 转写闭环」 |

| `/dev/folders`、`/dev/director-repro` | **两个开发调试台**——文件夹样式预览台与导演台复现台。同样挂在生产路由里、**界面上没有任何入口**，只能手敲网址。比 `/test-voice-recording` 更冷的一层：**导演台复现台专门写了一段「隔离」逻辑**（源码注释：跳过工作区启动，*免得没有后端时打出真实 502 污染判据*），**但那段判断是 `import.meta.env.DEV` 包的，生产构建里会被摇树删除**——所以线上这两页**照样会去打后端**，没起后端时你看到的是连不上的半成品。 |

**已退场、访问会被重定向回首页的路由**：`/tasks`（任务中心）、`/skills`、`/skill`、`/skills/reference`——都随旧 Agent / 任务中心一起下线。旧链接不会 404，会静默跳回 `/`，所以「点进去发现回到了首页」是预期行为，不是故障。

这四条路由在源码里**只剩重定向**（`/tasks` 那条甚至还留着注释「任务页暂不开放，保留路由以避免旧链接进入半成品界面」），而对应的页面源码**一行都没删**，合计约 **2354 行**留在仓库里（任务中心 1221 行 + 技能页 1133 行）——**没有入口能到达它们，也不必担心误触**。

### 只能手敲、界面上没有入口的查询参数

BeefTV 会读一批 URL 查询参数，其中有几个**没有任何界面动作会产生它们**——只能手动改网址：

| 参数 | 位置 | 作用 | 备注 |
|---|---|---|---|
| `readonly=1` 或 `mode=readonly` | `/canvas/:id` | 进入只读模式（两种写法等价） | 见 [10-tasks/readonly-canvas.md](10-tasks/readonly-canvas.md) |
| `fixture=<10 种>`、`fixtureMedia`、`libtvChrome` | `/canvas/:id` | 注入演示画布数据 | **只读模式下全部不注入** |
| `agent=1` | `/canvas/:id` | 旧内置 Agent 的深链开关，**只被读取并原样转发**，旧 Agent 已下线 | 界面上**没有任何动作**会产出它 |
| `demo=conversation` | `/create` | 固定数据的模拟对话流，页面顶部会挂出「模拟对话流 · 固定数据演示，不会调用真实生成接口」横幅 | 不会产生真实生成与费用 |
| `stay=1` | `/canvas` | 新建画布后**留在画布库**，不进画布 | 源码注释写明是留给浏览器验收脚本的开关 |
| `baseUrl` / `apiKey` | 全站 | 首次启动时预填第一个渠道，随后被自动从地址栏抹掉 | 供外部启动器注入，见下 |

::: warning `baseUrl` / `apiKey` 会写进你的配置，慎用
`?baseUrl=…&apiKey=…` 打开站点时，**首个渠道的 Base URL 会被直接改成你给的值**，然后这几个参数才从地址栏消失（刷新也回不来）。这通常由桌面端启动器注入；**手工用它把密钥放进地址栏，等于把密钥留在浏览器历史记录里**。请优先到 [10-tasks/plugins-management.md](10-tasks/plugins-management.md) 提到的模型配置界面手动填写。
:::

::: tip 「只读不写」的参数不等于「进不去」
全库扫描下来，共有 **9** 个查询参数**只有读取、没有任何界面写入点**。但其中大半是**设计上就由外部提供**的深链——`baseUrl` 由外部启动器注入、`projectId` / `uuid` 来自你粘贴的 LibTV 链接、`readonly` 等属于手工调试入口。**「界面上没有按钮」不足以断言「这个功能不存在」**，逐个查过来源之后，真正属于「功能完整但无界面入口」的只有只读模式这一条。

这个 **9** 是有定义的、可复现的：**读**＝源码里出现 `searchParams.get("参数名")`；**写**＝**代码**里出现 `?参数名=` / `&参数名=` 或 `set("参数名")`，**注释不算**。它由 `scripts/verify-unreachable.py` 在每次构建时现场重数，**手册写的数与实测的数对不上就直接构建失败**（`agent` 与 `fixture` 这两个原先漏在判据外、只靠人工查证的参数，也是在这套口径下才补进来的）。
:::

::: warning 章节与工作流这两组路由进不去
`/projects/:projectId/chapters/:chapterId` 与 `/projects/:projectId/workflow/:unitId/:stage` **在路由表里注册着**，但它们和 `/projects/:projectId` 走同一个入口组件，而该组件在当前构建下**无条件把地址改写成 `/canvas/:projectId`**（本地工作区模式恒开启）。所以你手动敲这两条 URL 会被弹回画布页，**不会 404、也看不到章节或工作流界面**。

同理，「章节 / 故事大纲 / 分镜 / 角色卡」那套项目级功能在当前版本**没有可用的入口**，不只是路由别名的问题。画布库里能看到的只是画布与文件夹两层（见 [10-tasks/manage-canvases.md](10-tasks/manage-canvases.md)）。
:::

::: tip `/settings` 里没有 Agent 记忆
旧版说明「设置（含 Agent 记忆）」已不成立：设置页当前只有一个分区（`channels`），而整个分区还挂在 `customChannelsEnabled` 特性开关之后——开关关闭时分区列表为空，报错文案会变成「当前没有可用的系统模型，请联系管理员配置系统渠道」。Agent 记忆与技能相关说明见 [10-tasks/agent-memory-skills.md](10-tasks/agent-memory-skills.md)。
:::

## 主要 REST 端点（供排障参考）

本节已按上游 `origin/main` 的**生产路由注册**逐条机器核对（`backend/internal/bootstrap/runtime.go` 把路由挂在 `/api` 组下，下表省略该前缀）。核对方法与结果见「已下线端点」小节。

**仍然存在：**

| 端点 | 用途 |
|---|---|
| `GET /tasks` | 任务列表（分页/过滤） |
| `POST /tasks/:id/cancel` | 取消任务 |
| `POST /resources/uploads` | 大文件分片上传会话 |
| `GET /skills/:id/files` | 技能包文件列表 |
| `/api/plugins/eagle/*` | Eagle 资源代理（后端转发，浏览器不直连） |
| `POST /diagnostics/preview` · `POST /diagnostics/export` | 诊断包预览与导出（单次请求体上限 4MB）——反馈问题给官方时用它打包 |
| `GET /system/version` | 返回构建号与数据库 schema 版本，确认前后端是否同版本 |
| `GET /health/live` · `/health/ready` · `/health/startup` | 存活 / 就绪 / 启动状态；「画布卡在正在打开画布」先查 `/health/ready` |
| `/runtime/session/*`（127.0.0.1:17371） | 本地伴随进程会话（challenge/exchange），**不经过本后端** |

### 已下线端点（不要按这些路径排查）

| 端点 | 状态 |
|---|---|
| `POST /agent/runs` | **已下线**——旧内置 Agent 已从产品运行面退场 |
| `GET /agent/runs/:id/events` | 同上 |
| `POST /agent/runs/:id/messages` | 同上 |
| `POST /agent/runs/:id/interjections` | 同上 |
| `POST /agent/runs/:id/cancel` | 同上 |
| `POST /agent/memories/compact` | 同上 |
| ~~`/api/canvas-projects/:id/import/libtv` \| ~~`/api/canvas-projects/:id/import/tapnow`~~ | 跨产品导入，v1.6.x 已下线（v1.6.14 运行时路由核对无此组） |

> **Agent 相关端点为什么查不到**：后端**没有注册任何 `/agent/*` 路由**。上游有一份专门的测试文件 `backend/internal/handler/agent_retired_test.go`，它用**真实 HTTP 路由图**（而不是源码字符串）固化这条边界：旧 Agent 能力已下线，通用任务 API 也不能创建旧 Agent 任务。命中该边界时服务端的提示是「**Agent 能力已下线，请在画布中手动创建节点并生成**」。
>
> 也就是说，Agent 能力缺失**不是**你的部署问题，也不该去查网络或版本——直接在画布里手动建节点生成即可。相关机制说明见 [10-tasks/cloud-agent.md](10-tasks/cloud-agent.md)。

### v1.6.14 运行时核对新增（后端路由全量比对）

| 端点 | 用途 |
|---|---|
| `GET /api/tasks/:id/logs` | 任务日志（v1.6.14 任务详情实时刷新后端） |
| `POST /api/tasks/:id/query-provider` | 原任务查询（v1.6.16）：视频任务失败时「取回结果」所调用的接口，返回 `providerStatus` 与 `recovered` |
| `POST /api/tasks/:id/retry` | 任务重试 |
| `GET /api/tasks/:id/text-deltas·text-events·text-replay-complete` | 文本生成流式增量/事件/回放 |
| `POST /api/timeline/renders` · `POST /api/timeline/transcriptions` | 时间线渲染与**转写**（转写需本地 whisper.cpp，见下） |
| `GET/POST /api/depth-captures` | 深度捕捉产物存取 |
| `/api/creation-runs/*`（claim/execute/heartbeat/proposal-approve/canvas-commit 等） | Agent 创作运行后端契约（含付费提议审批；前端入口未挂载，API 先行） |

## 本地伴随进程

深度/线稿/姿态等本地推理由独立进程提供：强制 `http://127.0.0.1:17371` 精确回环地址；会话经挑战-签名交换建立；响应体上限 64KB（深度模块 32MB）。

## 本地转写服务（whisper.cpp）

时间线编辑器的「转写」面板把音视频素材转成字幕，走**本机 whisper.cpp**，语音不出本机：

| 项 | 值 |
|---|---|
| 后端配置项 | 环境变量 `CANVAS_WHISPER_BASE_URL`，指向 whisper.cpp 的 `/inference` 服务（如 `http://127.0.0.1:8082`） |
| 启动脚本 | `scripts/start-whisper-local.sh`（默认 base 模型、端口 8082；`WHISPER_MODEL` 换模型，`WHISPER_PORT` 换端口） |
| 依赖 | `whisper-server` 可执行文件（macOS：`brew install whisper-cpp`）与模型文件（先下载到 `.local/whisper-models/`） |
| 未配置时 | 任务在进入转写前明确失败：「本地转写服务未配置：请设置 CANVAS_WHISPER_BASE_URL」 |
| 产物 | 识别段落转成 `SrtEntry[]`，经 `rebuildSubtitleClips` **原子替换**字幕轨道快照 |

转写结果直接写入字幕轨道，可再编辑；识别不到可用字幕时提示「转写完成，但没有识别出可用字幕（语音内容为空？）」。字幕的编辑与高亮见 [10-tasks/subtitle-highlights.md](10-tasks/subtitle-highlights.md)。

## 桌面端更新（v1.6.13 起）

桌面客户端会**定期检查更新**，侧栏提供更新入口。官方文档描述的更新流程是：

1. 应用启动时检查一次更新，**显示当前版本**；
2. **用户点击后才会开始下载**——下载完成**不会自动退出**；
3. 只有用户**选择安装**后，应用才保存当前工作、退出并启动新版本；
4. **保存失败会留在当前应用中**（不会丢工作也不会半装）。

> 这些步骤取自 `docs/content/docs/backend/desktop-updater.mdx`；桌面端按钮的具体文案不在本仓库内（桌面壳独立分发），故此处只描述流程、不逐字引用按钮文字。
