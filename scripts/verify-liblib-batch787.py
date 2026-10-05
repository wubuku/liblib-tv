#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 787 验收器 —— **独立实现**，不 import 普查器，也不 import 汇编器

## 本批要防的错误方向

787 的结论是「`store action 调用`也是写入，接上之后组数 6 ⟹ 10」。

- 若把「**往模型库加条目会取消正在进行的运镜绘制**」漏掉 ⟹ 786 那份
  「模型库这一带的互斥关系」清单继续缺一条，而它正好落在 D1i 的风险面上。
- 若把「四组新增」当成「四组**偶然**撞上」⟹ 以为换个写法就没事 ⟹
  实际是**结构性不可见**：786 那层根本没有 action 这个概念。
- 若信普查器的 `crossWriteGroups` 计数而不重算 ⟹ 计数是派生字段（R149）。
- 若阴性对照只改**组件侧**、不碰 store 侧 ⟹ action→字段这条链**一半**没被测到。

## 静态层为什么算「独立」

★ **action → 字段**的解析：普查器用「`create<…>((set, get) => ({` 锚点之后
所有顶层 `  name:` 键**切段**」；本验收器用**从 action 定义处做括号配对**取函数体。
⟹ 同一份信息、两种取法。

★ **写入点 → 函数体**：普查器用**括号链**；本验收器用**缩进列**
（786 那套）+ 单行内联处理器自带头。

## 沿用 775–786 的纪律

- 阴性对照的变异**实测**证据、`kw` **唯一**
- ★ **源码变异必须行数中性**（782 立）
- ★ **同一文件的多处编辑必须原子化**（786 立，否则复原后仍是脏的）
- ★ **基线必须全绿才准跑阴性对照**（785 立）
- ★ 阴性对照跑完源码必须**字节级复原**（785 立，S16）
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch787-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
CENSUS = OUTDIR / "raw/census787.json"
C786_SRC = (ROOT / "docs/research/liblib-canvas-batch786-2026-10-01"
            / "probes/census786.py")

DV = "src/components/director/DirectorViewport.tsx"
DT = "src/components/director/DirectorTimeline.tsx"
DD = "src/components/director/DirectorDesk.tsx"
DOT = "src/components/director/DirectorObjectTree.tsx"
DI = "src/components/director/DirectorInspector.tsx"
DVP = "src/components/director/DirectorPhoneVcamPanel.tsx"
DS = "src/store/directorStore.ts"
US = "src/store/uiStore.ts"

GATES = ["activeDirectorNodeId", "contextMenu", "crowdPanelOpen",
         "exportPanelOpen", "followTargetId", "modelLibraryOpen",
         "motionPathDraft", "pathMenuLeft", "phoneVcamOpen",
         "presetPanelLeft", "viewerCaptureId"]
SRC_FILES = (DV, DT, DD, DOT, DI, DVP)
STORE_FILES = (DS, US)
BLOCK_HDR = re.compile(r"^\s*(if|for|while|switch|try|catch|do|else|return)\b")
ONE_LINE = re.compile(r"^\s*on[A-Za-z]+\s*=\s*\{?\s*\(\)\s*=>")
STORE_DEF = re.compile(r"(?m)^  ([A-Za-z_$][\w$]*)\s*:\s*")


def setter(s):
    return "set" + s[0].upper() + s[1:]


