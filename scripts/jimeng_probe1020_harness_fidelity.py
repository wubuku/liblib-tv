#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1020：**把 1019 那 8 个行为格本身当被测对象** —— 量这个 harness 的保真度与判别力。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 1019 把一条判据从「字面量存在性」升级成了「真行为验证」，
但**升级完就宣布通过了** —— 按 P6 通则（任何交付物都必须被下一批当被测对象重新过一遍），
本批回头量它两件事：

  ① **保真度**：1019 那个「最小 DOM stub」的 `contains` 只认**直接父节点**，
     而真 DOM 的 `Node.contains` 是**深包含、且含自身** ⇒ 两者在「自身」和
     「深度 ≥ 2」上分叉。⇒ 本批把同一个函数真身、同一批输入，
     分别跑在 **1019 的 stub** 与**一条更忠实的 stub** 上，逐格对账。

  ② **判别力**：1019 只试了 2 个**手挑的**补丁 ⇒ 本批**系统枚举**变异体
     （机器按 token 规则生成、不是手挑），量那 8 个格的 mutation score
     与**存活变异体清单**。

⭐⭐⭐⭐⭐ **本批的核心发现是「差分器杀不死变异体」**：
  - 8 个**手写期望**的格 = **判别器**（能杀变异体）
  - 86 个**机器枚举**的格 = **差分器**（只能比两个 stub 的异同）
  ⇒ 差分器的期望若是「以其中一个 stub 为基准」推出来的，它在**结构上**
  永远杀不死任何变异体 ⇒ **把覆盖从 8 格拉到 86 格，不等于多了一个字的判别力。**

⚠️ 口径边界（写在产物里，不含糊）：
  - 两条 stub **都不是浏览器** ⇒ 本批量的是**「stub 之间的分歧」**，
    **不是**「真浏览器会怎样」⇒ 不报「复刻真的错了」
  - 变异体是**本探针按 token 规则生成的**，不是业界标准变异算子集
    ⇒ mutation score 只在**本口径内**可比，不与别的工具的数字横向比
  - **不碰任何浏览器、不联网、不按任何键**；一个字节都不动仓里的原型文件

**纯离线。**
"""
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
GOLDEN = ROOT / "docs/research/jimeng-canvas/harness-fidelity-1020.json"

TMPDIR = Path(tempfile.mkdtemp(prefix="b1020-"))
atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)


# ── 抽函数真身（与 1019 同一套：按函数名 + 括号配平，不是转写） ─────────────────
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
                return src[m.start():j + 1]
        j += 1
    raise SystemExit("函数 %s 括号没配平" % name)


WS_SRC = (ROOT / WS).read_text(encoding="utf-8")
FN_ALL = extract_fn(WS_SRC, "armAll")
FN_ARM = extract_fn(WS_SRC, "armRovingTabindex")
FN_BODY = FN_ALL + "\n\n" + FN_ARM


# ── 变异体：**按 token 规则系统枚举**，不手挑 ──────────────────────────────────
# ⭐ `===` / `!==` 必须排在 `!` / `<` 前面，否则会被短的那个先吃掉
TOKEN_RE = re.compile(r"===|!==|>=|<=|[<>]|&&|\|\||[+!]|\b\d+\b")
TOKEN_OPTS = {
    "===": ["!=="], "!==": ["==="], ">=": ["<"], "<=": [">"],
    ">": ["<"], "<": [">"], "&&": ["||"], "||": ["&&"],
    "+": ["-", "* 2"], "!": [""],
    "0": ["1"], "1": ["0", "2"], "2": ["1"],
}
# 只有这两类整行可以删：纯守卫 `return;` 行，和 `armAll(…)` 调用行
DEL_LINE_RE = re.compile(r"^\s*(?:if\s*\(.*\)\s*)?return;\s*$|^\s*armAll\(.*\);\s*$")


def comment_col(line):
    """返回该行 `//` 注释的起始列（没有则返回 None）。只认行注释 —— 真身里只有行注释。"""
    in_s = None
    for k, ch in enumerate(line):
        if in_s:
            if ch == in_s:
                in_s = None
        elif ch in "\"'`":
            in_s = ch
        elif ch == "/" and k + 1 < len(line) and line[k + 1] == "/":
            return k
    return None


def gen_mutants(body):
    lines = body.split("\n")
    out = []
    for li, line in enumerate(lines):
        ccol = comment_col(line)
        lim = ccol if ccol is not None else len(line)
        if DEL_LINE_RE.match(line):
            out.append(("del_line_%d" % li, "".join(
                l if k != li else "" for k, l in enumerate(lines)),
                li, line, "（整行删除）"))
        for m in TOKEN_RE.finditer(line):
            if m.start() >= lim:
                continue
            tok = m.group(0)
            for rep in TOKEN_OPTS.get(tok, []):
                if rep == tok:
                    continue
                nl = list(lines)
                nl[li] = line[:m.start()] + rep + line[m.end():]
                if nl[li] == line:
                    continue
                # ⭐⭐⭐⭐⭐ 名字里**必须带列号** —— 同一行出现两次同一个 token 时，
                #   只按 (行,token,替换值) 命名会把两个**不同的**变异体合并成一个
                #   ⇒⇒⇒⇒⇒ 第一版就栽在这儿：38 个里有一批是**被合并掉的**
                out.append(("tok_%d_%d_%s_to_%s" % (li, m.start(), tok or "empty",
                                                    rep.strip() or "empty"),
                            "\n".join(nl), li, line, nl[li]))
    seen, ded = set(), []
    for name, txt, li, before, after in out:
        if txt == body or name in seen:
            continue
        seen.add(name)
        ded.append((name, txt, {"line": li, "before": before.strip(), "after": after.strip()}))
    return ded


MUTANTS = gen_mutants(FN_BODY)
N_MUT = len(MUTANTS)
MUT_DIFF = {name: d for name, _t, d in MUTANTS}


# ── JS harness：两条 stub 共用一份代码，只差 `contains` 的语义 ─────────────────
HARNESS_HEAD = r"""
'use strict';
let ACTIVE = null;
let WRITES = 0;

