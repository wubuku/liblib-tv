# Batch 24 Screenshot Analysis

> 识图日期：2026-08-25  
> 用途：固化逐帧拉片入口与结果拓扑；后续优先读取本文，不重复打开两张整图。

## 1. Source entry

### 文件

- 路径：`docs/research/liblib-seedance-2.5-2026-08-25/evidence/frame-analysis-entry.png`
- 来源：外部 LibTV Seedance 2.5 功能文章
- 文件尺寸：`1768x834`
- 状态：ready 视频节点通过顶部工具条创建/连接逐帧拉片节点
- 本批识图次数：1

### Source screenshot fact

- 左侧 ready 视频节点标题为 `视频节点 5-片段重拍`，媒体为 `1280 × 720`、`0:30`。
- 顶部处理工具条可见：高清、逐帧拉片、智能续写、智能去字幕、音频分离、画面编辑、下载、展开。
- 逐帧拉片按钮被文章红框强调；红框不是产品 UI。
- 右侧为独立分析节点，上方外部标题为 `逐帧拉片`，由 edge 与视频节点连接。
- 分析节点内部：
  - 标题 `逐帧拉片` 和 cyan `SD 2.5` badge；
  - `视频素材` 左对齐，`00:30 · 1280×720` 右对齐；
  - 视频预览不覆盖源名称 pill；
  - `拆解维度`；
  - `分镜 / 动态 / 音乐` 三个 cyan active control；
  - 白色 `开始拉片` 按钮。

### Geometry inference

- 截图经过文章排版，不能将像素直接当作源 DOM rect。
- 分析节点内部预览约为 `16:9`；三个维度同排等宽。
- 当前 live audit 的空态 world size `320x389` 优先于文章截图的视觉像素。

## 2. Source output

### 文件

- 路径：`docs/research/liblib-seedance-2.5-2026-08-25/evidence/frame-analysis-output.png`
- 来源：外部 LibTV Seedance 2.5 功能文章
- 文件尺寸：`1053x2757`
- 状态：逐帧拉片完成后的纵向画布区域
- 本批识图次数：1

### Source screenshot fact：总体拓扑

- 结果不是 tab dialog、drawer 或选中态下方 panel。
- 结果沿画布纵向排列为多个独立深灰圆角 surface。
- 每个 surface 左侧边缘附近可见连接曲线/端点片段。
- 没有统一的“分析完成”、选择计数或“加入参考” footer。
- 结果卡标题位于媒体上方；媒体右上有单个复用/导出图标。

### Source screenshot fact：分镜

1. `分镜组01｜出发探店·出门→咖啡`
   - `S01｜中景·固定｜出门微笑·引出人物`
   - `S02｜中近景·平稳｜吧台接咖啡·建立场景`
   - `S03｜近景·固定｜窗边捧杯看镜头·人物性格建立`
2. `分镜组02｜抵达海边·逛街→沙滩漫步`
   - `S04｜中近景·侧面｜逛饰品店拍摄·展示探店过程`
   - `S05｜中景·背面跟拍｜走向海边·进入新场景`
   - `S06｜中景·侧前方｜弯腰捡贝壳·展示海边互动`
3. `分镜组03｜海边时光·嬉闹→日落`
   - `S07｜中景·固定｜四人浅滩打水嬉闹·展示群体互动`
   - `S08｜中近景·侧后逆光｜日落捧饮品望海·情绪收束`

分镜组使用两列媒体卡；三张卡的组保留一个空 grid 位置，第三组只有一行两张。

### Source screenshot fact：动态

- 标题：`动态｜运镜与动作参考`
- 两列排列：
  - `M01｜6s·中景跟拍｜走向海边捡贝壳...`
  - `M02｜6s·固定中景｜四人浅滩打水...`
  - `M03｜4s·固定中近景｜日落沙滩静...`
- 每张动态卡标题右侧显示 `1280 × 720`。

### Source screenshot fact：音乐

- 标题：`音乐｜BGM参考片段`
- 单个较窄节点：
  - `BGM｜14.6s·轻快节奏｜...`
  - 波形；
  - `00:00 / 00:14`；
  - 圆形播放命令；
  - 媒体右上复用/导出命令。

### 非结果内容

- 第二个分镜组右下附近可见单独的 `视频节点 9` 和 `1280 × 720`。
- 它具有独立视频节点标题和完整预览，不符合 `Sxx/Mxx/BGM` 结果命名。
- 本批不把它计入逐帧拉片产物，也不据此新增额外结果视频。

## 3. Current clone gap

- `ShotBreakdownResultsPanel` 为 `660x260` 节点相对浮层，只在 source node selected + complete 时存在。
- 结果被压进 `分镜 / 动态 / 音乐` tabs。
- 分镜只有 `S01-S04`。
- clone 自创：
  - `分析完成 · 本地示例结果`
  - card check 状态
  - `已选择 N 项`
  - `加入参考`
- ready 预览上覆盖 `sourceName · 00:30` pill，而 source screenshot 把时长/分辨率放在 section label 右侧。

## 4. Re-inspection rule

除非进入以下新范围，不再打开这两张整图：

- 原站 live completed DOM 或网络 payload；
- 精确 SVG path、computed style、hover/animation；
- 卡片右上命令的真实行为；
- output screenshot 中连接线和节点 type 的 DOM 证明。

本批 clone 验证截图完成后，应在本文追加一次性 contact sheet 识图结论。
