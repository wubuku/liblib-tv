# Batch 29 计划：视频帧截取工作流

## 1. 缺口与价值排序

| 候选 | 当前 clone | 当前原站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 首帧/尾帧/当前帧 | 完全缺失 | 双入口、时点、命名、节点/边、位置完整 | 5 | 本批实施 |
| 画面编辑 | 两项临时文字 | 主体消除/修改/替换、抠像 | 5 | 后续拆批 |
| 深度动作捕捉 | 缺失 | 入口、intro、参数和派生节点 | 4 | 后续候选 |
| 高清视频 | 仅本地滤镜 | 派生视频节点与任务 handoff | 4 | 后续候选 |

frame capture 是当前最佳下一批：范围可控，source evidence 覆盖入口、语义与
graph handoff；同时它修复一个顶部工具条的明显功能缺口，并为“视频转图片再
进入图片编辑链路”建立可复用工作流。

## 2. 实施步骤

1. 扩展 `canvasStore`：
   - 新增 `VideoFrameCaptureKind` / `VideoFrameCaptureMetadata`；
   - 新增 `createVideoFrameCapture`；
   - 创建 `512x288` image result 与 direct source edge；
   - 首个 anchor 为 source right `+100`、同 Y；
   - 重复结果做纵向 slot search；
   - 保留 source selection；
   - 整个 graph change 只写一个 history snapshot。
2. 扩展 `VideoProcessingToolbar`：
   - 在画面编辑后增加 frame menu；
   - trigger 显示 `截取首帧` 和 chevron；
   - menu 顺序严格为首、尾、当前；
   - 复用当前 trigger-relative `160px` dropdown。
3. 扩展 `VideoNode`：
   - 维护 prototype `currentTime`；
   - timeline click/seek 更新当前帧时点；
   - 顶部三项调用同一个 store workflow；
   - 播放栏 camera click 截当前帧；
   - hover menu 暴露相同三项；
   - 成功后显示短生命周期 feedback。
4. 扩展 `ImageNode`：
   - 暴露 frame capture metadata selectors；
   - filename、dimensions 和 poster 沿用普通 image renderer；
   - 结果被选中后继续使用普通 ImageToolbar/ImageEditPanel。
5. 新增 `scripts/verify-liblib-batch29.py`：
   - 顶部 menu 顺序和 trigger-relative geometry；
   - 播放栏 camera click 与 hover menu；
   - 三种 name/alt/time metadata；
   - `source -> image` edge；
   - `100` world-unit 首个 gap、同 Y；
   - 重复截取不重叠；
   - source selection 保留；
   - atomic undo/redo；
   - 多选隐藏、移动端裁切、零浏览器错误；
   - screenshot/contact sheet。

## 3. 验收标准

- ready-video 顶部新增 `截取首帧` trigger，位于画面编辑后、下载前。
- dropdown 三项顺序为首帧、尾帧、当前帧，宽 `160px`，中心对齐 trigger。
- player camera 是 `28x28` 当前帧快捷入口，hover menu 复用三项顺序。
- 三种 capture 都新增一个 image 和一条 direct source edge。
- metadata：
  - first：`0`、`首帧`、`视频首帧`；
  - last：`duration - 0.05`、`尾帧`、`视频尾帧`；
  - current：当前 timeline time、`截图`、`视频截图`。
- 首个 output 的 world x 为 source right `+100`，world y 与 source 相同。
- 重复 capture 不产生相互覆盖的结果节点。
- source 保持唯一选中，toolbar 可连续截取。
- 一次 undo/redo 只回退/恢复最后一个 output + edge。
- output 被主动选择后出现普通 ImageToolbar 与 ImageEditPanel。
- 390px 下 toolbar 自然裁切且 document 无横向 overflow。
- Batch 9、15、26、27、28、29 与工程/文档门禁通过。

## 4. 不在本批

- 真实 `<video>` 加载、seek 和 frame decoding；
- 8 秒 load timeout 与 3 秒 seek timeout 的运行时模拟；
- PNG data URL、Blob、预签名上传和 resource URL 替换；
- CORS / seek / upload failure matrix；
- 原站 overlap resolver 的完整算法；
- 未经 source 验证的 toast 框视觉复制。
