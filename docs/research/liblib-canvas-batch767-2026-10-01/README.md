# Batch 767 — 导演台 6 个 disclosure 浮层的关闭契约普查

## 选题

765 只量了**一个**浮层（导出面板），查出 D4（Esc 关面板后焦点掉到 body）、
D5（没有外点关闭）、D6（disclosure 契约残缺）。但全仓带 `aria-expanded` 的
disclosure 一共 **6 个**，而且静态上就已经分成两派：

| 浮层 | 触发器 | 浮层 | 关闭 effect |
| --- | --- | --- | --- |
| 导出面板 | `data-director-export-trigger` | `data-director-export-panel` | **无** |
| 预设运镜面板 | `data-director-camera-preset-trigger` | `data-director-camera-preset-panel` | 有（`DirectorTimeline.tsx:578-599`） |
| 创建运动轨迹菜单 | 「创建运动轨迹」`DirectorTimeline.tsx:1121` | `data-director-motion-path-menu` | 有（`:554-575`） |
| 虚拟相机面板 | `data-director-phone-vcam-trigger` | `data-director-phone-vcam-panel` | Esc 有（`DirectorPhoneVcamPanel.tsx:286-296`），外点无 |
| 添加群众阵列面板 | `data-director-crowd-trigger` | `data-director-crowd-panel` | **无** |
| 模型库面板 | `data-director-model-library-trigger` | `data-director-model-library-panel` | 有（`DirectorViewport.tsx:2734-2753`） |

静态只能证明「某条路径可达/不可达」（765 的 R64），**证明不了浏览器实际
怎么处理事件**。所以本批把同一套问题挨个问一遍，让读数定案：打开是否移动
焦点、外点能不能关、Esc 能不能关、aria 契约。

这批的用处不只是「又查出几个毛病」：**同一族里有做对了的样本**，可以当
D5/D6 修法的同仓先例。

## 判据（11 条：6 PASS / 5 FAIL）

FAIL 里 3 条是缺陷（D8/D9/D10），2 条是不声称（J9 焦点读数被污染、J10 测错了
触发器）。两轮**逐字段一致**（`results` 整棵树的归一化 diff 为空），且先证明
可比：本批只点触发器与浮层外面，每轮开头还清了导演台项目的 localStorage。

| 判据 | 结论 | 读数 |
| --- | --- | --- |
| J1 | PASS | 两轮逐字段一致；本批无破坏性动作、每轮清 localStorage |
| J2 | PASS | 6/6 能打开，且**打开瞬间一律不移动焦点**（焦点留触发器、不进浮层）—— 6 个完全一致，按 disclosure 惯例**不判缺陷** |
| J3 | PASS | **外点关闭 3/6 有效**：预设运镜、路径菜单、模型库。点外面**不关**的 3 个：导出面板、虚拟相机、群众阵列。6 格的落点都验过「不在浮层内、且不是可点元素」 |
| J4 | **FAIL** | ★ **缺陷 D8（中）**：**添加群众阵列面板开着时按 Esc，把整个导演台关掉了**（2/2 轮，探针不得不重开） |
| J5 | PASS | 能测到 Esc 的 2 个都**只关自己不关导演台**：导出面板（阶梯里唯一那档 `:557`）、虚拟相机（自己的 window 捕获监听 + `stopImmediatePropagation`） |
| J6 | **FAIL** | ★ **缺陷 D9（低）**：3/6 没有外点关闭 —— 765 的 D5 不是个案，是通病。**同仓已有正确实现**可照抄 |
| J7 | **FAIL** | ★ **缺陷 D10（低）**：`role="dialog"`+`aria-label` 只有 **2/6**；`aria-controls` **0/6**、`aria-haspopup` **0/6** —— 765 的 D6 是全族通病 |
| J8 | PASS | ★ **同仓有完整的正确样本**（`DirectorViewport.tsx:2734-2753`）：外点 pointerdown + 捕获阶段 Esc + `preventDefault` + `stopImmediatePropagation` |
| J9 | **FAIL** | ★ **「关闭是否归还焦点到触发器」这一问 6 格全废**：本批先测外点再测 Esc，而**点空白本身就把焦点挪到对话框根** ⟹ 不下判断 |
| J10 | **FAIL** | ★ **路径菜单那格测的触发器不是带 `aria-expanded` 的那个**：本批点的是 `data-director-track-draw-trail`（只有 `aria-pressed`），`aria-expanded` 读数是 `null`，**如实记、不当缺陷** |
| J11 | PASS | 没点任何有副作用的按钮：提交、虚拟相机「连接」、模型库添加都没点 |

