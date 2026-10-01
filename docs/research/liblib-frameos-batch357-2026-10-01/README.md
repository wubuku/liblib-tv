# Batch 357 — 第三类交互谎言普查：「点了有反应、但状态没变」

日期：2026-10-01
工具：`scripts/toast_lie_census.mjs`（AST）
门禁：`scripts/verify-frameos-batch357.py`（30 项）

## 这批在找什么

克隆侧的前两类交互谎言已经各修过一轮：

| 类别 | 形状 | 代表批次 |
|---|---|---|
| 静默丢弃输入 | 控件收下输入，不绑定 `onChange`，面板一字不变 | 350（裁剪宽高）、355（资产搜索框） |
| 假可点按钮 | 控件能点，但压根没有 handler | 344（删除分组）、356（素材库五按钮） |
| **本批** | **有 handler、点了确实出了东西（一条绿色 ✓「已xxx」toast），但底层状态一点没变** | 357 |

第三类最难发现，因为它**在每一层单看都是「正常的」**：源码里有个函数、点击有反馈、控制台零错误、截图上还挺好看的。只有在「点完去看结果」这一步才会露馅——而大多数时候用户不会去看。

## 普查结果

`node scripts/toast_lie_census.mjs` 扫 36 个 frameos 源文件，找带 toast 的 handler，再**逐条 toast** 判定（不是一个 handler 一票，见下文「粒度」）。6 条 TOAST-ONLY：

| 位置 | toast 文案 | 人工核实 |
|---|---|---|
| `page.tsx:517` 设置为资产图 | 已设置为资产图 (mock) | **谎报** |
| `FrameosGroupCanvas.tsx:121` 复制分组 | 已复制分组 (mock) | **谎报** |
| `FrameosGroupCanvas.tsx:126` 创建分组副本 | 已创建分组副本 (mock) | **谎报** |
| `FrameosGroupCanvas.tsx:250` 批量连线 | 批量连线 (mock) | **谎报** |
| `FrameosGroupToolbar.tsx:264` 存为模板 | 已存为模板 (mock) | **谎报** |
| `page.tsx:357` ⌘S | 已保存当前画布 | **非谎报，见下** |

### 逐条核实

**1. 设置为资产图 → 面板结构性为空。**
`FrameosProjectAssetsPanel` 的内容是写死的空态「暂无已生成的资产图」，没有任何数据源。点完菜单项去看面板，什么也没有。面板的搜索框在 Batch 355 已经被禁用了——那条注释里其实已经点破了根因：*「面板内容是硬编码空态……克隆侧没有资产数据」*。菜单项却还在弹绿色成功提示。同一件事的两头，一头已经诚实、一头还在撒谎。

**2/3. 复制分组 / 创建分组副本 → 没有 action，而且语义未定义。**
store 里根本没有分组的复制 action。真正卡住的是**语义**：分组是由存活成员算出来的盒子（Batch 341 不变式「分组盒 == 存活成员包围盒 + padding」），那么「复制分组」复制的是盒子还是成员？成员副本归不归入新组？两个组引用同一批成员合不合法？源站未采样，全是编造。
对照组：节点级「创建副本」是**真的**（`page.tsx` 调 `duplicateNode`，Batch 170）。同名不同命，反而更容易让人以为分组那档也能用。

**4. 批量连线 → 多步交互的起点。**
它不是一个能就地补上的 action，而是「选起点 → 选终点 → 建边」的开头。源站连线流程未采样。

**5. 存为模板 → 面板是硬编码常量表。**
这批最值得记的一条，因为它要**翻到面板的另一头**才能看穿：`FrameosTemplatePanel` 渲染的 `data-frameos-template-card` 来自常量 `TEMPLATE_CARDS`，store 里没有 `template` 字段。存进去的模板**永远不会**出现在面板里，面板也不会多出一张卡。
菜单项的反馈和它声称写入的那个目的地，是两套互不相干的东西。

**6. ⌘S → 不是谎报，保持原样。**
画布每次 `nodes/groups/edges` 变动都由 mount 订阅自动写 `localStorage`（`frameosStore.writePersistedCanvases`），所以「已保存当前画布」这句话在事实上为真——它只是把功劳记在一次并不存在的动作上。门禁把这一条写进白名单常量 `BENIGN_TOAST` 并注明：**若日后画布不再自动保存，这条应当改判为谎报并移出白名单**。
绑死「必须改掉它」就是绑缺陷副作用，不是绑真实性质（Batch 346/352 的同一条纪律）。

