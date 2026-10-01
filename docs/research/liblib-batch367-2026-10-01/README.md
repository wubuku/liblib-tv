# Batch 367 — 普查工具自己的两个洞，和 7 处「自称可点却什么都不发生」的控件

日期：2026-10-01
范围：`src/components/`（画布本体，**不含** `director/` `jimeng/` 跨线目录）

## 起因：上一批留下的可测性债务

Batch 366 的发现是：覆盖普查用 `data-*` 标记衡量「这个面有没有被验证过」，
但**标记体系本身有洞** —— `StoryboardScriptEditor` 几十个 `<button>` 里只有
一个带标记，于是「标记覆盖率」会**低估**组件的控件数，死控件藏在没标记的那些里。

所以 batch 367 先补一个**不依赖标记**的判据：直接扫源码里的 `<button>`。

## 一、普查工具自己的两个洞

`probe_liblib_batch367_dead_buttons.py` 第一次跑出 8 个候选，**但它自己的两个洞
比这 8 个候选更值得记**。两个都是靠阳性对照抓出来的，不是靠读代码看出来的。

### 洞 1：`glob` 不递归，`src/components/nodes/` 整片失明

第一版用 `COMPONENTS.glob("*.tsx")` —— 非递归。于是 `src/components/nodes/`
（16 个 tsx，**画布本体核心**：`VideoNode` / `ImageNode` / `ShotBreakdownResultNode`
都在这儿）完全没被扫到。

关键在于：**batch 364 亲手修掉的「播放视频」死控件就在 `nodes/VideoNode.tsx`**。
也就是说，上一批**已经证明这条线存在这类缺陷**，而普查工具对它完全失明。

**怎么抓到的**：往 `nodes/` 塞一个明知死掉的 `ZzProbeTmp`，工具**报不出来**。
下界不成立，不是「大概没问题」而是「根本没看」。

> **教训：判据的下界必须在「你以为覆盖的每个目录」上分别验证，不能只在顶层验一次。**
> 顶层验过了不等于整棵树验过了。

### 洞 2：跨线判定撞小写目录名

改成 `rglob` 之后，42 个 `jimeng/` 文件全被当成本线候选报了出来 ——
`CROSS_LINE = ("Director", "Jimeng")` 里写的是驼峰，而目录名是**小写** `jimeng/`，
`startswith` 不匹配。

这个方向的错误比漏报更糟：**跨线一旦被误扫，就会把别人的 WIP 报成候选、
诱导后续去改**。所以按相对路径的每一段做**大小写无关**判定。

### 自检

两个洞都是双向验的：

- **下界**：`nodes/ZzProbeTmp` 的明知死按钮被报出；
- **上界**：同文件的「已接线 / 已 inert / 已禁用」三个阴性对照都不报；
- **跨线**：`rglob` 后输出里 `jimeng` / `director` 出现 0 次。

## 二、源码普查只报候选：8 项可达性实测

`probe_liblib_batch367_reachability.py` 逐个走到那 7 处，采运行时事实
（`visible` / `inViewport` / `title` / `data-inert` / `disabled` / `cursor` / rect）。

**第一版 8 项里跳过 7 项。** 入口选择器全是猜的，逐个回源码核对后每一处都猜错了：

| 候选 | 我猜的 | 真实情况 |
|---|---|---|
| 片段重拍 | `[data-video-tool='reshoot']` | 根本没这种标记，是 `ToolbarButton label="片段重拍"`，靠文本找 |
| 去字幕说明 | 往节点 data 写 `subtitleMode` | `subtitleMode` 是**从 `activeTool` 派生**的，写 node data 完全无效 |
| 参考选择横幅 | `data-reference-select-trigger` | 它开的是 refSelectMode；「关闭」在 **`markSelectMode`** 横幅里 |
| 添加节点 | `Alt+Shift+S` / 双击画布 | 侧栏 `button[aria-label="添加节点"]`；主菜单 `script` 只**开子菜单**不建节点 |
| 准备资产 | 找 tab 标记 | 不是 tab，是 `data-storyboard-next="assets"` 那颗「下一步」 |
| 展开全景编辑器 | 选中图片节点即可 | 它在 `variant === "panorama"` 分支里，得先经「全景」派生节点 |
| 图片节点选择 | `.first` | 5 个图片节点有 4 个在**视口左侧外面**（x = -514 / -368），点了个空气 |

还踩了 **stale state**：调完 `addNodeAtPosition` 仍用调用前捕获的
`const s = ...getState()` 读画布 —— zustand 的 state 是不可变快照，旧引用永远是旧的。

以及一个更隐蔽的：**`store.setViewport({...})` 改不动 React Flow 实例的视口**，
「拉远一点再看」这条退路不通。而 `visible: true` 但 `inViewport: false` 的控件
是**渲染了但用户在屏幕上根本看不到** —— 只看 `visible` 会把「画布外」当成「够得着」。

> **教训：「跳过」极易在下一步被当成「没问题」。** 7 个跳过看起来像 7 个干净的
> 面，实际是 7 个**没测的面**。所以 `__skipped__` 做成必须人工复核的显式信号，
> 门禁里「走不到」直接判红，**不给假零的机会**。

修完后：**8 项全测通，0 跳过**。

## 三、一个反例：普查也会误报

`SubtitleErasePanel.tsx:472` 的「查看框选去字幕说明」没有 `onClick`，
按判据是标准死控件。浏览器实测：

```json
{"found": true, "visible": true, "opacity": "1", "visibility": "visible",
 "text": "使用说明• 在画面上拖拽鼠标,框选要擦除的区域• 支持框选多个区域…"}
```