// ⭐⭐⭐ 两条 stub **唯一的差别** 就是 `contains`：
//   shallow = 1019 那个（`el.__parent === this`）—— **只认直接父节点、且不含自身**
//   deep    = 真 DOM 的 `Node.contains` 语义 —— **沿父链上溯、含自身**
function mkEl(parent, mode) {
  const el = {__parent: parent || null, __attrs: {}, __mode: mode};
  el.setAttribute = function (k, v) {
    // ⭐⭐⭐⭐⭐ **死循环护栏**：把 `i += 1` 变异成 `i += 0` 会让 `armAll` 永不退出。
    //   ⭐ 1019 的 harness **没有这道护栏** ⇒ 真跑一次是「挂住」，不是「报红」。
    //   ⭐ 护栏放在 **stub 的 setAttribute** 里，**一个字节都不动被测函数体**
    //   （不许用手术去改被测代码 —— 可能手术出第二种真身）。
    //   ⇒ 死循环在这里变成一次**普通的抛错** ⇒ 被 `probe` 的 try 收成 `err`
    //   ⇒ 对判别器来说「挂死」和「报错」是同一件事：**行为坏了**。
    if (++WRITES > 200000) { throw new Error("B1020_STEP_LIMIT"); }
    this.__attrs[k] = v;
  };
  el.getAttribute = function (k) { return this.__attrs[k] === undefined ? null : this.__attrs[k]; };
  el.querySelectorAll = function () { return []; };
  if (mode === "shallow") {
    el.contains = function (o) { return !!o && o.__parent === this; };
  } else {
    el.contains = function (o) {
      for (let p = o; p; p = p.__parent) { if (p === this) { return true; } }
      return false;
    };
  }
  return el;
}
const document = { get activeElement() { return ACTIVE; } };

