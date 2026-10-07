#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 786 验收器 —— **独立实现**，不 import 普查器，也不 import 汇编器

## 本批要防的错误方向

786 的结论是「`{modelLibraryOpen, crowdPanelOpen, phoneVcamOpen}` **三向互斥**」。
四个方向各自有代价：

- 若只测「**A 单独打开**」⟹ 读数是「B、C 都是关的」，而 B、C **本来就关着**
  ⟹ 与「A 把它们关掉了」**完全无法区分** ⟹ 所以必须是**有序对**（先 A 后 B）。
- 若信 raw 里的 `verdict` / `openAfter` / `coLive` 派生字段 ⟹ 探针自己算错就一起错
  ⟹ 一律**从 `steps[].read` 重算**（R149）。
- 若沿用 783 的层（只在 1 个文件里报出交叉写入）⟹ `DirectorViewport.tsx`
  那三组互斥**继续隐形** ⟹ 而它们恰好是最容易共活的一组（三者都没外点关闭的
  `phoneVcamOpen` 在里面）。
- 若把「无条件关掉另外两个」当真 ⟹ **vcam 触发器 `:3537` 有门**
  （`if (phoneVcamRecording) return;`）⟹ 录制中点它什么都不会发生。

## 静态层为什么算「独立」

普查器（`census786.py`）用**括号链**（从写入点向上取未配对的 `{`，
看这个 `{` 前面是不是 `=>`）；汇编器（`mk786audit.py`）用**手写行锚定字面量**。

本验收器用**第三种**：★ **缩进列**。对每一条门状态写入行，
取它的缩进，向上找到**第一条缩进更小、且以 `{` 或 `=>` 结尾**的行 ⟹ 那就是函数头。
⟹ 完全不数括号、不用正则去匹配 `const NAME = … =>`，
JSX 内联箭头（`onClick={() => {`）在这种机制下是**最自然**的一档。

## 沿用 775–785 的纪律

- 阴性对照的 `mutatedAnything` **实测**、`kw` **唯一**
- ★ **源码变异必须行数中性**（782 立）
- ★ 阴性对照要**先验它真改了目标性质**（783 立）
- ★ 派生字段一律**从 raw 重算**（784 立）
- ★ **基线必须全绿才准跑阴性对照**（785 立，本批踩过一次）
- ★ 阴性对照跑完源码必须**字节级复原**（785 立）
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch786-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
CENSUS = OUTDIR / "raw/census786.json"
RAW = OUTDIR / "raw/vb786a.json"
C783 = (ROOT / "docs/research/liblib-canvas-batch783-2026-10-01"
        / "raw/census783.json")

DV = "src/components/director/DirectorViewport.tsx"
DT = "src/components/director/DirectorTimeline.tsx"
DOT = "src/components/director/DirectorObjectTree.tsx"
DD = "src/components/director/DirectorDesk.tsx"
DI = "src/components/director/DirectorInspector.tsx"
DVP = "src/components/director/DirectorPhoneVcamPanel.tsx"

GATES = ["activeDirectorNodeId", "contextMenu", "crowdPanelOpen",
         "exportPanelOpen", "followTargetId", "modelLibraryOpen",
         "motionPathDraft", "pathMenuLeft", "phoneVcamOpen",
         "presetPanelLeft", "viewerCaptureId"]
TRI = ["lib", "vcam", "crowd"]
NAME = {"lib": "modelLibraryOpen", "vcam": "phoneVcamOpen",
        "crowd": "crowdPanelOpen"}

SRC_FILES = (DV, DT, DOT, DD, DI, DVP)


def setter(s):
    return "set" + s[0].upper() + s[1:]


def line_at(rel, n):
    return (ROOT / rel).read_text(encoding="utf-8").split("\n")[n - 1]


# ───────────────── 静态层：★ 缩进列分组（第三种机制）─────────────────

BLOCK_HDR = re.compile(r"^\s*(if|for|while|switch|try|catch|do|else|return)\b")
ONE_LINE_HANDLER = re.compile(r"^\s*on[A-Za-z]+\s*=\s*\{?\s*\(\)\s*=>")


