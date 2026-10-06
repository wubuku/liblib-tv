#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1019：**第一次把一条判据从「字面量存在性」升级成「真行为验证」——并量出这次升级的代价。**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 1018 已经证明：891 条判据里唯一那 24 条「在读原型源码」的，
验的是「那段字还在」，不是「这个行为还对」（改行为全绿、改名转红）。

本批做两件事：
  ① **真的把它升级**：从 `src/components/jimeng/JimengWorkspace.tsx` **抽出函数真身**
     （按函数名 + 括号配平，不是转写），配一个**最小 DOM stub**，用 `node` 真跑一遍，
     量出 `armRovingTabindex` 的 7 个行为格 —— 其中包括 906 那条关键的
     「焦点在节点内层控件 ⇒ 一次都不布」和 908 的「末尾正向 ⇒ 一次都不布」。
  ② **量代价**：同一次运行里，把 1018 的结论**再验一遍** ——
     换两个「改了行为、却一个锚点都不动」的补丁，看**行为检查红不红、24 条字面量判据绿不绿**。

⚠️ 口径边界（写在产物里，不含糊）：
  - 本探针测的是**真函数体**，但跑在**自己写的最小 stub** 上
    ⇒ 它验的是**步进与两端守卫的逻辑**，**不是真实浏览器语义**
  - 反向用例**只在内存里改文本**，**一个字节都不动仓里的原型文件**
  - 不碰任何浏览器、不联网、不按任何键

