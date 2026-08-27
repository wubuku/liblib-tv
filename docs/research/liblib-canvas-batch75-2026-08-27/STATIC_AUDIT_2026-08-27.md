# Batch 75 Director Clipboard Static Audit

> 状态：`STATIC_AUDIT_COMPLETE / IMPLEMENTATION_PENDING`。
>
> 日期：2026-08-27；代码基线：`ce7b883`。

## 1. 事实分层

| 事实 | 分类 | 结论 |
|---|---|---|
| StoryAI 有 `copySelectedObjects`、`pasteClipboardObjects` 和 `Cmd/Ctrl+C/V` | `UPSTREAM_FACT` | 可借 session clipboard、paste offset、ID map 和快捷键方法 |
| StoryAI 只复制 object/camera/crowd，测试主要覆盖单角色 | `UPSTREAM_LIMIT` | 不能证明 typed timeline/path/group/capture/resource closure |
| Open Canvas packet 只保留 selected nodes 与 internal edges，paste two-pass remap | `OPEN_CANVAS_FACT` | 可借结构化 packet、内部闭包、offset 和 ID map |
| Open Canvas payload 是普通 graph `type/data/edge` | `OPEN_CANVAS_LIMIT` | 不能作为 Director project schema |
| 当前 Director 有 strict V1 document、project-local history、delete planner 和 persistence | `CLONE_FACT` | clipboard 可以建立在 canonical document 之上 |
| 当前 Director 没有 clipboard state、copy/paste action 或 C/V workspace shortcut | `CLONE_FACT` | UI/UX 和 domain command 都缺失 |
| LibTV authenticated Director 的 copy/paste DOM/CSS/shortcut 未取得 | `SOURCE_UNKNOWN` | 本批不得宣称 source-exact surface |

## 2. 当前实体与引用

| 实体 | 需要 remap 的身份/引用 |
|---|---|
| object | object ID、camera `lookAtObjectId`、`followTargetId`、asset ref |
| group | group ID、character IDs |
| track | track ID、object ID、group ID、motion path ID、keyframe IDs、member offset keys |
| motion path | path ID、object ID、anchor IDs |
| resource | stable reference alias；bytes/lease 不复制 |
| capture | 本批不复制；`sentNodeId` 绝不进入 live clipboard projection |

### 2.1 Group closure

`selectedGroupId` 是显式 group owner。copy group 时必须收集：

```text
group
  -> member objects
  -> group track
  -> member object tracks
  -> member motion paths
  -> referenced stable resources
```

普通 object selection 不隐式复制未选中的 group 或其其他成员。

### 2.2 Camera relation

- internal target/follow object：remap 到 pasted object；
- external target/follow object：detach；
- detach 后保留 authored transform，并将 coordinate target 按 paste offset 平移；
- 不复制 active-camera authority；paste 不改变当前 active camera。

### 2.3 Spatial policy

同一 packet 的所有空间值使用相同 deterministic offset：

- object transform position；
- motion-path transform position；
- transform/camera/group keyframe position；
- camera coordinate target。

anchor local coordinates、rotation、scale、pose、speed curve 和时间保持不变。

## 3. Authority 与副作用

| 动作 | document | history | selection | persistence |
|---|---:|---:|---:|---:|
| copy valid selection | 0 | 0 | preserve | 0 |
| copy empty/invalid | 0 | 0 | preserve | 0 |
| paste valid same-project packet | 1 atomic document | 1 | pasted IDs | canonical save |
| paste empty/stale/invalid | 0 | 0 | preserve | 0 |
| undo/redo paste | exact document restore | existing history semantics | restore adapter policy | canonical save |

Clipboard packet 和 paste counter 是 session UI/runtime state，不进入
`DirectorProjectDocumentV1`、history snapshot、browser persistence envelope 或
ordinary `canvasStore`。

## 4. 风险

1. 先 append object 再补 track/path 会产生 partial document；
2. 只 remap object ID 会留下 group/member、track/path、camera dangling ref；
3. 复制 capture 会把历史 `sentNodeId` 错当 live graph projection；
4. local asset bytes 没有 stable lease 时跨 project paste 会悬空；
5. 复用 source project ID 或 clipboard across project 会造成 owner 串线；
6. paste 通过普通 mutation subscriber 提交可能形成多条 history；
7. UI handler 若不尊重 editable/composition，会劫持输入框原生 copy/paste。

## 5. 决策

- 新增 pure `directorClipboard.ts`，packet builder 与 paste planner 都以 strict
  V1 document 为输入；
- store 只保存一个 project-scoped packet 和 paste count；
- same-project 是本批硬边界；跨 project 返回 stale/zero mutation；
- paste 完整 plan 通过 strict normalize 后才写 registry/store/persistence；
- workspace 只增加非 editable 的 `Cmd/Ctrl+C/V`，不脑补可见 toolbar/context
  menu；
- 不新增截图；focused pure + fresh-page verifier 输出结构化 JSON。

