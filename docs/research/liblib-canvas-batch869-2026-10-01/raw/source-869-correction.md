# Batch 869 · 更正记录（本批一度走错方向 ⟹ 留痕）

> ★ 纪律：★ 追加式文档**不可重写** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 更正只能**标注**、不能抹掉痕迹。
> ★ 本文件是 batch 869 的**更正记录**：★ 记录两处「一度判断错 / 一度查法错」的地方。

## 一、更正 ①：「源站没有『添加关键帧』」⟹ ⟹ ⟹ ⟹ ⇒ ★ **是查法错**，不是事实

★ 当时的结论：★ 源站 i18n 字典里**查不到** `directorAddKeyframe` ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 所以判断「源站没有『添加关键帧』这个功能」。

★ ★★ **真相**：★ 那是**查法错** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 三处 chunk 缓存的对照读数：

| 缓存目录 | chunk 数 | 「添加关键帧」字面命中 |
| --- | --- | --- |
| `/tmp/liblib_srcjs` | 161 | **1**（★ 含 i18n 字典 chunk） |
| `/tmp/liblib_srcjs_desk` | 162 | **1** |
| `/tmp/liblib_srcjs2` | 159 | **0** ⟹ ⟹ ⟹ ⟹ ⇒ ★ **该目录根本没有 i18n 字典 chunk** |

★ ⇒ 「0 命中」⟹ ⟹ ⟹ ⟹ ⇒ ★ 只是**那个目录里没有那份文件** ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 不是「源站没有这个功能」。★ 且仓库里
★ `docs/research/liblib-canvas-batch36-2026-08-26/SOURCE_EVIDENCE.md`
★ **早就逐字列着**「◆ 添加关键帧」。

★ ★★ **通式**：★ 「0 命中」可能是**查法错**（★ 搜的目录没那份文件）；
★ 「没列出来」≠「不存在」；★ 引用旧结论前必须先查它**有没有被后续证据推翻**。

## 二、更正 ②：★ 「把工具条『添加关键帧』改成切换语义」⟹ ⟹ ⟹ ⟹ ⇒ ★ **方向错了，已撤回**

★ 当时的改动：★ 把工具条那枚「添加关键帧」改成「**有则移除、无则添加**」的
★ 切换语义 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 并打算改写门禁 `700`（★ 它把该按钮记成「幂等控件」）。

★ ★★ **撤回理由（★ 源站 batch 36 逐字规格）**：
★ `docs/research/liblib-canvas-batch36-2026-08-26/DIRECTOR_TIMELINE.spec.md`：

```
◆ 添加关键帧 captures the selected track object's complete current value;
same-time add replaces the existing keyframe value;
previous/next searches all keyframes and skips the current timestamp using a small epsilon
```

★ ⇒ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 「添加关键帧」是**取当前值、同时刻覆盖既有值** ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ **不是**切换 ⟹ ⟹ ⟹ ⟹ ⇒ ★ clone 原有的 `addTimelineKeyframe()` →
★ `upsertTrackKeyframe` **本来就是源站语义** ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 「播放头处已有关键帧时点击**数量不变**」⟹ ⟹ ⟹ ⟹ ⇒ ★ **不是缺陷**、
★ 是**幂等** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 门禁 `700` 的判断**是对的** ⟹ ⟹ ⟹ ⟹ ⇒ ★ **本批不动 700**。

★ ⇒ 本批**真正改掉**的是**轨道行中键**（★ 源站 `cZ`）⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 它的**命中窗口**从 `1e-3` 改成源站逐字的 **±0.05s**（★ **差 50 倍**）。

## 三、本批改动对照表