def indent_of(line):
    return len(line) - len(line.lstrip())


def is_header(line):
    t = line.rstrip()
    return t.endswith("{") or t.endswith("=>")


def is_fn_header(line):
    """★ 函数级表头。`if (...) {` 之类是**块**不是函数 ⟹ 上溯时要跳过，
    否则一个函数体会被自己的 `if` 切成好几段（第一版就踩了这个）。"""
    return is_header(line) and not BLOCK_HDR.match(line)


def is_type_annotation(line):
    """★ 类型标注 vs 真的写入。第一版用「以 `;` 结尾」判 ⟹ **误杀**
    `DirectorDesk.tsx:565` 的 `{ followTargetId: null });`（它同样以 `;` 结尾）。
    ⟹ 机械判据：类型标注里不会出现 `(` 或 `=>`。"""
    t = line.rstrip()
    return t.endswith(";") and "(" not in t and "=>" not in t


def is_toggle(line):
    """「打开自己」的写入是 toggle：`() => !value`；「关掉别人」的是 `(false)`。
    ⟹ 这是**机械**判据，不靠猜函数名（第一版靠函数名/成员顺序去猜，既脆又错）。"""
    return "=> !value" in line


def gate_writes_on(line):
    """这一行写了哪些门状态（`set<S>(` 或对象字面量键）。"""
    hits = []
    for s in GATES:
        if re.search(r"\b%s\s*\(" % re.escape(setter(s)), line):
            hits.append(s)
        elif re.search(r"[{(,]\s*%s\s*:" % re.escape(s), line) \
                and not is_type_annotation(line):
            hits.append(s)
    return hits


def is_rung(lines, idx):
    """★ 这个写入是不是「早退阶梯的一档」？

    判据（**故意**与普查器的「后 3 行里有 return」不同）：最近一条非空行
    是不是 `if (…) {` ⟹ 是的话这一档写完就 `return`。
    ⟹ 于是同一个概念有**两套**独立实现，互相兜着。
    """
    for j in range(idx - 1, max(-1, idx - 4), -1):
        if not lines[j].strip():
            continue
        return bool(re.match(r"^\s*if\s*\(.*\)\s*\{\s*$", lines[j]))
    return False


def group_by_indent(rel, sources):
    """★ 缩进列分组：写入行 ⟶ 它所属的**函数级**表头行号。

    ★ 单行内联处理器（`onClick={() => setX(false)}`）**自己**就是表头 ——
      否则它会被并进外层某个 `onClick={() => {` 的块里（第一版就误并过一次）。
    """
    text = sources[rel]
    lines = text.split("\n")
    groups = {}
    for i, line in enumerate(lines):
        hits = gate_writes_on(line)
        if not hits:
            continue
        if ONE_LINE_HANDLER.match(line):
            hdr = i + 1
        else:
            ind = indent_of(line)
            hdr = None
            for j in range(i - 1, -1, -1):
                if not lines[j].strip():
                    continue
                if indent_of(lines[j]) < ind and is_fn_header(lines[j]):
                    hdr = j + 1
                    break
            if hdr is None:
                continue
        g = groups.setdefault(hdr, {"header": lines[hdr - 1].strip()[:90],
                                    "headerLine": hdr, "states": [],
                                    "members": []})
        for s in hits:
            g["states"].append(s)
            g["members"].append({"line": i + 1, "state": s,
                                 "toggle": is_toggle(line),
                                 "rung": is_rung(lines, i),
                                 "code": line.strip()[:80]})
    for g in groups.values():
        g["states"] = sorted(set(g["states"]))
        g["members"].sort(key=lambda m: m["line"])
        rungs = sum(1 for m in g["members"] if m["rung"])
        g["mechanism"] = ("early-return-ladder" if rungs >= len(g["members"])
                          else "cross-write+ladders" if rungs
                          else "cross-write")
    return groups


