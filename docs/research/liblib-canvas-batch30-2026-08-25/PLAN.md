# Batch 30 计划：主体编辑菜单与智能抠像

## 1. 缺口与价值排序

| 候选 | 当前 clone | 当前源站证据 | 价值 | 决策 |
|---|---|---|---:|---|
| 主体编辑菜单纠偏 | `画面编辑/片段截取/画面裁切` | 四项、顺序、hover、geometry 完整 | 5 | 本批实施 |
| 智能抠像 | 无 | panel、request、output、edge 完整 | 5 | 本批实施 |
| 三类主体标注器 | 无 | store/tools/validation/prompt 丰富，视觉状态仍大 | 5 | 下一批 |
| 视频限制反馈 | 无 | 30 秒精确文案完整 | 4 | 本批实施 |

## 2. 实施步骤

1. 修正 `VideoProcessingToolbar`：
   - 删除无证据的 `画面编辑` 两项菜单；
   - trigger 改为 `主体消除`；
   - menu 顺序改为消除、修改、替换、智能抠像；
   - 增加 `100ms` open / `120ms` close hover；
   - 保留 click toggle，兼容键盘/测试入口。
2. 扩展 `VideoNode`：
   - subject action 执行 source-backed duration validation；
   - 当前 `30s` fixture 显示精确 unsupported feedback；
   - matting action 打开下方面板；
   - panel submit 暴露短 submitting 状态并调用 store transaction。
3. 新增 `SmartMattingPanel`：
   - source-shaped `512x48` bottom panel；
   - close、label、`--` power state、generate/spinner；
   - pointer events 不影响 node selection/drag。
4. 扩展 `canvasStore`：
   - 新增 `SmartMattingMetadata`；
   - 新增 `createSmartMatting`；
   - 创建 pending video + direct edge；
   - source right `+100`、同 Y、重复 output 避让；
   - source selection 保留；
   - graph change 为单次 history。
5. 扩展 pending VideoNode：
   - 单独识别 smart matting output；
   - 暴露 metadata selectors；
   - 显示 `智能抠像 · 等待媒体资源`，不伪造媒体。
6. 新增 `scripts/verify-liblib-batch30.py`：
   - menu 文案、顺序、hover delay/close bridge、geometry；
   - 30 秒三项 subject validation；
   - panel anchor/size/controls；
   - spinner 和 output graph；
   - metadata、name、edge、position、selection、undo/redo；
   - repeated output non-overlap、多选隐藏、移动端裁切；
   - screenshot/contact sheet 和零浏览器错误。

## 3. 验收标准

- `画面编辑/片段截取/画面裁切` 从 ready-video toolbar 消失。
- `主体消除` trigger 位于 `音视频分离` 后、`截取首帧` 前。
- hover 约 `100ms` 后打开，离开组约 `120ms` 后关闭；click 仍可切换。
- menu 固定四项，宽 `160px`，相对 trigger 中心对齐并保持约 `7~8px` gap。
- 默认 30 秒 source 点击三项 subject action 均显示
  `视频大于15秒，暂不支持该功能`，且不创建节点。
- `智能抠像` 打开 source 下方 `512px` compact panel，并替换普通 generation
  panel。
- generate busy 后创建一个 pending VIDEO 和一条 direct source edge。
- metadata 包含 provider/model/taskType/format/source/dimensions/duration/edge。
- 首个 output 在 source right `+100` world units、同 Y。
- 重复 matting output 不重叠。
- source 保持唯一选中；一次 undo/redo 回退/恢复最后一个 output + edge。
- 多选时上下浮层隐藏；390px 下自然裁切且 document 无横向 overflow。

## 4. 不在本批

- 点选、框选、画笔、橡皮和对象识别 API；
- remove/modify/replace 的 mark cards、description 和 replacement library；
- 真实 MP4/MOV MIME、natural metadata 和 CORS 校验；
- 真实 power calculation、commercial gate 和 generation task；
- WEBM 透明视频解码、上传和任务轮询；
- 原站 `findClosestRightFlowPosition` 的完整碰撞实现。

