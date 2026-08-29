# Batch 96：Director 多机位与 Shot 工作流

> 状态：`SCRIPT_RECORDED_PASS`
>
> 建档日期：2026-08-29。
>
> 上一批 checkpoint：`36ed905`。
>
> 代码 checkpoint：`3f897b2`。

本批以导演台为最高优先级，补齐“相机对象”和“镜头组织”之间的最小完整
纵向体验：每个相机拥有一个可编辑 Shot 记录，用户可以切换当前 Shot、设置
镜头名称和时间范围，并让截图保留 shot provenance。

## 导航

- [PLAN.md](PLAN.md)：范围、证据边界、决策与停止条件。
- [DIRECTOR_MULTI_CAMERA_SHOT.spec.md](DIRECTOR_MULTI_CAMERA_SHOT.spec.md)：
  数据、交互、稳定选择器和验证合同。
- [IMPLEMENTATION.md](IMPLEMENTATION.md)：实施结果、诊断和剩余风险。
- [runtime-audit.json](runtime-audit.json)：结构化运行时证据。

## 本批价值

当前 clone 已能新增机位、为机位创建 camera track、截图和按 cameraName 分组，
但没有稳定的 Shot identity。多机位创作因此只能依赖对象名称，无法表达当前
镜头、镜头时段、截图归属和删除后的 fallback。

本批优先解决这些 authoring integrity 问题，不扩展真实渲染资产，不声称还原了
LibTV 原站的 exact Director schema 或视觉。

## 证据边界

| 标签 | 本批含义 |
|---|---|
| `CLONE_FACT` | 当前仓库已经实现的 Director camera、timeline、capture、document、history 和 delete 行为 |
| `STORYAI_UPSTREAM_FACT` | 固定 StoryAI 上游有独立 camera shot、active camera 和按 camera 分组的启发 |
| `DECISION` | 本批 clone-owned 的 Shot record、兼容 V1 decode、shot switcher 和 provenance |
| `SOURCE_UNKNOWN` | LibTV 原站是否使用相同 shot schema、时段模型、DOM/CSS 或持久化字段 |

本批不使用新截图；现有截图识别结果按 Batch 95 及更早的 `SCREENSHOT_ANALYSIS`
记录复用。新事实来自 DOM、store snapshot、项目 JSON 和纯函数/Playwright
验证。

## 实施结果

Batch 96 已完成 clone-owned 的多机位/Shot 纵向切片：

- `DirectorShotRecordV1` 进入 portable V1 document；旧文档缺少 `shots` 时仍可
  解码，并按“一机位一 Shot、覆盖完整 timeline”派生兼容记录；
- 新增机位以一个 command 同时创建 camera、camera track 和 Shot；
- Shot 可切换、重命名和编辑时间范围；编辑进入一条可撤销 history，切换不进入
  history，同值/非法更新分别返回 `NOOP`/`REJECTED`；
- capture 具备 `shotId` provenance，图库按 Shot 分组并保留 camera 信息；
- camera/Shot 删除、最后一个 camera 阻断、clipboard remap 和 whole-project
  duplicate 都保持引用完整性；
- desktop `1440x900`、mobile `390x844`、reload/import/export 和
  `0/0/0` browser diagnostics 均通过。

专项 verifier 输出为 `SCRIPT_RECORDED_PASS`，结构化记录见
[`runtime-audit.json`](runtime-audit.json)。没有生成截图，也没有新增截图识别。

## 完成定义

1. 旧的 schema V1 文档在缺少 `shots` 时仍能被解码，并派生一机位一默认 Shot。
2. 新导出文档包含规范化 Shot 记录；Shot 的 camera、时间范围和 capture 引用
   经 strict validation。
3. 新增机位以一个 semantic command 同时创建 camera、camera track 和 Shot。
4. 切换 Shot 同步 active camera、对象选择和 timeline 轨道，但不产生 history。
5. 编辑 Shot 名称/时间范围产生一条可撤销 history；同值或非法输入不产生 history。
6. 删除 camera 会删除关联 Shot 并修复 active Shot、active camera、selection、
   timeline 和 capture provenance。
7. capture gallery 按 Shot 展示，并继续显示相机信息；移动端无横向溢出。
8. Batch 96 专项 verifier、相邻 current gates、`npm run check`、文档检查通过，
   commit/push 后工作区干净且 `master == origin/master`。
