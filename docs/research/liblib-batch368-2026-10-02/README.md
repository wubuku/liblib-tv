# Batch 368 — 运行时扫描器打通面板面：12 处新暴露的骗人控件 + 三个判据盲区

日期：2026-10-02
范围：`src/components/`（含 `frameos/`，**不含** `director/` `jimeng/` 跨线目录）

## 起因：367 的普查口径太窄

batch 367 读源码 `<button>` 标签抓到 7 处死控件。但它要求按钮**「自称可点」**
（有 `aria-label` / `data-testid` / `role="button"`）才收。这个口径有两个洞：

1. **没有任何标记的裸 `<button>`** —— `SegmentReshootPanel` 的「参考」「标记」
   「角色库」三颗 pill 连 `aria-label` 都没有，却和同一行右侧**真能用的**
   「展开/收起」长得一模一样。367 一个都没抓到。
2. **有 `data-*` 但不是 `data-testid`** —— `data-panorama-add-reference` /
   `data-image-editor-model` / `data-mark-select-return` 全被漏掉。

证据（同一批面，源码普查 vs 运行时扫描）：

```text
源码普查:   1 个候选（还是那个已证实的 hover 目标误报）
运行时扫描: 14 个候选
```

所以 368 改用 359/360 已有的**运行时**扫描器（`SCAN_JS` / `classify`），
并复用 367 刚踩平 8 个坑才走通的导航路径，把扫描打到 9 个面板面上。

## 扫描结果：0 跳过，14 个候选

**`lyingAffordance = 0`** —— 这是对 367 修复的独立交叉验证：我给 7 个控件加的
`data-inert` 没有一个漏掉 `hover:`。这条判据本来是为 360 加的元缺陷检查，
这次正好用来查自己上一批的账。

14 个候选逐个定性：

| 候选 | 定性 |
|---|---|
| `<a download>` ×4 | **扫描器盲区**（见下）—— `<a href download>` 有原生行为，不经 React handler |
| `data-subtitle-erase-help` | 367 已证实的 **hover 目标**浮层，有行为，不能动 |
| `+参考` / `Lib Image` / `2:1 · 标准画质` | 全景分支 3 处真死控件 |
| `参考` / `标记` / `角色库` | 片段重拍 3 处真死（**367 口径漏掉的**） |
| `2.5` / `720P · 1个` | 片段重拍 2 处真死，带 `ChevronDown` 下拉箭头 |
| `返回节点` | 标记选择横幅，与 367 修的「关闭」并排 |

## 三个判据盲区

### 1. `SELF_CLAIM` 口径太窄

改法：**全都收**，把「自称」降级成 `selfClaim` 标签。
`selfClaim: false` 的候选**更值得看** —— 它连自己是个控件都没说清楚。

口径放宽后普查从 1 项涨到 10 项，又捞出 4 个运行时扫描没覆盖的：

- `nodes/ScriptGeneratorNode.tsx` 「参考图」—— 虚线框，标准「点这里能上传」视觉语言
- `StoryboardScriptEditor.tsx` 「一键合成全部提示词」
- `frameos/FrameosGroupToolbar.tsx` 「整组执行」
- `VideoGenerationPanel.tsx` 的 pill 兜底分支

### 2. 裸块注释没剥 —— **我为修复写的说明文档，反过来制造了一个新误报**

我给 `SegmentReshootPanel` 写修复说明时用了这种写法：

```jsx
return (
  /* Batch 368: …按「<button> 即控件」的口径… */
  <button ... />
)
```

这是**表达式位置**的 JS 块注释，外面**没有花括号**。而工具只剥 `{/* */}`
和 `//`，于是注释里那句字面量 `<button>` 被当成真标签扫了出来。

> **判据必须扛得住源码里出现「关于判据本身的文字」**，否则每修一次就多一个假阳。

### 3. `<a href>` 被误判成死控件，且**无 href 的 `<a>` 根本进不了扫描**

原选择器是 `a[href]`，`wired` 只认 React 的 `onClick/onChange/onInput`。
两个洞叠在一起：有 href 的被判死（4 个面板各一次），**没有 href 的压根不收** ——
而「看起来是链接、点了什么也不发生」最经典的形态恰恰是 `<a>` 无 href。

补法：`a` 全收，由 `nativeAnchor` 决定 `wired`；空 href / `href="#"` 仍判死。
本仓库画布本体当前只有一处 `<a>`（带 href + download），所以这是**修判据**不是修产品。

## 处置：12 处让 UI 停止撒谎，不发明

源站行为全部未采样（人机验证阻塞）；其中「积分」「整组执行」「一键合成全部提示词」
关联付费，**永不接线**。同 batch 358/359/360/364/366/367：去悬停骗人反馈 +
`cursor: default` + `title` 说明 + `data-inert` 自证惰性，几何文案不动。

| 组件 | 控件 | 尺寸（未变） |
|---|---|---|
| `ImageEditPanel` | `+参考`（全景） | h-26 |
| `ImageEditPanel` | `Lib Image`（全景） | h-8 |
| `ImageEditPanel` | `2:1 · 标准画质`（全景） | h-8 |
| `SegmentReshootPanel` | 参考 / 标记 / 角色库 | h-7 ×3 |
| `SegmentReshootPanel` | `2.5`（积分） | h-8 |
| `SegmentReshootPanel` | `720P · 1个` | h-8 |
| `VideoGenerationPanel` | `返回节点` | — |
| `StoryboardScriptEditor` | 一键合成全部提示词 | — |
| `nodes/ScriptGeneratorNode` | 参考图 | h-8 |
| `frameos/FrameosGroupToolbar` | 整组执行 | — |

