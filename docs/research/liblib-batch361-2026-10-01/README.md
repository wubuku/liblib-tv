# Batch 361 — liblib 验证器并发 runner

## 为什么要做这个

liblib 线到本批已有 **306 个** `verify-liblib-*.py`, 但没有统一入口。此前每批
回归只能手动逐个定向跑, 单批 20~40 分钟, 长期是这条线最耗时的环节 —— 拖慢的
不是写代码, 是**验证**。

frameos 线早就有 `run-frameos-verifiers.sh`(93 个), 但它是纯串行的。306 个
验证器串行约需 4 小时。

## 测量方法本身先验证过

**先验证测量方法, 再用它下结论** —— 并发 runner 有个天然的风险: 并发会制造
**假失败**(CPU/内存争抢、dev server 编译抢锁), 而这些假失败会被误读成真回归。
所以没有直接开跑, 而是先建立基线:

| 跑法 | 样本 | 结果 | 耗时 |
|---|---|---|---|
| 串行 `-j 1` | 10 个 | **10/10 PASS** | ~5 min |
| 并发 `-j 4` | 同 10 个 | 10/10 PASS | — |
| 并发 `-j 8` | 同 10 个 | 10/10 PASS | 43 s |
| 并发 `-j 12` | 同 10 个 | 10/10 PASS | 40 s |
| 并发 `-j 8` | 30 个跨批次 | 见下 | — |

**判定与串行基线逐条一致, 零新增假失败**, 并发才被认为可用。

`279`/`300` 在样本里但仓库无对应脚本(它们是 frameos 线批次), runner 会自动
跳过并计入总数 —— 不静默丢, 也不假装跑过。

### 压测样本怎么选的

不能只挑自己新写的、跑得快的门禁 —— 那样测的是「我写的东西在并发下没问题」,
不是「这个 runner 在并发下没问题」。所以按 `sort -V` 每隔 10 个取一个
(`6 16 26 37 47 58 ...`), 跨新旧批次。

### 并发 8 与 12 几乎无差(43s vs 40s)

因为 10 个样本在 `-j 8` 下已全部并行铺开, 瓶颈已经不在并发度上。
**没有把「更快」当成目标去继续加并发** —— 目标是「不制造假失败」,
达到后继续加只会提高翻车概率。默认取 4, 想快自己 `-j 8`。

## runner 自带的三道保护

1. **dev server 探活前置**。306 个验证器在服务器挂了时会全部报连接错误,
   刷屏且零信息量。现在先 `curl` 探活, 不通直接 `exit 2` 并提示怎么起。
   > 实战验证过: 测并发 12 时 dev server 恰好被别人重启, runner 0.02 秒就 FATAL
   > 退出, 而不是把 306 个超时错误糊你一脸。
2. **失败自动重试一次**(与 frameos runner 同策)。并发负载下的偶发失败隔离;
   隔离后仍红才算真回归。**已在基线里见过它干活**。
3. **按批号取日志**。每个验证器一个独立 python 进程, 输出落
   `$TMPDIR/liblib-verifiers.XXXX/<批次号>.log`, 只有失败时保留目录。
   截图落盘路径都带 batch 号(核查过 305 个), 并行不会互相覆盖。

## `--changed`: 两类命中分开报

`--changed` 挑「改动可能影响到的门禁」。但**提到 ≠ 覆盖** —— 门禁 docstring 常在
解释原因时提到无关路径(例如 batch360 写「跳过导演台, 那条线有并行 session 在改」,
于是 `src/components/director/*` 出现在它的 docstring 里)。若只按「docstring 提过
这个文件」判定, 一旦**别人**在改导演台, 就会有 35 个门禁被拖去回归, 与我的改动无关。

所以输出**必须分类**, 否则使用者分不清哪些是自己惹的:

```
direct (code I changed): 358 359 360
collateral (shared files, incl. others' WIP): 35 36 40 41 46 50 68 93 ...
```

`collateral` 是超集(宁可多跑不可漏跑), 但**明确标出来**。

另外只认 `src/` 与 `scripts/` 的改动: `docs/` 下几百张截图和 md 不会驱动任何门禁,
计入只会白跑。

## 压测抓到 3 个失败, 三种完全不同的性质

30 样本 @ 并发 8 → **27 passed, 3 failed**(重试后仍红)。逐个看失败在哪一步,
结论是三种性质, 处理方式也三种不同:

| 批次 | 失败表象 | 性质 | 处置 |
|---|---|---|---|
| **69** | `FileNotFoundError: 'node'` | **runner 自己的缺陷** | 已修 |
| **89** | 首跑红, 重试绿 | 并发偶发 | 重试机制正确工作 |
| **37 / 601** | 断言红 / 样式不符 | **他人 WIP 的构建中间态** | 等对方保存后复跑, 全绿 |