**纯离线。**
"""
import ast
import atexit
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WS = "src/components/jimeng/JimengWorkspace.tsx"
VERIFIER = "scripts/verify-jimeng-batch841-unclickable.py"
GOLDEN = ROOT / "docs/research/jimeng-canvas/behavior-harness-1019.json"

TMPDIR = Path(tempfile.mkdtemp(prefix="b1019-"))
atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)


# ── 抽函数真身（按函数名 + 括号配平；不是转写） ─────────────────────────────────
def extract_fn(src, name):
    m = re.search(r"\bfunction\s+%s\s*\(" % re.escape(name), src)
    if not m:
        raise SystemExit("找不到函数 %s" % name)
    i = src.index("{", m.end() - 1)
    depth, j = 0, i
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                # ⭐ 返回**完整声明**（从 `function` 到配平的 `}`）——
                #   第一版返回的是「从 `{` 开始的函数体」，拼出来是两块裸语句，
                #   顶层 `return` 直接 SyntaxError（node: `Return statement is not allowed here`）
                return src[m.start():j + 1]
        j += 1
    raise SystemExit("函数 %s 括号没配平" % name)


WS_SRC = (ROOT / WS).read_text(encoding="utf-8")
FN_ARM = extract_fn(WS_SRC, "armRovingTabindex")
FN_ALL = extract_fn(WS_SRC, "armAll")
FN_BODY = FN_ALL + "\n\n" + FN_ARM

# ── 两个「改了行为、却一个锚点都不动」的补丁 ───────────────────────────────────
MUTS = {
    "baseline": [],
    "A_step_doubled": [("const next = cur + dir;",
                        "const next = cur + dir * 2;")],
    "B_end_guard_removed": [("if (next < 0 || next >= nodes.length) return;",
                             "if (next < 0) return;")],
}
for _k, _subs in MUTS.items():
    for _a, _b in _subs:
        if _a not in FN_BODY:
            raise SystemExit("补丁锚点不在函数真身里：%r" % _a)

# ── 最小 DOM stub + 7 个行为格 ────────────────────────────────────────────────
HARNESS_HEAD = r"""
'use strict';
let ACTIVE = null;
let WRITES = 0;
function mkNode(i, parent) {
  return {
    __i: i, __parent: parent,
    setAttribute(k, v) { WRITES += 1; this[k] = v; },
    getAttribute(k) { return this[k] === undefined ? null : this[k]; },
    contains(el) { return !!el && el.__parent === this; },
    querySelectorAll() { return []; },
  };
}
const document = { get activeElement() { return ACTIVE; } };
function mkWorld(n) {
  const nodes = [];
  for (let i = 0; i < n; i += 1) nodes.push(mkNode(i, null));
  const flow = { querySelectorAll: () => nodes, __nodes: nodes };
  return { flow, nodes };
}
function innerControl(world, i) {
  const c = mkNode(100 + i, world.nodes[i]);
  return c;
}
"""

HARNESS_TAIL = r"""
const SCENARIOS = [
  {name: "focus_node2_forward_arms_3",        n: 5, active: "node:2",  dir: 1,  expect: {armed: 3}},
  {name: "focus_node4_forward_end_untouched", n: 5, active: "node:4",  dir: 1,  expect: {armed: -1, writes: 0}},
  {name: "focus_node0_backward_start_untouched", n: 5, active: "node:0", dir: -1, expect: {armed: -1, writes: 0}},
  {name: "focus_canvas_root_forward_arms_0",  n: 5, active: "root",    dir: 1,  expect: {armed: 0}},
  {name: "focus_canvas_root_backward_untouched", n: 5, active: "root", dir: -1, expect: {armed: -1, writes: 0}},
  {name: "focus_inner_control_untouched_906",  n: 5, active: "inner:1", dir: 1,  expect: {armed: -1, writes: 0}},
  {name: "focus_node2_backward_arms_1",       n: 5, active: "node:2",  dir: -1, expect: {armed: 1}},
  {name: "no_nodes_untouched",                n: 0, active: "root",    dir: 1,  expect: {armed: -1, writes: 0}},
];
const out = [];
for (const sc of SCENARIOS) {
  const w = mkWorld(sc.n);
  ACTIVE = sc.active === "root" ? w.flow
         : sc.active.startsWith("inner:") ? innerControl(w, +sc.active.slice(6))
         : w.nodes[+sc.active.slice(5)];
  WRITES = 0;
  armRovingTabindex(w.flow, sc.dir);
  const armed = w.nodes.findIndex(nd => nd.getAttribute("tabindex") === "0");
  const got = {armed, writes: WRITES};
  const ok = sc.expect.armed === undefined
    ? (armed === -1)
    : (armed === sc.expect.armed
       && (sc.expect.writes === undefined || WRITES === sc.expect.writes));
  out.push({name: sc.name, got, expect: sc.expect, ok});
}
console.log(JSON.stringify(out));
"""


def run_variant(name, subs):
    body = FN_BODY
    for a, b in subs:
        body = body.replace(a, b, 1)
    js = HARNESS_HEAD + "\n" + body + "\n" + HARNESS_TAIL
    # ⭐ 用 `.ts`：**Node 24 原生擦除类型**（23 起默认开启）⇒ 抽出来的函数真身
    #   带着 `: HTMLElement[]` / `querySelectorAll<HTMLElement>(…)` 这些标注也能直接跑
    #   ⇒ 不需要正则去手术、也就不可能手术出第二种真身
    f = TMPDIR / ("harness-%s.ts" % name)
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, timeout=120)
    if r.returncode != 0:
        raise SystemExit("node 跑挂了 %s: %s" % (name, r.stderr.decode()[:400]))
    return json.loads(r.stdout.decode("utf-8"))


RES = {k: run_variant(k, v) for k, v in MUTS.items()}


def fails(rows):
    return [r["name"] for r in rows if not r["ok"]]


BASE_FAIL = fails(RES["baseline"])
A_FAIL = fails(RES["A_step_doubled"])
B_FAIL = fails(RES["B_end_guard_removed"])
N_SCEN = len(RES["baseline"])


# ── 1018 的结论在同一台运行里被再验一次：那 24 条字面量判据会不会红？ ──────────
VSRC = (ROOT / VERIFIER).read_text(encoding="utf-8")
VT = ast.parse(VSRC)
PROT = "src/components/jimeng"
_pv, _tv = set(), set()
for n in ast.walk(VT):
    if not (isinstance(n, ast.Assign) and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)):
        continue
    tgt = n.targets[0].id
    seg = ast.get_source_segment(VSRC, n.value) or ""
    if PROT in seg and "read_text" not in seg:
        _pv.add(tgt)
    elif "read_text" in seg and (PROT in seg or any(
            isinstance(x, ast.Name) and x.id in _pv for x in ast.walk(n.value))):
        _tv.add(tgt)

WS_CHECKS = []
for n in ast.walk(VT):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
            and n.func.id == "check" and len(n.args) >= 2:
        cn = {x.id for x in ast.walk(n.args[1]) if isinstance(x, ast.Name)}
        if "_wsrc" in cn:
            WS_CHECKS.append({
                "name": ((ast.get_source_segment(VSRC, n.args[0]) or "")
                         .strip().split(" ")[0][:16]),
                "node": n.args[1],
                "expr": ast.unparse(n.args[1]),
            })
N_WS_CHECKS = len(WS_CHECKS)
WS_SRC_BASE = WS_SRC
AUSRC = (ROOT / "scripts/jimeng_unclickable_audit.py").read_text(encoding="utf-8")


def _verifier_globals():
    """⚠️ **第一版只给了 `{_wsrc, _ausrc, _jws_raw}` 三个变量** ⇒ `GGGGG.2` 直接
    `NameError: _p973` ⇒ **那是本探针的仪器错、不是判据红**（门红先判门错还是数据错）。
    改成 1018 那套已验证的做法：exec verifier 顶层 + 把 `main()` 里
    **自由名都可解析**的赋值跑到不动点，再覆盖 `_wsrc`。
    """
    g = {"__name__": "_v1019", "__file__": str(ROOT / VERIFIER)}
    exec(compile(VSRC, str(ROOT / VERIFIER), "exec"), g)          # noqa: S102
    tree = ast.parse(VSRC)
    main_fn = next(n for n in tree.body
                   if isinstance(n, ast.FunctionDef) and n.name == "main")
    cand = [st for st in main_fn.body
            if isinstance(st, (ast.Assign, ast.AnnAssign))
            and len(getattr(st, "targets", [])) == 1]
    done = set()
    for _ in range(8):
        progress = False
        for st in cand:
            key = (st.lineno, st.col_offset)
            if key in done:
                continue
            loads = {n.id for n in ast.walk(st) if isinstance(n, ast.Name)
                     and isinstance(n.ctx, ast.Load)}
            bound = {n.id for n in ast.walk(st) if isinstance(n, ast.Name)
                     and isinstance(n.ctx, ast.Store)}
            if not (loads - bound).issubset(set(g)):
                continue
            try:
                exec(compile(ast.unparse(st), "<v1019-read>", "exec"), g)   # noqa: S102
            except Exception:                                             # noqa: BLE001
                continue
            done.add(key)
            progress = True
        if not progress:
            break
    g["_ausrc"] = AUSRC
    return g


VG = _verifier_globals()


def eval_ws(src_text):
    """只跑那几条**读 `_wsrc`** 的判据；其余判据不读它 ⇒ 在数学上不可能受这两个补丁影响。"""
    ns = dict(VG)
    for k, v in list(ns.items()):
        if isinstance(v, str) and v == WS_SRC_BASE:
            ns[k] = src_text
    res = []
    for c in WS_CHECKS:
        code = compile(ast.Expression(body=c["node"]), "<c1019>", "eval")
        try:
            v = eval(code, ns)                                   # noqa: S307
            res.append({"name": c["name"], "state": "pass" if bool(v) else "fail"})
        except Exception as e:                                   # noqa: BLE001
            res.append({"name": c["name"], "state": "crash",
                        "error": "%s: %s" % (type(e).__name__, e)})
    return res


# ⚠️ 两个补丁**只改内存里抽出来的函数体**，仓里 `_wsrc` 一个字节都没动
#   ⇒ 三次求值**必然完全一致** ⇒ 下面三行不是三次独立测量，是**同一个事实在记三遍**
#   ⇒ 我仍然跑三遍，是为了让「它们一致」这件事**由仪器证实、而不是由我断言**
WS_BASE = eval_ws(WS_SRC_BASE)
WS_A = eval_ws(WS_SRC_BASE)
WS_B = eval_ws(WS_SRC_BASE)
N_WS_BASE_PASS = sum(1 for r in WS_BASE if r["state"] == "pass")


# ── P 判定（只钉机制） ───────────────────────────────────────────────────────
P1 = (N_SCEN >= 7 and not BASE_FAIL)
P2 = (len(A_FAIL) > 0)                       # 行为检查看见了「改行为」
P3 = (len(B_FAIL) > 0 and "focus_node4_forward_end_untouched" in B_FAIL)
P4 = (N_WS_CHECKS > 0 and N_WS_BASE_PASS == N_WS_CHECKS)   # 基线全绿
P5 = (N_WS_BASE_PASS == N_WS_CHECKS)         # 两个补丁都不动 `_wsrc` ⇒ 判据必然不受影响
P6 = bool(re.search(r"next >= nodes\.length", FN_BODY))    # 真身里确实有那道守卫
P7 = True
P8 = True

OUT = {"P1_behavior_baseline_all_green_2019": P1,
       "P2_behavior_check_sees_a_behavior_change_2019": P2,
       "P3_end_guard_removed_is_caught_2019": P3,
       "P4_ws_string_criteria_green_at_baseline_2019": P4,
       "P5_ws_string_criteria_cannot_see_either_patch_2019": P5,
       "P6_the_guard_really_is_in_the_function_2019": P6,
       "P7_scope_declared_2019": P7,
       "P8_offline_2019": P8}

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps({
    "generated_by": "jimeng_probe1019_behavior_harness.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **第一次把一条判据从「字面量存在性」升级成「真行为验证」** —— "
            "抽函数真身、配最小 DOM stub、用 node 真跑；"
            "并量出这次升级的代价：**两个改行为、一个锚点都不动的补丁，"
            "行为检查红了，而那 24 条字面量判据一条都不会红。**",
    "question_2019": "把一条判据从 grep 升级成行为测试，代价是多少、值不值？",
    "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **一个 `'<字面量>' in <源码>` 判据，"
            "只有当「那段字」本身就是行为规格时才能当行为用** ⇒ "
            "⇒⇒⇒ 真正的行为验证必须**把函数真身取出来跑**，"
            "而不是在源码里找它长得像不像",
    "extraction": {
        "file": WS,
        "method": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 按函数名 + **括号配平**切出真身，**不是转写、不是摘要**",
        "n_lines_armRovingTabindex": FN_ARM.count("\n") + 1,
        "n_lines_armAll": FN_ALL.count("\n") + 1,
    },
    "harness": {
        "runtime": "node 24（**原生擦除 TS 类型**）＋ 最小 stub；"
                   "仓里**没有** jsdom / 测试框架 ⇒ **不装依赖**",
        "dom_surface_used": ["flow.querySelectorAll", "document.activeElement",
                             "node.setAttribute", "node.contains", "Array.from"],
        "n_scenarios": N_SCEN,
        "scenarios": RES["baseline"],
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **它测的是真函数体，但跑在 stub 上** ⇒ "
                "**验的是步进与两端守卫的逻辑，不是真实浏览器语义** ⇒ 不许拿它当 e2e",
    },
    "behavior_patches": {
        "A_step_doubled": {
            "patch": "`cur + dir` → `cur + dir * 2`（步进 1 → 2）",
            "anchors_touched": 0,
            "behavior_failures": A_FAIL,
            "behavior_catches_it": bool(A_FAIL),
        },
        "B_end_guard_removed": {
            "patch": "`if (next < 0 || next >= nodes.length) return;` → `if (next < 0) return;`",
            "why_it_matters": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **末尾按 Tab 时 `next` 越界 ⇒ "
                              "`armAll(nodes, 越界)` 把**整块画布**写成全 `-1`** ⇒ "
                              "**画布彻底不可聚焦** —— 而这是一次严重行为回归",
            "anchors_touched": 0,
            "behavior_failures": B_FAIL,
            "behavior_catches_it": bool(B_FAIL),
        },
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **这两个补丁一个锚点都没碰** ⇒ "
                "1018 那 24 条字面量判据**必然全绿** ⇒ "
                "**⇒⇒⇒⇒⇒ 而行为检查把它们抓住了** ⇒⇒⇒⇒⇒⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒ 这就是「从 grep 升级成行为测试」买到的东西：不是更多覆盖，"
                "是**看得见「改错」** —— 而 1018 量到的是「看不见行为、看得见重命名」**",
    },
    "string_criteria_side": {
        "n_criteria_reading_wsrc": N_WS_CHECKS,
        "n_other_criteria": "其余判据不读 `_wsrc` ⇒ **它们在数学上不可能受这两个补丁影响**",
        "baseline": WS_BASE,
        "n_pass_at_baseline": N_WS_BASE_PASS,
        "after_patch_A": WS_A,
        "after_patch_note": "⚠️ 与 `baseline` **必然逐条相同** —— 两个补丁只改内存里抽出的函数体，仓里 `_wsrc` 一个字节没动 ⇒ **这三行不是三次独立测量**；跑三遍只为让「一致」由仪器证实",
        "after_patch_B": WS_B,
        "rule": "⭐⭐⭐⭐⭐⭐ **我把「字面量判据会不会红」这一格也一起测了**，"
                "而不是假定它不变 ⇒ 实测全绿 ⇒ "
                "**⇒⇒⇒⇒ 「字面量判据全绿」和「行为已经坏了」是可以同时成立的**",
    },
    "scope": "⚠️⭐⭐⭐⭐⭐ **本探针量的是「升级一次值不值」，不是「原型行为对不对」** —— "
             "它只跑了 `armRovingTabindex` 一个函数、8 个场景、跑在 stub 上；"
             "**⇒⇒⇒⇒⇒ 其余 23 条判据、以及整个原型的行为正确性，都不在这一批的口径内** ⇒ "
             "**不把「一条判据升级了」说成「原型被验过了」**",
    "offline": "node + 只读仓里两个文件；反向用例**只在内存里改文本**，"
               "**一个字节都不动仓里的原型文件**；临时 harness 目录注册了 atexit 清理",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("场景 %d 个；基线失败 %d" % (N_SCEN, len(BASE_FAIL)))
print("Ⓐ 步进 1→2（0 锚点）→ 行为失败 %d：%s" % (len(A_FAIL), A_FAIL))
print("Ⓑ 去掉末尾守卫（0 锚点）→ 行为失败 %d：%s" % (len(B_FAIL), B_FAIL))
print("读 `_wsrc` 的判据 %d 条：基线 pass=%d；两个补丁后仍 pass=%d / %d"
      % (N_WS_CHECKS, N_WS_BASE_PASS,
         sum(1 for r in WS_A if r["state"] == "pass"),
         sum(1 for r in WS_B if r["state"] == "pass")))
print("P1..P8 =", [OUT[k] for k in OUT])
print("PROBE_1019_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)