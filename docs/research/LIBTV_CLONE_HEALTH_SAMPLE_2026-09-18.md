# LibTV Clone Health Sample — 2026-09-18（batch 344）

> 目的：LibTV 复刻目标（batch 344 起）的首轮 clone 健康抽样。与并行开发者的
> 维护集（78 项，HARNESS.md Batch 381 权威清单）互补——本样本取自维护集
> **补集**，覆盖维护集未周期性覆盖的批次。

## 方法

- 非维护集样本（存在文件且不在 78 项清单内）：
  `10 30 45 75 95 210`（首批含 120/160/300 等编号空洞与文件缺失剔除）。
- 运行环境：dev server 4317；原生 arm64 shell 直启（Rosetta 陷阱规避）。
- 回写处理：liblib 截图与 runtime-audit.json 按 DEC-018 **恢复**（非本批
  fixture 不落库）；jimeng 侧截图按 jimeng 约定提交。

## 结果

| 批次 | 结果 | 备注 |
|---|---|---|
| 10 | PASS | 图片编辑状态矩阵 |
| 30 | PASS | 智能抠图/时长反馈 |
| 45 | PASS | 导演台群组/多选 |
| 65 | **FAIL** | `run_canvas_restore` 中 `KeyError: 'canvas-1'`——多画布生命周期 ownership 断言取不到 `canvas-1` |
| 75 | PASS | — |
| 95 | PASS | — |
| 210 | PASS | — |

**通过率 6/7。** 唯一失败为 batch 65 的真实断言失败（非超时/非 flake）。

## batch 65 失败线索（复刻缺口）

`verify-liblib-batch65.py:351` — `canvas_one["ownership"]["canvas-1"]`
KeyError：多画布生命周期隔离合同（LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT）
的 ownership 快照中不存在 `canvas-1` 键。两种可能：

1. clone 侧行为回归（canvas-1 的 ownership 记录丢失/改名）；
2. verifier 合同过期（runtime-audit.json 结构已演进，键名变化）。

后续排查方向：对照
`docs/research/LIBTV_MULTI_CANVAS_LIFECYCLE_ISOLATION_CONTRACT.md` 与当前
`runtime-audit.json` 实际结构，确认键名漂移或行为回归，再做最小修复。
**未自动修复**——该合同属并行开发者重点维护域，改动前需对照其最新提交。

## 抽样教训

- 后台 shell 的 zsh 不做无引号变量分词——样本列表须以 Python 构建。
- verifier 编号存在空洞（2/34/55/66/108-110/118/120/250/340/400/460/490
  等无文件），样本须按 `glob` 实存文件过滤。
