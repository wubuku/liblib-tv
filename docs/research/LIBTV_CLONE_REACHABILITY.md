# LibTV 复刻版 —— 页面可达性 ＆ 交互测试说明

> ★ 这份文档回答两个问题：
> ★ **①「怎么到达」** —— 每个已完成的复刻页面，**从 clone 的根目录**怎么点进去；
> ★ **②「怎么交互测试」** —— 进去之后，**怎么自己验它是不是活的**。
>
> ★ 口径（**重要**）：
> - 「根目录」＝ clone 站的**根路由**，**不带任何参数**：`http://localhost:4317/`。
>   ⟹ ⟹ **不允许**靠手敲 URL 到达任何一个页面 ⟹ ⟹ 必须**点**进去。
> - 每条路径都**实测过**（真的点一遍再读 DOM），证据在
>   `docs/research/liblib-canvas-batch854-2026-10-01/raw/reachability-854.json`
>   （截图同目录 `images/854reach_*.png`）。
> - ★ **「这个入口没有 X」这类断言必须真的点一下才算数** ⟹ ⟹ 本文的每条路径
>   都是**点完再读**，不靠「源码里有这个按钮」推断。

---

## 0. 先把 clone 跑起来

```bash
cd <仓库根>
npm install          # 首次
npm run dev          # ⟹ 监听 4317
# 浏览器打开 http://localhost:4317/
```

★ `package.json` 的 `dev` 脚本就是 `next dev --port 4317`；若端口被占，
用 `npm run dev:restart`（`scripts/restart-dev.sh`）。

★ **不要用 `npm run build && npm start`**：本 clone 的若干门禁依赖 **dev 态**
（时间轴默认态、store 探针 `window.__libtv_store`／`window.__director_store`）。

★ 4317 是**多人共用**的 ⟹ ⟹ **别并发跑多个浏览器脚本**。

---

## 1. 根目录长什么样

`http://localhost:4317/` 打开就是 **LibTV 画布**（一个可拖拽／可连线的节点工作区）：

| 区域 | 能点什么 |
| --- | --- |
| 画布中央 | **节点**：导演台（`script-execution`）、图片、视频、音频、文本、分镜组等 |
| 左侧竖排图标条 | **角色造型室**、生成历史、素材库、添加节点、快捷键、教程… |
| 底部工具条 | **资产管理**、小地图、连线、吸附、缩放 |
| 顶部 | 画布切换、Agent、会员等（clone 的装饰性外壳） |

★ 实测：根页共 **10 个节点**（`raw/reachability-854.json` 的 `根页.画布节点数`）。

---

## 2. 三条主干路径（每条都实测过）

### 2.1 路径 A —— **导演台**（本仓复刻的最高优先级之一）

**怎么到达**

1. 打开 `http://localhost:4317/`（根目录，无参数）
2. 在画布上找到标题为「**第一集：咖啡馆对峙**」的那张 **导演台卡片**
   （节点类名 `.react-flow__node-script-execution`）
3. **鼠标悬停**在它上面 ⟹ 卡片里出现「**打开导演台 →**」按钮
4. 点它 ⟹ **导演台**盖在画布上

★ 为什么必须**先悬停**：按钮默认透明，悬停才显形（与源站一致）。

**怎么交互测试**（导演台里有什么、点什么）

