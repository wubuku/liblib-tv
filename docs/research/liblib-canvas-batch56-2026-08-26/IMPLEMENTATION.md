# Batch 56 实施记录：图片旋转入口的最小派生节点复刻

> 状态：实施中。
> 本文记录代码变更、验证结果和边界。源站事实与 clone-only 决策见
> [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)；本批计划见 [`PLAN.md`](PLAN.md)。

## 1. 实施范围

本批只实现一个可重复的本地 graph slice：

```text
selected image with media
  -> click 旋转
  -> add image node: 旋转与镜像
  -> add source -> derived edge
  -> select derived node
  -> undo/redo the complete transaction
```

保留以下边界：

- 不旋转或镜像真实 bitmap；
- 不引入 angle、horizontal-flip 或 vertical-flip 控件；
- 不触发上传、任务、积分、保存或远程 provider；
- 无 `imageUrl` 的图片仍 disabled/no-op；
- 派生节点复用 source URL 只是本地可见 fixture，不代表处理结果。

## 2. 预定代码变更

| 文件 | 变更 |
|---|---|
| `src/components/ImageToolbar.tsx` | 让旋转入口按当前图片是否有媒体动态启用 |
| `src/components/nodes/ImageNode.tsx` | 增加 typed `rotateMirror` metadata 和独立旋转 dispatch |
| `src/store/canvasStore.ts` | 仅复用现有 `addDerivedNode` 原子 node/edge/history 路径，不改 store API |
| `scripts/verify-liblib-batch56.py` | 新增 desktop/mobile、graph、selection、history、no-media 和 overflow 断言 |
| `docs/research/components/ImageNode.spec.md` | 更新旋转动作与 metadata 合同 |
| `docs/research/README.md`、`docs/HARNESS.md` | 加入 Batch 56 研究和 verifier 入口 |
| `docs/research/VERIFICATION_LEDGER.md` | 记录本批验证成熟度和限制 |
| `docs/research/LIBTV_UIUX_PARITY_BACKLOG.md` | 更新 `LIBTV-PAR-002` 的旋转子项状态 |
| `CHANGELOG.md` | 记录本地有界旋转入口复刻 |

若实际实施不需要某项变更，将在 closeout 中说明，不为形式而扩大 diff。

## 3. 实施与验证记录

| 阶段 | 状态 | 记录 |
|---|---|---|
| 计划与源站证据 | 已完成 | `PLAN.md`、`SOURCE_EVIDENCE.md` |
| 代码实现 | 待执行 | 仅允许本批列出的文件 |
| 截图识别台账 | 已建档 | `SCREENSHOT_ANALYSIS.md`，实施后追加实际截图 |
| Batch 56 focused verifier | 待执行 | 目标：desktop/mobile 与 graph transaction |
| 相邻回归 | 待执行 | Batch 52、53、54，必要时 Batch 20/29 |
| `npm run check` | 待执行 | lint、typecheck、production build |
| docs/diff 检查 | 待执行 | `verify-docs.py`、`git diff --check` |
| commit/push | 待执行 | 完成验证后记录 commit SHA |

## 4. 失败与修正记录

尚无本批实施失败。任何因旧 dev server、viewport 裁切、selector 或 history
边界导致的失败，都必须在这里记录根因、修正和重新运行的命令。

## 5. 提交历史

| Commit | 内容 | 状态 |
|---|---|---|
| 待定 | Batch 56 计划、证据、实施和截图台账 checkpoint | 待提交 |
| 待定 | Batch 56 代码实现 | 待提交 |
| 待定 | Batch 56 verifier、回归和 closeout | 待提交 |
