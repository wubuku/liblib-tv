# LibTV 双浮层多 Zoom 与生命周期矩阵

> 定位：补充单一 28% 快照，验证当前 LibTV 图片节点在多 zoom 下的工具条、编辑面板、中心锚点、间距和卸载时序。本文只记录研究，不代表已经授权修改 clone 代码。

## 1. 结论

当前源站在 28%、34% 和 50% 三个直接可见 zoom 档都满足：

- 图片工具条保持当前动作集合的 `1092.5x49` 屏幕尺寸；
- 下方编辑面板保持 `660px` 屏幕宽度和当前内容态高度 `191px`；
- 两个浮层都以节点屏幕中心为 anchor，负 x 被自然裁切，不做 viewport clamp；
- 面板与节点底部的 gap 是 `16 * zoom`，分别为约 `4.525px` 和 `8px`；
- 空白画布点击会同时卸载顶部工具条和底部面板；再次选择图片会一次性恢复两层。

同时发现一个不能被旧 clone 合同掩盖的差异：顶部工具条到节点顶部的实测 gap 并非固定 `16px`。当前快照在约 28% 为 `16.794px`，34% 为 `18.152px`，50% 为 `22px`。三点与 `10px + 24 * zoom` 的简单模型相差约 `0.01px` 以内，但这仍是证据支持的推断，不是已从源代码确认的公式；不能直接把 clone 的 `offset=16` 当作完整 source contract。

## 2. 测量边界

- 页面：当前登录态 LibTV canvas URL（见原始 JSON）；
- viewport：`929x874`；
- 观察日期：2026-08-26；
- 动作：缩放菜单切换 `50%`、`100%`、`适合屏幕`，并从约 28% 执行一次“放大”到 34%，切换图片节点，读取 DOM rect；
- 未执行：Prompt 编辑、AutoLink 切换/接受、生成、上传、下载、保存和图片工具动作；
- 100% 档因源站只渲染可见节点，选中节点离开 viewport 后 node DOM 被卸载，因此 100% 只作为 virtualization boundary 记录，不作为完整几何样本。

结构化数据见 [`libtv-overlay-multizoom-audit-2026-08-26.json`](../liblib-seedance-2.5-2026-08-25/libtv-overlay-multizoom-audit-2026-08-26.json)。

## 3. 直接可见几何

### 3.1 约 28%：`图片4`

当前 viewport style：

```text
transform: translate(12.4578px, 185.027px) scale(0.282798);
```

| 元素 | x | y | width | height |
|---|---:|---:|---:|---:|
| node | `128.405` | `674.833` | `197.958` | `98.979` |
| top toolbar | `-318.867` | `609.039` | `1092.5` | `49` |
| bottom panel | `-102.616` | `778.337` | `660` | `191` |

派生关系：

- node center `227.384`；toolbar center `227.383`，误差约 `-0.001px`；panel center `227.384`；
- toolbar bottom到 node top：`16.794px`；
- node bottom到 panel top：`4.525px = 16 * 0.282798`，误差来自 sub-pixel rounding；
- toolbar 和 panel 均负 x，源站保留裁切。

### 3.2 34%：上方空图片

从适合屏幕的约 28% 执行一次源站“放大”得到 `34%`，选择 `i-1FQ9tErTcC`：

| 元素 | x | y | width | height |
|---|---:|---:|---:|---:|
| node | `-33.155` | `227.277` | `209.723` | `118.775` |
| top toolbar | `-474.547` | `160.125` | `1092.5` | `49` |
| bottom panel | `-258.294` | `351.482` | `660` | `191` |

中心与 gap：

- node center `71.706`；toolbar center约 `71.703`；panel center `71.706`；
- toolbar bottom到 node top：`18.152px`；
- node bottom到 panel top：`5.430px = 16 * 0.339357`；
- 该点与 `10 + 24 * zoom = 18.145px` 相差约 `0.008px`，可作为 positioning inference，不升级为 source fact。

### 3.3 50%：上方空图片

为了让面板完整留在 viewport 内，切到 50% 后选择 `i-1FQ9tErTcC`。当前 viewport style：

```text
transform: translate(-334.732px, -8.5px) scale(0.5);
```

| 元素 | x | y | width | height |
|---|---:|---:|---:|---:|
| node | `-268.732` | `128` | `309` | `175` |
| top toolbar | `-660.477` | `57` | `1092.5` | `49` |
| bottom panel | `-444.232` | `311` | `660` | `191` |

派生关系：

- node center `-114.232`；toolbar center `-114.227`，误差约 `0.005px`；panel center `-114.232`；
- toolbar bottom到 node top：`22px`；
- node bottom到 panel top：`8px = 16 * 0.5`；
- toolbar 和 panel 均负 x，源站没有把它们移回浏览器中心。

### 3.4 100%：可见性边界

切换到 100% 后，当前 selected image 的 node 已离开可见渲染区域，`.react-flow__node.selected` 不再存在；源站仍短暂保留工具条 DOM，尺寸为 `1092.5x49`，但不能用缺失 node 的 rect 计算中心和 gap。切回“适合屏幕”会恢复约 `28%`，再选择 `图片4` 即可恢复标准双浮层。