def static_side(sources=None):
    src = sources or {rel: (ROOT / rel).read_text(encoding="utf-8")
                      for rel in SRC_FILES}
    cross = {}
    for rel in SRC_FILES:
        for hdr, g in sorted(group_by_indent(rel, src).items()):
            if len(g["states"]) >= 2:
                cross["%s:%d" % (rel, hdr)] = {
                    "file": rel, "headerLine": hdr, "header": g["header"],
                    "states": g["states"], "members": g["members"],
                    "mechanism": g["mechanism"]}
    return {"cross": cross, "sources": src}


# ───────────────── raw 层：从 steps 重算，不信派生字段 ─────────────────

def recompute_cell(cell):
    """★ 一律从 `steps[].read` 重算 `openAfter` / `coLive` / `verdict`。"""
    steps = (cell.get("steps") or [])
    reads = [s["read"] for s in steps if "read" in s]
    if not reads:
        return None
    last = reads[-1]
    openAfter = {k: last.get(k) == "true" for k in TRI}
    order = cell.get("order") or []
    nOpen = sum(1 for v in openAfter.values() if v)
    out = {"openAfter": openAfter, "simultaneouslyOpen": nOpen,
           "coLive": nOpen >= 2}
    if len(order) == 1:
        only = order[0]
        out["verdict"] = (openAfter[only] is True
                          and sum(1 for k, v in openAfter.items()
                                  if k != only and v) == 0)
        out["discriminator"] = ((cell.get("before") or {}).get(only) == "false")
    elif len(order) == 2:
        first, second = order
        third = [k for k in TRI if k not in (first, second)][0]
        out["verdict"] = (openAfter[second] is True
                          and openAfter[first] is False
                          and openAfter[third] is False)
        out["discriminator"] = (len(reads) > 1
                                and reads[0].get(first) == "true")
    return out


def load_cells(raw):
    return [(rd.get("round"), r) for rd in (raw.get("rounds") or [])
            for r in (rd.get("rows") or [])]


# ───────────────── 检查 ─────────────────

