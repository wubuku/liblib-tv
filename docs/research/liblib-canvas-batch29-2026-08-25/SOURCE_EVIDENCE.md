# Batch 29 Source Evidence

> 采样日期：2026-08-25  
> 页面：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`

## 1. Evidence Boundary

本批重新请求当前 canvas HTML，并下载页面实际声明的 108 个静态 chunk 到
临时目录 `/tmp/liblib-batch29-all/`。证据来自当前 bundle，而不是旧 clone
文案或未登录首页。

关键文件：

| File | SHA-256 | Evidence |
|---|---|---|
| `2jbcm5mok_bay.js` | `4380cf7e54d07a899f801718fa369331f3c43d5418c386ff37947ed54f3274d8` | `VideoNodeToolbar`、`VideoPlayerBar`、菜单结构 |
| `15epcn_e-6pl6.js` | `3c976a417d35ead78e44a985f3d6d47cf1f9c5c6ae3c31221d82c5ebe70cef00` | 截帧、节点创建、上传 handoff |
| `0_o2gxip5splz.js` | `19ae080ffa0c23788cc3a6543cf835d34d50da331ab739fdafd558f994bb441e` | 运行时依赖背景 |

节点布局常量来自 `2ga3c1quu6wbd.js` 的 module `713118`：

```text
NODE_GAP = 100
NODE_WIDTH = 350
NODE_HEIGHT_EMPTY = 350
```

## 2. Top Toolbar

`VideoNodeToolbar` 构造 frame items：

```text
firstFrame   -> captureFirstFrameLabel
lastFrame    -> captureLastFrameLabel
currentFrame -> captureCurrentFrameLabel
```

运行时中文顺序：

1. `截取首帧`
2. `截取尾帧`
3. `截取当前帧`

该 `IconGroupStoryboard` 工具组位于 `画面编辑` 之后、下载分隔线之前。通用
group menu：

- trigger 显示首项文案，并带 chevron；
- 外层使用 `w-max`；
- dropdown `minWidth: 160px`；
- dropdown `borderRadius: 12px`、`padding: 6px`；
- item `fontSize: 13px`、`padding: 8px 10px`。

## 3. Player Camera Entry

`VideoPlayerBar` 在音量控制后渲染 camera：

- camera button 点击直接执行 `onScreenshot`，即截取当前帧；
- wrapper hover 时在 button 上方显示 menu；
- menu 顺序同为首帧、尾帧、当前帧；
- menu 位于 `bottom-full right-0`，通过 `pb-2` 留出 hover bridge；
- menu 为 column、`gap: 4px`、`padding: 4px`、`12px` radius；
- item 高 `32px`、`13px`、`padding-inline: 8px`；
- camera button 是 `28x28` 圆形 hover target。

## 4. Capture Semantics

### First frame

- seek time：`0`
- node name：`首帧`
- alt：`视频首帧`

### Last frame

- duration 优先取播放器 duration，否则取节点 duration；
- 无有效 duration 时提示：
  `视频尚未加载完成，暂时无法截取尾帧`；
- seek time：`max(duration - 0.05, 0)`；
- node name：`尾帧`
- alt：`视频尾帧`

### Current frame

- seek time：播放器 `currentTime`
- node name：`截图`
- alt：`视频截图`

真实提取流程：

1. 创建 off-DOM muted video，设置 `crossOrigin = anonymous`；
2. `loadeddata` timeout 为 8 秒；
3. seek timeout 为 3 秒；
4. 按 video intrinsic dimensions 绘制 canvas；
5. 转为 PNG data URL；
6. 创建 IMAGE resource node；
7. 创建 `source video -> image` edge；
8. 通知 `{name}已截取，并添加到画布`；
9. 异步转 Blob、上传，并替换临时 URL/resource metadata。

## 5. Graph Position And Selection

frame helper 使用：

```text
x = source absolute x + source display width + NODE_GAP
y = source absolute y
NODE_GAP = 100
```

调用 add-node 时传 `skipOverlapResolution: true`，因此重复截取仍会经过原站
碰撞避让。

截帧 handler 调用 add-node 和 add-edge，但没有调用新节点 selection helper。
同文件的高清、解析等 workflow 会显式选择目标，因此“截帧后保留 source
selection”是高置信 inference，不是 bundle 中的显式 selected assignment。

## 6. Source Fact / Inference / Clone Decision

### Source fact

- 顶部和播放器均提供首帧、尾帧、当前帧入口。
- 顶部工具组位于画面编辑后、下载前。
- 播放器 camera click 直接截当前帧，hover menu 提供三项。
- 三种 seek time、name 和 alt 如上。
- 创建 IMAGE node 与 `source video -> image` edge。
- 初始位置使用 source right `+100` world units、同 Y。
- add-node 启用碰撞避让。
- 成功后先使用 PNG data URL，再异步上传替换。

### Inference

- 截帧后 source 保持选中；依据是 handler 未调用 selection helper。
- 原站 add-node/add-edge 的 undo snapshot 边界未在本批 bundle 中确认。
- 播放器 hover menu 的精确像素视觉来自 CSS bundle，尚无新登录态 screenshot。

### Clone-only decision

- 使用 source poster 代表首帧、尾帧和当前帧 bitmap。
- 当前帧由本地 timeline state 表示，不执行真实视频解码。
- 每次 capture 用一个 store action 原子创建 image + edge。
- 一次 undo/redo 回退或恢复该 transaction。
- 重复截取用确定性的纵向 slot search 近似原站 overlap resolution。
- metadata 只保存在 Zustand 内存，刷新后丢失。