**三处值得单说**：

1. **同一面板的两个 variant 处置不一致**。`ImageEditPanel` 的主分支里
   `data-image-editor-settings` **早在本批之前就修好了**（带 `data-inert`），
   `data-image-editor-footer-icon` 也修好了 —— 而**全景分支**这一支的同款按钮
   没人管。按 variant 分支写代码最容易漏的就是这一支。
2. **两处是「处置只做了一半」的补齐**：
   - 「一键合成全部提示词」**早就有 title** 写明「clone 不触发」，说明当初知道它
     不干活。但缺 `data-inert`，而且 `hover:bg-white` 还在。
     **「有 title 就算自证」不成立** —— title 要悬停才看得见，视觉承诺已经先给出去了。
   - 「整组执行」**早就有 `cursor: default` + 变暗**，同样只做了一半，缺
     `data-inert` 和 `title`。
3. **「2.5」带 `Gem`（钻石）图标 + `ChevronDown` 下拉箭头** —— 下拉箭头是
   「点开有菜单」最强的视觉承诺，这里是纯骗，而且它关联付费。

## 只记录不改动：够不着 ≠ 骗人

- **`CameraConfigDialog.tsx` 4 处**：**全仓库无人 import**，连 director 也没引用。
  是死代码（554 行），不是骗人控件 —— 用户永远看不到。
  （此前记为「属导演台跨线范围」，实测 director 也没引用，是纯顶层死代码。）
- **`VideoGenerationPanel.tsx:499` 的 pill 兜底分支**：5 个 pill 全部有 `hasMenu`
  或专门分支，这行是**给不存在的 label 留的**，当前不可达。改它没有用户可见效果。
  但它是**潜在陷阱**：将来加一个没处理的新 pill，会静默变成骗人控件。

## 门禁 90 项

1. **防假零**：12 处必须真的走到，走不到直接红；
2. 每处 `data-inert` + 非空 `title` + `cursor: default` + **无 hover 类**；
3. **几何未变**：class 尺寸 token 精确比对；
4. **反向断言**：同一面里**真能用的**控件没被改 inert
   （「展开片段重拍编辑器」「提交片段重拍」「生成720全景图」「标记」…）；
5. **判据自身的双向自检**：
   - 植入 1 死 2 好 → 普查必须只报 1 个，且它的 `selfClaim` 必须是 `False`；
   - 裸 `/* */` 注释里的 `<button>` 不得被扫出；
   - `<a href>` 不得再被判死，空 href / 无 href 必须仍被判死；
6. 源码普查残余必须**只落在**「够不着」白名单，且白名单**项数也要对**
   （少一个说明有人顺手清理了死代码，那要人来定）；
7. 诊断零错误。

### 门禁连带更新：367 的断言

拓宽口径后 367 的 `source-census:no-plain-dead-buttons`（要求 0）如实变红。
断言的**意图没变**（「不许出现会骗用户的死控件」），但「够不着」与「骗人」必须
分开记：改成白名单形式，按**文件+行**写死，不按文件名开口子。

### 变异测试（三项，全部精确红在对应断言）

| 变异 | 结果 |
|---|---|
| 把 `hover:` 加回三颗 pill | 三条 `class-has-no-hover`（共用 class 串，一处改动三处生效） |
| 把**真能用的**「标记」pill 误标 inert | `live:[data-mark-select-trigger]` + `source-census:residual-only-allowlisted` **两层同时红** |
| 关掉裸注释剥离 + 选择器退回 `a[href]` | **四条**同时红：注释剥离自检、植入阳性、`<a>` 空 href 判死、普查残余 |

**门禁自己踩的两个坑**（都记在脚本注释里）：
- `button:text-is("2.5")` 匹配不到「文本包在子 `<span>` 里」的按钮 → 改用 JS
  比对 `textContent.trim()`；
- `page.evaluate` 返回的是**反序列化后的普通对象**，没有 `.evaluate` 方法 →
  找元素和采事实必须在同一个 evaluate 里做完。

## 回归

- 本批门禁 **90/90**
- 共享 `SCAN_JS` 改动的三个下游门禁：359 / 360 / 364 全过
- 367（断言更新后）全过；366 / 531 / 534 全过
- FrameOS 侧：347（21）/ 356（34）/ 357（40）全过
- `tsc --noEmit` 干净
- `verify-assertions.py`：570 个脚本 0 个空洞断言
- `verify-docs.py`：1293 文件 / 5656 目标 / 0 缺失

## 产物

- `scripts/probe_liblib_batch368_panel_runtime.py` —— 9 个面的运行时普查
- `scripts/verify-liblib-batch368.py` —— 90 项门禁
- `runtime-panel-census.json` / `verify.json`
- 改动：`probe_liblib_batch367_dead_buttons.py`（口径 + 注释剥离）、
  `probe_liblib_batch359_node_surfaces.py`（`<a>` 选择器 + nativeAnchor）、
  `verify-liblib-batch367.py`（断言改白名单）
