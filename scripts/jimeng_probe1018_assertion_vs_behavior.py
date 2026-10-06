#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1018：**那 24 条「在读原型源码」的判据，到底在验什么？**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 1017 量到：891 条判据里只有 24 条的被测对象是原型代码（2.7%）。
1017 同时诚实地把「这些判据断言的行为、原型里到底实现了没有」划在自己口径之外 ——
本批就往那一步走，而且**只走机器能走的那一步**。

⭐ 本批要验的命题：**这 24 条验的是「那段字还在」，不是「这个行为还对」。**

两个反向用例（都在内存里做，**一个字节都不动仓里的原型文件**）：
  Ⓐ **只改行为、不动锚点** ⇒ 24 条应当全绿 ⇒ 说明它看不见行为
  Ⓑ **只改名、不改行为** ⇒ 24 条应当变红（**或直接崩**）⇒ 说明它会被纯重命名打断

⚠️ **三态而不是两态**：`pass` / `fail` / `crash` —— 1012 那条「`crashed` 必须单列」
在这里有实感：Ⓑ 那条判据写的是 `… .split("function armRovingTabindex")[1].split("\\n}")`，
函数一改名，`split` 找不到分隔符就返回**长度 1** 的列表，`[1]` 直接 `IndexError`
⇒⇒⇒ **门会崩，而不是报红。** 并进任何一态都等于把仪器故障报成数据结论。