| # | 文件 | 改动 | 源站逐字出处 |
| --- | --- | --- | --- |
| 1 | `src/components/director/directorKeyframeWindow.ts`（**新建**） | 导出 `DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW = 0.05`、`DIRECTOR_KEYFRAME_EPSILON = 1e-3` 与 `directorKeyframeHit/Earlier/Later` | 源站 chunk `cZ`（`raw/source-869-cz-toggle.txt`） |
| 2 | `src/components/director/DirectorTimeline.tsx` | 轨道行三键的命中/取点窗口 ⟹ 改用共享窗口；工具条按钮**已还原**成 upsert（代码里留有指向本记录的注释） | 同上 ＋ `raw/source-869-batch36-spec.md` |
| 3 | `src/components/director/DirectorInspector.tsx` | 两处 `< 0.001` ⟹ `directorKeyframeHit(...)` | 同上 |
| 4 | `src/store/directorStore.ts` | `upsertTrackKeyframe` / `upsertGroupTrackKeyframe` 的字面量 `0.001` ⟹ 具名常量 `DIRECTOR_KEYFRAME_EPSILON`（★ **不是**命中窗口） | `docs/research/beeftv-canvas-2026-09-27/SOURCE_ANALYSIS.md` §23.3 |
| 5 | `scripts/verify-liblib-batch866.py` | 把「在用回归清单」从**写死快照**改成**动态解析**（★ 批次号最大者＝在用）＋ 新增两条结构性判据 | batch 868 引入 `verify-liblib-batch868.py`（★ 碰被跟踪源文件）⟹ 缺口＝`['868.py']` |

## 四、★ 两个容差为什么必须分开

| 容差 | 值 | 语义 | 出处 |
| --- | --- | --- | --- |
| `DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW` | `0.05` | 「**当前帧**关键帧」的**命中**窗口 | 源站 chunk `cZ`：`markers.find(e => .05 >= Math.abs(e.time - h))` |
| `DIRECTOR_KEYFRAME_EPSILON` | `0.001` | 「**同一时刻** upsert」的容差 | `SOURCE_ANALYSIS.md` §23.3 |

★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 混用会出现「以为在命中、其实在 upsert」的账 ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ **必须分开**，且**各自写明出处**。

## 五、被本批作废的方向（★ 留痕，不删）

★ `probes/keyframe_toggle869.py` ＋ `raw/keyframe-toggle-869.json` 编码的是
★ **更正 ② 那个错误方向**（★ 「把工具条按钮改成切换」）⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 探针文件头部已加 `SUPERSEDED` 横幅 ⟹ ⟹ ⟹ ⟹ ⇒ ★ JSON 原样保留作为**痕迹**。
★ 真正生效的探针是 `probes/keyframe_window869.py`（★ 13 条判据全绿）。

## 六、866 门禁那条红的归因（★ 受控对照取证）

★ 全量回归 283 条 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 红 71 条（★ 旧账 70 ＋ 新红 1）⟹ ⟹ ⟹ ⟹ ⇒ ★
★ 新红那条是 `866.py` ⟹ ⟹ ⟹ ⟹ ⇒ ★ 根因：`866` 把「在用回归清单」**写死**成
★ `probes/regress866.py`（★ 177 条历史快照）⟹ ⟹ ⟹ ⟹ ⇒ ★ batch 868 提交了新的
★ `verify-liblib-batch868.py`（★ 它碰被跟踪源文件）⟹ ⟹ ⟹ ⟹ ⇒ ★ 缺口＝`['868.py']`。

★ ★★ **受控对照**（★ 证明归因，不是猜）：
1. 临时移走 `scripts/verify-liblib-batch868.py` ⟹ ⟹ ⟹ ⟹ ⇒ ★ `866` **立刻 18 判据 0 失败**；
2. 复原后 sha256 **逐字一致**（`a3fddae3b675c8043f0125a5aa57d4a093f099d0e9dbe1905b8e3dc38822704a`）✔

★ ⇒ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 归因＝**batch 868 提交引入**，⟹ ⟹ ⟹ ⟹ ⇒ ★ **不是 869 引入**。
★ 修法＝把写死改成**动态解析在用清单**（★ 批次号最大者）＋ 加「清单只增不减」判据。
