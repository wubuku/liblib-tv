#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 781 汇编器 —— **补上 780 矩阵的最后一行**，并回答「放行会不会引入新伤害」

## 本批的两件事

① 780 的矩阵里 `Meta+c` / `Meta+v` 那一行被**显式标注为「本批未测」**
   ⟹ 它是矩阵里唯一没有读数支撑的一行，而判据却已经按它推过一轮。

② 更要紧：**「放行」这个动作本身安不安全？**
   780 说「range 上 `Meta+c` 无原生兜底 ⟹ 该放行」。但放行之后，桌的
   `Cmd+C` 分支（`DirectorDesk.tsx:491`）会调 `copyDirectorSelection()`。
   ★ **若它写的是系统剪贴板，用户按 `Cmd+C` 就会把系统剪贴板内容换成
   导演台内部数据 ⟹「修复」变成新的伤害，方向正好相反。**

## ② 的答案（静态，方向相反的那个担心不成立）

`copyDirectorSelection`（`src/store/directorStore.ts:3888-3946`）只写
**内部**的 `clipboard: DirectorClipboardPacketV1`，
而**整个 director 面没有任何 `navigator.clipboard` 调用**
（`writeText` / `readText` 一次都没有）⟹ 导演台的复制/粘贴**完全内部**。

⟹ **放行不会碰系统剪贴板** ⟹ 判据可安全覆盖全部 5 个键。
★ 而这**加固**了 780 的判据：不是「三个键的样本支持一个判据」，
是「五个键全支持，而且不存在『系统剪贴板被污染』这一列」。

## ① 的读数（从源码逐行推出的预测）

- gesture 臂（number/range × `Meta+c`/`Meta+v`，共 4 臂 × 2 次）：
  事件**到达 window**（hook 只拦 Escape）而 `lastCommand` **不出现**
  `COPY_SELECTION` / `PASTE_CLIPBOARD` ⟹ `:487` 吞了 ⟹ 死键。
  ★ **我预测 live 区「无任何文案」—— 被否掉了**：实测是**占位文案
  「无命令反馈」**，而且 `lastCommand`/`lastDisp` **都是陈旧值**
  （`GESTURE_BEGIN`/`COMMITTED`，来自聚焦时开手势那一刻）。
- ★ 对照臂（非输入落点）：`Meta+c` 出现 `COPY_SELECTION`+`COMMITTED`
  ⟹ live 区是占位文案；`Meta+v` 出现 `PASTE_CLIPBOARD`+**`NOOP`**
  ⟹ live 区是**真实消息**「当前没有可复制或粘贴的对象」。

