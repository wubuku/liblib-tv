#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1038：**沉默退出**普查门（早退时产物写不写、能不能现场验证、登记是否对得上）

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**动机（1032-⑩ 实测出来的同一族）**：
  · 1019 / 1020 原来在「抽不出函数真身」时 `raise SystemExit(...)`
  ⇒ ⇒⇒ **产物一个字都不写** ⇒⇒⇒ 下游只看到「这本书不在」
  ⇒ ⇒⇒ ⇒ 而「读不到」与「读到 0」在账上**长得一模一样** ⇒⇒⇒ ⇒ 那就是假绿的温床
  · 1032-⑩ 已把这两本改成「早退也写产物 + rc=2」，但那是**逐个撞见再修**
  ⇒ ⇒⇒⇒ ⇒ 而这一族是**可枚举**的 ⇒⇒⇒⇒ ⇒ 那就该**普查**，而不是等人来撞

⭐⭐⭐⭐⭐ **本门的三段**
  ① **静态枚举**（可数）：从源码 AST 得出每个探针的**退出点**，
     并判断「这条退出之前有没有可能写过产物」（同作用域 + **传递性写闭包**）
  ② **登记制**（可审计）：每一条「疑似沉默退出」必须登记，
     带「是否写产物 / 是否可现场验证 / 处置 / 强制开关」
     ⇒⇒⇒⇒ 枚举与登记**双向**对得上（多一条少一条都红）
  ③ **现场验证**（★ 关键）：登记为可现场验证的 ⇒ **门自己打开开关真跑一次**
     ⇒⇒⇒⇒ 读产物 ⇒⇒⇒ 判「可读 + 自报 + rc=2」
  ④ **阴性对照**：把某条早退路径的「写产物」去掉 ⇒ **门必须转红**

⭐⭐⭐⭐⭐ **口径（写在产物里，不含糊）**
  · 普查范围 = **册子里的那些探针**（只有它们才有产物、才影响 1015 / 1032n）
  ⇒⇒⇒⇒ ⇒ 范围**由数据决定**（读产物里的 `generated_by`），不是手写清单
  · 退出点 = `sys.exit` / `os._exit` / `raise SystemExit`
  · 「退出前写过」= 同作用域内有更早的写产物调用 **或** 退出前调用过
    「会写产物的本地函数」（**传递性**：f 写 ⇔ f 直接写 或 f 调用的 g 写）
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
OUT = GDIR / "silent-exit-census-1038.json"
SELF = "jimeng_probe1038_silent_exit_census.py"


# ── AST 基础件（⭐「唯一实现」：判定口径不许散在多处） ─────────────────────
WRITE_METHODS = {"write_text", "write_bytes", "dump", "writelines", "write"}
OPEN_MODES = {"w", "wb", "w+", "wt", "a", "ab", "a+"}


def call_name(node):
    """⇒ 调用的名字。**Call 与函数引用都能吃**。

    ⭐⭐⭐⭐⭐ 踩过的坑：只吃「函数引用」而调用点传的是 `Call`
    ⇒ ⇒⇒ 于是返回**空串** ⇒⇒⇒ 而「空串」不报错 ⇒⇒⇒
    ⇒ ⇒⇒⇒ 退出点与写产物点会**双双识别不到** ⇒⇒⇒⇒ 普查器**静默返回 0**
    ⇒ ⇒⇒⇒ ⇒ ⇒ 而「真的一个都没有」与「我根本没识别到」在账上长得一模一样
    """
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def is_write_call(node):
    n = call_name(node)
    if n in ("write_text", "write_bytes", "writelines"):
        return True
    if n == "dump":
        return len(node.args) >= 2
    if n == "write":
        return True
    if n == "open":
        mode = ""
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            mode = str(node.args[1].value)
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = str(kw.value.value)
        return any(m in mode for m in OPEN_MODES)
    return False


def is_exit_call(node):
    if isinstance(node, ast.Call):
        return call_name(node) in ("exit", "_exit")
    if isinstance(node, ast.Raise):
        exc = node.exc
        if isinstance(exc, ast.Call):
            return call_name(exc) == "SystemExit"
        if isinstance(exc, ast.Name):
            return exc.id == "SystemExit"
    return False


def exit_arg(node):
    if isinstance(node, ast.Raise):
        exc = node.exc
        if isinstance(exc, ast.Call) and exc.args:
            return ast.unparse(exc.args[0])[:80]
        return ""
    if isinstance(node, ast.Call) and node.args:
        return ast.unparse(node.args[0])[:80]
    return ""