### 69: 10 个门禁悄悄依赖 node —— 元缺陷, 改 runner

`batch69` 报 `FileNotFoundError: 'node'`, 隔离跑加 node PATH 即 PASS。
**不是回归, 是 runner 没准备环境**: 有 **10 个** liblib 门禁
(`10/51/52/53/54/60/62/69/172/173/185`) 会 `subprocess` 调 `node` 跑配套 `.mjs`
静态门禁, 而裸 bash 里 `node` 不在 PATH。

> 属「元缺陷踩到即变门禁」: 不是某个门禁的问题, 是**一批验证器悄悄共享同一个
> 外部运行时**, 而这个依赖在任何单个门禁里都看不出来。修法不是逐个门禁加 PATH,
> 是 runner 统一兜住 —— 找不到 node 就 `exit 2` 并说明, **早失败好过 10 个
> 门禁各报一次一模一样的 FileNotFoundError**。

**修完还是红的 —— 而且症状变得更难查。** 第一版兜底这么写:

```sh
for cand in "$HOME/.nvm/versions/node"/*/bin; do
  if [ -x "$cand/node" ]; then PATH="$cand:$PATH"; break; fi   # 取 glob 的第一个
done
```

glob 的第一个是 **v12.18.4**。`FileNotFoundError` 消失了, 换成
`exit status 9` —— node 存在但**不支持** `--experimental-strip-types`。
从「找不到 node」变成「node 存在却跑不动」, 搜索方向完全不同, 更难查。
改成按版本号取**最新**的, 裸 PATH 下复跑 batch69 → **PASS**。

> **兜底代码自己也会挑错版本。** 这台机器有 13 个 node 版本, glob 第一个是最旧的。
> 修法本身引入了一个比原缺陷更难诊断的新缺陷 —— 而它长得像「门禁真的坏了」。


### 89: 「日志说 passed 但判 FAIL」本身不是 bug

第一次看到以为统计逻辑错了。隔离复跑 `exit=0` —— 它是并发下的偶发失败,
重试机制正确工作。**日志内容与退出码不一致不代表退出码错了**,
先复现退出码再下结论。

### 601: 我自己的一次测量错误, 门禁是对的

隔离复跑 batch601 时我用 `... | tail -3; echo exit=$?` 取退出码, 拿到 `exit=0`,
一度以为「这批门禁报失败却不返回非零」—— 若真是这样, runner 会静默放过所有
这类失败, 是个比 batch 601 本身严重得多的问题。

**实际是 `| tail` 吃掉了上游退出码。** 不接管道重跑: `REAL exit=1`。
batch601 结尾**有** `raise SystemExit(1)`, 门禁完全正常。

> 这是本批最值得记的一条: 结论「某工具报了失败却不报错」听起来非常严重,
> 差点就写进文档。**先验证测量方法本身** —— 报出「某个门禁有致命缺陷」之前,
> 得先确认自己测退出码的方式是对的。差点把测量工具的缺陷当成产品的缺陷。

### 37 / 601: 我先归错了因, 复跑后全部改判

第一次看到这两条红, 我归因成「他人 director WIP / 已被他人提交的改动」——
依据是它们都落在 `src/components/director/*`。**这个归因错了。**

真正的日志证据在 37 的重试输出里:

```
console:error: Export JimengSharePanel doesn't exist in target module
  The module has no exports at all.
```

`src/components/jimeng/JimengSharePanel.tsx` 是**他人未提交 WIP**, 且在我跑批的
那个瞬间正处于「文件被清空到无导出」的中间态 —— **整个 dev server 编译失败**,
于是所有依赖编译产物状态的断言全崩。37 断的是时间轴 `currentTime`(其实是在
诊断 console error), 601 断的是 auto-keyframe 背景色, 都只是被同一个编译失败
的连带受害者, 跟导演台没关系。

等对方保存文件后隔离复跑:

| 批次 | 复跑结果 |
|---|---|
| 37 | `exit=0` — `Batch 37 ... verification passed` |
| 601 | `exit=0` |
| 89 | `exit=0` |

**三个全绿。** 没有真回归。

> **教训: 归因要有一手证据, 不能只靠「失败发生在哪个目录」。**
> 我看到失败堆栈里是 `director/*`, 就顺势归因到导演台 —— 但日志里真正的
> 第一条错误是 jimeng 的编译失败, 只是它出现在 director 门禁的诊断输出里。
> **「在哪看到」不等于「因什么而红」。**
> 正确顺序是: 先找日志里**最早**的那条错误, 再谈归属。


## 工具自身踩的三个坑

1. **第一版扫描慢到不可用**: 对 306 个门禁逐个 `grep` docstring, 光筛选就 >120 秒
   还出不来。改为一次性抓出所有 `src/` 引用排序去重, 再求交 —— **306 次进程调用
   变 1 次**, 秒级出结果。
