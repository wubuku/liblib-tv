# LibTV Source Freshness 2026-08-27：标准图片 41% 双浮层

> Queue：`OC-EQ-001`
>
> 状态：`PARTIAL_RECORDED`；只覆盖标准图片选中态、41% zoom、`929x874` viewport
>
> 安全边界：共享登录态项目只读；本轮没有 click、keypress、type、fill、toggle、drag、connect、generate、upload、save 或 download

## 1. 观察上下文

| 字段 | 值 |
|---|---|
| 日期 | 2026-08-27 |
| URL | `https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd` |
| 页面标题 | `未命名项目 - 画布 2 - LibTV - 专业视频创作工具` |
| Viewport | `929x874`，device pixel ratio `2` |
| 可见 zoom | `41%` |
| 精确 zoom 变量 | `0.40722891566265057` |
| Fixture | `LIBTV-FIX-SOURCE-SHARED-01` / `SHARED_READ_ONLY` |
| 页面初始状态 | 浏览器接管前已选中图片节点 `i-1FQ9tErTcC`，标准顶部工具条和底部面板已挂载 |
| 实际动作 | claim 已打开 tab、读取 DOM/computed rect、读取可见 button、截图 |

本轮没有通过交互构造 fixture。页面本来就处于目标选中态，因此只读取当前状态；不能据此推出从空白点击到选择节点的转换在新日期也已复核。

## 2. 结构化证据

- 原始数据：[`libtv-source-freshness-standard-image-41-2026-08-27.json`](libtv-source-freshness-standard-image-41-2026-08-27.json)
- 截图：[`liblib-original-oc-eq-001-standard-image-41-929x874-2026-08-27.png`](../../design-references/liblib-original-oc-eq-001-standard-image-41-929x874-2026-08-27.png)

### 2.1 同一 frame 几何

| Surface | `x` | `y` | `width` | `height` | center X |
|---|---:|---:|---:|---:|---:|
| selected node | `38.1313` | `365.7349` | `251.6675` | `142.5302` | `163.9651` |
| top toolbar | `-382.2891` | `296.9609` | `1092.5` | `49` | `163.9609` |
| bottom panel | `-166.0349` | `514.7807` | `659.9999` | `191` | `163.9650` |

横向中心误差：

- toolbar vs node：约 `0.0041px`；
- panel vs node：约 `0.00002px`。

三个 surface 继续共享节点 screen center，但不共享 containing block 或垂直公式。

### 2.2 垂直公式

顶部实际 gap：

```text
nodeTop - toolbarBottom
= 365.73492431640625 - (296.9609375 + 49)
= 19.77398681640625px
```

既有 source 公式期望值：

```text
10 + 24 * 0.40722891566265057
= 19.773493975903612px
```

残差约 `0.00049px`。

底部实际 gap 为 `6.515625px`，`16 * zoom` 的期望值为 `6.515662650602409px`，残差约 `0.00004px`。

这次新日期样本继续支持：

- 顶部工具条：screen-space host，gap 为 `10 + 24 * zoom`；
- 底部面板：node-internal inverse scale，gap 为 `16 * zoom`；
- 两者都保持 screen-size，不使用同一个固定 `16px` screen offset。

### 2.3 自然裁切

选中节点中心位于 viewport 左侧 `163.965px`。`1092.5px` 工具条的左边界为 `-382.289px`，`660px` 面板的左边界为 `-166.035px`；两者都自然超出 viewport 左边缘，没有被 clamp 或平移到浏览器中心。

截图中的左侧动作因此被裁切。这是当前 edge sample 的源站表现，不是浮层定位错误，也不允许后续 clone 为了让整条 toolbar 可见而擅自增加 viewport collision avoidance。

## 3. 当前动作集合

顶部工具条仍有 `13` 个 button：

| Index | 可见文字 / accessible name | 尺寸 |
|---:|---|---:|
| 0 | `人像质感调节` + `NEW` | `178x32` |
| 1 | `全景` | `62x32` |
| 2 | `多角度` | `75x32` |
| 3 | `打光` | `62x32` |
| 4 | `九宫格` | `91x32` |
| 5 | `高清` | `78x32` |
| 6 | `元素编辑` | `88x32` |
| 7 | `图层分离` | `88x32` |
| 8 | `宫格切分` | `104x32` |
| 9-12 | 四个无可访问文字的 `32x32` icon button | `32x32` each |

本轮只直接确认九个文字动作和四个 icon button 的存在、顺序与尺寸。四个 icon 的语义继续引用 [`LIBTV_IMAGE_ACTION_MATRIX.md`](LIBTV_IMAGE_ACTION_MATRIX.md) 和既有 bundle 证据；不能仅凭图形外观把本次截图升级为新的动作副作用证明。

## 4. 与既有结论的比较

| Claim | 2026-08-27 判定 | 说明 |
|---|---|---|
| `1092.5x49`、13 button 标准 toolbar | `UNCHANGED` | 与 2026-08-26 五节点矩阵一致 |
| top gap `10 + 24 * zoom` | `STRENGTHENED` | 新日期 41% 样本残差小于 `0.001px` |
| bottom panel `660x191`、gap `16 * zoom` | `STRENGTHENED` | 新日期样本残差小于 `0.001px` |
| toolbar/panel 保持 node center | `STRENGTHENED` | edge sample 两个中心误差均小于 `0.01px` |
| viewport edge 自然裁切 | `STRENGTHENED` | toolbar/panel 左边界均为负，未观察到 clamp |
| selection/blank click 生命周期 | `UNKNOWN_THIS_RUN` | 页面接管前已选中，没有点击 |
| 28/34/50/100% 多 zoom | `UNKNOWN_THIS_RUN` | 没有改变 viewport zoom |
| active tool replacement | `UNKNOWN_THIS_RUN` | 没有点击任何工具动作 |

没有观察到会使 [`LibTVOverlayPositioning.contract.md`](../components/LibTVOverlayPositioning.contract.md) 失效的 drift。

## 5. 对当前实施工作的含义

本次证据加强 `OC-BP-001` 的 `L0 Evidence`，也支持并行 Batch 51 使用 live zoom 映射顶部 `NodeToolbar` offset。但它不评审或证明 Batch 51 的 clone 实现，不修改其 WIP，也不允许把当前 clone 的旧 action set 写成 source parity。

`OC-EQ-001` 仍未整体关闭：page shell、desktop/mobile、空白点击、selection switch、fit view、多 zoom 和前台 overlay freshness 仍可按只读规则分场景补充。由于当前图片几何问题已经得到新日期强化，后续只读研究应优先补未覆盖场景，而不是重复测量同一 41% 节点。

## 6. 不可推出的结论

本次观察不能证明：

- source 的四个 icon action 副作用在新日期没有变化；
- Auto Link 输入、accept、IME 或 graph transaction 已复核；
- 任意非 Seedance 模型具有当前可执行 runner；
- ready-video、process/result 或保存后端合同；
- 当前 clone、Batch 51 verifier 或截图已经通过；
- Open Canvas 的 overlay DOM/CSS 应被移植到 LibTV clone。

## 7. 安全结论

本轮只读取用户已打开、已登录、已选中状态下的页面。没有向 LibTV 发送用户输入，没有改变共享 graph、偏好、参数、任务或账户状态；Open Canvas submodule 和本地 `src/`/verifier 均未由本研究修改。
