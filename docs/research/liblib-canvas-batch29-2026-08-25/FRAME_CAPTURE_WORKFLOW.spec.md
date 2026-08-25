# Video Frame Capture Workflow Specification

## Goal

复刻当前 LibTV ready-video 的视频帧转图片画布工作流：

```text
source video
  └── image frame
```

顶部 toolbar 和播放器 camera 使用同一个 store transaction。

## Data Contract

```typescript
type VideoFrameCaptureKind = "first" | "last" | "current";

interface VideoFrameCaptureMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  kind: VideoFrameCaptureKind;
  captureSeconds: number;
  name: "首帧" | "尾帧" | "截图";
  alt: "视频首帧" | "视频尾帧" | "视频截图";
  edgeId: string;
}
```

| Kind | Menu | Time | Name | Alt |
|---|---|---:|---|---|
| `first` | 截取首帧 | `0` | 首帧 | 视频首帧 |
| `last` | 截取尾帧 | `max(duration - 0.05, 0)` | 尾帧 | 视频尾帧 |
| `current` | 截取当前帧 | clamped player time | 截图 | 视频截图 |

## Entry Points

### Top toolbar

- 位于 `画面编辑` 后、download divider 前；
- trigger icon 为 storyboard/frame group；
- trigger label 为第一项 `截取首帧`；
- 带 chevron；
- dropdown 顺序为 first、last、current；
- dropdown 相对自己的 trigger 居中。

### Player camera

- `28x28` icon button；
- click 直接创建 current capture；
- hover 在按钮上方显示 first、last、current；
- hover bridge 使 pointer 从 button 移到 menu 时菜单不消失。

## Graph Transaction

一次 store action：

1. snapshot 当前 graph；
2. resolve source absolute position；
3. clamp capture time；
4. 找到 source 右侧可用 output slot；
5. 创建 `512x288` image node；
6. 创建 `source video -> image` edge；
7. 保留 source selection；
8. 清空 redo stack。

首个 slot：

```text
x = source absolute x + source width + 100
y = source absolute y
```

clone 重复截取避让：

- x 保持同一 output column；
- 从 source y 开始向下搜索；
- 每个 slot 为 image height `288` + vertical gap `48`；
- 与任何现有 node rectangle 相交时继续下移；
- 这是可测试的 clone approximation，不声明为原站算法。

## Result Rendering

- node type：`image`；
- dimensions：`512x288`；
- `imageUrl`：source poster；
- logical media dimensions：`1280x720`；
- `filename`：`首帧`、`尾帧` 或 `截图`；
- `editorVariant: "empty"`；
- 普通 ImageToolbar 和 ImageEditPanel 保持可用；
- metadata 暴露 source、kind、time、name、alt 和 edge ID。

## Selection And History

- capture 不切换 selection；
- source 仍是唯一 selected node；
- top toolbar 保持挂载，允许连续 capture；
- 主动点击 output 后，按普通 image node 行为显示上下浮层；
- undo 删除最后一个 image + edge；
- redo 恢复最后一个 image + edge；
- undo/redo 的 selection reset 沿用当前全局 history contract。

## Prototype Boundary

- poster 仅是代表性 frame bitmap；
- current timeline state 不是实际媒体 playhead；
- 不创建 data URL，不上传，不替换 resource；
- 不模拟 CORS、load、seek 或 upload error；
- feedback 是本地短提示，不声明复刻原站 toast 容器。

## Stable Selectors

- `[data-video-frame-menu-trigger]`
- `[data-video-toolbar-menu="frame"]`
- `[data-video-frame-kind]`
- `[data-video-player-camera]`
- `[data-video-player-frame-menu]`
- `[data-video-player-frame-kind]`
- `[data-video-playhead]`
- `[data-video-frame-feedback]`
- `[data-video-frame-capture]`
- `[data-video-frame-capture-kind]`
- `[data-video-frame-source-id]`
- `[data-video-frame-capture-seconds]`
- `[data-video-frame-edge-id]`
