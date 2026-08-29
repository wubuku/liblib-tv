# Director Multi-Camera / Shot Contract

> 状态：`IMPLEMENTATION_CONTRACT`
>
> Batch：96。

## 1. Portable document

规范化后的 `DirectorProjectDocumentV1` 增加：

```ts
shots: DirectorShotRecordV1[];
```

每个 shot 必须满足：

- `id` 唯一且非空；
- `name` 非空；
- `cameraId` 指向现存 camera object；
- `0 <= startTime < endTime <= timeline.duration`；
- `captureIds` 唯一且只引用现存 capture descriptor；
- 一个 capture 最多属于一个 shot；
- descriptor 的 `shotId` 若非空，必须等于包含它的 shot。

旧文档没有 `shots` 时派生默认记录：

```text
每个 camera -> 一个 shot
shot.startTime = 0
shot.endTime = timeline.duration
shot.captureIds = 同 camera 的 captures
```

如果旧 capture 没有 shot provenance，则按 `cameraId` 归入对应默认 shot；
没有有效 camera 的 capture 保留 `shotId: null`，不伪造归属。

## 2. Runtime/session

runtime store 增加：

- `shots: DirectorShotRecord[]`：由 portable document restore；
- `activeShotId: string | null`：当前 session UI；
- `selectShot(shotId: string): void`：不产生 history；
- `updateShot(shotId, patch): DirectorCommandResult`：semantic command；

`selectShot` 的联动：

1. `activeShotId = shot.id`；
2. `activeCameraId = shot.cameraId`；
3. 选择 camera object；
4. 选择该 camera 的 camera track；
5. 保留当前 playhead，但超出时段时 clamp 到 `[startTime, endTime]`。

选择动作不影响 project fingerprint。名称和时段修改需通过现有
`commitDirectorMutation`，同值/非法/锁定目标返回零 history。

## 3. Camera lifecycle

### 新增

`addDirectorCamera` 一次创建：

- camera object；
- camera timeline track；
- shot record；
- active shot/camera/selection。

单次 command `ADD_CAMERA` 只产生一条 history。

### 删除

现有 delete planner 的 camera object closure 必须同时：

- 删除关联 shot；
- 修复 `activeShotId` 到第一个存活 shot；
- 修复 active camera、selection、timeline；
- 将 capture 的 camera/shot provenance 置空或回退到存活 shot；
- 保持最后 camera 阻断规则。

## 4. Capture provenance and gallery

`DirectorCapture` 与 `DirectorCaptureDescriptorV1` 增加 `shotId: string | null`。

capture 创建时读取当前 `activeShotId`。恢复、undo/redo、删除和 project duplicate
必须保留或重映射 shotId。

gallery 组键使用稳定 `shotId`；缺少 shot 的 legacy capture 使用稳定
`camera:${cameraId ?? "unassigned"}` fallback。组标题显示 shot 名称和 camera 名称，
而非只依赖 camera name。

## 5. Stable selectors

| Selector | Purpose |
|---|---|
| `[data-director-shot-bar]` | Shot switcher container |
| `[data-director-shot-option="<id>"]` | Shot selection |
| `[data-director-active-shot-id]` | Current active shot identity |
| `[data-director-shot-name]` | Shot name field |
| `[data-director-shot-start]` | Shot start field |
| `[data-director-shot-end]` | Shot end field |
| `[data-director-shot-range]` | Current normalized range |
| `[data-director-capture-group-shot="<id>"]` | Shot capture group |
| `[data-director-capture-shot-id]` | Capture provenance |

## 6. Verification contract

专项验证必须覆盖：

- old V1 decode without shots；
- new export contains normalized shots；
- create/switch/update shot；
- one-entry update history and undo/redo；
- invalid range and same-value no-op；
- camera deletion and last-camera block；
- capture provenance and shot gallery；
- import/export and reload restoration；
- whole-project duplicate and clipboard reference safety；
- desktop `1440x900` and mobile `390x844`；
- zero console/page/request diagnostics and no horizontal overflow。

