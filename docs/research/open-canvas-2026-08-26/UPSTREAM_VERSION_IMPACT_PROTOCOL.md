# Open Canvas 上游版本影响审计协议

> 状态：`CURRENT_GUIDANCE`
>
> 当前基线：`cf3a906bb8c35bb940d3267497e7f394b8f42582`
>
> 用途：当未来需要比较或更新 Open Canvas submodule 时，保持源码事实、运行态、模式卡、采纳决策和 LibTV 影响可追溯。本文不授权移动 submodule 指针。

## 1. 为什么需要单独协议

本研究包大量结论绑定到固定 commit 和具体源码行。如果直接把 submodule 更新到 `main` 最新：

- `OC-001..025` 的事实或置信度可能变化；
- 源码行链接可能仍能打开，但指向不同实现；
- pattern card 可能只剩历史价值；
- provider registry/current runner 的漂移可能扩大或收敛；
- agent 可能误把“上游已改”当成“LibTV 应同步改”；
- 旧报告无法解释当时为何作出某个采纳/拒绝决定。

因此，上游比较、研究结论更新、submodule pointer 更新和 LibTV 实施是四个独立动作。

## 2. 当前不变量

1. 当前研究事实永远绑定 `cf3a906b...`；
2. 新候选版本先以 commit SHA 比较，不先移动 pointer；
3. 每个受影响 claim 单独更新状态，不宣布整份报告自动失效；
4. 官网部署版本若无法证明与候选 commit 一致，仍单独记录 runtime observation；
5. Open Canvas 新功能不会自动改变 LibTV source contract；
6. submodule pointer 只有在明确批准“更新研究基线”后才变更；
7. pointer、研究文档和任何 LibTV code change 不放在同一个 commit。

## 3. 触发条件

只有以下事件需要启动本协议：

- 用户明确要求研究 Open Canvas 新版本或更新 submodule；
- 上游 release/commit 声称改变 canvas graph、execution、overlay、persistence 或 provider；
- 当前行号链接/文件路径在本地基线中损坏；
- LibTV 新问题需要参考上游新增机制，固定版本没有相关实现；
- 安全边界变化，例如 key storage、client identity、KV/auth 或 upload 路径改变；
- 官网运行态与固定源码出现新的可验证冲突。

“main 有新 commit”本身不是更新理由。

## 4. 路径观察清单

| 领域 | 优先路径 | 影响的当前主张/模式 |
|---|---|---|
| graph types | `shared/lib/canvas/types.ts` | `OC-002/003/009`、typed node/status claims |
| serialization/import | `shared/lib/canvas/serialization.ts` | graph version、import/export、subgraph boundary |
| validation | `shared/lib/canvas/validation.ts` | DAG、direction、type/limit/edge validation |
| execution projection | `shared/lib/canvas/execution.ts` | `OC-004/005`、typed buckets、scene、run mapping |
| canvas store | `shared/stores/canvas-store.ts` | selection、clipboard、revision、dirty/save/conflict |
| studio interaction | `shared/blocks/canvas/canvas-studio-shell.tsx` | measured overlays、Quick Add、pending connection、clipboard、autosave |
| current runner | `shared/services/canvas/local-canvas-runner.ts` | `OC-007/009`、audio/provider coverage |
| current execute route | `app/api/canvas/[canvasId]/nodes/[nodeId]/execute/route.ts` | current studio call chain |
| legacy execute route | `app/api/execute/route.ts` | `OC-008`、legacy provider branches |
| model registry | `shared/services/public-ai-models.ts` | registry/UI/runner drift |
| provider settings | `lib/provider-settings.ts`、`lib/provider-settings-cookie.ts` | visible settings and key/security boundary |
| persistence | `shared/models/local-canvas-store.ts`、`middleware.ts` | local JSON/KV/client namespace/revision |
| product entry | `README.md`、locale/page entry | positioning and onboarding claims |
| package/runtime | `package.json`、deployment config | framework/runtime and deploy assumptions |

Path relocation itself is an impact: record old and new ownership even if behavior appears unchanged.

## 5. 审计流程

### Phase A：冻结候选

Record before reading diffs:

```text
Audit date:
Old baseline SHA:
Candidate SHA:
Candidate ref/release:
Upstream remote:
Submodule pointer moved: no
Working tree status:
Research question:
```

The candidate must be an immutable SHA. A branch name or release page alone is not a research baseline.

### Phase B：静态 change inventory

Produce a path-level inventory before semantic conclusions:

```text
added / modified / deleted / renamed paths
commit range and authorship summary
graph schema and migration diff
execution/runner diff
UI interaction diff
persistence/security diff
tests/examples/docs diff
```

Generated lockfile churn, formatting and actual behavior changes must be separated. Do not treat commit messages as sufficient evidence.

### Phase C：Claim impact

Review every affected `OC-*` claim using this status vocabulary:

