# Batch 96 计划：Director 多机位与 Shot 工作流

> 状态：`COMPLETED`
>
> 建档日期：2026-08-29。

## 1. 背景

Director 当前已经有真实 R3F 视口、相机对象、active camera、camera track、
截图回流、项目文档和引用安全删除。缺口是 camera 与 shot 仍是同一层概念：
截图 gallery 主要按 `cameraName` 分组，无法稳定表达“当前正在编辑的镜头”。

固定 StoryAI submodule `8c8bd361...` 提供了独立 `DirectorCameraShot`、
`activeCameraId`、camera panel 和按 camera 分组 capture 的上游事实。本批只
借鉴这种分层方法，不把上游 schema、CSS 或行为称为 LibTV 源站事实。

## 2. 决策

### 2.1 数据分层

camera 继续是 Director object；Shot 是独立的 portable authoring record：

```ts
interface DirectorShotRecordV1 {
  id: string;
  name: string;
  cameraId: string;
  startTime: number;
  endTime: number;
  captureIds: string[];
}
```

`activeShotId` 只属于当前 session UI，不写入 portable document。新相机和新
Shot 通过一个 command 一起创建，保持一个 history entry。

### 2.2 V1 兼容

当前 `schemaVersion: 1` 保持不变。`shots` 是兼容扩展字段：

- 旧文档没有 `shots` 时，根据 camera、timeline duration 和 capture descriptors
  派生默认 Shot；
- 新生成/导出的文档总是含有规范化 `shots`；
- 不引入 schema migration，除非实现过程中证明现有 V1 无法表达该字段。

capture descriptor 增加可选兼容的 `shotId`，规范化后与 Shot 的 `captureIds`
保持一致。capture bytes、`sentNodeId` 和 R3F runtime 仍不进入持久化。

### 2.3 交互

- Shot bar 位于 Director header 的视角切换附近，按顺序显示镜头名和时段；
- 选择 Shot 是 session UI，不写 history；
- Shot inspector 在 camera 属性中显示名称、起止时间；
- 相机删除时关联 Shot 一并删除；若删除 active Shot，选择第一个存活 Shot；
- 删除最后一个 camera 继续被现有 `DIRECTOR_LAST_CAMERA_REQUIRED` 阻止；
- gallery 先按 Shot 分组，组内保留 camera 名称。

## 3. 证据边界

| 分类 | 允许写入本批文档的内容 |
|---|---|
| `CLONE_FACT` | 当前代码与当前 clone runtime 可直接证明的事实 |
| `STORYAI_UPSTREAM_FACT` | 固定上游源码直接证明的事实 |
| `DECISION` | 为 clone 完整性选定的模型和交互 |
| `SOURCE_UNKNOWN` | 尚未获得认证 LibTV Director 证据的内容 |

禁止：

- 用 StoryAI 或 clone 截图推导 LibTV source-exact DOM/CSS；
- 把 Shot 选择、时段字段或导出字段写成 LibTV 原站事实；
- 用截图替代已存在的 DOM/store/JSON 证据；
- 修改普通 canvas graph 的 Director owner/history 边界。

## 4. 实施批次

| 阶段 | 工作 | 验证 |
|---|---|---|
| A | document types、兼容 decode/normalize、runtime restore | pure fixture |
| B | store snapshot/restore、history、camera add/delete、capture provenance | store/runtime verifier |
| C | Shot bar、camera Inspector、shot gallery、mobile overflow | Playwright desktop/mobile |
| D | governance docs、专项审计、跨批回归、质量门 | current gates + `npm run check` |

## 5. 停止条件

完成上述四阶段、专项台账和远端 checkpoint 后停止本批。不得在本批结束后
自动启动 Batch 97 或继续循环。

## 6. 完成记录

Batch 96 已按 A-D 四阶段完成。代码 checkpoint 为 `3f897b2`；专项
verifier 为 `scripts/verify-liblib-batch96.py`，结构化结果写入
[`runtime-audit.json`](runtime-audit.json)。本批没有新增截图或截图识别，
没有修改 LibTV 原站状态，也没有引入 worktree。

专项结果覆盖：

- V1 旧文档兼容 decode、规范化 Shot export、Shot/camera/reference integrity；
- Shot 创建、切换、名称与时间范围编辑、同值 no-op、非法值 reject；
- 一条 history、undo/redo、camera/Shot/capture 删除修复和最后机位阻断；
- clipboard Shot ID remap、whole-project duplicate、reload/import/export；
- desktop `1440x900`、mobile `390x844`、无横向溢出和
  console/page/request `0/0/0` diagnostics。

稳定治理文档已同步到 current manifest、fixture catalog、verification ledger、
Harness、traceability、Big Picture、Agent Task Map 和研究导航。Batch 96
完成后按本计划停止，不启动 Batch 97。
