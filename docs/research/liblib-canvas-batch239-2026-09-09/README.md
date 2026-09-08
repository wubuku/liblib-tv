# Batch 239 — 首帧自动图片节点流复刻（源站 2026-09-09 采样落地）

> 状态：`IMPLEMENTED`（batch 237 采样 → 本批实施 → 11 checks 验收 → 31 项回归绿）。
>
> 源站证据：`../liblib-canvas-batch237-2026-09-09/a1-after-firstframe.png` +
> 面板放大截图（本批无新增源站采样，纯实施批次）。

## 复刻范围（对齐源站 `SOURCE_FACT`）

点击视频节点卡「首帧生成视频」尝试芯片后，源站行为的三要素：

1. **自动创建图片节点并连入视频节点**（图片在左、边 image → video）；
2. **面板出现参考槽**（48×55、角标 1）；
3. **说明文案**「以当前图为首帧生成视频。」替代提示词输入框
   （a1 截图直证无 textarea）。

## 实施

### `canvasStore.createFirstFrameReference(videoNodeId)`（新动作）

- 单事务创建图片节点（视频节点左侧，`width+80` 间距）+ 边
  （`sourceHandle: "source"` / `targetHandle: "target"`，同 batch 192 合同）；
- **事务内保持视频节点选中**（`addNodeAtPosition`/`addDerivedNode` 都会把
  选中切到新节点导致面板关闭——故新建专用动作）；
- 单条历史记录（undo 同时回滚节点+边）；
- **防重守卫**：视频节点已有入边图片节点时跳过（芯片重击/面板重挂载
  重放联动均不重复建节点）。

### `VideoNode` 芯片 onClick

`首帧生成视频` 分支调用 `createFirstFrameReference(id)`（与 batch 192
`onSelectEffect` 的画布操作模式同构）。

### `VideoGenerationPanel` 首帧态分支

`attempt === "首帧生成视频"` 时渲染 `data-video-firstframe-slot`
（48×55 槽 + 角标 1，本地 storyboard-2 图）+ `data-video-firstframe-hint`
（以当前图为首帧生成视频。），**替代**引用槽行与提示词 textarea。

### `CLONE_DECISION`（未复刻差异）

- 槽缩略图/图片节点内容：源站为自动带入的示例图（蓝色跑车），clone 使用
  本地素材图与空编辑器图片节点（无对应本地资产）；
- 说明文案字号/间距按截图目测（15px/leading-6），未逐像素校准。

## 验收

- `verify-liblib-batch239.py`：**11 checks**（增量 +1 节点 +1 边；边方向
  image→video；面板槽 48×55/角标；说明文案逐字；首帧态无 textarea；模式
  触发器 全能参考（batch 237 合同）；面板保持打开；芯片重击防重）。
- 回归绿：21 / 22 / 26 / 33 / 100 / 111 / 128 / 141 / 145 / 146 / 149 /
  151 / 155 / 160 / 165 / 166 / 172 / 173 / 174 / 175 / 176 / 177 / 178 /
  189 / 191 / 213 / 215 / 218 / 236 / 237 / 238（31 项）。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 无源站操作（纯实施批次，无残留问题）。

## 不证明 / 后续候选

- 首尾帧生成视频芯片的对应流（源站未采到——芯片一次性消失）；
- 自动创建图片节点的素材来源机制（源站示例图选取规则）；
- 其余约 30 个模型族的平价率与清晰度列表采样（batch 238 遗留）。
