#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-①：把「克隆版里有多少糊弄」变成**会红的门**。

背景（一次反省的产物）
----------------------
1032 做了三件事：(1) 读 `reverse-engineer-anything` 技能并尝试用它的 CLI；
(2) 派三个只读审计者把 44 个组件、15171 行里的「用户能感知的元素」分类；
(3) 用 TypeScript AST 独立扫一遍。

结论：克隆版里「用户能点、但点下去什么都不会发生」的元素**大量存在**。
其中**完全可机检**的一类是「死按钮」——一个 `<button>` 自身没有事件属性、
祖先没有 onClick 委托、也不在 form 里（默认提交），它在 DOM 里就是个**点不动的壳**。

⭐⭐⭐⭐⭐ **本门不打算把现有死按钮判红** —— 那样门一开就是红的，
等于没有门。做法是：
    死按钮集合 **必须恰好等于** `interaction-wiring-allowlist-1032.json`：
      · 多一条 ⇒ **新增了糊弄** ⇒ 红
      · 少一条 ⇒ **修好了却没销账** ⇒ 红（白名单会腐烂）
    那份白名单同时是**修复清单**（每条写明它属于哪类糊弄、为什么）。
    ⇒ 于是这条门的作用是「**不许再糊弄了**」，而不是「现在还没糊弄」。

⚠️⚠️⚠️ **本门只覆盖「压根没接线」这一类。** 另外三类静态不可判，必须靠运行时：
    · FAKE_SUCCESS   —— 弹一句「已执行 / 已保存 / 下载已开始」，但什么都没发生
    · CONST_AS_STATE —— 写死的读数（积分 745、历史恒空、时钟恒 00:00）冒充状态
    · FEATURE_MISSING—— 整个功能不存在（如 `<ReactFlow>` 没有 `onConnect` ⇒ 连不出边）
    ⚠️ **「本门绿」绝不可读成「克隆版没有糊弄」。**

退出码三态（与 1031 探针同一套约定）
    0 = 全绿；1 = 有 P 判据为假；2 = 探针崩了 / 数据不是合法 JSON
