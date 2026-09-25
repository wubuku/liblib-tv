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
| CanvasMapDock 小地图拖拽 (2026-09-24 源站实测, Batch 179) | 在小地图内拖拽 | 视口随拖拽平移（光标下的世界点成为视口中心）；mini-node 点击仍为选中 + 聚焦 |
| 指针交互配置 (Batch 191/195 文档对齐) | ReactFlow props | panOnDrag=[1,2]（鼠标中键/右键拖动平移，对应帮助声明）；panOnScroll+zoomOnScroll（滚轮缩放）；multiSelectionKeyCode=Shift/Meta/Control（多选管道已通，工具条未实现） |
| CanvasMapDock (缩小/放大) | click | XYFlow `zoomIn/zoomOut({duration:200})` + 更新 `zoomPercent` |
| CanvasMapDock (适应画布) | click | XYFlow `fitView({duration:200, padding:0.1})` + `zoomPercent=100` |
| CanvasMapDock (一键整理) | click | `runOrganize('grid')` 实际重排节点 |
| CanvasMapDock (搜索节点, 2026-09-23 源站实测, Batch 163) | click / ⌘F | 开关节点搜索面板：输入框占位“搜索节点名称”、按名称/内容实时过滤、无匹配显示“无匹配节点”、点击结果选中并缩放聚焦（100%→273%，× / Esc 关闭） |
| CanvasMapDock (选择整理方式下拉) | click | 弹出 3 选项菜单（按连线横向/纵向/网格） |
| DebugToggle (右下角) | click | 切换 `isDebugMode`（默认 false） |
| 全屏编辑遮罩 (PromptBar 全屏时) | click | 退出全屏 |

## 顶部 / 左侧 / 左下 UI

| 元素 | 触发 | 结果 |
|---|---|---|
| TopBar "使用教程" (2026-09-23 源站实测, Batch 169) | click | mock 对话框（源站打开外部飞书文档，URL 未采样） |
| 连线视觉 (2026-09-23 源站实测, Batch 169) | 默认 | 蓝色虚线 (rgba(59,130,246,0.42), 2px, dasharray 7 5)，与源站虚线形态一致 |
| 节点右键菜单 (2026-09-25 源站实测, Batch 226/228; 旧版 Batch 170) | 节点右键 | 按类区分：**内容图片** 复制 ⌘C / 复制图片 / 创建副本 ⌘D / 设置为资产图 / 删除 ⌫(红)；**空图片** 复制图片+重新生成均禁用（Batch 170 旧采样=空图片形态）；**非媒体**(文本/导演台) 复制/创建副本/重新生成(禁)/删除；**内容视频**(Batch 228 实测)与**音频**极简三行 复制/创建副本/删除（无中间行）。禁用行点击无效。图片空白右键菜单 整理/重置 另见 Batch 170 |
| 空白右键菜单 (2026-09-23 源站实测, Batch 170) | 画布空白右键 | 五项逐字：添加节点（打开 选择节点类型 菜单）/ 上传文件（系统文件选择）/ 粘贴 ⌘V / 整理（按当前整理方式重排）/ 重置 ⌘0（适配画布） |
| Breadcrumb "测试作品" | click | 作品下拉（Batch 164 对齐源站：作品列表 + 当前项高亮） |
| Breadcrumb "测试项目" | click | 项目下拉（项目列表 + 当前项高亮） |
| Breadcrumb "画布 1" | click | 画布下拉（Batch 164 对齐源站：画布 头 + 「+」新建入口 + 画布行带节点数与当前勾标 + 重命名/删除操作行；切换画布按 key 加载 mock 数据） |
| ToolRail "添加节点" (Batch 167 对齐源站逐字) | click | 弹出菜单：组「添加节点」7 项短标签 文本/图片/视频/音频/3D模型/3D导演台/视频剪辑台，全部创建真实节点（Batch 221 起 3D导演台/视频剪辑台渲染器实现；音频为图标卡片，Batch 213）+ 组「添加资源」上传文件（触发系统文件选择，行为与本地上传一致） |
| ToolRail "查看项目资产" (2026-09-23 源站实测, Batch 165) | click | 开关 `FrameosProjectAssetsPanel`：标题 项目资产，页签 角色/物品/环境（角色默认激活），搜索占位 “搜索资产名称...”，空态 “暂无已生成的资产图”，× 关闭 |
| ToolRail "从素材库选择" | click | 打开素材库对话框（Batch 212/224 对齐：全部素材/我的收藏顶级目录 + 筛选行 收藏/创建者/创建时间 + 素材卡时长徽章/创建者名 + 底部 已选 N 个/取消/添加参考素材；添加=按所选素材在画布创建带内容节点并关闭，0 选中禁用，2026-09-25 源站实测） |
| ToolRail "本地上传" | click | Batch 223 起真实接线：文件选择（image/video/audio，多选）→ 按 MIME 建带内容节点（图片→imageUrl、音频→audioUrl、视频→imageUrl 封面），标题 = 文件名去扩展名（2026-09-25 探针采样对齐）；空态 上传文件 CTA 同行为 |
| ToolRail "模板" (2026-09-23 源站新增, Batch 162) | click | 开关 `FrameosTemplatePanel`：页签 公共模板/企业模板/我的模板（公共模板默认激活）+ 模板卡片（30s小说切片/九宫格大师分镜/大师电影分镜/时间凝固流光/暂别×视角×特效镜头大全/360度旋转展示）；卡片应用保持 mock（源站未采样） |
| ToolRail "帮助" | click | 打开 `FrameosHelpPanel` |

