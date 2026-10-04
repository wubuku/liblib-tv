# Batch 763 — 导演台未覆盖面：移动端 focus scope、导演台自己的快捷键、逐控件 Esc 普查

- 日期：2026-10-01
- clone dev server：`http://localhost:4317`
- 测试画布：`canvas-2`（10 节点），导演台入口节点 `b-bTLLuU4w5q`
- 视口：桌面 `1440x1000`、窄视口 `800x1000`
- 探针：8 个（763a–763h），原始读数全部落盘在 `raw/`，探针与汇编器在 `probes/`
- **`src/` 零改动**（本批只普查，不动实现）
- 未做源站对照；未碰付费与真实生成

## 选题

762 挂了三条「导演台没测」：移动端 focus scope 完全没测、导演台自己的快捷键没测、
导入/导出面板内的焦点行为没测。本批把前两条做完，第三条留到 764（导出面板的
焦点围栏与 Esc 优先级在 763a 已经验过一轮，见 J2）。

结果是：**围栏、抽屉、快捷键这三块都没毛病，毛病在一个手势边界的
`stopPropagation` 上** —— 它把 Esc 从 9 个数值框里整个吞掉，导致窄视口下
属性抽屉关不掉。

## 判据（14 条，全部 PASS）

| 判据 | 结论 | 依据 |
| --- | --- | --- |
| J1 | PASS | Batch 622 的 1px 断点缝成立：896/897/898 三档 JS 与 CSS 都判移动端，899/900/901 三档都判桌面，六档零错位；移动端两列真在屏外（树 x=-220、属性 x≥视口宽），桌面端树首控件命中且在树内 |
| J2 | PASS | Esc 优先级阶梯**五步**全对：无面板时关导演台；导出面板开着时第一次只关面板、第二次才关导演台；焦点在可编辑控件里时不关；离开可编辑控件后能关 |
| J3 | PASS | 窄视口两个抽屉都能开：`data-director-mobile-panel-state` 变 open、`data-director-focus-scope` 分别落 tree/inspector，焦点**进到抽屉里**，Tab 12 步 0 次逃出 dialog |
| J4 | PASS | Esc **只关抽屉、不关导演台**（`drawerClosed=True` 与 `workspaceClosed=False` 同时成立），焦点回到对应触发按钮 |
| J5 | PASS | 快捷键阶梯四步全对：⌘Z 撤销（past 1→0、future 0→1）、⌘Y 重做（past 0→1、future 1→0）、再 ⌘Z、再 ⌘⇧Z，每步 `lastCommand` 都跟着变 UNDO/REDO |
| J6 | PASS | Delete 与 Backspace **都真的删掉了对象**（`historyPast` 1→2 / 2→3、点中时对象数 6→5 / 5→4、被点的行消失），两轮同 |
| J7 | PASS | **缺陷 D1 的定量**：树面板 20 个控件按 Esc 全部能关抽屉；属性面板 35 个里 **9 个关不掉**，两轮完全一致，序号 6/9/12/15/18/21/24/27/30，`type` 全是 number |
| J8 | PASS | 传播判决：这 9 个控件上的 Esc **从未到达 window 冒泡**（`reachedWinBubble=false`），但 window 捕获照样触发；能关掉的那 26 个全部触发了 window 冒泡 ⟹ 导演台的 Esc 阶梯根本没机会跑 |
| J9 | PASS | 注入对照**否掉**「`type=number` 原生吞 Esc」：同一面板里现插的 text 与 number 输入框按 Esc **都能**关抽屉 |
| J10 | PASS | 结构性后果：焦点留在那 9 个框里时 Esc 连按两次都关不掉、焦点一直在框内；**Tab 离开该框后 Esc 立刻恢复正常** |
| J11 | PASS | **光聚焦**那个框就已经开出一个 `activeGesture` 却不写历史（`historyPast` 仍 0）；真编辑一次（ArrowUp）后 gesture 仍挂着、past 仍 0，直到 Tab 失焦才 commit（past=1、`GESTURE_COMMIT`） |
| J12 | PASS | 导演台项目**持久化在 localStorage**（键含 owner/canvasId/nodeId）：同一浏览器会话内新增的机位扛过一次完整 reload（两轮 `addSurvivedReload=true`） |
| J13 | PASS | 种子本身确定：两轮都稳定 5 个对象（1 character + 3 prop + 1 camera），t=600ms 一次到位到 6s 不再变，零重复 id |
| J14 | PASS | 改变视口宽度后立刻 fitView，落点**没有**出现「用旧容器宽度」的偏移：4 档 delay × 2 轮 = 8 次 trial 全部落在期望值 x=276、zoom 正确、命中 169 点 |

