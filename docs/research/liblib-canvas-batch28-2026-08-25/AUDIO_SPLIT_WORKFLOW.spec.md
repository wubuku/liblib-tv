# Audio Split Workflow Specification

## Goal

复刻当前 LibTV ready-video 的三项音视频分离画布工作流：

```text
source video
  ├── audio output
  └── silent-video output
```

两个 output 都直接连接 source。silent video 只是位置上排在 audio 右侧。

## Modes

```typescript
type AudioSplitMode = "av" | "vocals" | "background";

type AudioSplitOutputKind = "audio" | "silent-video";

interface AudioSplitMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  mode: AudioSplitMode;
  outputKind: AudioSplitOutputKind;
  edgeId: string;
}
```

| Mode | Menu label | Audio filename |
|---|---|---|
| `av` | 音视频分离 | `{source}_音轨` |
| `vocals` | 人声提取 | `{source}_人声` |
| `background` | 背景音提取 | `{source}_背景音` |

silent-video filename 始终为 `{source}_无声`。

## Toolbar State

- idle：
  - icon；
  - `音视频分离`；
  - chevron；
  - dropdown enabled。
- busy：
  - spinner 替换 icon；
  - label 为 `分离中`；
  - chevron 隐藏；
  - trigger disabled；
  - menu closed。

## Graph Transaction

一次 store action：

1. snapshot 当前 graph；
2. 创建 audio node；
3. 创建 source-to-audio edge；
4. 创建 silent video；
5. 创建 source-to-silent-video edge；
6. 单选 silent video；
7. 清空 redo stack。

建议 clone calibration：

- source -> audio gap：`120` world units；
- audio -> silent video gap：`120` world units；
- 三个节点顶边对齐。

精确 gap 是 clone decision，不声明为 source DOM fact。

## Result Rendering

### Audio

- `350x140`；
- title 使用 mode 对应 filename；
- waveform placeholder；
- duration 继承 source；
- metadata selectors 暴露 mode/source/output kind。

### Silent video

- `512x288`；
- title `{source}_无声`；
- pending/resource placeholder；
- muted visual；
- duration/resolution 继承 source；
- metadata selectors 暴露 mode/source/output kind。

## Lifecycle

- 只在 ready video 单选态可见 toolbar。
- action 期间不能再次打开 audio menu 或重复提交。
- action 完成后 selection 移到 silent video，因此 source toolbar 自然卸载。
- undo 删除两个 outputs 和两条 edges。
- redo 恢复整个 graph transaction。

## Prototype Boundary

- timer 只用于复刻 busy 可见性；
- output 不含真实媒体 URL；
- waveform 和 muted body 是本地 placeholder；
- 不计算积分，不请求服务，不轮询，不上传；
- 不声明 audio-only、video-only 或失败路径已实现。

## Stable Selectors

- `[data-video-audio-menu-trigger]`
- `[data-video-toolbar-menu="audio"]`
- `[data-video-audio-mode]`
- `[data-video-audio-busy]`
- `[data-audio-split-output]`
- `[data-audio-split-mode]`
- `[data-audio-split-output-kind]`
- `[data-audio-split-source-id]`
