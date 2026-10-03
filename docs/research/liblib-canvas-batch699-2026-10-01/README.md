# batch 699 — 「有 onClick / 有 title 都不等于接线」：惰性自证的四件套在导演台只补了一件

## 起点

698 记下一条强读数：**「创建运动轨迹」和「预设运镜」各有两个 DOM 副本，四个全部
`disabled=false`，四个全部点了什么也不发生。**

本批想把「点了没反应」从两个功能扩成全导演台普查。第一遍扫出 **144 个「惰性按钮」**。

**那个数是假的。** 144 条记录里 **108 条是定位失败、36 条是点击超时，
零条真正走完「点击 + 快照比对」**。一个从不成功的普查照样吐出了一个
看起来像事实的整数 —— 而如果照单全收，它会变成账本里一条「导演台有 144 个死控件」
的结论。

## 144 是怎么来的：三条可复现的根因

| 根因 | 现象 | 修法 |
|---|---|---|
| 在同一页面上**累积点击** | 36 次 `TimeoutError` —— 后点的按钮被前面打开的面板/浮层挡住 | **每枚按钮一个全新页面** |
| 定位靠「文本 + 区域 + 像素 <3px」 | 108 条 `notFound` —— 任何一次重排都让它失效 | 按稳定键定位，且**校验后置条件** |
| 快照里含 `body.innerHTML.length` | 任何重渲染都让前后不等 | 换成结构化投影 |

另外 145 枚可见 button 里，**35 枚被遮挡**（顶栏 z-40 覆盖层 + 图边把手）、**13 枚在视口外**。
「够不着」和「惰性」是两个结论，普查必须分开。

## 698 那条读数被推翻了两处

| 属性 | 698 的读数 | 本批实测 |
|---|---|---|
| `data-director-create-motion-path`（时间轴） | 惰性 | **活的**：`aria-expanded` false→true，下拉 `[data-director-motion-path-menu]` 带出 3 个新面 |
| `data-director-camera-preset-trigger`（时间轴） | `disabled=false` | 初始态 **`disabled=true`** |
| `data-director-motion-preset-button`（右栏） | 惰性 | **初始态根本没渲染**；要走「选中机位 → 打关键帧 → 切运动轨迹页签」三步才出现 |
| `data-director-motion-create-path`（右栏） | 惰性 | 同上 |

698 的快照里**没有 `aria-expanded` 这一面，也没有「新出现的 DOM 面」这一面**，
于是一个真的会开下拉的按钮被读成了惰性。**698 不重写，纠正记在本批。**

## 修好之后的普查：14 枚入口类控件

工作区共 111 枚 button。本批普查其中 **14 枚「入口类」控件**（时间轴控制簇 12 +
右栏 motion 区 2）；对象树/视口/时间轴主体上的按钮是**逐对象的操作**而不是入口，
不在范围内。**每枚一个全新页面，零 store 写入。**

- **活 8 枚**：`playback` `auto-keyframe` `loop` `time-unit` `create-motion-path`
  `open-curve-editor` `remove-track` `delete-keyframe`
- **惰 4 枚**：`add-track` `add-keyframe`（新开态）`motion-preset-button` `motion-create-path`
- **够不着 2 枚**：`camera-preset-trigger`（`disabled`）`add-track-manual`（`disabled`）

## 剩下的真问题：惰性自证的四件套

项目对主画布早就立了合同（batch 358/359/360/364/366/367）：
**惰性控件必须自证 = `data-inert` + 非空 `title` + `cursor: default` + 去掉 hover 反馈。**

实测：

- **导演台 `data-inert` 一处都没有** —— 运行时 `[data-director-workspace] [data-inert]` = **0**，
  源码 `src/components/director/**` 内 = **0**；主画布顶层组件 = **40 处**。
