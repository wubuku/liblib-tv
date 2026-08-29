# Batch 91 实施与验证记录

> 状态：`FOCUSED_RUNTIME_RECORDED_PASS`
>
> 日期：2026-08-29。

## 1. 实施范围

本批承接 Batch 90 的 scene command，处理 Director 高频 direct writers：

- `updateObject`：name、color、visible、locked 的类型/值校验、no-op、
  locked guard、canonical document、persistence 和一条 history；
- `updateCamera`：FOV/tuple/reference/follow 字段校验、no-op、locked guard、
  authored/runtime projection、camera keyframe 和一条 history；
- `groupSelectedCharacters`：角色组创建、selection 结果、document/persistence
  和一条 history；
- `updateGroup`：label trim、no-op/invalid、timeline label 同步和一条 history；
- `updateGroupTransform`：有限值/正 scale 校验、authored/runtime projection、
  gesture defer 和一条 history；
- Director 对象名和分组名使用 DOM draft，Enter/blur 才调用 command。

新增共用 `commitDirectorMutation` helper，收敛 registry update、browser-local
persistence、history entry 和 command result 的重复逻辑。活动手势期间，该
helper 不提前写 canonical persistence/history，由 `commitDirectorGesture`
负责最终提交。

## 2. 验证命令

```bash
node --experimental-strip-types scripts/verify-liblib-batch91.mjs
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch91.py
```

回归基线：

```bash
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch88.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch89.py
LIBLIB_BASE_URL=http://localhost:4317 python3 scripts/verify-liblib-batch90.py
```

## 3. 证据边界

本批通过只能证明 clone-owned Director command/history/persistence 可靠性，
不能证明 LibTV 原站使用相同的 API、字段、history policy、默认值、DOM/CSS
或视觉布局。`updateObject`/`updateCamera`/group action 在普通应用层仍是
prototype store contract，不是 backend 或 remote collaboration protocol。

## 4. 验证结果

Batch 91 pure/source verifier 通过 10 项断言；fresh-page Playwright verifier
覆盖对象名称 draft、对象 visibility command、相机 FOV/keyframe、
same-value no-op、非法 follow reference、角色组创建/重命名/变换、非法 scale
zero-history 和 persistence，browser diagnostics 为 `0 / 0 / 0`。

Batch 88、89、90 changed-slice regression 均通过，`npm run typecheck` 和
`git diff --check` 通过。Batch 89/90 历史 runtime audit 的测试随机 ID/时间戳
已恢复，未把验证副作用混入本批 checkpoint。

## 5. 当前限制与下一批入口

- `addCrowdArray`、`addModelLibraryObject`、pose/timeline/path 的部分旧入口仍
  由 subscriber 兜底形成 `PROJECT_MUTATION`，尚未全部改成显式 typed command；
- `commitDirectorMutation` 在活动 gesture 中只返回零 history 的 transient
  result，由 `commitDirectorGesture` 完成最终 document/persistence/history；
- 本批仍不证明 LibTV 原站 Director 的 exact command API、history policy、
  persistence、DOM/CSS 或视觉行为；
- Batch 92 继续处理 local resource descriptor、attempt freshness、lease 与
  materializer 的 command/生命周期一致性。
