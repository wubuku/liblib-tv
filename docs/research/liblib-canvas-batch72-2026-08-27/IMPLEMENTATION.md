# Batch 72 实施与验证记录

> 状态：`COMPLETE / REFERENCE_DELETE_FOCUSED_PASS`。
>
> 日期：2026-08-27。
>
> implementation checkpoint：`faf9c2d`。

## 1. 实施目标

Batch 71 结束后，Director 最危险的可靠性缺口是 destructive mutation 仍分散在
object、track、path、capture 和 local asset action 中。它们只过滤局部数组，不能
保证 camera relation、group membership、active camera、selection、runtime draft
和 resource reference 同步合法。

本批建立以下 clone-owned command boundary：

```text
delete intent
  -> pure closure planner
  -> strict V1 post-state validation
  -> one registry commit or zero mutation
  -> one Director history entry
  -> runtime/selection/resource reconciliation
```

这不是 LibTV source-exact 删除菜单、确认弹层或快捷键的结论。当前登录态 LibTV
Director 的 source DOM/CSS/delete semantics 仍未充分取得；本批只实现和验证本地
prototype 的数据完整性与可恢复性。

## 2. 代码变更

### 2.1 Pure delete planner

新增 [`directorDeletePlanner.ts`](../../../src/lib/directorDeletePlanner.ts)：

- typed intent：object(s)、group、track、motion path、capture(s)、resource；
- 在任何 store 写入前构造完整工作副本和 inverse-reference closure；
- object 删除会 detach group member、删除 object-owned track/path、修复相机
  look-at/follow、修复 active camera 和 capture camera provenance；
- group 明确支持 `UNGROUP` 和 `CASCADE`；
- track 删除同时删除绑定 path，path 删除会解绑所有 track；
- capture 删除只删除 Director capture descriptor，不删除已发送的普通 canvas node；
- local resource 支持 `BLOCK` 与显式 `CASCADE`；
- candidate resource 只有在 document 中已无 object/capture strong reference 时才
 进入 `resourceEffects`；
- post-state 经过 `normalizeDirectorProjectDocument`，失败返回
  `DIRECTOR_REFERENCE_INVALID`，不会写入输入 document。

### 2.2 Store authority

修改 [`directorStore.ts`](../../../src/store/directorStore.ts)：

- 新增 `deleteDirectorEntity`；
- destructive command 先取消 active gesture，再验证 active owner/session/generation；
- accepted plan 一次恢复完整 portable document，并用一条 history entry 记录
  before/after；
- selection、timeline selected track/keyframe/path/anchor、draft、camera preset、
  phone imported refs 和 capture sidecar 一起重建；
- 删除活动相机时选择稳定 fallback；删除最后相机返回
  `DIRECTOR_LAST_CAMERA_REQUIRED`；
- capture sidecar 现在以 document descriptor 的 camera metadata 为 authority，避免
  删除相机后从内存 archive 恢复旧的 dangling camera ID；
- local model descriptor 只在 resource command accepted 后从 browser storage 移除。

旧的 `removeCapture`、`clearCaptures`、`removeTimelineTrack`、
`deleteMotionPath`、`ungroupSelectedCharacters` 和 local model delete adapter 已
改走统一 command。没有新增绕过 planner 的 destructive writer。

### 2.3 Visible routing

- `DirectorObjectTree` 为对象和分组提供删除按钮；
- 分组删除按钮明确采用 `UNGROUP`，保留成员；
- Director workspace foreground 的 Delete/Backspace 处理当前选择对象或分组；
- editable target、截图 viewer、workspace busy 状态仍优先，不误消费删除键；
- local model library 删除按钮明确是“删除模型及场景实例”，采用显式 `CASCADE`。

## 3. 验证实现

新增：

- [`verify-liblib-batch72.mjs`](../../../scripts/verify-liblib-batch72.mjs)：
  dependency-light pure planner corpus；
- [`verify-liblib-batch72.py`](../../../scripts/verify-liblib-batch72.py)：
  fresh-page Playwright runtime corpus；
- [`runtime-audit.json`](runtime-audit.json)：当前结构化结果。

### 3.1 Pure corpus

覆盖：

1. object group/member detach；
2. object-owned transform/pose track 和 motion path closure；
3. camera look-at/follow repair；
4. active-camera fallback 与 capture camera provenance；
5. last-camera rejection；
6. group ungroup；
7. path delete 与 track detach；
8. local resource block/cascade；
9. capture/resource closure；
10. planner input immutability。

### 3.2 Fresh-page corpus

| 场景 | 结果 |
|---|---|
| foreground Delete/Backspace + exact undo/redo | PASS |
| last-camera reject，zero partial mutation | PASS |
| group/member/track/path/camera reference closure | PASS |
| imported camera delete + capture provenance + graph preservation | PASS |
| local resource `BLOCK` / explicit `CASCADE` + storage cleanup | PASS |

每个场景创建独立 Director owner，普通 canvas graph/history 先记录 baseline。验证结果：

- pure verifier：`PASS`；
- Batch 72 fresh-page：`PASS`；
- console/page/request errors：`0`；
- screenshot writes：`0`；
- ordinary canvas graph/history：未被 Director delete 改变；
- `delete -> undo -> redo`：portable document fingerprint exact round-trip。

## 4. 回归命令

在 `http://localhost:3001` dev server 上运行：

```bash
LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch59.py
LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch67.py
LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch68.py
LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch69.py
LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch70.py
LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch71.py
LIBLIB_BASE_URL=http://localhost:3001 python3 scripts/verify-liblib-batch72.py
npm run docs:check
npm run check
```

最终结果：

- Batch 59、67、68、69、70、71、72：`PASS`；
- `npm run docs:check`：通过；
- `git diff --check`：通过；
- `npm run check`：通过；
- lint：既有 9 条 warning，0 error；
- typecheck/build：通过。

## 5. 失败与修正

| 现象 | 分类 | 修正 |
|---|---|---|
| 新增批次 README 将未来产物写成断链 | documentation defect | 在产物生成前使用 pending filename，完成后再变成链接 |
| 首次提交命令包含被环境策略拒绝的 `rm -rf` | environment/tooling | 改用 `find ... -delete` 与 `rmdir`，未影响代码 |
| fresh audit 写入随机 graph node ID，重复运行产生无意义 diff | verifier determinism defect | 输出稳定语义值 `ordinary-canvas-result-node`，保留 graph preservation 断言 |
| camera 删除后 archive 可能恢复旧 camera ID | sidecar authority defect | `capturesForDirectorDocument` 以 descriptor 的 camera metadata 覆盖 archive metadata |

## 6. 当前边界与下一步

本批关闭 `LIBTV-VR-024` 的 reference-aware delete focused slice，但不关闭整个
Director authority。仍未覆盖：

- capture/export/phone async owner freshness；
- durable project/resource persistence 和跨项目 lease/reachability；
- copy/paste identity remap；
- real mesh/panorama/resource loader；
- 所有旧 Director action 的 typed command migration；
- LibTV authenticated Director source-exact delete UI、confirmation、feedback、
  shortcut copy 和 DOM/CSS。

下一批应在当前保护性 checkpoint 后，优先评估 async result ingress 与 durable
project/resource persistence 的最小合同；不应把本批 clone-owned delete pass
解释成源站功能证据。