| 想测什么 | 怎么点 | 看什么 |
| --- | --- | --- |
| 场景树 | 左侧树 `[data-director-tree]` | 角色／场景物体／机位三类分区，行可点、可多选 |
| 视图类快捷键 | `T` / `Y` / `H` / 裸 `WASDQE` | 相机视角切换、取景框显示隐藏 |
| 变换类快捷键 | `V` / `R` / `F` / `X` | 移动／旋转／缩放模式、网格吸附开关 |
| 打组／解组 | `⌘G` / `⌘⇧D` | 树上多出一个组行，成员缩进在组标题**右侧 16px** |
| 组的成员语义 | 点「机位1」⟹ **⌘+点**「角色A」⟹ 「打组」 | 组里**同时有**机位和角色；成员**默认展开** |
| ★ 组的**唯一移动路径** | 选中组 ⟹ 时间轴上建**组轨道** ⟹ 加关键帧 ⟹ 拖时间 | 成员**随轨道一起走**（★ 源站**没有**组 gizmo ⟹ ⟹ 轨道是组唯一的移动路径） |
| ★ 组的**检查器** | 选中组 ⟹ 看右侧检查器 | ★ **只有「名称」一个字段**（源站逐字：组对象**没有** transform） |
| ★ **「添加角色」面板** | 左侧 rail「**添加角色**」（第 2 枚） | 左侧资源栏**切成一个面板**（源站逐字：**模式互斥**）⟹ ⟹ ★ **场景树消失**（切到它时场景树**不渲染**）；面板 **232** 宽、标题条 48px、**11 行**（本地上传／8 个体型／群众 (3x3)／几何模型） |
| ★ **「几何模型」就地展开** | 面板里点「**几何模型**」 | 8 项**就地展开在面板里**（源站逐字 `ml-3 border-l pl-1`）⟹ ⟹ **不是**浮层；实测 @(68,452) 204×256、每项 199×32 |
| ★ **面板 ↔ 场景树互斥** | 点 rail 的「**场景**」 | 面板关闭、**场景树回来**（源站逐字 `"scene"===z?n:null`） |
| ★ **群众阵列**（crowd） | 左侧 rail「**添加角色**」⟹ 「**群众 (3x3)**」 | 弹出「添加群众阵列」对话框（**220×204 @(280,388)**，落在按钮**右侧**：按钮 right+8、顶＝按钮顶）；行/列 **1–10**、间距 **0.1–10**、初值 3／3／**1.2**；★ 间距填 `1.55` 会读回 **`1.6`**；★ 填 `1.55` 那格是**跨两列**的（源站逐字 `col-span-2`） |
| ★ crowd 对话框的**两个源站行为** | 再点一次「群众 (3x3)」／点对话框**外面** | 对话框**关闭**（源站逐字：`if("crowd"===L)O(null)` ＋ 外部 mousedown 关闭） |
| 多选 | **⇧／⌘／Ctrl** + 点击 | 选中多个对象（任意类别） |
| 快捷键面板 | 左下角「快捷键」 | 12 条快捷键清单 |
| ★ **画幅比例 → 机位取景框** | 左侧 rail「**选择画幅比例**」（第 6 枚）⟹ 点「**16:9**」 | 视口里出现**机位取景框**（★ 源站逐字：选比例改的是**取景框**，**不改画布**）⟹ ⟹ 取景框读数 `[data-director-aspect-frame]`（带 `data-director-aspect-ratio="16:9"` 标记）；★ 点「**自适应**」⟹ ⟹ **取景框不在场** |
| ★ **构图参考线（三分线）** | 点**取景框右上角**那枚 32×32 的按钮（`[data-director-frame-thirds-toggle]`，`title="构图参考线"`） | 框内出现**4 条**分线（白 **50%**，`[data-director-thirds]`）⟹ ⟹ 再点消失；★ 按钮关闭态是半透明白、**开启时变青**（源站逐字 `text-btn-primary`）⟹ ⟹ ★ 该按钮**只在取景框在场时存在**（源站逐字 `null!==tr` 才给回调） |
| ★ **取景框外的遮罩** | 点 rail「**选择画幅比例**」⟹ 「**16:9**」（框出现后**自动生效**） | 框外**压暗 20% ＋ 背景被化开**（`blur(12px)`，源站逐字 `bg-black/20 backdrop-blur-md`），**框内那一块保持清晰**（被 CSS mask **挖空**，`mask-composite: exclude`）⟹ ⟹ 遮罩层读数 `[data-director-aspect-mask]`、容器 `[data-director-aspect-mask-container]`；★ **自己验「框内被挖空」**：DevTools 里把遮罩层的 `background-color` 改成 `rgba(255,0,0,0.85)` ⟹ ⟹ **框外变红、框内不变**；★ 点「**自适应**」⟹ ⟹ 框与遮罩**一起消失** |
| ★ **本地事件记录**（源站那条埋点的**本地等价**） | 点 rail「**选择画幅比例**」⟹ 选「**16:9**」；**或者**点**取景框右上角**那枚「构图参考线」开关 | DevTools 控制台读 `window.__director_store.getState().telemetryLog` ⟹ ⟹ 追加一条 `{"e":"libtv.canvas.director.camera.update","var":{"camera_uuid":"director-camera-main","setting_name":"aspect_ratio","setting_value":"16:9","operation_source":"right_panel"}}`；★ 切参考线记的是 `setting_name:"reference_line"`、`setting_value` 为**数字 1／0**（记的是**切换后**的值）；★ 选「**自适应**」记 `setting_value: null`；★ 机位 ＝ **选中机位优先**，否则**第一个机位**（源站逐字）；★ ★ **不触网**（原型不碰真实接口）⟹ ⟹ 改了比例／切了参考线**不会发出任何请求**；★ 日志上限 50 条；★ **注意 id 拼写**：clone 的机位 id 是 `director-camera-main`，而**源站**那条埋点里是 `director-main-camera`（★ 两者**差一个词序**，别把源站的值当成 clone 的） |
| ★ **构图参考线开关**（可点性） | 点**取景框右上角**那枚 32×32 的按钮（`[data-director-frame-thirds-toggle]`） | ★ **batch 864 修掉了 batch 863 引入的遮挡**：那时候遮罩容器（`z-10`）**创建了层叠上下文** ⟹ ⟹ 开关的 `z-20` 被困在里面 ⟹ ⟹ **点不到**（命中的是视口坐标控件）；现在开关**恢复可点**（分线 0 → 4 条）⟹ ⟹ 自己验：DevTools 里 `document.elementFromPoint` 取按钮中心 ⟹ ⟹ 返回的**最顶层元素就是那枚开关** |
| ★ ★ **取景框的四者平级结构**（★ **batch 865**：D25 结案） | 点 rail「**选择画幅比例**」⟹ 「**16:9**」⟹ ⟹ 点**取景框右上角**那枚「构图参考线」开关 | ★ 源站逐字：取景框那四层是「**遮罩层／空框／三分线层／开关**」**四者平级**（都是遮罩容器的**直接子元素**），而**框里没有任何 children** ⟹ ⟹ clone 现在**同构**了 ⟹ ⟹ ★ **自己验**：DevTools 控制台跑 `(()=>{const c=document.querySelector('[data-director-aspect-mask-container]');const m=e=>e.hasAttribute('data-director-aspect-mask')?'遮罩层':e.hasAttribute('data-director-aspect-frame')?'空框':e.hasAttribute('data-director-thirds')?'三分线层':e.hasAttribute('data-director-frame-thirds-toggle')?'开关':'其他';return [...c.children].map(m)})()` ⟹ ⟹ 期望打印 **`["遮罩层","空框","三分线层","开关"]`**；★ 再跑 `document.querySelector('[data-director-aspect-frame]').childElementCount` ⟹ ⟹ 期望 **`0`**（空框）；★ ★ **视觉上没有任何变化**（846,630 像素逐个比对 ⟹ ⟹ **0 个不同**）⟹ ⟹ 这是**纯结构对齐**，不是视觉改进 |
| ★ ★ **视口坐标控件不再被挡**（★ **batch 865** 整改 batch 864 的后遗症） | 打开导演台 ⟹ ⟹ 看**视口左上角**那枚六轴坐标控件（`[data-director-viewport-gizmo]`） | ★ **batch 864 的后遗症**：它把坐标控件降到 `z-10` 之后 ⟹ ⟹ 框上那枚开关（`z-20`）**反过来盖住**坐标控件的「X 反向」「Z 正向」两枚按钮 ⟹ ⟹ **点不到**；★ **batch 865 把坐标控件挪到视口左侧**（`absolute left-3`）⟹ ⟹ 六枚按钮**全部命中自己** ⟹ ⟹ 自己验：`[...document.querySelectorAll('[data-director-viewport-gizmo-button]')].map(b=>{const r=b.getBoundingClientRect();const t=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));return [b.getAttribute('aria-label'),t?.closest('[data-director-viewport-gizmo-button]')===b]})` ⟹ ⟹ 期望 **6 枚全是 `true`**；★ ★ **可挪的依据**：源站 chunk 里 15 处「Gizmo」**全是 three.js `TransformControls`** ⟹ ⟹ **源站的 3D 视口根本没有这枚六轴控件** ⟹ ⟹ 它是 **clone 自有扩展** ⟹ ⟹ 位置没有源站约束 |

