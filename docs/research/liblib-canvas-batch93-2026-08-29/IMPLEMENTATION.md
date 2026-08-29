# Batch 93 实施与验证记录

> 状态：`FINAL_REGRESSION_RECORDED_PASS`
>
> 日期：2026-08-29。
>
> 本批完成后停止，不启动 Batch 94。

## 1. 实施范围

Batch 93 不新增产品功能，完成最终回归和文档治理收口：

- 建立 fresh-page Director 桌面/移动端专项 verifier；
- 运行普通画布跨批回归；
- 运行 Director Batch 59、67-92 current gates；
- 更新 current verifier manifest、verification ledger、fixture catalog、
  traceability、Harness、component coverage、Research Hub、Documentation Hub、
  Agent Task Map 和 Big Picture；
- 运行项目、文档和 diff 全量检查。

固定服务为 `http://localhost:4317`。本批没有创建 worktree，也没有写入截图。

## 2. 专项桌面/移动端回归

新增：

```bash
LIBLIB_BASE_URL=http://localhost:4317 \
  python3 scripts/verify-liblib-batch93.py
```

脚本使用两个独立 BrowserContext：

- 桌面 `1440x900`：workspace/session diagnostics、R3F canvas nonblank、对象
  树、Inspector、Timeline、侧栏折叠/恢复、close/reopen 和横向溢出；
- 移动端 `390x844`：workspace、R3F canvas、tree/Inspector drawer、Timeline、
  drawer open/close、组件及 document/body 横向溢出；
- 两端都收集 console error、page error 和 request failure；
- static contract 检查 workspace/mobile panel/tree/timeline/eventSource/
  owner-scoped lease 入口可发现。

结果：

- desktop：全部通过，WebGL 非空，close/reopen 后 object/track 数量保持；
- mobile：全部通过，tree/Inspector drawer 可发现且无横向溢出；
- diagnostics：desktop/mobile 均为 `console=0, page=0, request=0`；
- `screenshotsWritten=false`，没有消耗截图识别预算。

结构化结果见 [`runtime-audit.json`](runtime-audit.json)。

## 3. 普通画布跨批回归

串行运行：

```text
Batch 57, Batch 60, Batch 61, Batch 63, Batch 64, Batch 65, Batch 77
```

覆盖 graph connection transaction、图片双浮层 owner/命中边界、React Flow
change routing、actual-host placement、Asset drawer resize anchor、responsive
viewport bootstrap、source-aligned navigation 和 Director TransformControls
pointer drag。全部通过，没有发现 Director resource/session 改动破坏普通画布
行为。

## 4. Director current gate 回归

串行运行：

```text
Batch 59, Batch 67, Batch 68, Batch 69, Batch 70, Batch 71, Batch 72,
Batch 73, Batch 74, Batch 75, Batch 76, Batch 77, Batch 78, Batch 79, Batch 80,
Batch 81, Batch 82, Batch 83, Batch 84, Batch 85, Batch 86, Batch 87,
Batch 88, Batch 89, Batch 90, Batch 91, Batch 92
```

其中：

- Batch 67 通过 strict Project Document V1 codec；
- Batch 68-81 通过 owner/session、authored/runtime、history、pointer、
  reference delete、async、persistence、clipboard、reachability、duplicate、
  tombstone、import/export；
- Batch 82/92 的 pure lifecycle verifier 和 fresh-page verifier 均通过；
- Batch 83-91 的 feedback、lock/editability、selection/CRUD、transform、
  restore-selection、timeline authority、scene command 和
  object/camera/group command 均通过；
- Batch 77 的普通导航和 Director gizmo pointer slice 在跨批回归中再次通过。

Batch 82 历史 verifier 的 `attempt >= 1` 兼容性适配已在 Batch 92 记录；本批
确认适配后的脚本仍然通过。详细 sequence 和执行边界见
[`current-gate-regression.json`](current-gate-regression.json)。

## 5. 全量检查

本批最终执行：

```bash
npm run check
npm run docs:check
python3 scripts/verify-docs.py
git diff --check
```

全部通过。`npm run check` 的既有 lint warning 没有新增 error；文档链接检查
结果见最终命令输出和提交前状态记录。

## 6. 证据边界与停止条件

本批通过证明：

- 当前 clone 在固定 `4317` 服务上的 Director 桌面/移动端结构和运行时没有
  发现回归；
- 已选普通画布跨批 slices 未被破坏；
- Batch 59、67-92 current gates 在当前 HEAD 上通过；
- 文档、代码入口、verifier 和治理台账可互相发现。

本批不证明 LibTV 原站 Director 的 exact DOM/CSS、资源协议、project/session/
history 语义、远程持久化、触摸板硬件行为或 source parity。Batch 93 完成后
停止，等待后续用户指示。
