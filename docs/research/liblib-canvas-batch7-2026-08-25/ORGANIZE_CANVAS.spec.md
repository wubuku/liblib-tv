# Organize Canvas Spec

## 1. Interaction Model

- 触发：底部左侧“整理画布”按钮或 `Option/Alt+Shift+F`；
- 类型：单次命令；
- 结果：节点立即进入整理预览，同时出现确认卡；
- 确认前保存整理前节点和 viewport 快照；
- “还原”恢复快照，“保留”确认当前节点位置；
- 整理节点变化进入 graph history，普通 viewport 变化不进入 graph history。

## 2. 原站截图直接事实

参考：`docs/design-references/liblib-original-organize-preview-2026-08-25.png`。

在 `929x874` 截图中：

- 底部缩放文案为 `28%`；
- 左列自上而下为女性参考图、咖啡馆参考图、男性参考图、咖啡参考图；
- 中列为剧本执行节点和 `分镜 #2`；
- 右列为图片组、视频组及组内失败视频；
- 剧本位于更右上方；
- 内容从左上区域开始，底部保留大面积空白；
- 这不是当前 clone 的等宽三列网格。

## 3. 反推实现候选

以下世界坐标由截图屏幕位置、当前节点已知世界尺寸和约 `0.2828` 缩放反推。它们用于复现截图，不登记为原站 DOM 提取值。

| 身份 | 当前节点 ID | 候选世界坐标 |
|---|---|---:|
| 女性参考图 | `i-lBzmo67AHv` | `(0, 0)` |
| 咖啡馆参考图 | `i-vxeeCnxySa` | `(-85, 450)` |
| 男性参考图 | `i-1FQ9tErTcC` | `(0, 900)` |
| 咖啡参考图 | `i-dnwoZQ7jsG` | `(-85, 1350)` |
| 剧本执行 | `b-bTLLuU4w5q` | `(910, 470)` |
| 分镜图 | `i-YDfWhFlthe` | `(820, 1040)` |
| 图片组 | `g-245IDFh8sB` | `(1640, 370)` |
| 视频组 | `g-EFbbHpwq5w` | `(1640, 940)` |
| 失败视频 | `v-UGQZzZOpbv` | `(1710, 1010)` |
| 剧本 | `t-9j2MoccxBj` | `(2500, 0)` |

对应的已知边界约为：

```text
minX = -85
maxX = 2850
minY = 0
maxY = 1700
```

## 4. Viewport 算法

目标不是写死 `929px` 截图 transform，而是让同一拓扑在不同宽度下保持同类构图。

```text
horizontalMargin = 48
topMargin = 49
availableWidth = viewportWidth - horizontalMargin * 2
zoom = clamp(availableWidth / organizedBounds.width, 0.1, 0.526)
x = horizontalMargin - bounds.minX * zoom
y = topMargin - bounds.minY * zoom
```

在 `929px` 宽下，候选边界得到：

```text
zoom ≈ 0.284
x ≈ 72
y = 49
```

这与截图中的 `28%` 和左列位置一致。较宽视口允许同一拓扑适度放大，但不超过当前桌面基线 `52.6%`。

## 5. 未知节点 Fallback

原站截图只证明当前项目的整理结果。为了避免 clone 在新增节点后把未知节点全部堆叠：

- 已知节点先使用上表位置；
- 未知顶层节点按原数组顺序稳定排列；
- fallback 从已知拓扑下方开始，使用与语义拓扑一致的三个固定列坐标；
- 每列下一个节点的 y 由该列当前高度、节点高度与固定 gutter 计算；
- 有 `parentId` 的 child 不单独进入 fallback，保留相对 parent 坐标；
- fallback 是 clone 的可逆工程决策，不描述为原站算法。

## 6. History

- `organize` 记录整理前 graph snapshot；
- “保留”只关闭确认卡，不新增 history；
- 保留后 undo/redo 在整理前后 graph snapshot 之间切换；
- “还原”恢复节点和 viewport 快照并关闭确认卡；
- viewport 仍不进入通用 graph history。
