# Batch 31 计划：主体编辑标注工作流

## 1. 缺口与价值排序

| 候选 | 当前 clone | 当前源站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 三类主体编辑可达 | 30 秒只显示限制反馈 | 三个 mode 共享 `usePictureEditStore` | 5 | 本批实施 |
| 标注工具 | 无 | `point / box / brush / eraser` | 5 | 本批实施 |
| 标记生命周期 | 无 | mark 持有时间、候选、描述、替换图 | 5 | 本批实施 |
| 模式校验 | 无 | remove 4、modify 4、replace 2；modify 描述必填；replace 替换图必填 | 5 | 本批实施 |
| 分析/提交反馈 | 无 | `分析中`、`提交`、`确定` 文案证据 | 4 | 本批实施 |
| 输出 graph handoff | 无 | 三类主体编辑共用编辑器，已有生成任务语义 | 4 | 本批以 request-shaped pending graph 闭环 |
| 真实识别与上传 | 无 | 只有服务语义，未取得可复现 API | 3 | 不实现 |

## 2. Source Fact / Inference / Clone Decision

### Source fact

- 三项入口共享主体编辑 store，mode 为 `subjectRemove`、`subjectModify`、
  `subjectReplace`。
- active tools 是 `point`、`box`、`brush`、`eraser`。
- remove 最多 4 处，modify 最多 4 处，replace 最多 2 处。
- mark 持有 frame time、识别候选、描述和 replace image。
- modify 的每个有效 mark 需要描述；replace 的每个有效 mark 需要替换图。
- 可见文案包括 `点选 / 框选 / 画笔 / 橡皮`、`重置 / 确定 / 提交 /
  分析中`、`描述想要如何更改画面`、`最多标记 {count} 处`、
  `本地上传 / 历史图库`。
- source validation 仍先阻止 `>15s`、`<2.5s`、格式、分辨率、面积和宽高比
  不合规的视频。

### Inference

- 编辑器需要保留 source video 的当前 frame time，并把标记归一化到画面坐标。
- box/point/brush/eraser 的视觉标记应直接覆盖视频画面，提交前可继续编辑。
- 提交后应形成主体编辑任务的画布结果，而不是只显示一条 toast。

### Clone-only decision

- 当前 30 秒 fixture 仍用于专项测试，因此 Batch 31 在测试中通过本地
  `?duration=10` fixture override 使三项编辑器可达；默认用户路径仍保留
  `>15s` source guard，不改变旧批次数据。
- point 使用固定大小的 normalized marker；box 使用 normalized rectangle；
  brush/eraser 使用 normalized polyline。它们表达可验证的 UI 状态，不是
  真实 segmentation mask。
- 候选对象使用 `主体 1/主体 2...` 的本地标签，不声称来自识别服务。
- replace 的“本地上传 / 历史图库”只写入本地 prototype 状态，不弹真实文件
  选择器、不读取账户图库。
- 提交创建一个 pending video、一个 direct source edge 和 request-shaped
  metadata；不生成媒体、不写真实 task ID。

## 3. 实施步骤

1. 写入 `PictureEditMark`、`PictureEditMetadata` 和 store action。
2. 新增 `PictureEditPanel`：
   - mode header、mark counter、四工具、撤销/重做/重置；
   - 视频内 normalized marker overlay；
   - selected mark detail；
   - modify description、replace source actions；
   - disabled reason、分析中 spinner。
3. 将 VideoNode 的三项 subject action 从 toast guard 扩展为：
   - 合规 duration 进入编辑器；
   - source poster 作为 prototype frame；
   - submit 后创建 pending output。
4. 扩展 pending VideoNode renderer 和 stable selectors。
5. 新增 Batch 31 专项 Playwright，覆盖三模式与关键 pointer/keyboard 流程。
6. 更新 component specs、行为目录、验证矩阵、Big Picture 和实施日志。

## 4. 验收标准

- 默认 30 秒视频仍显示 `视频大于15秒，暂不支持该功能`，graph/history 不变。
- 可达 fixture 能切换三种主体编辑模式，且模式标题/上限正确。
- 四个工具都能建立或修改 normalized marks；橡皮可删除选中 mark。
- 达到上限后新增 mark 不改变计数，并显示上限状态。
- modify 无描述、replace 无替换图时 submit disabled，reason 可见。
- replace 的两个本地来源入口都可反馈且不触发真实上传。
- reset、undo、redo、Escape/cancel 可恢复编辑器状态。
- submit 显示 `分析中`，之后创建一个 pending video 和 source edge。
- metadata 保存 mode、marks、source、frame time、描述/替换图来源和 edge ID。
- 首个 output 使用 source right `+100` world units；重复输出不重叠。
- 一次 undo/redo 回退/恢复完整主体编辑结果。
- 多选隐藏主体编辑器；`390x844` 自然裁切且 document 无横向溢出。
- 专项脚本和 Batch 9、15、26、27、28、29、30 回归通过。
