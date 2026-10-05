#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 785 验收器 —— **独立实现**，不 import 普查器，也不 import 汇编器

## 本批要防的错误方向

785 更正 784 的覆盖面。两个方向各自有代价：

- 若沿用 784 的「3 有 / 7 没有」⟹ `setModelLibraryOpen(false)` 继续算成
  「模型库没有外点关闭」⟹ 而模型库**恰好是**纯鼠标 D1i 的两个搭档之一。
- 若把 key `open` **丢掉**（而不是改名为 `phoneVcamOpen`）⟹ 分母从 10 掉到 9
  ⟹ vcam 面板从「无外点关闭」的风险面里**消失**⟹ 「没有全局保障」
  这个大结论的支撑数字会**少一个**。
- 若信 census785 自己写的 `droppedKeys` 理由（「`setOpen(false)` 属于
  `TopNavBar` 的另一个 `open` ⟹ 跨文件撞名」）⟹ 归属就错了：
  784 的 raw 里 `open` 记的是 **`[]`** ⟹ **没发生撞名**。
- 若信 raw 里的派生值而不重算（R149）⟹ `exportOpen` 字段一旦错，
  「导出面板留在原地」这条会跟着错。

## 静态层为什么算「独立」

普查器（`census785.py`）是**监听器优先**：先找每条 `addEventListener`，
再按 `const NAME` 声明回溯取处理器体，最后在里面搜 `set<S>(falsy)`。

本验收器**反过来**：**状态优先** —— 对每个 `S` 先找它**全部**的 `set<S>(`
调用点，从每个调用点向上取**最近的未配对 `{`**，沿括号链一层层往外走，
在每一层检查「这个块的外面是不是一个 pointer 类 `addEventListener` 的实参」。
⟹ 顺序、方法、判据三样都不同，任何一边写错都会被抓出来。

★ 静态层**自己重算**外点关闭清单，不读 `census785.json` ——
否则「改源码」的阴性对照会作用在一个 JSON 上，什么也测不到。

## 沿用 775–784 的纪律

- 阴性对照的 `mutatedAnything` **实测**、`kw` **唯一**
- ★ **源码变异必须行数中性**（782 立）
- ★ 阴性对照要**先验它真改了目标性质**（783 立）
- ★ 派生字段一律**从 raw 重算**（784 立）
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch785-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
CENSUS = OUTDIR / "raw/census785.json"
C784 = (ROOT / "docs/research/liblib-canvas-batch784-2026-10-01"
        / "raw/census784.json")
RAW782 = (ROOT / "docs/research/liblib-canvas-batch782-2026-10-01"
          / "raw/vb782a.json")

DV = "src/components/director/DirectorViewport.tsx"
DT = "src/components/director/DirectorTimeline.tsx"
DOT = "src/components/director/DirectorObjectTree.tsx"
DD = "src/components/director/DirectorDesk.tsx"
DI = "src/components/director/DirectorInspector.tsx"
DVP = "src/components/director/DirectorPhoneVcamPanel.tsx"

PE = ("mousedown", "pointerdown", "click", "touchstart")
FALSY = ("null", "false", "undefined")

STATES = ["activeDirectorNodeId", "contextMenu", "exportPanelOpen",
          "followTargetId", "modelLibraryOpen", "motionPathDraft",
          "pathMenuLeft", "phoneVcamOpen", "presetPanelLeft", "viewerCaptureId"]
EXPECT_WITH = ["contextMenu", "modelLibraryOpen", "pathMenuLeft",
               "presetPanelLeft"]
EXPECT_WITHOUT = ["activeDirectorNodeId", "exportPanelOpen", "followTargetId",
                  "motionPathDraft", "phoneVcamOpen", "viewerCaptureId"]


def setter(s):
    return "set" + s[0].upper() + s[1:]


def line_at(rel, n):
    return (ROOT / rel).read_text(encoding="utf-8").split("\n")[n - 1]


# ───────────────────────── 静态层：状态优先 + 括号链 ─────────────────────────

