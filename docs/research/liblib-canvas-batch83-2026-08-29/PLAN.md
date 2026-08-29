# Batch 83 计划：Director command feedback current gate

> 状态：`COMPLETED` / `RECORDED_PASS`。
>
> 建档日期：2026-08-29。
>
> 实施 checkpoint：`6c1d4c1`；结果见本目录 `IMPLEMENTATION.md`。
>
> 本批目标是收口 clone-owned Director command result 的可发现性和 current
> verifier 入口，不新增 LibTV 原站 source-exact 结论。

## 1. 背景与缺口

`DirectorCommandResult` 已在 `directorCommandKernel` 和 `directorStore` 中
形成 typed outcome、stable reason、history/resource/graph effects，并通过
workspace `data-*` 属性供 verifier 读取。但当前 `DirectorDesk` 没有将一般
Director command 的 rejection/conflict/stale/no-op 投影为真正的可见、可访问
primary feedback surface。用户只能从具体 panel 的局部状态或开发者属性推断
结果。

这会造成：

- invalid value、missing target、stale owner 和 history conflict 对用户不可见；
- `aria-live` 不覆盖 Director command result；
- current gate 能证明 store result，却不能证明结果抵达 foreground surface；
- generic feedback 可能与项目导入/导出局部 feedback 混淆。

## 2. 本批优先级

| 优先级 | Slice | 验收 |
|---|---|---|
| P0 | typed result -> Director feedback mapping | reason/disposition 分支不依赖 display string |
| P0 | foreground visible/accessibility surface | rejection/conflict/stale 有稳定区域和 `aria-live` |
| P0 | feedback lifecycle | accepted success 不制造高频噪音；新结果替换旧结果 |
| P1 | current gate | pure mapping + fresh browser rejection/visibility/diagnostic |
| P1 | 文档治理 | manifest、fixture、ledger、harness、hub、decision/traceability 同步 |

## 3. 实施边界

纳入：

- 新增 clone-owned Director command feedback adapter；
- 在 `DirectorDesk` header 放置紧凑、稳定尺寸的 command feedback region；
- 对
  `REJECTED`、`CONFLICT`、`STALE`、`UNKNOWN` 和有恢复价值的 `NOOP`
  提供可见文案与 `aria-live`；
- `COMMITTED` 不显示高频通用成功文案，避免 TransformControls/slider/input
  每次变化产生噪音；具体 workflow 的已有 result surface 继续拥有成功状态；
- 专项 pure/browser verifier 与零诊断审计。

不纳入：

- 普通 LibTV route 的全局 toast；
- 未经源站证据确认的 LibTV Director 文案、颜色、timeout、toast placement；
- fake retry、fake provider、remote operation、graph/history mutation；
- 将 feedback presentation 写入 Director document 或 semantic history；
- FrameOS feedback channel。

## 4. 证据边界

| 类型 | 本批结论 |
|---|---|
| `CLONE_FACT` | typed result 已存在；DirectorDesk 当前只有 data attributes 与项目 IO 局部反馈 |
| `CLONE_DECISION` | command outcome 的可见 primary surface 采用 compact header region |
| `SOURCE_UNKNOWN` | LibTV 原站 Director 是否有相同 command feedback surface |
| `UPSTREAM_INSPIRATION` | Open Canvas 的 typed result -> UI adapter、persistent owner surface 仅作方法参考 |

## 5. 完成标准

- stable reason 到 display copy 的映射由纯函数提供；
- mapping 不使用任意 display string 作为分支身份；
- rejection/conflict/stale/unknown 在 Director foreground surface 可见且可被辅助技术发现；
- same-value/no-op 的提示不制造 graph/history mutation；
- `COMMITTED` command 不在 header 产生高频 generic success noise；
- 新结果会替换旧结果，不保留过期 command message；
- desktop/mobile feedback 不改变 header 固定操作区的布局；
- pure verifier、browser verifier、`npm run check`、`npm run docs:check` 和
  `git diff --check` 通过；
- current manifest、fixture catalog、verification ledger、harness 和项目导航
  留下实施结果与 checkpoint。

## 6. 预定文件

- `src/lib/directorCommandFeedback.ts`
- `src/components/director/DirectorDesk.tsx`
- `scripts/verify-liblib-batch83.mjs`
- `scripts/verify-liblib-batch83.py`
- `docs/research/liblib-canvas-batch83-2026-08-29/IMPLEMENTATION.md`
- `docs/research/liblib-canvas-batch83-2026-08-29/runtime-audit.json`
- 相关 current manifest、fixture、ledger、harness、hub 和治理文档

## 7. 收口结果

- pure outcome/reason mapping：通过；
- fresh browser feedback surface：通过；
- Batch 80 `.glb` -> `.obj` current fixture drift：已修正并记录；
- Batch 59、67–83 current Director gate：通过；
- `npm run check`：通过（9 条既有 lint warning，0 error）；
- `npm run docs:check`、`python3 scripts/verify-docs.py`、`git diff --check`：通过；
- current-gate regression：已落档；
- commit/push：待本批最终文档 checkpoint 执行。
