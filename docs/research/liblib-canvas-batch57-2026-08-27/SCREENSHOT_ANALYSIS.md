# Batch 57 截图分析：普通画布连接事务

> **Purpose**: 记录本批首次截图识别结果，避免后续重复消耗视觉识别成本。
> **Status**: `RECORDED`（首次识别：2026-08-27）。

## 1. 现有证据

本批新增两张 clone runtime 截图。主要验收证据仍是 DOM、React Flow state、
history 和 pure validator；截图只记录 accepted connection 的可见层级，不替代
state 断言。source static evidence 见 [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)。

## 2. 截图清单

| 文件 | 来源 | viewport | 状态 |
|---|---|---:|---|
| [`liblib-clone-batch57-connection-accepted-desktop-929-2026-08-27.png`](../../design-references/liblib-clone-batch57-connection-accepted-desktop-929-2026-08-27.png) | 本地 clone | `929x874` | accepted edge，redo 前 |
| [`liblib-clone-batch57-connection-accepted-mobile-390-2026-08-27.png`](../../design-references/liblib-clone-batch57-connection-accepted-mobile-390-2026-08-27.png) | 本地 clone | `390x844` | accepted edge，redo 前 |

## 3. 首次识别结果

识别范围：两张截图均来自 Batch 57 verifier 的 accepted source-start
connection 场景；`deviceScaleFactor=1`；截图采集点位于 accepted edge 写入后、
undo 前，因而保留 target node 的既有 selection。

### Desktop `929x874`

- 深色 React Flow 画布、顶部导航、底部工具栏和既有网格/边视觉保持现状；
- 两个普通 text node 同时可见，中间为一条从 source Handle 指向 target Handle
  的连接线；
- 连接线使用现有 `DeletableEdge` renderer，没有新增连接气泡、toast 或错误
  提示层；
- 节点及连接整体位于画布工作区内，未出现 page/body 横向溢出；
- 截图只显示 accepted 结果，不证明 source invalid gesture 的反馈状态。

### Mobile `390x844`

- 画布在窄视口保持可操作的缩放布局，两个节点与连接线仍可见；
- 顶部/底部 shell 继续使用现有移动端布局，没有为连接事务新增独立面板；
- 没有观察到 document/body 横向滚动；
- 连接线和 Handle 仍属于原有 React Flow 图层，未被额外的 `+` overlay 覆盖。

### 证据分层

| 观察 | 类型 |
|---|---|
| 节点、Handle、edge 和 shell 的可见层级 | clone screenshot fact |
| viewport、edge identity、selection/history 数值 | DOM/store-backed fact，见 `runtime-audit.json` |
| source 的 duplicate/self/cycle 结构信号 | source static evidence，见 `SOURCE_EVIDENCE.md` |
| 未新增 invalid feedback、Reference exception 或 domain compatibility | 未确认/本批边界 |

## 4. 识图边界

- 只识别 accepted connection 的节点、Handle、edge 和既有画布层级。
- rejected cases 优先使用 state/history 断言；只有出现新的视觉问题时才截图。
- 后续 verifier 重跑不得重复识别相同截图；如截图文件、viewport、代码状态或
  研究问题未变化，直接读取本台账。