FN_HEAD = re.compile(
    r"(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)\s*(?:=\s*)?"
    r"(?:\([^)]*\)|[A-Za-z_$][\w$]*)?\s*(?:=>\s*)?$")
INLINE_HEAD = re.compile(
    r"addEventListener\(\s*[\"']([a-z]+)[\"']\s*,\s*$")


def enclosing_chain(text, pos):
    """从 `pos` 往上，取**最近**的未配对 `{`，一路往外，产出所有包裹块。"""
    stack, out, i = [], [], 0
    while i < pos:
        c = text[i]
        if c == "{":
            stack.append(i)
        elif c == "}":
            if stack:
                stack.pop()
        i += 1
    for start in reversed(stack):                 # 由内到外
        d, j = 0, start
        while j < len(text):
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
                if d == 0:
                    break
            j += 1
        out.append((start, j))
    return out


def handler_name_at(text, brace_start):
    """这个块的 `{` 前面紧挨着的是**具名**函数声明吗？返回名字，没有就 None。"""
    head = text[:brace_start].rstrip()
    m = FN_HEAD.search(head)          # FN_HEAD 以 `$` 锚定 ⟹ 只可能匹配紧邻的那一段
    return m.group(1) if m else None


def pointer_listener_for(text, brace_start):
    """这个块是不是某个 **pointer 类 `addEventListener` 的处理器**？

    ★ 注意方向：这些 effect 里**注册写在函数定义之后**
    （`DirectorTimeline.tsx` 的 `close` 定义在 `:555`、注册在 `:569`），
    ⟹ 不能只往 `{` **之前**找注册，要**全文件**找这个名字的注册。
    """
    inline = INLINE_HEAD.search(text[max(0, brace_start - 200):brace_start])
    if inline and inline.group(1) in PE:
        return inline.group(1)
    name = handler_name_at(text, brace_start)
    if not name:
        return None
    # ★ 必须 `finditer`：**同名处理器在一个文件里可能注册多次**
    #   （`DirectorTimeline.tsx` 的 `close` 既挂在 `pointerdown`(:569)
    #   又挂在更早的 `pointerenter` 上）⟹ `search` 会拿到**第一个**、
    #   也就是错的那个 ⟹ 语义是「**任一**注册是 pointer 类」。
    for mm in re.finditer(r"addEventListener\(\s*[\"']([a-z]+)[\"']\s*,\s*%s\b"
                          % re.escape(name), text):
        if mm.group(1) in PE:
            return mm.group(1)
    return None


def scan_outside_close(sources):
    """**状态优先**：对每个 S 找全部 `set<S>(falsy)`，判定是否落在 pointer 监听实参里。"""
    hits = {}
    for s in STATES:
        st, out = setter(s), []
        for rel, text in sources.items():
            for m in re.finditer(r"\b%s\s*\(\s*(%s)" % (st, "|".join(FALSY)),
                                 text):
                for bstart, _bend in enclosing_chain(text, m.start()):
                    ev = pointer_listener_for(text, bstart)
                    if ev:
                        out.append({"event": ev, "file": rel,
                                    "line": text[:m.start()].count("\n") + 1,
                                    "arg": m.group(1)})
                        break
        hits[s] = out
    return hits


def static_side(sources=None):
    src = sources or {rel: (ROOT / rel).read_text(encoding="utf-8")
                      for rel in (DV, DT, DOT, DD, DI, DVP)}
    hits = scan_outside_close(src)
    withoc = sorted(s for s in STATES if hits[s])
    without = sorted(s for s in STATES if not hits[s])
    return {"hits": hits, "with": withoc, "without": without,
            "sources": src}


# ───────────────────────── raw 层：从 782 重算 ─────────────────────────