## 缺陷

### D8（中，新增）添加群众阵列面板开着时按 Esc 会关掉整个导演台

- `crowdPanelOpen` 的 state 在 `DirectorViewport.tsx:2545`；
- 而 `DirectorDesk.tsx` 的 Esc 阶梯（`:549-568`）**对它 0 处引用** ——
  阶梯里唯一的浮层档是 `if (exportPanelOpen)`（`:557`）
  （实测 `grep -cE "crowdPanelOpen|modelLibraryOpen|phoneVcamOpen|presetPanelLeft|pathMenuLeft" DirectorDesk.tsx` = **0**）；
- 而群众阵列面板**自己也没有** Esc 处理（模型库有，`:2742`）；
- ⟹ Esc 从阶梯顶一路走到 `closeWorkspace()`。

**严重度中**（不是低）：后果是整个工作区连同未保存的改动一起消失，而用户只是
想关一个小面板。**这是本批唯一一个「按 Esc 丢工作区」的路径。**

**修法二选一**：①在阶梯里给 `crowdPanelOpen` 加一档，位置在
`closeWorkspace()` 之前 —— 同族的 `exportPanelOpen`（`:557`）就是这么做的；
②或者照抄模型库面板那份实现（`DirectorViewport.tsx:2734-2753`）：自己监听捕获
阶段 Esc 并 `stopImmediatePropagation()`。

### D9（低，新增，扩宽 765 的 D5）6 个浮层里 3 个没有外点关闭

导出面板、虚拟相机面板、添加群众阵列面板都没有「点外面关闭」的监听。765 的 D5
把「导出面板没有外点关闭」当个案，本批证明**这是 3/6 的通病**。

**同仓最完整的一份实现**是模型库面板（`DirectorViewport.tsx:2734-2753`）：外点
`pointerdown` + 捕获阶段 Esc + `preventDefault()` + `stopImmediatePropagation()`。
路径菜单（`:554-575`）与预设面板（`:578-599`）也各有一个关闭 effect。
⟹ **D5 不需要新发明，照抄同族即可。**

### D10（低，新增，扩宽 765 的 D6）disclosure 的 aria 契约全族残缺

- `role="dialog"` + `aria-label`：**只有 2/6**（群众阵列 `:3086-3087`、
  模型库 `:3163-3164`）；
- 导出面板是**无 role 的 `<section>`**、预设面板与路径菜单是**无 role 的裸
  `<div>`**、虚拟相机面板同样没有；
- 6 个触发器**全都没有** `aria-controls` 与 `aria-haspopup`（只有 `aria-expanded`）。

另外 4 个浮层里有的带 `<h2>`/`<h3>` 标题 —— **标题不构成可访问名**（要靠 role
或 aria-label）。

## 观察

- **O1**：6/6 打开都不移动焦点（焦点留在触发器上、不进浮层），两轮一致。5 个
  浮层各有 ≥2 个可聚焦控件（模型库 15、预设 10、导出 5、路径菜单 5、群众 5、
  虚拟相机 2）⟹ 键盘用户要自己 Tab 进去。按 disclosure 惯例这不算缺陷，
  **不判缺陷**，只记事实。
- **O2**：**静态与读数在「外点关闭」上完全对上**：有关闭 effect 的那三个实测
  都关，没有 effect 的那三个实测都不关。本批这一次静态推理与读数没有分歧 ——
  但这是运气，765 的 R64 已经记过静态证明不了浏览器的事件处理。
- **O3**：**Esc 的两种正确实现方式在同仓并存**：导出面板靠导演台阶梯里的一档
  （`:557`），虚拟相机与模型库靠自己的 window **捕获**监听 +
  `stopImmediatePropagation()`。捕获优先于冒泡，所以后者能在阶梯之前把事件
  截住 —— 这也是为什么虚拟相机只关自己不关导演台。**这也是 D8 的修法依据。**
- **O4**：**预设运镜的触发器有 `disabled` 条件**（`DirectorTimeline.tsx:1084`：
  选中轨道不是 camera 或机位在跟随中都 disabled）⟹ 测它之前必须先选中相机
  对象，否则触发器点不动。

