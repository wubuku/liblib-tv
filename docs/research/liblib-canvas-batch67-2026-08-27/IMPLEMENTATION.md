# Batch 67 实施与验证记录

> 状态：`CODEC_IMPLEMENTED / GOVERNANCE_AND_FULL_REGRESSION_PENDING`。
>
> 日期：2026-08-27。
>
> 本文件随代码切片和验证结果更新；未完成项不得写成通过。

## 1. 目标

建立 `DirectorProjectDocumentV1` 的 strict codec、normalize、round-trip 和当前
Director state snapshot adapter，为后续 project/session authority 提供可执行的
portable authored-state 边界。

## 2. 预实施记录

| 项目 | 状态 |
|---|---|
| Batch 66 authority contracts | 已完成 |
| StoryAI/Open Canvas 评估吸收 | 已落档，作为方法启发 |
| 新截图识别 | 未执行，成本决策已记录 |
| 业务 runtime 修改 | 独立纯 codec 已实现；未接 store/session/persistence |
| 两个 submodule | 不修改指针 |
| 其他开发者 WIP | 不覆盖 |

## 3. 代码变更

- `src/lib/directorProjectDocument.ts`：
  - `DirectorProjectDocumentV1`、owner、scene/object/group/timeline/path、
    resource/capture DTO；
  - current Director state 的显式 snapshot adapter；
  - strict unknown-field、future schema、finite number、tuple、ID 和 reference
    校验；
  - deterministic encode/decode round-trip、深复制与 zero-partial result；
  - 排除 `dataUrl/sentNodeId`、selection、playback、timeline UI、phone runtime、
    R3F refs 和 ordinary graph history。
- `scripts/verify-liblib-batch67.mjs`：纯 Node contract corpus；
- `scripts/verify-liblib-batch67.py`：与项目现有 verifier 命名一致的入口。

codec 没有导出 private `DirectorState`，没有修改 `directorStore`、Director UI、
R3F scene、普通 graph 或两个 submodule。

## 4. 实施日志

| 时间 | 动作 | 结果 |
|---|---|---|
| 2026-08-27 | 读取 Batch 66 合同、Director store 类型和 project-docs skill | 完成 |
| 2026-08-27 | 创建 Batch 67 计划、README、截图台账和实施记录 | `e56f2e6` 已提交并推送 |
| 2026-08-27 | 实现 V1 DTO、strict decoder、normalizer、encoder 和 snapshot adapter | 完成 |
| 2026-08-27 | 首次 verifier | 发现 track `kind` 未进入白名单；保持 strict policy 并修正白名单 |
| 2026-08-27 | 第二次 verifier | 发现反例同时命中 path-owner mismatch；拆分 corpus 使每例只验证一个合同 |
| 2026-08-27 | 第三次 verifier | 通过，17 个 rejection case 全部返回预期 code/path |

实现过程中还修正了一个预实施假设：object/tree、track、group member 和 path
anchor 数组顺序具有领域语义，不能为了 canonical JSON 按 ID 排序。codec 保留这些
数组顺序，只稳定无语义的 controls/member-offset 字典键。

## 5. 验证结果

```text
python3 scripts/verify-liblib-batch67.py：
  PASS
  schemaVersion=1
  roundTripBytes=4359
  accepted=3 objects / 1 group / 4 tracks / 1 path / 1 resource / 1 capture
  rejectedCases=17
  excludedRuntimeFieldsVerified=true
  inputIsolationVerified=true
  orderPreservationVerified=true

npm run typecheck：PASS
npx eslint src/lib/directorProjectDocument.ts scripts/verify-liblib-batch67.mjs：PASS
docs:check：收口前待运行
npm run check：收口前待运行
Batch 59 current smoke：收口前待运行
git diff --check：PASS
git status：仅 Batch 67 codec/verifier WIP
```

## 6. 未决事项

- current `objects` 在 timeline seek 后同时承担 sampled projection 和 authored
  baseline；本批 adapter 只记录该过渡边界，不重构 playback；
- V1 对 pose preset 使用封闭的 20 项 schema 枚举；未来新增 runtime preset 时必须
  显式决定 schema migration，不能静默接受；
- 本批只建立 codec 和 snapshot adapter，没有把 project document 设为 store 的
  当前 source of truth，因此跨 node/canvas 串场风险尚未关闭；
- project registry、local persistence、Director history/redo、delete repair、真实
  asset/panorama 和 multi-camera 仍是后续批次；
- LibTV source-exact project persistence 和 Director UI 不由本批推断。
