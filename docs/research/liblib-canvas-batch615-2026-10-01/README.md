# Batch 615 — 窄屏顶栏：「收起」钮不再被居中的视角切换器压住

日期：2026-10-01
验收脚本：`scripts/verify-liblib-batch615.py`（22 项，390×844 + 1920×1150 两腿）
取证脚本：`/tmp/src593/probe615.py`（顶栏 grid、四个直接子节点、逐枚命中测试）、`/tmp/src593/probe615b.py`（源站窄屏，只读、独立 tab）
参考图：`docs/design-references/liblib-header-mobile-615-390.png`、`liblib-header-mobile-615-1920.png`
顺手转绿：`scripts/verify-liblib-batch94.py`（此前整轮红）

## 靶心

这不是普查找出来的，是**回归一直红着**：`batch 94` 的移动端那条腿从本轮开始就没绿过。

```
Locator.click: Timeout 30000ms exceeded — waiting for
  locator("[data-director-panels-toggle]")
  … 56 × waiting for element to be visible, enabled and stable
    - <div class="flex h-9 w-[170px] …"> from
      <div role="group" aria-label="导演台视角"
           class="pointer-events-auto absolute left-1/2 top-2 z-10
                  -translate-x-1/2"> subtree intercepts pointer events
```

一枚画在屏幕上、却点不着的控件，与 batch 604 被吞掉的 prompt 胶囊、batch 611 被属性面板埋掉的导出按钮同类。

**基线对照**（`cp` 到 /tmp 再 `git checkout --`，不用 stash）确认：撤掉 613/614 后同样失败 —— 是既有缺陷，不是这两批的连带。

## 碰撞是怎么来的

`probe615` 在 390×844 上把顶栏整棵树量了出来：

```
header        [0,     0, 390,  52]  grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)]
  child[0]    [0,     0, 147.5,51]  左列 = minmax(0,1fr)，分到 (390-95)/2
    关闭       [8,     5.5, 40, 40]
    收起       [99.5,  5.5, 40, 40]   ← 右半被压
  child[1]    [147.5, 18, 95,  15]  中列（命令反馈）
  child[2]    [110,   8, 170, 36]   视角切换器 = 195 ± 85，absolute
  child[3]    [242.5, 0, 147.5,51]  右列
```

关键在 `child[2]`：视角切换器是 `absolute left-1/2 top-2 z-10 -translate-x-1/2` 加一条 **170px 定宽**的内行。它是绝对定位，**完全无视外层 grid**，直接骑在正中。390px 下它占 110..280，而左列分到 147.5、收起落在 99.5..139.5 —— 切换器左缘 110 切进按钮内 10.5px，把圆心（119.5）盖住了。

## 修法

给左列加一条窄屏上限：`max-w-[calc(50vw-85px)]`，85 = 170/2。

- 390px：左列收成 110，收起落到 62..102，与切换器 110 **相接不重叠**，命中测试回到自己的 `svg`。
- ≥900px：`50vw − 85 ≥ 395 > 280`，**该上限永不生效**，源站的 280px 定宽左头与 `关闭 @(0,5.5)` / `收起 @(240,5.5)` 一字未动 —— batch 606 的 28 条断言照旧全绿，本批验收里也把这两条读数单列出来钉住。

只压左列、不动右列：右列是 `justify-end`，控件靠右缘（≈320..382），与切换器右缘 280 不冲突（验收里 `导出` / `导入` 两枚的命中测试也断言了）。

## 顺带说明：源站窄屏**未**取证

`probe615b` 另开一个 tab、下 device-metrics override 到 390×844（**只作用于新 tab**，共享会话原 tab 全程未碰，也没发任何点击），结果落到的是**画布页** —— 导演台要点开才进。

所以源站在手机宽度下顶栏长什么样、会不会也撞，本批**不声称**。本批只做一件事：拿掉一枚点不动的控件，并且不动任何有源站读数支撑的桌面几何。

## 验收

- 390×844：切换器仍 170 宽仍居中；左列宽度 ≤ 切换器左缘；两者不重叠；`关闭` / `收起` / `导出` / `导入` 四枚逐枚 `elementFromPoint` 命中自己；点 `收起` 后 `data-director-panels-collapsed="true"`。
- 1920×1150：左列仍 280、`max-width` 上限不生效、`关闭 @(0,5.5,40,40)`、`收起 @(240,5.5,40,40)`、切换器仍 `@(875,…)`；并跑一遍 `收起` → `场景` 的收起/恢复往返，验证几何复原。

22/22。门禁另跑：`batch 94` **由红转绿**、`606`(28)、`614`(48)、`613`(53)、`605`(38)、`93`。

## 移动端那条腿的另一个约束

往返测试只放在桌面段：恢复入口是 rail 的「场景」项，而 rail 在 <900px 是 `hidden`（batch 573 的既有设计），窄屏下那条恢复路径本就不存在。窄屏腿只断言点击本身落地。

## 不声称

- 源站顶栏在手机宽度下的行为（未取证，见上）。
- 切换器 170px 这个宽度本身来自 batch 605 的桌面读数，本批保留不动。