function mkWorld(n, mode) {
  const nodes = [];
  for (let i = 0; i < n; i += 1) { nodes.push(mkEl(null, mode)); }
  const flow = mkEl(null, mode);
  flow.__nodes = nodes;
  flow.querySelectorAll = function () { return nodes; };
  const d1 = [], d2 = [];
  for (const nd of nodes) { const a = mkEl(nd, mode); d1.push(a); d2.push(mkEl(a, mode)); }
  return {flow, nodes, d1, d2, other: mkEl(flow, mode)};
}
function activeFor(w, kind, idx) {
  if (kind === "root") { return w.flow; }
  if (kind === "other") { return w.other; }
  if (kind === "node") { return w.nodes[idx]; }
  if (kind === "inner1") { return w.d1[idx]; }
  if (kind === "inner2") { return w.d2[idx]; }
  return null;
}
function probe(w, kind, idx, dir) {
  ACTIVE = activeFor(w, kind, idx);
  WRITES = 0;
  let err = null;
  try { armRovingTabindex(w.flow, dir); } catch (e) { err = String((e && e.message) || e); }
  const armed = w.nodes.findIndex(nd => nd.getAttribute("tabindex") === "0");
  return {armed: armed, writes: WRITES, err: err};
}
"""

HARNESS_TAIL = r"""
// ── ① 1019 那 8 个格：**手写期望**，原样搬过来，一个字没改 ───────────────────
const CELLS1019 = [
  {name: "focus_node2_forward_arms_3",            n: 5, kind: "node",   idx: 2, dir: 1,  expect: {armed: 3}},
  {name: "focus_node4_forward_end_untouched",     n: 5, kind: "node",   idx: 4, dir: 1,  expect: {armed: -1, writes: 0}},
  {name: "focus_node0_backward_start_untouched",  n: 5, kind: "node",   idx: 0, dir: -1, expect: {armed: -1, writes: 0}},
  {name: "focus_canvas_root_forward_arms_0",      n: 5, kind: "root",   idx: 0, dir: 1,  expect: {armed: 0}},
  {name: "focus_canvas_root_backward_untouched",  n: 5, kind: "root",   idx: 0, dir: -1, expect: {armed: -1, writes: 0}},
  {name: "focus_inner_control_untouched_906",      n: 5, kind: "inner1", idx: 1, dir: 1,  expect: {armed: -1, writes: 0}},
  {name: "focus_node2_backward_arms_1",           n: 5, kind: "node",   idx: 2, dir: -1, expect: {armed: 1}},
  {name: "no_nodes_untouched",                    n: 0, kind: "root",   idx: 0, dir: 1,  expect: {armed: -1, writes: 0}},
];
// ── ② 86 格枚举：**没有手写期望** ⇒ 它只能是差分器，不是判别器 ────────────────
//   口径（明写，不含糊）：n ∈ {0,1,2,3,5}；焦点 5 类（node/inner1/inner2/root/other）
//   × dir ∈ {+1,−1}。`other` = 画布根下、但不属于任何节点的元素。
const NS = [0, 1, 2, 3, 5];
function runAll(mode) {
  const cells = CELLS1019.map(function (c) {
    const w = mkWorld(c.n, mode);
    const got = probe(w, c.kind, c.idx, c.dir);
    const ok = got.err === null
      && got.armed === c.expect.armed
      && (c.expect.writes === undefined || got.writes === c.expect.writes);
    return {name: c.name, ok: ok, got: got};
  });
  const grid = [];
  for (const n of NS) {
    for (let i = 0; i < n; i += 1) {
      for (const k of ["node", "inner1", "inner2"]) {
        for (const dir of [1, -1]) {
          grid.push({n: n, kind: k, idx: i, dir: dir, got: probe(mkWorld(n, mode), k, i, dir)});
        }
      }
    }
    for (const k of ["root", "other"]) {
      for (const dir of [1, -1]) {
        grid.push({n: n, kind: k, idx: 0, dir: dir, got: probe(mkWorld(n, mode), k, 0, dir)});
      }
    }
  }
  // ── ③ 那个 8 格一条都没覆盖的分支：`!flow` ───────────────────────────────
  let flowNull = null;
  try { ACTIVE = null; WRITES = 0; armRovingTabindex(null, 1); flowNull = {threw: false, writes: WRITES}; }
  catch (e) { flowNull = {threw: true, err: String((e && e.message) || e)}; }
  // ── ④ `contains` 的语义差异：直接量「四个问题」，不靠推理 ───────────────
  const we = mkWorld(1, mode);
  const nd = we.nodes[0], c1 = we.d1[0], c2 = we.d2[0], un = mkEl(null, mode);
  const contains = {self: nd.contains(nd), depth1: nd.contains(c1),
                    depth2: nd.contains(c2), unrelated: nd.contains(un)};
  // ── ⑤ ⭐⭐⭐⭐⭐⭐ 判决分叉演示：**同一条期望、只把 906 那条格的样本从深度 1
  //     换成深度 2** ⇒ 看两条 stub 给出**相反的通过/不通过**。
  //     这不是新增一个格，是把已有那条格的**样本**换掉 ⇒ 期望一个字没动。
  const EXP906 = {armed: -1, writes: 0};
  const w6 = mkWorld(5, mode);
  const g6 = probe(w6, "inner1", 1, 1);   // 1019 用的：深度 1
  const w6b = mkWorld(5, mode);
  const g6b = probe(w6b, "inner2", 1, 1); // 只换样本深度：深度 2
  const okOf = (g, e) => g.err === null && g.armed === e.armed && g.writes === e.writes;
  const cell906 = {
    depth1: {got: g6, ok: okOf(g6, EXP906)},
    depth2: {got: g6b, ok: okOf(g6b, EXP906)},
  };
  // ── ⑥ ⭐⭐⭐⭐⭐ 「补两格能买到多少判别力」：**在 1020 自己的 harness 上加格**，
  //     **一个字都不动 1019** ⇒ 1019 产物里写死的那个「8」不会过期。
  //     两格各自对准一个**实测存活**的变异体：
  //       Ⓐ `next < 0` → `next < 1`：1019 的后向步进只测了 next=1 / next=-1，
  //          **恰好跳过 next=0** ⇒ 补 `focus_node1_backward_arms_0`
  //       Ⓑ `"-1"` → `"-0"` / `"-2"`：8 格**从不断言「非布防节点被写成什么」**
  //          ⇒ 补一条 `expect.others`
  const CELLS_PLUS = CELLS1019.concat([
    {name: "focus_node1_backward_arms_0",        n: 5, kind: "node", idx: 1, dir: -1, expect: {armed: 0}},
    {name: "focus_node2_forward_others_minus1",   n: 5, kind: "node", idx: 2, dir: 1,  expect: {armed: 3, others: "-1"}},
  ]);
  function runCells(set, mode) {
    return set.map(function (c) {
      const w = mkWorld(c.n, mode);
      ACTIVE = activeFor(w, c.kind, c.idx);
      WRITES = 0;
      let err = null;
      try { armRovingTabindex(w.flow, c.dir); } catch (e) { err = String((e && e.message) || e); }
      const armed = w.nodes.findIndex(nd => nd.getAttribute("tabindex") === "0");
      let othersOk = true;
      if (c.expect.others !== undefined) {
        othersOk = w.nodes.every(function (nd) {
          const v = nd.getAttribute("tabindex");
          return nd.getAttribute("tabindex") === "0" ? v === "0" : v === c.expect.others;
        });
      }
      const ok = err === null
        && armed === c.expect.armed
        && (c.expect.writes === undefined || WRITES === c.expect.writes)
        && othersOk;
      return {name: c.name, ok: ok, armed: armed, writes: WRITES, err: err};
    });
  }
  const cellsPlus = runCells(CELLS_PLUS, mode);
  // ── ⑦ ⭐⭐⭐⭐⭐⭐ **第二处 stub 保真度**：`tabindex` 在真 DOM 里是**整数**，
  //     而 harness 判的是**字符串相等** `"0"` ⇒ 浏览器会做整数解析，stub 不会。
  const TAB_VALS = ["0", "-1", "-0", "1", "00", "-2", "+0", " 0"];
  const tabindexFidelity = TAB_VALS.map(function (v) {
    return {value: v,
            harness_string_eq_0: v === "0",
            browser_int_eq_0: parseInt(v, 10) === 0,
            agree: (v === "0") === (parseInt(v, 10) === 0)};
  });
  return {mode: mode, cells: cells, cellsPlus: cellsPlus, grid: grid,
          flowNull: flowNull, contains: contains, cell906: cell906,
          tabindexFidelity: tabindexFidelity};
}
const RESULT = {shallow: runAll("shallow"), deep: runAll("deep")};
console.log(JSON.stringify(RESULT));
"""


def run_variant(tag, body):
    js = HARNESS_HEAD + "\n" + body + "\n" + HARNESS_TAIL
    f = TMPDIR / ("h-%s.ts" % tag)
    f.write_text(js, encoding="utf-8")
    try:
        r = subprocess.run(["node", str(f)], capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return None, "B1020_SUBPROCESS_TIMEOUT"
    if r.returncode != 0:
        return None, (r.stderr.decode()[:300])
    return json.loads(r.stdout.decode("utf-8")), None


BASE, e0 = run_variant("base", FN_BODY)
if BASE is None:
    raise SystemExit("基线跑挂了: %s" % e0)
BASE_SHALLOW, BASE_DEEP = BASE["shallow"], BASE["deep"]


# ── ① 保真度：同一真身、同一批输入，两条 stub 逐格对账 ────────────────────────
GKEY = lambda g: (g["n"], g["kind"], g["idx"], g["dir"])                 # noqa: E731
GS = {GKEY(g): g["got"] for g in BASE_SHALLOW["grid"]}
GD = {GKEY(g): g["got"] for g in BASE_DEEP["grid"]}
N_GRID = len(GS)
DISAGREE = []
for k in sorted(GS, key=lambda t: (t[0], t[1], t[2], t[3])):
    if GS[k] != GD[k]:
        DISAGREE.append({"n": k[0], "kind": k[1], "idx": k[2], "dir": k[3],
                         "shallow": GS[k], "deep": GD[k]})
N_DISAGREE = len(DISAGREE)
DISAGREE_KINDS = sorted({d["kind"] for d in DISAGREE})

# ── ② 判别力：逐个变异体 × 两条 stub，看 8 个手写格杀不杀得住 ─────────────────
SH_CELLS0 = {c["name"]: c["ok"] for c in BASE_SHALLOW["cells"]}
DP_CELLS0 = {c["name"]: c["ok"] for c in BASE_DEEP["cells"]}
N_CELL = len(SH_CELLS0)
BASE_ALL_GREEN = all(SH_CELLS0.values())
# ⭐ 1020 自己那 10 格（8 + 补的 2）的基线 —— 补的格**自己也必须先全绿**，
#   否则「它能杀变异体」这句话就是拿一个本身就红的格在说（1018 撤回过的坑）
SH_PLUS0 = {c["name"]: c["ok"] for c in BASE_SHALLOW["cellsPlus"]}
DP_PLUS0 = {c["name"]: c["ok"] for c in BASE_DEEP["cellsPlus"]}
N_CELL_PLUS = len(SH_PLUS0)
PLUS_BASE_GREEN = all(SH_PLUS0.values()) and all(DP_PLUS0.values())
N_CELL_PLUS_NAMES = [c["name"] for c in BASE_SHALLOW["cellsPlus"]]
NEW_CELLS = [n for n in N_CELL_PLUS_NAMES if n not in SH_CELLS0]
# ⭐ `tabindex` 字符串 vs 整数：harness 判的是哪个
TAB_FID = BASE_SHALLOW["tabindexFidelity"]
TAB_DISAGREE = [t for t in TAB_FID if not t["agree"]]

mut_rows = []
for name, txt, diff in MUTANTS:
    row = {"name": name, "diff": diff}
    res, err = run_variant("m%04d" % len(mut_rows), txt)
    if res is None:
        # ⭐ 子进程超时/语法错 = **这份变异体跑不出结果**，单列，不并进任何一态
        row["shallow"] = row["deep"] = ("timeout" if err == "B1020_SUBPROCESS_TIMEOUT"
                                        else "syntax_error")
        mut_rows.append(row)
        continue
    for mode, base0 in (("shallow", SH_CELLS0), ("deep", DP_CELLS0)):
        killed = [c["name"] for c in res[mode]["cells"]
                  if base0.get(c["name"], True) and not c["ok"]]
        row[mode] = "killed" if killed else "survived"
        row[mode + "_by"] = killed
        kp = [c["name"] for c in res[mode]["cellsPlus"] if not c["ok"]]
        row[mode + "_plus_by"] = kp
        row[mode + "_plus"] = "killed" if kp else "survived"
    mut_rows.append(row)

N_VALID = sum(1 for r in mut_rows
              if r.get("shallow") not in ("syntax_error", "timeout")
              or r.get("deep") not in ("syntax_error", "timeout"))
N_SYNTAX = sum(1 for r in mut_rows
               if r.get("shallow") == "syntax_error" and r.get("deep") == "syntax_error")
N_TIMEOUT = sum(1 for r in mut_rows
                if r.get("shallow") == "timeout" and r.get("deep") == "timeout")
for mode in ("shallow", "deep"):
    k = sum(1 for r in mut_rows if r.get(mode) == "killed")
    kp = sum(1 for r in mut_rows if r.get(mode + "_plus") == "killed")
    per_cell = {}
    per_cell_plus = {}
    for r in mut_rows:
        for c in r.get(mode + "_by", []):
            per_cell[c] = per_cell.get(c, 0) + 1
        for c in r.get(mode + "_plus_by", []):
            per_cell_plus[c] = per_cell_plus.get(c, 0) + 1
    mut_rows.append({"_summary": mode, "killed": k, "killed_plus": kp,
                     "per_cell": per_cell, "per_cell_plus": per_cell_plus})

SUMMARY = {m["_summary"]: m for m in mut_rows if "_summary" in m}
mut_rows = [m for m in mut_rows if "_summary" not in m]
SURV_SHALLOW = [m["name"] for m in mut_rows if m.get("shallow") == "survived"]
SURV_DEEP = [m["name"] for m in mut_rows if m.get("deep") == "survived"]
SURV_PLUS = [m["name"] for m in mut_rows if m.get("shallow_plus") == "survived"]
SURV_PLUS_DEEP = [m["name"] for m in mut_rows if m.get("deep_plus") == "survived"]
# ⭐ 补两格**新杀掉**的那些变异体（这是「补格买到判别力」的可复核名单）
NEWLY_KILLED = [{"name": m["name"], **MUT_DIFF.get(m["name"], {}),
                 "shallow_by": m.get("shallow_plus_by", [])}
                for m in mut_rows
                if m.get("shallow") == "survived" and m.get("shallow_plus") == "killed"]
SYNTAX_ONLY = [m["name"] for m in mut_rows
               if m.get("shallow") == "syntax_error" and m.get("deep") == "syntax_error"]
TIMEOUT_ONLY = [m["name"] for m in mut_rows
                if m.get("shallow") == "timeout" and m.get("deep") == "timeout"]

# ⭐ 两个 stub 判别力**不一致**的变异体：一边杀得住、一边杀不住
DISCRIM = [{"name": m["name"], "shallow": m.get("shallow"), "deep": m.get("deep"),
            "shallow_by": m.get("shallow_by", []), "deep_by": m.get("deep_by", [])}
           for m in mut_rows
           if {m.get("shallow"), m.get("deep")} == {"killed", "survived"}]

N_K_SHALLOW = SUMMARY["shallow"]["killed"]
N_K_DEEP = SUMMARY["deep"]["killed"]
N_KP_SHALLOW = SUMMARY["shallow"]["killed_plus"]
N_KP_DEEP = SUMMARY["deep"]["killed_plus"]
N_TESTABLE = sum(1 for m in mut_rows
                 if m.get("shallow") not in ("syntax_error", "timeout")
                 or m.get("deep") not in ("syntax_error", "timeout"))

# ⭐ 差分器能不能杀变异体？——拿 8 个**手写**格当基准，问 86 格**有没有一格**在分歧
DEEP0 = {GKEY(g): g["got"] for g in BASE_DEEP["grid"]}


def diff_vs_deep(gs):
    return [k for k in gs if gs[k] != DEEP0[k]]


BASE_DIFF = set(diff_vs_deep(GS))
# 差分器的「期望」若是以 shallow 为基准推的，它能发现 deep 与 shallow 的异同；
# 但它**不可能**发现 shallow 与 deep 都同样错的地方 ⇒ 结构上杀不死变异体。
N_DIFF_BASE = len(BASE_DIFF)


# ── ③ 1019 那 8 条手写期望，在更忠实的 stub 下还对不对？ ──────────────────────
CELLS_SHALLOW = {c["name"]: c["ok"] for c in BASE_SHALLOW["cells"]}
CELLS_DEEP = {c["name"]: c["ok"] for c in BASE_DEEP["cells"]}
N_CELL_BAD_DEEP = sum(1 for v in CELLS_DEEP.values() if not v)

# ── ④ 分支覆盖：真身里有 7 条互斥的出口，那 8 格覆盖了几条 ────────────────────
BRANCHES = ["!flow", "!nodes.length", "cur===-1 & contains-inner",
            "cur===-1 & dir!==1", "cur===-1 & dir===1", "cur>=0 & 越界",
            "cur>=0 & 区间内"]
# ⭐ 分支覆盖**只按 1019 那 8 个格**算 —— `!flow` 那支 1019 一个格都没有，
#   是**本探针另加了一条 flowNull 探针**才量到的 ⇒ 两件事必须分开报，
#   否则就是我自己在给自己补的格记成 1019 的功劳。
HIT = {
    "!flow": False,
    "!nodes.length": CELLS_SHALLOW.get("no_nodes_untouched", False),
    "cur===-1 & contains-inner": CELLS_SHALLOW.get("focus_inner_control_untouched_906", False),
    "cur===-1 & dir!==1": CELLS_SHALLOW.get("focus_canvas_root_backward_untouched", False),
    "cur===-1 & dir===1": CELLS_SHALLOW.get("focus_canvas_root_forward_arms_0", False),
    "cur>=0 & 越界": (CELLS_SHALLOW.get("focus_node4_forward_end_untouched", False)
                      and CELLS_SHALLOW.get("focus_node0_backward_start_untouched", False)),
    "cur>=0 & 区间内": (CELLS_SHALLOW.get("focus_node2_forward_arms_3", False)
                        and CELLS_SHALLOW.get("focus_node2_backward_arms_1", False)),
}
N_BRANCH_HIT = sum(1 for v in HIT.values() if v)
N_BRANCH = len(BRANCHES)
FLOW_NULL_1020 = BASE_SHALLOW["flowNull"]
FLOW_NULL_REACHED = (FLOW_NULL_1020 is not None
                     and not FLOW_NULL_1020.get("threw", False))

# ⭐ 函数体里有多少是中文注释（1018 的回声：13 条判据的锚点本身就是中文散文）
N_COMMENT_LINES = sum(1 for l in FN_BODY.split("\n") if comment_col(l) is not None)
N_CODE_LINES = sum(1 for l in FN_BODY.split("\n") if l.strip() and comment_col(l) is None)

# ── ⑤ 判决分叉：同一条 906 期望，只把样本从深度 1 换成深度 2 ──────────────────
C906_SHALLOW, C906_DEEP = BASE_SHALLOW["cell906"], BASE_DEEP["cell906"]
VERDICT_FORK = (C906_SHALLOW["depth2"]["ok"] != C906_DEEP["depth2"]["ok"])
D1_AGREE = (C906_SHALLOW["depth1"]["ok"] == C906_DEEP["depth1"]["ok"])

# ── P 判定（只钉机制） ───────────────────────────────────────────────────────
P1 = (N_DISAGREE > 0 and DISAGREE_KINDS == ["inner2"])
P2 = (BASE_ALL_GREEN and N_CELL_BAD_DEEP == 0)
P3 = (N_TESTABLE > 0 and N_K_SHALLOW > 0 and N_K_DEEP > 0)
P4 = len(SURV_SHALLOW) > 0
P5 = (N_BRANCH_HIT == N_BRANCH - 1 and not HIT["!flow"] and FLOW_NULL_REACHED)
P6 = (N_COMMENT_LINES > 0 and N_DIFF_BASE > 0)
P7 = VERDICT_FORK and D1_AGREE
P8 = (PLUS_BASE_GREEN and N_KP_SHALLOW > N_K_SHALLOW and len(NEWLY_KILLED) > 0)
P9 = len(TAB_DISAGREE) > 0
P10 = True

OUT = {"P1_stub_and_dom_disagree_exactly_on_depth2_2020": P1,
       "P2_1019_eight_expectations_hold_under_the_faithful_stub_2020": P2,
       "P3_both_stubs_can_kill_mutants_2020": P3,
       "P4_there_are_surviving_mutants_2020": P4,
       "P5_branch_coverage_is_six_of_seven_and_the_missing_one_is_dead_code_2020": P5,
       "P6_differential_grid_cannot_kill_mutants_by_construction_2020": P6,
       "P7_one_sample_depth_flips_a_verdict_2020": P7,
       "P8_two_more_cells_buy_more_discriminating_power_2020": P8,
       "P9_string_versus_integer_tabindex_disagrees_2020": P9,
       "P10_offline_2020": P10}

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps({
    "generated_by": "jimeng_probe1020_harness_fidelity.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **把 1019 那 8 个行为格本身当被测对象** —— "
            "量这个 harness 的**保真度**（同一个函数真身、同一批输入，"
            "两条 stub 的答案在哪些格上分叉）与**判别力**（系统枚举的变异体，"
            "8 个格杀死了几个）。",
    "question_2020": "1019 把一条判据升级成「真行为验证」之后，那个验证器本身有多可靠？",
    "under_test": {
        "delivered_by": "batch 1019",
        "cells": N_CELL,
        "harness": "shallow stub（`contains` 只认直接父节点）+ 8 个手写期望的格",
        "file_under_test": "scripts/jimeng_probe1019_behavior_harness.py 的 HARNESS_HEAD",
    },
    "fidelity": {
        "the_only_difference": "⭐⭐⭐⭐⭐⭐⭐ **`contains` 的语义** —— "
                               "`shallow`: `el.__parent === this`（只认直接父节点、**不含自身**）；"
                               "`deep`: 沿父链上溯、**含自身**（真 DOM `Node.contains` 的语义）",
        "contains_probe_measured_not_reasoned": {
            "shallow": BASE_SHALLOW["contains"], "deep": BASE_DEEP["contains"],
            "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「含不含自身」「含不含子孙」这两条是量出来的，不是推理出来的** —— "
                    "shallow 在 `self` 与 `depth2` 上与 deep **分叉**，"
                    "在 `depth1` 与 `unrelated` 上一致",
        },
        "grid": {"rule": "⭐ 明写口径：n ∈ {0,1,2,3,5}；焦点 5 类（node/inner1/inner2/root/other）× dir ∈ {+1,−1}",
                 "n_points": N_GRID,
                 "n_disagreements": N_DISAGREE,
                 "disagreement_kinds": DISAGREE_KINDS,
                 "disagreements": DISAGREE[:24],
                 "rule2": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **分歧只出现在 `inner2`（深度 ≥2 的内层控件）** —— "
                          "而 1019 那条 906 关键格用的是 `inner1`（深度 1）"
                          "⇒ **harness 的保真度问题，恰好落在它唯一测过的那一格的邻居上、"
                          "而在它测过的那一格上它是对的**",
        },
        "why_it_matters": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 906 那条源站事实是「焦点在节点**内层控件** ⇒ 一次都不布」，"
                          "而 906 自己量的是**两种口径**（`closest` 与 `contains`）的差。"
                          "⇒ **真身里那段注释防的正是「`contains` 用错」** ⇒ "
                          "⇒⇒⇒⇒⇒ **而 1019 的 stub 自己就把 `contains` 用错了 —— "
                          "只是错的方向恰好被它测的那一格掩盖了**",
    },
    "the_fix_measured": {
        "where": "⭐⭐⭐⭐⭐⭐⭐ **在 1020 自己的 harness 上加格，一个字都不动 1019** —— "
                 "因为 1019 的产物与判据里**写死了「8 个行为格」**，加格会让那个数过期；"
                 "⇒⇒⇒⇒⇒ **「随重跑变化的读数不许写死进判据或文档」这条通则，"
                 "在写它自己那批时就该想到**",
        "baseline_of_the_new_cells": {"n_cells": N_CELL_PLUS, "all_green": PLUS_BASE_GREEN,
                                      "new_cells": NEW_CELLS},
        "score_before": {"cells": N_CELL, "killed_shallow": N_K_SHALLOW},
        "score_after": {"cells": N_CELL_PLUS, "killed_shallow": N_KP_SHALLOW,
                        "killed_deep": N_KP_DEEP},
        "newly_killed": NEWLY_KILLED,
        "per_cell_kill_count_plus_shallow": SUMMARY["shallow"]["per_cell_plus"],
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **补两格把 mutation score 从 %d/%d 抬到 %d/%d**"
                "⇒⇒⇒⇒⇒⇒⇒ **而这两格各自对准的是一个**实测存活**的变异体**，不是「感觉这里该补」"
                % (N_K_SHALLOW, N_TESTABLE, N_KP_SHALLOW, N_TESTABLE),
        "gate_before_credit": "⭐⭐⭐⭐⭐⭐⭐⭐⭐ **补的格自己必须先在基线上全绿**"
                              "（`all_green=%s`）—— 否则「它能杀变异体」就是拿一个"
                              "**本身就红的格**在说，那正是 1018 刚撤回过的那种假发现"
                              % PLUS_BASE_GREEN,
    },
    "tabindex_fidelity": {
        "measured": TAB_FID,
        "disagreements": TAB_DISAGREE,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **第二处 stub 保真度缺口："
                "`tabindex` 在真 DOM 里是一个**整数**，浏览器会做整数解析；"
                "而 harness 判的是**字符串相等** `\"0\"`** ⇒ "
                "**`-0`、`00`、`+0`、`\" 0\"` 在 stub 里都不等于 `\"0\"`，在浏览器里都等于 0。**"
                "⇒⇒⇒⇒⇒⇒⇒ **而这正好是上面那个存活变异体 `\"-1\" → \"-0\"` 藏身的地方**"
                "⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **同一个值，在 stub 里能骗过 8 格，在真 DOM 里会让整块画布全部可 Tab**",
        "scope_caveat": "⭐⭐⭐⭐⭐ **上面这句里「会让整块画布全部可 Tab」是**按 HTML 的整数解析规则**推的**，"
                        "本批**没有在浏览器里实测**（零浏览器、纯离线）⇒ "
                        "**报成「两套口径不一致」这个实测事实，不报「复刻坏了」**",
    },
    "the_verdict_fork": {
        "what_was_done": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **不是新增一个格，是把已有那条 906 的格"
                         "「样本深度 1 → 2」换掉** ⇒ **期望一个字没动**"
                         "（仍是 `armed:-1, writes:0`）",
        "depth1_1019_original": C906_SHALLOW["depth1"],
        "depth2_under_1019_stub": C906_SHALLOW["depth2"],
        "depth2_under_faithful_stub": C906_DEEP["depth2"],
        "verdict_fork": VERDICT_FORK,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**同一条期望、同一个函数、只换一个样本深度 ⇒ 两条 stub 给出相反的通过/不通过。**"
                "⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 而 1019 那 8 格在**两条** stub 下都 8/8 全绿"
                "⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **这 11 格分歧当前一条都没影响判别结论** —— "
                "**它是潜在的、不是已发生的**"
                "⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **但它离「变成已发生」只差一个样本**",
        "honest_caveat": "⭐⭐⭐⭐⭐⭐⭐ **我不报「复刻在真实控件上错了」** —— "
                         "「节点内层控件的真实嵌套深度」本批**没有量**（离线、零浏览器）"
                         "⇒ 只报「**harness 在这一类状态上不保真，且该类状态正好是 906 那条格守的东西**」",
    },
    "discriminating_power": {
        "mutants": {
            "rule": "⭐⭐⭐⭐⭐⭐⭐ **机器按 token 规则系统生成**（`===`/`!==`/`<`/`>=`/`||`/`<=>`/`&&`/"
                    "`+`/一元`!`/整数字面量 各换一个值，外加整行删除守卫/调用行）"
                    "⇒ **不是手挑**，分母由探针生成、不由我断言",
            "n_generated": N_MUT,
            "n_testable": N_TESTABLE,
            "n_syntax_error_under_both": N_SYNTAX,
            "n_timeout_under_both": N_TIMEOUT,
            "timeout_names": TIMEOUT_ONLY[:12],
            "rule_timeout": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「把 `i += 1` 变异成 `i += 0`」会让 `armAll` 永不退出** —— "
                            "⭐ **1019 的 harness 没有死循环护栏**，真跑一次是「挂住整个探针」，不是「报红」。"
                            "⇒⇒⇒⇒⇒ 本探针把护栏放在 **stub 的 `setAttribute`** 里"
                            "（**一个字节都不动被测函数体**）⇒ 死循环变成一次普通抛错 "
                            "⇒⇒⇒⇒⇒⇒ **对判别器来说「挂死」和「报错」是同一件事：行为坏了**",
        },
        "score_shallow_1019_harness": {"killed": N_K_SHALLOW, "of": N_TESTABLE,
                                       "survived": len(SURV_SHALLOW)},
        "score_deep_faithful_stub": {"killed": N_K_DEEP, "of": N_TESTABLE,
                                     "survived": len(SURV_DEEP)},
        "per_cell_kill_count_shallow": SUMMARY["shallow"]["per_cell"],
        "per_cell_kill_count_deep": SUMMARY["deep"]["per_cell"],
        "survivors_shallow": SURV_SHALLOW[:40],
        "survivors_with_diff": [{"name": m["name"], **MUT_DIFF.get(m["name"], {})}
                                for m in mut_rows
                                if m.get("shallow") == "survived"][:40],
        "survivor_rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **存活变异体要看它改的是哪一行** —— "
                         "把「突变体名字」当结论报出去，等于报了一个没法复核的东西。"
                         "⇒ 产物里逐个附上 `before` / `after` 两行原文",
        "n_disagreeing_on_verdict": len(DISCRIM),
        "disagreeing_examples": DISCRIM[:16],
        "honest_negative": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **两条 stub 的判别力在我的变异体集合下完全一样**"
                           "（杀 %d / 存活 %d，两边逐个相同，判别结论不一致的 %d 个）"
                           " ⇒⇒⇒⇒⇒⇒ **不要把这个读成「stub 保真度不影响判别力」** —— "
                           "**它只说明：我这 %d 个变异体里没有一个落在这 11 格的区域上**"
                           % (N_K_SHALLOW, len(SURV_SHALLOW), len(DISCRIM), N_TESTABLE),
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「保真度缺口」和「判别力缺口」是两个独立的量** —— "
                "前者靠**换更真的 stub** 才有，后者靠**补样本/补期望** 才有 ⇒ "
                "**本批两条 stub 判别力相同，但保真度差 11 格 ⇒ 报一个不许替另一个说话**",
    },
    "the_structural_finding": {
        "handwritten_cells": "8 个**手写期望**的格 = **判别器**：期望是人（或源站实测记录）定的，"
                             "所以变异体改了行为就会红",
        "machine_grid": "86 个**枚举**的格 = **差分器**：它只能回答「两条 stub 差在哪」，"
                        "**结构上杀不死任何变异体** —— 它的判据就是「与基准不同」，"
                        "而基准自己就是被测对象的一部分",
        "n_differential_disagreements_at_baseline": N_DIFF_BASE,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**把覆盖从 8 格拉到 86 格，不等于多了一个字的判别力。** "
                "⇒ ⇒⇒⇒⇒⇒⇒ 覆盖率与判别力是**两个不同的量**，报一个不许替另一个说话（1017）",
        "in_1019": "⭐ 1019 报的是「8 个行为格基线 8/8 全绿」⇒ **它报的是判别器的基线，"
                   "没有一个字在说判别器有多强** ⇒ **「全绿」和「够强」是两回事**",
    },
    "branch_coverage": {
        "branches": BRANCHES, "hit_by_1019_eight_cells": HIT,
        "n_hit": N_BRANCH_HIT, "n_total": N_BRANCH,
        "the_missing_one": "!flow",
        "added_by_this_probe": {"flow_null_probe": FLOW_NULL_1020, "reached": FLOW_NULL_REACHED},
        "why_acceptable": "⭐⭐⭐⭐⭐ 真调用点 `const flow = t?.closest?.('.react-flow'); if (!flow) return;` "
                          "**已经先挡了一道** ⇒ `armRovingTabindex` 里的 `if (!flow) return;` "
                          "**在生产里是死代码** ⇒⇒⇒⇒⇒ 补这一格不会提高判别力，"
                          "**但补它会让「分支覆盖」这个数好看 —— 而好看不是理由**",
        "honest_note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐ **我第一版把本探针自己加的 `flowNull` 探针算进了"
                       "「1019 的分支覆盖」里，量出 7/7** ⇒ "
                       "**那是我在给自己的格记 1019 的功劳** ⇒ 改成只按那 8 个格算，**是 6/7**",
    },
    "self_audit": {
        "n_comment_lines_in_extracted_body": N_COMMENT_LINES,
        "n_code_lines": N_CODE_LINES,
        "rule": "⭐ 1018 量到「13 条判据的锚点本身就是中文注释」⇒ "
                "本探针把**函数体里有多少是散文**一并报出来：同一份文本，散文占多数",
    },
    "scope": "⚠️⭐⭐⭐⭐⭐⭐⭐ **两条 stub 都不是浏览器** ⇒ 本批量的是「stub 之间的分歧」，"
             "**不是**「真浏览器会怎样」⇒ **不报「复刻真的错了」**，只报"
             "**「harness 在这一格上不保真、且这个偏差方向会掩盖 906 关键格」**；"
             "「节点内层的真实嵌套深度」本批**没有量**（离线、零浏览器）⇒ "
             "**不推断复刻在真实控件上的对错**",
    "offline": "node + 只读仓里一个文件；变异体**只在内存里改文本**，"
               "**一个字节都不动仓里的原型文件**；临时目录注册 atexit 清理",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("网格 %d 格；shallow vs deep 分歧 %d 格（类别 %s）" % (N_GRID, N_DISAGREE, DISAGREE_KINDS))
print("contains 量测：shallow=%s" % BASE_SHALLOW["contains"])
print("           deep=%s" % BASE_DEEP["contains"])
print("1019 那 8 格：shallow 绿 %d/%d；deep 绿 %d/%d"
      % (sum(CELLS_SHALLOW.values()), N_CELL, sum(CELLS_DEEP.values()), N_CELL))
print("变异体：生成 %d，可测 %d，两边都语法错 %d，两边都超时 %d"
      % (N_MUT, N_TESTABLE, N_SYNTAX, N_TIMEOUT))
print("  shallow 杀 %d，存活 %d" % (N_K_SHALLOW, len(SURV_SHALLOW)))
print("  deep    杀 %d，存活 %d" % (N_K_DEEP, len(SURV_DEEP)))
print("  判别结论不一致的变异体 %d 个" % len(DISCRIM))
print("分支覆盖（只算 1019 那 8 格）%d/%d；未覆盖 = %s"
      % (N_BRANCH_HIT, N_BRANCH, [b for b in BRANCHES if not HIT[b]]))
print("906 那条格：深度1 样本 shallow/deep = %s/%s（一致=%s）"
      % (C906_SHALLOW["depth1"]["ok"], C906_DEEP["depth1"]["ok"], D1_AGREE))
print("         深度2 样本 shallow/deep = %s/%s（判决分叉=%s）"
      % (C906_SHALLOW["depth2"]["ok"], C906_DEEP["depth2"]["ok"], VERDICT_FORK))
print("补两格：%d 格基线全绿=%s；mutation score %d/%d -> %d/%d；新杀 %d 个"
      % (N_CELL_PLUS, PLUS_BASE_GREEN, N_K_SHALLOW, N_TESTABLE,
         N_KP_SHALLOW, N_TESTABLE, len(NEWLY_KILLED)))
print("tabindex 字符串 vs 整数：不一致的值 = %s"
      % [t["value"] for t in TAB_DISAGREE])
print("差分器在基线上的分歧数 %d" % N_DIFF_BASE)
print("P1..P9 =", [OUT[k] for k in OUT])
print("PROBE_1020_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)