## ⚠️ 修法改过一次：被 batch170 打回，而它是对的

最初把 5 项统统改成 `disabled` + `title`，门禁 30 项全绿、3 项变异全红，看着很稳。
跑全量回归时 **batch170 红了**：

```
AssertionError: batch170 check failed: node:item:设置为资产图:disabled=false
```

按「我的改动撞上旧断言，第一动作是找一手源站证据」的纪律去查，**证据站在旧断言这边**：

```
docs/research/frameos/BEHAVIORS.md:33（2026-09-25 源站实测, Batch 226/228）
内容图片 复制⌘C / 复制图片 / 创建副本⌘D / 设置为资产图 / 删除⌫(红)
空图片 复制图片+重新生成均禁用
```

源站里内容图片态的「设置为资产图」是**启用**的，禁用的只有空图片态那两行。
我改 enabled，是在改源站事实。

更重要的是第二层：**缺陷本来就不在「这个菜单项能不能点」，而在它谎称成功。**
拿 `disabled` 当修复，是用「改源站事实」去盖住「文案不诚实」这个真问题。

于是 5 条统统改为：

> **保持启用**（源站事实，batch170 钉住）**+ toast 从 `success` 改成 `warning` 并说清「暂不可用」** + `title` 说明

一个谎报都没被藏起来——用户照样点得到、照样得到反馈，只是那条反馈终于说的是实话。
判据也随之从「只弹 toast」收紧为「**只弹 toast 且声称成功**」。

（另四项没有门禁钉住启用态，但也没有任何证据说它们该是禁用的；既然同一条修法在
有证据的那一项上被证伪，就没有理由只对它网开一面。）

「修复过头」也被纳进门禁：重新 `disabled` 会直接判红。

### 同一个回归里，另一条断言**该**改 —— 区别在于断的是不是源站事实

全量回归还打回了 `verify-frameos-batch251.py` 的一条：`port:click-mock-toast`，
断言点圆点后页面上出现文本 `批量连线 (mock)`。

它和 batch170 那条的区别正是本批最该记的东西：

| | batch170 | batch251 |
|---|---|---|
| 断的是什么 | 「设置为资产图」**启用** | 文案 `批量连线 (mock)` |
| 是不是源站事实 | **是**。`BEHAVIORS.md:33` 2026-09-25 实测，禁用的只有空图片态那两行 | **不是**。源站点击效果从未采样，所以才一直是 mock；断言名里就写着 mock |
| 该改谁 | 改我的代码 | 改断言 |

batch251 周围那几条断言（`port:24px-circle`、`port:style` 的 `48, 54, 66` /
`255, 255, 255`、`port:right-edge-centered`）**全部是采样到的源站几何**，一根都没动。
只把那条 mock 文案断言换成两条不钉死具体文案、只钉真实性质的断言：

- `port:click-gives-feedback` —— 点了要有反馈（圆点没变成死的元素）；
- `port:click-not-success-claim` —— 那条反馈不能是绿色成功。

同一次回归里 batch279 / batch300 失败是**环境噪音**（`WebSocket is already in
CLOSING or CLOSED state` / `ERR_CONNECTION_REFUSED`，dev server 当时掉线），
隔离跑即通过，与本批改动无关。是否要把这两类补进 `is_dev_server_noise`
（它目前只挡 `requestfailed:...net::ERR_ABORTED`）留作单独一批——门禁过滤器
必须双向验证，不能顺手放宽。

## 普查工具本身：三次假绿

这个工具在能给出可信数字之前，**先假绿了三次**。每一次都是「扫不全」伪装成「没问题」，记在这里是因为它们全都是同一个家族：

1. **`.tsx` 里 `(e) => {}` 是 `ParenthesizedExpression`** — 只解包了它的一半（`AsExpression`），没解包 `JsxExpression`。结果：**全部 JSX handler 一条都没扫到**，只有对象字面量属性（上下文菜单项）命中。
2. **紧凑箭头函数的 body 是表达式不是块** — `calledNames` 从 `node.forEachChild` 起步，恰好跳过了顶层那个 `CallExpression` 自己。`() => showToast(...)` 因此被判成「没调用任何东西」。而 `page.tsx` 的快捷键 handler 都是块体 `{ ...; showToast(...) }`，**侥幸命中**——让一个「扫不全」的工具看起来像是「没问题」。
3. **同文件两个同名 `const handler`** — `findLocalFnDecl` 按名字取全文件第一个声明，于是把 223 行的 keydown handler 解析成了 213 行的 `delete-edge` handler，⌘Z 撤销 / ⌘S 保存整段凭空消失。改成按作用域解析（从使用点向上找最近的函数体，取位置在前的同名声明）。

