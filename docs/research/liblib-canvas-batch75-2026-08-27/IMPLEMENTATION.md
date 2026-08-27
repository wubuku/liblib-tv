# Batch 75 实施与验证记录

> 状态：`IMPLEMENTED / CLIPBOARD_REMAP_FOCUSED_PASS`。
>
> 建档日期：2026-08-27；实现 checkpoint：`27c6127`。

## 1. 实施范围

Batch 75 增加了同一 Director project 内的 clone-owned session clipboard：

- `src/lib/directorClipboard.ts`
  - 定义 `DirectorClipboardPacketV1`、copy selection、build/paste result；
  - selected group 扩展为成员 closure，普通 selection 只复制显式 objects；
  - 收集 object-local tracks、motion paths、stable resource descriptors；
  - 为 object/group/track/path/keyframe/anchor 分配新 ID 并 two-pass remap；
  - internal camera relation remap，external relation detach 并冻结坐标；
  - stable resource 只有目标 document 已存在完全一致 descriptor 才 alias；
  - 通过 strict document normalization 保证 accepted full plan 或 zero mutation。
- `src/store/directorStore.ts`
  - 保存 project-scoped、memory-only clipboard 与 paste ordinal；
  - `copyDirectorSelection` 不修改 document/history/persistence；
  - `pasteDirectorClipboard` 以一个 semantic command 提交 document/history；
  - paste 后 selection 指向新 group 或 objects；
  - project switch、reload 和 persistence 不转移 clipboard。
- `src/components/director/DirectorDesk.tsx`
  - Director foreground 支持非 editable/composing 的 `Cmd/Ctrl+C/V`；
  - active gesture、busy、capture viewer 和 native editable context 保持优先；
  - 未增加 toolbar、context menu、toast 或其他无源站证据的 visible UI。

同时新增：

- `scripts/verify-liblib-batch75.mjs`
- `scripts/verify-liblib-batch75.py`
- [`runtime-audit.json`](runtime-audit.json)

## 2. Pure Corpus

`verify-liblib-batch75.mjs` 通过 12 个 scenario：

1. single-object typed closure；
2. selected-group full closure；
3. external camera detach and coordinate freeze；
4. internal camera relation remap；
5. object/group/track/path/keyframe/anchor identity remap；
6. deterministic repeated paste offset；
7. stable resource alias；
8. missing/conflicting resource rejection；
9. cross-project stale rejection；
10. strict packet shape and empty selection；
11. identity allocation failure；
12. capture/runtime/graph projection exclusion。

结构化计数：

```text
group objects: 2
group tracks: 4
group paths: 1
remapped keyframes: 7
remapped anchors: 3
```

## 3. Browser Corpus

`LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch75.py`
通过：

- `Control+C` / `Control+V` 完成 copy/paste；
- accepted paste 恰好一条 Director history，selection 指向新实体；
- exact undo/redo；
- repeated offsets 为 `0.6`、`1.2`、`1.8`；
- 所有 remapped IDs 唯一；
- editable、composition、active gesture、busy、capture viewer guard；
- cross-project paste 返回 `DIRECTOR_CLIPBOARD_STALE`；
- A-B-A 切换后 project A clipboard continuity；
- ordinary graph/history unchanged；
- persistence 排除 clipboard 和 capture bytes；
- reload 恢复 canonical document，但不恢复 clipboard、paste count 或 session capture；
- zero screenshots；
- zero console/page/request errors。

## 4. 回归与质量门禁

2026-08-27 在实现 checkpoint `27c6127` 上串行运行：

```bash
python3 scripts/verify-liblib-batch67.py
for batch in 68 69 70 71 72 73 74 75; do
  LIBLIB_BASE_URL=http://localhost:3001 \
    python3 "scripts/verify-liblib-batch${batch}.py" || exit 1
done
npm run docs:check
git diff --check
npm run check
```

结果：

- Batch 67-75 全部通过；
- docs link check 通过：575 个 Markdown、3406 个本地目标；
- `git diff --check` 通过；
- lint、typecheck、Next 16.2.1 production build 通过；
- lint 只保留既有 9 条 warning；
- Batch 75 runtime audit 无截图、无 browser diagnostics；
- 验证后只有本批治理文档变更，业务实现保持在 `27c6127`。

## 5. 边界与未完成项

本批不是 LibTV source-exact copy/paste 证据，也不实现：

- system clipboard MIME、跨窗口或跨浏览器 transfer；
- cross-project/cross-canvas clipboard；
- resource bytes、lease transfer 或 real asset materialization；
- capture/capture gallery copy；
- source/canvas whole-project duplicate；
- ordinary React Flow graph clipboard；
- Option-drag 或 visible clipboard feedback。

下一项高价值 Director reliability 候选为 inactive-owner/source deletion
reconciliation，或复用本批 remap machinery 实现 whole-project duplicate；两者都
必须独立规划、fixture、verifier、文档和 checkpoint。