"""
import ast
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GDIR = ROOT / "docs/research/jimeng-canvas"
SCAN = GDIR / "inputs" / "interaction-wiring-1032.json"
ALLOW = GDIR / "inputs" / "interaction-wiring-allowlist-1032.json"
OUT = GDIR / "interaction-wiring-check-1032.json"
# ⭐⭐⭐⭐⭐ Batch 1032-②b-0: **真源是生成器源码里的 `NOTES`，不是白名单 JSON** ——
#   白名单 JSON 是**产物**（生成器每次都会把它同步成「现状」）⇒ ⇒ 若门比 JSON，
#   ⇒ ⇒ 「少一条（修好了却没销账）也红」这条判据**根本不成立**
#   ⇒ ⇒ ⇒ 1032-① 的 commit message 与 README 里那句话**当时是假的**。
#   ⇒ ⇒ ⇒ 改比 `NOTES`（源码里的真源）⇒ ⇒ ⇒ **两条判据才都真**：
#   ⇒ ⇒ ⇒ ① 现状多出一条、`NOTES` 里没有 ⇒ **新增糊弄** ⇒ 红；
#   ⇒ ⇒ ⇒ ② 修好一条（现状少了）而 `NOTES` 里还留着标注 ⇒ **该销账了** ⇒ 红。
GEN = ROOT / "scripts/jimeng_probe1032_build_allowlist.py"


def _load(p: Path, what: str):
    if not p.exists():
        sys.stderr.write("%s_MISSING (data-side error, rc=2)\n" % what)
        sys.exit(2)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.stderr.write("%s_BAD_JSON (data-side error, rc=2): %s\n" % (what, e))
        sys.exit(2)


scan = _load(SCAN, "SCAN")
allow = _load(ALLOW, "ALLOW")

buttons = scan.get("buttons") or []
allow_entries = allow.get("entries") or []


def _load_notes():
    """从生成器源码里取出 `NOTES`（真源）。纯字面量 ⇒ `literal_eval` 可解。"""
    if not GEN.exists():
        sys.stderr.write("GEN_MISSING (data-side error, rc=2)\n")
        sys.exit(2)
    tree = ast.parse(GEN.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", "") == "NOTES" for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, SyntaxError) as e:
                sys.stderr.write("NOTES_NOT_LITERAL (rc=2): %s\n" % e)
                sys.exit(2)
    sys.stderr.write("NOTES_MISSING (data-side error, rc=2)\n")
    sys.exit(2)


NOTES = _load_notes()
# ⭐ 键是**稳定键**（见 1032-②b-0：行号是位置不是身份）
notes_keys = set(NOTES.keys())


def _key(entry):
    # ⭐⭐⭐⭐⭐ Batch 1032-②b-0: **键 = 稳定键**，不是 `(file, line)` ——
    #   行号是**位置**不是**身份**（1021/1030 栽过一次；这里是同一形状的复发）：
    #   在判据上方插一行代码，那个判据就「消失」了。
    #   ⇒ 而死按钮的白名单若按行号索引 ⇒ ⇒ 改一行代码 ⇒ 全部标注错位
    #   ⇒ ⇒ ⇒ 每一处都被当成「新增糊弄」⇒ ⇒ ⇒ **修按钮的过程本身会一直误报**。
    #   ⇒ 稳定键 = `文件#可访问名#同文件同名出现序号`（AST 探针给出）。
    #   ⚠️ **不 fallback 到行号** —— 两种口径混用 ⇒ 「谁算糊弄」没人说得清；
    #   ⇒ 键缺失时门会红（提示：先跑 `jimeng_probe1032_build_allowlist.py` 重建白名单）。
    return entry.get("stable_key") or ""


def dead_set(btns):
    # ⚠️ 口径必须与 mjs 探针的 `dead_buttons` **完全一致** ——
    #   两边口径不同 ⇒ 门开张就红，而且红的原因（「谁算糊弄」）没人说得清。
    #   ⭐ `DISABLED_NO_HANDLER` **不算糊弄**：明确禁用是诚实（用户看得到禁用态），
    #   它与「能点但毫无反应」不是一回事。
    return {b.get("stable_key") or "" for b in btns
            if b.get("verdict") in ("DEAD_NO_HANDLER", "DEAD_EMPTY_INLINE")}


def p1_exact(btns, allowed_keys):
    """死按钮集合必须**恰好**等于「真源标注集合」。

    ⚠️⭐⭐⭐⭐⭐ 比的是 **`NOTES`（源码真源）**，不是白名单 JSON（产物）：
      JSON 每次都被生成器同步成「现状」⇒ ⇒ 比它的话，「少一条也红」永远不成立。
    """
    code = dead_set(btns)
    allowed = set(allowed_keys)
    return code == allowed, {"new_dead": sorted(code - allowed),
                             "stale_allow": sorted(allowed - code)}


out = {"generated_by": "jimeng_probe1032_interaction_wiring.py"}

# ── P2：扫描范围完整性（防「扫到 0 个」这种恒真）────────────────────
n_files = scan.get("n_files") or 0
n_buttons = scan.get("n_buttons") or 0
out["scan_coverage"] = {"n_files": n_files, "n_buttons": n_buttons}
out["P2_scan_is_not_empty_1032"] = bool(n_files > 0 and n_buttons > 0)

# ── P3：spread 按钮会让静态判据失效 ⇒ 必须为 0（新增时人工确认）──────
n_spread = len(scan.get("unknown_spread") or [])
out["n_unknown_spread"] = n_spread
out["P3_no_spread_buttons_1032"] = bool(n_spread == 0)

# ── P1：死按钮集合 == 白名单集合 ─────────────────────────────────────
p1_ok, p1_detail = p1_exact(buttons, notes_keys)
out["P1_dead_buttons_match_allowlist_1032"] = p1_ok
out["P1_detail"] = p1_detail
out["P1_source_of_truth"] = "⭐⭐⭐ 比的是生成器源码里的 NOTES（真源），不是白名单 JSON（产物）"

# ── P4：阳性对照 —— 注入一条**不在白名单里**的死按钮，P1 必须变红 ────
# ⚠️ 注入的那条必须带**稳定键** —— 门现在按稳定键判等
#   ⇒ ⇒ 少了这个字段，它会落进「空键」那一类 ⇒ ⇒ 注入就**不再**是「一条新的糊弄」
#   ⇒ ⇒ ⇒ 阳性对照会**假绿**（它必须让 P1 变红才算数）。
_injected = list(buttons) + [{"file": "src/components/jimeng/__probe_injected__.tsx",
                               "line": 1, "verdict": "DEAD_NO_HANDLER",
                               "label": "__injected_probe__",
                               "stable_key": "src/components/jimeng/__probe_injected__.tsx#__injected_probe__#0"}]
_inj_ok, _inj_detail = p1_exact(_injected, notes_keys)
out["P4_injected_dead_button_is_caught_1032"] = bool(p1_ok and (not _inj_ok))

# ── P6/P7：**双向**阳性对照 ——
# ⚠️⭐⭐⭐⭐⭐ 1032-① 只验了**正向**（P4 注入一条新死按钮 ⇒ 必须红）
#   ⇒⇒ 「少一条（修好了却没销账）也红」那条**从没被验过**
#   ⇒⇒⇒ 而它**当时根本不成立** —— 门比的是**产物 JSON**，而生成器每次都把它
#   ⇒⇒⇒⇒ 同步成「现状」⇒ ⇒⇒ 「少一条」永远不出现 ⇒ ⇒⇒ 那条判据形同虚设。
#   ⇒⇒⇒⇒ ⇒ 本批把门改成比**源码里的 `NOTES`（真源）**，并补上**双向**对照：
#   ⇒⇒⇒⇒ ① 从 `NOTES` 删一条 ⇒ 现状比真源多一条 ⇒ **必须红**（= 新增糊弄）
#   ⇒⇒⇒⇒ ② 往 `NOTES` 加一条不存在的 ⇒ 真源比现状多一条 ⇒ **必须红**（= 该销账了）
#   ⇒⇒⇒⇒ ⇒⇒ 两边都红 ⇒⇒ 「多一条红」与「少一条红」**两条都真**。
_victim = sorted(notes_keys)[0] if notes_keys else ""
_m_del_ok, m_del = p1_exact(buttons, notes_keys - {_victim})
_m_add_ok, m_add = p1_exact(buttons, notes_keys | {"__fake_entry__"})
out["P6_more_than_source_is_red_1032"] = bool(
    (not _m_del_ok) and _victim in m_del.get("new_dead", []))
out["P6_detail"] = {"victim": _victim, "new_dead": m_del.get("new_dead", [])[:5]}
out["P7_fewer_than_source_is_red_1032"] = bool(
    (not _m_add_ok) and "__fake_entry__" in m_add.get("stale_allow", []))
out["P7_detail"] = {"stale_allow": m_add.get("stale_allow", [])[:5]}
out["P4_detail"] = {"injected_new_dead": _inj_detail["new_dead"]}

# ── P5：白名单里每条都必须仍能在代码里找到对应按钮（防止销账时删掉真问题）──
# ⚠️⭐⭐⭐⭐⭐ Batch 1032-②b-1: 这里原本写的是 `"%s:%s" % _key(e)` ——
#   `_key(e)` 是**一个字符串** ⇒ ⇒ `"%s:%s" % "abc"` 抛
#   `TypeError: not enough arguments for format string`
#   ⇒ ⇒ 而这个表达式只在**列表推导的 body 里**求值 ⇒ ⇒ body 只在
#   「有条目对不上」时才跑 ⇒ ⇒ **P5 真正该报红的时候，门是崩的，不是红的**。
#   ⇒ ⇒ 而崩 ⇒ ⇒ 退出码 1 ⇒ ⇒ 与「P5 为假」在退出码上**完全一样**
#   ⇒ ⇒ ⇒ 于是一个**本该点名是哪几条对不上**的判据，实际只会说「崩了」。
#   ⇒ ⇒ ⇒ 修法：别做格式化，直接用键本身。
_btn_by_key = {}
for b in buttons:
    _btn_by_key.setdefault(_key(b), b)
_missing_kind = [("%s" % _key(e)) for e in allow_entries
                 if _key(e) not in _btn_by_key]
out["P5_every_allowlist_entry_still_exists_1032"] = bool(not _missing_kind)
out["P5_missing"] = _missing_kind

# ── 产物：只留「形状 + 待办清单」，不留会变的读数 ───────────────────
_counts = scan.get("counts") or {}
out["button_counts"] = _counts
out["n_dead_buttons"] = len(dead_set(buttons))
out["n_allowlist_entries"] = len(allow_entries)
out["dead_buttons"] = [
    {"file": e.get("file"), "line": e.get("line"), "verdict": e.get("verdict"),
     "label": e.get("label"), "kind": e.get("kind")}
    for e in allow_entries
]
out["notes"] = {
    "scope": "本门只覆盖「压根没接线」这一类糊弄",
    "not_covered": ["FAKE_SUCCESS（弹一句『已执行』但什么都没做）",
                    "CONST_AS_STATE（写死读数冒充状态）",
                    "FEATURE_MISSING（整个功能不存在，例如没有 onConnect ⇒ 连不出边）"],
    "why_green_is_not_clean": "⭐⭐ **本门绿 ≠ 克隆版没有糊弄** —— "
                              "它只说明「死按钮的数量与清单一致」，"
                              "而上面三类糊弄**静态不可判**，必须靠运行时探针。",
}

_P = [(k, v) for k, v in out.items() if k.startswith("P") and isinstance(v, bool)]
_bad = [k for k, v in _P if v is False]
out["n_p_criteria"] = len(_P)
out["failed_criteria"] = _bad

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("P 判据 =", [v for _, v in _P])
print("P 为假的：", _bad or "无", "| 共 %d 条" % len(_P))
print("死按钮 %d 条（白名单 %d 条）" % (out["n_dead_buttons"], out["n_allowlist_entries"]))
print("PROBE_1032_WIRING_DONE ->", OUT)
sys.exit(1 if _bad else 0)
