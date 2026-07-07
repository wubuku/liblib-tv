# FrameOS 画布页 — 行为清单

> 复刻自 `frameos.cn/#/canvas/...`。下方列出**已实现**的交互行为和**缺失/简化**的部分（明确标注）。
> 关于"为什么有些面板我没做"详见 [`IMPLEMENTATION.md` §7](./IMPLEMENTATION.md#7-与原站-frameos-的差异明确承认的)。

## 全局交互

| 元素 | 触发 | 结果 |
|---|---|---|
| AppHeader (logo) | hover | 鼠标变 pointer（**无**点击行为） |
| AppHeader (下载桌面端) | click | console.log（mock） |
| AppHeader (金币/积分) | hover/click | 静态显示（无展开） |
| TopNavBar "FrameOS" 链接 | click | 跳转到 `/frameos/canvas/demo`（**liblib-tv 主页** 添加的入口） |
| HistoryDock (撤销/重做) | click | 接入 store 的 history stack；按钮在无可撤销时 disabled |
| CanvasMapDock (画布小地图钉) | click toggle | minimap 显隐（**简化为** `showMinimap` flag） |
| CanvasMapDock (缩小/放大) | click | XYFlow `zoomIn/zoomOut({duration:200})` + 更新 `zoomPercent` |
| CanvasMapDock (适应画布) | click | XYFlow `fitView({duration:200, padding:0.1})` + `zoomPercent=100` |
| CanvasMapDock (一键整理) | click | `runOrganize('grid')` 实际重排节点 |
| CanvasMapDock (选择整理方式下拉) | click | 弹出 3 选项菜单（按连线横向/纵向/网格） |
| DebugToggle (右下角) | click | 切换 `isDebugMode`（默认 false） |
| 全屏编辑遮罩 (PromptBar 全屏时) | click | 退出全屏 |

## 顶部 / 左侧 / 左下 UI

| 元素 | 触发 | 结果 |
|---|---|---|
| Breadcrumb "默认作品" | click | 弹出 4 个项目下拉（mock 数据） + 新建项目 |
| Breadcrumb "咖啡馆对峙" | click | 弹出当前项目下场景下拉 + 新建场景 |
| Breadcrumb "画布 1" | click | 弹出画布下拉 + 新建画布 |
| ToolRail "添加节点" | click | 弹出 3 种节点类型菜单（文本/图片/视频），点击后新建并自动选中 |
| ToolRail "从素材库选择" | click | console.log（mock） |
| ToolRail "本地上传" | click | console.log（mock） |
| ToolRail "帮助" | click | 打开 `FrameosHelpPanel` |

## 节点交互

| 节点 | 触发 | 状态 |
|---|---|---|
| 任意节点 | hover | 右下角 resize-handle 渐显（视频节点除外）；图片节点 hover 蒙层 + 缩放 1.02 + 预览/编辑按钮 |
| 任意节点 | click | selected 状态：蓝色边框 + 4px 光晕 + 左右 handle 显现（14×14 白色圆 + 蓝边） |
| 任意节点 | drag | 自由拖动（XYFlow 内建） + **floating-toolbar 和 PromptBar 用 `transition: left 0.15s` 平滑跟随** |
| 任意节点 | drag end | 位置写回 store（不入 history stack） |
| 文本节点 | 输入 | contenteditable 实时写 `promptValue` |
| 视频节点 | click 中心播放按钮 | 切换 `isPlaying` → 内嵌 `<video>` 元素，错误自动 fallback 到封面 |
| 视频节点 | hover | 中心播放按钮 hover scale 1.1 + 显示时长徽章 "00:05" |
| 视频/图片节点 | click 替换按钮 (右上角) | 触发 `<input type="file">` 文件选择（无后端） |
| 任意节点 | Delete / Backspace 键 | 从 store 删除该节点 + 关联的边 |

## 选中节点时的浮动面板（**跟随节点 + 画布缩放**）

> 实现原理：所有面板用 `position: fixed` + `useViewport()` 拿 pan/zoom 实时计算视口坐标。

| 面板 | 出现条件 | 位置 | 内容 |
|---|---|---|---|
| `FrameosNodeToolbar` | 节点选中 | 节点正上方 50px 处，居中 | 下载/收藏 + 按节点类型的工具（图片：超清/720/改图/宫格切分；视频：超清/改图；文本：超清）+ 关闭 |
| `FrameosPromptBar` | 节点选中 | 节点正下方 12px 处，居中 | 节点缩略图 + contenteditable 输入框 + 模型/1K/16:9/更多参数下拉 + 60 积分 + 提交按钮 |
| `FrameosNodeEditPanel` | **调试模式** + 节点选中 | 节点右侧 12px（或左侧如右边空间不够） | 节点 ID / X,Y 坐标 / 按类型的参数表单 / 快捷操作（复制/锁定/删除） |

边界碰撞：所有面板有 `window.innerWidth/Height` 检查，节点靠右时面板左偏，靠下时面板上移。

## 边交互

| 元素 | 触发 | 状态 |
|---|---|---|
| 边 | hover | 变粗（4px）+ flowing pulse 1.6s linear infinite + 剪刀删除按钮出现 |
| 边 | click 剪刀 | 从 store 删除该边（`removeEdge`） |
| 拖 handle 创建连接 | drag from handle | 临时蓝色虚线 + handle 蓝色光晕（来自 CSS） |

## 键盘快捷键

| 键 | 行为 |
|---|---|
| `Esc` | 多级退出：帮助 → 全屏 Prompt → 添加节点菜单 → 整理菜单 → 取消选中 |
| `Delete` / `Backspace` | 删除选中节点（输入框内不触发） |
| `Cmd/Ctrl + Z` | 撤销 |
| `Cmd/Ctrl + Shift + Z` | 重做 |
| `Cmd/Ctrl + D` | 复制选中节点（位置偏移 +40,+40） |
| `?` 或 `Shift + /` | 打开/关闭 `FrameosHelpPanel` |
| `+` / `=` | 放大 |
| `-` / `_` | 缩小 |
| `0` | 适应画布 |

## 视觉态

| 元素 | 默认 | hover | 选中 |
|---|---|---|---|
| node-card | shadow 0 2px 8px rgba(0,0,0,0.2) | (无) | shadow 0 0 0 4px rgba(59,130,246,0.18) + border 蓝 |
| node-floating-title | color #A3A3A3 | — | — |
| breadcrumb-switcher | bg transparent | bg rgba(255,255,255,0.05) | bg rgba(59,130,246,0.16) + 蓝边 |
| rail-btn | bg #1A1A1A | bg #2A2A2A + scale 1.05 | rail-btn--primary 蓝渐变 |
| rail-btn--primary | 蓝渐变 + 蓝 glow | 蓝渐变 + scale 1.05 | 蓝渐变 + active 状态（蓝边） |
| dock-btn | color #C2C2C2, bg transparent | bg rgba(255,255,255,0.05) | color #60A5FA, bg rgba(59,130,246,0.16) |
| prompt-bar / floating-toolbar | — | (无) | — |

## 动画

- **flowing pulse on edge**: 1.6s linear infinite, 3 段错相位, dashoffset 100→0
- **节点 hover resize-handle**: opacity 0→1, 0.15s
- **节点 selected shadow**: box-shadow 0.15s 过渡
- **节点 pop-in (首次出现)**: 0.2s scale 0.92→1
- **floating-toolbar / prompt-bar / edit-panel 跟随**: transition: left 0.15s ease
- **按钮 hover**: bg 0.15s
- **dock-btn active**: bg+color 0.15s
- **rail-btn hover**: transform scale + box-shadow 0.15s

## 缺失 / 简化（明确承认）

| 项 | 状态 |
|---|---|
| 节点详情面板 | ❌ 原站没有，我加了但**默认 DEBUG 模式才显示** |
| 节点添加时的模板选择（除了 3 种基础类型） | ❌ 简化为仅 文本/图片/视频 |
| 脚本/故事板/批量节点类型 | ❌ 属于 liblib-tv 路线 |
| 边上的文字标签 | ❌ 边只有纯 Bezier |
| 节点多选 + Group | ❌ 仅单选 |
| 右键菜单 | ❌ 暂未实现 |
| 拖动时节点对齐辅助线 | ❌ |
| 真实 API 提交 prompt | ❌ submit 按钮 `disabled` 直到有输入 |
| 节点文件名/时间戳显示 | ❌ |
| 视频节点内嵌播放的真实控制条 | 部分（用浏览器原生 `<video controls>`） |

完整差异表见 [`IMPLEMENTATION.md` §7](./IMPLEMENTATION.md)。
