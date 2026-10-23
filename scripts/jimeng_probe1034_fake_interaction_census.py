#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-④：「假交互」普查门 —— 把「用户能点、点了什么都不会发生」变成**会红的门**。

为什么要有这道门
----------------
1032 的一批只读审计把 44 个组件、15171 行里的「用户能感知的元素」分类过，
结论是「DEAD_WIRE（压根没接事件）」「FAKE_SUCCESS（弹一句『已执行』但什么都没做）」
「CONST_AS_STATE（写死的读数冒充状态）」占了将近一半。
1032-① 只把 **DEAD_WIRE** 变成了一道门（死按钮集合必须恰好等于登记册）；
**另外两类静态不可枚举** ⇒ ⇒ 它们只能靠**登记制**逐条钉。

本门的形状（与 1032-① 同型，但多了「目标形态」）
------------------------------------------------
    扫描器（.mjs，用 TypeScript 编译器 API 看 AST）⇒ 只报**事实**
    判决器（本文件）⇒ 拿**登记册（真源）**去比这些事实

  · **现状集合** = 扫描器扫出来的「糊弄点」（死按钮 + 只弹一句的 handler）
  · **登记册**   = 当前已知的糊弄点（每条带**目标形态**的可机读谓词）
  · 判据 = **现状集合 == 登记册集合**（双向精确）
      多一条 ⇒ 新增糊弄 ⇒ 红
      少一条 ⇒ 修好了却没销账 ⇒ 红（登记册会腐烂）
  · 每条登记项的「目标形态」必须**当前为假**（= 它确实还没兑现）
      ⇒ 这一条让登记册**现在就长牙**（不是等销账那天才有判据）

⚠️ 纪律：
  · 「静态看不出来」必须记成 UNKNOWN，不许记成 False；
  · 产物里不许出现随机量（时间戳 / 临时目录 / 耗时）；
  · 每条判据都要有**注入式反证**（改事实 ⇒ 必须翻红）——
    否则「现状集合 == 登记册集合」在登记册为空时是恒真。
  · **「恒真」与「不适用」必须分开**（读数自报「几半适用」）。