★ **移动端（390×844）**：rail 是 `hidden` ⟹ ⟹ 「添加角色」这条路**走不通** ⟹ ⟹
crowd 入口改在**视口底部工具条**的「**添加群众阵列**」按钮
（`[data-director-crowd-mobile-trigger]`）⟹ ⟹ 它开的是**同一个**对话框
（量程／默认值／落点规则与桌面**完全同源**）⟹ ⟹ 桌面端**这枚按钮不出现**
⟹ ⟹ 所以**每个断点上可见的 crowd 入口都只有 1 枚**。
★ 为什么这么分：★ **源站没有移动端布局**（实测 390px 下源站渲染的仍是桌面画布、
导演台根本没开，见 `raw/source-857-mobile.json`）⟹ ⟹ 移动端这枚是 **clone 自己的扩展**，
如实登记，不冒充源站行为。

★ 导演台打开后（**URL 不变**，是盖在画布上的一层），实测有 **7 个 rail 项**、
**5 个对象树行**、**28 个可交互元素**
（`raw/reachability-854.json` 的 `路径A_导演台` ＋
`raw/clone-854-reachability.json` 的 `③导演台可交互元素`）。

### 2.2 路径 B —— **角色大编辑器**（角色造型室 → 角色卡 → 编辑角色）

**怎么到达**

1. 打开根目录
2. 点左侧竖排图标条里的「**角色造型室**」（`aria-label="角色造型室"`）
   ⟹ 左侧滑出**角色库**面板
3. 切到「**官方角色库**」页签 ⟹ 出现角色卡片列表
4. 点**任意一张角色卡** ⟹ 卡片下方出现操作区
5. 点「**编辑角色**」⟹ **角色大编辑器**盖上来

**怎么交互测试**

| 想测什么 | 怎么点 | 看什么 |
| --- | --- | --- |
| 编辑器整体 | — | 中列是**预览区**（可缩放、可换取景：全身／半身／特写） |
| 脸部精修（限免） | 左列第 1 段 | 脸部精修参数 |
| 脸部 & 身体特征 | 左列第 2 段 | 脸型／发型／发色／妆容等参数 |
| 身材塑形（限免） | 左列第 3 段 | 身材参数 |
| 服装造型 | 左列第 4 段 | 「服装」子段（**引用**源站 CDN 图，不是复刻）、AI 生成入口 |
| 音色音调 | 左列第 5 段 | 音色库卡片、播放按钮、我的音色／音色库两个页签 |
| 底部生成 | 「生成」 | 数量／分辨率等设置 |

★ 实测：左列共 **5 段**（`raw/reachability-854.json` 的 `路径B_角色大编辑器.左列分段`），
官方角色库共 **17 张**角色卡，「编辑角色」CTA **1 个**。

★ **如实标注**：音色卡与服装卡的**图**是**引用**源站 CDN；**图标字形**用的是
lucide 占位（源站是 iconify）——详见 batch 847／849 的 README。

### 2.3 路径 C —— **资产管理**

**怎么到达**

1. 打开根目录
2. 点底部工具条里的「**资产管理**」（`aria-label="资产管理"`）
   ⟹ 弹出资产管理面板

**怎么交互测试**：面板内分「角色」「场景物体」「机位」等分区；右上角 `✕`
（`aria-label="关闭资产管理"`）关闭面板。

---

## 3. 「我自己怎么测」—— 三档由浅入深

### 3.1 手动点（最快，验证「像不像活的」）

按 §2 的路径走一遍，每一步都该看到界面**真的变化**（不是静态图）。

### 3.2 跑现成的门禁（验证「没被改坏」）

```bash
# 单批门禁（每批一份，判据写在各批 README 里）
python3 scripts/verify-liblib-batch854.py
# → 11/11 通过

# 回归：一次跑 76 条既有门禁
python3 docs/research/liblib-canvas-batch854-2026-10-01/probes/regress854.py
# → 期望：只有「已知旧账」那几条红
```

★ 门禁都是 **headless Chromium** 跑的 ⟹ ⟹ **不要和另一个浏览器脚本并发**
（4317 多人共用）。

### 3.3 自己写探针（验证「某个具体交互」）

现成的探针在每批目录的 `probes/` 下，可以照抄。最小的骨架：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)          # ★ 无头
    ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                         locale="zh-CN")
    pg = ctx.new_page()
    pg.goto("http://localhost:4317/", wait_until="domcontentloaded")
    pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    # …你的点击与读数…
    br.close()