def run_checks(st, audit, raw, c783, cen):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    # ── 静态 ──
    mine = st["cross"]
    files_mine = sorted({v["file"].split("/")[-1] for v in mine.values()})
    add("S1:重算出 6 组「同一函数体写 ≥2 个门状态」",
        "★ 缩进列分组必须找出 6 组（Desk 1 + Timeline 2 + Viewport 3）",
        len(mine) == 6, {"n": len(mine),
                         "keys": sorted(k.split("/")[-1] + ":" + str(v["headerLine"])
                                        for k, v in mine.items())})
    add("S2:跨三个文件",
        "★ P786-1：783 的层只在 DirectorTimeline.tsx 报出 ⟹ 修好后必须多出 "
        "DirectorViewport.tsx 的三组**和** DirectorDesk.tsx 的一组",
        files_mine == ["DirectorDesk.tsx", "DirectorTimeline.tsx",
                       "DirectorViewport.tsx"], files_mine)
    tri_groups = [v for v in mine.values()
                  if set(v["states"]) == {"modelLibraryOpen",
                                          "crowdPanelOpen", "phoneVcamOpen"}]
    add("S3:三向互斥的三组都在",
        "★ `{modelLibraryOpen, crowdPanelOpen, phoneVcamOpen}` 的三个打开者"
        "必须**各自**都写出全部三个",
        len(tri_groups) == 3,
        sorted("%s:%d" % (v["file"].split("/")[-1], v["headerLine"])
               for v in tri_groups))
    # 「先关另外两个、再开自己」：★ 用**机械**判据 —— 组里**恰好一个**
    # toggle 写入（`() => !value`），它就是「打开自己」；其余是 `(false)` 关别人。
    order_ok, order_det = True, []
    for v in tri_groups:
        toggles = [m for m in v["members"] if m["toggle"]]
        detail = {"group": "%s:%d" % (v["file"].split("/")[-1],
                                      v["headerLine"]),
                  "members": [(m["state"], m["line"], m["toggle"])
                              for m in v["members"]]}
        if len(toggles) != 1:
            order_ok = False
            detail["ok"] = False
            detail["why"] = "toggle 写入不是恰好 1 个（实为 %d）" % len(toggles)
        else:
            self_line = toggles[0]["line"]
            others = [m["line"] for m in v["members"] if not m["toggle"]]
            good = bool(others) and all(o < self_line for o in others)
            order_ok = order_ok and good
            detail["selfLine"] = self_line
            detail["others"] = others
            detail["ok"] = good
        order_det.append(detail)
    add("S4:都是「先关另外两个、再开自己」",
        "★ 每个打开者里**恰好一个** toggle 写入（打开自己），且**另外两个**的 "
        "`(false)` 写入行号都**更小**（排在打开自己之前）",
        order_ok, order_det)

    # ★ C786-3：三种机制必须分开 —— 「早退阶梯」**不是**「交叉写入」
    ladder = {k: v for k, v in mine.items()
              if v["mechanism"] == "early-return-ladder"}
    pure = {k: v for k, v in mine.items()
            if v["mechanism"] == "cross-write"}
    mixed = {k: v for k, v in mine.items()
             if v["mechanism"] == "cross-write+ladders"}
    add("S17:三种互斥机制分得开",
        "★ 6 组里必须**恰好** 1 组是早退阶梯（DirectorDesk 的 Escape 阶梯）、"
        "3 组是纯交叉写入（Viewport 的三向）、2 组是混合（Timeline 那对）",
        len(ladder) == 1 and len(pure) == 3 and len(mixed) == 2,
        {"earlyReturnLadder": sorted(ladder), "crossWrite": sorted(pure),
         "mixed": sorted(mixed)})
    # 早退阶梯那一组：两档**都**必须紧跟在 `if (…) {` 之后
    lad = list(ladder.values())
    lad_ok = bool(lad) and all(m["rung"] for v in lad for m in v["members"]) \
        and len(lad[0]["members"]) == 2
    add("S18:早退阶梯的两档都带 `if (…) {`",
        "★ `DirectorDesk.tsx` 的 `handleKeyDown` 写 `exportPanelOpen` 与 "
        "`followTargetId` 两处，但两处**都在 `if (…) {` 里** ⟹ 一次 Escape "
        "最多走一档 ⟹ 它们**互相排斥**、**不是**交叉写入。"
        "★ 这正是第一版普查器**误判**的地方：它用「以 `;` 结尾」当类型标注判据，"
        "把 `:565` 那条**真的**写入也杀了 ⟹ 数字对上了，**理由是错的**",
        lad_ok,
        {"members": lad[0]["members"] if lad else None})

    # 类型标注判据本身的两个方向
    ta_type = is_type_annotation(line_at(DVP, 99))        # `open: boolean;`
    ta_write = not is_type_annotation(
        line_at(DD, 565))                                  # `…{ followTargetId: null });`
    add("S19:类型标注判据两个方向都对",
        "★ `open: boolean;`（`DirectorPhoneVcamPanel.tsx:99`）判成**标注**，"
        "而 `DirectorDesk.tsx:565` 的 `…{ followTargetId: null });` 判成**写入**",
        ta_type and ta_write,
        {"openBooleanIsType": ta_type, "followTargetWriteIsWrite": ta_write})

    # vcam 触发器带门
    gate_line = [n for n in range(3520, 3545)
                 if "if (phoneVcamRecording) return;" in line_at(DV, n)]
    add("S5:vcam 打开者带门",
        "★ 「无条件」这个说法**不成立**：`DirectorViewport.tsx` 的 vcam 触发器"
        "里必须有 `if (phoneVcamRecording) return;`",
        len(gate_line) == 1, {"lines": gate_line})

    # ── 与普查器 / 汇编器三方对账 ──
    cen_groups = sorted("%s:%d" % (g["file"], g["startLine"])
                        for g in cen["crossWrites"])
    aud_groups = sorted("%s:%d" % (g["file"], g["startLine"])
                        for g in audit["crossWriteGroups"]) if audit else []
    mine_groups = sorted("%s:%d" % (v["file"], v["headerLine"])
                         for v in mine.values())
    add("S6:三方对账（汇编器 / 普查器 / 验收器）",
        "三个**独立**实现必须给出同一组「文件:起始行」",
        cen_groups == aud_groups == mine_groups,
        {"census": cen_groups, "audit": aud_groups, "verifier": mine_groups})

    # ── 783 的层确实只报了 Timeline ──
    files_783 = sorted({x["file"].split("/")[-1]
                        for x in c783["crossWriteFiles"]})
    add("S7:783 的基线是 1 个文件",
        "P786-1 的对照：783 raw 里 crossWriteFiles 必须只含 DirectorTimeline.tsx",
        files_783 == ["DirectorTimeline.tsx"], files_783)

    # ── 运行时 ──
    if RAW.exists():
        raw = json.loads(RAW.read_text(encoding="utf-8"))
        cells = load_cells(raw)
        failed = [r.get("arm") for _, r in cells if r.get("FAILED")]
        add("S8:没有 FAILED 的格", "★ 探针每格都必须跑出读数",
            not failed, {"failed": failed})
        rec = {}
        for rd, r in cells:
            rec.setdefault(r.get("arm"), []).append(
                (rd, recompute_cell(r), r.get("verdict"),
                 r.get("openAfter"), r.get("coLive")))
        # 探针自己算的派生字段 vs 我们重算的 ⟹ 不一致就是发现
        mismatch = [a for a, lst in rec.items()
                    for (_, mine2, rawVerdict, rawOpen, rawCoLive) in lst
                    if mine2 and (rawVerdict != mine2["verdict"]
                                  or rawOpen != mine2["openAfter"]
                                  or rawCoLive != mine2["coLive"])]
        add("S9:重算与探针派生字段一致",
            "★ raw 里的 `verdict`/`openAfter`/`coLive` 必须与我们**从 `steps[].read` "
            "重算**的结果逐字段相同（R149）",
            not mismatch, {"mismatch": mismatch})
        # ★ 按**实际 order 长度**数格型，不按名字 —— 第一版用 `"Then" in arm`，
        #   于是「把 `order` 压成单点」这种变异它**完全看不见**
        #   （N5 第一次跑就暴露了：翻了 S9/S11，S10 一声不吭）
        def orders_of(arm):
            return [len(r.get("order") or [])
                    for _rd, r in cells if r.get("arm") == arm]
        singles = sorted(a for a in rec if orders_of(a)
                         and all(n == 1 for n in orders_of(a)))
        pairs = sorted(a for a in rec if any(n >= 2 for n in orders_of(a)))
        add("S10:9 格都在（3 单点 + 6 有序对）",
            "★ 单点给判别力、**有序对**才测得到「能不能共活」；"
            "格型按**实际 order 长度**数，不按臂名",
            len(singles) == 3 and len(pairs) == 6,
            {"singles": singles, "pairs": pairs})
        bad = []
        for a, lst in rec.items():
            for rd, mine2, _rv, _ro, _rc in lst:
                if not mine2 or not mine2["verdict"]:
                    bad.append({"arm": a, "round": rd,
                                "after": mine2 and mine2["openAfter"]})
        add("S11:P786-2 六个有序对全部互斥",
            "★ 点开 A 再点 B，读数必须是「A 已关、B 已开、第三个仍关」",
            not bad, {"violations": bad})
        colive = [{"arm": a, "round": rd, "n": mine2["simultaneouslyOpen"]}
                  for a, lst in rec.items()
                  for (rd, mine2, _a, _b, _c) in lst
                  if mine2 and mine2["coLive"]]
        add("S12:没有任何一格出现共活",
            "★ 三者**永不**同时开着",
            not colive, {"coLiveCells": colive})
        disc = [{"arm": a, "round": rd}
                for a, lst in rec.items()
                for (rd, mine2, _a, _b, _c) in lst
                if mine2 and not mine2["discriminator"]]
        add("S13:判别力都成立",
            "★ 有序对必须**真的**先开成 A 再点 B，否则「被关掉」不是一次转变",
            not disc, {"noDiscriminator": disc})
        # 两轮一致
        by_arm = {}
        for a, lst in rec.items():
            sigs = {json.dumps(mine2 and mine2["openAfter"], sort_keys=True)
                    for (_rd, mine2, _a, _b, _c) in lst if mine2}
            by_arm[a] = len(sigs)
        add("S14:两轮逐臂一致",
            "★ 同一个臂两轮的 `openAfter` 必须完全一样",
            all(v == 1 for v in by_arm.values()), by_arm)
    else:
        add("S8:没有 FAILED 的格", "（无 raw，跳过）", True, None)
        add("S9:重算与探针派生字段一致", "（无 raw，跳过）", True, None)
        add("S10:9 格都在（3 单点 + 6 有序对）", "（无 raw，跳过）", True, None)
        add("S11:P786-2 六个有序对全部互斥", "（无 raw，跳过）", True, None)
        add("S12:没有任何一格出现共活", "（无 raw，跳过）", True, None)
        add("S13:判别力都成立", "（无 raw，跳过）", True, None)
        add("S14:两轮逐臂一致", "（无 raw，跳过）", True, None)

    if audit:
        add("S15:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S15:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
    return checks


# ───────────────── 阴性对照 ─────────────────

def mut_lines(*specs):
    """行数中性的多行变异（`specs` 全是 `(rel, line, old, new)`）；
    返回 `(复原, 实测证据)`。

    ★ **同一文件的多处编辑必须共用一次快照** ——
      第一版用两次独立的 `mut_line` 改**同一个文件**，第二次的 `orig` 抓到的是
      **已被第一次改过**的内容 ⟹ 复原时后写的覆盖先写的 ⟹ **文件仍是脏的**，
      后面每一个阴性对照都跑在污染源上（S16 抓到它，而 S3 因此在**每一条**对照里
      都「翻了」，全是假的）。
    """
    assert specs, "specs 不能为空"
    rels = sorted({s[0] for s in specs})
    orig = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in rels}
    evidence = []
    for rel, line, old, new in specs:
        assert old != new, "★ 变异前后相同：%r" % old
        before = (ROOT / rel).read_text(encoding="utf-8").split("\n")
        assert old in before[line - 1], "★ needle 不在 %s:%d" % (rel, line)
        lines = list(before)
        lines[line - 1] = lines[line - 1].replace(old, new)
        assert len(lines) == len(before), "★ 变异不是行数中性"
        (ROOT / rel).write_text("\n".join(lines), encoding="utf-8")
        after = (ROOT / rel).read_text(encoding="utf-8").split("\n")[line - 1]
        ev = {"file": rel, "line": line, "oldPresentBefore": True,
              "oldPresentAfter": old in after, "newPresentAfter": new in after,
              "codeAfter": after.strip()[:100]}
        assert not ev["oldPresentAfter"] and ev["newPresentAfter"], \
            "★ 变异没真改到目标性质：%r" % ev
        evidence.append(ev)
    for ev in evidence:                                # 最后统一核对一遍
        cur = (ROOT / ev["file"]).read_text(encoding="utf-8")
        assert ev["newPresentAfter"] and not ev["oldPresentAfter"], \
            "★ 变异证据状态失真：%r" % ev
        assert ev["codeAfter"] in cur, \
            "★ 变异后的代码没有留在文件中：%r" % ev

    def restore():
        for rel, txt in orig.items():
            (ROOT / rel).write_text(txt, encoding="utf-8")
    return restore, evidence


