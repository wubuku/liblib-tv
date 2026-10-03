# batch 704 — 「Enter 不提交、失焦才提交」，以及一次被拒绝的编辑在账本上留下的两条记录

## 起点

703 顺带查出一件事并写进了账本：`[data-director-shot-end]` 能输入、能聚焦，
但 `Enter` / `ArrowUp` / `Tab` 三条路径**全部进不去 store**，于是 703 把它归成
**「第四类：能输入但没有提交路径」**。

**这条结论是错的，而且错在两个地方。** 本批把它取回来。

## 703 错在哪

**① 703 填的是 12，而这个输入框的 `max` 就是 `duration`（=8）。**
填一个**范围内的值**（6）再按 `Tab` —— **提交成功**，区间标签同步变成 `0.0-6.0s`。

所以「没有提交路径」是错的：**提交路径存在，就是失焦。**

**② 「第四类」这个分类是 703 自己造的，704 把它拆掉。**
它不是「没有提交路径」，而是「**提交路径只有失焦、没有回车**」——
这个说法一旦放进普查表，立刻显示出它不是一类，而是**两个具体字段的行为**。

## 普查（7 枚输入控件 + 1 个越界样本，每格一个全新页面）

| 控件 | 新值 | 在 `[min,max]` 内 | 按 `Enter` | 按 `Tab` | 记账 |
|---|---|---|---|---|---|
| `object-name` | 改名试试A | 是 | 提交 ✓ | 提交 ✓ | `UPDATE_OBJECT` |
| `shot-name` | 镜头改名B | 是 | 提交 ✓ | 提交 ✓ | `UPDATE_SHOT` |
| **`shot-start`** | 2 | 是 | **留着但不提交** | 提交 ✓ | `UPDATE_SHOT` |
| **`shot-end`** | 6 | 是 | **留着但不提交** | 提交 ✓ | **`GESTURE_BEGIN`** |
| **`shot-end`** | **9（越界）** | **否** | **留着但不提交** | 输入框回弹 8 | **`GESTURE_BEGIN`/`COMMITTED`** |
| `camera-fov-number` | 50 | 是 | 提交 ✓ | 提交 ✓ | `UPDATE_CAMERA` |
| `hex-input` | ff0000 | 是 | 提交 ✓ | 提交 ✓ | `UPDATE_OBJECT` |
| `transform-field position/x` | 3.5 | 是 | 提交 ✓ | 提交 ✓ | `GESTURE_COMMIT` |

**7 枚里只有 2 枚（`shot-start` / `shot-end`）忽略 `Enter`。**
「留着但不提交」= 值留在输入框里、store 不动、**连一条命令都不记** ——
这不是拒绝，是**什么都没发生**。

## 越界样本：一次被拒绝的编辑，在账本上是两条相隔任意时间的记录

| 阶段 | `activeGesture` | `shotEnd` | `pastLen` | 账上最后一条 |
|---|---|---|---|---|
| 初始 | `null` | 8 | 0 | `null` |
| 填 9 按 `Tab` | **SET** | 8 | 0 | **`GESTURE_BEGIN` / `COMMITTED`** |
| +2.5s 复查 | **SET**（不自动收） | 8 | 0 | `GESTURE_BEGIN` / `COMMITTED` |
| 点画布空白收尾 | `null` | 8 | 0 | **`GESTURE_COMMIT` / `NOOP`** |
| 改另一个字段收尾 | `null` | 8 | 0→1 | **`UPDATE_OBJECT` / `COMMITTED`** |

**镜头区间一个叶子都没变、历史没长、输入框弹回 8 —— 用户什么也没得到；
而账本当场写的是 `COMMITTED`。**

那句 `NOOP` 要等下一个动作触发收尾才出现，**而且补不补得上取决于下一个动作是什么**：
点画布才会写 `NOOP`；改另一个字段的话，账上留下的是**那次编辑自己的** `COMMITTED`，
被拒手势的 `NOOP` 压根没出现过。

## 判据

| 判据 | 断言 |
|---|---|
| `enter-commits-for-every-input-except-the-two-shot-time-fields` | 普查表逐行：只有那两个时间字段的 `Enter` 不提交 |
| `the-two-shot-time-fields-are-siblings-on-different-command-paths` | `shot-start` → `UPDATE_SHOT`，`shot-end` → `GESTURE_BEGIN` |
| `a-rejected-edit-is-ledgered-as-committed-and-leaves-an-open-gesture` | 越界编辑当场记 `COMMITTED`、手势不自动收、两种收尾留下不同的最后一条账 |
| `correction-to-703-...` | 撤回「没有提交路径」，说明 703 的读数为何仍为真 |

## 本批自己踩的坑：第三次「读面太窄」

判据 3 第一版写的是「**`COMMITTED` 却不改状态**」，依据是只读了 `shots[0].endTime`。
**全 store 逐叶投影一照，变了 119 个叶子** —— 全是 `history.activeGesture`
（`null` → 一整份文档基线快照）。所以「什么都没发生」也是错的。

⟹ 这是同一个错误的第三次：**699** 的 `time-unit`（只读 store，看不见组件局部 `useState`）、
**703** 的「没有提交路径」（只试三个键、且值越界）、**704** 的「不改状态」（只读一个字段）。
**读面的宽度决定了结论的形状，而宽度是被上一个错误的结果选出来的，不是被设计出来的。**

## 不声称

- 不声称这是缺陷还是刻意的交互取舍（**源站未取证，需授权点击**）。
- 不声称 `GESTURE_BEGIN` 这个命令名意味着实现上走了拖拽手势 ——
  **那只是名字，读数只到「命令名不同」**。
- 不声称其余 17 枚右栏 `input`/`select` 都有同样行为 —— 本批只测了 7 枚有代表性的。
- **不改 `src/`**

## 复现

```bash
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch704.py
```

需 dev server 跑在 4317。零 store 写入；提交全部用真实键盘事件。
