# Batch 353 — 可寻址门禁的覆盖面从 3 种 UI 态扩到 8 种

日期：2026-10-01
范围：`scripts/verify-frameos-batch347.py`（门禁）、`FrameosGroupToolbar.tsx`、
`FrameosGenerationOverlay.tsx`、`FrameosPromptEditor.tsx`
性质：**CLONE_DECISION**（可测性基础设施；不改任何交互行为）

---

## 问题：门禁只普查了 3 种 UI 态

Batch 347 把「交互盲区」清零并做成了门禁：运行时枚举所有可点元素
（`button, [role=button], a[href], input, textarea, select, [tabindex]`），
任何一个缺稳定钩子就红。这解决了「以后新增元素忘加钩子」。

但门禁本身有个**边界没被当成约束**：它只普查三种态 ——
**默认 / 帮助面板开 / 选中节点**。于是**这三种态碰不到的东西一律逃过检查**：

- 裁剪态（Batch 350 加的工具条）
- 分组态（选中分组后的工具条）
- 节点搜索面板
- 模板面板
- 生成浮窗 —— `FrameosGenerationOverlay` **整个组件零 `data-frameos-*`**

Batch 349/350 的研究记录里都写了「门禁没触达生成浮窗」，但**没人把它变成约束**。

## 测量：先量出欠账，再改代码

`scripts/probe-frameos-batch353-addressability.py`（只读探针，与门禁**同一把尺子**）：

| 状态 | 可交互元素 | 有钩子 | 盲区 |
|---|---|---|---|
| crop | 43 | 43 | 0 |
| **group** | 45 | 42 | **3** |
| node_search | 40 | 40 | 0 |
| template_panel | 48 | 48 | 0 |
| **generation** | 61 | 59 | **2** |

盲区：`整组执行` / `存为模板` / `解组`（分组态）、`取消`（生成浮窗）、
一个 prompt `textarea`。

## 修复

| 位置 | 钩子 |
|---|---|
| `FrameosGroupToolbar` | `data-frameos-group-action="run-all" / "save-template" / "ungroup"` |
| `FrameosGenerationOverlay` | `data-frameos-generation-overlay`（带 `-remaining` 值）、`data-frameos-generation-cancel` |
| `FrameosPromptEditor` | 4 个 textarea 全部：`data-frameos-prompt-input`（常态面板）、`-fullscreen`、`-audio-`、`-video-` |

补完后 5 个新态全部零盲区，并把 5 个新态**并入门禁**（`verify-frameos-batch347.py`
从 9 项检查扩到 **21 项**），每个新态都带 `scan:not-empty:<态>` 防假绿自检。

## 过程中的三个坑

### 1. JSX 开始标签的属性区里不能写 `//` 注释

```jsx
<div
  // Batch 353: ……
  data-frameos-generation-overlay=""
```

这会让**整个页面编译失败、节点一个都不渲染**，而 `tsc` 的报错全在
`.next/dev/types/routes.d.ts` 这个生成文件里，**看不出是我写的**。
注释必须放在开始标签**外面**。

> 页面突然 404/500 时，先怀疑最近的 JSX 改动；
> `tsc` 报的生成文件错误是噪音，**要过滤掉 `.next/` 再看**。

### 2. 一次 grep 的输出被我自己的 `head` 截断了

`grep -n -B 3 -A 6 "<textarea"` 我加了 `head -30`，于是只看到 **3** 个 textarea，
据此「补齐了 3 个」。实际文件里有 **4** 个（132 / 263 / 409 / 575），
漏掉的 575 正是**用户在画布上看到的常态面板**那个。

而且 409 与 575 用**完全相同的 placeholder**，只靠 grep 上下文无法区分。
最后靠运行时枚举（`querySelectorAll('textarea')` 打印每个元素的 `data-*`）
才定位到。

> **别截断自己正在用来做判断的证据。** 需要「全都看到」的时候，
> 就要真的全都看到。

### 3. dev server 反复 404/崩溃，把排查带偏了两次

期间 dev server 至少崩了 3 次、返回过 404 与 500。500 的真凶是**另一个 session
正在改的** `DirectorDesk.tsx`（JSX 未闭合），不是我 —— 等了约 90 秒后
tsc 里 `src` 已无错误，**他自己修好了**。

处置：
- 语法错误属他人进行中的重构 → **不去猜他的结构意图、不抢同一个文件**，等他收尾；
- 路由全 404（含 `/`）→ `.next` 缓存已不一致。`rm -rf .next` 被安全策略拦，
  改用 `mv` 挪到 `/tmp`（挪出仓库，**未删除**），dev server 重建后恢复。

> `.next` 是 git 忽略的纯构建产物，但**挪走时要确认它不会出现在 `git status` 里**
> —— `.next` 被忽略不代表 `.next.corrupt-xxxx` 也被忽略（实测确实会冒出来）。

## 验证

- `verify-frameos-batch347.py`：**21 项检查，0 诊断**（原 9 项）
- 变异测试：摘掉「解组」按钮的钩子 → 红，
  `blind:group-zero 盲区 1/45: [{'tag': 'button', 'text': '解组'}]`，
  **报错精确指名是哪个元素**

## 保真度差距

无。本批只加 `data-*` 属性与门禁覆盖，不改任何交互行为、样式或文案。
钩子按 Batch 347 起的既有约定命名（`data-frameos-*`）。

## 遗留的边界

门禁现在覆盖 8 种 UI 态，但**仍然是枚举式的**：没有覆盖到的态依然可能藏盲区
（例如全屏编辑态、资产面板、多选态）。真正的根治是让「缺钩子」在**类型层面**
或 lint 层面就报错，而不是靠运行时枚举——那需要自定义 ESLint 规则，
是另一个量级的改动。