| Status | Meaning |
|---|---|
| `UNCHANGED` | candidate has equivalent direct evidence |
| `STRENGTHENED` | new direct evidence reduces prior inference/uncertainty |
| `NARROWED` | claim remains true only for a smaller path/provider/state |
| `CHANGED` | candidate behavior or contract differs materially |
| `REMOVED` | supporting path/behavior no longer exists |
| `NEW_CLAIM_REQUIRED` | candidate introduces a distinct fact that should not overwrite an old ID |
| `RUNTIME_UNKNOWN` | source changed but hosted deployment equivalence is unproved |

For each impacted row record old evidence, candidate evidence, exact changed scope and what still cannot be concluded.

### Phase D：Pattern and adoption impact

Source changes do not imply all downstream documents change equally:

```text
source claim changed
  -> pattern still valid?
  -> LibTV problem still exists?
  -> adoption disposition still valid?
  -> parity / fixture / verifier mapping changed?
  -> implementation history affected? normally no
```

Use these impact classes:

| Class | Action |
|---|---|
| `UPSTREAM_FACT_ONLY` | update candidate report/claim; no LibTV decision change |
| `PATTERN_REFINED` | version the pattern card and explain old/new applicability |
| `ADOPTION_REVIEW` | revisit `OC-ADOPT-*`; do not change disposition silently |
| `LIBTV_NO_IMPACT` | explicitly record that LibTV source/current slice is unaffected |
| `FIXTURE_OR_VERIFIER_IMPACT` | update only the mapped setup/assertions after LibTV review |
| `SECURITY_REVIEW` | stop any integration recommendation until key/auth/storage review |
| `RUNTIME_REINSPECTION` | hosted site must be separately observed |

### Phase E：Runtime comparison

If the claim concerns the official site:

- record URL, locale, date, viewport and auth/key state;
- prove deployment/version relation where possible;
- keep no-key/read-only observations separate from configured execution;
- do not trigger paid generation or upload merely to match source code;
- screenshot and DOM evidence enter a new dated runtime record, not the old file.

### Phase F：Baseline decision

After the impact report, choose one:

| Decision | Meaning |
|---|---|
| `KEEP_PINNED` | current study remains sufficient; candidate is only a comparison appendix |
| `ADD_SECOND_BASELINE` | preserve both versions because behavior evolution matters |
| `UPDATE_BASELINE` | candidate becomes the new default research object after explicit approval |
| `REJECT_CANDIDATE` | candidate is unstable, irrelevant or lacks provenance |

`UPDATE_BASELINE` requires explicit user approval because it changes repository git metadata and invalidates assumptions. Even then, old dated research remains in history or an explicit versioned directory.

## 6. Impact Matrix Template

```text
Impact ID:
Old SHA / candidate SHA:
Changed paths:
Affected OC claims:
Old source fact:
Candidate source fact:
Claim status:
Runtime equivalence:
Affected pattern cards:
Affected OC-ADOPT decisions:
Affected OC-BP / LIBTV-PAR / FIX / VR:
LibTV current source impact:
Security impact:
Documentation updates:
Submodule decision:
Unknowns / stop conditions:
```

One impact row may affect multiple links, but it must not combine unrelated graph, provider and UI changes into one conclusion.

## 7. 禁止的更新方式

| Anti-pattern | Risk | Required correction |
|---|---|---|
| `git submodule update --remote` then inspect | pointer moves before evidence is frozen | compare immutable SHA first |
| rewrite old `OC-*` rows in place | loses historical truth | mark impact and add versioned evidence |
| bulk replace all line anchors | links may point to semantically different code | verify each affected claim |
| copy new upstream UI into LibTV | upstream evolution is not LibTV source evidence | return to LibTV contract and adoption gate |
| infer hosted deployment from repository main | deploy may lag/diverge | separate runtime audit |
| treat new provider registry row as runnable | registry/adapter/runner can drift | trace full call chain |
| update pointer and LibTV code together | provenance and rollback become ambiguous | separate research metadata from implementation |
| discard old report as outdated | old Batch/decision provenance disappears | retain dated baseline and supersession scope |

## 8. Verification And Commit Protocol

For a documentation-only candidate comparison:

1. verify old and candidate SHAs are recorded;
2. verify current submodule pointer has not moved;
3. run Markdown link validation and `git diff --check`;
4. commit only the new impact report and index changes;
5. push the comparison commit;
6. request explicit approval before any pointer update.

For an approved pointer update:

1. commit the submodule pointer and baseline declaration separately;
2. update affected claim links and statuses in a follow-up documentation commit;
3. keep unrelated LibTV code and parallel WIP unstaged;
4. run the documentation gate again;
5. record old/new SHAs and the approval in the iteration log.

## 9. 当前结论

No upstream change is being proposed or applied in this batch. The current fixed baseline remains valid. This protocol closes the maintenance gap identified by the research completeness review: future upstream evolution now has a reproducible path that preserves old evidence and does not silently authorize LibTV changes.