def scope_nodes(scope):
    """作用域内的所有节点（**不进入嵌套函数/类**）。"""
    stack = list(scope.body if hasattr(scope, "body") else [])
    while stack:
        node = stack.pop(0)
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        stack = list(ast.iter_child_nodes(node)) + stack


def calls_in_scope(scope):
    """⇒ [(lineno, callee_name)] —— 本作用域内、不含嵌套函数内部的调用。"""
    out = []
    for node in scope_nodes(scope):
        if isinstance(node, ast.Call):
            nm = call_name(node)
            if nm:
                out.append((node.lineno, nm))
    return out


def write_lines_in_scope(scope):
    """⇒ [lineno] —— 本作用域内**直接**写产物的调用位置。"""
    return [n.lineno for n in scope_nodes(scope)
            if isinstance(n, ast.Call) and is_write_call(n)]


def _has_direct_exit(scope):
    for node in scope_nodes(scope):
        if is_exit_call(node):
            return True
    return False


def _closures(funcs):
    """⇒ (writes, exits)：两个**传递性闭包**。

    ⭐⭐⭐⭐⭐ `exits` 这一层是必需的：修好之后早退不再写 `raise SystemExit`，
    ⇒⇒⇒ 而是调 `_fail_early(...)` ⇒⇒⇒⇒ 而那个函数内部才有 `sys.exit`
    ⇒⇒⇒⇒ ⇒⇒ **只认 `raise SystemExit` 的普查器会把「已修好的早退」当成不存在**
    ⇒⇒⇒⇒ ⇒⇒ ⇒⇒ 所以「调用会退出的函数」**也算退出点**
    """
    direct_w = {n: bool(write_lines_in_scope(f)) for n, f in funcs.items()}
    direct_e = {n: _has_direct_exit(f) for n, f in funcs.items()}
    callees = {n: {c for _l, c in calls_in_scope(f) if c in funcs}
               for n, f in funcs.items()}
    writes = {n for n, v in direct_w.items() if v}
    exits = {n for n, v in direct_e.items() if v}
    changed = True
    while changed:
        changed = False
        for name, cs in callees.items():
            if name not in writes and (cs & writes):
                writes.add(name)
                changed = True
            if name not in exits and (cs & exits):
                exits.add(name)
                changed = True
    return writes, exits


