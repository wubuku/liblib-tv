# Batch 359 — 普查扩到节点编辑面：39 个死控件，以及三次假零

日期：2026-10-01
工具：`scripts/probe_liblib_batch359_node_surfaces.py`（运行时，双类判据）
门禁：`scripts/verify-liblib-batch359.py`（52 项）

## 为什么做这一批

Batch 358 普查的是**画布外框**的 16 个态。节点一被选中，浮出来的是另一整片界面——
图片节点浮动工具条、图片编辑面板、标注模式工具条、视频片段编辑面板——
**这片面一次都没普查过**，而 frameos batch 350 那个「裁剪宽高静默丢弃输入」正是在
节点级编辑态里。

## 结果：39 个死控件

「静默丢弃输入」这一类：**0 命中**，且做过功能抽检（见下）。
「点了没反应」这一类：**39 个**，全部集中在两个文件：

| 位置 | 控件 |
|---|---|
| `ImageEditPanel` | 展开编辑器、参考/标记/风格、比例·画质·分辨率、高级设置（两个变体各一）、翻译、撤销 |
| `VideoGenerationPanel` | doc-sparkle、翻译视频提示词、settings2 |

整个图片编辑器面板里**只有「生成图片」和模型菜单是真接线的**（全文件 6 处 `onClick`：
引用、移除参考、模型菜单、智能引用 AutoLink、生成图片 ×2）。这是整个应用的主创作面。

对照组很说明问题：视频片段面板的「展开智能剪辑编辑器」**已经诚实报告**了
「本地原型：展开编辑器未连接」——同一类问题在那边早就解决过了，
图片编辑器这边却一直挂着悬停反馈假装能用。

## 修法

与 batch 358 完全一致：**保持启用 + 去掉悬停骗人的反馈 + `cursor: default` +
`title` 说明 + `data-inert` 标记**。文案与几何一律不动——既有门禁 `batch10`
断的正是 `54×26` / `32×32` 与文案。

标记用 `data-inert` 而不是 `aria-disabled`：**Playwright 的 `is_disabled()` 把
`aria-disabled` 也算作禁用**，加上它会撞上钉住启用态的门禁（batch 357/358 各踩过一次）。

## 「静默丢弃输入」这一类的 0 是可信的

`onChange` 存在只是**必要条件**——frameos batch 350 的裁剪框就是「有 handler、
值进了 store、但没有任何代码读它」。所以做了功能抽检：

- 风格库搜索：16 张卡 → 敲不存在的词 → **0 张**
- 特效库搜索：24 张 → **0 张**
- 工作区改名：输入生效

## 这批真正的收获：三次假零

普查工具最危险的失败模式不是报错，是**安静地什么都没测，然后报「无问题」**。
本批实际拦下三次，而且每一次都是先看到「0」再去怀疑它：

1. **画布没 hydration 完** —— 一轮 `wait_for_timeout(1500)` 没等到，`node_ids` 拿到
   空数组，探针「跑完」并报 0 问题 / 0 死控件。**假零。**
   现在显式 `wait_for_selector('.react-flow__node')`，节点为空直接抛错。
2. **标注模式没打开** —— 工具条带 scale transform，页面内 `el.click()` 点不动它。
   第一版标注态的 testid 集合是空的、控件数反而从 ~50 掉到 39，却照样显示「无问题」。
   三连跑里还**间歇性**失败（第 2 轮有一个 False）。现在先 `click(force=True)`、
   失败退回派发、**有界重试**直到标注工具条真的出现，仍打不开就红。
3. **⚠️ 扫描器把要找的缺陷预先滤掉了** —— 这个最讽刺，是我在 batch 358 批评过
   别人的同一个错误，自己又犯了一遍：node 探针里写了「有 handler **或**
   `cursor:pointer` 才收」，而 Tailwind 下 `<button>` 的 computed cursor 是 `default`
   不是 `pointer`——于是**没有 handler 的按钮在判定之前就被丢掉**，死控件判据
   根本没有机会触发。变异测试红在了下游的 `annotate:opened` 上而不是死控件断言上，
   这才暴露出来。
   修法与 batch 358 相同：**凡是自称控件的元素（`<button>` / `role=button` /
   `data-testid` / `aria-label`）一律收，不看 cursor**。
   一改就是 39 个。

   顺带修掉一条**不成立的豁免**：原先「祖先有 handler 就放过」对
   `ImageToolbar` 是错的——工具条容器上是 `onClick={(e) => e.stopPropagation()}`，
   阻止冒泡，什么也不做。现在自称控件的元素必须**自己**有 handler。

## 变异测试

| 变异 | 结果 |
|---|---|
| 摘掉图片提示词框的 `onChange` | 红（`no-silent-discard`，指名那个 textarea） |
| 整个摘掉 ImageToolbar 动作按钮的 `onClick` | 红（`no-dead-control`，指名那个按钮） |

> 第二项第一版写成了 `onClick={() => undefined}`——函数还在，普查认为「已接线」，
> 死控件判据不触发。**要让判据生效，必须让 handler 真的不存在。**

## 顺带修掉一处**别人批次引入的回归**

跑受影响验证器时 `verify-liblib-batch25` 红了。查下来与本批改动**无关**——
它只用 `data-video-clip-*` 选择器，与 `ImageEditPanel` / `VideoGenerationPanel`
零交集；引入点是提交 `612689b1`（batch 477「clip panel status disposition」）：

```diff
-  const [status, setStatus] = useState("");
+  const [status, setStatus] = useState<{ text: string; tone: ... }>({...});
-          {status && (
+          {status && (          // ← 对象永远 truthy
```

`status` 从字符串改成对象后，`{status && ...}` **恒真**：即使
`setStatus({ text: "", ... })` 把文案清空，这行状态区仍然渲染，在提示词下面
**永久占一行空白**（`pb-2`）。batch25 的 `count() == 0` 断言就是这么红的。

判据应是「有没有文案」，不是「对象存不存在」—— 改成 `{status.text && (`，
既保留 batch 477 加的 `data-status-tone` 与对象模型，又恢复原意。batch25 随即通过。

> 与本会话早先修的 `verify-liblib-batch612` 恒真断言是同一类问题：
> 仓库里的门禁会因别的批次改动而红。**先查是谁、什么时候引入的**，再决定改代码
> 还是改断言——不要默认是自己造成的，也不要因为「不是我弄的」就不管。

## 覆盖下界

门禁要求：节点数 ≥ 8、节点面 ≥ 8、控件总数 ≥ 300、输入控件 ≥ 10、至少 3 个节点
进到标注模式。界面长大后门禁会要求重新枚举，而不是安静地少测。

当前实测：16 个画布态 + 15 个节点面（5 个标注态）、**709 个控件**、29 个输入控件。
