# batch 705 — 把普查做完：右栏 24 枚可输入控件的提交路径全表

## 起点

704 测了右栏 7 枚输入控件，然后诚实地写下
**「不声称其余 17 枚右栏 `input`/`select` 都有同样行为 —— 本批只测了 7 枚」**。

**普查停在 7/24 并标「未取证」是可以的，但既然能做，就把它做完。**

## 三条预测（写死在代码里，先于任何测量）

| | 预测 | 结果 |
|---|---|---|
| P1 | 多数输入控件把 `Enter` 当提交键 | **成立**（19/21） |
| P2 | `range` 没有提交步骤，不该混进 `Enter`/`Tab` 的比较 | **成立**（2 枚 range） |
| P3 | `select` 与 `text` 的提交行为不同 | **被推翻** |
| P4 | 每枚控件都有唯一稳定键，普查不按索引 | **成立**（24/24） |

**P3 被推翻，而被推翻的方向是「类别变少」**：
`camera-follow-target` 与 `camera-look-at-mode` 两个 `select`
与 `text` 完全一样，`Enter` 与 `Tab` 都提交。

## 全表（24 枚，唯一键 24 个）

| 判定 | 枚数 | 控件 |
|---|---|---|
| **忽略 `Enter`**（值留在框里、store 不动、连账都不记） | **2** | `shot-start` `shot-end` |
| `Enter` 与 `Tab` 都提交 | **19** | 其余全部适用控件 |
| 不适用 | 3 | `uniform-scale` / `camera-fov`（range，无提交步骤）<br>`camera-switch`（**只有一个选项，造不出差异**） |

**独立复现了 704 的读数**，而且这次是全覆盖：忽略 `Enter` 的**仍然只有那 2 枚**。

> 覆盖率最高的交叉核对就是这种：一个 7 样本的读数，被一张 24/24 的全表独立复现。

## 顺带一条：12 枚 `transform:*` 全走手势

`position` / `rotation` / `scale` / `target` 各 x/y/z 共 **12 枚数字框**，
提交后账上一律记 **`GESTURE_COMMIT` / `COMMITTED`**。

⟹ **在数字框里敲数字，和拖 3D 手柄，走的是同一套手势机制。**
一个看起来像独立 setter 的数字框，其实是手势的一个视图 ——
**这也解释了 704 那条「越界值会留下一个不自动收的手势」为什么可能发生**。

对比：`shot-start` 记 `UPDATE_SHOT`、`shot-end` 记 `GESTURE_BEGIN`。

## 本批自己踩的坑：第三态的第四个应用面

**「无变化」有两种：控件不提交，和我没造出差异。**

普查器三版各踩一次：

1. **第一版**给 `text` / `color` 填了它**已有的值** —— 那一列的「提交✓」其实全是
   `NOOP`（没东西可改）。
2. **第二版**改成真换值，又给 `hex-input` 造出 **`9bdcf2-X`** ——
   **那不是合法颜色**，于是它两侧都「无变化」。
3. 加上 **703** 那次测的是**越界**值（`9 > max 8`）。

⟹ **造出来的值必须是这个控件能接受的值**，否则读数落在第三态上。
本批给 `hex-input` 单独用**合法色值** `ff0000` 复测 —— 两侧都提交，
与 704 的读数一致。

## 判据

| 判据 | 断言 |
|---|---|
| `the-census-covers-all-24-controls-and-each-has-a-unique-key` | 24/24、唯一键 24 个、3 枚不适用**都写明理由**、无错误 |
| `exactly-two-controls-ignore-enter-and-they-are-the-two-shot-time-fields` | 忽略 `Enter` 的恰是那 2 枚；19 枚两侧都提交；0 枚两侧都不提交 |
| `select-fields-behave-like-text-fields-so-prediction-3-is-falsified` | 2 枚 select 两侧都提交 ⟹ P3 被推翻 |
| `the-twelve-transform-fields-go-through-the-gesture-machinery` | 12 枚一律记 `GESTURE_COMMIT` |

## 不声称

- 不声称 3 枚不适用的控件有问题 —— **它们的「不适用」是控件类型或 fixture 造成的，不是缺陷**。
- 不声称源站行为（**未取证，需授权点击**）。
- **不改 `src/`**

## 复现

```bash
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch705.py
```

需 dev server 跑在 4317。零 store 写入；提交全部用真实键盘事件。
