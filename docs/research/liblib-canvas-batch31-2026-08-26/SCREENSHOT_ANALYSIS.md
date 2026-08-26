# Batch 31 Screenshot Analysis Ledger

> 状态：已完成一次性 clone contact-sheet 识别；没有重复识别 Batch 30
> contact sheet，也没有把 clone 截图当作新的原站事实。

## Reused Evidence

主体编辑器的可执行事实来自：

- [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
- [`../liblib-canvas-batch30-2026-08-25/SCREENSHOT_ANALYSIS.md`](../liblib-canvas-batch30-2026-08-25/SCREENSHOT_ANALYSIS.md)
- [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)

这些记录已经覆盖菜单入口、duration guard 和智能抠像，不需要再次打开整张
旧截图。

## New Screenshot Policy

实施后只识别本批新增的 clone 状态截图一次，并把：

- viewport、state 和截图路径；
- panel/mark overlay 的层级；
- tool、counter、字段和 disabled reason；
- node anchor、natural clipping 和 output graph；
- source fact、inference、clone-only calibration；

写回本文件。后续回归先读本节，不重复识别同一 contact sheet。

## Batch 31 Clone Contact Sheet

截图：
[`liblib-clone-batch31-picture-edit-contact-sheet-2026-08-26.png`](../../design-references/liblib-clone-batch31-picture-edit-contact-sheet-2026-08-26.png)

采集时间：2026-08-26
来源：本地 clone `http://localhost:3000`
桌面视口：`929x874`
移动视口：`390x844`
识别次数：1 次

### 画面事实

- `30s duration guard`：ready video 顶部工具条仍显示 source-order
  `主体消除` 菜单，视频画面上方出现 `视频大于15秒，暂不支持该功能` 的
  局部反馈；没有新增节点或边。
- `remove editor`：进入编辑器后顶部处理工具条卸载；视频 poster 上可见
  `主体 1/主体 5/主体 4` 等本地 mark label 和青色标记框，画面下方是
  `主体消除` 编辑器。工具行同时可见点选、框选、画笔、橡皮和撤销/重做/
  重置，右下角有 `提交`。
- `modify panel`：视频画面上有一个青色点选 mark；下方面板标题为
  `主体修改`，计数为 `1/4`，描述输入框中显示本地测试文案
  `改成白色外套`，提交按钮可用。
- `picture edit graph`：source 保持 selected，普通 source generation panel
  恢复在 source 下方；右侧可见多个主体编辑 pending output，占据同一
  source-right 列并按纵向槽位分开，连线从 source 指向各 output。
- `mobile clipping`：`390px` 视口下，视频和 `660px` 编辑器按画布坐标
  自然越过左右边界并被视口裁切；底部主工具条仍可见，未检测到 document
  横向滚动。

### Geometry And Layering

- 桌面主体编辑器以 source node 中心对齐，宽度为 clone calibration
  `660px`；其内部 mark overlay 与 source video body 同层级关系正确：
  poster < mark overlay < panel controls。
- graph 输出沿用 `+100` world-unit source-right placement 和
  `288 + 48` world-unit vertical slot spacing；截图中没有输出重叠。
- mobile 的裁切与已有 Image/Video lower-editor 合同一致，没有为了适配视口
  把 panel 重新居中到浏览器窗口。

### Evidence Classification

| Observation | Classification |
|---|---|
| `30s` guard copy and no graph | source-backed behavior, clone verified |
| four tool labels and mode-specific fields | source-backed behavior, clone verified |
| `660px` panel width, cyan mark styling, local candidate labels | clone calibration |
| source selected after submit | clone decision, aligned with repeated-source workflow |
| three pending outputs in deterministic slots | clone graph decision |

### Unresolved

- 本批仍没有主体编辑器的原站完整登录态截图，因此不把当前 clone 的
  `660px`、标记颜色、候选标签样式或结果选择生命周期写成 source geometry。
- 若后续获得原站主体编辑器截图，只比较最小的对应 crop，并保留本台账的
  现有 clone 结果作为历史记录。
