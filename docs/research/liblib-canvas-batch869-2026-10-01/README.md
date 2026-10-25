# batch 869 —— 「当前帧关键帧」的命中窗口：clone 1e-3 vs 源站 ±0.05s（**差 50 倍**）

> ★ 本批一句话：★ 源站那枚「当前帧有关键帧 / 当前帧无关键帧」的按钮，
> ★ **命中窗口是 ±0.05 秒**（★ 源站 chunk `cZ` 逐字）⟹ ⟹ ⟹ ⟹ ⇒ ★
> ★ 而 clone 用的是 **1 毫秒** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 于是播头在关键帧后 **40ms** 时
> ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ **两边决策相反**：★ 源站说「有」（点它＝**移除**那一枚）、
> ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ clone 说「无」（点它＝**再加一枚**）⟹ ⟹ ⟹ ⟹ ⇒ ★
> ★ 而且「上一关键帧」在源站是 **disabled**、⟹ ⟹ ⟹ ⟹ ⇒ ★ clone 却给它点亮了。
> ★ ⇒ 本批把窗口改成**从源站原文解析出来的数**、⟹ ⟹ ⟹ ⟹ ⇒ ★ 并把
> ★ 「命中窗口」与「同时刻 upsert 容差」**彻底分开**。

---

## 1. 靶子与结论（★ 先说结论）

| 项 | 结论 |
| --- | --- |
| 靶子 | 导演台时间轴与检查器里「当前帧关键帧」的**命中窗口** |
| 源站逐字 | ±**0.05s**（★ 三处：命中／上一／下一）⟹ 见 `raw/source-869-cz-toggle.txt` |
| clone 原状 | ±**0.001s**（1 毫秒）⟹ ⟹ ⟹ ⟹ ⇒ ★ **差 50 倍** |
| 本批改动 | 新建 `src/components/director/directorKeyframeWindow.ts` ⟹ ⟹ ⟹ ⟹ ⇒ ★ 命中窗口收成**一个出处** |
| 运行时读数 | **13 条判据 0 失败**（★ `raw/keyframe-window-869.json`） |
| 门禁 | `scripts/verify-liblib-batch869.py` ⟹ ⟹ ⟹ ⟹ ⇒ ★ **20 条判据 0 失败** |
| 负控 | **8 条负控 0 失败**（★ 含**运行时负控**：★ 改回 1e-3 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 探针打红 **6** 条） |
| ★ 撤回 | ★ 本批**一度**把工具条「添加关键帧」改成切换语义 ⟹ ⟹ ⟹ ⟹ ⇒ ★ **方向错了、已撤回**（★ 见 §6） |

---

## 2. 源站逐字证据（★ 判据的期望值全部**只从这里**来）

### 2.1 `cZ`（★ `raw/source-869-cz-toggle.txt`）

★ 源站 chunk `0fmehki05gkzw.js.js` 的轨道行三键，逐字：

```js
m = function(e,t){let r=cd(e);for(let e=r.length-1;e>=0;e-=1){let n=r[e];
     if(n&&n.time<t-.05)return n}return null}(e.markers,h),      // ← 上一关键帧
f = (l=e.markers, cd(l).find(e=>.05>=Math.abs(e.time-h))??null),  // ← 当前帧命中 ±0.05s
x = (d=e.markers, cd(d).find(e=>e.time>h+.05)??null),              // ← 下一关键帧
v = !!f,
b = p(f?"canvas:directorTimelineCurrentKeyframeVisible"
        :"canvas:directorTimelineCurrentKeyframeHidden"),
// 轨道行中键：
"aria-label":b, "aria-pressed":!!f,
onClick: o({target:y, trackId:e.id, time:f?.time??h,
            propertyKey:e.propertyKey, action:f?"remove":"add"})
// 上一键 disabled:!m   下一键 disabled:!x
```

★ ⇒ 三处用**同一个 0.05 秒**；⟹ ⟹ ⟹ ⟹ ⇒ ★ 命中时 `action` ＝ **remove**，
⟹ ⟹ ⟹ ⟹ ⇒ ★ 未命中时 ＝ **add**、且记在**播放头**那一刻（`f?.time??h`）。