def line_at(rel, n):
    return (ROOT / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def indent_of(line):
    return len(line) - len(line.lstrip())


def is_fn_header(line):
    t = line.rstrip()
    return (t.endswith("{") or t.endswith("=>")) and not BLOCK_HDR.match(line)


def is_type_annotation(line):
    t = line.rstrip()
    return t.endswith(";") and "(" not in t and "=>" not in t


# ── action → 字段：★ 用**括号配对**取函数体（普查器用「下一个顶层键切段」）──

def action_fields(sources=None):
    src = sources or {rel: (ROOT / rel).read_text(encoding="utf-8")
                      for rel in STORE_FILES}
    out = {}
    for rel, text in src.items():
        for m in STORE_DEF.finditer(text):
            name = m.group(1)
            cb = text.find("{", m.end())
            if cb < 0:
                continue
            d, j = 0, cb
            while j < len(text):
                if text[j] == "{":
                    d += 1
                elif text[j] == "}":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            body = text[cb:j + 1]
            fields = set()
            for g in GATES:
                if re.search(r"\b%s\s*\(" % re.escape(setter(g)), body):
                    fields.add(g)
                    continue
                for om in re.finditer(r"[{,]\s*%s\s*:" % re.escape(g), body):
                    ln = text[:cb + om.start()].count("\n") + 1
                    if not is_type_annotation(text.split("\n")[ln - 1]):
                        fields.add(g)
                        break
            if fields:
                out.setdefault(name, set()).update(fields)
    return {k: sorted(v) for k, v in out.items()}


# ── 写入点 → 函数体：★ 缩进列（普查器用括号链）──

def writes_in(text, start, end, actions):
    body = text[start:end]
    hits = set()
    for a in sorted(actions):
        if re.search(r"(?<![\w.$])%s\s*\(" % re.escape(a), body):
            hits.update(actions[a])
    for s in GATES:
        if re.search(r"\b%s\s*\(" % re.escape(setter(s)), body):
            hits.add(s)
            continue
        for m in re.finditer(r"[{(,]\s*%s\s*:" % re.escape(s), body):
            ln = text[:start + m.start()].count("\n") + 1
            if not is_type_annotation(text.split("\n")[ln - 1]):
                hits.add(s)
                break
    return hits


def writes_on_line(line, actions):
    """这一行写了哪些门状态（三种形态）。"""
    hits = set()
    for a in sorted(actions):
        if re.search(r"(?<![\w.$])%s\s*\(" % re.escape(a), line):
            hits.update(actions[a])
    for s in GATES:
        if re.search(r"\b%s\s*\(" % re.escape(setter(s)), line):
            hits.add(s)
            continue
        for m in re.finditer(r"[{(,]\s*%s\s*:" % re.escape(s), line):
            if not is_type_annotation(line):
                hits.add(s)
            break
    return hits


def group_by_indent(rel, text, actions):
    """★ 缩进列分组：写入行 ⟶ 它所属的**函数级**表头行号。

    ★ 第一版拿 `writes_in(text, i, i + 1, actions)` 去判「这一行写了什么」——
      那个切片拿到的是**一个字符**（换行符）⟹ 恒为空 ⟹ **一个组都找不到**。
      ⟹ 判据必须是**按行**判（`writes_on_line`），函数体判据只用于算早退档数。
    """
    lines = text.split("\n")
    groups = {}
    for i, line in enumerate(lines):
        has = writes_on_line(line, actions)
        if not has:
            continue
        if ONE_LINE.match(line):
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
        g = groups.setdefault(hdr, {"headerLine": hdr, "states": set()})
        g["states"].update(has)
    return groups


def static_side(sources=None):
    src = sources or {rel: (ROOT / rel).read_text(encoding="utf-8")
                      for rel in SRC_FILES}
    actions = action_fields()
    cross = {}
    for rel in SRC_FILES:
        for hdr, g in group_by_indent(rel, src[rel], actions).items():
            if len(g["states"]) >= 2:
                cross["%s:%d" % (rel, hdr)] = sorted(g["states"])
    return {"cross": cross, "actions": actions, "sources": src}


# ───────────────── 检查 ─────────────────

def run_checks(st, audit, cen):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    mine = st["cross"]
    add("S1:重算出 10 组",
        "★ 缩进列分组 + action 解析必须找出 10 组",
        len(mine) == 10, {"n": len(mine),
                          "keys": sorted(k.split("/")[-1] for k in mine)})

    new4 = {
        "%s:1532" % DT: {"motionPathDraft", "pathMenuLeft"},
        "%s:1574" % DT: {"motionPathDraft", "pathMenuLeft"},
        "%s:2835" % DV: {"motionPathDraft", "modelLibraryOpen"},
        "%s:2842" % DV: {"motionPathDraft", "modelLibraryOpen"},
    }
    missing = [k for k, v in new4.items() if set(mine.get(k, [])) != v]
    add("S2:四组新增都在",
        "★ `DirectorTimeline.tsx:1532/:1574` 与 `DirectorViewport.tsx:2835/:2842`",
        not missing,
        {"missingOrWrong": missing,
         "found": {k.split("/")[-1]: v for k, v in mine.items()
                   if k in new4}})

    add("S3:★ 重头戏：模型库加条目会杀掉运镜绘制",
        "★ `addModelLibraryObject` 必须既写 `motionPathDraft` 又被 "
        "`addModelLibraryItem` 在**同一个函数体**里调",
        "addModelLibraryObject" in st["actions"]
        and "motionPathDraft" in st["actions"]["addModelLibraryObject"]
        and set(mine.get("%s:2835" % DV, [])) ==
        {"motionPathDraft", "modelLibraryOpen"},
        {"actionFields": st["actions"].get("addModelLibraryObject"),
         "group2835": mine.get("%s:2835" % DV)})

    add("S4:action 侧行锚定",
        "★ `directorStore.ts:5190` 必须是 `motionPathDraft: null,`"
        "（**置空**，不是赋值成别的）",
        "motionPathDraft: null," in line_at(DS, 5190)
        and "addModelLibraryObject: (item) => {" in line_at(DS, 5152),
        {"5190": line_at(DS, 5190).strip()})

    # ★ 汇编器的范围**只有那 4 组新增**（它逐行手锚的就是这 4 组）⟹
    #   拿它去比「全部 10 组」是**越界**，第一版这么写直接 KeyError。
    #   ⟹ 改成**四方一致**：普查与验收器都必须给出 10 组、彼此相同，
    #     且汇编器断言的那 4 组**必须同时出现在**这两份里。
    raw_keys = set("%s:%d" % (g["file"], g["startLine"]) for g in cen["crossWrites"])
    my_keys = set(mine)
    aud_keys = set("%s:%d" % (g["file"], g["startLine"])
                   for g in (audit["newGroups"] if audit else []))
    add("S5:四方一致（普查 / 验收器 计数+清单，汇编器 那 4 组）",
        "★ 普查与验收器必须都给出 **10** 组且清单相同；汇编器断言的 4 组"
        "必须**同时出现在**这两份里",
        len(raw_keys) == 10 and len(my_keys) == 10
        and raw_keys == my_keys and aud_keys <= raw_keys and aud_keys <= my_keys
        # ★ 普查**自己声明的计数**也要和它的清单对账（R149：派生字段必须与
        #   自己的输入一致）—— 第一版只比清单长度，于是「把计数字段改成 6」
        #   这条对照**一条都没翻**
        and cen["crossWriteGroups"] == len(raw_keys),
        {"censusDeclaredCount": cen["crossWriteGroups"],
         "censusListCount": len(raw_keys),
         "censusCount": len(raw_keys), "verifierCount": len(my_keys),
         "assemblerGroups": sorted(k.split("/")[-1] for k in aud_keys),
         "assemblerNotInCensus": sorted(k.split("/")[-1]
                                         for k in aud_keys - raw_keys),
         "diff": sorted(k.split("/")[-1] for k in raw_keys ^ my_keys)})

    src786 = C786_SRC.read_text(encoding="utf-8")
    add("S6:786 那层确实不认识 action（缺陷被钉住）",
        "★ `census786.py` 里既无 `store_action_writes` 也无 `\"action\"` 形态",
        "store_action_writes" not in src786 and '"action"' not in src786,
        {"hasStoreActionWrites": "store_action_writes" in src786,
         "hasActionForm": '"action"' in src786})

    if audit:
        add("S7:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S7:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
    return checks


# ───────────────── 阴性对照 ─────────────────

def mut_lines(*specs):
    """行数中性的多行变异；**同一文件多处编辑必须原子化**（786 立）。"""
    assert specs
    rels = sorted({s[0] for s in specs})
    orig = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in rels}
    evidence = []
    for rel, line, old, new in specs:
        assert old != new
        before = (ROOT / rel).read_text(encoding="utf-8").split("\n")
        assert old in before[line - 1], "★ needle 不在 %s:%d" % (rel, line)
        lines = list(before)
        lines[line - 1] = lines[line - 1].replace(old, new)
        assert len(lines) == len(before), "★ 变异不是行数中性"
        (ROOT / rel).write_text("\n".join(lines), encoding="utf-8")
        after = (ROOT / rel).read_text(encoding="utf-8").split("\n")[line - 1]
        ev = {"file": rel, "line": line, "oldGone": old not in after,
              "newThere": new in after, "codeAfter": after.strip()[:100]}
        assert ev["oldGone"] and ev["newThere"], \
            "★ 变异没真改到目标性质：%r" % ev
        evidence.append(ev)

    def restore():
        for rel, txt in orig.items():
            (ROOT / rel).write_text(txt, encoding="utf-8")
    return restore, evidence


def neg(name, why, mutate, expect, cen, audit):
    restore, ev = mutate()
    try:
        c = run_checks(static_side(), audit, cen)
        flipped = [x["id"] for x in c if not x["ok"]]
        return {"name": name, "why": why, "evidence": ev,
                "expectFlipped": expect, "flipped": flipped,
                "ok": expect in flipped,
                "stillPassing": [x["id"] for x in c if x["ok"]]}
    finally:
        restore()


def main():
    cen = json.loads(CENSUS.read_text(encoding="utf-8"))
    audit = (json.loads(AUDIT.read_text(encoding="utf-8"))
             if AUDIT.exists() else None)
    st = static_side()
    fingerprint = {rel: (ROOT / rel).read_bytes()
                   for rel in SRC_FILES + STORE_FILES}
    checks = run_checks(st, audit, cen)
    nPos = sum(1 for c in checks if c["ok"])
    assert nPos == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照没意义"
        % (len(checks) - nPos, [c["id"] for c in checks if not c["ok"]]))

    negs = []
    # ① 组件侧：去掉那个 action 调用 ⟹ 组数掉
    negs.append(neg("N1 去掉组件侧的 action 调用",
                    "验证 S1/S2 真的在看那个 action 调用",
                    lambda: mut_lines((DV, 2836, "addModelLibraryObject(item);",
                                       "/* 不加条目了 */")),
                    "S1:重算出 10 组", cen, audit))
    # ② ★ store 侧：让这个 action **不再**写 motionPathDraft ⟹ 组数掉
    #    （只改组件侧的话，action→字段这条链**一半**没被测到）
    negs.append(neg("N2 store 侧：该 action 不再写 motionPathDraft",
                    "★ 验证 action→字段的解析链**整条**都在测"
                    "（第一版只改组件侧，于是 store 侧根本没被覆盖）",
                    lambda: mut_lines((DS, 5190, "motionPathDraft: null,",
                                       "motionPathDraftKept: null,")),
                    "S1:重算出 10 组", cen, audit))
    # ③ 把「置空」改成别的写入 ⟹ S4 必须翻
    negs.append(neg("N3 置空改成别的值",
                    "验证 S4 真的在断言「**置空**」而不是「有写入」",
                    lambda: mut_lines((DS, 5190, "motionPathDraft: null,",
                                       "motionPathDraft: draft,")),
                    "S4:action 侧行锚定", cen, audit))
    # ④ 把普查计数改掉 ⟹ S5 必须翻
    orig = CENSUS.read_text(encoding="utf-8")
    d = json.loads(orig)
    d["crossWriteGroups"] = 6
    CENSUS.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    try:
        cen2 = json.loads(CENSUS.read_text(encoding="utf-8"))
        c = run_checks(static_side(), audit, cen2)
        f = [x["id"] for x in c if not x["ok"]]
        negs.append({"name": "N4 raw：普查计数被改回 6",
                     "why": "验证 S5 的对账真的在比计数",
                     "evidence": {"before": cen["crossWriteGroups"],
                                  "after": 6},
                     "expectFlipped": "S5:四方一致（普查 / 验收器 计数+清单，汇编器 那 4 组）",
                     "flipped": f,
                     "ok": "S5:四方一致（普查 / 验收器 计数+清单，汇编器 那 4 组）" in f,
                     "stillPassing": [x["id"] for x in c if x["ok"]]})
    finally:
        CENSUS.write_text(orig, encoding="utf-8")

    drifted = sorted(rel for rel, b in fingerprint.items()
                     if (ROOT / rel).read_bytes() != b)
    checks.append({
        "id": "S8:阴性对照已复原（源码 + raw）",
        "desc": "★ 阴性对照改过的源码与 raw 必须字节级还原",
        "ok": not drifted, "detail": {"drifted": drifted}})
    nPos = sum(1 for c in checks if c["ok"])
    nNeg = len(negs)
    nCaught = sum(1 for n in negs if n["ok"])
    report = {"batch": 787, "checks": checks,
              "totals": {"checks": len(checks), "passed": nPos,
                         "failed": len(checks) - nPos},
              "negativeControls": {"total": nNeg, "caught": nCaught,
                                   "detail": negs},
              "static": {"groups": len(st["cross"]),
                         "actions": len(st["actions"]),
                         "keys": sorted(k.split("/")[-1] for k in st["cross"])}}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("=== batch 787 验收 ===")
    for c in checks:
        print("  %s %-32s %s" % ("OK  " if c["ok"] else "FAIL", c["id"],
                                 c["desc"][:56]))
    print("--- 阴性对照 ---")
    for n in negs:
        print("  %s %-36s flipped=%s"
              % ("OK  " if n["ok"] else "FAIL", n["name"], n.get("flipped")))
    print("★ 正向 %d/%d   阴性 %d/%d" % (nPos, len(checks), nCaught, nNeg))
    print("wrote %s" % REPORT)
    if nPos != len(checks) or nCaught != nNeg:
        sys.exit(1)


if __name__ == "__main__":
    main()