2. **第一版把「命中原因」算错了**: 想去区分「我改的」还是「别人 WIP 的」, 结果又
   写了个每次都成立的判断(两个来源是同一份 diff), 等于没分类。**分类字段必须能
   真的分出两类**, 否则就是装饰。简化后 `direct`/`collateral` 仍有意义 —— 靠
   「脚本自身被改」这个硬信号区分。
3. **「没跑成」被当成了「跑过了」**: 统计里第一版是
   `[ -f "$LOG_DIR/$b.log" ] || continue` —— 进程被 OOM kill 或被手动中断时不会留下
   日志, 于是那个门禁**从统计里彻底消失**: 说「跑了 30 个」但只列出 29 个结果,
   少掉的那个既没 PASS 也没 FAIL。
   > 门禁**没跑成**绝不能等于**通过**。判据不成立时宁可报红。
   现在单列 `MISSING (never produced output, e.g. killed)`, 并计入失败。

   同处把 `grep -c "^PASS $b\$" | cat` 换成 `grep -qxF "PASS $b"` 直接读
   `results`: 前者要起一次 `cat` 子进程, 后者直接锚定整行。**双向验证过边界** ——
   `PASS 4` 不会误匹配 `PASS 41` / `PASS 4b`。


## 交付

`scripts/run-liblib-verifiers.sh`, 支持 `-j` / `-r` / `--list` / `--changed` /
指定批号。与 frameos runner 同风格(同 discover、同 retry、同汇总口径)。

**这是工具批, 不改产品代码** —— 唯一产出是回归成本的下降。

## 意外收获: 这批让 batch352 的一个注释变成了共识

建 runner 时发现 `verify-frameos-batch352.py` 的 `find_node()` 里有这么一段:

> 踩过的坑: 全量套件 `run-frameos-verifiers.sh` 的运行环境里 **node 不在 PATH**
> (它只用 pyenv 的 python, 不导出 nvm 的 node 路径), 于是本验证器在套件里
> 直接 `FileNotFoundError: 'node'` 崩掉 —— 单独手跑能过、进门禁就挂。
> **门禁必须在最贫瘠的环境里也能跑**

而我在 batch361 压测里撞到的是**同一类问题的另一半**: 10 个 liblib 门禁会
subprocess 调 node, 裸 bash 里 node 不在 PATH。batch352 是「单个门禁自己兜底」,
batch361 是「runner 统一兜底」—— 现在 liblib 线有了和 frameos 线对等的保护。

## 另一个意外收获: 「死状态」不能删, 因为它被当成阳性对照

原计划 batch362 清理 `uiStore` 的 5 个零读取面板开关 + `toggleUserMenu`(全部确认
无人调用)。**动手前查了门禁引用, 结果动不了:**

`verify-frameos-batch352.py` 有一条**反向断言**:

```python
EXPECTED_DEAD = ("src/store/uiStore.ts", "UIState",
                 ["isToolboxPanelOpen", "isMaterialPanelOpen",
                  "isCharacterPanelOpen", "isHistoryPanelOpen"])
...
missed = [f for f in expected_dead if f not in r["dead"]]
check("still-detects-real-dead-state", not missed, ...)
```

它拿这 4 个字段当**普查工具的阳性对照** —— 证明工具仍能报出真死状态,
不是靠「啥都不报」蒙混过关(与本线「过滤器必须双向验证」同源)。

**删掉它们 = batch352 变红, 且会毁掉一个必要的自证能力。** 计划当场作废。
> 「死代码就该删」是对的直觉, 但要先问: **有没有人拿它当探针的标尺?**
> 看起来没用的东西, 可能是唯一那个「已知有病」的对照样本。
> 这也再次说明为何**动手前先查门禁引用**。

顺带确认了两件事(都属于「差点归错因」):
- `isUserMenuOpen` 看似死, 实则被 `page.tsx` 用 `useUIStore.getState()` 整个快照
  传给 `resolveLibTVBlockingForegroundSurface` —— 字段真实存在且被读。
  中间我一度认定「`LibTVForegroundSurfaceSnapshot` 没人构造, 该分支永假」,
  只因 grep 不到构造点就下了结论, 查调用方才发现整个 store 就是那个快照。
- `CameraConfigDialog` / `CameraMovementDialog`(554 行)无人渲染, 且其 spec 说由
  `ImageEditPanel` 的「摄像机」按钮触发 —— 但**那个按钮根本不存在**,
  全项目「摄像机」字样都在 `director/*`(跨线地盘), 且导演台已有实装的
  `DirectorCameraMotionTab.tsx`(14KB) 覆盖同一功能。
  **不删**: 跨线代码只记录不动手, 何况它可能是导演台在途工作的素材。

