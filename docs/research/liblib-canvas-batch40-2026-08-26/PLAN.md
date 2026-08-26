# Batch 40 计划：导演台动画视频导出与画布回流

## 1. 缺口与价值排序

| Candidate | Current clone | Source evidence | Value | Decision |
|---|---|---|---:|---|
| export command/settings | absent | exact labels | 5 | implement |
| duration/aspect controls | absent | exact labels | 5 | implement with calibrated ranges |
| real canvas recording | absent | explicit record/error contracts | 5 | implement |
| playable canvas video node | absent | guided canvas-return workflow | 5 | implement |
| atomic node/edge history | still capture only | existing graph convention | 5 | implement |
| progress/success/error states | absent | exact state strings | 5 | implement |
| source MP4 upload | no backend | explicit source contracts only | 2 | document/defer |
| auth/read-only gates | no auth model | exact failure strings only | 2 | document/defer |
| audio recording | no director audio track | no current workflow evidence | 1 | defer |

## 2. Source / Replication / Clone Boundary

### LibTV source fact

- The director has `导出设置`, `时长`, `比例` and `导出视频到画布`.
- The source distinguishes browser/MP4/canvas-recording/empty-frame/
  empty-video/upload/node-create failures.
- Successful export creates a video result on the canvas for later editing.

### Existing replication fact

- The upstream director project has an R3F viewport and still-image capture.
- It has no animation timeline, motion path or animation video export.
- The current clone already has a serializable timeline/path pipeline, a
  `preserveDrawingBuffer` WebGL canvas and an atomic still-capture return.

### Clone decision

- Record a cropped 2D output canvas sourced from the real R3F WebGL canvas.
- Use `HTMLCanvasElement.captureStream(30)` and `MediaRecorder`.
- Pick the first supported WebM MIME candidate and store the result as a
  session-local blob URL.
- Map the full timeline range into the chosen output duration so short test
  exports still contain the full authored motion.
- Preserve and restore the user's timeline time/playback state.
- Keep the director open after success; the returned node is observable when
  the user returns to the canvas.

## 3. State And Ownership

```text
DirectorDesk
  export panel state
  request id + settings
  progress/result/error presentation
  canvas transaction on success

DirectorViewport
  source WebGL canvas ownership
  aspect-frame crop geometry
  browser recording orchestration
  timeline sampling callbacks

canvasStore
  createDirectorAnimationExport()
  one video node + one edge + one history snapshot

VideoNode
  actual <video> rendering for director blob output
  metadata-only semantic selectors
```

No `MediaRecorder`, `MediaStream`, `Blob` or Three.js object enters Zustand.
Only scalar metadata and the blob URL cross into `canvasStore`.

## 4. Implementation Steps

1. Add a browser recording utility with capability checks, MIME selection,
   aspect crop, non-empty frame/video validation, progress and cleanup.
2. Add a typed request/result/error contract between `DirectorDesk` and
   `DirectorViewport`.
3. Add a source-labeled export trigger and settings popover with duration,
   aspect ratio, progress, success and error states.
4. During export, hide director helpers, stop ordinary playback, sample the
   full timeline deterministically and restore prior state afterward.
5. Add `DirectorAnimationExportMetadata` and
   `createDirectorAnimationExport` to `canvasStore`.
6. Render returned director exports as real playable `<video>` elements.
7. Add Batch 40 Playwright for recording bytes, actual video metadata, graph
   return, source edge, selection, one-step undo/redo, error-free desktop and
   mobile layout.
8. Inspect screenshots once, update the ledger and stable docs, then run
   Batch 35-40 and project-wide quality gates.

## 5. Stable Selectors

| Selector | Contract |
|---|---|
| `[data-director-export-trigger]` | opens/closes export settings |
| `[data-director-export-panel]` | source-labeled export settings surface |
| `[data-director-export-duration]` | output duration input |
| `[data-director-export-aspect]` | ratio choice |
| `[data-director-export-submit]` | begins browser recording |
| `[data-director-export-status]` | idle/exporting/success/error |
| `[data-director-export-progress]` | normalized or percentage progress |
| `[data-director-animation-export]` | returned video media element |
| `[data-director-animation-export-node]` | returned node semantic root |

## 6. Acceptance Criteria

- The export panel exposes exact source labels for settings, duration, ratio
  and submit.
- Duration is finite and clamped to `1..timeline.duration`.
- Ratio changes both output dimensions and the active composition frame.
- Unsupported browser APIs and recorder failures surface explicit errors and
  create no graph node.
- Recording captures the real R3F canvas, hides helpers and advances authored
  animation across the full timeline.
- The resulting blob is non-empty and browser-decodable as a video.
- Returned metadata records source, scene, camera, ratio, dimensions, duration,
  MIME, byte size, creation time and edge id.
- One store call creates one ready video node and one direct source edge.
- The target is selected; one undo removes node and edge; one redo restores
  both.
- Existing still capture remains functional.
- Desktop and `390x844` settings/status UI stay in viewport with no document
  overflow.
- Batch 35-39, `docs:check`, `npm run check` and `git diff --check` pass.

## 7. Out Of Scope

- claiming exact source geometry, duration defaults, encoding or bitrate;
- MP4 transcoding and remote upload;
- login/read-only feature gates;
- durable blob persistence across reload;
- audio muxing, background workers, cancellation or queued exports;
- service-side render parity.

## 8. Status

- [x] Current source vocabulary and failure taxonomy recorded
- [x] Upstream and current-clone implementation boundaries recorded
- [x] Recording, UI, graph and verification contracts documented
- [x] Browser recording utility and director integration
- [x] Canvas video return and playable node
- [ ] Focused Playwright and screenshot ledger
- [ ] Cross-batch regression, stable docs and final quality gate