## 节点交互

| 节点 | 触发 | 状态 |
|---|---|---|
| 任意节点 | hover | 右下角 resize-handle 渐显（视频节点除外）；图片节点仅在**已有内容**时 hover 显示右上角 替换内容 按钮——空图片节点 hover 无任何按钮（2026-09-23 源站实测, Batch 172 修正过期的 hover 蒙层描述） |
| 任意节点 | click | selected 状态：蓝色边框 + 4px 光晕 + 左右 handle 显现（14×14 白色圆 + 蓝边） |
| 任意节点 | drag | 自由拖动（XYFlow 内建） + **floating-toolbar 和 PromptBar 用 `transition: left 0.15s` 平滑跟随** |
| 任意节点 | drag end | 位置写回 store（不入 history stack） |
| 文本节点 | 输入 | contenteditable 实时写 `promptValue` |
| 视频节点 | click 中心播放按钮 | 切换 `isPlaying` → 内嵌 `<video>` 元素，错误自动 fallback 到封面 |
| 视频节点 | hover | **仅对有内容的视频节点**：中心播放按钮 + 替换按钮；空视频节点为纯图标无任何按钮/徽章（2026-09-23 源站实测, Batch 173；时长徽章 “00:05” 为过期描述，已移除） |
| 视频/图片节点 | click 替换按钮 (右上角) | 触发 `<input type="file">` 文件选择，选中即以 objectURL 更新节点内容（Batch 203 起图片节点可用，且可撤销） |
| 音频节点 | 选中 | 空音频：下方音频面板：参考 按钮 + 占位 描述音乐 / 配音 / 音效 + BGM S6 模型 + 参数 + 积分 100 + ↑ 生成按钮 (Batch 213；真实生成不在原型范围)。内容音频（Batch 222 源站实测）：节点内 图标 + 播放器行 [播放|当前时间|进度|总时长] + 替换内容 按钮，仅右 handle；工具条 [下载,收藏]，无面板 |
| 任意节点 | Delete / Backspace 键 | 从 store 删除该节点 + 关联的边（**立即删除，无确认框**——2026-09-24 源站实测对齐, Batch 177；右键菜单 删除 / ⌘X 剪切同样立即执行） |

## 选中节点时的浮动面板（**跟随节点 + 画布缩放**）

> 实现原理：所有面板用 `position: fixed` + `useViewport()` 拿 pan/zoom 实时计算视口坐标。

| 面板 | 出现条件 | 位置 | 内容 |
|---|---|---|---|
| `FrameosNodeFloatingToolbar` | 节点选中 | 节点正上方 57px 处，居中 | 文本：[全屏查看/下载]（Batch 158/171）；空图片：无工具条（Batch 172）；内容图片：**⛶全屏查看/下载/⭐收藏/超清/720全景/打光/改图/裁剪/标注/宫格切分∨** 十项（Batch 220）；空视频：[全屏查看/下载]（Batch 171 旧版采样）；**内容视频：全屏查看/下载/收藏/剪辑/裁剪/音视频分离/超清/去字幕/片段重拍 九项**（2026-09-25 实测，Batch 225，覆盖旧两项）；内容音频：[下载/收藏]（Batch 222） |
| `FrameosPromptEditor` | 选中**空**媒体节点（图片/视频无内容、音频无音频） | 节点正下方 12px 处居中，**跟随节点与缩放移动**（Batch 180 恢复跟随定位；此前误停靠在右下角） | Batch 225 语义：**内容媒体节点（有图/有音频）选中无面板**（2026-09-25 源站实测）；空节点显示 内容区占位“描述你想要的图像，@引用素材”+ 全屏编辑；头部 聚焦/故事版/参考 + 引用芯片 + 删除连线/替换参考；底部 模型/档位/高级设置/积分/生成（详见 Batch 159/160） |
| `FrameosNodeEditPanel` | **调试模式** + 节点选中 | 节点右侧 12px（或左侧如右边空间不够） | 节点 ID / X,Y 坐标 / 按类型的参数表单 / 快捷操作（复制/锁定/删除） |
| `FrameosImageLightbox` (Batch 227 图片 / 230 视频) | 内容图片/视频工具条 ⛶全屏查看 | 全屏浮层（近黑背景） | 图片：居中 contain（可缩放）+ 顶部 [放大/缩小/重置/下载]；视频：真视频源渲染 `<video controls>` 播放器（无缩放钮），封面源渲染封面图；右上 × 关闭；Esc 关闭（Batch 227 源站采样；视频为同族推断） |
| `FrameosGroupToolbar` (Batch 229) | 框选选中 ≥2 节点 | 选中集合包围盒上方 15px，水平居中 | `.group-toolbar` 形态：[成组 | 批量下载]（高 36）；多选时单节点工具条隐藏；点选区包围盒外空白清除。成组/批量下载为 mock（源站点击效果未采样） |
| 工具条 下载 (Batch 231) | 点击 | 触发浏览器下载 | 内容节点按 imageUrl/audioUrl 下载（接受 http/blob:/根相对路径，文件名=节点标题）；无可下载源时 alert 提示 |

