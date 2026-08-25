# Batch 28 计划：音视频分离多输出工作流

## 1. 缺口与价值排序

| 候选 | 当前 clone | 当前原站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 音视频/人声/背景音分离 | 错误菜单 + 临时文字 | menu、busy、guard、双输出 graph 完整 | 5 | 本批实施 |
| 画面编辑 | 菜单 + 临时文字 | 主体消除/修改/替换、抠像，范围较大 | 4 | 后续拆批 |
| 首尾帧/当前帧 | 未实现 toolbar group | 截帧与节点创建可确认 | 4 | 后续候选 |
| 深度动作捕捉 | 未实现 | dialog、校验与派生节点可确认 | 4 | 后续候选 |

音视频分离是当前最优项：入口已经存在且直接产生错误反馈；当前 bundle 同时覆盖菜单集合、busy、guard、节点命名、连接方向、选择和 history，主要交互模型不需要猜测。

## 2. 实施步骤

1. 重构 `VideoProcessingToolbar`：
   - label 改为 `音视频分离`；
   - menu 改为 `音视频分离 / 人声提取 / 背景音提取`；
   - 移除当前不可见的 `音效提取`；
   - 增加 stable selectors；
   - busy 时 spinner + `分离中`，禁用 entry 并隐藏 chevron；
   - `音视频分离` item 增加 source tooltip。
2. 扩展 `VideoNode`：
   - 维护短生命周期 `audioSplittingMode`；
   - action 期间保持 toolbar 可见但进入 busy；
   - timer 结束后调用 store graph transaction；
   - pending silent-video 使用独立 audio-split body，不进入 subtitle body。
3. 扩展 `canvasStore`：
   - 新增 `AudioSplitMode` / `AudioSplitMetadata`；
   - 新增 `createAudioSplit`；
   - 创建 audio + silent video；
   - 两条 edge 都从 source 发出；
   - 最右侧 silent video 自动单选；
   - 整批变化只记录一个 history snapshot。
4. 扩展 `AudioNode`：
   - 显示音轨/人声/背景音来源；
   - 暴露 mode、source 和 output-kind selectors；
   - 保留本地 waveform 和 prototype 边界。
5. 新增 `scripts/verify-liblib-batch28.py`：
   - menu 顺序、文案、tooltip、无 sfx；
   - busy spinner/label/disabled；
   - 三种 mode 的 output labels、metadata、node/edge counts；
   - source-to-output edge direction；
   - target selection 和 geometry；
   - graph undo/redo；
   - action 互斥、多选隐藏、zoom/pan、390px overflow；
   - screenshots、console/page errors。

## 3. 验收标准

- toolbar trigger 为 `音视频分离`。
- dropdown 只有三项，顺序为音视频、人声、背景音；不存在音效。
- 点击后 trigger 进入 `分离中`，spinner 可见，按钮 disabled。
- 每个 mode 完成后一次新增两个节点和两条 edge。
- audio 与 silent video 都直接连接 source。
- audio 位于 source 右侧，silent video 位于 audio 右侧。
- 最终只选择 silent video。
- 命名：
  - av：`${source}_音轨`；
  - vocals：`${source}_人声`；
  - background：`${source}_背景音`；
  - video：`${source}_无声`。
- metadata 保存 source、mode、output kind 和 edge IDs。
- 一次 undo/redo 完整回退/恢复双节点双边。
- 多选隐藏 toolbar；390px 下画布自然裁切且 document 无横向 overflow。
- Batch 9、15、26、27、28 与完整工程/文档门禁通过。

## 4. 不在本批

- 真实媒体下载、音轨解码、上传和 URL 管理；
- 真实人声分离接口与轮询；
- audio-only / video-only / failure / timeout 矩阵；
- 大于 180 秒或无音轨的专门 fixture；
- 当前 feature flag 关闭的音效 prompt modal；
- 原站碰撞避让算法的完整复制。