```

★ 两个探针纪律：
1. **先 `scrollIntoView` 再点**（不然点的是可视区外的元素）；
2. ★ **4317 探针要先移除 `nextjs-portal`**（那是 Next.js 的 dev 浮层，会挡住读数）：
   ```python
   pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
   ```

★ **store 副读数**（方便断言）：页面里暴露了
`window.__libtv_store`（画布）与 `window.__director_store`（导演台）。

---

## 4. 不在「从根可达」范围内的东西（**如实登记**）

| 东西 | 为什么不在范围内 |
| --- | --- |
| `/frameos`、`/frameos/canvas/[id]` | **FrameOS 是另一个 App 的原型**，不属于 LibTV 复刻范围（目标里明确排除） |
| `/jimeng`、`/jimeng/canvas/[id]` | 即梦画布，**属于他人的并发开发区**，不是本仓 LibTV 复刻成果 |
| `/project` | 独立路由，**尚未**从根画布接入入口 ⟹ 不算「已完成的复刻页面」 |

★ 登记口径：**路由存在 ≠ 复刻完成**。一份「完成」至少要满足
**① 可交互**（不是静态图）＋ **② 从根点得到** ＋ **③ 文档写清怎么到达与怎么测**。

---

## 5. 证据索引

| 文件 | 内容 |
| --- | --- |
| `docs/research/liblib-canvas-batch854-2026-10-01/raw/reachability-854.json` | 三条路径的**实测**读数（根页清单／每条路径的步骤与落点读数） |
| `docs/research/liblib-canvas-batch854-2026-10-01/raw/clone-854-reachability.json` | 根地址无参可达 ＋ 导演台 21 个可交互元素清单 |
| `docs/research/liblib-canvas-batch854-2026-10-01/images/854reach_*.png` | 根页／导演台／角色大编辑器／资产管理 的截图 |
| `docs/research/liblib-canvas-batch854-2026-10-01/README.md` | 本批（组模型成员语义）的完整取证与验收 |
| `docs/research/liblib-canvas-batch856-2026-10-01/README.md` | batch 856（组的检查器与画布 gizmo）的完整取证与验收（★ 它的「用户可达」在 857 里**补上**，见 857 README §8.4） |
| `docs/research/liblib-canvas-batch857-2026-10-01/raw/source-857-contract.json` | 源站 crowd **17 条逐字**片段 ＋ 两项自检（任意值类名／跨片段防呆） |
| `docs/research/liblib-canvas-batch857-2026-10-01/raw/source-857-crowd.json` | 源站实测：对话框 **220×204 @(280,388)**、量程、间距 1.55→**1.6**、★ **唯一入口**的自指判据 |
| `docs/research/liblib-canvas-batch857-2026-10-01/raw/source-857-mobile.json` | ★ 源站在 **390×844** 下的实测 ⟹ ⟹ **源站没有移动端布局** |
| `docs/research/liblib-canvas-batch857-2026-10-01/raw/clone-857-crowd.json` | clone 实测：落点（按钮 right+8／top）、两个源站行为、**两个断点**的可见入口数 |
| `docs/research/liblib-canvas-batch857-2026-10-01/raw/clone-857-geometry.json` | ★ clone 的「添加角色」浮层与场景树**完全重叠** ＋ 命中测试（树里那枚按钮被浮层截走） |
| `docs/research/liblib-canvas-batch857-2026-10-01/README.md` | 本批（群众阵列）的完整取证、整改、**用户可达**与验收 |
| `docs/research/liblib-canvas-batch858-2026-10-01/raw/source-858-panel.json` | ★ **源站实测**：「添加角色」面板 **(48,52) 232 宽**、11 行逐行 y、crowd 按钮 **(56,388) 216×32**、几何**就地展开 (68,452) 204×256**、对话框 **(280,388) 220×204** ＋ **内部三段**（标题行 20／网格 106／页脚 28）＋ label 行高 **17.05px** ＋ ★ **场景树不在场**（模式互斥） |
| `docs/research/liblib-canvas-batch858-2026-10-01/raw/clone-858-panel.json` | clone 实测：与源站**同口径**的逐段读数（面板／11 行／crowd 按钮／几何就地展开／对话框内部三段）⟹ ⟹ **逐字命中** |
| `docs/research/liblib-canvas-batch858-2026-10-01/README.md` | 本批（「添加角色」面板化 ＝ D1 结案）的完整取证、整改、**用户可达**与验收；★ 顺带登记 **D8**：源站的「全景图」「选择画幅比例」**也是左侧面板模式**（batch 859 靶子） |
| `docs/research/liblib-canvas-batch858-2026-10-01/controlled-comparison.json` | ★ **受控对照**三态读数（HEAD 全回退／WORK／**MIX 半回退**）＋ 复原自检；★ 顺带登记 **D10**：`857.py` 是**归档型门禁**（读录下的 JSON 产物）⟹ ⟹ 结构上没有运行时牙 |
| `scripts/check-tailwind-classes-in-css.py` | ★ 类名**是否真的在构建产物 CSS 里**的检查器（4317 的 Tailwind 扫描是冻结的 ⟹ ⟹ 新类名可能**静默无样式**；★ 注意 CSS 里类名是**转义**的，朴素子串搜索会误报 MISS） |
| `docs/research/liblib-canvas-batch859-2026-10-01/raw/source-859-panels.json` | ★ **源站实测**：「全景图」面板 **(48,52) 232×1028**、标题条 232×48/12px、容器 `px-2`、三行 **216×32** @(56,100/132/164) 逐字「本地上传」「历史记录」「**AI生成**」；「选择画幅比例」面板同上、网格 232×324、列 `104px 104px`、gap 8px、**七格各 104×72**、描边选中 0.85／未选 0.1 ＋ ★ **场景树不在场**（模式互斥） |
| `docs/research/liblib-canvas-batch859-2026-10-01/raw/clone-859-panels.json` | clone 实测：与源站**同口径**的逐段读数 ⟹ ⟹ **逐字命中**（含旧浮层选择器 **count=0**） |
| `docs/research/liblib-canvas-batch859-2026-10-01/README.md` | 本批（「全景图」「选择画幅比例」面板化 ＝ **D8 结案**）的完整取证、整改、**用户可达**与验收；★ 顺带登记 **D11**：clone 的画幅比例**不改画布宽高比**（源站 `aj` 的 value 是数值比例并写进画布状态）<br>★★ **batch 860 更正标注（2026-10-25）**：本行登记的 **D11 说法已被 batch 860 的源站实测推翻** ⟹ ⟹ 源站**本来就不改画布**（画布容器三态恒为 1920×1080），⟹ ⟹ D11 应改写为「**取景框只支持三档** ＋ **面板七格没接 store** ＋ **自适应应为无框**」；★ **本行原文保留不改**（审计链不可重写）⟹ ⟹ 以 `docs/research/liblib-canvas-batch860-2026-10-01/README.md` 的 §11 为准 |
| `docs/research/liblib-canvas-batch861-2026-10-01/raw/source-861-panorama-diff.json` | ★ **源站实测**：「全景图」三行各自的真实行为 —— 点「本地上传」**弹出了文件选择器**（`filechooser` ＝ True）／点「历史记录」按钮 **86 → 95**（打开**全屏**资产库选择器）／点「AI生成」按钮 **86 → 98**（同一选择器 ＋ 多「上传图片」「生成」「关闭」） |
| `docs/research/liblib-canvas-batch861-2026-10-01/raw/clone-861-panorama.json` | ★ **clone 实测**（改之后）：三行逐字文本 ＋ 隐藏 file input（`accept=image/*`）＋ `filechooser` **1 次** ＋ 两种选择器形态 ＋ 喂真 PNG 后 store 出现 `localPanoramaAsset` ⟹ ⟹ **「当前全景图」从画布那张变成 `local-panorama:…`** |
| `docs/research/liblib-canvas-batch861-2026-10-01/README.md` | 本批（「全景图」三行**不再是死按钮**）的完整取证、整改、**用户可达**与验收；★ 登记 **D12**（选择器形态不同）／**D13**（本地上传走 blob 不上传）／**D14**（「AI生成」不接真实生成）／**D15**（面板多一行「当前全景图」）／**D16**（源站 `disabled:!hasCameras` 未对齐） |
| `docs/research/liblib-canvas-batch861-2026-10-01/negative-audit.json` | ★ **阴性对照** 8/8（★ 含一条**底线门禁**：选择器源码里不许出现任何网络调用 ⟹ ⟹ clone 绝不接真实全景图生成） |
| `docs/research/liblib-canvas-batch861-2026-10-01/controlled-comparison.json` | ★ **受控对照**四态 ＋ **MIX 半回退态**读数 ＋ 复原自检 |
| `docs/research/liblib-canvas-batch859-2026-10-01/negative-audit.json` | ★ **阴性对照** 9/9（每条行数中性变异先断言 SHA-256 变了 ⟹ ⟹ 跑完整门禁 ⟹ ⟹ 字节级复原） |
| `docs/research/liblib-canvas-batch859-2026-10-01/controlled-comparison.json` | ★ **受控对照**四态 ＋ **MIX 半回退态**读数 ＋ 复原自检 |
| `docs/research/liblib-canvas-batch860-2026-10-01/raw/source-860-frame.json` | ★ **源站实测**：「选择画幅比例」**七档逐档**的机位取景框（自适应**不在场**／21:9 1262×541／16:9 1262×710／4:3 1141×856／1:1 856×856／3:4 642×856／9:16 482×856）＋ ★ **画布三态恒为 1920×1080**（⟹ ⟹ **源站选比例不改画布**）＋ 框在机位视角下同样在场 |
| `docs/research/liblib-canvas-batch860-2026-10-01/raw/source-860-viewport.json` | ★ 画布容器**逐条**枚举（1920×1080 恒定 ＋ `react-flow__viewport` 732×411 恒定）⟹ ⟹ 推翻「改画布宽高比」那个说法 |
| `docs/research/liblib-canvas-batch860-2026-10-01/raw/source-860-bottombar.json` | ★ 源站视口底部 **27 枚**控件清单 ⟹ ⟹ **没有**任何比例按钮 ⟹ ⟹ clone 底部那三枚是**自己的扩展** |
| `docs/research/liblib-canvas-batch860-2026-10-01/README.md` | 本批（画幅比例**真的驱动机位取景框**）的完整取证、整改、**用户可达**与验收；★ 顺带**改写 D11**（原说法被实测推翻） |
| `docs/research/VERIFICATION_LEDGER.md` | 历批验收台账 |
| `docs/research/liblib-canvas-batch862-2026-10-01/raw/source-862-frame-thirds.json` | ★ **源站实测**：取景框 @(329,185) **1262×710** ＋ 框上开关 @(1551,193) **32×32**（`title="构图参考线"`）＋ ★ **位置公式实测命中**（329＋1262−40 ＝ 1551／185＋8 ＝ 193）＋ 「自适应」时**框与开关都不在场** ＋ 点开关后出现 **4 条**分线 |
| `docs/research/liblib-canvas-batch862-2026-10-01/raw/source-862-frame-thirds-style.json` | ★ 源站计算样式（★ 颜色经 **canvas 归一化**，才能与 clone **同口径**比）：框描边 1px／白 **18%**／内缩 1px／圆角 **12px**、分线白 **50%**、开关开启态前景 `rgb(9,202,245)` ＋ 背景 `rgba(255,255,255,0.1)` |
| `docs/research/liblib-canvas-batch862-2026-10-01/raw/source-862-frame-thirds-icon.json` | ★ 源站框上开关的 **svg 逐字**（16×16、**单 path**、`fill=currentColor`）⟹ ⟹ clone 的图标必须是**同一份 path**（不许拿近似图形） |
| `docs/research/liblib-canvas-batch862-2026-10-01/raw/clone-862-frame-thirds.json` | clone 实测：六档的开关**相对框**的偏移恒为 (框宽−40, 8) ＋ 描边／圆角／分线颜色 ＋ 点击 **0 → 4 → 0** ＋ 「自适应」时框与开关一起消失 |
| `docs/research/liblib-canvas-batch862-2026-10-01/README.md` | 本批（**取景框上的「构图参考线」开关** ＝ 源站逐字补齐）的完整取证、整改、**用户可达**与验收；★ 登记 **D17**（机位级 `aspect_ratio`／`reference_line` 写入未做）／**D18**（框像素几何差异）／**D19**（底部那枚是 clone 扩展）／**D20**（框外遮罩无模糊）＋ **D16 的诚实收窄**（两侧皆不可达） |
| `docs/research/liblib-canvas-batch862-2026-10-01/negative-audit.json` | ★ **阴性对照** 7/7（★ 含一条**自曝**：第一版 N7 因为**注释里抄了同一个字面量** ⟹ ⟹ 负控改到注释 ⟹ ⟹ 打空 ⟹ ⟹ 已改成「锚点定位代码行」＋ 立了注释纪律） |
| `docs/research/liblib-canvas-batch862-2026-10-01/controlled-comparison.json` | ★ **受控对照**四态 ＋ **MIX 半回退态**（只回退 viewport）读数 ＋ 复原自检 |
| `scripts/verify-liblib-batch862.py` | 本批门禁（**57 判据**；★ 源站期望值**只从入库的源站 raw 读**） |
| `docs/research/liblib-canvas-batch863-2026-10-01/raw/source-863-mask-literal.txt` | ★ **源站逐字入库证据**（chunk `0fmehki05gkzw.js.js` 的「外层容器 → 遮罩层 → 取景框」三段连续 JSX；文件头记 chunk 路径／字符偏移／chunk 与摘录的**两个 sha256**）⟹ ⟹ 门禁的期望值**只从它解析**（含「黑 20%」「描边 18%」两个百分比） |
| `docs/research/liblib-canvas-batch863-2026-10-01/raw/source-863-frame-mask.json` | ★ **源站运行时实测＝失败**（源站项目页本批不可用：画布节点 0、正文停在「项目加载中...」、**不发任何 XHR/fetch**；首页正常 ⟹ ⟹ 判定为源站侧故障）⟹ ⟹ 异常原文入库；★ 源站恢复后须补跑 `probes/source863_frame_mask.py` |
| `docs/research/liblib-canvas-batch863-2026-10-01/raw/clone-863-frame-mask.json` | clone 实测：遮罩层 `absolute inset-0 bg-black/20 backdrop-blur-md`、背景 `oklab(0 0 0 / 0.2)`、`backdropFilter: blur(12px)`、mask 两次 `linear-gradient`、`maskComposite: exclude, exclude`、`maskPosition: 0px 0px, 65.6667px 32px`、`maskSize: 100% 100%, 1226.67px 690px`、遮罩铺满 1358×810 @(281,88)、框 @(347,120) 1227×690 且 **boxShadow=none**／outline 1px 白 18% 内缩 1px／圆角 12px |
| `docs/research/liblib-canvas-batch863-2026-10-01/raw/clone-863-redprobe-{inside,outside}.png` | ★ **红色探针**两张取样截图（把遮罩层临时染成 `rgba(255,0,0,0.85)`）⟹ ⟹ 框外 R=**151.58**（红）、框内 R=**32.0**（没被染红）⟹ ⟹ 差 **119.58** ⟹ ⟹ **mask 真的把框那块挖空了**（★ 这是**确定性**证明；亮度比会漂移，只能作参考） |
| `docs/research/liblib-canvas-batch863-2026-10-01/raw/clone-863-{inside,outside}.png` | ★ 同一支探针的「**亮度参考**」取样（48×48）⟹ ⟹ 框内平均亮度 36.37／框外 32.85（比值 0.9033）⟹ ⟹ ★ **只作参考**：3D 场景一直在动 ⟹ ⟹ 数值会漂移（实测 0.87↔0.90）⟹ ⟹ 判据用的是**红色探针** |
| `docs/research/liblib-canvas-batch863-2026-10-01/README.md` | 本批（**取景框外的遮罩** ＝ 源站逐字补齐，**D20 结案**）的完整取证、整改、**用户可达**与验收；★ 含「源站运行时**待补**」的诚实标注 ＋ 四条方法学（变异没落地／取样点取错档／先计数再决定要不要测／像素比不可当判据） |
| `docs/research/liblib-canvas-batch863-2026-10-01/negative-audit.json` | ★ **阴性对照** 7/7（★ 含一条**自曝**：第一版 `apply_mutation` 算出变异却**没写回文件** ⟹ ⟹ 7 条变异一条都没落地 ⟹ ⟹ 负控 **0/7** 打空 ⟹ ⟹ 已改成「返回变异后的源码」＋「变异已落地」自检） |
| `docs/research/liblib-canvas-batch863-2026-10-01/controlled-comparison.json` | ★ **受控对照**五态：`HEAD-1`／`HEAD-2`／**`MIX`（只把 `maskComposite` 改成 `"add"`）**／`WORK-1`／`WORK-2` ＋ 改前／改后**同口径**探针读数 ＋ 复原自检 |
| `scripts/verify-liblib-batch863.py` | 本批门禁（**110 判据**；★ 源站期望值**只从入库的逐字证据解析**；★ 缺证据文件 ⟹ ⟹ **直接判失败**） |
| `docs/research/liblib-canvas-batch864-2026-10-01/raw/source-864-camera-write.json` | ★ **源站运行时网络取证**：点「16:9」与点「构图参考线」各发出**一条** `libtv.canvas.director.camera.update`（`var` 里 `camera_uuid`／`setting_name`／`setting_value`／`operation_source` 四键逐字）⟹ ⟹ 落点是**埋点端点** `api2.liblib.art/api/www/log/acceptor/f` ⟹ ⟹ **零工程状态写入**（只有 `project/heartbeat`）⟹ ⟹ **D17 被推翻**（源站**不**把比例／`reference_line` 写进机位对象） |
| `docs/research/liblib-canvas-batch864-2026-10-01/raw/source-864-capture-ratios.json` | ★ **源站「截图」取证** ⟹ ⟹ **源站没有比例面板**（点一下直接出图，埋点用当前取景比例）⟹ ⟹ **D23**：clone 的三档截图比例是 **clone 自己的扩展**；★ 源站**间歇弹**「Agent 已升级为 TV Director」模态（A/B）⟹ ⟹ 用「叶子节点精确文本 ＋ DOM `.click()`」关闭 ＋ 3～4 次重试 |
| `docs/research/liblib-canvas-batch863-2026-10-01/raw/source-863-frame-mask.json` | ★ **2026-10-24（batch 864）补跑** ⟹ ⟹ batch 863 那行写的「源站恢复后须补跑」**到此为止**：现在是**真实读数**——遮罩层逐字 class `absolute inset-0 bg-black/20 backdrop-blur-md`、`backgroundColor: lab(0 0 0 / 0.2)`、`backdropFilter: blur(12px)`、`maskComposite: exclude, exclude`、mask 位置 `0px 0px, 329px 185.062px`、尺寸 `100% 100%, 1262px 709.875px`、遮罩铺满 **1920×1080**、框 @(329,185) **1262×710** |
| `docs/research/liblib-canvas-batch864-2026-10-01/negative-audit.json` | ★ **阴性对照** 7/7（★ N2「`"right_panel"` 在**类型声明**与**常量**里各有一份」⟹ ⟹ 裸 `in` 检查被骗过 ⟹ ⟹ 改用 `block_between()` 锚定；★ N7 的写死值必须**与真值不同**——clone 的 `activeCameraId` 恰是 `director-camera-main`） |
| `docs/research/liblib-canvas-batch864-2026-10-01/controlled-comparison.json` | ★ **受控对照**五态（`HEAD-1`／`HEAD-2`／**`MIX`（只把坐标控件的 z 改回 `z-20`）**／`WORK-1`／`WORK-2`）＋ 复原自检；★ **第一轮自曝**：门禁**崩**了也算「有牙」⟹ ⟹ 第一版的命中测试判据**没有牙**（它跑在比例循环末位 `9:16` ⟹ ⟹ 开关与坐标控件永不重叠）⟹ ⟹ 已修（切到 `16:9` ＋ 把比例钉成判据 ＋ 加 z 序机制判据 ＋ 点前先判命中 ＋ 缺文件判红不判崩）；★ **第二轮**：HEAD 47 红／MIX 50 红／WORK 0 红，**零 CRASH**，HEAD 态命中测试 detail 原文 `'isToggle': False`＋`'命中标签': 'X 反向'`、MIX 态 z 序 detail 原文 `'gizmoZ': '20'` vs `'containerZ': '10'` |
| `docs/research/liblib-canvas-batch864-2026-10-01/raw/attrib/<态>/*.txt` | 受控对照**每一态**的完整门禁输出（HEAD-1／HEAD-2／MIX／WORK-1／WORK-2）⟹ ⟹ 可逐条核对红条原文 |
| `docs/research/liblib-canvas-batch864-2026-10-01/runtime-audit.json` | 本批门禁（`scripts/verify-liblib-batch864.py`）的产物：★ 含**不触网底线判据**（改了比例／切了参考线**不得**发出任何请求）＋「**不许造出 D17 假字段**」判据 ＋ 源站运行时取证段 ＋ 同口径对照段 |
| `docs/research/liblib-canvas-batch864-2026-10-01/README.md` | 本批（**D17 复核与推翻** ＋ 整改「构图参考线开关点不到」 ＋ **本地埋点等价实现**）的完整取证、整改、**用户可达**与验收；★ 含 **D18 结案**／**D21–D23、D25 登记** ＋ 六条方法学 |
| `scripts/verify-liblib-batch864.py` | 本批门禁（**37 判据**；★ 期望值**只从入库的源站 raw 解析**） |
| `docs/research/liblib-canvas-batch866-2026-10-01/raw/baseline-46.json` | ★ **普查基线**：★ 仓库 **563** 个 liblib `.py` 门禁里 ⟹ ⟹ **碰被跟踪源文件**的 **80** 个 ⟹ ⟹ **46 个不在回归清单** ⟹ ⟹ 逐条读数（★ **21 红 25 绿**）⟹ ⟹ 那些红**从来没人看见** |
| `docs/research/liblib-canvas-batch866-2026-10-01/raw/head464-comparison.json` | ★ **HEAD 受控对照**：★ 把被跟踪源码换回 **batch 864 提交**（`ed167382`）⟹ ⟹ 门禁脚本不动 ⟹ ⟹ 跑那 21 条 ⟹ ⟹ 再复原到工作副本跑同样 21 条 ⟹ ⟹ 判据「**红绿必须完全相同**」⟹ ⟹ 结果 **相同 21 条、不同 0 条** ⟹ ⟹ **本批引入的红 0 条** |
| `docs/research/liblib-canvas-batch866-2026-10-01/runtime-audit.json` | 本批门禁（`scripts/verify-liblib-batch866.py`，★ **18 判据 0 失败**）的产物：★ 含「**碰被跟踪源文件的门禁全部在清单里**」这条**核心保证**（★ 普查**同时扫 `.py` 与 `.mjs`**、★ 比较**按 (批次, 扩展名)**）＋「清单里每条都存在」＋「去重按 (批次, 扩展名)」＋「基线红的**每一条**都必须在 `KNOWN_RED` 里」＋「`785` 的行号断言已不在」＋「`785` 变异失败必须复原源码」＋ ★★「**缺口判定有牙**」（★ 临时删一条 ⟹ ⟹ 缺口必须恰好是那一条）＋ ★★「**独立实现复算一致**」（★ 另一条实现路径 ⟹ ⟹ 普查结论必须相同）＋ ★★「**`.mjs` 族在视野里**」 |
| `docs/research/liblib-canvas-batch866-2026-10-01/README.md` | 本批（**回归清单的覆盖面** ＋ **整改 `785` 的行号依赖与失败不复原** ＋ **修门禁自身的两个假绿**）的完整普查、归因、整改与验收；★ 含**五条方法学**（清单即旧前提普查表／「旧账」必须有对照证据／断言失败先问判据是否写反／**门禁自己也要经得起同样的检查**／**负控没打红先查变异落点**） |
| `docs/research/liblib-canvas-batch866-2026-10-01/probes/regress866.py` | ★ 回归脚本（清单 **177** 条 ⟹ ⟹ 111 → 177）⟹ ⟹ ★ 含 **19** 个 `.mjs` 静态断言门禁 ⟹ ⟹ ★ **`.py` 与 `.mjs` 是两份不同门禁** ⟹ ⟹ 旧账/WATCH 匹配**必须按 (批次, 扩展名)** ⟹ ⟹ 否则 `68.mjs` 的绿会替 `68.py` 的红背书 ⟹ ⟹ **掩盖新红** |
| `docs/research/liblib-canvas-batch867-2026-10-01/raw/baseline-tmp-deps.json` | ★ **普查基线**：★ 对每个门禁找出它引用的 `/tmp` 绝对路径 ⟹ ⟹ 再**实测**那些路径现在**是否存在** ⟹ ⟹ 不存在 ⟹ ⟹ ★ 该门禁**必然红** ⟹ ⟹ ★ 仓库里引用 `/tmp` 的门禁 **40** 个 ⟹ ⟹ 其中**实测**依赖已消失文件的 **16** 个 ⟹ ⟹ 逐条读数（★ **18 条 14 红 4 绿**）⟹ ⟹ ★ 其中 **14** 个**根本不在**回归清单里 ⟹ ⟹ ⇒ **那些红从来没人看见** |
| `docs/research/liblib-canvas-batch867-2026-10-01/raw/negative-audit.json` | ★ **负控读数**：★ **十二条**负控逐条结果 ⟹ ⟹ ★ **12/12 全打红** ⟹ ⟹ 源码**字节级干净**（★ 复原自检过 ⟹ ⟹ 含回归清单脚本本身）⟹ ⟹ ★ N1–N10 证明**被整改的七条门禁**有牙 ⟹ ⟹ ★★ G1／G2 证明**本批门禁自己**有牙（★ G1 删掉清单里的 `761.py` ⟹ ⟹ 缺口必须精确指出它；★ G2 删掉它**并把同一条写进注释** ⟹ ⟹ 仍必须翻红 ⟹ ⟹ 守住「`parse_gates()` 先剥注释」那条修复）⟹ ⟹ ★ 变异**逐条**落在【被断言读的那个量】上 |
| `docs/research/liblib-canvas-batch867-2026-10-01/runtime-audit.json` | 本批门禁（`scripts/verify-liblib-batch867.py`，★ **53 判据 0 失败**）的产物：★ 含「**依赖已消失 `/tmp` 文件的门禁全部在清单里**」这条**核心保证** ＋ 「清单里每条都存在／无重复」＋ 「**独立实现**重算普查 ⟹ ⟹ 两边必须一致」＋ 七条门禁逐条检查（★ 跳过**不计入分母**／★ 旧的「跳过=失败」写法不许还在／★ **不许**写死行号／★ **不许**写死会变的常量／★ 「读整文件的『不含』断言」必须用**剥注释后**的变量）＋ 「**十二条**负控**全部打红**」＋ 「变异**复原了源码**」 |
| `docs/research/liblib-canvas-batch867-2026-10-01/README.md` | 本批（**「依赖已消失的 `/tmp` 文件」的那批门禁**⟹ ⟹ 让它们的红**被看见**）的完整普查、归因、整改与验收；★ 含**五个真缺陷**（★ 「跳过」被实现成「失败」／★ 门禁断言了一个**已被修复的 bug**／★ 写死行号当断言／★ 门禁绿着却没在验它声称要验的东西／★★ **门禁自己的清单解析器不剥注释** ⟹ ⟹ 缺口判定恒空 ⟹ ⟹ **门禁一度是假绿的**）＋ **七条方法学**（★ 「必然红」的门禁是一份**环境依赖清单**／★ 「门禁红」先问「**那个 bug 是不是已经被修**」／★ 「跳过」必须**真的跳过**⟹ ⟹ 但**不是**改成「通过**」／★ 判据「绿」本身**不能证明**它有效／★ 「全文不含某串」必须**剥掉注释**再查／★★ 「**门禁自己**也必须有负控 ⟹ ⟹ 且负控要**能被证伪**」／★ 负控没打红**先查变异落点**）★ 并**明写未做的事**（★ `554`／`562` 的 fixture 与 `750`／`751` 的探针**不可恢复** ⟹ ⟹ 那几条**仍然红** ⟹ ⟹ 但已登记旧账 ＋ 已进清单） |
| `docs/research/liblib-canvas-batch867-2026-10-01/probes/regress867.py` | ★ 回归脚本（清单 **189** 条 ⟹ ⟹ 177 → 189）⟹ ⟹ ★ 补进「依赖已消失 `/tmp` 文件」的那 **16** 个 ⟹ ⟹ 含 `554`／`562`／`565`／`760`／`761` |
| `docs/research/liblib-canvas-batch867-2026-10-01/probes/verify_regression_log.py` | ★ **回归自洽核对**脚本：★ 「落盘 189 条」这句话**本身**不能证明日志没漏 ⟹ ⟹ ⇒ 九条判据（落盘==清单／清单无重复／日志**条目行**==落盘／**逐条** (批次, 扩展名, rc) 相同／条目之间**无孤儿续行**／末尾摘要块**数字**一致／末尾摘要块**红名单**一致／红全旧账／新红 0）⟹ ⟹ ★ 实测 **9 条核对 0 失败** |
| `docs/research/liblib-canvas-batch867-2026-10-01/raw/regression-consistency.json` | ★ **回归自洽核对**的读数（★ 落盘 189 条／日志 196 行 ⟹ ⟹ 其中 **189** 行是条目行） |
| `scripts/verify-liblib-batch867.py` | 本批门禁 |
| `scripts/verify-liblib-batch866.py` | 本批门禁 |
| `scripts/verify-liblib-batch785.py` | ★ **整改后**的 785：★ **行号只当提示**、定位靠 needle **唯一命中** ＋ 多行上下文 ＋ `all_hits` ⟹ ⟹ ★ **变异失败必复原源码** ⟹ ⟹ 结果**正向 14/14、阴性 7/7** |
| `docs/research/liblib-canvas-batch865-2026-10-01/raw/source-865-mp-verbatim.txt` | ★ **源站逐字**（chunk `0fmehki05gkzw.js.js` 的 `mP` 组件；文件头记 chunk 路径／字符偏移／chunk 与摘录的**两个 sha256**）⟹ ⟹ 取景框那四层是「**遮罩层／空框／三分线层／开关**」**四者平级**，框里**零 children** |
| `docs/research/liblib-canvas-batch865-2026-10-01/raw/source-865-frame-structure.json` | ★ **源站运行时**取证：遮罩容器**直接子元素数 = 4**、**四者都直属容器 = True**、那个**框的子元素数 = 0**、**框的 `pointerEvents` = `"none"`** ⟹ ⟹ 逐字 ＋ 运行时**双重证实** D25 |
| `docs/research/liblib-canvas-batch865-2026-10-01/raw/clone-865-pixels.json` ＋ `raw/clone-865-pixels-{old,new}.png` | ★ **像素对照**（隐藏 3D canvas ＋ 纯色底 ⟹ ⟹ DOM 手术还原旧结构 ⟹ ⟹ 两次截图确定性可比）：**846,630** 像素逐个比对 ⟹ ⟹ **不同像素 0 个**、**最大通道差 0** ⟹ ⟹ ★ **D25 是纯结构对齐，视觉无差别** |
| `docs/research/liblib-canvas-batch865-2026-10-01/raw/negative-audit.json` | ★ **阴性对照** 7/7；★ **N2 打空并已修**：`aria-hidden="true"` 全文 **11 处** ⟹ ⟹ 负控锚点不唯一（改到了别处）＋ **门禁静态判据本身是「全文 contains」的假绿** ⟹ ⟹ 两条都修（负控锚点扩到唯一 ＋ 门禁改锚到**三分线层自己的开始标签** ＋ 加「锚点唯一性」判据） |
| `docs/research/liblib-canvas-batch865-2026-10-01/raw/regression.json` | ★ **回归**（**111 条**清单）结果；★ 清单里**补入了 `77`／`788`**（它们**不在** batch 864 清单里 ⟹ ⟹ 那些红从来没人看见）⟹ ⟹ 两条老门禁的**旧前提**已整改（`77` 写死个数 → 结构性判据 ＋ 窄口径噪声过滤；`788` 写死行号 → 锚点式） |
| `docs/research/liblib-canvas-batch865-2026-10-01/controlled-comparison.json` | ★ **受控对照**五态（`HEAD-1`／`HEAD-2`／**`MIX`（只把框改成开标签 ⟹ ⟹ 三分线层从「兄弟」变成「子元素」）**／`WORK-1`／`WORK-2`）＋ 复原自检；★ MIX 变异**两处各改一行** ⟹ ⟹ 行数中性、位置偏移不变 |
| `docs/research/liblib-canvas-batch865-2026-10-01/runtime-audit.json` | 本批门禁（`scripts/verify-liblib-batch865.py`）的产物：★ **22 判据、0 失败**；★ 含四者的**父子关系与顺序**、框是**空框**、三分线层的**裁剪／圆角／aria**、四条线的**相对位置百分比**、开关的**容器坐标**、D26 的**源站／clone 并排断言**、以及「**坐标控件六枚按钮全部命中自己**」 |
| `docs/research/liblib-canvas-batch865-2026-10-01/README.md` | 本批（**D25 结案并对齐** ＋ 整改 **batch 864 的后遗症** ＋ **D26 核实为非差距**）的完整取证、整改、**用户可达**与验收；★ 含**像素对照**与**四条方法学** |
| `scripts/verify-liblib-batch865.py` | 本批门禁（**22 判据**；★ 期望值**只从入库的源站 raw 解析**；★ 静态判据**锚到被断言的那一处**、不是全文 contains） |

★ ★ **每批 README 的 §「复现步骤」都写了这条链**：契约提取 → 源站实测 →
clone 实测 → 门禁 → 阴性 → 回归 → 受控对照。**先看那一条**，
就能知道某个页面的结论是**实测来的**还是**推来的**。
