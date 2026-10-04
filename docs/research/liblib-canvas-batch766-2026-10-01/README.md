# Batch 766 — 用行为反推取代标记扫，并把 764 未验证的三类控件逼出来量

## 选题

764 明确留了两条不声称，本批正面处理：

① **路径锚点（`:825`）、路径变换（`:866`）、FOV（`:1579`）三类控件两轮一次都
   没渲染出来** ⟹ 763 那句「推测同样受影响」对这三类**仍然只是推测**。

② **边界检测是按 data-* 标记做的，标记挂在外层容器上的控件会漏检**
   —— 764 自己承认的。

本批的做法是**换一种查法**：不看标记，只看行为。焦点落在控件上时按 Esc，读
「事件有没有到达 window 冒泡」：

| 读数组合 | 判别 |
| --- | --- |
| `reachedCapture=true` 且 `reachedBubble=false` | 有人在下面 stopPropagation 了 ⟹ **边界候选（D1 的签名）** |
| `reachedBubble=true` 且 target 可编辑 | 事件上来了，被 `DirectorDesk.tsx:487` 的 `if (isEditable) return;` 挡在门外 |
| `reachedBubble=true` 且 target 不可编辑 | 事件畅通 |

然后把**行为分类**与**标记分类**交叉成一张表，交叉表里对不上的格子就是 ②
那个漏洞的具体形状。

**为什么必须这么测**：逐控件按真 Esc 时，不可编辑控件会顺着阶梯把整个导演台
关掉，后面几十格全变空（765 的 R63 同族）。所以页面一加载就往 window 上装
传播探针（**注册在 React 的监听器之前**，因为导演台是后来才挂载的），并在
冒泡阶段调 `stopImmediatePropagation()` 冻住导演台自己的处理器 —— 事件照样
能到达 window（所以「到没到」照常可测），但导演台不会有任何反应。
**这一批只测传播，不测效果。**

## 三类控件的渲染条件（静态侦察，本批先查清才动手）

| 控件 | 位置 | 渲染条件 |
| --- | --- | --- |
| 路径变换 9 个数值框 | `:1041/1056/1071` | `MotionPathInspector` 内**无条件**渲染，只要 `{selectedPath ? … : null}`（`:2749`）成立 |
| 路径锚点位置 3 个框 | `:825` | 再加一道 `{selectedAnchor ? … : null}`（`:1134`）⟹ **必须再点一个锚点** |
| 路径锚点控制柄 6 个框 | `:1191/1207` | `{selectedAnchor.type !== "vertex" ? … : null}`（`:1189`）⟹ **必须把锚点类型从 `vertex` 改成 `symmetric`/`asymmetric`** |
| FOV 滑杆 | `:1652` | 只要 `{selected.camera ? <CameraFovField/> : null}`（`:2579`）⟹ 选中机位对象就有 |
| FOV 数值框 | `:1667` | 同上，但**它那一段源码里 `gesture` 出现 0 次** |

`selectedPath` 要 `selectedTrack?.motionPathId`，而 `selectedTrack` 要求时间轴
轨道选中且该轨道的 `objectId` 等于当前选中的对象（`:2159-2168`）。

764 就是停在前两步：它记的「+15 个控件」正好是 9 路径变换 + 6 锚点按钮/类型
按钮，**锚点数值框一个都没渲染**。

## 判据（11 条：9 PASS / 2 FAIL）

FAIL 里 1 条是缺陷（D7），1 条是不声称（J11）。两轮**逐字段一致**，且先证明
可比（766a 比 8 个 key、766b 比 7 个 key 的归一化 diff 全为空；**每轮开头都清
了 `liblib-tv-director-project-v1:*`**，因为建轨迹是破坏性的且会持久化）。