def pure_mouse_reading(raw):
    """★ 从 782 的 raw **重算**纯鼠标 D1i 读数，不信任何派生字段。"""
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            if r.get("arm") != "captureOwner":
                continue
            ps = r.get("presses") or []
            if len(ps) >= 2:
                return {"cap": (ps[0].get("read") or {}).get("cap"),
                        "win": (ps[0].get("read") or {}).get("win"),
                        "targetOpen": (ps[0].get("state") or {}).get("targetOpen"),
                        "exportOpen": (ps[0].get("state") or {}).get("exportOpen"),
                        "exportOpen2": (ps[1].get("state") or {}).get("exportOpen")}
    return None


# ───────────────────────── 检查 ─────────────────────────

def _ok(x):
    return bool(x)


def run_checks(st, audit, c784, raw):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": _ok(cond), "detail": detail})

    add("S1:4 有外点关闭",
        "重算清单必须正好是 contextMenu / modelLibraryOpen / pathMenuLeft / presetPanelLeft",
        st["with"] == EXPECT_WITH, {"got": st["with"], "want": EXPECT_WITH})
    add("S2:6 无外点关闭",
        "重算清单必须正好是另外 6 个（**含 phoneVcamOpen**）",
        st["without"] == EXPECT_WITHOUT,
        {"got": st["without"], "want": EXPECT_WITHOUT})
    add("S3:modelLibraryOpen 计入",
        "★ `setModelLibraryOpen(false)` 是「关掉」⟹ 模型库**有**外点关闭（784 的假阴性）",
        "modelLibraryOpen" in st["with"]
        and st["hits"]["modelLibraryOpen"][0]["arg"] == "false",
        st["hits"]["modelLibraryOpen"])
    falsy_call = re.search(r"\b%s\s*\(\s*(%s)"
                           % (re.escape(setter("phoneVcamOpen")),
                              "|".join(FALSY)), st["sources"][DV])
    add("S4:phoneVcamOpen 留在分母",
        "★ `open` 要**改名**成 `phoneVcamOpen` 而不是丢掉 ⟹ 它必须在「无外点关闭」里，"
        "**而且必须真的可写**（`DirectorViewport.tsx:3081` 那个 falsy 关闭写入得在）",
        "phoneVcamOpen" in st["without"] and falsy_call is not None,
        {"inWithout": "phoneVcamOpen" in st["without"],
         "falsyWriteAt": (st["sources"][DV][:falsy_call.start()].count("\n") + 1)
         if falsy_call else None})
    add("S5:`open` 不是可写状态",
        "★ `setOpen(` 在面板文件里 0 次 ⟹ 784 那个 key 是 prop",
        "setOpen(" not in st["sources"][DVP], {"file": DVP})
    add("S6:事件全是 pointer 类",
        "★ 4 个外点关闭的事件必须全在 mousedown/pointerdown/click/touchstart 里"
        " ⟹ 键盘一律绕过",
        all(e in PE for s in st["with"] for e in
            (h["event"] for h in st["hits"][s])),
        {s: sorted({h["event"] for h in st["hits"][s]}) for s in st["with"]})
    add("S7:784 基线是 3/7",
        "784 的 raw 必须真的说 3 有 / 7 没有（否则更正无从谈起）",
        len(c784["statesWithOutsideClose"]) == 3
        and len(c784["statesWithoutOutsideClose"]) == 7,
        {"with": len(c784["statesWithOutsideClose"]),
         "without": len(c784["statesWithoutOutsideClose"])})
    add("S8:784 把 `open` 记成「没有」",
        "★ 归属更正：784 raw 里 `open` 在 without 里 ⟹ **没发生撞名**，"
        "错在**整个漏掉一个门状态**",
        "open" in c784["statesWithoutOutsideClose"]
        and "open" not in c784["statesWithOutsideClose"],
        {"with": c784["statesWithOutsideClose"],
         "without": c784["statesWithoutOutsideClose"]})
    add("S9:更正后 4/6",
        "更正必须是从 3/7 变成 **4/6**（不是 4/5 ⟹ 那会把 vcam 面板藏掉）",
        (len(st["with"]), len(st["without"])) == (4, 6),
        {"got": [len(st["with"]), len(st["without"])]})

    pm = pure_mouse_reading(raw)
    add("S10:纯鼠标 D1i 第 1 次",
        "★ 从 782 raw **重算**：第 1 次 Escape `cap=0`（阶梯跑不到）、"
        "模型库已关、**导出面板仍在**",
        pm and pm["cap"] == 0 and pm["win"] == 0
        and pm["targetOpen"] is False and pm["exportOpen"] is True, pm)
    add("S11:纯鼠标 D1i 第 2 次",
        "第 2 次 Escape 才把导出面板关掉",
        pm and pm["exportOpen2"] is False, pm)

    if audit:
        cen = (json.loads(CENSUS.read_text(encoding="utf-8"))
               if CENSUS.exists() else None)
        add("S12:三方对账（汇编器 / 普查器 / 验收器）",
            "★ 三个**独立**实现必须给出同一份清单："
            "汇编器（源码行锚定）、普查器（正则扫描）、本验收器（状态优先重算）",
            cen is not None
            and audit["states"]["withOutsideClose"] == st["with"]
            and audit["states"]["withoutOutsideClose"] == st["without"]
            and cen["statesWithOutsideClose"] == st["with"]
            and cen["statesWithoutOutsideClose"] == st["without"],
            {"audit": audit["states"], "census": cen["statesWithOutsideClose"]
             if cen else None, "verifier": {"with": st["with"],
                                             "without": st["without"]}})
        add("S13:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S12:三方对账（汇编器 / 普查器 / 验收器）",
            "（无 runtime-audit.json，跳过）", True, None)
        add("S13:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
    return checks


# ───────────────────────── 阴性对照 ─────────────────────────

def neg_case(name, why, mutate, kw, chk, st):
    """通用阴性：应用变异 ⟹ 期望某项检查翻成 False。

    ★ `mutate()` 返回 `(复原函数, 实测证据)`。
      1. 复原函数**内建且强制**（`finally`）。
         ★ 第一版把复原函数塞进 `kw["restore"]`（一个空 lambda）⟹
        **阴性对照改了源码却没复原**，后面几次对照全在污染过的源码上跑，
        连「基线本来就红」都被掩盖成「阴性对照 OK」。
      2. 证据必须**实测**：断言 needle 原来**确实在**、变异后**确实不在**
         （783 立的纪律：阴性对照要先验它真改了目标性质）。
    """
    restore, evidence = mutate()
    try:
        st2 = static_side()
        c2 = run_checks(st2, None, kw["c784"], kw["raw"])
        flipped = [c["id"] for c in c2 if not c["ok"]]
        return {"name": name, "why": why,
                "mutatedAnything": True, "evidence": evidence,
                "expectFlipped": chk,
                "flipped": flipped, "ok": chk in flipped,
                "stillPassing": [c["id"] for c in c2 if c["ok"]]}
    finally:
        restore()


def mut_raw(arm, index, field, value, where=None):
    """`where` 形如 `"read"` / `"state"` ⟹ 指明改哪个字典；返回 `(复原, 实测证据)`。"""
    p = RAW782
    orig = p.read_text(encoding="utf-8")
    d = json.loads(orig)
    hit = 0
    seen = []
    for rd in d["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") != arm:
                continue
            press = r["presses"][index]
            if where:
                assert where in press, (
                    "★ press%s 里没有 %r 这层字典（实有 %r）"
                    % (index, where, sorted(press)))
                seen.append(press[where].get(field))
                press[where][field] = value
            else:
                tgt = press.get("state") or press["read"]
                seen.append(tgt.get(field))
                tgt[field] = value
            hit += 1
    assert hit, "★ raw 里没找到 %s 的 press%s.%s" % (arm, index, field)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    reread = json.loads(p.read_text(encoding="utf-8"))
    after = None
    for rd in reread["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == arm:
                press = r["presses"][index]
                after = (press[where] if where else
                         (press.get("state") or press["read"]))[field]
    evidence = {"arm": arm, "press": index, "where": where, "field": field,
                "before": seen[0], "after": after,
                "reallyChanged": after == value and seen[0] != value}
    assert evidence["reallyChanged"], (
        "★ raw 变异没真改到目标字段：%r" % evidence)

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, evidence


def mut_all_falsy_writes(rel, state, new="true"):
    """把这个文件里**所有** `set<S>(falsy)` 逐个改成非 falsy；返回 `(复原, 实测证据)`。

    ★ 不硬编码行号：785 复查时发现 `setPhoneVcamOpen(false)` 在
      `DirectorViewport.tsx` 里有**三处**（`:2826` `toggleModelLibrary`、
      `:3081` 面板 `onClose` 接线、`:3558` 群众面板触发器），
      少改一处就翻不了 S4 ⟹ 逐个列出来也会漏。
    """
    p = ROOT / rel
    orig = p.read_text(encoding="utf-8")
    before = orig.split("\n")
    after = list(before)
    pat = re.compile(r"\b%s\s*\(\s*(%s)" % (re.escape(setter(state)),
                                            "|".join(FALSY)))
    evidence = []
    for i, line in enumerate(before):
        m = pat.search(line)
        if not m:
            continue
        after[i] = (line[:m.start(1)] + new + line[m.end(1):])
        evidence.append({"file": rel, "line": i + 1,
                         "oldPresentBefore": True,
                         "oldPresentAfter": False,
                         "newPresentAfter": True,
                         "codeAfter": after[i].strip()[:100]})
    assert len(after) == len(before), "★ 变异不是行数中性"
    assert evidence, "★ 在 %s 里没找到任何 `set%s(falsy)`" % (rel, state)
    p.write_text("\n".join(after), encoding="utf-8")
    now = p.read_text(encoding="utf-8").split("\n")
    assert not pat.search("\n".join(now)), "★ 还有 falsy 写入没被改掉"
    for e in evidence:
        assert now[e["line"] - 1] == after[e["line"] - 1]

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, evidence


def mut_src(rel, old, new, line):
    """行数中性的源码变异；返回 `(复原, 实测证据)`。"""
    return mut_src_multi((rel, line, old, new))


def mut_src_multi(*specs):
    """一次改多处；仍然要求**行数中性**，并一次性复原全部。"""
    paths = sorted({rel for rel, _, _, _ in specs})
    orig = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in paths}
    evidence = []
    for rel, line, old, new in specs:
        assert old != new, "★ 变异前后相同：%r" % old
        p = ROOT / rel
        before = p.read_text(encoding="utf-8").split("\n")
        assert old in before[line - 1], "★ needle 不在 %s:%d" % (rel, line)
        lines = list(before)
        lines[line - 1] = lines[line - 1].replace(old, new)
        assert len(lines) == len(before), "★ 变异不是行数中性"
        p.write_text("\n".join(lines), encoding="utf-8")
        # ★ 实测：needle 原来在、现在不在
        after = p.read_text(encoding="utf-8").split("\n")[line - 1]
        evidence.append({"file": rel, "line": line,
                         "oldPresentBefore": old in before[line - 1],
                         "oldPresentAfter": old in after,
                         "newPresentAfter": new in after,
                         "codeAfter": after.strip()[:100]})
    assert all(e["oldPresentBefore"] and not e["oldPresentAfter"]
               and e["newPresentAfter"] for e in evidence), \
        "★ 变异没真的改到目标性质：%r" % evidence

    def restore():
        for rel, txt in orig.items():
            (ROOT / rel).write_text(txt, encoding="utf-8")
    return restore, evidence


def main():
    c784 = json.loads(C784.read_text(encoding="utf-8"))
    raw = json.loads(RAW782.read_text(encoding="utf-8"))
    audit = (json.loads(AUDIT.read_text(encoding="utf-8"))
             if AUDIT.exists() else None)
    st = static_side()
    # ★ 阴性对照前记下**字节**，跑完必须一模一样（见 neg_case 的注释）
    fingerprint = {rel: (ROOT / rel).read_bytes() for rel in st["sources"]}
    checks = run_checks(st, audit, c784, raw)
    nPos = sum(1 for c in checks if c["ok"])
    base = {"c784": c784, "raw": raw}

    # ★★ 基线必须**全绿**才准跑阴性对照。
    #   本批已踩过一次：S4 基线红着，它出现在**每一条**阴性对照的 `flipped` 里
    #   ⟹ 7/7 全「通过」，其实全是「本来就在红」。
    assert nPos == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照会在污染过的前提上跑、"
        "且「翻了」可能只是本来就在红"
        % (len(checks) - nPos, [c["id"] for c in checks if not c["ok"]]))

    negs = []
    # ① 把模型库的关闭写成非 falsy ⟹ 清单必须少一个（假阴性被造出来）
    negs.append(neg_case(
        "N1 模型库关闭改成非 falsy", "验证 S1/S3 真的在看 `false` 这个形态",
        lambda: mut_src(DV, "setModelLibraryOpen(false);",
                        "setModelLibraryOpen(true);", 2739),
        dict(base), "S1:4 有外点关闭", st))
    # ② 树的外点关闭不再是 falsy ⟹ 清单必须少一个
    negs.append(neg_case(
        "N2 右键菜单关闭改成非 falsy", "验证 S1 真的在看树那条",
        lambda: mut_src(DOT, "setContextMenu(null);", "setContextMenu(KEEP);", 207),
        dict(base), "S1:4 有外点关闭", st))
    # ③ 把 pointerdown 换成非 pointer 事件 ⟹ 该状态失去外点关闭
    # ★ **两处都要改**：`DirectorTimeline.tsx` 里 `close` 有**两个同名**处理器
    #   （`:569` 运镜菜单、`:593` 预设面板），本方法按**名字**回查注册 ⟹
    #   只改一个，另一个的 `pointerdown` 仍然在 ⟹ 性质没变、翻不了。
    #   ★ 这与 784 汇编器「同名 `close`」是同一类坑，两种方法互相兜着。
    negs.append(neg_case(
        "N3 两处 pointerdown 换成 pointerenter",
        "验证 S6/S1 的 pointer 判据（**同名处理器两处一起改**才真改到性质）",
        lambda: mut_src_multi(
            (DT, 569, 'window.addEventListener("pointerdown", close);',
             'window.addEventListener("pointerenter", close);'),
            (DT, 593, 'window.addEventListener("pointerdown", close);',
             'window.addEventListener("pointerenter", close);')),
        dict(base), "S1:4 有外点关闭", st))
    # ④ 切断 phoneVcamOpen 的 falsy 写入 ⟹ 它不再可写 ⟹ S4 必须发现分母不对
    # ★ **全部** falsy 写入都要切断（`:2826` / `:3081` / `:3558` 三处），
    #   所以用 `mut_all_falsy_writes` **算出来**，不硬编码行号。
    negs.append(neg_case(
        "N4 phoneVcamOpen 全部 falsy 写入被切断",
        "★ 验证 S4 靠的是「它确实有 falsy 写入」而不是靠清单里有个名字",
        lambda: mut_all_falsy_writes(DV, "phoneVcamOpen"),
        dict(base), "S4:phoneVcamOpen 留在分母", st))
    # ⑤ raw：把「导出面板仍在」翻成 False ⟹ S10 必须炸
    r5, e5 = mut_raw("captureOwner", 0, "exportOpen", False)
    try:
        c5 = run_checks(static_side(), None, c784,
                        json.loads(RAW782.read_text(encoding="utf-8")))
        f5 = [c["id"] for c in c5 if not c["ok"]]
        negs.append({"name": "N5 raw：导出面板「仍在」翻成 False",
                     "why": "验证 S10 真的在读这个字段",
                     "mutatedAnything": e5["reallyChanged"], "evidence": e5,
                     "expectFlipped": "S10:纯鼠标 D1i 第 1 次",
                     "flipped": f5, "ok": "S10:纯鼠标 D1i 第 1 次" in f5,
                     "stillPassing": [c["id"] for c in c5 if c["ok"]]})
    finally:
        r5()
    # ⑥ raw：把 `cap=0` 翻成 1 ⟹ S10 必须炸（阶梯其实跑到了）
    # ★ 必须指明改 `read` 层：`cap` 在 `read` 里而不在 `state` 里
    r6, e6 = mut_raw("captureOwner", 0, "cap", 1, where="read")
    try:
        c6 = run_checks(static_side(), None, c784,
                        json.loads(RAW782.read_text(encoding="utf-8")))
        f6 = [c["id"] for c in c6 if not c["ok"]]
        negs.append({"name": "N6 raw：cap=0 翻成 cap=1",
                     "why": "★ 验证「`cap` 在 `read` 层」这个指认是对的"
                            "（第一版没指明层，变异打在 `state` 上，翻不了）",
                     "mutatedAnything": e6["reallyChanged"], "evidence": e6,
                     "expectFlipped": "S10:纯鼠标 D1i 第 1 次",
                     "flipped": f6, "ok": "S10:纯鼠标 D1i 第 1 次" in f6,
                     "stillPassing": [c["id"] for c in c6 if c["ok"]]})
    finally:
        r6()
    # ⑦ 把普查输出与汇编器对调 ⟹ S12 必须发现不一致
    p = CENSUS
    orig = p.read_text(encoding="utf-8")
    d = json.loads(orig)
    d["statesWithOutsideClose"] = ["contextMenu", "pathMenuLeft",
                                   "presetPanelLeft"]
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    try:
        s7 = static_side()
        c7 = run_checks(s7, audit, c784, raw)
        f7 = [c["id"] for c in c7 if not c["ok"]]
        negs.append({"name": "N7 普查清单退回 784 的 3 个",
                     "why": "★ 验证 S12 的三方对账**真的读了** raw/census785.json"
                            "（第一版 S12 只比汇编器 ⟹ 这个变异打在没人读的文件上）",
                     "mutatedAnything": True,
                     "expectFlipped": "S12:三方对账（汇编器 / 普查器 / 验收器）",
                     "flipped": f7,
                     "ok": "S12:三方对账（汇编器 / 普查器 / 验收器）" in f7,
                     "stillPassing": [c["id"] for c in c7 if c["ok"]]})
    finally:
        p.write_text(orig, encoding="utf-8")

    # ── 阴性对照跑完，源码必须**字节一致**（784 的教训：改完没复原）──
    drifted = sorted(rel for rel, b in fingerprint.items()
                     if (ROOT / rel).read_bytes() != b)
    checks.append({
        "id": "S14:阴性对照已复原源码",
        "desc": "★ 阴性对照改过的源码必须字节级还原，否则后续结论都跑在污染源上",
        "ok": not drifted, "detail": {"drifted": drifted}})
    # ★ S14 是**最后**追加的 ⟹ 通过数必须**重新**统计
    nPos = sum(1 for c in checks if c["ok"])

    negs = [n for n in negs if not n.get("skipped")]
    nNeg, nCaught = len(negs), sum(1 for n in negs if n["ok"])
    report = {
        "batch": 785, "checks": checks,
        "totals": {"checks": len(checks), "passed": nPos,
                   "failed": len(checks) - nPos},
        "negativeControls": {"total": nNeg, "caught": nCaught,
                             "detail": negs},
        "static": {"withOutsideClose": st["with"],
                   "withoutOutsideClose": st["without"],
                   "count": {"with": len(st["with"]), "without": len(st["without"])}},
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("=== batch 785 验收 ===")
    for c in checks:
        print("  %s %-28s %s" % ("OK  " if c["ok"] else "FAIL", c["id"],
                                 c["desc"][:60]))
    print("--- 阴性对照 ---")
    for n in negs:
        print("  %s %-34s flipped=%s" % ("OK  " if n["ok"] else "FAIL",
                                         n["name"], n.get("flipped")))
    print("★ 正向 %d/%d   阴性 %d/%d"
          % (nPos, len(checks), nCaught, nNeg))
    print("wrote %s" % REPORT)
    if nPos != len(checks) or nCaught != nNeg:
        sys.exit(1)


if __name__ == "__main__":
    main()
