# Batch 89 计划：Director 场景设置与新增机位

> 状态：`PLANNED`
>
> 日期：2026-08-29。
>
> 本批是连续五批中的第 1 批；完成后继续 Batch 90，不在此处宣称 Director
> 整体成熟。

## 1. 为什么现在做

StoryAI Director Desk 评估指出，当前 clone 的功能纵深已经超过固定上游，主要
缺口转为可靠性和创作入口的完整性。现有 clone 的 scene settings 只有少量散落
字段，且没有通用 add-camera action/UI；默认 fixture 只有
`director-camera-main`，限制多镜头创作。

本批选择一个窄而高价值的纵向 slice：

```text
object tree / scene inspector affordance
  -> addDirectorCamera command
  -> camera object + camera track
  -> active camera / selection / timeline authority
  -> portable document + Director history
  -> fresh-page verifier + current-gate regression
```

## 2. Clone-owned 决策

### 2.1 新增机位

- 入口在对象树头部长期可见；场景属性为空选择时也提供同一 command 的文字入口；
- 新机位以当前 `activeCameraId` 的 transform、target、FOV 和关系清空为基线，
  再应用确定性的轻微横向/纵向/纵深偏移，避免新机位与旧机位完全重合；
- 名称按当前 camera 数量生成 `机位 NN · 新镜头`，ID 使用 session 内唯一的
  `director-camera-...` identity；
- 为新 camera 创建一个当前 playhead 的 camera track 和一个 keyframe；
- 新机位成为 `activeCameraId`，同时成为唯一对象选择和 Timeline selected track；
- 保持当前 `viewMode`，不因为新增动作强制切换导演视角/机位视角；
- 新增是一个 semantic command，成功时恰好一条 Director history，undo/redo 可
  完整恢复 camera、track、active camera 和 selection repair；
- 没有 active camera 时拒绝，不创建半成品对象；capture、phone recording、
  motion-path draft 或 active gesture 等冲突状态遵循现有 command guard。

### 2.2 场景设置

- 将现有名称、背景色、地面色、ground/grid 显隐组织为明确的“场景设置”区域；
- 增加稳定的 `data-*` 语义选择器，供 agents 和 verifier 发现；
- 本批不添加未经 source/product 证据支持的 panorama、灯光、雾、地面高度、
  scene transform 或 snap；
- scene field 的逐字段 history/commit policy 不在本批扩展，Batch 90 单独处理，
  防止文本输入每个字符都产生 history entry。

## 3. 代码范围

纳入：

- `DirectorState.addDirectorCamera` 及新增 camera 的纯确定性构造/command commit；
- camera track、selection、active camera、runtime projection 和 history continuity；
- `DirectorObjectTree` 和 `DirectorInspector` 的新增机位/场景设置入口；
- Batch 89 pure/source verifier、fresh-page Playwright verifier；
- current verifier manifest、verification ledger、Harness、coverage、研究索引；
- 本批 dated implementation/audit/regression 文档。

不纳入：

- 不改变普通 LibTV React Flow、FrameOS 或 Director project owner/session 合同；
- 不引入 camera shot 独立 schema、远程同步、真实 mesh/panorama；
- 不复制 StoryAI 的默认坐标、CSS 或上游 store；
- 不新增截图，除非结构化 DOM/状态无法回答验收问题；
- 不把本批 clone 行为写成 LibTV 原站 source-exact 行为。

## 4. 验收标准

- 对象树和场景属性都能发现同一个“新增机位”动作；
- 新增后 object tree 有新的 camera object，camera 数量增加 1；
- 新 camera 与 active camera、唯一对象选择、Timeline selected track 同步；
- 新 camera 有一个 camera track 和至少一个当前时间 keyframe；
- 新 camera 的 transform 不与旧 active camera 完全重合，关系引用为空；
- `undoDirector` 恢复新增前 document，`redoDirector` 恢复新增后 document；
- portable export 包含新 camera/track，但不包含 selection、runtime refs 或 media bytes；
- mobile 视口下入口、场景设置区域和 object tree 无水平溢出；
- fresh-page verifier、Batch 59/67–89 current gate、`npm run check`、
  `npm run docs:check`、`python3 scripts/verify-docs.py` 和 `git diff --check`
  全部通过，browser diagnostics 为 `0 / 0 / 0`。

## 5. 执行清单

- [x] 读取 Director 评估、project/session/history/delete 合同和现有实现；
- [x] 记录 source / upstream / clone 边界和新增机位决策；
- [ ] 实施 store command 与 UI affordance；
- [ ] 新增并运行 pure/source verifier；
- [ ] 新增并运行 fresh-page Playwright verifier；
- [ ] 更新 manifest、ledger、Harness、coverage、索引；
- [ ] 运行 current-gate、全量检查并 commit/push；
- [ ] 确认工作区干净并进入 Batch 90。