### 2.2 i18n 逐字（★ `raw/source-869-i18n-dictionary.txt`）

```
"directorTimelineCurrentKeyframeVisible":"当前帧有关键帧"
"directorTimelineCurrentKeyframeHidden":"当前帧无关键帧"
```

### 2.3 batch 36 逐字规格（★ `raw/source-869-batch36-spec.md`）

```
◆ 添加关键帧 captures the selected track object's complete current value;
same-time add replaces the existing keyframe value;
previous/next searches all keyframes and skips the current timestamp using a small epsilon
```

---

## 3. ★★ 本批改了什么（★ 4 处）

| # | 文件 | 改动 | 出处 |
| --- | --- | --- | --- |
| 改动 1 | `src/components/director/directorKeyframeWindow.ts`（**新建**） | `DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW = 0.05`、`DIRECTOR_KEYFRAME_EPSILON = 1e-3`、`directorKeyframeHit/Earlier/Later` | `cZ` 逐字 |
| 改动 2 | `src/components/director/DirectorTimeline.tsx` | 轨道行三键的命中／取点窗口 ⟹ 改用共享窗口；工具条按钮**已还原**成 upsert | `cZ` ＋ batch36 规格 |
| 改动 3 | `src/components/director/DirectorInspector.tsx` | 两处 `< 0.001` ⟹ `directorKeyframeHit(...)` | `cZ` 逐字 |
| 改动 4 | `src/store/directorStore.ts` | `upsertTrackKeyframe`／`upsertGroupTrackKeyframe` 的字面量 `0.001` ⟹ 具名常量 `DIRECTOR_KEYFRAME_EPSILON` | `SOURCE_ANALYSIS.md` §23.3 |

### 3.1 ★★ 两个容差**必须分开**

| 容差 | 值 | 语义 | 出处 |
| --- | --- | --- | --- |
| `DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW` | `0.05` | 「**当前帧**关键帧」的**命中**窗口 | `cZ`：`markers.find(e => .05 >= Math.abs(e.time - h))` |
| `DIRECTOR_KEYFRAME_EPSILON` | `0.001` | 「**同一时刻** upsert」的容差 | `docs/research/beeftv-canvas-2026-09-27/SOURCE_ANALYSIS.md` §23.3 |

★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 混用会出现「以为在命中、其实在 upsert」的账 ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 所以两者**各有名字、各写出处**，⟹ ⟹ ⟹ ⟹ ⇒ ★ 门禁里也各有一条判据。

---

## 4. ★ 本批门禁的判据构成（`scripts/verify-liblib-batch869.py`，**20 条**）

| 组 | 判据 | 读的是哪个量 |
| --- | --- | --- |
| S1–S4 | 源站证据在库 | `cZ` 逐字／i18n 逐字／batch36 逐字／更正记录 |
| S5 | ★ 共享窗口常量 **等于从 `cZ` 解析出的数** | `DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW` |
| S6 | ★ 命中窗口 **≠** upsert 容差 | 两个常量的数值 |
| S7 | ★ 命中只有一个出处 | 时间轴与检查器**都** import `directorKeyframeHit` |
| S8 | ★ UI 两处不再有裸的 1e-3 命中容差 | **剥注释后**的 `0.001`／`1e-3` |
| S9 | ★ 工具条「添加关键帧」**仍是 upsert** | 工具条块里有没有 `addTimelineKeyframe` |
| S10–S12 | ★ 运行时读数在库且**自洽** | `raw/keyframe-window-869.json` |
| S13 | ★ 负控证据在库（含运行时负控） | `raw/negative-audit-869.json` |
| S14 | ★ 866 门禁**动态解析**在用清单 | `866.py` 里有没有 `resolve_live_regress` |
| S15 | ★ 回归清单**只增不减** | `regress869.py` ⊇ `regress868.py` |

