# Batch 349 — 生成完成提示重复派发 11 次 + 清理死状态字段

日期：2026-10-01
范围：`src/components/frameos/FrameosGenerationOverlay.tsx`、`src/store/frameosStore.ts`
性质：**CLONE_DECISION**（克隆侧缺陷，无源站采样证据；源站人机验证仍被拦）

---

## 缺陷一：一次生成弹出 11 条一模一样的「生成完成 ✓」

### 机制

`FrameosGenerationOverlay` 的进度由 `setInterval(tick, 50)` 驱动。收尾逻辑写在 `tick` 里：

```ts
if (p >= 100) {
  setTimeout(() => {
    useFrameosStore.setState({ currentGeneration: null });
    window.dispatchEvent(new CustomEvent("frameos-toast", {...}));
  }, 500);
}
```

`p >= 100` 之后 **interval 并不会停**（没有 `clearInterval`），所以收尾窗口内的
**每一个 tick 都会再排一个 `setTimeout(500)`**。

第一个 timeout 在 500ms 后把 `currentGeneration` 置 null，触发 effect 清理、清掉
interval——但它之前排下的那些 timeout 已经躺在定时器队列里，仍会陆续触发，
**每个都 dispatch 一次 `frameos-toast`**。而 `showToast` 不去重、逐条堆叠。

静态推算：500ms 窗口 / 50ms 间隔 ≈ **11 个** timeout。

### 实测（修复前，真实 30 秒 mock 时长）

`scripts/probe-frameos-batch349-generation-toast.py`：

```json
{
  "toast_event_count_total": 11,
  "dom_toast_count": 11,
  "dom_done_toast_count": 11,
  "dom_toasts": ["生成完成 ✓", ... 共 11 条]
}
```

**推算的 11 与实测的 11 逐一对上。**

### 修复

加一个「本次生成已完成」闩锁，并在进入收尾时立刻停表：

```ts
let finished = false;
let intervalId: ReturnType<typeof setInterval> | null = null;
const tick = () => {
  ...
  if (p >= 100 && !finished) {
    finished = true;
    if (intervalId !== null) clearInterval(intervalId);
    setTimeout(...);   // 每次生成只排一个
  }
};
tick();
intervalId = setInterval(tick, 50);
```

`finished` 是 effect 体内的局部变量，effect 依赖 `currentGeneration`，所以
**每次新生成天然获得一个全新的闩锁**——验证器专门对「第二次生成也要提示」
做了断言，盯的就是这个回归方向。

> 顺带的好处：进度跑满后不再每 50ms 触发一次 `setProgress`/`setNow`（每秒 20 次渲染）。

---

## 缺陷二：`generations` 是死状态字段

### 普查方法

写了普查工具 `scripts/frameos_deadstate_census.py`（**已入库**，可复跑）：
抽出 `FrameosCanvasState` 接口的全部 **33 个数据字段**（排除箭头函数形式的
action），逐个统计它在 `src/` 下、store 之外的读取点。

> 纪律：不能只看 store 自己的 `set`/初值行——那些是「写」。要找的是
> 「store 之外真正读它的地方」。零外部读 = 死状态。

### 结果

**33 个字段里只有 1 个零外部读取**：

| 字段 | 外部读取点数 | store 内出现位置 |
|---|---|---|
| `generations` | **0** | 仅 L140 声明、L646 初值 `[]` |

`startGeneration` 只写 `currentGeneration`；生成完成时记录直接丢失。
`generations` 在 `src/` 零引用、在 `scripts/` 零引用（`docs/` 的命中全是
别的上下文的行文或本项目自己的待办记录）。

### 为什么删而不是留着

留着它等于用注释承诺一个「生成任务列表」功能——那是对下一个维护者的
**文档性谎言**。真正要不要「生成历史」是产品决定，源站未采样，**不在这里发明**。

删完后重跑普查工具，输出已是「零外部读取字段：无」。

> **别把这个工具直接当门禁用**：它只看数据字段、不看 action；且「零外部读」
> 对「只在 store 内部读」的字段（如 `nodeClipboard`）会误报。真要门禁化，
> 得先处理这两类误报，否则就是个假绿制造机。

### 工具本身的两个误报类（用同一工具扫 jimengStore 时现形并修掉）

把工具泛化成可指定任意 store 后，扫 `jimengStore` 一开始报了 4 个「死状态」——
**4 个全是误报**：

| 误报 | 真相 | 修法 |
|---|---|---|
| `trimmedDuration` / `startOffset` | 是 `applyTrim: (\n id: string,\n trimmedDuration: number,\n)` 的**多行函数参数**，被单行正则误当成字段 | 跟踪括号深度，只把**深度 0** 的行当字段候选 |
| `groupColors` / `groupNames` | **有读** —— `JimengGroupFrames.tsx:69` 用 `const { nodes, groupNames, groupColors } = useJimengStore.getState()` **解构**读的 | 证据分两层：A=属性访问 `.name`（强）、B=与 store 同行出现的裸标识符（解构等）。两层都为 0 才算候选；只被 B 命中的单独标为「活着，别当死状态」 |

第二类里还藏了一个更隐蔽的 bug：hook 真名是 `useJimengStore`，文件名是
`jimengStore`，而 `\bjimengStore\b` **永远匹配不到** `useJimengStore`
（`use` 与 `Jimeng` 之间没有词边界）。

> 这个工具的假阳性方向是「把活字段判成死的」——那是**会诱导人删掉在用代码的
> 危险方向**。所以 hook 匹配刻意用**无词边界的大小写不敏感子串**，宁可多算。

