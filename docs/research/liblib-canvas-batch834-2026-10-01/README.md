# batch 834 — clone 导演台：时间轴引导气泡**补齐 5 步**（源站 chunk 原文照抄 ＋ 定位算法照抄）

> 批次性质：**实施批次**（新增 `src/components/director/DirectorTimelineGuide.tsx` ＋ 改 `DirectorTimeline.tsx`／`DirectorDesk.tsx` ⟹ 已跑 `npm run build`）
> 日期：2026-10-22
> 门禁：`scripts/verify-liblib-batch834.py` ⟹ **主检查 14/14 ｜ 阴性对照 15/15**
> 真实注入自检：`probes/inject834.py` ⟹ 往 clone 组件注入一个错字 ⟹ **只有 S2 翻红** ⟹ 按字节复原（sha256 一致）
> 回归与归因：门禁 556／557／36／575／536／540／649／650／652／656／657 **全绿**；
> **748（4/7）与 749（7/9）已用 HEAD 换版归因 ⟹ 两条都是既有旧账、非本批引入**（详见第十节）
> 源站测试项目：**只读**（引导是纯前端浮层；本批**没改**项目数据）

---

## 一、一句话结论

batch 556 只做了引导的**第 1 步**，batch 831 记下「源站是 5 步、步骤 2–5 **未采样**」。

本批把源站的 5 步**一次采全**并**照抄实现**：

- 源站活体：开时间轴 ⟹ 逐点「下一步」直到「完成」⟹ **5 步的正文／宽度／位置／按钮全读到**；
- 源站 **chunk 原文**：组件 `cC` 的 5 步数据 ＋ **定位算法** ＋ **状态机**（`onNext`／auto-advance／收起键）；
- clone：新建 `DirectorTimelineGuide.tsx`，**数据、算法、类名逐字照抄** ⟹
  门禁 14 条全绿（含「渲染位置 == 按源站算法重算的位置」这条）。

★ ★ 顺带抓到一个**真缺陷**（不是判据问题）：源站用 Tailwind 任意值类 `z-[1900]` 给引导浮层定层叠，
而 **4317 的 Tailwind 扫描是冻结的**（batch 824）⟹ 新增任意值类在 dev 上**不生成** ⟹
z-index 落回 `auto` ⟹ 整块引导被时间轴的 `z-30` 盖住 ⟹ ★★ **「下一步」按钮点不动**。
⟹ 改成 inline style 后 5 步**都能真点**（探针从「必须用 JS 直点」变成「5/5 真点击成功」）。

---

## 二、源站的 5 步（活体 ＋ chunk 原文两路交叉核对）

★ 下表的「正文／宽度／按钮」来自**活体读数**，「target／偏移」来自**chunk 原文**，
两路在 `probes/mk833raw.py`（本批为 `mk834raw.py`）里**逐项交叉核对**，不一致就**拒绝出 raw**。

| 序 | target | 正文 | 步数 | 宽 | 偏移 X | 气泡高 | 按钮 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 序 1 | add-track | 请选择一个角色或者摄像机后，可新建轨道 | 1/5 | 260 | -80 | 112 | 跳过／下一步 |
| 序 2 | draw-trajectory | 点击创建路径，弹出选项面板 | 2/5 | 300 | -64 | 112 | 跳过／下一步 |
| 序 3 | motion-preset-ring | 点击圆环/直线/矩形创建路径，或用铅笔/钢笔工具绘制想要路径 | 3/5 | 360 | -48 | 136 | 跳过／下一步 |
| 序 4 | play | 路径绘制后点击播放，可预览动画 | 4/5 | 300 | 12 | 112 | 跳过／下一步 |
| 序 5 | export-to-canvas | 预览动画效果已确认，点击“导出视频到画布”，可以在画布内，进行后续编辑 | 5/5 | 360 | -268 | 112 | 跳过／**完成** |

★ 第 5 步那枚按钮是**另一个词**（「完成」不是「下一步」）——chunk 原文：
`4===e?l("canvas:directorTimelineGuideComplete"):l("canvas:directorTimelineGuideNext")`。

★ 每步的**宽度不同**（260／300／360／300／360）⟹ 气泡不是固定宽。

