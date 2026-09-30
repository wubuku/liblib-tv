# 参考：快捷键全表、路由与端点

> 适用角色：所有用户。快捷键均已实际核对实现代码；展示文案与实现不一致处以实现为准。

## 画布快捷键全表

| 快捷键 | 行为 |
|---|---|
| Ctrl/Cmd + `+`/`=` / `-`/`_`（含小键盘） | 步进缩放 ±10% |
| Ctrl/Cmd + `0`（含小键盘） | 适应整个画布 |
| Ctrl/Cmd + `0` / `1` / `2` / `3` | 0/2 适应画布 · 1 恢复 100% · 3 适应选择（快捷键中心运行时口径，已逐条核对） |
| Ctrl/Cmd + S | 保存画布 |
| Ctrl/Cmd + F | 搜索节点 |
| Ctrl/Cmd + Shift + F | 进入专注模式 |
| Alt + Shift + F | 自动整理画布 |
| Alt + L | 批量连线（需 >1 选中） |
| ? | 快捷键中心 |
| Ctrl/Cmd + Z | 撤销 |
| Ctrl/Cmd + Shift + Z / Y | 重做 |
| Ctrl/Cmd + A | 全选节点 |
| Ctrl/Cmd + C / V | 复制 / 粘贴节点 |
| Ctrl/Cmd + D | 创建参数变体 |
| Delete / Backspace | 删除（选中连线时优先删连线） |
| Esc | 取消选择 / 关浮层 / 退出专注模式 |
| V / H | 移动工具（空白左键拖即框选）/ 抓手工具 |
| Space + 拖 | 平移 |
| 粘贴系统剪贴板 | 节点标记文本→还原节点；否则系统图片优先 |
| Alt + 点击 / 框选 | 从当前选择中移除 |
| 缩放滑杆 | 精确调整缩放比例 |

> 上表与「画布快捷键中心」运行时面板逐条核对过（共 24 条·5 分类：常用 4/视图与导航 7/选择与连接 6/编辑与文件 7）。

**保护条件**：文本编辑框内按键原样放行；节点工具条上的按键被忽略；`data-canvas-no-zoom` 控件上只放行复制/粘贴。

## 导演台快捷键

| 按键 | 动作 |
|---|---|
| V / R / F | 移动（translate）/ 旋转（rotate）/ 缩放（scale）模式（v1.6.x 起为主键位，兼容旧 W/E） |
| Delete | 删除选中 |
| Ctrl/Cmd+Z / Shift+Z | 撤销 / 重做 |
| H | 显隐切换（注意：与画布 H=抓手语义不同） |
| Esc | 取消选择 |
| 空格 | 播放/暂停 |

## 主要页面路由

| 路由 | 页面 |
|---|---|
| `/`（项目工作区） | 画布主工作区（项目列表与画布） |
| `/settings` | 设置（含 Agent 记忆） |

## 主要 REST 端点（供排障参考）

| 端点 | 用途 |
|---|---|
| `GET /tasks` | 任务列表（分页/过滤） |
| `POST /tasks/:id/cancel` | 取消任务 |
| `POST /agent/runs` | 创建 Agent 运行 |
| `GET /agent/runs/:id/events` | Agent SSE 事件流 |
| `POST /agent/runs/:id/messages` | 多轮续聊 |
| `POST /agent/runs/:id/interjections` | 运行中插话（下一步生效） |
| `POST /agent/runs/:id/cancel` | 取消运行 |
| `POST /resources/uploads` | 大文件分片上传会话 |
| `POST /agent/memories/compact` | 记忆压缩 |
| `GET /skills/:id/files` | 技能包文件列表 |
| ~~`/api/canvas-projects/:id/import/libtv|tapnow`~~ | 跨产品导入（**v1.6.x 已下线**；v1.6.14 运行时路由核对无此组） |
| `/api/plugins/eagle/*` | Eagle 资源代理（后端转发） |
| `/runtime/session/*`（127.0.0.1:17371） | 本地伴随进程会话（challenge/exchange） |

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

桌面客户端会**定期检查更新**；侧栏提供更新入口，支持**一键下载并安装**：点击「保存并安装」后系统先保存当前工作（仍有内容在保存时会拒绝更新并提示「仍有内容正在保存」），下载完成后安装、应用自动关闭再打开。下载就绪时侧栏显示「下载完成，可以安装」。