**外加一条构造性假阳性**：`const finish = () => showToast("已复制图片")` 外面才真正 `writeText(url)`。停在那个箭头函数上会把这种写法**必然**判成 TOAST-ONLY。加了「回调逃逸」处理——若最近的作用域是某个变量声明的初始化箭头，就合并上一层块里的调用。

以及一条**有意的假阳性**：`FrameosToast.tsx` 里监听 `frameos-toast` 自定义事件的那条不是用户手势，它**就是** toast 通道本身。显式排除并在输出里报出排除数（不静默丢弃）。

**粒度**：判定单位是**单条 toast**，不是整个 handler。`page.tsx` 的 keydown handler 里有 6 条 toast，⌘Z 调了 `undo()`、⌘S 什么都没调——按 handler 整体判定会把前者算成「有实质动作」从而**放过后者**。做法是对每条 showToast 上溯到最近的块（if 分支体 / 箭头函数体），只在这个窄范围内数其它调用。

## 门禁

`scripts/verify-frameos-batch357.py` 40 项：

- **静态普查进门禁**：只允许剩下 1 条「声称成功」的 toast，且必须是白名单里那条 `已保存当前画布`。以后任何人新写一条「什么都没做却说已成功」的处理，这里会红。
- **5 条谎报文案逐条钉死**：任一条文案重新出现即失败。
- **5 条「暂不可用」必须在场且都不是 `success` 变体**：这抓的是「话说对了、颜色还在撒谎」的半修。
- **防假绿**：`scanned >= 30`、`toastSites >= 8`。普查整体失效时不能报「零违规」。
- **运行时**：5 处点下去都必须弹 `warning`、文案说清是哪个功能暂不可用；`title` 齐全。
- **源站事实没被动过**：菜单项与圆点/按钮**仍然启用**（batch170 回归防护）。
- **不回归 Batch 344**：菜单里「删除」必须仍然启用，且点下去要真的 ungroup、不弹 mock toast。

### 探针自己踩的三个坑（都不是应用缺陷）

1. **菜单开着就右键 = 菜单被关掉**。`FrameosContextMenu` 有一层 `position:fixed; inset:0` 的遮罩，其 `onContextMenu` 只做 `closeContextMenu()`。实测：第 1 次右键 items=3 → 点完项菜单关闭 → 第 2 次右键 items=3 → 第 3 次右键直接 **items=0**。`open_group_menu()` 因此做成幂等（先 Esc 收场再右键）。
2. **别删 React 管的 DOM**。原本用 `querySelectorAll('[data-frameos-toast]').forEach(e => e.remove())` 给 toast「清场」，结果 fiber 树与 DOM 对不上，下一次重渲染把右键菜单一起拖没了。改成**点击前后取差集**，只读不写。
3. **点完菜单项菜单会关**，所以每点一项之前都要重新打开。

### 变异测试（双向）

| 变异 | 期望 | 结果 |
|---|---|---|
| 撤销修复：「存为模板」改回 success 绿 toast | 红 | 红（`census:exactly-one-success-claim`） |
| 半修：说了实话但仍用 `success` 变体（绿色 ✓） | 红 | 红（`census:exactly-one-success-claim`） |
| 改源站事实：「设置为资产图」又改回 `disabled` | 红 | 红（`census:five-unavailable-toasts`） |

## 与源站的关系

- `设置为资产图` 的源站**点击效果**自 Batch 226 起未采样（`SOURCE_ACCESS_BLOCKED_2026-10-01.md`，人机验证阻塞）；但它的**启用态是采样过的**（`BEHAVIORS.md:33`），这正是第一版修法被推翻的原因。
- `复制分组` / `创建副本` / `批量连线` / `存为模板` 四项的源站行为**从未采样**。`FrameosGroupCanvas.tsx:110` 的注释记着「点击效果未采样」，四年下来一直是 mock toast。
- 标签严格区分：`SOURCE_FACT` = 菜单项/按钮的**存在、文案、快捷键标注、几何、启用态**（已采样）；`INFERENCE` = 无；`CLONE_DECISION` = 保持启用 + 把成功提示改成「暂不可用」的实话 + `title` 说明。**未发明任何源站未采样的行为，也未改动任何已采样的形态。**