| 判据 | 结论 | 读数 |
| --- | --- | --- |
| J1 | PASS | 两轮可比且逐字段一致（766a 8 key / 766b 7 key，diff 全空） |
| J2 | PASS | ★ **行为反推判据成立**：凡是自身带边界标记的控件一律 `swallowed`（无一例外），`reachedBubble=true` 的格子 `reachedCapture` 也必为 true；193 格焦点全部成功、0 格没聚焦上 |
| J3 | PASS | ★ **更正 764 承认的漏检风险方向**：三个上下文里 `no-marker \| swallowed` 恒为 **0** ⟹ 标记扫的失效方向是**多报**不是漏检 |
| J4 | **FAIL** | **缺陷 D7**：容器级 `data-director-camera-fov-field` 把 FOV 数值框与它的关键帧按钮各误判成 1 个边界控件（两者 `reachedBubble=true`、并没有吞 Esc）。每个上下文固定 **2** 格误判 |
| J5 | PASS | ★ **764「推测同样受影响」对路径变换已验证**：9 个 `path-transform-axis` 数值框**全部**吞 Esc、全部自身带标记；从机位属性增量进来（+15 控件 / +9 边界，两轮一致） |
| J6 | PASS | ★ **对路径锚点位置已验证**：3 个 `path-anchor-position` 数值框**全部**吞 Esc |
| J7 | PASS | ★ **对 FOV 已验证，且要分开说**：滑杆（`-fov`，range，自身 spread gesture）**吞**；同屏数值框（`-fov-number`，**没有** gesture）**不吞**。764 说的「FOV 标记挂在外层容器上」不准确 |
| J8 | PASS | ★ **未验证清单最后一项也关掉**：路径锚点**控制柄** 6 个框（入/出 × 3 轴）**全部**吞 Esc。关键是把锚点类型从 `vertex` 改成 `symmetric` |
| J9 | PASS | 控件数逐档递增且两轮一致：52 → 67 → 74，自身带标记的 13 → 22 → 25；0 格扫到一半导演台消失、0 格没获得焦点 |
| J10 | PASS | **冻结机制本身有效**：逐控件按 Esc 时导演台毫无反应，所以三段扫查各能扫几十格 |
| J11 | **FAIL** | ★ **本批判不了「冻结期间导演台自己的处理器会不会有反应」** —— 冻结就是把它挡掉的。「吞 Esc 对界面意味着什么」沿用 763/764 在别的上下文量过的结论 |

## 缺陷

### D7（低，新增）容器级 data-* 标记会把非边界控件误判成边界控件

FOV 那一段的外层容器 `data-director-camera-fov-field`（`:1604`）**同时包着滑杆
与数值框**：

- 滑杆的 `input[type=range]`（`:1652`）自己带 `data-director-camera-fov` 并
  spread 了 gesture（`:1655`）⟹ **是真边界控件**，实测吞 Esc；
- 数值框（`:1667`）**没有** gesture spread —— 它那一段源码里 `gesture` 出现
  **0 次** ⟹ **不是**边界控件，实测 `reachedBubble=true`、**没有吞 Esc**；
- 同段的「当前帧有关键帧」按钮（`:44` 格）同样只是被容器标记捎带上 ⟹ 也不吞。

用 `closest('[data-director-camera-fov-field]')` 判边界，会把这两个算进去，
于是**每个上下文固定 2 格误判**，两轮一致。

- **严重度低**：这是**测量工具**的缺陷，不是产品的缺陷 —— 那两个控件本来就不
  该吞 Esc，**行为是对的**。
- **对 764 的影响**：764 用的就是标记扫，方向上它会**多报**，所以 764 记的
  「43 个边界控件全部吞 Esc」里**至少含这 2 个误判** ⟹ **43 是上界**。本批
  没有重算那个 43（那是另一批的读数）。

## 观察

- **O1**：边界控件的判别式在本批是 **1:1** 的：`boundary-own ⟺
  reachedCapture=true 且 reachedBubble=false`，共 193 格无一例外。反过来
  `reachedBubble=true` 的格子 `reachedCapture` 也全为 true ⟹ 「事件完全没
  上来」这种情况**一格都没有**。
- **O2**：**标记扫的失效方向取决于标记集本身**。766b 首版只把
  `path-anchor-handle`/`path-anchor-position` 算作边界标记，于是那 9 个路径
  变换框（带 `path-transform-axis` 标记）被标成 `no-marker` 而行为是
  swallowed —— 那是**假阴性**。把属性补进标记集后交叉表归零。所以
  「标记扫不可靠」不等于「标记扫总是漏检」，而是**它和标记集一样脆**。
- **O3**：**属性面板是可滚动容器**。锚点选项按钮实测在 `y≈1769`，而视口高只有
  1000 ⟹ 扫网格全部跳过、`elementFromPoint` 永远打不中，表现为 `noHit`。
  任何「扫网格找元素」的探针在这个面板上都必须**先滚进视口**。
