# Batch 66 实施与验证记录

> 状态：`RESEARCH_AND_GOVERNANCE_COMPLETE`。
>
> 日期：2026-08-27。
>
> Runtime 修改：无。

## 1. 完成内容

本批吸收 Open Canvas 与 StoryAI Director Desk 两份评估，完成：

1. 当前 Director project/session/owner、mutation/history/delete 的固定静态审计；
2. project/session authority 与 command/history/delete 两份正式合同；
3. Batch 35-50、59 共 17 个 Director verifier 的 current manifest；
4. `LIBTV-FIX-LOCAL-DIRECTOR-AUTHORITY-01` 与 `LIBTV-VR-024` 的治理登记；
5. Research Hub、Big Picture、Agent Task Map、decision、traceability、fixture、
   verifier、coverage 和 verification ledger 的可发现性同步。

本批没有修改 `src/`、R3F scene、普通 graph、Next 配置或两个固定 submodule。

## 2. 关键结论

- Director 可见能力已不是主要短板；单例 authoring state、缺失 project
  identity/schema/generation、authored/runtime 混写、无领域 history 与删除引用修复
  才是下一阶段风险中心。
- 第一代码 slice 应是 `DirectorProjectDocumentV1` strict codec，不同时包装 85
  个 action。
- Batch 59 是当前最低成本 smoke；Batch 46/48/49/50 是有价值但仍需隔离
  artifact/storage 的 merge candidates；其余脚本保持 historical regression。
- StoryAI/Open Canvas 提供方法和反例，不提供 LibTV source-exact UI、persistence
  或 delete/undo 真相。

## 3. Current Smoke 诊断

第一轮使用：

```bash
LIBLIB_BASE_URL=http://127.0.0.1:3001 \
  python3 scripts/verify-liblib-batch59.py
```

结果为 Director 入口可见但 workspace 未打开。Next dev log 明确记录
`127.0.0.1` 的 dev resource 被 origin policy 阻止。该结果没有写成产品回归。

改为同源：

```bash
LIBLIB_BASE_URL=http://localhost:3001 \
  python3 scripts/verify-liblib-batch59.py
```

结果通过：

- desktop/mobile Director workspace 与 WebGL canvas 可见且非空；
- asset search、empty result、preview-only selection、显式加入场景通过；
- object tree、Inspector selection 连续；
- ordinary graph 未变化；
- panel bounds、no-overflow 和浏览器 diagnostics 通过；
- tracked runtime audit 内容未漂移，工作区保持干净。

## 4. 证据与边界

| 内容 | 证据等级 |
|---|---|
| 19 state fields、85 actions、单例 store、late-read canvas owner | `CLONE_STATIC_FACT` |
| StoryAI versioned project、scoped persistence、undo batch、partial repair | `UPSTREAM_FACT` |
| Batch 35-50/59 原有结果 | `HISTORICAL_RECORDED_PASS` |
| 本批 Batch 59 同源 smoke | `CURRENT_CLONE_RECORDED_PASS` |
| V1 document、owner registry、command/history/delete 顺序 | `CLONE_ENGINEERING_DECISION` |
| LibTV source project/persistence/undo/delete exact behavior | `UNKNOWN` |

本批没有新增或重复识别截图。

## 5. 下一批交接

下一批只实现最小可靠性切片：

```text
DirectorProjectDocumentV1 types
  -> strict decode/normalize/validate
  -> deterministic create/serialize round-trip
  -> current store snapshot adapter at an explicit boundary
  -> pure invalid/future/reference corpus
```

明确不在同一批实现：

- project registry open/switch/close；
- localStorage/IndexedDB/backend persistence；
- 全部 85 actions 的 command migration；
- undo/redo/delete UI；
- 真实 mesh、panorama、多机位；
- LibTV source-exact shell 校准。

这些内容必须在 codec 成为稳定边界后分批进入。