★★ **这趟源站采集**只能跑一次：走完第 5 步的「完成」之后，源站那个帐号的
引导就被标记成「看过」了（收起键 `libtv.director.timeline-guide.dismissed.v1`）
⟹ **再跑同一个探针会找不到引导** ⟹ 所以探针（`probes/coach834b.py`）
**一趟必须采全**（5 步的正文／宽度／位置／按钮 ＋ 末步按钮文案）。
⟹ ★ 也正因如此，**期望值必须已经入库**（本批的 raw ＋ 门禁），
而不是「留个探针以后再跑」。

---

## 三、★ 源站的定位算法（chunk 原文照抄）

```
target = 「export-to-canvas」用导出按钮的 ref
       ?? document.querySelector('[data-director-timeline-guide-target="<target>"]')
       ?? （target == "motion-preset-ring" 时退回 draw-trajectory）
       ?? document.querySelector('[data-director-timeline-guide-target="add-track"]')
icon   = target.querySelector('[data-director-timeline-guide-icon="true"]') ?? target
width  = Math.min(步宽, innerWidth - 24)
left   = clamp(icon 中心 x ＋ bubbleOffsetX, 12, innerWidth - width - 12)
top    = target.top - bubbleHeight - 2；不足 12 则改成 target.bottom + 14（再夹一次）
ring   = 以 icon 中心为心的 60×60 盒子（里一枚 24×24 的涟漪圆，1.4s 循环脉动）
```

★ 源站用 `data-director-timeline-guide-target` **标记**目标、用
`data-director-timeline-guide-icon="true"` **标记**图标锚点 ⟹ clone 用**同名属性**。

★ 兜底链的实测效果：clone 的默认场景**没有**运动路径浮层 ⟹ 第 3 步的
`motion-preset-ring` 不在 DOM ⟹ **退回 draw-trajectory** ⟹ 与源站算法**同构**（门禁 S8）。

---

## 四、★ 源站的状态机（chunk 原文）

| 序 | 触发 | 源站行为 |
| --- | --- | --- |
| 序 1 | 「下一步」 | 关掉运动绑定浮层 ⟹ 若有 trackId 则打开它 ⟹ 进第 2 步；否则**直接收起** |
| 序 2 | 「下一步」 | 若已画出轨迹 ⟹ 进第 3 步；否则**直接收起** |
| 序 3 | 「下一步」 | 若浮层已打开 ⟹ 套用「圆环」预设 ⟹ 关浮层 ⟹ 进第 4 步；否则**直接收起** |
| 序 4 | 「下一步」 | 若未在播放 ⟹ **开始播放** ⟹ 进第 5 步 |
| 序 5 | 「完成」 | 点「导出视频到画布」⟹ 收起 |
| 序 6 | 自动推进 | 浮层打开 ⟹ 0→1；浮层打开 ⟹ 1→2；浮层关闭 ⟹ 2→3；**开始播放** ⟹ 3→4 |
| 序 7 | 收起标记 | 到第 3 步且浮层既没开也没在开 ⟹ **120ms 后**写 localStorage 标记并收起 |

★ 收起标记的键：源站 `libtv.director.timeline-guide.dismissed.v1`；
**clone 沿用自己的 `director-timeline-coach-dismissed`** ⟹ ★ 因为门禁 36／575
**直接断言那个键名** ⟹ 改键名会让那两条门禁失效。

★ 启动条件（源站）：`step 为 null` ＋ `localStorage 标记 != "1"` ＋ `有目标上下文` ＋ `另一个守卫为假`。
clone 沿用自己既有的语义（没被标记看过就显示）⟹ 因为门禁 36／575 依赖这个气泡在开台后**就在**。

---

## 五、★★ 第一版探针为什么「找不到引导」（本批最值得记的一处）

第一版探针 `probes/coach834.py` 的做法是「开台 ⟹ 点『帮助 → 使用教程』⟹ 找 `n/5` 样式的元素」
⟹ **全页零命中** ⟹ 一度以为源站**没有**这个引导。

★ 真因：**源站的引导锚在时间轴上，而源站时间轴默认是「收起」的** ⟹ 引导**根本没机会出现**。