- **O4**：**相机轨道在选中相机对象时就自动选中了**（`director-track-camera-main`
  读数 `selected=true`）⟹ `selectedTrack` 自动解析成功，不需要额外点轨道行。
  `data-director-track-draw-trail` 那一次点击同时做了「选中相机轨道」+「打开
  路径菜单」。

## 探针教训（返工项）

- **R67｜JS 片段的语法要单独过一遍 `node --check`，别靠跑浏览器发现**。766a
  连续三轮白跑，每轮都是「少一个 `}` / 多一个 `)` / 少一个 `pg.evaluate` 的收尾
  括号」这种一眼可见的错误 —— 而每次都要起浏览器、跑十几秒，才在日志末尾看到
  `SyntaxError`，前面十几秒全废。抽出所有 `()=>…` 片段逐个 `node --check` 只要
  0.1 秒。**写完这个检查器之后，它当场又抓出了我新加的 3 段同类错误。**
- **R68｜「元素不在 DOM 里」和「元素在视口外」是两回事，报错长得却一样**。
  766a 找不到路径预设按钮时只记了 `missing:true`，我据此以为「这个种子数据
  建不出轨迹」；实际上按钮在**折叠菜单**里（`pathMenuLeft` 为 null 时根本不
  渲染），入口是 `data-director-track-draw-trail`。教训：把「不在 DOM」「在
  DOM 但没渲染出盒子」「在 DOM 且有盒子但在视口外」三种情况**分开记**，
  否则一个探针缺陷会被读成产品结论。
- **R69｜扫网格之前先滚进视口**（O3）。看起来像「点不到」，其实是「在屏幕外」。
- **R70｜要冻住别人的处理器，就必须在它之前注册**。导演台在挂载时才往 window
  上装 Esc 监听器，所以页面一加载就装的探针**注册在前**；在冒泡阶段调
  `stopImmediatePropagation()` 就能挡住它。

## 不声称

- **无源站对照**：本批全部结论只针对 clone 自身的行为自洽性。
- **冻结期间导演台自己的处理器会不会有反应，本批判不了**（J11）。本批只测
  传播，不测效果。
- **只测了 1440 桌面一档视口**；移动端抽屉形态下的同一批控件没测。
- **只测了机位这一个对象**：角色/道具上下文里的同类控件没重扫（764 扫过）。
- **只建了 `line` 一种轨迹预设**；`ring`/`rectangle` 没建，锚点数量因此固定为 2。
- **没有测锚点类型为 `asymmetric` 的情形**（只测了 `symmetric`）。
- **没有重算 764 那个「43 个边界控件」**。本批证明标记扫会**多报**，所以 43
  是上界，但具体少几个没量。
- **没有测拖动手势本身**（ArrowUp 之类）—— 本批只测 Esc 的传播。
- 建运动轨迹是**破坏性**操作，会改项目并持久化到 localStorage；本批每轮开头
  清了 `liblib-tv-director-project-v1:*`，但探针结束时**没有把项目恢复原状**
  （Playwright 每次新开 context，不会影响他人）。
- D7 是**测量工具**的缺陷，不是产品缺陷 —— 那两个被误判的控件行为本来就是对的。

## 复现

```bash
export PATH="$HOME/.nvm/versions/node/v24.6.0/bin:$PATH"
cd /Users/yangjiefeng/Documents/wubuku/liblib-tv

# 0. 先把探针里的 JS 片段过一遍 node --check（R67：别靠跑浏览器发现语法错）
$HOME/.pyenv/shims/python3 /tmp/jscheck.py /tmp/dbg766a.py /tmp/dbg766b.py

# 1. 起 clone（4317）
npm run dev

# 2. 两个探针（各 2 轮；原始读数落在 raw/，探针原件同批提交在 probes/）
$HOME/.pyenv/shims/python3 /tmp/dbg766a.py   # → raw/vb766a.json
$HOME/.pyenv/shims/python3 /tmp/dbg766b.py   # → raw/vb766b.json

# 3. 汇编（数字全部现算，findings 与 judgments[].evidence 写盘前逐条断言相等）
$HOME/.pyenv/shims/python3 \
  docs/research/liblib-canvas-batch766-2026-10-01/probes/mk766audit.py

# 4. 验收（静态层 + 产物层 + 原始读数交叉核对 + 阴性对照）
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch766.py
```

**授权边界**：源站可执行副作用 CRUD，但禁止付费与真实生图生视频。本批未碰
源站，也未改 `src/`；建运动轨迹用的是本地预设 `line`，不是 AI 生成。