## 探针教训（返工项）

- **R71｜JS 的 `in` 只能查对象属性，不能用在字符串上**。我写
  `('aria-controls' in trigSeg)` 查 outerHTML 是不是含这个属性，六个浮层
  **每一格**都在运行时抛 `TypeError: Cannot use 'in' operator`。字符串判定
  要用 `.includes()`。我把这个记成了 Python 的 `in`。
- **R72｜`node --check` 只验语法、不验语义**。766 的 R67 那个检查器抓语法错很
  有效，但它对 R71 那个 `in` 完全无感 —— 语法合法、运行即抛。结论：检查器能
  把「少一个括号」这类错提前 0.1 秒拦下，**类型/语义错仍然只能靠真跑**。
- **R73｜「先测 A 再测 B」会污染 B 的读数**。本批顺序是「先点浮层外面测外点
  关闭、浮层还开着才测 Esc」，结果**点空白本身就把焦点挪到了对话框根** ⟹
  「关闭是否归还焦点」这一列 6 格全废（J9）。要同时量两件事就得**各开一次干净
  的浮层**，不能串在一条时间线上。765 的 R63 是同一族的另一面（准备动作
  **关掉了**整个导演台）。
- **R74｜外点那一下的落点必须先验再点**。本批对每个浮层都先
  `elementFromPoint` 读出那里是什么元素、`clickable` 是不是 false，确认「不在
  浮层内、且不是按钮」才点 —— 并把 `tried` 列表原样记进产物。R59 的同族：
  **先量可点性，再点**。

## 不声称

- 无源站对照：本批全部结论只针对 clone 自身的行为自洽性。
- ★ **「关闭时是否把焦点归还触发器」这一问本批没有干净读数**（J9）。要干净地
  量得重跑一版「打开 → 直接按 Esc → 读焦点」。
- ★ **路径菜单那一格测的触发器不是带 `aria-expanded` 的那个**（J10）。
- **只测了 1440 桌面一档视口**。虚拟相机/群众阵列/模型库三个触发器在视口
  左侧的 rail 上，窄视口下可能不可见或位置不同 —— 未测。
- **3 个浮层因为外点那一下已经关掉了，Esc 无从测起**（预设运镜、路径菜单、
  模型库）⟹ 它们的 Esc 行为**本批没有读数**。静态上三者都有 Esc 处理，
  但**静态不能替代读数**。
- **没有测打开状态下再点一次触发器会怎样**（toggle 关闭 vs 报错）。
- **没有测这些浮层里的 Tab 围栏**（762/765 只量过导出面板与对话框级）。
- **没有测多个 disclosure 同时开着会怎样** —— 本批每次都从干净状态开始。
- **没有测虚拟相机在录制中的 Esc**：`DirectorPhoneVcamPanel.tsx:292` 写着
  `if (!recording) onClose()`，录制中按 Esc 不关面板 —— 但本批没进录制状态，
  那条分支**未验证**。
- **没有点任何提交/生成/连接按钮**；导出面板的提交按钮、虚拟相机的「连接」、
  模型库的添加都没点。

## 复现

```bash
export PATH="$HOME/.nvm/versions/node/v24.6.0/bin:$PATH"
cd /Users/yangjiefeng/Documents/wubuku/liblib-tv

# 0. 先把探针里的 JS 片段过一遍 node --check（只验语法，验不了语义 —— 见 R72）
$HOME/.pyenv/shims/python3 /tmp/jscheck.py /tmp/dbg767a.py

# 1. 起 clone（4317）
npm run dev

# 2. 探针（2 轮；原始读数落在 raw/，探针原件同批提交在 probes/）
$HOME/.pyenv/shims/python3 /tmp/dbg767a.py   # → raw/vb767a.json

# 3. 汇编（数字全部现算，findings 与 judgments[].evidence 写盘前逐条断言相等）
$HOME/.pyenv/shims/python3 \
  docs/research/liblib-canvas-batch767-2026-10-01/probes/mk767audit.py

# 4. 验收（静态层 + 产物层 + 原始读数交叉核对 + 阴性对照）
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch767.py
```

**授权边界**：源站可执行副作用 CRUD，但禁止付费与真实生图生视频。本批未碰
源站，也未改 `src/`；没点任何提交/生成/连接按钮。