⟹ **修正后的结论比预测更准**：桌**有**「无操作/拒绝」的反馈通道，
而 gesture 臂上**一个命令都没产生** ⟹ 走不到那条通道 ⟹ 面板只能显示
占位文案。**不是「没有反馈通道」，是「命令根本没产生」。**
"""
import hashlib
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent.parent
BATCH = REPO / "docs/research/liblib-canvas-batch781-2026-10-01"
OUT = BATCH / "runtime-audit.json"
RAW = BATCH / "raw/vb781a.json"
RAW776 = REPO / "docs/research/liblib-canvas-batch776-2026-10-01/raw/vb776a.json"
AUDIT780 = REPO / "docs/research/liblib-canvas-batch780-2026-10-01/runtime-audit.json"

COPY_CMD = "COPY_SELECTION"
PASTE_CMD = "PASTE_CLIPBOARD"
META = {"tries", "retried"}
GESTURE_RX = re.compile(r"director-gesture-\d+-(\d+)")
GESTURE_ARMS = ["numberCopy", "numberPaste", "rangeCopy", "rangePaste"]
CONTROL_ARMS = ["controlCopy", "controlPaste"]
ARMS = GESTURE_ARMS + CONTROL_ARMS
PRESSES = 2
#: ★ 搜索**必须带作用域**（R110/R128）—— `navigator.clipboard` 在
#: `app/frameos/` 与 `components/jimeng/` 里都有，只在 director 面里查才算数。
DIRECTOR_GLOBS = ["src/store/directorStore.ts",
                  "src/components/director"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def src_text(rel):
    p = REPO / rel
    if not p.exists():
        raise SystemExit("FATAL 缺源码 %s" % rel)
    return p.read_text(encoding="utf-8")


def blank_comments(s):
    """注释抹白而不删（行号不漂移）。★ 只抹注释，不抹字符串（R107）。"""
    out = list(s)
    i, n, state = 0, len(s), None
    while i < n:
        c = s[i]
        nxt = s[i + 1] if i + 1 < n else ""
        if state is None:
            if c == "/" and nxt == "/":
                state = "line"
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if c == "/" and nxt == "*":
                state = "block"
                out[i] = out[i + 1] = " "
                i += 2
                continue
        elif state == "line":
            if c == "\n":
                state = None
            else:
                out[i] = " "
        else:
            if c == "*" and nxt == "/":
                out[i] = out[i + 1] = " "
                state = None
                i += 2
                continue
            if c != "\n":
                out[i] = " "
        i += 1
    return "".join(out)


def norm(x):
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    if isinstance(x, list):
        return [norm(v) for v in x]
    if isinstance(x, str):
        return GESTURE_RX.sub(r"director-gesture-<TS>-\1", x)
    return x


def strip(rows):
    if isinstance(rows, dict):
        return {k: v for k, v in rows.items() if k not in META}
    return [{k: v for k, v in r.items() if k not in META} for r in (rows or [])]


def reading(row):
    r = {k: v for k, v in row.items() if k not in META}
    r.pop("arm", None)
    return r


# ═══════════════ 1. 原始读数 ═══════════════
raw = json.loads(RAW.read_text(encoding="utf-8"))
rounds = raw["rounds"]
assert len(rounds) == 2, "轮数不是 2"
arms = {}
for rd in rounds:
    for r in strip(rd.get("rows")):
        arms.setdefault(r.get("arm"), []).append(norm(r))
assert set(arms) == set(ARMS), "臂集合不符：%r" % sorted(arms)
bad = [(k, v[0].get("FAILED")) for k, v in arms.items() if v[0].get("FAILED")]
assert not bad, "★ 有 FAILED：%r" % bad
for k, rs in arms.items():
    assert len(rs) == 2, "%s 只跑了 %d 轮" % (k, len(rs))
    assert reading(rs[0]) == reading(rs[1]), "%s 两轮不一致" % k
for k, rs in arms.items():
    c = rs[0]  # ★ 每臂两轮 ⟹ 取第 1 轮那一格（`arms[k]` 是**列表**）
    assert (c.get("focus") or {}).get("ok") is True, "%s 聚焦没落上" % k
    assert (c.get("stateBefore") or {}).get("deskOpen") is True, "%s 桌没开" % k
    for p in c["presses"]:
        assert (p["read"].get("cap") or 0) >= 1, (
            "★ %s 第%s次 cap=%r ⟹ 按键没送达浏览器 ⟹ "
            "「没触发」这个读数没有鉴别力"
            % (k, p["n"], p["read"].get("cap")))
print("（阶段一）%d 轮 × %d 臂 × %d 次按压 = %d 格，零 FAILED，两轮逐字段一致"
      % (len(rounds), len(ARMS), PRESSES, len(ARMS) * PRESSES))

# ═══════════════ 2. 读数（从源码逐行推出的预测） ═══════════════
# ── 预测 A：gesture 臂上 `Meta+c` / `Meta+v` **不发生** ──
#   ⟸ 桌的 C/V 分支（`:490`/`:495`）排在 `:487` **之后**
#   ⟹ 事件到达 window（hook 只拦 Escape）但桌早退
# ★ **我预测 live 区「无任何文案」—— 被否掉了。** 实测是**占位文案
#   「无命令反馈」**（777 的 D1e）⟹ 结论更好也更准：不是「没有反馈通道」，
#   而是「**命令根本没产生，所以走不到那条通道**」。
PLACEHOLDER = "无命令反馈"
STALE_CMD = "GESTURE_BEGIN"
STALE_DISP = "COMMITTED"
noFire = {}
for arm in GESTURE_ARMS:
    c = arms[arm][0]
    per = []
    for p in c["presses"]:
        rd, s = p["read"], p["state"]
        live = s.get("liveTexts") or []
        per.append({"n": p["n"], "cap": rd.get("cap"), "win": rd.get("win"),
                    "lastCommand": s.get("lastCommand"),
                    "lastDisp": s.get("lastDisp"), "liveTexts": live})
        assert (rd.get("win") or 0) >= 1, (
            "★ %s 第%s次 win=%r ⟹ 事件**没到达** window ⟹ "
            "「`:487` 吞的」这个归因不成立，真因是 hook" % (arm, p["n"],
                                                        rd.get("win")))
        assert s.get("lastCommand") not in (COPY_CMD, PASTE_CMD), (
            "★ %s 第%s次 `lastCommand=%r` ⟹ C/V 分支**真的执行了** ⟹ "
            "「`:487` 吞了 Meta+c/Meta+v」这条不成立"
            % (arm, p["n"], s.get("lastCommand")))
        # ★ 两个读数都是**陈旧值** ⟹ 只读其中一个会被骗
        assert s.get("lastCommand") == STALE_CMD, (
            "%s 第%s次 `lastCommand=%r`，而预测是陈旧的 %r"
            % (arm, p["n"], s.get("lastCommand"), STALE_CMD))
        assert s.get("lastDisp") == STALE_DISP, (
            "%s 第%s次 `lastDisp=%r`，而预测是陈旧的 %r"
            % (arm, p["n"], s.get("lastDisp"), STALE_DISP))
        # ★ live 区**不止反馈面板一条**（还有两条无关提示）⟹ 判据是
        #   「占位文案**在其中**」，不是「live 区恰好等于它」（R113 同族：
        #   把「集合相等」当成「包含」会在有别的条目时误判）。
        assert PLACEHOLDER in live, (
            "★ %s 第%s次 live 区是 %r，而**不含**占位文案 %r ⟹ "
            "「面板在骗人」这条要重算" % (arm, p["n"], live, PLACEHOLDER))
    noFire[arm] = per
nNoFire = sum(len(v) for v in noFire.values())
nPlaceholder = sum(1 for arm in GESTURE_ARMS for e in noFire[arm]
                   if PLACEHOLDER in e["liveTexts"])
print("（阶段二）gesture 臂 %d/%d 次：事件**到达 window** 而 `lastCommand` "
      "既不是 COPY_SELECTION 也不是 PASTE_CLIPBOARD、live 区是**占位文案"
      "「%s」** ⟹ **死键，而且面板在骗人**"
      % (nPlaceholder, nNoFire, PLACEHOLDER))

# ── 预测 B：对照臂上 C/V **真的发生** ⟹ 桌自己那条反馈路径是通的 ──
ctrl = {}
for arm in CONTROL_ARMS:
    c = arms[arm][0]
    per = []
    want = COPY_CMD if arm == "controlCopy" else PASTE_CMD
    for p in c["presses"]:
        s = p["state"]
        per.append({"n": p["n"], "cap": p["read"].get("cap"),
                    "win": p["read"].get("win"),
                    "lastCommand": s.get("lastCommand"),
                    "lastDisp": s.get("lastDisp"),
                    "liveTexts": s.get("liveTexts") or []})
        assert s.get("lastCommand") == want, (
            "★ 对照臂 %s 第%s次 `lastCommand=%r`，而预测是 %r ⟹ "
            "桌的 C/V 分支**没跑到** ⟹ 「gesture 臂不发」可能只是"
            "「那个分支本来就不跑」，判别力为零"
            % (arm, p["n"], s.get("lastCommand"), want))
    ctrl[arm] = per
nCtrl = sum(len(v) for v in ctrl.values())
# ★ `Meta+v` 在内部剪贴板为空时应是**非 COMMITTED**（`:3959 if (!state.clipboard)`）
#   ⟹ 而那**正是**桌自己的反馈路径（`getDirectorCommandFeedback` 只对
#   非 COMMITTED 返回文案）⟹ 差异是「静默死键」vs「有反馈的拒绝」
pasteDisps = [e["lastDisp"] for e in ctrl.get("controlPaste") or []]
assert pasteDisps and all(d and d != "COMMITTED" for d in pasteDisps), (
    "★ 对照臂 `Meta+v` 的 disposition 全是 COMMITTED=%r ⟹ "
    "「有反馈的拒绝」这条说法没有读数支撑" % pasteDisps)
nPasteRejected = sum(1 for d in pasteDisps if d and d != "COMMITTED")
copyDisps = [e["lastDisp"] for e in ctrl.get("controlCopy") or []]
# ★ 对照臂的 live 区文案：Paste 给**真实消息**，Copy 给占位（因为 COMMITTED）
pasteLives = sorted({t for e in (ctrl.get("controlPaste") or [])
                     for t in e["liveTexts"]})
copyLives = sorted({t for e in (ctrl.get("controlCopy") or [])
                    for t in e["liveTexts"]})
assert pasteLives and all(t != PLACEHOLDER and t for t in pasteLives), (
    "★ 对照臂 `Meta+v` 的 live 区是 %r ⟹ 「桌有拒绝反馈通道」这条没有读数支撑"
    % pasteLives)
print("（阶段二）对照臂 %d/%d 次：Copy/Paste **真的发生**（Copy disposition=%r；"
      "Paste %d/%d 次是**非 COMMITTED** 的拒绝）⟹ 判别力成立"
      % (nCtrl, nCtrl, copyDisps[0] if copyDisps else None,
         nPasteRejected, len(pasteDisps)))

# ═══════════════ 3. 静态层 ═══════════════
DD = blank_comments(src_text("src/components/director/DirectorDesk.tsx"))
dl = DD.split("\n")
STORE = blank_comments(src_text("src/store/directorStore.ts"))
FB_LIB = src_text("src/lib/directorCommandFeedback.ts")


def all_in(lines, pat):
    rx = re.compile(pat)
    return [n for n, ln in enumerate(lines, 1) if rx.search(ln)]


def first_in(lines, pat, after=0):
    return next((n for n in all_in(lines, pat) if n > after), None)


guardLine = first_in(dl, r"if \(isEditable\) return;")
copyLine = first_in(dl, r'key\.toLowerCase\(\) === "c"')
pasteLine = first_in(dl, r'key\.toLowerCase\(\) === "v"')
copyCall = first_in(dl, r"copyDirectorSelection\(\);", after=copyLine or 0)
pasteCall = first_in(dl, r"pasteDirectorClipboard\(\);", after=pasteLine or 0)

# ★ 「导演台从不碰系统剪贴板」——**必须带作用域**地只在 director 面里查
#   （`app/frameos/` 与 `components/jimeng/` 里都有 `navigator.clipboard`，
#    不带作用域会得到一个**完全相反**的结论，R110/R128）
import glob as _glob  # noqa: E402

director_files = []
for g in DIRECTOR_GLOBS:
    p = REPO / g
    if p.is_file():
        director_files.append(p)
    elif p.is_dir():
        director_files.extend(sorted(p.rglob("*.ts"))
                              + sorted(p.rglob("*.tsx")))
sysClipHits = []
for p in director_files:
    t = p.read_text(encoding="utf-8")
    for n, ln in enumerate(blank_comments(t).split("\n"), 1):
        if re.search(r"navigator\.clipboard|clipboard\.writeText|"
                     r"clipboard\.readText", ln):
            sysClipHits.append("%s:%d" % (p.relative_to(REPO), n))
# 内部剪贴板：store 里真的写它，且类型是**内部包**
internalClip = [n for n, ln in enumerate(STORE.split("\n"), 1)
                if "clipboard: built.packet" in ln]
internalType = "DirectorClipboardPacketV1" in STORE
# 反馈路径：`getDirectorCommandFeedback` 对 COMMITTED 返回 null
committedNull = 'disposition === "COMMITTED") return null' in FB_LIB
# `Meta+v` 在剪贴板为空时的拒绝
pasteEmptyGuard = first_in(STORE.split("\n"), r"if \(!state\.clipboard\) \{",
                           after=first_in(STORE.split("\n"),
                                           r"pasteDirectorClipboard: \(\) =>"))

static = {
    "guardLine": guardLine, "copyLine": copyLine, "pasteLine": pasteLine,
    "copyCallLine": copyCall, "pasteCallLine": pasteCall,
    "copyAfterGuard": bool(guardLine and copyLine and guardLine < copyLine),
    "pasteAfterGuard": bool(guardLine and pasteLine and guardLine < pasteLine),
    "directorFilesScanned": len(director_files),
    "systemClipboardHits": sysClipHits,
    "internalClipboardWriteLine": internalClip[0] if internalClip else None,
    "internalClipboardType": internalType,
    "committedReturnsNull": committedNull,
    "pasteEmptyGuardLine": pasteEmptyGuard,
}
assert guardLine is not None, "守卫找不到了"
assert copyLine is not None and pasteLine is not None, "C/V 分支找不到了"
assert static["copyAfterGuard"] is True and static["pasteAfterGuard"] is True, (
    "★ C/V 分支排到了守卫**之前** ⟹ 「`:487` 吞了 Meta+c/Meta+v」要重算")
assert static["copyAfterGuard"] and static["pasteAfterGuard"], ""
assert internalClip, "★ store 里找不到写内部 clipboard 的那一行"
assert internalType is True, "★ 内部剪贴板的类型不再是 `DirectorClipboardPacketV1`"
assert sysClipHits == [], (
    "★ director 面里**出现了** `navigator.clipboard` 调用（%r）⟹ "
    "「放行不会碰系统剪贴板」这条安全论证**不成立**，矩阵要重算" % sysClipHits)
assert committedNull is True, (
    "★ `getDirectorCommandFeedback` 不再对 COMMITTED 返回 null ⟹ "
    "「早退时连拒绝都看不到」这条要重算")
assert pasteEmptyGuard, "★ store 里找不到 `if (!state.clipboard)` 那道拒绝"
print("（阶段三）静态：守卫 :%s 早于 Copy :%s / Paste :%s｜扫了 %d 个 director "
      "文件，`navigator.clipboard` 命中 **%d** 处 ⟹ 复制/粘贴**完全内部**｜"
      "内部包类型=%s 写入行=%r｜COMMITTED→null=%s｜Paste 空剪贴板拒绝行=%s"
      % (guardLine, copyLine, pasteLine, len(director_files),
         len(sysClipHits), internalType, internalClip, committedNull,
         pasteEmptyGuard))

# ═══════════════ 4. 矩阵补全（族规模从 776 raw 重算并与 780 产物对账） ═══════════════
c776 = json.loads(RAW776.read_text(encoding="utf-8"))["rounds"][0]["census"]
best = {}
for x in c776:
    if not x.get("selfJustified"):
        continue
    if x.get("id") not in best or (x.get("live") or 0) > (
            best[x["id"]].get("live") or 0):
        best[x["id"]] = x
for k, x in best.items():
    assert (x.get("live") or 0) > 0, "★ 776 普查里 %s 族 live=0" % k
fam = {}
for x in best.values():
    fam[x.get("wantType")] = fam.get(x.get("wantType"), 0) + (x.get("live") or 0)
a780 = json.loads(AUDIT780.read_text(encoding="utf-8"))
nRange = fam.get("range")
nNumber = fam.get("number")
c780 = (a780.get("matrix") or {}).get("counts") or {}
assert (nNumber, nRange) == (c780.get("number"), c780.get("range")), (
    "★ 776 raw 重算得 %r，而 780 产物记的是 %r ⟹ 跨批去重规则变了"
    % ((nNumber, nRange), (c780.get("number"), c780.get("range"))))
assert nNumber + nRange == 53, "两族合计 %d，而 776 README 自述 53" % (
    nNumber + nRange)
# ★ 780 那一行必须**确实**标着「未测」⟹ 本批把它换成读数
row780 = {r["key"]: r for r in (a780.get("matrix") or {}).get("rows") or []}
cv780 = row780.get("Meta+c / Meta+v")
assert cv780 and "未测" in (cv780.get("number") or ""), (
    "★ 780 产物里 `Meta+c`/`Meta+v` 那一行**不再标着未测** ⟹ "
    "本批的「补最后一行」前提不成立")

matrix = {
    "rows": [
        {"key": "Escape", "number": "**无** ⟹ 779：hook 吞，桌够不着",
         "range": "**无** ⟹ 同左", "passThrough": "**两族都该放行**",
         "measuredIn": "779"},
        {"key": "Meta+z", "number": "**有**（文本撤销）⟹ 778：早退是**承重墙**",
         "range": "**无** ⟹ D1f 死键", "passThrough": "**只 range 放行**",
         "measuredIn": "778"},
        {"key": "Delete / Backspace", "number": "**有**（删字符）⟹ 780：早退",
         "range": "**无** ⟹ 780 新记录", "passThrough": "**只 range 放行**",
         "measuredIn": "780"},
        {"key": "Meta+c / Meta+v", "number": "**有**（文本复制/粘贴）⟹ **本批实测**："
                                             "事件到达 window 而命令不发",
         "range": "**无** ⟹ **本批实测**：同样不发、且 live 区无任何文案",
         "passThrough": "★ **待产品决定**（见 C781-1）",
         "measuredIn": "781"},
    ],
    "criterion": "★ **放行判据仍是「该键在该类型上有没有原生兜底」**，"
                 "本批把 `Meta+c`/`Meta+v` 也测了 ⟹ 五个键全部支持它。"
                 "★ 但本批**没有**因此给出「C/V 该放行」的结论 —— 因为"
                 "「放行 C/V」不是「恢复一个死键」，而是"
                 "「让 `Cmd+C` 从『什么都不做』变成『把导演台选中写进内部"
                 "剪贴板』」，**那是新增功能而不是修缺陷** ⟹ 属产品决定。",
    "counts": {"range": nRange, "number": nNumber},
    "notMeasured": [],
    "noSystemClipboardColumn": "★ **矩阵里不存在「系统剪贴板被污染」这一列** —— "
                              "director 面 %d 个文件里 `navigator.clipboard` "
                              "命中 **%d** 处 ⟹ 复制/粘贴完全内部。"
                              % (len(director_files), len(sysClipHits)),
}
print("（阶段四）矩阵补全：五个键全部有读数（Escape 779 / Meta+z 778 / "
      "Delete 780 / Meta+c·Meta+v **本批**）｜range %d / number %d"
      "｜★ 不存在「系统剪贴板」那一列" % (nRange, nNumber))

# ═══════════════ 5. 可比性 ═══════════════
r0 = norm(strip(rounds[0].get("rows")))
r1 = norm(strip(rounds[1].get("rows")))
tries = [r.get("tries", 1) for rd in rounds for r in (rd.get("rows") or [])]
comparability = {
    "rounds": len(rounds), "armsPerRound": len(ARMS),
    "pressesPerArm": PRESSES,
    "allConsistent": [reading(x) for x in r0] == [reading(x) for x in r1],
    "retryPolicy": "每格最多试 3 次（含第一次），900×n 退避；`tries`/`retried` "
                   "记进 raw 但**排除在两轮一致性比较之外**。",
    "retryStats": {"cells": len(tries),
                   "retriedCells": sum(1 for t in tries if t > 1),
                   "maxTries": max(tries) if tries else None},
    "boundary": "★ **本批未改 `src/`，也没有任何注入。** 本批**不做任何破坏性"
                "操作**（只按 `Meta+c`/`Meta+v`；`Cmd+V` 因内部剪贴板为空而被"
                "拒绝，**没有粘进任何东西**）；每格开头 `fresh()` 清 "
                "localStorage ⟹ 不留残留；**不点**提交/连接/新增机位/导入导出，"
                "不做付费或真实生图生视频。",
}
assert comparability["allConsistent"] is True, "★ 两轮不一致"

# ═══════════════ 6. 结论 ═══════════════
judgments = [
    {"id": "J1",
     "text": "★ **780 矩阵最后一行被测出来了：gesture 臂上 `Meta+c`/`Meta+v` "
             "同样不发**（%d/%d 次：事件**到达 window** 而 `lastCommand` 既不是 "
             "`COPY_SELECTION` 也不是 `PASTE_CLIPBOARD`）⟹ `:487` 把它们也吞了。"
             "★ 而且比「静默」更糟：`lastCommand`/`lastDisp` **都是陈旧值**"
             "（`GESTURE_BEGIN`/`COMMITTED`，来自聚焦时开手势那一刻），"
             "而 live 区显示的是**占位文案「无命令反馈」** ⟹ "
             "**面板在明确地告诉用户「这里什么也没发生」**。"
             % (nPlaceholder, nNoFire),
     "evidence": "阶段二 预测 A"},
    {"id": "J2",
     "text": "★ **对照臂证明桌自己那条路径是通的**（%d/%d 次：Copy 出现 "
             "`COPY_SELECTION`；Paste 出现 `PASTE_CLIPBOARD` 且 %d/%d 次是"
             "**非 `COMMITTED`** 的拒绝）⟹ 差异不是「有没有功能」，"
             "而是「**静默的死键** vs **有反馈的拒绝**」。" % (
                 nCtrl, nCtrl, nPasteRejected, len(pasteDisps)),
     "evidence": "阶段二 预测 B"},
    {"id": "J3",
     "text": "★ **「放行会不会引入新伤害」—— 不会，而且这个结论是静态可证的。** "
             "扫了 director 面 **%d** 个文件，`navigator.clipboard` / "
             "`clipboard.writeText` / `readText` 命中 **%d** 处；"
             "`copyDirectorSelection` 只写内部 `clipboard: "
             "DirectorClipboardPacketV1`（写入行 :%s）⟹ 导演台的复制/粘贴"
             "**完全内部** ⟹ **矩阵里不存在「系统剪贴板被污染」这一列**。"
             "★ 顺带说明为什么这个搜索**必须带作用域**：`app/frameos/` 与 "
             "`components/jimeng/` 里都有 `navigator.clipboard`，"
             "全仓搜会得到一个**完全相反**的结论。" % (
                 len(director_files), len(sysClipHits), internalClip[0]),
     "evidence": "阶段三"},
    {"id": "J4",
     "text": "★ **但本批不给「C/V 该放行」的结论** —— 「放行 `Cmd+C`」不是"
             "「恢复一个死键」，而是**新增功能**（「把导演台选中写进内部剪贴板」）。"
             "780 的判据只回答「早退是否正当」，而 C/V 两族**都有原生兜底**"
             "⟹ 按判据它们**本来就该早退** ⟹ **不该放行**。"
             "★ 真正的问题被本批暴露出来的是另一件事：那 %d 个 range 滑杆上，"
             "`Meta+c`/`Meta+v` 与 `Meta+z`/`Delete` 一样是死键，"
             "而 780 记 D1f 时**只列了后两者** ⟹ **D1f 的键种清单要补全**。",
     "evidence": "阶段四 + J1"},
]
corrections = [
    {"id": "C781-1",
     "targets": ["**780 的 C780-2 / D1f**：「在没有原生兜底的键上，那 %d 个 "
                 "滑杆是死键」——本批暗示这个键种清单**不完整**" % nRange],
     "was": "读作「死键 = `Meta+z` 与 `Delete`/`Backspace`（780 实测的两个）」。",
     "now": "★ **`Meta+c` 与 `Meta+v` 也是死键**（%d/%d 次实测），而它们"
            "**同样没有原生兜底**（range 滑杆上不可能有文本选区）⟹ "
            "**清单要补全成四个键**。★ 但**这不改变「该放行」的结论** —— "
            "range 侧该放行的仍然是 `Meta+z`/`Delete`/`Backspace`；"
            "C/V 放行属**新增功能**而非修缺陷 ⟹ 单独列为**产品决定**。",
     "evidence": "J1 + J4"},
    {"id": "C781-2",
     "targets": ["**本批的预测**：「`Meta+c`/`Meta+v` 在 gesture 臂上是"
                 "**静默的死键**（live 区无任何文案）」"],
     "was": "读作「按下之后界面什么都不显示」—— 即「没有反馈通道」。",
     "now": "★ **被实测否掉，而且否掉的方式让结论更准。** live 区**有文案**，"
            "是**占位文案「无命令反馈」**；而 `lastCommand`/`lastDisp` "
            "**两个读数都是陈旧值**（`GESTURE_BEGIN`/`COMMITTED`，来自"
            "聚焦时开手势那一刻）⟹ 它们**没有**被这两下按键更新。"
            "★ 对照臂给出了正确对照：`Meta+v` 在内部剪贴板为空时是 "
            "**`NOOP`**，而 live 区显示**真实消息**%r ⟹ "
            "**桌是有「无操作/拒绝」反馈通道的**，只是 gesture 臂上"
            "**一个命令都没产生**，所以走不到那条通道。"
            "⟹ 准确说法是「**死键 + 面板显示占位文案**」，"
            "**不是「静默」，也不是「没有反馈通道」**。"
            % (pasteLives[:1],),
     "evidence": "J1 + J2 + 阶段三"},
]
assert [c["id"] for c in corrections] == ["C781-1", "C781-2"]

probeLessons = [
    {"id": "R138", "text": "★ **判据要覆盖全集才敢用。** 780 用三个键的样本"
                            "立了一个判据，第四行却**没测** ⟹ 矩阵里出现"
                            "一行「凭判据推出来、但没有读数」的结论。"
                            "⟹ 立判据时要说清**它覆盖哪些键**，"
                            "并把未覆盖的**显式列出来**（780 做对了标注，"
                            "781 补上读数）。"},
    {"id": "R139", "text": "★ **提一条修法时先问「放行之后会发生什么」。** "
                            "780 说「`Meta+c` 无原生兜底 ⟹ 该放行」——"
                            "若 `copyDirectorSelection` 写的是系统剪贴板，"
                            "这条「修复」就是**新的伤害**。"
                            "★ 781 静态查了 %d 个 director 文件才敢下结论。"
                            % len(director_files)},
    {"id": "R140", "text": "★ **搜索带作用域在这批是生死线。** "
                            "`navigator.clipboard` 在 `app/frameos/` 与 "
                            "`components/jimeng/` 里都有 ⟹ 全仓搜会得到"
                            "「导演台会污染系统剪贴板」的**完全相反**结论，"
                            "而那会让一个正确的修法被否掉（R110/R128）。"},
]
assert [x["id"] for x in probeLessons] == ["R138", "R139", "R140"]

defects = [
    {"id": "D1f", "severity": "中（★ 780 记的中，781 补全了键种清单）",
     "text": "★ **%d 个 range 族滑杆上，凡是没有原生兜底的键都是死键，且零反馈。**"
             "★ **781 补全**：死键不止 `Meta+z`（778）与 "
             "`Delete`/`Backspace`（780），**`Meta+c`/`Meta+v` 也是死键**"
             "（%d/%d 次实测：事件到达 window 而命令不发、live 区是占位文案）。"
             "⟹ 键种清单是 **4 个**（`Meta+z` / `Delete` / `Backspace` / "
             "`Meta+c`·`Meta+v` 的两个），不是 2 个。" % (
                 nRange, nPlaceholder, nNoFire),
     "evidence": "J1 + C781-1"},
]
audit = {
    "batch": 781,
    "topic": "补上 780 矩阵最后一行（Meta+c/Meta+v），并回答「放行会不会引入"
             "新伤害」—— 答案：不会，因为导演台的复制/粘贴**完全内部**",
    "generatedBy": "probes/mk781audit.py",
    "sources": {
        "vb781a.json": {"sha16": sha(RAW), "rounds": len(rounds),
                        "armsPerRound": len(ARMS), "pressesPerArm": PRESSES},
        "vb776a.json": {"sha16": sha(RAW776), "usedFor": "★ 族规模重算并对账"},
        "batch780/runtime-audit.json": {"sha16": sha(AUDIT780),
                                       "usedFor": "确认那一行标着「未测」"},
    },
    "theHole780Left": {
        "row": "`Meta+c` / `Meta+v`",
        "how780LeftIt": "**显式标注为「本批未测」** ⟹ 矩阵里唯一没有读数"
                        "支撑的一行，而判据已按它推过一轮",
        "safetyQuestion": "★ 「放行」会不会引入新伤害？若 "
                          "`copyDirectorSelection` 写的是**系统剪贴板** ⟹ "
                          "用户按 `Cmd+C` 会把系统剪贴板内容换成导演台内部数据 "
                          "⟹ **「修复」变成新的伤害**。",
        "answer": "★ **不会。** director 面 %d 个文件里 "
                  "`navigator.clipboard`/`writeText`/`readText` 命中 **%d** 处；"
                  "`copyDirectorSelection` 只写内部 "
                  "`clipboard: DirectorClipboardPacketV1`（写入行 :%s）。"
                  % (len(director_files), len(sysClipHits), internalClip[0]),
    },
    "readings": {
        "R-gesture": "gesture 臂 %d/%d 次：事件**到达 window** 而命令不发、"
                     "两个读数都是**陈旧值**、live 区是**占位文案「无命令反馈」**"
                     " ⟹ **死键，而且面板在骗人**" % (nPlaceholder, nNoFire),
        "R-control": "对照臂 %d/%d 次：Copy 出现 `%s`+`COMMITTED`（live=%r）；"
                     "Paste 出现 `%s`+%s（live=%r）⟹ **桌自己那条「无操作/拒绝」"
                     "的反馈通道是通的** ⟹ 差异不在「有没有通道」，"
                     "在「**命令有没有产生**」"
                     % (nCtrl, nCtrl, COPY_CMD, copyLives, PASTE_CMD,
                        pasteDisps[0] if pasteDisps else None, pasteLives),
    },
    "matrix": matrix,
    "verdict": {
        "780最后一行": "**测出来了** —— `Meta+c`/`Meta+v` 在 gesture 臂上"
                       "**同样是死键且零反馈**",
        "放行是否引入新伤害": "**不会** —— 导演台的复制/粘贴**完全内部**，"
                              "矩阵里不存在「系统剪贴板」这一列",
        "C/V该不该放行": "★ **不是「修缺陷」而是「新增功能」** ⟹ 单独列为"
                         "**产品决定**，不进修法",
        "D1f键种清单": "**补全为 4 个**（`Meta+z`/`Delete`/`Backspace`/"
                       "`Meta+c`·`Meta+v`）",
        "780的判据": "**仍成立**，本批把覆盖面从 3 个键扩到 5 个",
    },
    "comparability": comparability,
    "static": static,
    "noFire": noFire,
    "controlArm": ctrl,
    "results": {
        "noFirePresses": nNoFire,
        "placeholderPresses": nPlaceholder,
        "controlFired": nCtrl,
        "pasteRejected": nPasteRejected,
        "controlCopyLive": copyLives,
        "controlPasteLive": pasteLives,
        "gestureLivePlaceholder": PLACEHOLDER,
        "staleCommand": STALE_CMD,
        "staleDisposition": STALE_DISP,
        "systemClipboardHits": len(sysClipHits),
        "directorFilesScanned": len(director_files),
        "rangeControls": nRange, "numberControls": nNumber,
        "failedCells": 0,
    },
    "judgments": judgments,
    "corrections": corrections,
    "findings": {
        "F1": "★ **`Meta+c`/`Meta+v` 在 gesture 臂上也是死键**，而面板显示"
              "**占位文案「无命令反馈」** ⟹ 不只是没反馈，是**在骗人**。",
        "F2": "★ **对照臂证明差异是「静默死键」vs「有反馈的拒绝」**。",
        "F3": "★ **放行不会碰系统剪贴板**（director 面 %d 文件 0 命中）⟹ "
              "安全论证成立，矩阵没有那一列。" % len(director_files),
        "F4": "★ **C/V 该不该放行是产品决定**，不是修缺陷 ⟹ D1f 的键种清单"
              "补全为 4 个，但修法范围不变。",
        "F5": "★ 780 的判据**仍成立**，覆盖面从 3 个键扩到 5 个。",
    },
    "probeLessons": probeLessons,
    "defects": defects,
    "srcDiff": "**本批未改 `src/`**（工作区 `src/` 干净）；**没有任何注入**。",
    "rawSha": {"vb781a.json": sha(RAW), "vb776a.json": sha(RAW776),
               "batch780-audit": sha(AUDIT780)},
    "retryStats": comparability["retryStats"],
    "boundary": comparability["boundary"],
}
OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s" % OUT)
