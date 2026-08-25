# Batch 23：片段重拍时间带与 Prompt 编辑器

> 状态：已实施；专项 Playwright、Batch 9-23 跨批回归和完整工程门禁均通过。

## 当前缺口

当前 clone 把片段计数、时间带和关闭按钮塞进一个自创的 `660x286` 标题面板，并要求用户必须输入修改意图后才能提交。原站流程图显示时间带是编辑器上方的独立层，编辑器本身沿用生成器的“参考 / 标记 / 角色库 + Prompt + footer”结构；当前线上 bundle 还明确支持“留空 = 原样重跑一次”。

## 本批范围

- 把 4 秒片段时间带从编辑器面板中拆成独立上层；
- 移除没有源证据的“片段重拍”标题栏；
- 增加 source-shaped 参考视频缩略项、inline 视频/range token 和生成器 footer；
- 保留 `0/5` 到 `5/5` 的片段选择上限；
- 修正空意图提交语义；
- 只产生本地任务反馈，不伪造重拍结果或模型调用。

## 阅读顺序

1. [`PLAN.md`](PLAN.md)
2. [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)
3. [`SEGMENT_RESHOOT_EDITOR.spec.md`](SEGMENT_RESHOOT_EDITOR.spec.md)
4. [`IMPLEMENTATION.md`](IMPLEMENTATION.md)

## 证据

- [source article flow](../liblib-seedance-2.5-2026-08-25/evidence/segment-reshoot-flow.png)
- [`live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)
- [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)
- 当前组件规格：[`../components/SegmentReshootPanel.spec.md`](../components/SegmentReshootPanel.spec.md)
- [clone whole rerun](../../design-references/liblib-clone-batch23-segment-reshoot-default-929-2026-08-25.png)
- [clone five ranges + intent](../../design-references/liblib-clone-batch23-segment-reshoot-selected-929-2026-08-25.png)
- [clone mobile](../../design-references/liblib-clone-batch23-segment-reshoot-mobile-390-2026-08-25.png)
- [clone contact sheet](../../design-references/liblib-clone-batch23-segment-reshoot-contact-sheet-2026-08-25.png)
- 可执行验证：[`scripts/verify-liblib-batch23.py`](../../../scripts/verify-liblib-batch23.py)

## 完成结果

- 时间带从 editor 内部拆成独立 `660x56` surface；下方 editor 为 `660x252`。
- 移除自创标题栏，补齐生成器命令、源视频缩略项、视频 token 和 range chips。
- 7 个 `4.0s` 区间、disabled `2.0s` remainder 和五段上限受自动化保护。
- 空意图现在可以创建本地整段重跑任务，不再违背线上 bundle 语义。
- 390px 下保持节点锚定与自然裁切，不引入 document overflow。
- 所有提交和结果仍是本地原型，不声称真实模型或视频处理已经发生。