★ ★ **期望值不许手打**：★ S5 的期望值是**从 `cZ` 原文正则解析出来的**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以改坏源码常量、或改坏源站证据，**两边都会红**。
★ ★ **不写死判据条数**：★ S10 用的是「非空 ∧ 每条为真 ∧ 自洽」
⟹ ⟹ ⟹ ⟹ ⇒ ★ 而不是「必须恰好 13 条」（★ 写死的个数是老门禁「旧前提」的形状）。

---

## 5. ★ 运行时探针（`probes/keyframe_window869.py`，**13 条判据**）

| # | 判据 |
| --- | --- |
| W0a | ★ 轨道行中键**读得到** aria-label（★ 探针可读性自检） |
| W0b | ★ 挪动对象后**读回**的 transform **确实变了**（★ 否则 W9 是空判） |
| W1 | ★ 播头在关键帧 **+0.04s** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 中键 aria-label 逐字＝「当前帧有关键帧」 |
| W2 | ★ 同处 `aria-pressed`＝`true` |
| W3 | ★ 同处「上一关键帧」**disabled** |
| W7 | ★ 检查器那枚开关在 +0.04s 处逐字＝「当前帧有关键帧」、state＝`on` |
| W5/W5b | ★ 播头在 **+0.2s** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 逐字＝「当前帧无关键帧」、`aria-pressed`＝`false` |
| W4 | ★ 窗口内点中键 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那枚**消失**（数量 −1） |
| W4b | ★ 播头**正好**落在关键帧时刻 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 点它 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那枚**消失**（★ 源站逐字 `action`＝remove） |
| W6 | ★ 窗口外点中键 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 真的**多出一枚**（数量 +1） |
| W8 | ★ 检查器开关在 +0.04s 处点击 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那枚**消失**（数量 −1） |
| W9 | ★ 工具条「添加关键帧」＝**取当前值覆盖**：★ 数量不变、时间列表不变、但那枚的 value 变成对象当前变换 |

### 5.1 ★★ 探针本身踩的坑（★ 两条，都是"判据自己要先自检"）

★ **坑 ①：判据之间互相污染。** ★ 第一版探针**没有固定夹具** ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 于是「点中键」那一步会在当前帧**新增**一枚 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而后面的
★ 「检查器开关」读到的是**那枚新增的** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 于是**检查器那两条判据
★ 与窗口无关**（★ 变异成 1e-3 之后它们照样绿）⟹ ⟹ ⟹ ⟹ ⇒ ★ **证不出**检查器
★ 那枚开关到底用哪个窗口。
★ ⇒ **修法**：★ 加**固定夹具**（★ 每一步都把轨道关键帧**重置成同一份已知集合**）
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 并把**只读**判据全部放到**任何点击之前**。

★ **坑 ②：负控的变异压根没落到文件上。** ★ 负控脚本的运行时分支
★ **漏了 `mutate()`** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 于是探针跑的是**未变异的代码** ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 必然「全绿」⟹ ⟹ ⟹ ⟹ ⇒ ★ 而且**表面上完全看不出异常**（★ 退出码 0、★ 输出干净）。
★ ⇒ **修法**：★ 运行时分支也必须先 `mutate()` ⟹ ⟹ ⟹ ⟹ ⇒ ★ 并在负控里
★ 加一条**读回自检**（★ 确认文件字节真的变了）。

### 5.2 ★★ 负控（`probes/neg869.py`，**8 条**）

★ ★★ 归因方式＝**红灯集合差分** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 不是「跑出来是红就算」
（★ 门禁**本来就有几条红**⟹ ⟹ ⟹ ⟹ ⇒ ★ 「恒红」与「因为变异而红」长得一样）。
★ 判据是：★ 目标判据在**变异前**是绿的、⟹ ⟹ ⟹ ⟹ ⇒ ★ 在**变异后**红了。

