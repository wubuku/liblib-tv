# Batch 52 计划：当前图片工具条与只读预览

> 建档日期：2026-08-26
> 对应 backlog：`LIBTV-PAR-001` action set、`LIBTV-PAR-002` Preview slice

## 1. 缺口与价值

| 项目 | 当前 clone | 当前源站合同 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 标准工具条 | 7 个文字动作 + 撤销/重做 | 9 个文字动作 + 4 个图标动作 | 5 | 更新 |
| toolbar 外框 | `900.5x49` | 当前快照 `1092.5x49`、`w-fit` | 5 | 更新当前动作快照 |
| 元素编辑/图层分离 | 无独立身份 | 两个 `88x32` 文字入口 | 5 | 补入口，不伪造任务 |
| 标注/旋转/下载/预览 | 撤销/重做替代 | 四个 `32x32` 图标入口 | 5 | 修正身份 |
| Preview | 无 | page-level 只读 overlay | 5 | 完整实现 |
| active authoring tools | 无状态模型 | 替换标准双浮层 | 5 | 后续独立 batch |

## 2. 实施顺序

1. 将 `ImageToolbar` 拆成有稳定 id、source test id、宽度和类别的动作描述；
2. 按源站顺序渲染 9 个文字按钮和 4 个 icon-only 按钮；
3. 保留已有低风险 clone 动作，但不再把末端按钮解释为撤销/重做；
4. 在 `uiStore` 建立 page-level image preview state；
5. 新增 `ImagePreviewOverlay`，按 `85vw x 80vh` stage、媒体 contain、
   `-12px` close button 和水印 offset 实现；
6. 让 Preview active 时普通画布 Delete/Space/Tab/undo 等快捷键不穿透；
7. close button 和 Escape 只关闭 Preview，不改变 selection、Prompt、
   nodes、edges 或 history；
8. 新增 Batch 52 focused Playwright 和结构化 runtime audit。

## 3. 高风险动作处理

本批不能把以下入口统一走 `addDerivedNode`：

| 动作 | 已知源站风险 | 本批状态 |
|---|---|---|
| 元素编辑 | local records 后才允许生成/任务 | 可见入口，等待专用空态 batch |
| 图层分离 | splitting/redrawing/merging 和任务链 | 可见入口，禁用提交 |
| 标注 | 专用 toolbar + DPR canvas + dirty/save | 可见入口，等待空态 batch |
| 旋转 | 当前共享 fixture 已证明入口可能创建派生节点 | 可见入口，禁用提交 |
| 下载 | 水印偏好、会员和浏览器文件副作用 | 可见入口，禁用下载 |

未完成动作必须保持稳定的按钮身份和可访问名称，但不能显示虚假的完成结果。

## 4. Preview 合同

- owner 是 page shell，不挂在 React Flow transform 内；
- overlay `fixed inset-0`、`bg-black/80`，覆盖整个 viewport；
- content viewport 为 `85vw x 80vh`，媒体保持原始比例并 contain；
- close button 为 `32x32`，位于 content 右上方各外扩 `12px`；
- 水印相对实际媒体左上角偏移 `10px`，尺寸 `48x23`；
- overlay 打开和关闭都不改变 graph/selection；
- Escape 与 close button 等价；
- Preview active 时底层画布快捷键不执行；
- 保留可访问 `role=dialog`、`aria-modal`、label 和关闭按钮名称，不复制源站
  缺失 accessible name 的缺陷。

## 5. 验收门

### 工具条

- 13 个 button，顺序和 source test id 完全一致；
- 外框 `1092.5x49px`；
- 9 个文字按钮和 4 个 icon button 的测量宽度符合 source audit；
- node center、`10 + 24 * zoom` gap、自然裁切继续满足 Batch 51；
- 多选和空白点击仍卸载单节点工具条。

### Preview

- overlay rect 等于 viewport；
- `929x874` 下 content 为约 `789.65x699.2`；
- 2:1 fixture 图片为约 `789.65x394.82` 并垂直居中；
- close 为 `32x32`，相对 content `right/top=-12px`；
- close 和 Escape 后 selected node、node/edge count、Prompt 和 viewport 不变；
- Preview active 时 Delete/Space/Tab/Ctrl+Z 不影响底层画布；
- 无 console/page/request error。

### Repository

- focused verifier 通过；
- Batch 9、10、51 及相关 overlay lifecycle 回归通过；
- `python3 scripts/verify-docs.py`、`git diff --check`、`npm run check` 通过；
- 历史截图若被 verifier 重写，必须在 commit 前恢复；
- 计划、代码、实施结果分别形成保护性 commit 并 push。

## 6. 后续队列

1. Batch 53：空标注替换态；
2. Batch 54：元素编辑空态；
3. 下载、旋转、图层分离必须等待各自可验证的副作用边界，不与空态批次捆绑。

## 7. Closeout

本计划已于 2026-08-26 实施完成。结果、回归命令、截图账本、runtime audit
和提交历史见 [`IMPLEMENTATION.md`](IMPLEMENTATION.md)；后续接力前先读
[`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)，不要重复识别本批截图。