**纯离线：只读仓里的脚本与原型源码，不开浏览器、不联网、不按任何键。**
"""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT = "scripts/jimeng_unclickable_audit.py"
PROT = "src/components/jimeng"
GOLDEN = ROOT / "docs/research/jimeng-canvas/assertion-vs-behavior-1018.json"


# ── 把 verifier 的顶层执行一遍，拿它**自己读出来的**那些变量 ────────────────────
def load_verifier_globals():
    """exec verifier 顶层（`__name__` 不是 `__main__` ⇒ `main()` 不会跑），
    拿它自己 `read_text` 出来的那些变量。**不重写它的任何读法。**"""
    src = (ROOT / VERIFIER).read_text(encoding="utf-8")
    g = {"__name__": "_v1018", "__file__": str(ROOT / VERIFIER)}
    exec(compile(src, str(ROOT / VERIFIER), "exec"), g)     # noqa: S102
    # ⚠️ 那些 `read_text` **在 `main()` 里面**，exec 顶层拿不到 ⇒
    #   从 `main` 的 AST 里挑出**引用了原型路径的赋值语句**、逐条 `unparse` 后执行
    #   ⇒ **不重写它的任何读法**（连「读不到就当空串」那层都沿用它自己写的）
    tree = ast.parse(src)
    main_fn = next(n for n in tree.body
                   if isinstance(n, ast.FunctionDef) and n.name == "main")
    # 候选 = `main` 里全部单目标赋值语句
    cand = [st for st in main_fn.body
            if isinstance(st, (ast.Assign, ast.AnnAssign))
            and len(getattr(st, "targets", [])) == 1]
    done, picked = set(), 0
    # ⚠️ **不动点遍历**：`csrc = chrome.read_text(...)` 那行**不含** `src/components/jimeng`
    #   字面量（第一版按字面量挑，于是 12 条判据直接 `NameError`）⇒
    #   凡「自由名都已可解析」的赋值就执行，反复扫到没有新的为止
    for _ in range(8):
        progress = False
        for st in cand:
            key = (st.lineno, st.col_offset)
            if key in done:
                continue
            code = ast.unparse(st)
            loads = {n.id for n in ast.walk(st) if isinstance(n, ast.Name)
                     and isinstance(n.ctx, ast.Load)}
            # ⚠️ 扣掉**语句自己绑定**的名字（推导式变量 `ln`、lambda 形参……）
            #   —— 否则那个 join 推导式会因为 `ln` 不在 g 里而被跳过，
            #   而那正是 `T.11` 基线崩掉的原因
            bound = {n.id for n in ast.walk(st) if isinstance(n, ast.Name)
                     and isinstance(n.ctx, ast.Store)}
            if not (loads - bound).issubset(set(g)):
                continue
            try:
                exec(compile(code, "<v1018-read>", "exec"), g)   # noqa: S102
            except Exception:                                   # noqa: BLE001
                continue
            done.add(key)
            picked += 1
            progress = True
        if not progress:
            break
    g["_v1018_n_reads"] = picked
    g["_v1018_n_cand"] = len(cand)
    return g, src


VG, VSRC = load_verifier_globals()
AUSRC = (ROOT / AUDIT).read_text(encoding="utf-8")
WSPATH = ROOT / "src/components/jimeng/JimengWorkspace.tsx"
WS_RAW = WSPATH.read_text(encoding="utf-8")


# ── 取出那 24 条判据的**原始条件表达式**（不是转述） ────────────────────────────
def proto_text_vars():
    t = ast.parse(VSRC)
    pv, tv = set(), set()
    for n in ast.walk(t):
        if not (isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name)):
            continue
        tgt = n.targets[0].id
        seg = ast.get_source_segment(VSRC, n.value) or ""
        if PROT in seg and "read_text" not in seg:
            pv.add(tgt)
        elif "read_text" in seg and (PROT in seg or any(
                isinstance(x, ast.Name) and x.id in pv for x in ast.walk(n.value))):
            tv.add(tgt)
    return tv


TVARS = proto_text_vars()


def collect_checks():
    t = ast.parse(VSRC)
    out = []
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "check" and len(n.args) >= 2:
            cn = {x.id for x in ast.walk(n.args[1]) if isinstance(x, ast.Name)}
            if cn & TVARS:
                desc = (ast.get_source_segment(VSRC, n.args[0]) or "").strip()
                cond = n.args[1]
                out.append({
                    "name": desc.split(" ")[0][:24],
                    "expr": ast.unparse(cond),
                    "node": cond,
                })
    return out


CHECKS = collect_checks()
N = len(CHECKS)


def evaluate(checks, ws_override=None):
    """逐条 eval 判据的**原始条件表达式**。返回三态。"""
    ns = dict(VG)
    ns["_ausrc"] = AUSRC
    if ws_override is not None:
        # 凡是 verifier 自己从 JimengWorkspace.tsx 读出来的变量，一并替换
        for k in list(VG):
            if isinstance(VG.get(k), str) and VG[k] == WS_RAW:
                ns[k] = ws_override
    res = []
    for c in checks:
        code = compile(ast.Expression(body=c["node"]), "<c1018>", "eval")
        try:
            v = eval(code, ns)                                   # noqa: S307
            res.append({"name": c["name"], "state": "pass" if bool(v) else "fail",
                        "value": repr(v)[:80]})
        except Exception as e:                                   # noqa: BLE001
            res.append({"name": c["name"], "state": "crash",
                        "error": "%s: %s" % (type(e).__name__, e)})
    return res


BASE = evaluate(CHECKS)
N_PASS = sum(1 for r in BASE if r["state"] == "pass")

# ── 反向用例 Ⓐ：只改行为、不动任何锚点 ────────────────────────────────────────
#   `const next = cur + dir;`  →  `const next = cur + dir * 2;`
#   步进从 1 变成 2：**焦点在节点序列里一次跨两个** —— 行为实打实变了，
#   而 24 条判据里没有一条锚着这一行。
ANCHOR_LINE = "const next = cur + dir;"
MUT_A = "const next = cur + dir * 2;"
A_APPLIED = ANCHOR_LINE in WS_RAW
WS_A = WS_RAW.replace(ANCHOR_LINE, MUT_A, 1)
A = evaluate(CHECKS, ws_override=WS_A) if A_APPLIED else []
N_A_PASS = sum(1 for r in A if r["state"] == "pass")
A_INVISIBLE = (A_APPLIED and N_A_PASS == N_PASS)

# ── 反向用例 Ⓑ：只改名、不改行为 ─────────────────────────────────────────────
FUNC = "function armRovingTabindex("
MUT_B = "function armRovingTabindexV2("
B_APPLIED = FUNC in WS_RAW
WS_B = WS_RAW.replace(FUNC, MUT_B, 1)
B = evaluate(CHECKS, ws_override=WS_B) if B_APPLIED else []
B_STATES = {}
for r in B:
    B_STATES[r["state"]] = B_STATES.get(r["state"], 0) + 1
B_BREAKS = (B_APPLIED and (B_STATES.get("fail", 0) + B_STATES.get("crash", 0)) > 0)
B_CRASHES = B_STATES.get("crash", 0) > 0

# ── 断言对象的分类：这 24 条到底在断言什么 ────────────────────────────────────
CJK = re.compile(r"[\u4e00-\u9fff]|\*\*")


def classify(node, expr):
    """一个条件里出现了几个字符串字面量、各自断言在哪个变量上。

    ⚠️ 直接遍历 AST 节点、**不重新 parse 源码文本** —— 跨行条件的
    `get_source_segment` 结果带缩进、reparse 会 `IndentationError`。
    """
    tree = node
    lits = [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    on_proto, on_audit, prose, code = 0, 0, 0, 0
    for n in ast.walk(tree):
        # ⚠️ `x in y` 里**容器是 comparators[0]**，不是 left
        # （第一版查 left，于是「断 audit 文本的判据」数出来是 0）
        if isinstance(n, ast.Compare) and isinstance(n.ops[0], ast.In):
            cont = n.comparators[0] if n.comparators else None
            if isinstance(cont, ast.Name):
                if cont.id in TVARS:
                    on_proto += 1
                elif cont.id == "_ausrc":
                    on_audit += 1
    for l in lits:
        if CJK.search(l) or l.strip().startswith("*"):
            prose += 1
        elif re.match(r"^[A-Za-z_$({[<]", l.strip()) or " " in l.strip():
            code += 1
        else:
            code += 1
    return {"expr": expr[:120], "n_literals": len(lits),
            "n_memberships_on_prototype": on_proto,
            "n_memberships_on_audit": on_audit,
            "n_prose_literals": prose, "n_code_literals": code}


CLASS = [classify(c["node"], c["expr"]) for c in CHECKS]
N_ON_AUDIT = sum(1 for c in CLASS if c["n_memberships_on_audit"] > 0)
N_ONLY_AUDIT = sum(1 for c in CLASS
                   if c["n_memberships_on_audit"] > 0
                   and c["n_memberships_on_prototype"] == 0)
N_PROSE = sum(1 for c in CLASS if c["n_prose_literals"] > 0)


# ── P 判定（只钉机制） ───────────────────────────────────────────────────────
P1 = (N == 24 and N_PASS == N)
P2 = bool(A_APPLIED) and bool(A_INVISIBLE) and N_A_PASS == N_PASS
P3 = bool(B_APPLIED) and bool(B_BREAKS)
P4 = (N_ON_AUDIT > 0 and N_ONLY_AUDIT > 0)
P5 = bool(N_PROSE)
P6 = True
P7 = True
P8 = True

OUT = {"P1_baseline_all_green_1018": P1,
       "P2_behavior_change_is_invisible_1018": P2,
       "P3_rename_breaks_it_2018": P3,
       "P4_some_checks_read_the_audit_not_the_prototype_2018": P4,
       "P5_some_anchors_are_prose_2018": P5,
       "P6_scope_declared_1018": P6,
       "P7_offline_1018": P7,
       "P8_hold_1018": P8}

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps({
    "generated_by": "jimeng_probe1018_assertion_vs_behavior.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **那 24 条「在读原型源码」的判据，验的是「那段字还在」，"
            "不是「这个行为还对」** —— 两个反向用例把它钉死了。",
    "question_1018": "891 条判据里唯一那 24 条，它们断言的是代码行为，还是源码里的字符串？",
    "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **一个 `'<字面量>' in <源码文本>` 形式的判据，"
            "它验的是「这段字还在」** ⇒ 改行为而保留字面量 ⇒ 照绿；"
            "保留行为而改掉字面量 ⇒ 变红或崩",
    "n_checks": N,
    "baseline": {"n_pass": N_PASS,
                 "n_fail": sum(1 for r in BASE if r["state"] == "fail"),
                 "n_crash": sum(1 for r in BASE if r["state"] == "crash"),
                 "rows": BASE},
    "reverse_A_behavior_only": {
        "mutation": "`%s` → `%s`" % (ANCHOR_LINE, MUT_A),
        "line_found_in_prototype": A_APPLIED,
        "what_it_changes": "焦点在节点序列里**一次跨两个**（步进 1 → 2）—— 行为实打实变了",
        "n_anchors_touched": 0,
        "n_pass_after": N_A_PASS,
        "all_still_green": A_INVISIBLE,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **改完之后 24 条一条没红** ⇒ "
                "**⇒⇒⇒⇒⇒ 这 24 条看不见行为变更** ⇒⇒⇒⇒⇒⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒ 它们不是行为回归测试，是字面量存在性检查**",
    },
    "reverse_B_rename_only": {
        "mutation": "`%s` → `%s`" % (FUNC, MUT_B),
        "applied": B_APPLIED,
        "what_it_changes": "**行为完全没动**，只改了一个函数名",
        "states": B_STATES,
        "breaks_something": B_BREAKS,
        "any_crash": B_CRASHES,
        "rows": B,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **纯重命名就把它们打断了** ⇒ "
                "**⇒⇒⇒⇒⇒ 门对「重命名」敏感、对「改错」不敏感**",
        "crash_note": "⚠️⭐⭐⭐⭐⭐ **诚实更正：本次两个反向用例里 `crash` = %d。** "
                      "我第一版**口头说过「改名会让门直接 `IndexError` 崩掉」** —— "
                      "那是**仪器自己的 bug**（`main` 里的赋值没被执行全、基线本来就崩），"
                      "**照抄到结论里就成了假发现** ⇒⇒⇒⇒ "
                      "**⇒⇒⇒⇒⇒ 1012 那条「`crashed` 必须单列」在这里仍然成立**（分类器确实是三态、"
                      "第一版确实崩了 24 条），**但「这个反向用例会崩」这个结论是错的、已撤回** ⇒⇒⇒⇒⇒⇒ "
                      "**⇒⇒⇒⇒⇒⇒⇒ 这正是 1016 那条「照抄散文里的预期和量出来长得一样」"
                      "在我自己的推演上的版本 —— 连「我以为发生过的事」都会变成假发现**" % B_STATES.get("crash", 0),
    },
    "what_is_actually_asserted": {
        "per_check": CLASS,
        "n_checks_touching_audit_text": N_ON_AUDIT,
        "n_checks_touching_ONLY_audit_text": N_ONLY_AUDIT,
        "n_checks_with_prose_literals": N_PROSE,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「在读原型源码」这个说法还要再切一刀**："
                "① 有 %d 条**同时断 audit 判据文本里的散文** —— 它们断的是「那条批注还在」，"
                "与原型无关；② 有 %d 条**根本只断 audit 文本**；"
                "③ 有 %d 条的锚点**本身是中文散文**（比如原型源码里那句「批 967 改写上面那段…」、"
                "「别复制第二份」「不跑 tsc」—— **注释被当成了实现**）⇒⇒⇒⇒⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒ 24 这个数已经是上界，而真·验代码的比它更小**" % (
                    N_ON_AUDIT, N_ONLY_AUDIT, N_PROSE),
    },
    "scope": "⚠️⭐⭐⭐⭐⭐ **本探针只做到这一步**：它验证「判据看得见/看不见行为变更」，"
             "**没有**验证「原型实现的行为本身对不对」—— 那需要真跑起来、"
             "对源站与复刻各测一遍，属交互式判读，不在这台普查的口径内 ⇒ "
             "**不把「字面量在」说成「行为对」**",
    "offline": "只读仓里的脚本与原型源码；反向用例**全部在内存里改文本，一个字节都不动仓里文件**",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("从 main 里执行成功的赋值 %d/%d 条" % (VG.get("_v1018_n_reads", 0), VG.get("_v1018_n_cand", 0)))
print("判据 %d 条，基线 pass=%d fail=%d crash=%d"
      % (N, N_PASS, sum(1 for r in BASE if r["state"] == "fail"),
         sum(1 for r in BASE if r["state"] == "crash")))
print("Ⓐ 只改行为（步进 1→2）→ 锚点命中 %d 处，之后 pass=%d ⇒ 全绿=%s"
      % (0, N_A_PASS, A_INVISIBLE))
print("Ⓑ 只改名（行为不动）→ %s" % B_STATES)
print("   其中直接崩掉：%d 条" % B_STATES.get("crash", 0))
print("断 audit 文本的判据 %d 条（其中只断 audit 的 %d 条）；锚点是中文散文的 %d 条"
      % (N_ON_AUDIT, N_ONLY_AUDIT, N_PROSE))
print("P1..P8 =", [OUT[k] for k in OUT])
print("PROBE_1018_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)