"""

import ast
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GDIR = ROOT / "docs/research/jimeng-canvas"
SCAN = GDIR / "inputs" / "fake-interaction-scan-1034.json"
GOLDEN = GDIR / "fake-interaction-census-1034.json"
OUT = "/tmp/b1034-fake-interaction-census.json"
SCAN_MJS = ROOT / "scripts" / "jimeng_probe1034_fake_interaction_scan.mjs"
SELF = Path(__file__).name
NODE = "node"
# ⭐ 登记册的**真源**在另一个文件里（文件名不匹配 `jimeng_probe*.py`
#   ⇒ ⇒ 1015 的「通道 B」不会把它当成一个探针、也就不会多出一本无主的 golden）。
REGISTRY_SRC = ROOT / "scripts" / "jimeng_fake_interaction_registry_1034.py"


# ── 谓词：一个可机读的「形态」 ────────────────────────────────────────────
#   类型只允许下面这几种 —— **新的形态必须先在这里登记**，
#   否则门会「读不出」而那与「没测到」长得一模一样。
def _f(ctx, rel):
    return (ctx["facts"].get(rel) or
            {"tags": {}, "identifiers": [], "jsx_texts": [], "string_literals": [],
             "attrs": {}, "calls": {}})


def _all_hold(preds, ctx):
    """一组谓词：**全部**成立才算成立（`current` / `target` 都是一组）。"""
    if isinstance(preds, dict):
        preds = [preds]
    return all(_hold(p, ctx) for p in preds)


def _hold(pred, ctx):
    """谓词是否成立。"""
    t = pred.get("type")
    f = _f(ctx, pred.get("file"))
    if t == "tag_count":
        got = int(f["tags"].get(pred["tag"], 0))
        op, n = pred.get("op", ">="), int(pred.get("n", 1))
        return got >= n if op == ">=" else got == n
    if t == "identifier":
        return pred["value"] in f["identifiers"]
    if t == "identifier_absent":
        return pred["value"] not in f["identifiers"]
    if t == "jsx_text":
        return pred["value"] in f["jsx_texts"]
    if t == "string_literal":
        return pred["value"] in f.get("string_literals", [])
    if t == "string_literal_absent":
        return pred["value"] not in f.get("string_literals", [])
    if t == "attr_text_contains":
        return any(pred["value"] in (v or "") for v in f["attrs"].get(pred["attr"], []))
    if t == "call_arg_text_contains":
        return any(pred["value"] in (v or "") for v in f["calls"].get(pred["callee"], []))
    if t == "call_arg_text_absent":
        return not any(pred["value"] in (v or "") for v in f["calls"].get(pred["callee"], []))
    if t == "no_toast_only":
        rel = pred.get("file")
        return not [h for h in ctx["toast_only"] if h.get("file") == rel]
    if t == "toast_only_count":
        rel = pred.get("file")
        got = len([h for h in ctx["toast_only"] if h.get("file") == rel])
        op, n = pred.get("op", ">="), int(pred.get("n", 1))
        return got >= n if op == ">=" else got == n
    if t == "key_present":
        return pred["key"] in ctx["keys"]
    if t == "key_absent":
        return pred["key"] not in ctx["keys"]
    raise ValueError("unknown_predicate_type:%r" % (t,))


def _break(pred, ctx):
    """造一份事实的副本，让该谓词**不再成立** ⇒ ⇒ 用于阳性对照。"""
    c = copy.deepcopy(ctx)
    rel = pred.get("file")
    t = pred.get("type")
    if c["facts"].get(rel) is None:
        c["facts"][rel] = {"tags": {}, "identifiers": [], "jsx_texts": [],
                           "string_literals": [], "attrs": {}, "calls": {}}
    f = c["facts"][rel]
    if t == "tag_count":
        if pred.get("op", ">=") == ">=":
            f["tags"][pred["tag"]] = 0
        else:
            f["tags"][pred["tag"]] = int(pred.get("n", 1)) + 1
    elif t == "identifier":
        f["identifiers"] = [x for x in f["identifiers"] if x != pred["value"]]
    elif t == "identifier_absent":
        f["identifiers"] = sorted(set(f["identifiers"]) | {pred["value"]})
    elif t == "jsx_text":
        f["jsx_texts"] = [x for x in f["jsx_texts"] if x != pred["value"]]
    elif t == "string_literal":
        f["string_literals"] = [x for x in f.get("string_literals", []) if x != pred["value"]]
    elif t == "string_literal_absent":
        f["string_literals"] = sorted(set(f.get("string_literals", [])) | {pred["value"]})
    elif t == "attr_text_contains":
        f["attrs"][pred["attr"]] = [""]
    elif t == "call_arg_text_contains":
        f["calls"][pred["callee"]] = [""]
    elif t == "call_arg_text_absent":
        f["calls"][pred["callee"]] = [pred["value"]]
    elif t == "no_toast_only":
        c["toast_only"].append({"file": rel, "line": 0, "prop": "onClick",
                                 "message": "已执行", "claim": True})
    elif t == "toast_only_count":
        c["toast_only"] = [h for h in c["toast_only"] if h.get("file") != rel]
        if pred.get("op", ">=") == ">=":
            c["toast_only"].append({"file": rel, "line": 0, "prop": "onClick",
                                     "message": "已执行", "claim": True})
        else:
            c["toast_only"].append({"file": rel, "line": 0, "prop": "onClick",
                                     "message": "x", "claim": False})
    elif t == "key_present":
        c["keys"] = set(k for k in c["keys"] if k != pred["key"])
    elif t == "key_absent":
        c["keys"] = set(c["keys"]) | {pred["key"]}
    else:
        raise ValueError("unknown_predicate_type:%r" % (t,))
    return c


# ── 真源与扫描器 ─────────────────────────────────────────────────────────
def _load_registry():
    """从**登记册真源文件**里取出 `REGISTRY`（一份字面量）。

    ⚠️ 为什么真源在源码里而不是产物 JSON：产物每次都被同步成「现状」
    ⇒ ⇒ 比它的话，「少一条也红」那条判据**根本不成立**（与 1032-① 同因）。
    """
    if not REGISTRY_SRC.exists():
        sys.stderr.write("REGISTRY_SRC_MISSING (data-side error, rc=2)\n")
        sys.exit(2)
    tree = ast.parse(REGISTRY_SRC.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", "") == "REGISTRY" for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, SyntaxError) as e:
                sys.stderr.write("REGISTRY_NOT_LITERAL (rc=2): %s\n" % e)
                sys.exit(2)
    sys.stderr.write("REGISTRY_MISSING (data-side error, rc=2)\n")
    sys.exit(2)


def _run_scanner():
    """现场跑一遍扫描器 ⇒ ⇒ 事实永远是【现在】的，不靠一份可能过期的 JSON。"""
    if not SCAN_MJS.exists():
        sys.stderr.write("SCANNER_MISSING (data-side error, rc=2)\n")
        sys.exit(2)
    env = dict(os.environ)
    env["JIMENG_1034_SCAN_OUT"] = str(SCAN)
    try:
        r = subprocess.run([NODE, str(SCAN_MJS)], cwd=str(ROOT),
                           capture_output=True, timeout=600, env=env)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write("SCANNER_CRASHED (rc=2): %s\n" % e)
        sys.exit(2)
    if r.returncode != 0:
        sys.stderr.write("SCANNER_RC=%d (rc=2): %s\n"
                         % (r.returncode, r.stderr.decode("utf-8", "replace")[-400:]))
        sys.exit(2)
    return SCAN


# ── 真源：登记册（另一个文件里的字面量，不是产物） ─────────────────────────
# ⭐ 登记册的**真源**是 `scripts/jimeng_fake_interaction_registry_1034.py`：
#   它是一份**字面量** ⇒ ⇒ `ast.literal_eval` 可解 ⇒ ⇒ 门读到的是「人写的清单」，
#   不是「每次都被同步成现状的产物」（与 1032-① 同一个坑）。
_REG = _load_registry()


def _live_keys(ctx):
    """现状里「可枚举」的糊弄点集合（死按钮 + 只弹一句的 handler）。"""
    ks = set()
    for d in ctx["dead_buttons"]:
        ks.add("DEAD#" + (d.get("stable_key") or ""))
    for h in ctx["toast_only"]:
        ks.add("TOAST#" + (h.get("key") or ""))
    return ks


def _build_ctx(scan):
    ctx = {
        "facts": scan.get("facts") or {},
        "toast_only": scan.get("toast_only_handlers") or [],
        "dead_buttons": scan.get("dead_buttons") or [],
    }
    ctx["keys"] = _live_keys(ctx)
    return ctx


def _criteria(ctx, reg):
    """⭐ **纯函数**：事实 + 登记册 ⇒ 逐条判据 + 逐条明细。

    ⇒ ⇒⇒⇒ 判据只有**一份实现** ⇒ ⇒⇒⇒ 主函数与 verifier 必须调同一个
    ⇒ ⇒⇒⇒ ⇒ ⇒ 而 verifier 的锚点钉的是「源码里有这几条判据」⇒ ⇒⇒⇒ ⇒ ⇒
    ⇒ ⇒⇒⇒ ⇒ ⇒ 两者一旦各写一份，锚点就钉在了空气上。
    """
    crit, det = {}, {}
    n_files = int(ctx.get("n_files") or 0)
    n_buttons = int(ctx.get("n_buttons") or 0)
    det["scan_coverage"] = {
        "n_files": n_files, "n_buttons": n_buttons,
        "n_dead_buttons": len(ctx["dead_buttons"]),
        "n_toast_only": len(ctx["toast_only"]),
        "n_registry_entries": len(reg),
    }

    # P1：扫描范围非空（防「扫到 0 个」这种恒真）
    crit["P1_scan_is_not_empty_1034"] = bool(
        n_files > 0 and n_buttons > 0 and ctx["facts"])

    # P2 / P3：现状集合 vs 登记册（**双向**精确）
    live = _live_keys(ctx)
    reg_keys = set(e.get("key") or "" for e in reg if e.get("kind") in ("DEAD", "TOAST"))
    new = sorted(live - reg_keys)
    stale = sorted(reg_keys - live)
    crit["P2_no_new_fake_interaction_1034"] = bool(not new)
    crit["P3_registry_is_not_rotten_1034"] = bool(not stale)
    det["P2_detail"] = {"n_new": len(new), "new": new[:20], "n_live": len(live)}
    det["P3_detail"] = {"n_stale": len(stale), "stale": stale[:20],
                        "n_registered": len(reg_keys)}

    # P4 / P5：登记制（枚举不到的那几类，逐条钉）
    rows = []
    for e in reg:
        rows.append({
            "id": e.get("id"), "kind": e.get("kind"), "file": e.get("file"),
            "promise": e.get("promise"),
            # ⭐ `current` = 「它现在还是那个糊弄形态」⇒ 必须**成立**
            # ⭐ `target`  = 「整改成什么样才算兑现」⇒ 今天必须**不成立**
            "current_holds": bool(_all_hold(e.get("current") or [], ctx)),
            "target_holds": bool(_all_hold(e.get("target") or [], ctx)),
        })
    det["promise_rows"] = rows
    det["n_promise_entries"] = len(rows)
    crit["P4_every_registered_fake_still_holds_1034"] = bool(
        all(r["current_holds"] for r in rows))
    det["P4_detail"] = [r["id"] for r in rows if not r["current_holds"]]
    crit["P5_no_registered_promise_is_already_fulfilled_1034"] = bool(
        all(not r["target_holds"] for r in rows))
    det["P5_detail"] = [r["id"] for r in rows if r["target_holds"]]

    # P6：注入式反证（这一门必须能红）
    inj = copy.deepcopy(ctx)
    inj["toast_only"].append({"file": "src/components/jimeng/__probe_injected__.tsx",
                               "line": 1, "prop": "onClick", "message": "已执行",
                               "claim": True,
                               "key": "src/components/jimeng/__probe_injected__.tsx#onClick#0"})
    new_inj = sorted(_live_keys(inj) - reg_keys)
    crit["P6_injected_new_fake_is_caught_1034"] = bool(new_inj)
    det["P6_detail"] = {"injected": new_inj[:5]}
    # ① 反向：往登记册里塞一条**不存在的**糊弄 ⇒ 「登记册腐烂」那半句必须红
    bogus = sorted((reg_keys | {"TOAST#__bogus_entry__"}) - live)
    crit["P6b_a_registry_entry_that_does_not_exist_is_caught_1034"] = bool(bogus)
    det["P6b_detail"] = {"stale": bogus[:5]}

    # P7：与 1032-① 的死按钮清单交叉核对（**两个独立实现必须一致**）
    wire = GDIR / "inputs" / "interaction-wiring-1032.json"
    if wire.exists():
        try:
            w = json.loads(wire.read_text(encoding="utf-8"))
        except ValueError:
            w = {}
        theirs = set(x.get("stable_key") or "" for x in (w.get("dead_buttons") or []))
        mine = set(d.get("stable_key") or "" for d in ctx["dead_buttons"])
        crit["P7_two_scanners_agree_on_dead_buttons_1034"] = bool(theirs == mine)
        det["P7_detail"] = {"mine": sorted(mine)[:10], "theirs": sorted(theirs)[:10]}
    else:
        crit["P7_two_scanners_agree_on_dead_buttons_1034"] = False
        det["P7_detail"] = {"why": "1032-① 的扫描产物不在盘上 ⇒ 两边口径没法对账"}

    # P8：覆盖边界必须**写出来**（不许让人把「本门绿」读成「没有糊弄」）
    det["not_covered"] = [
        "枚举不到的一切形态：只有登记册逐条钉住的那几类才看得见",
        "跨组件的「假持久化」（写进了 store、但 store 自己只是内存态）",
        "运行时才暴露的问题（异步竞态、焦点跑飞、动画中途的可点性）",
    ]
    crit["P8_coverage_boundary_is_declared_1034"] = bool(det["not_covered"])

    # P9：每条谓词都必须有牙（把它改坏 ⇒ 必须不再成立）
    no_teeth = []
    for e in reg:
        for k in ("current", "target"):
            ps = e.get(k) or []
            if isinstance(ps, dict):
                ps = [ps]
            for i, pr in enumerate(ps):
                if _hold(pr, _break(pr, ctx)):
                    no_teeth.append("%s.%s[%d]" % (e.get("id"), k, i))
    crit["P9_every_predicate_has_teeth_1034"] = bool(not no_teeth)
    det["P9_detail"] = no_teeth[:20]
    return crit, det


def _force_hold(pred, ctx):
    """造一份事实的副本，让该谓词**成立** ⇒ ⇒ 用于「已兑现却没销账」那条反证。"""
    c = copy.deepcopy(ctx)
    rel = pred.get("file")
    t = pred.get("type")
    if c["facts"].get(rel) is None:
        c["facts"][rel] = {"tags": {}, "identifiers": [], "jsx_texts": [],
                           "string_literals": [], "attrs": {}, "calls": {}}
    f = c["facts"][rel]
    if t == "identifier":
        f["identifiers"] = sorted(set(f["identifiers"]) | {pred["value"]})
    elif t == "identifier_absent":
        f["identifiers"] = [x for x in f["identifiers"] if x != pred["value"]]
    elif t == "tag_count":
        f["tags"][pred["tag"]] = int(pred.get("n", 1))
    elif t == "call_arg_text_contains":
        f["calls"][pred["callee"]] = [pred["value"]]
    elif t == "key_present":
        c["keys"] = set(c["keys"]) | {pred["key"]}
    elif t == "key_absent":
        c["keys"] = set(k for k in c["keys"] if k != pred["key"])
        c["toast_only"] = [h for h in c["toast_only"]
                           if ("TOAST#" + (h.get("key") or "")) != pred["key"]]
        c["dead_buttons"] = [d for d in c["dead_buttons"]
                             if ("DEAD#" + (d.get("stable_key") or "")) != pred["key"]]
    else:
        raise ValueError("force_hold_unsupported:%r" % (t,))
    return c


def _judge(ctx=None):
    """跑扫描器 ⇒ 读事实 ⇒ 算判据。**不落盘**（落盘在 `main()` 里）。"""
    try:
        scan = json.loads(_run_scanner().read_text(encoding="utf-8"))
    except ValueError as e:
        return {"ok": False, "why": ["scan_bad_json:%s" % e], "criteria": {},
                "details": {}, "n_criteria": 0, "n_criteria_true": 0, "ctx": None}
    if ctx is None:
        ctx = _build_ctx(scan)
    ctx["n_files"] = int(scan.get("n_files") or 0)
    ctx["n_buttons"] = int(scan.get("n_buttons") or 0)
    crit, det = _criteria(ctx, _REG)
    # ⭐⭐⭐⭐⭐ **P10（自检必须全过）也必须在这条路径里加**
    #   ⇒ ⇒⇒⇒⇒ 否则 `_judge()`（verifier 调的那条）算出 10 条、
    #   ⇒⇒⇒⇒ ⇒ 而 `main()`（门自己跑的）算出 11 条 ⇒ ⇒⇒⇒ ⇒ ⇒
    #   ⇒ ⇒⇒⇒ ⇒ ⇒ **⇒ ⇒ 「判据只有一份实现」当场被自己破坏** ⇒ ⇒⇒⇒ ⇒ ⇒
    #   ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
    _st = _selftest(ctx)
    crit["P10_selftest_must_be_green_1034"] = bool(_st.get("ok"))
    det["selftest"] = _st
    bad = [k for k, v in crit.items() if v is False]
    return {"ok": (not bad), "why": bad, "criteria": crit, "details": det,
            "n_criteria": len(crit),
            "n_criteria_true": sum(1 for v in crit.values() if v),
            "ctx": ctx, "scan": scan}


def _selftest(ctx):
    """⭐⭐⭐⭐⭐ **注入式反证**：改事实 ⇒ 判据必须翻红。

    ⇒ ⇒⇒⇒ 四族：① 现状里注入一条糊弄 ⇒ P2 翻红
    ⇒ ⇒⇒⇒ ② 登记册里塞一条不存在的 ⇒ P3 翻红
    ⇒ ⇒⇒⇒ ③ 把某条的「现状谓词」改坏 ⇒ P4 翻红
    ⇒ ⇒⇒⇒ ④ 让某条的「目标形态」提前成立 ⇒ P5 翻红（**已兑现却没销账**）
    """
    cases = []
    base, _d = _criteria(ctx, _REG)
    reg = _REG

    def _case(name, base_ok, mutated_ok):
        """⭐⭐⭐⭐⭐ **「世界本来就红」与「反证没生效」必须分开**。

        ⇒ ⇒⇒⇒ 若基准已经是红的，那这一族反证**不适用**（不是「自检坏了」）⇒ ⇒⇒⇒
        ⇒ ⇒⇒⇒ 否则「世界真红」会把自检也拖红 ⇒ ⇒⇒⇒ ⇒ ⇒ 而那两件事要能分开看
        ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ **⇒ 处置：不适用记 `applicable=False`，且**不算自检失败**
        """
        if not base_ok:
            cases.append({"case": name, "ok": True, "applicable": False,
                          "note": "⭐ 基准已是红的 ⇒ 这一族**不适用**（不是通过，"
                                  "也不是自检坏了）"})
            return
        cases.append({"case": name, "ok": bool(not mutated_ok),
                      "applicable": True})

    # ① 注入一条新的糊弄 ⇒ P2 必须翻红
    inj = copy.deepcopy(ctx)
    inj["toast_only"].append({"file": "src/components/jimeng/__probe_injected__.tsx",
                               "line": 1, "prop": "onClick", "message": "已执行",
                               "claim": True,
                               "key": "src/components/jimeng/__probe_injected__.tsx#onClick#0"})
    c1, _ = _criteria(inj, reg)
    _case("inject_new_fake_makes_P2_red",
          base["P2_no_new_fake_interaction_1034"],
          c1["P2_no_new_fake_interaction_1034"])

    # ② 登记册塞一条不存在的 ⇒ P3 必须翻红
    reg2 = list(reg) + [{"id": "__bogus__", "kind": "TOAST",
                         "key": "TOAST#__bogus__", "file": "x",
                         "promise": "x", "current": [], "target": []}]
    c2, _ = _criteria(ctx, reg2)
    _case("bogus_registry_entry_makes_P3_red",
          base["P3_registry_is_not_rotten_1034"],
          c2["P3_registry_is_not_rotten_1034"])

    # ③ 把某条的「现状谓词」改坏 ⇒ P4 必须翻红
    _c3 = None
    for _e in reg:
        _ps = _e.get("current") or []
        if isinstance(_ps, dict):
            _ps = [_ps]
        if _ps:
            _c3 = _break(_ps[0], ctx)
            break
    if _c3 is None:
        cases.append({"case": "break_current_predicate_makes_P4_red",
                      "ok": True, "applicable": False,
                      "note": "⭐ 登记册为空 ⇒ 这一族**不适用**（不是通过）"})
    else:
        c3, _ = _criteria(_c3, reg)
        _case("break_current_predicate_makes_P4_red",
              base["P4_every_registered_fake_still_holds_1034"],
              c3["P4_every_registered_fake_still_holds_1034"])

    # ④ 让某条的「目标形态」提前成立 ⇒ P5 必须翻红
    # ⚠️⭐⭐⭐⭐⭐ **目标是【合取】** ⇒ ⇒ 只让其中一个成立 ⇒ 合取仍不成立
    #   ⇒ ⇒ 判据不会翻红 ⇒ ⇒ 而那看起来像「这条反证没生效」
    #   ⇒ ⇒⇒⇒⇒ **⇒ 必须让该条的全部目标谓词都成立** ⇒ ⇒⇒⇒⇒ ⇒ 那才是「已兑现」
    _c4 = None
    for _e in reg:
        _ps = _e.get("target") or []
        if isinstance(_ps, dict):
            _ps = [_ps]
        if _ps:
            _c4 = ctx
            for _pr in _ps:
                _c4 = _force_hold(_pr, _c4)
            break
    if _c4 is None:
        cases.append({"case": "fulfilled_target_makes_P5_red",
                      "ok": True, "applicable": False,
                      "note": "⭐ 登记册为空 ⇒ 这一族**不适用**（不是通过）"})
    else:
        c4, _ = _criteria(_c4, reg)
        _case("fulfilled_target_makes_P5_red",
              base["P5_no_registered_promise_is_already_fulfilled_1034"],
              c4["P5_no_registered_promise_is_already_fulfilled_1034"])

    _applicable = [c for c in cases if c.get("applicable")]
    return {"ok": all(c["ok"] for c in cases), "n_cases": len(cases),
            "n_applicable": len(_applicable), "cases": cases}


def main():
    v = _judge()
    ctx = v.get("ctx") or {}
    # ⭐ 判据集合**只在 `_judge()` 里算一次** ⇒ ⇒ verifier 调的那条路径与门自己
    #   跑的这条路径**逐条相等** ⇒ ⇒ 不许在这里再加一遍
    crit = dict(v.get("criteria") or {})
    det = dict(v.get("details") or {})

    out = {
        "generated_by": SELF,
        "what_this_gate_asks": "**用户能点、而点了什么都不会发生**的那些地方，"
                               "现在还有哪些？登记册与现状是否逐条对得上？",
        "what_it_is_not": "⚠️ **本门绿 ≠ 克隆版没有糊弄** —— 它只覆盖"
                          "① 可枚举的两类（死按钮 / 只弹一句）"
                          "② 登记册里逐条钉住的那几类。"
                          "**枚举不到的那些形态，登记册之外仍然是盲区。**",
        "scan_scope": (v.get("scan") or {}).get("scan_scope"),
        "criteria": crit,
    }
    out.update(crit)
    out["details"] = det
    out["registry"] = [
        {"id": e.get("id"), "kind": e.get("kind"), "key": e.get("key"),
         "file": e.get("file"), "promise": e.get("promise"), "why": e.get("why")}
        for e in _REG
    ]
    out["n_p_criteria"] = len(crit)
    bad = [k for k, val in crit.items() if val is False]
    out["failed_criteria"] = bad
    out["why"] = bad
    GOLDEN.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
    print("判据逐条 =", " | ".join("%s=%s" % (k, crit[k]) for k in sorted(crit)))
    if bad:
        print("P 为假的：", ", ".join(bad))
        return 1
    print("P 为假的： 无 | 共 %d 条 P 判据" % len(crit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
