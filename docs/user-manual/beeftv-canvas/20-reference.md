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
| Alt + Shift + F | 自动整理画布（快捷键中心里叫「整理画布」） |
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

> **口径**：上表已与「画布快捷键中心」逐条核对——该中心共 **24 条、4 个分类**（常用 4 / 视图与导航 7 / 选择与连接 6 / 编辑与文件 7）。表中 ⌘D 一行来自节点右键菜单，不计入这 24 条，故表行数与条数不相等。
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
| `/create` | 新建创作 |
| `/projects`、`/project` | 画布工作区（两个路径指向同一页） |
| `/projects/:projectId`、`/projects/:projectId/:view` | 项目画布与其子视图 |
| `/canvas`、`/canvas/:id` | 画布页与指定画布 |
| `/assets` | 资产页 |
| `/settings`（`?section=channels`） | **模型配置 / 个人渠道**——配置模型服务与个人工作流 |
| `/plugins`、`/plugins/eagle` | 插件中心与 Eagle 素材库（需开启 `pluginCenterEnabled` 特性） |

**已退场、访问会被重定向回首页的路由**：`/tasks`（任务中心）、`/skills`、`/skill`、`/skills/reference`——都随旧 Agent / 任务中心一起下线。旧链接不会 404，会静默跳回 `/`，所以「点进去发现回到了首页」是预期行为，不是故障。

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
| ~~`/api/canvas-projects/:id/import/libtv|tapnow`~~ | 跨产品导入，v1.6.x 已下线（v1.6.14 运行时路由核对无此组） |

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
