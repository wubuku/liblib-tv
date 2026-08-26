# Depth Motion Capture Workflow

## Purpose

复刻 ready-video 上的“深度动作捕捉”前端工作流。它把视频的深度信息作为
镜头运动、人物动作和空间关系的参考素材，提交后在画布上生成一个
source-linked pending reference node。

## Evidence Boundary

当前 source evidence 只确认用户文案、节点命名模板、清晰度字段、时长限制
占位符和确认动作。入口位置、dialog geometry、真实参数枚举、结果媒体和
任务状态不属于 source fact。

## State Machine

```text
ready video selected
  -> click depth trigger
  -> panel open
  -> choose resolution
  -> validate local test fixture
  -> extracting
  -> pending depth reference node + direct source edge
```

## Panel Contract

| Element | Contract |
|---|---|
| title | `深度动作捕捉` |
| intro | source-backed purpose copy |
| resolution label | `清晰度` |
| local options | `720P`, `1080P` |
| submit | `确认提取` |
| busy | spinner + disabled submit |
| cancel | closes panel without graph mutation |
| source summary | source filename, duration and resolution |

Panel is node-anchored and screen-sized using the existing video lower-editor
contract. Its exact width and spacing are clone calibration.

## Validation Contract

- default 30s fixture shows a clone guard and does not mutate graph/history;
- `?duration=10` is test-only and opens the panel;
- unknown source maximum values are not displayed as fabricated numbers;
- changing local resolution affects only the request-shaped prototype metadata.

## Graph Contract

```typescript
interface DepthMotionCaptureMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  resolution: "720P" | "1080P";
  durationSeconds: number;
  edgeId: string;
  model: "depth-motion-reference";
  requestMode: "DepthMap";
}
```

Output:

- node type: `video`;
- status: `pending`;
- filename: `深度动作捕捉-{sourceLabel}`;
- no source poster reuse;
- one direct edge `source video -> depth reference`;
- source remains selected;
- one graph history snapshot for output + edge;
- repeated outputs use deterministic right-side slots.

## Stable Selectors

- `[data-depth-motion-panel]`
- `[data-depth-motion-close]`
- `[data-depth-motion-title]`
- `[data-depth-motion-intro]`
- `[data-depth-motion-resolution]`
- `button[data-depth-motion-resolution-option]`
- `[data-depth-motion-source-summary]`
- `[data-depth-motion-submit]`
- `[data-depth-motion-spinner]`
- `[data-depth-motion-submit-reason]`
- `[data-depth-motion-output]`
- `[data-depth-motion-source-id]`
- `[data-depth-motion-edge-id]`
- `[data-depth-motion-resolution-value]`