| # | 类别 | 变异 | 被测判据 |
| --- | --- | --- | --- |
| N1 | 源码 | 命中窗口常量 `0.05` → `0.001` | S5 |
| N2 | 源码 | upsert 容差 `1e-3` → `0.05` | S6 |
| N3 | 源码 | 时间轴中键改回裸的 `Math.abs(...) <= 0.001` | S8 |
| N4 | 源码 | 工具条「添加关键帧」改回切换语义 | S9 |
| N5 | 源码 | `866.py` 的动态解析改回写死清单 | S14 |
| N6 | 证据 | 把运行时读数文件挪走 | S10 |
| N7 | 证据 | 把读数里 W1 的 `通过` 改成 `false` | S10 |
| N8 | ★运行时 | 把命中窗口改回 `0.001` ⟹ ⟹ ⟹ ⟹ ⇒ ★ **跑探针** | 探针 13 条 |

★ N8 的读数：★ 探针基线 **0 条失败** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 变异后 **6 条**打红
★ （W1／W2／W3／W7／W4／W8）⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ **这 6 条真的在测那个窗口**。

★ 每条负控都**自声明改哪个文件** ＋ **字节级复原** ＋ sha 自检 ＋
★ **跨文件污染守卫**（★ 结束时全量比对 sha ⟹ ⟹ ⟹ ⟹ ⇒ ★ 本批读数「干净」）。

---

## 6. ★★ 前向更正（★ **撤回**了一个走错的方向）

★ 本批**一度**把工具条那枚「添加关键帧」改成「有则移除、无则添加」的**切换**语义
⟹ ⟹ ⟹ ⟹ ⇒ ★ 并打算改写门禁 `700`。
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ **方向错了，已撤回**：★ 源站 batch 36 逐字规格（§2.3）写的是
★ 「**取当前值、同时刻覆盖**」⟹ ⟹ ⟹ ⟹ ⇒ ★ clone 原有的
★ `addTimelineKeyframe()` → `upsertTrackKeyframe` **本来就是源站语义**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 「播放头处已有关键帧时点击**数量不变**」⟹ ⟹ ⟹ ⟹ ⇒ ★ **不是缺陷**、
★ 是**幂等** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 门禁 `700` 的判断**是对的** ⟹ ⟹ ⟹ ⟹ ⇒ ★ **本批不动 700**。

★ 另一处更正：「源站没有『添加关键帧』」⟹ ⟹ ⟹ ⟹ ⇒ ★ **是查法错**
（★ 当时搜的缓存目录里**没有** i18n 字典 chunk）⟹ ⟹ ⟹ ⟹ ⇒ ★ 完整记录见
★ `raw/source-869-correction.md`。

---

## 7. ★ 顺带修好的：`866` 门禁（★ 回归里那条新红的根因）

★ 全量回归 283 条 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 红 71 条（★ 旧账 70 ＋ **新红 1**＝`866.py`）。
★ 根因：`866` 把「在用回归清单」**写死**成 `probes/regress866.py`（★ 177 条历史快照）
⟹ ⟹ ⟹ ⟹ ⇒ ★ batch 868 提交了新的 `verify-liblib-batch868.py`（★ 它碰被跟踪源文件）
⟹ ⟹ ⟹ ⟹ ⇒ ★ 缺口＝`['868.py']`。

★ ★★ **受控对照**（★ 证明归因、不是猜）：
1. 临时移走 `scripts/verify-liblib-batch868.py` ⟹ ⟹ ⟹ ⟹ ⇒ ★ `866` **立刻 18 判据 0 失败**；
2. 复原后 sha256 **逐字一致**（`a3fddae3b675c8043f0125a5aa57d4a093f099d0e9dbe1905b8e3dc38822704a`）✔

★ ⇒ 归因＝**batch 868 提交引入**、⟹ ⟹ ⟹ ⟹ ⇒ ★ **不是 869 引入**。
★ 修法＝`resolve_live_regress()`（★ 扫 `docs/research/liblib-canvas-batch*/probes/regress*.py`
★ 取**批次号最大**的那份）＋ 新增两条结构性判据
★ （★ `the-live-regression-list-is-the-newest-one`、
★ `the-regression-list-never-shrinks`）⟹ ⟹ ⟹ ⟹ ⇒ ★ 复跑 **20 判据 0 失败**。

