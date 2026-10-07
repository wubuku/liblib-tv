#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1031-④b：让**原型**也接受同一份契约的对账

设计要点（都是本批反复撞到的那些）：
  ① 同一个契约，两个被测对象 —— 真实站与原型读**同一份**
     contracts/live-canvas-contract-1031.json ⇒ 这里只有一份期望值
  ② aria 两种口径分开对账（字面量 / 形状），与 1031 探针完全一致
  ③ 形状不许钉读数：3 nodes 与 76 nodes 都算命中
  ④ **保存态也是形状的一部分**：契约登记的是「已保存」那一行，
     所以形状判据只在已保存样本上做；保存中的样本只参与「数字是否接线」的判据
  ⑤ 产物里不许留会变的读数（节点数、可点元素数），数字一律脱敏成 N
  ⑥ 无浏览器通路时 P 记 null 而不是 False
  ⑦ 退出码三态 0/1/2，与 1031 探针同一套约定
"""
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GDIR = ROOT / "docs/research/jimeng-canvas"
CONTRACT = Path(os.environ.get("JIMENG_CONTRACT_JSON")
                or (GDIR / "contracts" / "live-canvas-contract-1031.json"))
READINGS = Path(os.environ.get("JIMENG_REPLICA_JSON", "/tmp/b1031d-local-fresh.json"))
OUT = GDIR / "replica-contract-1031d.json"

if not CONTRACT.exists():
    sys.stderr.write("CONTRACT_MISSING (data-side error, rc=2)\n")
    sys.exit(2)
try:
    C = json.loads(CONTRACT.read_text(encoding="utf-8"))
except ValueError as e:
    sys.stderr.write("CONTRACT_BAD_JSON (data-side error, rc=2): %s\n" % e)
    sys.exit(2)

REQ_T = list(C.get("required_testids", []))          # 口径一：区域级
REQ_A = list(C.get("required_aria", []))            # 口径一：区域级
SHAPES = C.get("aria_shapes", {}) or {}             # 口径二：形状
NODE_SCOPED = C.get("node_scoped", {}) or {}        # 口径三：节点级
NODE_T = list(NODE_SCOPED.get("testids", []))
NODE_A = list(NODE_SCOPED.get("aria", []))
KINDS = list(C.get("node_kinds", []))
SHAPE_RE = re.compile(C["status_shape"])
DIGIT_RE = re.compile(r"\d")
NUM_RE = re.compile(r"\d+")
SAVED_SUFFIX = "已保存."

out = {"generated_by": "jimeng_probe1031d_replica_contract.py"}
out["contract_file"] = (str(CONTRACT.relative_to(ROOT))
                        if str(CONTRACT).startswith(str(ROOT)) else str(CONTRACT))
out["contract_counts"] = {"n_testids": len(REQ_T), "n_aria_literals": len(REQ_A),
                          "n_aria_shapes": len(SHAPES),
                          "n_node_scoped_testids": len(NODE_T),
                          "n_node_scoped_aria": len(NODE_A),
                          "n_node_kinds": len(KINDS)}
# ⭐ 三种口径的**键不许重叠** —— 重叠意味着一条契约在两种口径里各被当权威，
#   而两种口径的判法不同（区域级恒该有 / 节点级没测到）⇒ 迟早有一边误判。
_overlap_t = sorted(set(REQ_T) & set(NODE_T))
_overlap_a = sorted(set(REQ_A) & set(NODE_A))
out["caliber_overlap"] = {"testids": _overlap_t, "aria": _overlap_a}
out["P7_calibers_do_not_overlap_1031d"] = bool(not _overlap_t and not _overlap_a)

def _node_kinds_present(live):
    """当前 mock 页面是否已经有**文本/时间线/音频**这类节点？
    只有有这类节点，「选中它们才出现的 aria」才是「测了没有」而不是「没测到」。"""
    kinds = live.get("node_kinds_present") or []
    want = set(C.get("node_kinds", [])) - {"文本"}  # 文本节点工具条与其它不同
    return bool(want & set(kinds))


live = None
try:
    live = json.loads(READINGS.read_text(encoding="utf-8"))
except Exception:
    live = None

# 离线自洽（不需要浏览器）
out["aria_literals_carrying_a_digit"] = [a for a in REQ_A if DIGIT_RE.search(a)]
out["P1_no_literal_aria_carries_a_driftable_number_1031d"] = bool(
    not out["aria_literals_carrying_a_digit"])
out["P2_contract_has_both_calibers_1031d"] = bool(REQ_T and REQ_A and SHAPES and KINDS)

if live is None:
    out["P3_replica_matches_contract_1031d"] = None
    out["P4_replica_status_line_shape_1031d"] = None
    out["P5_replica_status_numbers_are_wired_1031d"] = None
    out["P6_shape_criterion_only_judges_saved_samples_1031d"] = None
    out["P8_node_scoped_present_when_node_exists_1031d"] = None
    out["downgraded"] = ("no browser readings => P3..P6 recorded null (downgrade, not failure)")
else:
    out["replica_readings_file"] = str(READINGS)
    tid_list = live.get("testids", [])
    aria_list = live.get("aria", [])
    if not tid_list and isinstance(live.get("n_testids"), int):
        out["note_no_tid_list"] = ("readings file only stores the COUNT of testids, "
                                   "so per-item reconciliation is impossible")
    miss_t = [t for t in REQ_T if t not in tid_list]
    miss_a = [a for a in REQ_A if a not in aria_list]
    miss_s = [k for k, v in SHAPES.items()
              if not any(re.match(v.get("pattern", r"(?!)"), a) for a in aria_list)]

    out["replica_1031d"] = {
        # 只留「缺哪些」与「有没有节点」，不留可点元素数 / 节点数 ——
        # 它们每次跑都可能不同，落仓即漂移。
        "has_nodes": bool(live.get("n_nodes")),
        "missing_testids": miss_t,
        "missing_aria_literals": miss_a,
        "missing_aria_shapes": miss_s,
        "engine_found": bool(live.get("has_engine")),
    }
    out["P3_replica_matches_contract_1031d"] = bool(
        not miss_t and not miss_a and not miss_s and out["replica_1031d"]["engine_found"])

    # ── 口径三：节点级：当前页面有没有那种节点 ──────────────────
    miss_nt = [t for t in NODE_T if t not in tid_list]
    miss_na = [a for a in NODE_A if a not in aria_list]
    out["node_scoped_missing"] = {"testids": miss_nt, "aria": miss_na}
    # ⭐ 「当前页面没有那种节点」与「有那种节点但它缺 aria」是两件事 ——
    #   前者记 `None`（没测到），后者记 `False`（测了、没有）。
    _have_node_scoped = bool(live.get("n_nodes")) and len(KINDS) > 0
    if _have_node_scoped and _node_kinds_present(live):
        out["P8_node_scoped_present_when_node_exists_1031d"] = bool(
            not miss_nt and not miss_na)
    else:
        out["P8_node_scoped_present_when_node_exists_1031d"] = None
        out["node_scoped_not_measured_because"] = (
            "当前 mock 页面只有 video 节点；契约要求 node_kinds=%s "
            "⇒ 选中那些节点才出现的条目属于「没测到」，不是「测了没有」" % (KINDS,))

    lines = list(live.get("status_lines_found", []) or [])
    saved_lines = [l for l in lines if l.endswith(SAVED_SUFFIX)]
    other_lines = [l for l in lines if not l.endswith(SAVED_SUFFIX)]

    # 产物里只留脱敏后的形状（数字一律换成 N）
    out["status_line_shapes_saved"] = sorted({NUM_RE.sub("N", l) for l in saved_lines})
    out["status_line_shapes_other"] = sorted({NUM_RE.sub("N", l) for l in other_lines})
    out["n_saved_samples"] = len(saved_lines)
    out["n_other_samples"] = len(other_lines)

    out["P4_replica_status_line_shape_1031d"] = bool(saved_lines) and all(
        SHAPE_RE.match(l) for l in saved_lines)

    # 「数字真的接在 store 上」：光看形状对是不够的，一段写死的文案同样能命中形状
    # ⇒ 要求**彼此不同的样本**，且每一行都形状合规。
    distinct = sorted(set(lines))
    out["n_status_line_samples"] = len(lines)
    out["n_distinct_status_lines"] = len(distinct)
    # ⭐⭐⭐⭐⭐ **第一版的 P5 写错了**：它要求**所有**样本都命中契约里那一条形状，
    #   而「保存中…」本来**就是另一种形状** ⇒ 一旦页面处于保存中态，P5 必红。
    #   ⇒⇒⇒ 正确形式：**每个样本的脱敏形状都必须属于「已知形状集合」**
    #   （已保存形 + 保存中形），且样本之间**必须不同** —— 后者才是
    #   「这些数字真的跟着状态变」的证据；一段写死的文案只会产出一个样本。
    KNOWN = {NUM_RE.sub("N", "0 nodes, 0 edges, 0 selected. Editable. Room connected. 已保存."),
             NUM_RE.sub("N", "0 nodes, 0 edges, 0 selected. Editable. Room connected. 保存中…")}
    shapes_seen = {NUM_RE.sub("N", l) for l in distinct}
    out["status_shapes_seen"] = sorted(shapes_seen)
    out["unknown_status_shapes"] = sorted(shapes_seen - KNOWN)
    out["P5_replica_status_numbers_are_wired_1031d"] = bool(
        len(distinct) >= 2 and not (shapes_seen - KNOWN))

    # 形状判据只在已保存样本上做 —— 所以必须**真的**有已保存样本，否则那是恒假
    out["P6_shape_criterion_only_judges_saved_samples_1031d"] = bool(
        len(saved_lines) >= 1 and len(lines) >= 1)

_P = [(k, v) for k, v in sorted(out.items())
      if re.match(r"^P\d+_", k) and k.endswith("_1031d")]
_bad = [k for k, v in _P if v is False]
io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("P 判据 = %s" % json.dumps([v for _k, v in _P], ensure_ascii=False))
print("P 为假的：", _bad or "无", "| 共 %d 条" % len(_P))
assert len(_P) >= 7, "P 判据条数掉到 7 以下了：%d" % len(_P)
print("退出码约定：0=全绿 1=有 P 判据为假 2=探针崩了/契约不是合法 JSON")
print("PROBE_1031D_DONE ->", OUT)
sys.exit(1 if _bad else 0)