修完后：frameosStore 零死字段（batch349 删除后的基线），
jimengStore 零死字段（`groupColors`/`groupNames` 被正确标为「只被解构读取」）。
**两个 store 扫完，没有更多死状态。**

---

## 验证

`scripts/verify-frameos-batch349.py` —— 9 项检查，0 诊断。

1. `store:generations-field-removed` —— 死状态确已删除
2. `setup:generate-button-present` —— 主面板真的渲染出了（防假绿前提）
3. `r1:flow-started` —— 生成按钮变 disabled，**流程真的跑起来了**
   （否则「只有 1 条」可能是因为压根没跑到完成分支）
4. `r1:one-done-event` / `r1:one-done-dom-toast` —— **恰好 1 条**（原为 11）
5. `r2:*` —— 第二次生成同样恰好 1 条（闩锁随生成重置）

### 关于把 mock 时钟压到 2 秒

**机制与时长无关**：重复次数只取决于「`p>=100` 之后还剩几个 50ms tick」，
即恒为 500ms 窗口 ≈ 11 次。所以验证器把 `durationMs` 压到 2 秒，
运行时长从 ~35 秒降到 ~10 秒。变异测试在 2 秒时钟下**同样复现出 11 条**，
反过来印证了这个论证；真实 30 秒时长的证据保留在探针的 `runtime-audit.json` 里。

---

## 变异测试（两次，两处都确认验证器会红）

| 变异 | 验证器输出 |
|---|---|
| 去掉闩锁 + 去掉停表（= 修复前行为） | `r1:one-done-event got=11` + 11 条同文 toast |
| 把 `generations: Generation[]` 加回 store | `store:generations-field-removed has=True` |

### 变异测试自身的坑（值得记）

第一次变异我只去掉了闩锁、**却保留了 `clearInterval`** —— interval 照样停，
缺陷根本没被恢复，**验证器照常通过**。

> 也就是说：一次「变异测试通过」毫无意义，除非先确认变异真的把被测性质
> 移除了。变异不到位比不做变异更危险，因为它给的是虚假的信心。
> 这次是靠「报错信息里的数字必须等于缺陷原文的 11」才发现的——
> 如果我只看到「PASS」，就会把这批的验证证据当成废纸。

---

## 过程中踩到的一个**探针自身**的坑

第二轮断言数出 2 条，排查后确认是**测量脚手架造的缺陷**，不是产品回归：
`INSTALL_SPY` 每轮都调一次 `addEventListener` 且不清旧的，第一轮的监听器继续存活，
一次派发被两个监听器各推一遍。

修法：监听器只装一次，用游标切分事件数组。

> 这已经是本会话第四次「先看失败在哪一步」救下了一次误改应用代码
> （前三次：batch346 探针坐标失效、batch348 探针复用已有节点、Playwright `position` 笔误）。

---

## 顺带记录（未修，非缺陷）

- **`toggleDebugMode` 零调用 → `FrameosNodeEditPanel` 永远渲染不出来。**
  `isDebugMode` 初值 `false`，而 `toggleDebugMode` 全仓零调用，于是
  `FrameosNodeEditPanel` 的守卫 `if (!isDebugMode || !selectedNode) return null`
  **永远不可满足**（组件已挂在 `page.tsx:745`，import 与 tsc 都干净）。
  结构和 batch348 的 `paneMenuAt` 一模一样：状态与守卫都对，**缺的是入口那一半**。

  **但结论是「有据可查的有意状态」，不是缺陷，所以不改。** 依据是我们自己的
  设计文档 `docs/research/frameos/IMPLEMENTATION.md` §2.5：

  > `FrameosNodeEditPanel`（节点 ID / 坐标 / 参数表单 / 快捷操作）**不是**
  > FrameOS 原站有的功能。是我加的开发者调试便利。**默认隐藏**。

  它是克隆自带的开发期产物，源站没有。补一个右下角橙色 `DEBUG` 按钮
  （`BEHAVIORS.md:24` 里确实写了这么一行）等于是**往界面上加一个源站没有的
  元素，让克隆离源站更远**。这与 batch348 的 `paneMenuAt` 有本质区别：
  那个是补上源站承诺的菜单（更忠实），这个是补上一个源站没有的按钮（更不忠实）。

  记录在此，是为了防止以后有人（包括我）把它当缺陷「修」掉。
  真要处理，那是「删掉调试代码」这个产品决定，`IMPLEMENTATION.md` §2.5 已经
  写好了三步删法，不该由一个缺陷批次顺手做掉。

- **生成流程在 demo 首屏完全不可达**：7 个 fixture 节点全是 text 或带 `imageUrl` 的
  image/video，`FrameosPromptEditor` 对它们一律 return null。必须先加一个
  「无媒体内容的生成节点」才够得着。
  这是 fixture 的性质，不是缺陷——但它意味着**生成流程在 demo 首屏完全不可达**，
  任何验证器想碰它都得自己先造节点（Batch 349 验证器与探针都这么做）。
- **Batch 347 的可寻址性门禁普查不到生成按钮**：`FrameosGenerationOverlay`
  整个没有任何 `data-frameos-*` 钩子，门禁在三种 UI 态里都没触达过它。
  门禁的边界是「**普查所及范围内**零盲区」，不是「全 app 零盲区」。

## 保真度差距

无新增。`generations` 的删除是 CLONE_DECISION，不冒充源站对齐声明。

## 源站阻塞

`frameos.cn` 人机验证仍不可通过（用户手动点击亦失败），本批全部结论均为
克隆侧运行时证据，无一条源站采样。