def analyse_probe(path):
    """⇒ 该探针的**退出点**清单（每条带「终止前有没有写过产物」）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    writes, exit_funcs = _closures(funcs)
    rows = []

    def visit(node, cur_func):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cur_func = node
        scope = cur_func if cur_func is not None else tree
        if is_exit_call(node):
            hit = sorted({c for ln, c in calls_in_scope(scope)
                          if ln <= node.lineno and c in writes})
            own = [ln for ln in write_lines_in_scope(scope) if ln < node.lineno]
            rows.append(_row(path, node.lineno, cur_func,
                             ("raise SystemExit" if isinstance(node, ast.Raise)
                              else call_name(node)),
                             exit_arg(node),
                             bool(hit) or bool(own),
                             ("退出前调用了会写产物的本地函数:" + ",".join(hit[:3])
                              if hit else
                              ("同作用域内已有写产物调用" if own else
                               "★ 终止前没有任何写产物调用 ⇒ 疑似沉默退出"))))
        elif (isinstance(node, ast.Call) and call_name(node) in exit_funcs
              and not is_exit_call(node)):
            callee = call_name(node)
            # ⭐ 调「会退出的函数」也是退出点 ⇒ 它自己写没写，决定是不是沉默
            wrote = callee in writes
            arg = ""
            if node.args:
                arg = ast.unparse(node.args[0])[:80]
            rows.append(_row(path, node.lineno, cur_func,
                             "call:%s" % callee, arg, wrote,
                             ("被调函数 %s 会写产物 ⇒ 终止前写过了" % callee if wrote
                              else "★ 被调函数 %s 不写产物 ⇒ 疑似沉默退出" % callee)))
        for child in ast.iter_child_nodes(node):
            visit(child, cur_func)

    visit(tree, None)
    return rows


def _row(path, lineno, cur_func, how, arg, wrote, why):
    return {"file": path.name, "lineno": lineno,
            "func": getattr(cur_func, "name", None),
            "how": how, "arg": arg,
            "writes_before_exit": bool(wrote), "why": why}


# ── 登记制：每一条「曾经沉默过」的早退路径都在册上 ───────────────────────────
#   ⭐ 登记项**不含行号** ⇒⇒⇒ 行号会随改动漂移 ⇒⇒⇒⇒ 用「文件＋函数＋消息前缀」做键
#   ⭐ 「是否写产物 / 是否可现场验证」必须**显式声明** ⇒⇒⇒ 不许靠人记
REGISTRY_1038 = [
    {"file": "jimeng_probe1019_behavior_harness.py", "func": "extract_fn",
     "msg_prefix": "找不到函数",
     "writes_product": True, "verifiable": True,
     "switch": "JIMENG_FORCE_EXTRACT_FAIL", "expect_label": "extract-fail",
     "artifact": "docs/research/jimeng-canvas/behavior-harness-1019.json",
     "disposition": "改成 _fail_early ⇒ 写产物（判据逐条 None）＋ rc=2"},
    {"file": "jimeng_probe1019_behavior_harness.py", "func": "extract_fn",
     "msg_prefix": "括号没配平",
     "writes_product": True, "verifiable": True,
     "switch": "JIMENG_FORCE_EXTRACT_UNBALANCED", "expect_label": "extract-unbalanced",
     "artifact": "docs/research/jimeng-canvas/behavior-harness-1019.json",
     "disposition": "同上（强制开关验证的是**那条出口的契约**，不是扫描器的发现能力）"},
    {"file": "jimeng_probe1019_behavior_harness.py", "func": None,
     "msg_prefix": "补丁锚点不在函数真身里",
     "writes_product": True, "verifiable": True,
     "switch": "JIMENG_FORCE_ANCHOR_FAIL", "expect_label": "anchor-fail",
     "artifact": "docs/research/jimeng-canvas/behavior-harness-1019.json",
     "disposition": "同上"},
    {"file": "jimeng_probe1020_harness_fidelity.py", "func": "extract_fn",
     "msg_prefix": "找不到函数",
     "writes_product": True, "verifiable": True,
     "switch": "JIMENG_FORCE_EXTRACT_FAIL", "expect_label": "extract-fail",
     "artifact": "docs/research/jimeng-canvas/harness-fidelity-1020.json",
     "disposition": "改成 _fail_early ⇒ 写产物（判据逐条 None）＋ rc=2"},
    {"file": "jimeng_probe1020_harness_fidelity.py", "func": "extract_fn",
     "msg_prefix": "括号没配平",
     "writes_product": True, "verifiable": True,
     "switch": "JIMENG_FORCE_EXTRACT_UNBALANCED", "expect_label": "extract-unbalanced",
     "artifact": "docs/research/jimeng-canvas/harness-fidelity-1020.json",
     "disposition": "同上（强制开关验证的是**那条出口的契约**）"},
]


# ── 现场验证：★ 在**副本**上跑 ⇒⇒⇒ 仓库里的产物一个字都不许被改 ──────────────
def _prepare_copy(probe_rel, copy_dir, break_write=False):
    """⇒ (副本路径, 副本产物路径) —— 副本里 ROOT 指回真仓、产物写到副本目录。"""
    copy_dir.mkdir(parents=True, exist_ok=True)
    src = ROOT / "scripts" / probe_rel
    txt = src.read_text(encoding="utf-8")
    golden = copy_dir / "golden.json"
    txt = re.sub(r"(?m)^ROOT\s*=.*$", 'ROOT = Path("%s")' % ROOT, txt, count=1)
    txt = re.sub(r"(?m)^GOLDEN\s*=.*$", 'GOLDEN = Path("%s")' % golden, txt, count=1)
    if break_write:
        txt = txt.replace("GOLDEN.write_text(", "_NEG_NO_WRITE(")
        txt = txt.replace("def _fail_early(",
                          "def _NEG_NO_WRITE(*a, **k):\n    return 0\n\n\n"
                          "def _fail_early(", 1)
    dst = copy_dir / src.name
    dst.write_text(txt, encoding="utf-8")
    tc = ROOT / "scripts" / "jimeng_node_toolchain.py"
    if tc.exists():
        shutil.copy2(tc, copy_dir / tc.name)
    return dst, golden


def _run_forced(copy_path, switch, timeout=300):
    env = dict(os.environ)
    env[switch] = "1"
    return subprocess.run([sys.executable, "-u", str(copy_path)], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=timeout, env=env)


def _read_artifact(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:                                             # noqa: BLE001
        return None


def verify_entry(entry, tmpdir):
    """⇒ 真跑一次那条早退 ⇒ 判「rc=2 / 产物可读 / 产物自报 / 标签对」。"""
    d = tmpdir / ("v_" + entry["file"].replace(".py", ""))
    copy_path, golden = _prepare_copy(entry["file"], d)
    try:
        r = _run_forced(copy_path, entry["switch"])
    except subprocess.TimeoutExpired:
        return {"entry": entry["msg_prefix"], "ran": False,
                "rc": None, "artifact_readable": False, "self_reports_crash": False,
                "label_ok": False, "why": "强制运行超时"}
    art = _read_artifact(golden)
    crit = (art or {}).get("criteria")
    readable = bool(isinstance(crit, dict) and crit)
    label = (art or {}).get("crash_label")
    return {"entry": entry["msg_prefix"], "file": entry["file"],
            "ran": True, "rc": r.returncode,
            "artifact_exists": art is not None,
            "artifact_readable": readable,
            "n_criteria": len(crit) if isinstance(crit, dict) else 0,
            "self_reports_crash": (art or {}).get("probe_crashed") is True,
            "readings_available": (art or {}).get("readings_available"),
            "readings_fresh": (art or {}).get("readings_fresh"),
            "label": label, "label_ok": label == entry["expect_label"],
            "why": "在副本上强制触发 ⇒ 仓库产物未被改动"}


def negative_control(entry, tmpdir):
    """⇒ 把「写产物」去掉 ⇒ 普查必须把它标成沉默 ⇒ 而且产物确实不写。"""
    d = tmpdir / ("neg_" + entry["file"].replace(".py", ""))
    copy_path, golden = _prepare_copy(entry["file"], d, break_write=True)
    rows = analyse_probe(copy_path)
    hit = [r for r in rows
           if (r["func"] or "-") == (entry["func"] or "-")
           and entry["msg_prefix"] in (r["arg"] or "")]
    try:
        rc = _run_forced(copy_path, entry["switch"]).returncode
    except Exception:                                             # noqa: BLE001
        rc = None
    return {"entry": entry["msg_prefix"], "file": entry["file"],
            "n_matching_rows": len(hit),
            "flagged_silent": bool(hit) and all(not r["writes_before_exit"]
                                                for r in hit),
            "rc_without_write": rc,
            "artifact_absent": not golden.exists(),
            "why": "副本里去掉写产物 ⇒ 普查必须把它标成沉默（否则这扇门是恒真的）"}


def discover_probes():
    """⇒ 普查范围 = **有产物的那些探针**（按 `generated_by` 发现，不手写清单）。"""
    names = []
    for f in sorted(GDIR.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:                                         # noqa: BLE001
            continue
        gb = str((d or {}).get("generated_by") or "")
        if not gb.endswith(".py"):
            continue
        nm = os.path.basename(gb)
        if nm == SELF:
            continue
        if (ROOT / "scripts" / nm).exists() and nm not in names:
            names.append(nm)
    return sorted(names)


def _match_registry(rows):
    """⇒ 登记项 → 枚举行（按 文件＋函数＋消息前缀；**不用行号**）。"""
    matched = []
    missing = []
    for e in REGISTRY_1038:
        hit = [r for r in rows
               if r["file"] == e["file"]
               and (r["func"] or "-") == (e["func"] or "-")
               and e["msg_prefix"] in (r["arg"] or "")]
        if hit:
            matched.append((e, hit))
        else:
            missing.append({"file": e["file"], "func": e["func"],
                            "msg_prefix": e["msg_prefix"]})
    return matched, missing


def main():
    probes = discover_probes()
    all_rows = []
    for nm in probes:
        try:
            all_rows.extend(analyse_probe(ROOT / "scripts" / nm))
        except SyntaxError as exc:
            print("SKIP", nm, exc)
    silent_rows = [r for r in all_rows if not r["writes_before_exit"]]
    matched, missing = _match_registry(all_rows)
    registered_prefixes = {(e["file"], e["func"], e["msg_prefix"])
                           for e, _h in matched}
    silent_unregistered = [
        {"file": r["file"], "func": r["func"], "arg": r["arg"]}
        for r in silent_rows
        if (r["file"], r["func"], (r["arg"] or "")[:12]) not in registered_prefixes
        and not any(r["file"] == e["file"] and (r["func"] or "-") == (e["func"] or "-")
                    and e["msg_prefix"] in (r["arg"] or "")
                    for e in REGISTRY_1038)]

    tmpdir = Path(tempfile.mkdtemp(prefix="b1038-"))
    verifications = []
    negatives = []
    try:
        for e, _h in matched:
            if e.get("verifiable"):
                verifications.append(verify_entry(e, tmpdir))
        for e, _h in matched:
            if e.get("verifiable"):
                negatives.append(negative_control(e, tmpdir))
    finally:
        shutil.rmtree(str(tmpdir), ignore_errors=True)

    n_reg = len(REGISTRY_1038)
    n_matched = len(matched)
    n_verif = len(verifications)
    n_ok_rc = sum(1 for v in verifications if v.get("ran") and v.get("rc") == 2)
    n_readable = sum(1 for v in verifications if v.get("artifact_readable"))
    n_selfreport = sum(1 for v in verifications if v.get("self_reports_crash"))
    n_labels = sum(1 for v in verifications if v.get("label_ok"))
    n_declared_w = sum(1 for e in REGISTRY_1038 if isinstance(e.get("writes_product"), bool))
    n_declared_v = sum(1 for e in REGISTRY_1038 if isinstance(e.get("verifiable"), bool))
    n_neg_ok = sum(1 for x in negatives if x.get("flagged_silent"))

    P = {
        "P1_exit_points_are_enumerable_1038": bool(probes) and len(all_rows) > 0,
        "P2_registry_matches_enumeration_1038": (
            n_matched == n_reg and not missing and not silent_unregistered),
        "P3_registry_declares_writes_product_1038": n_declared_w == n_reg,
        "P4_registry_declares_verifiable_1038": n_declared_v == n_reg,
        "P5_every_verifiable_path_was_run_and_exited_2_1038": (
            n_verif == n_reg and n_ok_rc == n_verif),
        "P6_artifact_is_readable_after_early_exit_1038": (
            n_verif > 0 and n_readable == n_verif),
        "P7_artifact_self_reports_the_crash_1038": (
            n_verif > 0 and n_selfreport == n_verif),
        "P8_negative_control_detects_a_silent_exit_1038": (
            n_neg_ok == len(negatives) and n_neg_ok > 0),
    }


    out = {
        "generated_by": SELF,
        "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「早退时产物写不写」从此是一项可普查的量** —— "
                "不是撞见一个修一个，而是**枚举 → 登记 → 现场验证 → 阴性对照**四段",
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「读不到」与「读到 0」必须分开** ⇒ ⇒ ⇒ "
                "凡是没有写产物就退出的路径，**一律登记**、**一律现场验证**、**一律 rc=2**",
        "scope": {
            "how": "⭐ 按产物的 `generated_by` 发现探针（**不手写清单**）⇒ "
                   "范围 = 有产物、因而会进册子的那些探针",
            "n_probes_scanned": len(probes),
            "probes": probes,
        },
        "exit_point_kind": "⭐ 退出点 = `sys.exit` / `os._exit` / `raise SystemExit` "
                           "**或「调用一个会退出的本地函数」** ⇒ ⇒ ⇒ "
                           "后者是必需的：修好之后早退走的是 `_fail_early(...)`",
        "n_exit_points": len(all_rows),
        "n_suspected_silent": len(silent_rows),
        "exit_points": all_rows,
        "registry": REGISTRY_1038,
        "n_registry": n_reg,
        "n_registry_matched": n_matched,
        "registry_missing_in_enumeration": missing,
        "silent_unregistered": silent_unregistered,
        "verifications": verifications,
        "negative_controls": negatives,
        "probe_crashed": False,
        "readings_available": True,
        "readings_fresh": True,
        "criteria": P,
        "criterion_kinds_1038": {k: "failure" for k in P},
        "criterion_kinds_complete_1038": True,
        "criteria_n_1038": len(P),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    false_list = [k for k, v in P.items() if v is False]
    print("探针 %d 个；退出点 %d 处；疑似沉默 %d 处；登记 %d 条（匹配 %d）"
          % (len(probes), len(all_rows), len(silent_rows), n_reg, n_matched))
    print("现场验证 %d 条（rc=2 的 %d、产物可读 %d、自报 %d、标签对 %d）"
          % (n_verif, n_ok_rc, n_readable, n_selfreport, n_labels))
    print("阴性对照 %d 条（判成沉默的 %d）" % (len(negatives), n_neg_ok))
    print("判据逐条 = " + " | ".join("%s=%s" % (k, v) for k, v in sorted(P.items())))
    print("为假的：", false_list or "无")
    print("PROBE_1038_SILENT_EXIT_CENSUS_DONE ->", OUT)
    sys.exit(1 if false_list else 0)


if __name__ == "__main__":
    main()