这条记录的价值是明确测试边界：不要把“DOM 不存在”误判成选中状态错乱，也不要在 clone 中为了保留离屏节点浮层而新增 page-level portal。

## 4. 生命周期核验

| 操作 | 源站观察 | 对 clone 的合同含义 |
|---|---|---|
| 图片4选中 | 1 个当前工具条 + 1 个 node 内面板 | 单节点只允许一组双浮层 |
| 切换 34%/50% | 屏幕尺寸不变，node 世界尺寸随 zoom 增长 | 反缩放/非缩放层必须各自正确 |
| 选择另一张图片 | 旧双浮层卸载，新图片双浮层挂载 | 不能保留旧节点的 page overlay |
| 空白画布点击 | selected 为空，toolbar count `0`，大 panel count `0` | 选择清空是成组卸载，不是隐藏其中一层 |
| 适合屏幕 | viewport 回到约 `28%`，选择可重新建立 | 视图恢复不应生成/删除 graph 数据 |
| 100% 离屏 | node DOM 可因可见性策略卸载 | 需要区分 virtualization 与 selection state |

本轮回到用户初始上下文：约 `28%`、`图片4` 选中、标准双浮层恢复。

## 5. Source / Clone 差异

| 维度 | 当前源站 | 当前 clone | 当前结论 |
|---|---|---|---|
| toolbar width | `1092.5`、`w-fit`、13 buttons | `900.5` 固定宽度 | 已知 P0 视觉差异 |
| toolbar height | `49` at 28/50 | `49` | 尺寸一致 |
| toolbar horizontal anchor | node center | NodeToolbar center | 结构方向正确 |
| toolbar vertical gap | 28% `16.794`、34% `18.152`、50% `22` | 验证脚本按 `16` 断言 | 三点支持 `10 + 24 * zoom` 推断，仍需源码确认 |
| panel width | `660` | `660` | 屏幕宽度方向正确 |
| panel height | 当前样本 `191` | explicit `191` for empty state | 当前样本一致 |
| panel vertical gap | `16 * zoom` | `16 * zoom` | 公式已对齐 |
| edge behavior | negative x / natural clip | no clamp | 方向正确 |
| deselection | both overlays removed | both overlays expected removed | 需持续回归 |

相关 clone 入口：

- [`ImageToolbar.tsx`](../../../src/components/ImageToolbar.tsx#L33)：当前固定宽度和 `NodeToolbar`；
- [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx#L101)：节点内 `660px`、inverse zoom；
- [`verify-liblib-batch9.py`](../../../scripts/verify-liblib-batch9.py#L77)：当前 clone 的中心、toolbar gap、panel gap 断言；
- [`ImageNode.spec.md`](../components/ImageNode.spec.md#required-regressions)：已有 28/53/100 clone 回归目标。

## 6. 高价值实施队列（等待授权）

### P0：先修动作集合，再修多 zoom

当前 `900.5 -> 1092.5` 的动作集合落后是确定性差异，应先按 [`LIBTV_OVERLAY_GEOMETRY_MATRIX.md`](LIBTV_OVERLAY_GEOMETRY_MATRIX.md) 补齐 `元素编辑 / 图层分离` 和末端动作，再复测 toolbar 的垂直位置。否则宽度改变可能遮挡节点或改变可见裁切，导致多 zoom 诊断失真。

### P0：分离两种 gap 合同

- bottom panel：使用已证实的 `16 * zoom`；
- top toolbar：保留 source 多档实测，继续查明 `NodeToolbar` 的 source offset/transform 组合，不直接复用固定 `16`。

### P1：生命周期回归

在代码授权后，补充图片/视频各一组：选中、切换、空白点击、适合屏幕、50%/100% 离屏、回到 28%，并记录 DOM count、center delta、viewport transform 和 graph node 数量。所有 zoom 操作都必须证明不改 graph data。

### P1：源码与 live 对照

通过当前生产 chunk 继续定位 toolbar host 的定位公式，重点关注 `NodeToolbar`/自定义 toolbar wrapper 是否把 zoom、node measured rect、CSS transform 和固定 gap 叠加。没有足够证据前不添加新的 clamp、自动避让或第三种 overlay。

## 7. 未决问题

- 顶部 gap 的精确源代码函数尚未确认；三个 live 档与 `10 + 24 * zoom` 简单模型吻合，但不能把模型当作源码事实。
- 50% 样本使用不同宽度的图片节点，虽然 image4 在 50% 的补测也得到 `22px`，仍应在同一 node 上完成更多档位复测。
- 100% 离屏后 toolbar 残留的卸载时序需要更多 frame 级观察，不能据一个等待后的 DOM 快照决定 clone 行为。
- source toolbar 当前 action width 已确认，但各按钮 tooltip/disabled 条件不属于本批多 zoom 证据。

本批因此只升级“多 zoom 事实”和“下一步测量合同”，没有以猜测为依据修改任何业务代码。
