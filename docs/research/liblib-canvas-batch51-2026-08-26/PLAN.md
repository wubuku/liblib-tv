# Batch 51 计划：普通画布图片顶部工具条几何 parity

> 建档日期：2026-08-26
> 对应 backlog：`LIBTV-PAR-001`

## 1. 缺口与价值

| 审计项 | 当前 clone | 当前源站证据 | 价值 | 本批决策 |
|---|---|---|---:|---|
| 顶部工具条横向 anchor | `NodeToolbar align=center` | 与节点 screen center 对齐 | 5 | 保持 |
| 顶部 host 垂直公式 | 固定 `offset=16` | `nodeTop - 24 * zoom - 10`，再 `translateY(-100%)` | 5 | 修正 |
| 底部编辑面板 | 节点内 inverse scale | `660px` screen width，gap `16 * zoom` | 5 | 不改 |
| viewport 边缘 | 允许自然裁切 | 源站无 clamp | 4 | 不改 |
| 当前 action set | 7 个文字动作 + 撤销/重做 | 9 个文字动作 + 标注/旋转/下载/预览 | 5 | 本批只记录，另立动作状态 batch |

## 2. 证据边界

### 已有高置信证据

- [`../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_OVERLAY_MULTIZOOM_MATRIX.md)
  记录 2026-08-26 的 28%/34%/41%/50% source DOM rect 与 production
  bundle host 公式；
- [`../components/LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md)
  固化同一 frame、同一 viewport snapshot、自然裁切和双浮层关系；
- [`../components/ImageNode.spec.md`](../components/ImageNode.spec.md)
  固化 clone 的 ImageNode / ImageEditPanel ownership；
- Batch 9 verifier 提供 clone 的图片/视频锚定、pan/zoom、多选和手势隔离基线。

### 本轮不新增的证据

当前会话没有可调用的 in-app/headed browser control tool，因此不把
LibTV authenticated source 的新一轮 freshness 观察写成 `SOURCE_FACT`。
已有 source evidence 继续有效，但 source 部署漂移、Director shell
“全屏”语义和当前 action set 的后续变化仍需有头浏览器可用时只读复核。

## 3. 实施范围

1. `ImageToolbar` 接收当前 React Flow `zoom`；
2. 用 `10 + 24 * zoom` 计算 `NodeToolbar` 的 top offset；
3. 更新 Batch 9 图片断言，使其检查 source-confirmed 公式；
4. 新增窄的 Batch 51 verifier，覆盖 28%、38% 和 pan 后同一 frame 的
   node/toolbar/panel anchor；
5. 记录 DOM 测量和截图文件，不进行重复视觉识别；
6. 更新组件规格、backlog、verification ledger 和研究索引。

## 4. 不做

- 不修改 `ImageEditPanel` 的底部公式；
- 不把旧 `撤销 / 重做` 按钮声称为源站的标注/旋转/下载/预览；
- 不实现 active image tool、preview overlay、AutoLink structured mention；
- 不修改视频工具条、FrameOS、Director 或共享源站项目；
- 不新增 clamp、collision avoidance、page-level fixed portal。

## 5. 验收标准

对标准图片选中态，在同一 frame 读取 node、toolbar、panel 和 viewport：

- toolbar 与 node center 误差 `<= 1px`；
- toolbar bottom 到 node top 为 `10 + 24 * zoom ± 1px`；
- toolbar 宽度/高度保持当前 clone action set 的 `900.5 × 49px`；
- panel 与 node center 误差 `<= 1px`；
- panel bottom gap 为 `16 * zoom ± 1px`，宽度 `660px`；
- pan、zoom 不改变 graph node/edge 数量；
- 多选和空白点击仍卸载单节点双浮层；
- 控制台和 page error 为零；
- `npm run check`、`python3 scripts/verify-docs.py` 和本批脚本通过。

## 6. 提交门

- 代码与窄 verifier 先形成一个保护性 commit；
- 文档、截图台账和验证结果形成 closeout commit；
- 每个 commit 都 push 到 `origin/master`；
- closeout 后工作区必须为空。