★ 破局的那一步不是再试一次，而是**换一种读法**：`probes/diag834b.py` 拍「可见元素签名表」
（tag ＋ 类名 ＋ 盒）的**集合差** ⟹ 点「动画时间轴」那一刻，页面**多出两枚**
`h-7 rounded-lg bg-transparent px-3` / `bg-white/10` 的按钮 ⟹ ⟹ **引导就在那儿**。

⟹ ★ 与已存记忆同族：「**选择器在源站不存在 ⇒ 那个动作根本没发生**」——
这里的变体是「**目标不在 DOM 里 ⇒ 那个东西还没被触发**」⟹
先问「**触发条件满足了吗**」，再问「读数器写对了吗」。

---

## 六、★ 本批抓到的真缺陷：`z-[1900]` 在冻结的 Tailwind 扫描下**不生成**

- 源站的引导浮层是 `fixed inset-0 z-[1900]`（Tailwind **任意值类**）；
- ★ 4317 的 Tailwind 扫描是**冻结**的（batch 824 实测）⟹ **新增**任意值类在 dev 上**不生成**；
- ⟹ 覆盖层的 z-index 落回 `auto` ⟹ 整块引导被时间轴 section 的 `z-30` 盖住；
- ⟹ ★★ 探针点「下一步」时命中测试被时间轴的横向滚动容器截走 ⟹ **按钮点不动**。

⟹ 修法：覆盖层／气泡／光环的 z-index **全部走 inline style**（`zIndex: 1900 / 1 / 2`），
类名里不再出现 `z-[n]`。⟹ 门禁 S12 把这条**钉住**（且只在 `className` 属性里找 `z-[`，
⟹ 注释里提到「z-[1900]」不算数——第一版判据全文搜，命中了**自己写的注释** ⟹ 恒红）。

★ 同一坑在别处也踩过（batch 832 的列宽、batch 834 的 1px 图标锚点）⟹
**clone 里凡是新的任意值类，一律走 inline style。**

---

## 七、clone 的实施

| 序 | 文件 | 改动 |
| --- | --- | --- |
| 序 1 | `src/components/director/DirectorTimelineGuide.tsx`（**新增**） | 5 步数据 ＋ 定位算法 ＋ 覆盖层／气泡／光环（类名照抄源站） |
| 序 2 | `src/components/director/DirectorTimeline.tsx` | 用新组件替换旧气泡；加**步序状态机**（下一步／跳过／完成／自动推进）；给 4 枚常驻目标挂 `data-director-timeline-guide-target` |
| 序 3 | `src/components/director/DirectorDesk.tsx` | 给「导出视频到画布」按钮挂 target 标记 ＋ 1px 图标锚点 |
| 序 4 | `scripts/verify-liblib-batch556.py` | **只更正文件头的背景说明**（合同正文未改）⟹ 见 §九 |

★ 与源站**有意**的两处偏离（CLONE_DECISION）：

1. 气泡本体是 `pointer-events-none`、只有两枚按钮是 `pointer-events-auto`
   （源站气泡本体是 `pointer-events-auto`）——沿用 batch 556 的既定做法；
2. 涟漪圆的描边与气泡的字体走 **inline style**（源站用 Tailwind 任意值类）——因为扫描冻结。

★ **旧属性名保留为别名**（`data-director-timeline-coachmark`／
`data-director-coachmark-skip`／`data-director-coachmark-next`）⟹ 门禁 556／557 仍能定位。

---

## 八、门禁（`scripts/verify-liblib-batch834.py`）

**主检查 14 条** ＋ **阴性对照 15 条**（每条**只**翻它自己那一条）。

★ 期望值全部从 raw 读（`raw/source-834-timeline-guide.json` ＝ 源站活体 ＋ chunk 原文两路交叉核对）⟹ 不是手打。

★ 最有分量的一条是 **S6**：判「**渲染出来的气泡位置** == **按源站 chunk 原文的算法重算出来的位置**」
（5 步全对）⟹ 判的是「**算法被照抄了**」，而不是「某个绝对坐标碰巧对」。
⟹ 也正因为如此，**不**直接比绝对坐标：源站采集时场景里有相机轨道（第 2/3 步分别指向
「绘制轨迹」与浮层里的「圆环」），clone 的默认场景**没有**轨道 ⟹ 源站的算法会**退回**
add-track ⟹ 绝对坐标当然不同 ⟹ 那是**场景状态不同**，不是 clone 错。