---

## 8. ★ 用户可达

★ 本批**改的是**「当前帧关键帧」的判定 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 用户可交互面**没变**，
★ 但**行为**变了 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 路径与 batch 865／868 相同：

```
http://localhost:4317/  ⟹  hover 导演台卡片 ⟹  「打开导演台 →」
   ⟹  选中一个对象 ⟹  底部时间轴出现轨道行
   ⟹  轨道行中间那枚菱形按钮 ⟹  它现在的判定窗口是 ±0.05 秒
```

★ ★★ **怎么自己验这个窗口**（★ 手测，★ 不用脚本）：
1. 选中一个**已经有关键帧**的轨道（★ 比如默认机位轨道）；
2. 把播放头**拖到那枚关键帧之后一点点**（★ 大约 **40 毫秒**级，
   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 肉眼几乎看不出差别）；
3. ⟹ ⟹ ⟹ ⟹ ⇒ ★ 轨道行中间那枚按钮此刻应显示「**当前帧有关键帧**」
   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 且它左边的「上一关键帧」是**灰的**（★ 源站逐字：`0 < 0.04-0.05` 不成立）；
4. ⟹ ⟹ ⟹ ⟹ ⇒ ★ 点它 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那枚关键帧会**消失**（★ 而不是多出一枚）。

★ ★ 自动化版：★ `probes/keyframe_window869.py`（★ 13 条判据）。

---

## 9. 产物索引

| 文件 | 内容 |
| --- | --- |
| `raw/source-869-cz-toggle.txt` | ★ 源站 chunk `cZ` **逐字**（★ 2204 字节） |
| `raw/source-869-i18n-dictionary.txt` | ★ 源站 i18n 字典**逐字**摘录（含 chunk 路径／sha256／偏移） |
| `raw/source-869-batch36-spec.md` | ★ 源站 batch 36 **逐字规格**摘录 |
| `raw/source-869-director-i18n-keys.json` | ★ 源站 **354** 个 director 词条键 |
| `raw/source-869-correction.md` | ★★ **更正记录**（★ 两处：查法错 ＋ 撤回的方向） |
| `raw/keyframe-window-869.json` | ★★ **运行时读数**（★ 13 条判据） |
| `raw/negative-audit-869.json` | ★★ **负控读数**（★ 8 条，含运行时负控） |
| `raw/gate-869.json` | ★ 门禁读数（★ 20 条判据） |
| `raw/audit-869.json` | ★ 门禁解析出的源站数值（★ 三处窗口／两个容差／aria 文案） |
| `raw/regression.json` | ★ 全量回归读数（★ 284 条） |
| `probes/keyframe_window869.py` | ★★ 运行时探针（★ 13 条判据） |
| `probes/neg869.py` | ★★ 负控（★ 8 条） |
| `probes/regress869.py` | ★ 回归清单（★ 284 条） |
| `probes/keyframe_toggle869.py` | ★★ **已作废**（★ 编码的是被撤回的方向 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 头部有 `SUPERSEDED` 横幅） |
| `scripts/verify-liblib-batch869.py` | ★★ 本批门禁（★ 20 条判据） |

---

## 10. ★ 未做的事（★ 明写，避免下批误以为已覆盖）

- ★ **门禁 `700` 没动**（★ 它把「添加关键帧」记成幂等控件 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那个判断**是对的**）；
- ★ **「上一／下一关键帧」的去点语义**没改（★ 源站是 `w(m)`／`w(x)` ⟹ ⟹ ⟹ ⟹ ⇒ ★
  clone 的实现本批未逐字复核）；
- ★ 源站 `cZ` 里 `cd()`（★ 排序函数）没逐字取到 ⟹ ⟹ ⟹ ⟹ ⇒ ★
  clone 的升序假设**未被源站原文直接证实**（★ 但与「上一＝最后、「下一」＝最先」一致）；
- ★ 导演台**其它**轨道的命中语义（★ `group`／`pose`）本批未逐条实测。
