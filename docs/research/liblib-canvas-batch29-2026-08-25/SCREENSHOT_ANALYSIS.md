# Batch 29 Screenshot Analysis

## 1. Source Visual Evidence

规划阶段没有重复识别原站整图。

复用：

- Batch 24 ready-video toolbar 视觉记录；
- Batch 9 top toolbar node-relative anchor；
- Batch 27/28 trigger-relative dropdown 与移动端裁切记录。

本批新增的 toolbar/camera 细节来自 2026-08-25 当前线上 bundle CSS。没有把
未登录首页、旧 clone 截图或记忆当作 frame-capture 视觉事实。

## 2. Clone Ledger

专项脚本已生成：

| File | Viewport / state |
|---|---|
| [`liblib-clone-batch29-frame-menu-929-2026-08-25.png`](../../design-references/liblib-clone-batch29-frame-menu-929-2026-08-25.png) | top frame menu |
| [`liblib-clone-batch29-player-camera-929-2026-08-25.png`](../../design-references/liblib-clone-batch29-player-camera-929-2026-08-25.png) | player camera hover menu |
| [`liblib-clone-batch29-frame-graph-929-2026-08-25.png`](../../design-references/liblib-clone-batch29-frame-graph-929-2026-08-25.png) | source + repeated image outputs |
| [`liblib-clone-batch29-frame-output-selected-929-2026-08-25.png`](../../design-references/liblib-clone-batch29-frame-output-selected-929-2026-08-25.png) | captured image normal editor |
| [`liblib-clone-batch29-frame-mobile-390-2026-08-25.png`](../../design-references/liblib-clone-batch29-frame-mobile-390-2026-08-25.png) | mobile clipping |
| [`liblib-clone-batch29-frame-contact-sheet-2026-08-25.png`](../../design-references/liblib-clone-batch29-frame-contact-sheet-2026-08-25.png) | five-state ledger |

## 3. One-Time Contact-Sheet Recognition

识别对象：
`liblib-clone-batch29-frame-contact-sheet-2026-08-25.png`。

采样条件：

- clone route `http://localhost:3000`；
- 2026-08-25；
- desktop `929x874`、mobile `390x844`；
- Chromium device scale factor `1`；
- states：top menu、player menu、three-output graph、selected output、mobile。

### Top frame menu

- ready-video 顶部工具条保持单行 `w-max` 横条，新增 frame group 位于
  `画面编辑` 和下载分隔线之间。
- trigger 显示 frame icon、`截取首帧` 和 chevron，视觉层级与相邻
  dropdown commands 一致。
- dropdown 水平居中在 trigger 下方，三项顺序为首帧、尾帧、当前帧。
- menu 覆盖在 video body 上方，未被节点或 lower generation panel 截断。
- toolbar 左右在 `929px` viewport 中自然贴边/裁切，没有被错误地重排为两行。

### Player camera

- camera 位于 duration/volume 后的右端，保持 `28x28` 紧凑 target。
- hover menu 从 camera 右缘向上展开，菜单和按钮之间没有视觉断裂。
- `00:12` playhead、range track、duration、volume 和 camera 仍在同一基线。
- 菜单没有遮挡 playhead，三项可读且顺序与 top menu 一致。
- capture feedback 位于 source 画面上沿中部，短文案没有覆盖播放按钮。

### Output graph

- fit-view 后 source 位于左侧，first/last/current 三个 image outputs 位于
  同一右侧 column。
- 三个 outputs 顶边按固定 slot rhythm 纵向排列，没有相互覆盖。
- 每个 output 都保持 `1280 × 720` title dimensions 和 source poster。
- 三条曲线均从 source 右侧连出，表达 direct source-to-image topology。
- source 仍是青色 selected node；outputs 没有错误抢占 selection。

### Captured image selection

- 主动选择 current output 后，青色 selected border 移到图片。
- 普通 ImageToolbar 水平居中在图片上方，没有切换成 clone-only frame
  toolbar。
- 普通 ImageEditPanel 继续锚定图片下方；viewport 边缘只做画布裁切，
  没有改成页面中心浮层。
- first/last/current column 和 direct edges 在背景中仍可辨识。

### Mobile

- `991px` screen-sized toolbar 自然跨出 `390px` viewport。
- 当前可见的是 toolbar 中段；frame trigger 位于被裁掉的右段，符合原站
  node-relative unclamped behavior。
- source video、timeline 和 lower panel 仍围绕同一 node 中心。
- DOM 断言确认 document/body 无横向 overflow；裁切只发生在 canvas
  viewport 内。

## 4. Evidence Classification

### DOM + screenshot fact

- top toolbar `991x49`，frame dropdown `160px`，trigger/menu center delta
  `0px`，垂直 gap 约 `7px`。
- camera `28x28`，player menu 右缘与 camera 右缘对齐。
- first output world gap `100`、Y delta `0`。
- repeated outputs 使用 `336` world-unit vertical slot rhythm。
- source selection、ordinary image overlays、mobile clipping 与脚本断言一致。

### Source-backed behavior

- 双入口、三项顺序、camera direct-current shortcut、time/name/alt、
  direct source edge 和首个 `100` gap 来自当前线上 bundle。

### Clone-only visual/behavior decision

- poster 代表 frame bitmap。
- `336` world-unit repeated slot rhythm。
- local range playhead 和 `1400ms` in-node feedback。
- graph output screenshots 是 clone 验证，不是原站像素证据。

## 5. Re-inspection Rule

contact sheet 已于 2026-08-25 识别一次，结果已写入本文件。后续除非截图
或实现变化，不重复识别整图；先复用以上文字记录。
