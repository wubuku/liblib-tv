# FrameOS 画布页 — 行为清单

## 全局交互

| 元素 | 触发 | 结果 |
|---|---|---|
| AppHeader (logo) | hover | 鼠标变 pointer |
| AppHeader (下载桌面端) | click | 下载客户端（mock：无响应）|
| AppHeader (金币/积分) | hover/click | tooltip（mock：无展开）|
| CanvasToolRail (添加节点) | click | 弹出节点选择面板（mock：仅 console.log）|
| CanvasToolRail (从素材库选择) | click | 打开素材库（mock）|
| CanvasToolRail (本地上传) | click | 打开文件选择（mock）|
| CanvasToolRail (帮助) | click | 打开帮助（mock）|
| HistoryDock (撤销/重做) | click | 撤销/重做最后一步（mock：仅 console）|
| CanvasMapDock (画布小地图) | click toggle | 隐藏/显示 minimap |
| CanvasMapDock (缩小/放大) | click | XYFlow zoomIn/zoomOut |
| CanvasMapDock (适应画布) | click | XYFlow fitView |
| CanvasMapDock (一键整理) | click | 自动网格排列节点（mock）|

## 节点交互

| 节点 | 触发 | 状态 |
|---|---|---|
| 任意节点 | hover | 显示 resize-handle (右下角 18×18, opacity 0→1, transition 0.15s) |
| 任意节点 | click | selected 状态（border 高亮） |
| 任意节点 | drag | 自由拖动（XYFlow 内建）|
| 文本节点 | double-click | 进入编辑（mock：仅显示光标）|
| 视频节点 | click 播放按钮 | 播放视频（mock：弹出对话框占位）|
| 视频/图片节点 | click 替换按钮 (右上角) | 替换素材（mock）|

## 边交互

| 元素 | 触发 | 状态 |
|---|---|---|
| 边 | hover | 变粗 + 出现 flowing pulse 动画 + 出现剪刀删除按钮 |
| 边 | hover 持续 | flowing pulse 持续 1.6s linear infinite |
| 边 | click 剪刀 | 删除该边（mock：remove from store）|

## 视觉态

| 元素 | 默认 | hover/active | 选中 |
|---|---|---|---|
| node-card | box-shadow none | box-shadow 0 4px 12px rgba(0,0,0,0.3) | border 蓝色光晕 |
| node-floating-title | color #A3A3A3 | — | — |
| breadcrumb-switcher | bg transparent | bg rgba(0,0,0,0.05) | — |
| rail-btn | bg #1A1A1A | bg #2A2A2A | rail-btn--primary 蓝渐变 |
| rail-btn--primary | bg linear-gradient(135deg, #2563EB, #1D4ED8) | 维持 + transform scale(1.05) | — |
| dock-btn | color #C2C2C2, bg transparent | bg rgba(0,0,0,0.05) | dock-btn.is-active: color #60A5FA, bg rgba(59,130,246,0.16) |
| prompt-bar | bg #1C1C1C, border #2A2A2A | focus 时 border #60A5FA | — |
| model-option | bg #1A1A1A | bg #2A2A2A | model-option.is-selected: 蓝边 + 对勾 |

## 动画

- **flowing pulse on edge**: 1.6s linear infinite, 3 段错相位, dashoffset 100→0
- **节点 hover resize-handle**: opacity 0→1, 0.15s
- **节点 selected shadow**: 0 0 0 2px blue + box-shadow
- **按钮 hover**: bg 0.15s
- **dock-btn active**: bg+color 0.15s
- **rail-btn hover**: transform scale + box-shadow 0.15s