**它是有行为的 hover 目标** —— 悬停它，旁边��使用说明浮层真的会弹出来。
「无 handler = 死控件」这个假设，在 hover 目标面前是错的。按普查结论去改它，
会把一个好控件改坏。

处理方式：

- 普查给它打 `hoverTarget` 标签**照常上报**（过滤掉会让人学不到东西，
  下次普查就看不见这一类了）；
- 分类器只认「后面紧邻元素里同时有 `group-hover:visib` 和 `group-focus-within:visib`」
  这个**结构证据**，判据经双向自检：修复前 9 个候选里**只有 1 个**被判中；
- 门禁**断言它没有被改成 inert**，且浮层仍能弹 —— 防止「批量修死控件」顺手误伤。

## 四、7 处处置：让 UI 停止撒谎，不发明

源站行为全部未采样（人机验证阻塞），撤销栈 / 资产新增 / 收藏 / 全景展开 /
BGM 试听 / 提示词翻译 / 标记横幅关闭都没有源站事实。**不发明**，按
batch 358/359/360/364/366 的既有处置：去掉悬停骗人反馈 + `cursor: default`
+ `title` 说明 + `data-inert` 自证惰性。**几何与文案一律不动**。

| 组件 | 控件 | 尺寸（未变） | 说明 |
|---|---|---|---|
| `ImageEditPanel.tsx` | 展开全景编辑器 | 28×28 | 全景形态未采样 |
| `SegmentReshootPanel.tsx` | 翻译片段重拍提示词 | 32×32 | 翻译动作未采样 |
| `StoryboardScriptEditor.tsx` | 新增{角色,场景,道具}资产 | 195×190 ×3 | 资产新增未采样 |
| `VideoGenerationPanel.tsx` | 收藏 | 24×24 ×4 | 账号态动作，不涉及付费 |
| `VideoGenerationPanel.tsx` | 关闭 | 10×24 | 标记选择横幅，**点不掉横幅** |
| `VideoProcessingToolbar.tsx` | 撤销视频处理 | 32×32 | 无可撤销历史栈 |
| `VideoProcessingToolbar.tsx` | 重做视频处理 | 32×32 | 同上 |
| `nodes/ShotBreakdownResultNode.tsx` | 播放 BGM | 13×13 | 13px 实心圆 + Play，紧挨时长 |

其中两处最值得单说：

- **标记横幅的「关闭」**：一个点不掉横幅的关闭按钮，是这批里最直接的骗人 ——
  用户以为能退出标记选择模式，点了横幅纹丝不动。
- **「播放 BGM」**：13px 的实心圆 + Play 图标 + 紧挨 `00:14` 时长，
  任何人都会认为点它会播音频。它也是**普查工具修好递归之后才第一次被看见**的。

对照组（**不许被误伤**）：同工具条上真能用的「下载视频封面」（`<a download>`）
和「展开视频」（`onClick` 设 `lastAction`）保持原样。

## 五、门禁

`scripts/verify-liblib-batch367.py` —— **130 项断言**。

1. **防假零**：7 处必须真的走到，走不到直接红（不是跳过）；
2. 每个控件 `data-inert="true"` + 非空 `title` + `cursor: default` + **无 hover 类**；
3. **几何未变**：class 尺寸 token 精确比对 + 运行时 rect 落在实测带宽内（±3px 只吸收
   渲染取整，尺寸 token 才是精确契约）；
4. **反向断言**：能用的 hover 控件没被改 inert，且浮层仍会弹；
5. **对照组未被误伤**：「展开视频」实点一次仍出现「已打开预览」；
6. 源码普查里**非 hoverTarget** 的候选数为 0；
7. 诊断零错误。

不落 `disabled` / `aria-disabled`：Playwright `is_disabled()` 会把它当禁用。

### 变异测试（三项，全部精确红在对应断言）

| 变异 | 结果 |
|---|---|
| 把 `hover:` 加回「撤销视频处理」 | `…撤销视频处理@1352,231:class-has-no-hover`，`className 含 hover: = True` |
| 拿掉「播放 BGM」的 `data-inert` | `…播放 BGM@341,307:inert`（`data-inert=None`）+ `source-census:no-plain-dead-buttons` 两层同时红 |
| 把能用的「查看框选去字幕说明」误标 inert | `hover-target:not-marked-inert` |

**第一次跑变异 2 时结果不作数**：退出码 1 来自 dev server 重编译期的
`ERR_CONNECTION_REFUSED`，不是断言红。改文件后必须轮询到 200 再跑，
否则会把基础设施故障误读成「断言有效」。

## 六、回归

- 定向：batch 359 / 360 / 364 / 365 / 366 / 531–534 / 367 —— **10/10 通过**
- `tsc --noEmit` 干净
- `verify-assertions.py`：563 个脚本 0 个空洞断言
- `verify-docs.py`：见提交记录
- frameos 页面**不引用**这 7 个组件

## 产物

- `scripts/probe_liblib_batch367_dead_buttons.py` —— 不依赖 `data-*` 的死按钮源码普查
- `scripts/probe_liblib_batch367_reachability.py` —— 8 项可达性实测（0 跳过）
- `scripts/verify-liblib-batch367.py` —— 130 项门禁
- `dead-button-census.json` / `reachability.json` / `verify.json`

## 遗留

- `CameraConfigDialog` / `CameraMovementDialog` 共 554 行、无人渲染且无 `data-*`，
  仍是真盲区，但属导演台跨线范围，只记录不动。
- 标记覆盖率仍在**低估**控件数（`ToolbarButton` 的多数调用点没有 `data-*`），
  这是可测性债务，不影响本批判据（它不依赖标记）。