- 右栏那两枚指路牌控件只补了**四件套里的一件**（`title`）：
  `title="预设运镜面板位于时间线控制簇"` ✅，但 `data-inert` = `null` ❌、
  `hover:bg-[#3d3d3d]` 的骗人反馈仍在 ❌。（`cursor: default` 这件它们做对了。）

这两枚**不是「坏掉的入口」** —— 它们的 `title` 明说面板在时间轴控制簇，
是**指路牌**。问题在于**指路牌本身没按合同自证**。

## 惰性/活性是「控件 × 状态」的函数

同一个属性、同一份代码、同一批页面，两次读数：

| 状态 | `data-director-add-keyframe` |
|---|---|
| 新开导演台 | **惰**（点了什么也不发生） |
| 选中机位之后 | **活**（`selectedKeyframeId` 改变） |

同理，「四个全部 `disabled=false`」在初始态就不成立（控制簇 12 枚里 2 枚 disabled），
而右栏那两枚不是 disabled，是**压根没渲染**。

**所以普查必须写明起始状态，否则连自己的两次测量都对不上。**

## 仪器也要体检

新增一步「**零点击自检**」：不点任何东西，隔 400ms 取两次快照，必须逐字相同。
本次 `nullClickDrift = []` —— 仪器自身的假阳性率是 0。
一个会自己抖的快照面会把每次点击都读成「有变化」，整个普查退化成恒真。

## 本批自己踩的坑（同一个错误换了五种装束）

1. 695 用错属性名查页签 → 0 个
2. 697 点「空白」点中道具桌 → 读数 `None`
3. 698 查 `create-motion-path` 查不到右栏那个
4. 699 第一遍普查 108 条 `notFound`
5. **本批探针自己把 `data-director-motion-path-menu` 写成 `data-director-path-menu`，再查出一个 0**

以及一个更隐蔽的变体：**对象树的可选行是 `div[role="treeitem"][data-director-object-id]`，
而「身上没有 `data-` 属性的裸行」是 5 个 24×24 的可见性切换图标。**
选择器错了，返回的却**长得像一个列表**（21 行、有 rect、有顺序）——
最难发现的一种错。**是后置条件校验（点完断言 `selectedObjectId`）把它拦下来的。**

还有三次同一个错：**读到 0 的时候，先怀疑自己快了一步。**
点完机位立刻查页签（0 个）、点完关键帧立刻查按钮（0 个）、
点完页签立刻查目标（0 个）—— 全是 React 重渲染还没发生。

## 判据

| 判据 | 断言 |
|---|---|
| `timeline-create-motion-path-is-live-not-an-empty-entrance` | 它是活控件，会开下拉（纠正 698） |
| `census-classifies-into-three-verdicts-and-the-instrument-is-calibrated` | 14 枚各有判定；标定对判对；零点击漂移为空 |
| `director-desk-has-no-inert-attestation-at-all` | workspace 内 `data-inert` = 0；两枚指路牌只补了 `title` |
| `enabled-is-a-function-of-state-not-a-property-of-a-control` | 初始态控制簇 2 枚 disabled；698 的「四个全部 enabled」不成立 |
| `inert-or-live-is-a-function-of-control-times-state` | `add-keyframe` 两态两判 |

## 不声称

- 不声称 `data-director-add-track` 是缺陷。它 enabled、有真 `onClick`
  （`createTrackForSelectedObject()`）、`trackCreatable` 为真，点了却什么都不发生 ——
  **但本批没有测出为什么**（一个自然的候选是「选中对象已经有轨道了」这个守卫，
  **未取证**）。**「点了没反应」是读数，关于成因的猜测不是读数。**
- 不声称右栏那两枚指路牌是「缺陷」而非「占位」。它们的 `title` 读起来像刻意指引。
- 不声称源站有同样情况（**未取证，需授权点击**）。
- 不声称这 14 枚覆盖了导演台全部入口（范围见上）。
- **不改 `src/`**

## 复现

```bash
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch699.py
```

需 dev server 跑在 4317。零 store 写入，14 枚各开一个新页面，约 60 秒。
