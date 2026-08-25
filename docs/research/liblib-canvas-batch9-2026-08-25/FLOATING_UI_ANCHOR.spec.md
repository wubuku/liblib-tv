# Selected Node Floating UI Anchor Spec

## 1. 原站直接证据

### 图片：分镜 #2

采样视口 `929x874`，zoom 约 `0.282798`：

```text
node:
  x = 537.278
  y = 232.188
  w = 175.900
  h = 98.979

top toolbar:
  x = 174.977
  y = 166.398
  w = 900.500
  h = 49.000

bottom panel:
  x = 295.229
  y = 335.692
  w = 660.000
  h = 273.797
```

几何关系：

```text
node center x   = 625.228
toolbar center x = 625.227
panel center x   = 625.229

node top - toolbar bottom = 16.790px
panel top - node bottom   = 4.525px
16 * zoom                 = 4.525px
```

选择靠左的 `咖啡` 图片时，原站面板左边到达 `x=-24.616`。这直接证明原站不会为了保持完整可见而水平夹取面板。

### 视频：失败视频

同一视口，原站 Seedance 生成面板：

```text
video child:
  x = 701.353
  y = 199.167
  w = 175.900
  h = 98.979

generation panel:
  x = 459.304
  y = 302.671
  w = 660.000
  h = 273.797
```

几何关系：

```text
video center x = 789.303
panel center x = 789.304
panel top - video bottom = 4.525px = 16 * zoom
```

原站生成面板 class：

```text
node-floating-ui nodrag nowheel nopan origin-top
transition-[transform,opacity] duration-150 ease-out
absolute -bottom-4 left-1/2 z-20
-translate-x-1/2 translate-y-full
w-full min-w-[660px] max-w-[660px]
```

## 2. 锚定模型

### 顶部 NodeToolbar

图片工具条使用 React Flow `NodeToolbar`：

```text
position = top
align = center
offset = 16 screen px
screen size = 900.5 x 49
```

`NodeToolbar` 位于非缩放 overlay 层，因此工具条尺寸和 `16px` 间距不随 zoom 改变。

### 底部节点内面板

图片编辑器和视频生成器挂在节点内部：

```text
position: absolute
left: 50%
source semantic offset: -16 flow units
clone bordered-shell implementation: bottom: -17px
translate: -50% 100%
width: 660px
transform-origin: top center
transform: scale(1 / zoom)
```

clone 的 node shell 自带 `1px` border，absolute containing block 从 padding edge 计算。使用 `-16px` 时，节点外边界到面板实际只有 `15 * zoom`；因此当前实现用 `-17px` 抵消这一个 flow unit。该值属于 clone 的盒模型补偿，不应写成原站 CSS 事实。

最终屏幕关系：

```text
panelCenterX = nodeCenterX
panelTop = nodeBottom + 16 * zoom
panelScreenWidth = 660
```

面板跟随节点、ancestor parent 和 React Flow viewport 的 transform；反缩放只抵消面板自身的视觉缩放，不改变锚点所在的画布坐标。

## 3. Parent Child 场景

失败视频是视频组的 child：

```text
group absolute = (2374, -12)
video relative = (62, 62)
video absolute = (2436, 50)
```

面板锚定对象必须是 child 的最终屏幕矩形：

- ancestor parent 改变位置后：重新选择 child，面板必须按 child 新的最终屏幕矩形重建；
- child drag：只有 child 与面板移动；
- pan：child 与面板获得相同 viewport 位移；
- zoom：child 尺寸变化，面板保持 `660px` 宽，间距更新为 `16 * zoom`。

不得按 parent 的中心、child 的相对 store position 或浏览器视口中心定位面板。

当前 React Flow 用户交互中，拖动 parent 会把选择切换到 parent，child 面板随之卸载。这是选择生命周期，不是锚定失败。

## 4. 生命周期

当前 clone 合同：

- 单个图片被选中：显示图片顶部工具条与底部编辑器；
- 单个视频被选中：失败态显示生成面板；就绪态还显示顶部处理工具条；
- 多选：隐藏所有单节点大型浮层；
- 取消选择：卸载浮层；
- 面板根节点具有 `nodrag nowheel nopan`；
- 浮层允许超出 React Flow 可视区域后被裁切。

“多选时隐藏”是 clone 为保持画布可操作性定义的生命周期，不声称为本轮原站直接实测。

## 5. 稳定测试接口

专项自动化应使用明确的 data attribute 定位：

```text
data-image-toolbar
data-image-edit-panel
data-video-generation-panel
data-segment-reshoot-panel
```

这些 attribute 只服务于可重复测量，不改变视觉或交互。

## 6. Clone 最终测量

`929x874`、整理后约 `28%`：

```text
image node / toolbar / panel center x = 393.120 / 393.120 / 393.120
image toolbar gap = 16.000px
image panel gap = 4.541px = 16 * 0.283816

video child / panel center x = 643.446 / 643.446
video panel gap = 4.541px = 16 * 0.283816
```

在约 `38%`、child drag 和 wheel pan 后，屏幕宽度与相同锚定公式继续成立。