★ 门禁自己翻的车两处：① S12 第一版全文搜 `z-[1900]` ⟹ 命中**自己写的注释** ⟹ 恒红
（改成只在 `className` 属性里找）；② N9 第一版只砍第 1 步的可见 target ⟹ 而 S10 读的是
**各步的并集** ⟹ 判据照样绿（改成每一步都砍）。

★ **真实注入自检**（`probes/inject834.py`）：往组件注入一个错字 ⟹ **只有 S2 翻红** ⟹ 按字节复原。

---

## 九、更正旧合同（只改说明，不改断言）

`scripts/verify-liblib-batch556.py` 的文件头原话是「Steps 2-5 are unsampled, so both actions
dismiss the coachmark in the clone (CLONE_DECISION)」⟹ ★ 本批已过时（源站的 5 步已采样并实现）。

⟹ **只更正文件头的背景说明**，**断言一个字未改**（跳过 → 收起、重载后仍收起、第 1 步文案与 1/5
全部仍成立）⟹ 门禁保持绿灯。
⟹ ★ **旧批次的 README 不重写**（前缀/后缀式文档不可重写）⟹ 更正写在本行与本文件。

---

## 十、回归与归因（本批代码上实跑）

### 10.1 绿的（在本批代码上实跑）

| 序 | 门禁 | 结果 | 说明 |
| --- | --- | --- | --- |
| 序 1 | `verify-liblib-batch556.py` | 8/8 ✔ | 本批只改了它的**文件头说明**、断言未动 |
| 序 2 | `verify-liblib-batch557.py` | 5/5 ✔ | 旧属性名保留为别名 ⟹ 仍能定位 |
| 序 3 | `verify-liblib-batch36.py` | ✔ | 引导收起键名 `director-timeline-coach-dismissed` 仍被直接断言 |
| 序 4 | `verify-liblib-batch575.py` | 4/4 ✔ | 同上 |
| 序 5 | `verify-liblib-batch536.py` | 27/27 ✔ | |
| 序 6 | `verify-liblib-batch540.py` | 10/10 ✔ | |
| 序 7 | `verify-liblib-batch649/650/652/656/657.py` | 全 ✔ | |

### 10.2 红的，**逐条归因**（★ 关键：**不能只看「红」就当本批的锅**）

归因方法（沿用 batch 832 的做法，**不用 stash、不用 worktree**）：逐个 sha256 备份本批改过的
三个文件 → 换回 HEAD 的版本（新文件移出源码树）→ 在旧版本上跑同一条门禁 → 原样搬回并复核 sha256。

| 序 | 门禁 | 本批结果 | HEAD（batch 833）上的同一门禁 | 归因 |
| --- | --- | --- | --- | --- |
| 序 1 | `verify-liblib-batch748.py` | **4/7**（C1／C3／C4 红） | **同样 4/7**、**同样 C1／C3／C4 三条红** | ★ **既有旧账**，非本批引入 |
| 序 2 | `verify-liblib-batch749.py` | 7/9 | **同样 7/9**，C9 的数字同为 **447** | ★ **既有旧账**，非本批引入 |
| 序 3 | `verify-liblib-batch750/751.py` | 探针 **exit=2** | 同 | ★ **环境性**：旧批次探针脚本（`/tmp/dbg750e.py` 等）已不在本机 |
| 序 4 | `verify-liblib-batch758/759.py` | 读不到产物 | 同 | ★ **环境性**：`/tmp/vb758*.json` 不在本机 |

★ **748 这条最值得记**：它的 C1／C3 把导演台 `data-*` 的**静态并集锁死成 batch 748 时点的快照**
（去重字面量并集 446 / 补 `dataset.` 后有效并集 447 / 按文件求和 460），而 C4 锁死了
「7 枚 rail 里恰好 2 枚点开 0 新增」。

