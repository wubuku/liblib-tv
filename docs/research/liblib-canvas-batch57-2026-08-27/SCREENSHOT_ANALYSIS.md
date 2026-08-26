# Batch 57 截图分析：普通画布连接事务

> **Purpose**: 记录本批首次截图识别结果，避免后续重复消耗视觉识别成本。
> **Status**: `PENDING_CAPTURE`

## 1. 现有证据

本批尚未新增截图。现阶段以 DOM、React Flow state 和 pure validator 结果作为主要
验证证据；source static evidence 见 [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)。

## 2. 预定截图

| 文件 | 来源 | viewport | 状态 |
|---|---|---:|---|
| `clone-batch57-connection-accepted-desktop-*.png` | 本地 clone | 1440px | 待捕获 |
| `clone-batch57-connection-accepted-mobile-*.png` | 本地 clone | 390px | 待捕获 |

## 3. 识图边界

- 只识别 accepted connection 的节点、Handle、edge 和既有画布层级。
- rejected cases 优先使用 state/history 断言；只有出现新的视觉问题时才截图。
- 首次识别后把 viewport、交互状态、几何关系和不确定项写回本文件。
