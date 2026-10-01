# Batch 337（2026-10-01）：断言门禁接入 CI（附一处「刻意不做」的实测结论）

## 结论一句话

Batch 336 的门禁若没人跑就只是建议。本批接入 `.github/workflows/ci.yml`。
过程中实测发现 **`verify-docs.py` 目前无法进 CI**（干净 checkout 必失败），
故只接入门禁、并把原因写进 workflow 注释，避免后人「顺手」再加回去。

## 接入内容

```yaml
- name: Assertion quality gate
  run: python3 scripts/verify-assertions.py
```

位置在 Type check 之后、Build 之前（早失败、省时间）。
CI 现状：Checkout → Node → npm ci → Lint → Type check → **Assertion gate** → Build。

## 门禁在 CI 环境下的可用性验证

CI 是 `ubuntu-latest` + 干净 checkout，不能想当然。已用 `git archive HEAD |
tar -x` 还原出与 CI 等价的干净副本实测：

```
Assertion quality gate passed: 0 vacuous assertions in 451 verifier scripts.
GATE_EXIT=0
```

门禁只依赖 Python 标准库（`pathlib` / `re` / `sys`），无第三方依赖，
在 `actions/setup-node` 的环境里可直接运行。✅ 可进 CI。

## 🔴 顺带实测：`verify-docs.py` 现在**不能**进 CI

本来打算顺手把文档门禁也接上。干净 checkout 上实测：

```
$ python3 scripts/verify-docs.py
Missing local documentation links:
  docs/DECISION_REGISTER.md: ../research/upstream/open-canvas/shared/lib/canvas/types.ts
  ...
  docs/user-manual/tdcanvas-canvas/10-tasks/organize-canvas.md:
    ../screenshots/04-organize-canvas-side-panel-select.png
REAL_EXIT=1
```

两类缺失来源：

| 缺失 | 原因 |
|---|---|
| `research/upstream/*` 下的 `.ts` | **submodule 未初始化**（`.gitmodules` 声明了 open-canvas / storyai 两个） |
| `docs/user-manual/*/screenshots/*.png` | **被 gitignore**（`.gitignore` 排除验证/手册截图产物） |

也就是说 `verify-docs.py` **只在本地工作区能过**，因为那里有 submodule 内容和
被忽略的截图产物。接进 CI 会让**每次 push 都红**。

> 这是本次唯一「刻意不做」的事，并在 workflow 里留了注释说明原因与前置条件
> （需先让脚本区分「产物缺失」与「链接写错」）。

> 教训：加 CI 步骤前先在**干净 checkout** 上验一次。本地能跑 ≠ CI 能跑。
> 这与 Batch 329「13 处各自手写快照」的教训同源：
> 分散的隐式假设，总要在某个时刻集中爆发。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 338：
  - 让 `verify-docs.py` 区分「产物缺失（gitignore/submodule）」与「链接写错」，
    缺失类降级为 warning 而非 error，从而可安全进 CI；
  - 门禁规则扩展：目前只查恒真，未覆盖 Batch 208 那类**方向反了**的断言
    （需语义分析，正则难覆盖，可考虑对 `== nodes_before` 类断言要求注释说明）。