⟹ **本批新增了引导组件与 `data-director-timeline-guide-*` 属性名 ⟹ 静态并集必然被推高**
（本批实测 468／469／488）⟹ ★ 所以「数字变了」这件事**本身不能**证明是本批的锅。
⟹ **必须拿 HEAD 版本跑同一条门禁来比**：HEAD 上是 460／461／476（C3 同样红、C1 同样红）、
C4 的 zeroGain 同样只有 **1 枚（scene）**、同样红 ⟹ ★ **旧账早于本批**。

⟹ ★ 但要说清一件容易被忽略的事：**旧账归旧账，本批确实把数字推得更远了**。
748 的期望值已经**连着三个批次**（831 的 help 面板、832 的机位预设面板、本批的引导）
都不再对得上静态快照 ⟹ 它需要**单独一批**按新事实更新（已列入遗留），本批**不动**它
（那是别人的批次目录，且更新它等于把旧门禁改成一个「永远绿」的橡皮章）。

★ **归因的可信度自证**：`probes/attrib834b.py` 在复原时**逐个复核 sha256**，
不一致就 `SystemExit` ⟹ 不允许带着半恢复的源码树继续；本批源码树已复核一致。

---

## 十一、不声称（明确的空白）

1. ★ 源站 `onNext` 的**条件式收起**（例如第 2 步「没画出轨迹就直接收起」）在 clone 里**没有照抄** ⟹ clone 的「下一步」是**无条件推进** ⟹ 这是**有意**的简化（原型要能一路走完 5 步），**不声称**与源站完全同构。
2. ★ 源站在第 3 步会**真的套用「圆环」预设**、在第 5 步会**真的点导出**；clone 的「完成」只是收起引导 ⟹ 不声称动作链一致。
3. ★ 源站的「写收起标记」发生在**第 3 步的 120ms 定时器**里；clone 是在**收起时**写 ⟹ 语义相近、时机不同。
4. ★ 源站的引导在**没有目标上下文**时不启动（chunk 里的 `!eF` 守卫）；clone 只要没被标记看过就启动 ⟹ 不声称一致。
5. ★ 源站那个 `nY.C()` 守卫**没读**（它在 chunk 的另一个模块里）⟹ 不知道它拦的是什么。
6. ★ 引导的**文案 i18n 键**（`canvas:directorTimelineGuideStep1…5`）在 clone 里**换成了中文硬编码**（沿用 clone 既有做法：源站活体读数是中文）⟹ 不声称 i18n 机制一致。
7. ★ 窄屏（<899px）下的引导形态**未测**。

---

## 十一、产物清单

| 序 | 路径 | 说明 |
| --- | --- | --- |
| 序 1 | `scripts/verify-liblib-batch834.py` | 门禁（14 判据 ＋ 15 阴性） |
| 序 2 | `raw/source-834-timeline-guide.json` | ★ 源站 5 步（活体 ＋ chunk 原文，两路交叉核对） |
| 序 3 | `raw/clone-834-timeline-guide.json` | clone 5 步的活体读数 ＋ 按源站算法的重算位置 |
| 序 4 | `probes/coach834b.py` | 源站 5 步逐点采集（**一趟采全**——走完就再也看不到） |
| 序 5 | `probes/diag834.py` / `probes/diag834b.py` | 为什么第一版找不到引导（时间轴默认收起 ＋ 元素签名差分） |
| 序 6 | `probes/extract834.py` / `extract834b.py` / `extract834c.py` / `extract834d.py` | 从 chunk 抽出组件 `cC`、状态机、收起键、启动条件 |
| 序 7 | `probes/mk834raw.py` | 活体 ＋ 原文 → raw（**两路交叉校验**，不一致就拒绝出 raw） |
| 序 8 | `probes/guideclone834.py` | clone 侧 5 步读数 ＋ 按源站算法重算位置 |
| 序 9 | `probes/hit834.py` | 命中测试诊断（抓出 `z-[1900]` 不生成的真缺陷） |
| 序 10 | `probes/inject834.py` | 门禁的**真实注入自检** |
| 序 11 | `probes/attrib834.py` / `probes/attrib834b.py` | 749／750／751 与 **748** 的**归因**（HEAD 换版 ＋ sha256 复核复原） |
| 序 12 | `probes/ledger834.py` | 追加台账那一行（**自己**校验 4 竖线／0 FFFD／无占位符，不合格就不写） |
