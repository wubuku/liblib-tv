# Batch 67 实施与验证记录

> 状态：`PLANNED`。
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
| 业务 runtime 修改 | 待实施，限制为独立纯模块 |
| 两个 submodule | 不修改指针 |
| 其他开发者 WIP | 不覆盖 |

## 3. 预计代码变更

- `src/lib/directorProjectDocument.ts`：V1 schema、strict codec、normalize 和 adapter；
- `scripts/verify-liblib-batch67.py`：低成本 contract verifier；
- 项目治理索引：在代码和 verifier 稳定后同步。

## 4. 实施日志

| 时间 | 动作 | 结果 |
|---|---|---|
| 2026-08-27 | 读取 Batch 66 合同、Director store 类型和 project-docs skill | 完成 |
| 2026-08-27 | 创建 Batch 67 计划、README、截图台账和实施记录 | 已创建，待 checkpoint |

## 5. 验证结果

待实施后填写：

```text
专项 verifier：
docs:check：
npm run typecheck：
npm run check：
git diff --check：
git status：
```

## 6. 未决事项

- current `objects` 在 timeline seek 后同时承担 sampled projection 和 authored
  baseline；本批 adapter 只记录该过渡边界，不重构 playback；
- project registry、local persistence、Director history/redo、delete repair、真实
  asset/panorama 和 multi-camera 仍是后续批次；
- LibTV source-exact project persistence 和 Director UI 不由本批推断。

