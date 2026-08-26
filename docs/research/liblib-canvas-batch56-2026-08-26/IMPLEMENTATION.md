# Batch 56 实施记录：图片旋转入口的最小派生节点复刻

> 状态：已完成（2026-08-26）。本批完成的是源站已观察到的旋转入口
> graph delta，不声称完成真实 bitmap 旋转或镜像编辑器。
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

## 2. 实施结果

| 文件 | 变更 |
|---|---|
| `src/components/ImageToolbar.tsx` | 新增 `hasMedia` 门控；有媒体的图片启用旋转，无媒体保持 disabled |
| `src/components/nodes/ImageNode.tsx` | 增加 typed `RotateMirrorMetadata`、独立旋转 dispatch 和稳定 `data-*` 证据标记 |
| `scripts/verify-liblib-batch56.py` | 新增 desktop/mobile、graph、selection、history、no-media 和 overflow 断言 |
| `runtime-audit.json` | 保存本批结构化运行结果 |
| `docs/design-references/liblib-clone-batch56-*.png` | 保存创建后 selected 派生节点的 desktop/mobile 截图 |

明确未修改 `canvasStore`：复用现有 `addDerivedNode` 已能保证 node、source
edge、selection 和 history 的单事务边界。

## 3. 验证记录

| 阶段 | 状态 | 记录 |
|---|---|---|
| 计划与源站证据 | 已完成 | `PLAN.md`、`SOURCE_EVIDENCE.md` |
| 代码实现 | 已完成 | media-gated rotate + `rotateMirror` typed metadata |
| 截图识别台账 | 已完成 | `SCREENSHOT_ANALYSIS.md`，只识别本批两张新截图 |
| Batch 56 focused verifier | 已通过 | desktop/mobile、派生 graph、selection、metadata、undo/redo、no-media、overflow |
| 相邻回归 | 已通过 | Batch 52、53、54、20、29 串行通过 |
| `npm run check` | 已通过 | lint 0 error/9 existing warnings、typecheck、production build |
| docs/diff 检查 | 已通过 | 463 Markdown / 1955 local targets；`git diff --check` clean |
| commit/push | 待执行 | 完成验证后记录 commit SHA |

实际运行命令：

```text
python3 scripts/verify-liblib-batch56.py
python3 scripts/verify-liblib-batch52.py
python3 scripts/verify-liblib-batch53.py
python3 scripts/verify-liblib-batch54.py
python3 scripts/verify-liblib-batch20.py
python3 scripts/verify-liblib-batch29.py
npm run check
python3 scripts/verify-docs.py
git diff --check
```

Batch 52 的 media-backed fixture 原先仍断言 `旋转` disabled。该历史断言已按
Batch 56 当前合同迁移为 enabled，并在 Batch 52 `IMPLEMENTATION.md` /
`SOURCE_EVIDENCE.md` 中留下 supersession note；无媒体 disabled/no-op 继续由
Batch 56 专项 verifier 负责。

## 4. 失败与修正记录

### 4.1 Playwright Python API

首次运行使用了旧式 positional `wait_for_function` 参数，当前 Playwright
要求使用 `arg=` 关键字。已修正 `scripts/verify-liblib-batch56.py` 并重新运行
通过。

### 4.2 派生节点媒体 selector

节点内同时包含主图和 watermark 两个 `img`，初版“恰好一个 img”断言过窄；
已改为检查主图 `alt="旋转与镜像"`。

### 4.3 React Flow overlay owner

`NodeToolbar` 和 `ImageEditPanel` 挂在 React Flow 节点外层，而不是自定义节点
根内部。verifier 已改为全局唯一 overlay 断言，保留节点本地媒体和 metadata
断言。

### 4.4 截图状态

初版截图在 redo 后采集，selection 已按现有 history 合同清空，不能证明创建后
选中态。已将截图采集点前移到派生节点创建后、undo 前，并重新生成/识别。

## 5. 结果边界

已完成：

- 有媒体图片的 `旋转` 入口可用；
- 创建名为 `旋转与镜像` 的 image 派生节点；
- 创建 source -> derived edge；
- 创建后自动选中派生节点；
- `rotateMirror` metadata 可被 DOM 和 runtime audit 检查；
- 一次 undo/redo 恢复/撤销整个 graph transaction；
- 无媒体图片保持 disabled/no-op；
- desktop/mobile 不产生页面横向滚动；
- 本地 prototype 复用 source image URL 以保持可见媒体。

仍未完成且不能由本批推出：

- 真实旋转 bitmap、角度值和镜像结果；
- 水平/垂直镜像控件、旋转面板和 dirty/save/discard；
- 下载、上传、任务轮询、积分、provider 或远端持久化；
- 源站派生节点最终尺寸、水印策略和结果状态；
- 图层分离与旋转的共同 task/save 语义。

## 6. 提交历史

| Commit | 内容 | 状态 |
|---|---|---|
| `3d2ef4b` | Batch 56 计划、证据、实施和截图台账 checkpoint | 已 push |
| 待定 | Batch 56 代码实现、verifier、runtime audit 和全局索引 | 待提交 |