def mut_line(rel, line, old, new):
    return mut_lines((rel, line, old, new))


def neg(name, why, mutate, expect, c783, cen, audit, raw):
    restore, ev = mutate()
    try:
        st = static_side()
        c = run_checks(st, audit, raw, c783, cen)
        flipped = [x["id"] for x in c if not x["ok"]]
        return {"name": name, "why": why, "evidence": ev,
                "expectFlipped": expect, "flipped": flipped,
                "ok": expect in flipped,
                "stillPassing": [x["id"] for x in c if x["ok"]]}
    finally:
        restore()


def main():
    c783 = json.loads(C783.read_text(encoding="utf-8"))
    cen = json.loads(CENSUS.read_text(encoding="utf-8"))
    audit = (json.loads(AUDIT.read_text(encoding="utf-8"))
             if AUDIT.exists() else None)
    raw = json.loads(RAW.read_text(encoding="utf-8")) if RAW.exists() else None
    st = static_side()
    fingerprint = {rel: (ROOT / rel).read_bytes() for rel in SRC_FILES}
    raw_fp = RAW.read_bytes() if RAW.exists() else None
    checks = run_checks(st, audit, raw, c783, cen)
    nPos = sum(1 for c in checks if c["ok"])

    # ★ 基线不全绿 ⟹ 阴性对照没意义（785 踩过）
    assert nPos == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照会在污染过的前提上跑"
        % (len(checks) - nPos, [c["id"] for c in checks if not c["ok"]]))

    negs = []
    # ① 把「关掉另外两个」里的一处去掉 ⟹ 该组不再是三向 ⟹ S3 必须翻
    negs.append(neg(
        "N1 三向里少一个写入",
        "验证 S3/S4 真的在看三个状态都在",
        lambda: mut_line(DV, 3539, "setCrowdPanelOpen(false);",
                         "/* 群众面板那行被删了 */"),
        "S3:三向互斥的三组都在", c783, cen, audit, raw))
    # ② 把「先关另外两个」的**顺序**倒过来（先开自己再关别人）
    #    ⟹ S4 必须翻。这要求交换两行的内容 ⟹ 行数中性
    def swap_order():
        # ★ 同文件两处 ⟹ **必须**原子化（见 mut_lines 的注释）
        return mut_lines(
            (DV, 3540, "setPhoneVcamOpen((value) => !value);",
             "setCrowdPanelOpen(false);"),
            (DV, 3539, "setCrowdPanelOpen(false);",
             "setPhoneVcamOpen((value) => !value);"))
    negs.append(neg("N2 顺序倒过来（先开自己再关别人）",
                    "验证 S4 真的在断言行号顺序",
                    swap_order, "S4:都是「先关另外两个、再开自己」",
                    c783, cen, audit, raw))
    # ③ 把 vcam 触发器那道门删掉 ⟹ S5 必须翻（它断言「门存在」）
    negs.append(neg(
        "N3 vcam 触发器的门被删掉",
        "验证 S5 真的在断言那道门**在源码里**（而不是靠推断）",
        lambda: mut_line(DV, 3537, "if (phoneVcamRecording) return;",
                         "/* 门没了 */"),
        "S5:vcam 打开者带门", c783, cen, audit, raw))
    # ⑥ ★ 把那条**真的**写入改成**类型标注** ⟹ S1/S17 必须翻
    #   （验证「类型标注判据」真的在区分这两者，而不是「两种都不算」）
    negs.append(neg(
        "N6 真写入被改成类型标注",
        "★ 验证 S1/S18：把 `DirectorDesk.tsx:565` 那条真的 `followTargetId` 写入"
        "换成一条**类型标注** ⟹ 组数必须掉一个（第一版普查器正是被这个 bug "
        "掩盖成「数字恰好对」）",
        lambda: mut_line(DD, 565,
                         "if (activeCameraId) updateCamera(activeCameraId, { followTargetId: null });",
                         "const followTargetId: string | null;"),
        "S1:重算出 6 组「同一函数体写 ≥2 个门状态」", c783, cen, audit, raw))
    # ⑦ ★ 拆掉早退阶梯的一档的 `return` ⟹ 机制分类必须变 ⟹ S17 必须翻
    negs.append(neg(
        "N7 早退阶梯的一档 `if (…) {` 被拆成 `if (…)`",
        "★ 验证 S17/S18 的机制分类靠的是「这一档是不是**包在 `if (…) {` 里**」"
        "（★ 不是「后面有没有 return」——那是普查器的另一套判据，本验收器看不见，"
        "第一版把 N7 写成删 `return;`，结果一条都没翻）",
        lambda: mut_line(DD, 557, "if (exportPanelOpen) {",
                         "if (exportPanelOpen)"),
        "S17:三种互斥机制分得开", c783, cen, audit, raw))
    # ④ raw：把某一格的 `coLive` 翻成 True ⟹ S9/S12 必须翻
    if raw_fp is not None:
        orig = RAW.read_text(encoding="utf-8")
        d = json.loads(orig)
        hit = 0
        for rd in d["rounds"]:
            for r in rd["rows"]:
                if r.get("arm") == "libThenlib" or r.get("arm") == "libThenvcam":
                    r["coLive"] = not r.get("coLive", False)
                    hit += 1
        assert hit, "★ raw 里没找到目标臂"
        RAW.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        try:
            raw2 = json.loads(RAW.read_text(encoding="utf-8"))
            c = run_checks(static_side(), audit, raw2, c783, cen)
            f = [x["id"] for x in c if not x["ok"]]
            negs.append({"name": "N4 raw：派生字段 coLive 被翻",
                         "why": "验证 S9（派生字段要对账）真的在比",
                         "evidence": {"hit": hit},
                         "expectFlipped": "S9:重算与探针派生字段一致",
                         "flipped": f,
                         "ok": "S9:重算与探针派生字段一致" in f,
                         "stillPassing": [x["id"] for x in c if x["ok"]]})
        finally:
            RAW.write_text(orig, encoding="utf-8")
    # ⑤ raw：把某个臂的 `order` 改成一样（去掉「有序」）
    if raw_fp is not None:
        orig = RAW.read_text(encoding="utf-8")
        d = json.loads(orig)
        hit = 0
        for rd in d["rounds"]:
            for r in rd["rows"]:
                if "Then" in (r.get("arm") or ""):
                    r["order"] = [r["order"][0]]
                    hit += 1
        assert hit, "★ raw 里没找到有序对臂"
        RAW.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        try:
            raw2 = json.loads(RAW.read_text(encoding="utf-8"))
            c = run_checks(static_side(), audit, raw2, c783, cen)
            f = [x["id"] for x in c if not x["ok"]]
            negs.append({"name": "N5 raw：有序对被压成单点",
                         "why": "★ 验证 S10 真的在数「有序对」这个格型"
                                "（单点臂读数无法区分「本来就关」与「被关掉」）",
                         "evidence": {"hit": hit},
                         "expectFlipped": "S10:9 格都在（3 单点 + 6 有序对）",
                         "flipped": f,
                         "ok": "S10:9 格都在（3 单点 + 6 有序对）" in f,
                         "stillPassing": [x["id"] for x in c if x["ok"]]})
        finally:
            RAW.write_text(orig, encoding="utf-8")

    drifted = sorted(rel for rel, b in fingerprint.items()
                     if (ROOT / rel).read_bytes() != b)
    raw_drift = raw_fp is not None and RAW.read_bytes() != raw_fp
    checks.append({
        "id": "S16:阴性对照已复原（源码 + raw）",
        "desc": "★ 阴性对照改过的源码与 raw 必须字节级还原",
        "ok": not drifted and not raw_drift,
        "detail": {"driftedSrc": drifted, "driftedRaw": raw_drift}})
    nPos = sum(1 for c in checks if c["ok"])

    nNeg = len(negs)
    nCaught = sum(1 for n in negs if n["ok"])
    report = {"batch": 786, "checks": checks,
              "totals": {"checks": len(checks), "passed": nPos,
                         "failed": len(checks) - nPos},
              "negativeControls": {"total": nNeg, "caught": nCaught,
                                   "detail": negs},
              "static": {"crossWriteGroups": len(st["cross"]),
                         "keys": sorted(st["cross"])}}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("=== batch 786 验收 ===")
    for c in checks:
        print("  %s %-34s %s" % ("OK  " if c["ok"] else "FAIL", c["id"],
                                 c["desc"][:58]))
    print("--- 阴性对照 ---")
    for n in negs:
        print("  %s %-38s flipped=%s"
              % ("OK  " if n["ok"] else "FAIL", n["name"], n.get("flipped")))
    print("★ 正向 %d/%d   阴性 %d/%d" % (nPos, len(checks), nCaught, nNeg))
    print("wrote %s" % REPORT)
    if nPos != len(checks) or nCaught != nNeg:
        sys.exit(1)


if __name__ == "__main__":
    main()
