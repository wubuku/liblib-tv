# Long Video Process Graph Specification

## Goal

把超长视频提交表达为一个画布级、source-linked、可撤销的过程图：

```text
source video + references
  -> shot plan
  -> candidate batches
  -> assembly
  -> final pending video
```

## Trigger Contract

Target: `src/components/VideoGenerationPanel.tsx`

- 仅当 `mode === "long-video"` 时调用 graph handoff；
- 普通模式继续使用既有 component-local submission feedback；
- 长视频 submit 把当前 Prompt 和参数传给 `VideoNode`；
- submit 期间按钮 disabled，显示 spinner 或明确忙状态；
- 成功创建 graph 后仍保留 source video selection。

`查看过程` 不再渲染面板内四步卡。它只提示过程会在提交后出现在画布，
避免保留与 source interaction model 冲突的局部过程图。

## Request Metadata

```typescript
interface LongVideoProcessRequest {
  sourceNodeId: string;
  sourceLabel: string;
  processId: string;
  prompt: string;
  model: string;
  ratio: string;
  resolution: string;
  durationSeconds: number;
  audio: boolean;
  credits: number;
  referenceCount: number;
}

type LongVideoProcessStage =
  | "material"
  | "shot"
  | "candidate"
  | "assembly"
  | "final";

interface LongVideoProcessMetadata extends LongVideoProcessRequest {
  stage: LongVideoProcessStage;
  stageIndex: number;
  batchIndex?: number;
  status: "pending";
}
```

字段用于前端可观察性和后续 service integration，不代表已知原站 API。

## Graph Calibration

每次本地提交创建：

| Stage | Count | Visual responsibility |
|---|---:|---|
| material | 3 | 角色、场景、分镜参考缩略图 |
| shot | 3 | `S01-S03` 镜头计划等待态 |
| candidate | 4 | 两批、每批两个候选等待态 |
| assembly | 1 | 候选汇聚与拼接等待态 |
| final | 1 | 最终成片等待态 |

Topology:

- source video -> each shot;
- each material -> at least two shots, forming visible many-to-many reuse;
- each shot -> candidate batch A and B;
- all candidates -> assembly;
- assembly -> final.

节点数量与 edge 矩阵是 screenshot-shaped clone calibration，不是原站数据协议。

## Positioning And Repeated Submission

- first graph starts to the right of source in world coordinates;
- stages occupy stable columns;
- repeated process graphs retain the same internal column geometry;
- the store computes the whole graph bounds and moves the next origin downward
  until it does not overlap existing nodes;
- graph creation is one `set` call and one history snapshot.

No child/group hierarchy is required. The process is a top-level graph.

## Node Renderer

Target: `src/components/nodes/LongVideoProcessNode.tsx`

One renderer owns all stage variants:

- compact dark card with left/right Handles;
- stage eyebrow and short title;
- material/shot may show an existing local image;
- candidate/final overlays must visibly say pending and must not imply generated media;
- assembly uses a process icon and progress copy;
- selected state uses the existing cyan border/ring language;
- fixed dimensions by stage, read from node data or store defaults.

## History And Selection

- one submit = one graph history step;
- undo removes every process node and edge from the last submit;
- redo restores the same graph;
- selection remains `[sourceId]` after submit;
- process nodes may be selected normally, but do not open source-video editors.

## Stable Selectors

- `[data-video-long-process-info]`
- `[data-video-long-submit-state]`
- `[data-long-video-process-node]`
- `[data-long-video-process-id]`
- `[data-long-video-process-stage]`
- `[data-long-video-process-stage-index]`
- `[data-long-video-process-batch-index]`
- `[data-long-video-process-source-id]`
- `[data-long-video-process-status]`

## Verification

Focused Playwright must cover:

- long mode and `300s / 14700`;
- no graph from normal submit;
- busy/disabled long submit;
- 12 nodes, five stage classes and expected topology;
- shared request metadata;
- pending copy on candidates/final;
- source selection;
- repeated process bounds do not overlap;
- atomic undo/redo;
- multi-selection overlay lifecycle;
- desktop fit-view and mobile document overflow;
- zero console/page errors.