## 缺陷

### D1（中）`useDirectorGestureBoundary` 无条件吞掉 Escape

**位置**

- `src/components/director/useDirectorGestureBoundary.ts:92-98`
- `src/components/director/DirectorInspector.tsx:182`（`{...(isAxisDisabled(index) ? {} : gesture)}`）
- `src/components/director/DirectorDesk.tsx:475`（监听器挂在 **window 冒泡**）
- `src/components/director/DirectorDesk.tsx:481-485`（移动端「先关抽屉」那一档）

**机制**

```ts
onKeyDown: (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    event.stopPropagation();   // ← 事件在 React root 冒泡处被掐断
    cancel();
    return;
  }
  ...
}
```

事件根本到不了挂在 window 冒泡上的 `DirectorDesk` Esc 阶梯，**包括
`:481-485` 那条「移动端先关抽屉」的分支**。而那一分支本来就排在
`if (isEditable) return;` **之前** —— 说明作者本意就是让 Esc 从可编辑控件里
也能关抽屉，这个边界把该意图覆盖掉了。

**实测影响**

- 属性面板 35 个可聚焦控件里 **9 个** Esc 无效：X/Y/Z 三轴 × 位移/旋转/缩放的
  `<input type="number">`（59×28，紧跟在「左右拖动调整 X 轴」scrub 按钮后）。
- 树面板 20 个控件**全部**有效（含那个 `type=text` 搜索框）。
- 两轮完全一致，序号稳定在 6/9/12/15/18/21/24/27/30。
- 窄视口（800px）下，用户把焦点停在变换数值框里时**没有键盘方式关掉属性抽屉**：
  连按两次 Esc 都无效，焦点一直在框内。
- 逃生门存在：Tab 走到关键帧按钮之后 Esc 立刻恢复正常（抽屉关、导演台不关）。

**阳性对照**：这个边界对「编辑」是在正常干活的 —— ArrowUp 之后 gesture 挂着、
`historyPast` 仍 0，Tab 失焦才 commit（`past=1`、`lastCommand=GESTURE_COMMIT`）。
坏的只是 Escape 的放行。

**修法提示**（需改 `src/`，等授权）：两处一起改才有效。

1. `onKeyDown` 的 Escape 分支加 `if (!activeRef.current) return;` ——
   没有待取消的手势就放行，让上层阶梯接管。
2. `onFocus` 不该 `begin()`（`:79`）—— 实测「只聚焦」就已经开出一个
   `activeGesture` 却没写历史。**聚焦本身不是一次手势起点**；不拆掉这一条，
   上一条的 `activeRef.current` 恒为 true，加了也等于没加。

## 观察（不记缺陷）

- **O1 事实更正**：此前记的是「两个 store 都无持久化」。导演台项目另有一层
  localStorage 持久化，键为
  `liblib-tv-director-project-v1:["libtv","canvas-2","b-bTLLuU4w5q"]`，
  同一浏览器会话内**增删都扛过一次完整 reload**。副作用：探针一旦增删对象，
  同一会话里的后续轮次不再可比 —— 763b 两轮 B1 的差异（树可达控件 20 vs 17、
  属性 35 vs 33）完全由此而来，**不是焦点行为差异**。
- **O2 待拍板**：导演台里的删除对种子数据是破坏性的，界面没有任何
  「未保存/重置」提示，唯一恢复路径是同会话内的 ⌘Z。**不声称**源站是否也这样
  （没做源站对照）。

## 探针教训（返工项）

- **R53 派生量要对「效应」敏感，不能对「标签」敏感。** 763b 初版用
  `changed = lastCommand 前后不同` 判删除是否生效，而连续两次删除的
  `lastCommand` 都是 `DELETE_OBJECTS` ⟹ 派生量恒为 false，差点把
  「两个键都真删了」读成「Backspace 没用」。真实证据在 `historyPast` 与对象计数里。
- **R54 打印 id 不许截断。** 我按 18 字符打印相机 id，把
  `director-camera-main` 和 `director-camera-1791136225444-1` 截成两条一模一样的
  `director-camera-17`，看上去像 id 重复 —— 查全量后是 0 重复。