边界碰撞：所有面板有 `window.innerWidth/Height` 检查，节点靠右时面板左偏，靠下时面板上移。

## 边交互

| 元素 | 触发 | 状态 |
|---|---|---|
| 边 | hover | 变粗（4px）+ flowing pulse 1.6s linear infinite + 剪刀删除按钮出现 |
| 边 | click 剪刀 | 从 store 删除该边（`removeEdge`，Batch 159 起入撤销历史） |
| 拖 handle 创建连接 | drag from handle | 临时蓝色虚线 + handle 蓝色光晕（来自 CSS）；连线创建**入撤销历史**（Batch 174 对齐源站全局撤销栈） |
| PromptEditor 底部 (2026-09-23 源站实测, Batch 160) | 面板打开 | 模型下拉默认 **Seedream 5.0 Pro**；合并档位 chip **2K · 16:9**；**高级设置**按钮；积分行 = 金币 60 · 30 · **5折**；圆形 ↑ 生成按钮（点击进入 mock running 态并禁用） |
| ~~双击空白处~~（2026-09-24 源站新版本已移除该入口, Batch 182 同步移除） | ~~双击画布空白~~ | 创建节点请使用左栏 添加节点 菜单或空态 CTA |
| 聚焦模式 (2026-09-23 源站实测, Batch 161) | 面板头部点 **聚焦** | 节点覆盖 聚焦模式/请选择一张图像进行「局部框选」操作/按 ESC 键可退出当前模式 浮层 + 顶部条 请在图片上框选聚焦区域 + 返回节点/退出；Esc/退出/返回节点 三条退出路径均可用（真实局部框选未实现——需已生成图像） |
| PromptEditor 头部 (2026-09-23 源站实测, Batch 159) | 选中图片/视频节点 | 工具行 = 聚焦/故事版/参考 + 每条入边一枚引用芯片 (T 图标 + × 移除单条边) + 删除连线 (清空全部入边) / 替换参考；芯片删除与删除连线均可撤销 |

## 键盘快捷键

| 键 | 行为 |
|---|---|
| `Esc` | 多级退出：聚焦模式 → 节点搜索 → 双击菜单(已移除) → 帮助 → 添加节点菜单 → 整理菜单 → 取消选中 (Batch 177/182) |
| `Delete` / `Backspace` | 立即删除选中节点 + 关联的边（输入框内不触发；Batch 177 移除确认框） |
| `Cmd/Ctrl + Z` | 撤销 (Batch 159/174: 覆盖连线删除/创建) |
| `Cmd/Ctrl + Shift + Z` | 重做 |
| `Cmd/Ctrl + D` | 复制选中节点（位置偏移 +40,+40） |
| `Cmd/Ctrl + C/X/V` | 剪贴板循环 (Batch 134; ⌘V 用内部剪贴板) |
| `Cmd/Ctrl + F` | 搜索节点 (Batch 163) |
| `Cmd/Ctrl + S` | 保存 toast (mock) |
| `Cmd/Ctrl + A` | 画布上阻止浏览器原生全选 (Batch 188; 输入框内原生效) |
| `?` 或 `Shift + /` | 打开/关闭 `FrameosHelpPanel` |
| `+` / `=` | 放大 |
| `-` / `_` | 缩小 |
| `0` | 适应画布 |
| 方向键 | 移动选中节点 (Shift = 10px) |
| `Tab` | 切换选中下一个节点 |

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
| 右键菜单 | ✅ 已实现并验证（节点：复制/创建副本/删除；空白处：添加节点；Esc/外部关闭，Batch 157） |
| 拖动时节点对齐辅助线 | ❌ |
| 真实 API 提交 prompt | ❌ submit 按钮 `disabled` 直到有输入 |
| 节点文件名/时间戳显示 | ❌ |
| 视频节点内嵌播放的真实控制条 | 部分（用浏览器原生 `<video controls>`） |

完整差异表见 [`IMPLEMENTATION.md` §7](./IMPLEMENTATION.md)。
