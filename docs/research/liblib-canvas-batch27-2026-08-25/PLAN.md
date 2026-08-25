# Batch 27 计划：智能去字幕两模式工作流

## 1. 缺口与价值排序

| 候选 | 当前 clone | 当前原站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 智能/框选去字幕 | 菜单 + 临时文字 | 完整入口、编辑器、region store、graph handoff | 5 | 本批实施 |
| 音频分离 | 菜单 + 临时文字 | 多输出节点和任务状态可确认 | 4 | 后续候选 |
| 画面编辑 | 菜单 + 临时文字 | 多种选择工具与生成流程，范围较大 | 4 | 后续拆批 |
| 首尾帧/当前帧 | 未实现入口 | 节点创建与上传依赖较多 | 3 | 后续候选 |

去字幕是当前最高价值缺口：入口已经存在，用户可直接触发错误反馈；同时原站证据覆盖 UI、状态、参数和图拓扑，实施时不需要脑补主要交互模型。

## 2. 实施步骤

1. 重构 `VideoProcessingToolbar`：
   - 保留 dropdown；
   - 两项分别传出 `smart` / `region`；
   - tooltip 使用 `AI一键去除视频字幕，仅支持中英文字幕`；
   - 删除 subtitle 分支的临时 `lastAction`。
2. 新增 `SubtitleErasePanel`：
   - node-relative centered；
   - source `absolute -bottom-4` 语义；
   - `48px` 高紧凑条；
   - close、divider、模式名、积分占位、`28x28` submit；
   - region 模式增加 help、选择区域、undo、redo、reset。
3. 新增 region editor：
   - 相对坐标矩形；
   - 激活后空白拖拽创建多个区域；
   - 单选、拖动、四角 resize；
   - undo/redo/reset；
   - region 为空时 submit disabled。
4. 扩展 `VideoNode`：
   - subtitle 模式打开时隐藏普通 generator 和顶部处理工具条；
   - region overlay 覆盖视频画面；
   - close / Escape 清 session 并返回 generator。
5. 扩展 `canvasStore`：
   - 新增 `createSubtitleErase` 单事务；
   - 创建右侧 pending video 和 source-to-target edge；
   - 保存 mode、regions、source 和 edge metadata；
   - target 自动单选；
   - undo/redo 一次恢复整批图变化。
6. 新增 `scripts/verify-liblib-batch27.py`：
   - menu、tooltip、smart panel；
   - region create/multi-select/move/resize；
   - undo/redo/reset/disabled submit；
   - target title、pending copy、edge、metadata；
   - graph undo/redo；
   - zoom、drag、pan、多选、390px clipping；
   - screenshot、console/page errors。

## 3. 事实边界

### Source fact

- 顶部入口是 dropdown，选项为 `智能去字幕` / `框选去字幕`。
- tooltip 为 `AI一键去除视频字幕，仅支持中英文字幕`。
- 下方面板使用 `absolute -bottom-4 left-1/2 w-max` 和 `translate-y-full`。
- panel 使用 `px-2 py-2`，close 为 `32x32`，submit 为 `28x28`。
- region 模式增加 help、选择区域、undo、redo、reset。
- region overlay 支持多个矩形、选中、移动、八向 resize 和右键删除。
- region submit 在没有矩形时 disabled。
- smart 参数 mode 为 `Subtitle`；region 参数 mode 为 `Text`，并携带 `erase_ratio_location`。
- submit 创建右侧 `SUBTITLE_ERASE` video 和 edge。
- target 名称为 `视频一键去字幕-{nodeLabel}`。
- target pending 文案按模式分别为 `点击生成自动去除字幕` / `框选区域生成去字幕视频`。

### Inference

- clone 沿用既有 inverse-scale 节点浮层技术，用 `-bottom-[17px]` 补偿节点 `1px` border，使外部间距对应 source 的 `-bottom-4` 语义。
- target 使用当前 video node 的 `pending` 分支，不模拟真实 loading progress。
- 原站 region store 是跨组件状态；clone 可以把 session history 封装在 `SubtitleErasePanel` 内，只要卸载时完整清理。

### Clone-only decision

- 区域 ID 使用本地递增值。
- 最小区域边长采用相对画面尺寸的 `0.02`，避免零面积矩形。
- 积分显示使用 `-`，不请求计费接口。
- 本地 submit 永久保留 pending target，不模拟成功、失败或自动删除。
- 不保存跨刷新 session。

## 4. 验收标准

- subtitle 菜单不再写入临时文字。
- smart 模式只显示 `[data-subtitle-erase-panel]`，不显示普通生成器。
- region 模式同时显示 panel 和 `[data-subtitle-region-overlay]`。
- panel 高 `48px`；close `32px`；submit `28px`；节点中心对齐。
- region 可创建至少两个矩形，选中态清晰，移动和 resize 修改相对坐标。
- undo/redo/reset 按钮状态正确；reset 可被 undo。
- region 为空时 submit disabled；smart submit enabled。
- submit 一次增加一个 pending video 和一条 edge，且 target 被单选。
- target 名称和模式文案正确，metadata 保存 smart/region 语义。
- graph create 可由一次 undo/redo 完整回退/恢复。
- 50% zoom 后 panel 仍保持屏幕尺寸，并随节点 drag/pan 移动。
- 多选隐藏单节点工作流；390px 下自然裁切且 document 无横向 overflow。
- Batch 9、21、23、25、26、27 与完整工程/文档门禁通过。