- **R55 宣称「两轮一致」之前先证明两轮可比。** 探针自伤（增删对象且改动持久化）
  会让两轮不可比；763b 的 round 1 删掉的两个种子对象直接带进了 round 2。
- **R56 「抽屉关掉」与「整个导演台关掉」必须分开记。** 763f 初版只写
  `inspectorState != "open"` 就叫「关掉抽屉」，于是连导演台被关掉的那一格也被记成
  成功。现在固定成 `{deskOpen, drawerClosed, workspaceClosed}` 三个字段。
- **R57 注入对照能否掉看起来很笃定的假设。** 我一度认定「`type=number` 的原生
  Escape 行为吞掉了键」，源码里也确实找不到 `onKeyDown`；同位置注入的 number
  输入框却能正常关抽屉，假设当场被否，才顺藤摸到 `useDirectorGestureBoundary`。

另外两条初版被 FATAL 挡下来的：763b 初版在「1440 加载 → ⌘0 → resize 800 → ⌘0 →
点按钮」这串动作下反复落在 `x=596`、0 命中。763c 用 4 档 delay × 2 轮 = 8 次
trial 定量核查，**0/8 复现**（8 次全在 x=276、命中 169 点），定性为一次性瞬态，
不作为缺陷记账。探针侧改成「每格在自己的宽度上直接加载 + `settle()` 等 fitView
落定 + 落空时落盘判别读数」，见 `probes/dbg763b.py` 的文档字符串。

## 不声称

- 无源站对照：本批全部结论只针对 clone 自身的行为自洽性。
- 763b 的两轮**不可比**（round 1 的增删经 localStorage 带进了 round 2），
  所以 B1/B3 的两轮一致性只按焦点相关字段断言，`reachableInPanel` 单列不判等。
- 只测 800px 一个窄视口（在 899/898 断点之间），没测 700/768/850。
- 只测了 Escape、Tab、⌘Z/⌘Y/⌘⇧Z、Delete、Backspace；⌘C/⌘V 没测
  （要先造出可复制的选择），留挂起。
- 属性面板另外 8 个 `type=number` 输入框（路径锚点 `:825/:887`、场景位移
  `:2811/:2846`、FOV `:1662`、场景读数 `:1995/:2009`）当前不在渲染态，没逐个测；
  它们走同一个边界 hook，**推测**同样受影响 —— 推测不是读数。
- 9 个失效控件里只用 X 轴第一个（position/x）作为代表验了因果链，没有 9 个全测
  （9 个的失效是 763d 扫出来的）。
- 没测屏幕阅读器实际播报；没测 `workspaceBusy` 与 `capture-viewer` 两档
  （它们会吞 Delete 与 Esc，但不好主动制造）。
- 没开第二个导演台项目；导入/导出面板内的焦点围栏留到下一批。

## 复现

```bash
# 1) 起 dev server（4317，多人共用，不要并发跑浏览器脚本）
# 2) 跑探针（每个探针自带两轮，落盘到 raw/）
$HOME/.pyenv/shims/python3 probes/dbg763a.py    # 断点缝 + Esc 阶梯
$HOME/.pyenv/shims/python3 probes/dbg763b.py    # 抽屉 + 快捷键 + 删除
$HOME/.pyenv/shims/python3 probes/dbg763c.py    # resize 后 fitView 落点
$HOME/.pyenv/shims/python3 probes/dbg763d.py    # 逐控件 Esc 普查
$HOME/.pyenv/shims/python3 probes/dbg763e.py    # 传播判决 + 注入对照
$HOME/.pyenv/shims/python3 probes/dbg763f.py    # 吞 Esc 之后的后果
$HOME/.pyenv/shims/python3 probes/dbg763g.py    # 种子确定性
$HOME/.pyenv/shims/python3 probes/dbg763h.py    # 持久化边界
# 3) 汇编（从 raw/ 现算 runtime-audit.json，缺读数判失败）
$HOME/.pyenv/shims/python3 probes/mk763audit.py
# 4) 验收器
$HOME/.pyenv/shims/python3 scripts/verify-liblib-batch763.py
```

注意：`raw/vb763b.json` 与 `raw/vb763h.json` 是**破坏性**读数（真删了种子对象、
真加了机位），重跑会改变后续轮次的起点。763d/763e/763f 只开抽屉、只聚焦、
不增删，可直接重跑。跨轮比较前请先确认 localStorage 里没有
`liblib-tv-director-project-v1:*` 的残留。
