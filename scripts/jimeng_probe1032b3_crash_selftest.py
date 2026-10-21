#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②b-3 的**自检**：证明「探针崩了 ⇒ 门会红」这件事**真的成立**。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**背景（本批撞出来的真缺陷）**：
契约门在探针崩掉时，**会去读「上一轮留下的旧读数」** ⇒ ⇒
「本轮没跑」被伪装成「本轮跑过了」⇒ ⇒ **门报绿** ⇒ ⇒ **假绿**。

⭐⭐⭐⭐⭐ **为什么这件事必须单独有一条门**：
它是**门的门** —— 门自己的失效模式，别人看不见 ⇒ ⇒
只有「真的把探针换成一个会崩的」才能当场证明它转红。

⭐⭐⭐⭐⭐ **本自检做四件事，缺一不可**：
  ① 探针崩 ⇒ 契约门**必须** rc≠0（门要红）
  ② `P1_probe_actually_ran_1032b3` **必须**是 `False`（不许假绿）
  ③ `probe_crashed` **必须**是 `True`（门知道「这轮没跑成」）
  ④ ⭐ `n_checks` **必须**是 `null` —— ⇒ **不许拿旧读数冒充本轮读数**
     （这一条最关键：①②③ 都可能是「门红了但读数仍是旧的」）

⚠️ **本自检不碰真源**：它在 `/tmp` 里跑一份**契约门的副本**，把 `PROBE` 指向
仓内的假崩溃探针 ⇒ ⇒ **真源产物零污染**。
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
SRC = ROOT / "scripts/jimeng_probe1032b3_mention_contract.py"
FAKE = ROOT / "scripts/jimeng_probe1032b3_fake_crash_probe.mjs"
TMP_SCRIPT = Path("/tmp/b3_crash_selftest_contract.py")
TMP_OUT = Path("/tmp/b3_crash_selftest_out.json")
OUT = ROOT / "docs/research/jimeng-canvas/inputs/crash-selftest-1032b3.json"

out = {
    "generated_by": "jimeng_probe1032b3_crash_selftest.py",
    "measured_at": "2026-10-21",
    "question": "⭐⭐⭐⭐⭐ 探针崩了的时候，这道门**真的会红**吗？"
                "（而不是拿旧读数冒充本轮读数、报一个假绿）",
    "P": {},
}

# ── 造一份「探针会崩」的契约门副本 ─────────────────────────────────────
_res = {"ok": False, "detail": "self-test 没跑成"}
try:
    _s = SRC.read_text(encoding="utf-8")
    _s = _s.replace(
        'PROBE = ROOT / "scripts/jimeng_probe1032b3_mention_runtime.mjs"',
        'PROBE = Path("%s")' % FAKE)
    _s = _s.replace(
        'OUT = GDIR / "mention-contract-1032b3.json"',
        'OUT = Path("%s")' % TMP_OUT)
    _s = _s.replace('"probe": str(PROBE.relative_to(ROOT)),', '"probe": str(PROBE),')
    if 'PROBE = Path("%s")' % FAKE not in _s or str(TMP_OUT) not in _s:
        raise RuntimeError("契约门源码形状变了 ⇒ 自检的锚点没命中（仪器坏了）")
    TMP_SCRIPT.write_text(_s, encoding="utf-8")

    _r = subprocess.run([PY, str(TMP_SCRIPT)], cwd=str(ROOT),
                        capture_output=True, text=True, timeout=600)
    _rc = _r.returncode
    _data = json.loads(TMP_OUT.read_text(encoding="utf-8")) if TMP_OUT.exists() else {}
except Exception as e:  # noqa: BLE001
    _rc = None
    _data = {}
    _res["detail"] = "self-test 没跑成: %s" % str(e)[:200]

_p1 = (_data.get("P") or {}).get("P1_probe_actually_ran_1032b3")
_detail = _data.get("P1_detail") or {}

# ── P1：门必须红 ────────────────────────────────────────────────────
out["P"]["P1_gate_goes_red_when_probe_crashes_1032b3"] = bool(
    _rc not in (0, None) and _p1 is False)
# ── P2：门知道「这轮没跑成」 ─────────────────────────────────────────
out["P"]["P2_gate_knows_it_did_not_run_1032b3"] = bool(
    _data.get("probe_crashed") is True
    and "instrument-crash" in str(_data.get("probe_run") or ""))
# ── P3：⭐ 不许拿旧读数冒充本轮读数 ──────────────────────────────────
out["P"]["P3_no_stale_readings_masquerade_1032b3"] = bool(
    _detail.get("n_checks") is None
    and _detail.get("n_raw_checks") == 0
    and not (_data.get("criteria") or {}).get("P2"))
# ── P4：真源产物零污染（自检没改真源） ───────────────────────────────
_true_golden = ROOT / "docs/research/jimeng-canvas/mention-contract-1032b3.json"
out["P"]["P4_real_product_untouched_1032b3"] = bool(
    _true_golden.exists()
    and (_true_golden.read_text(encoding="utf-8").find("/tmp/") < 0))
# ── P5：⭐⭐⭐⭐⭐ **判据形状的自我证明**：前缀型注入必须让「带引号的 token 判据」变红
#   ⇒ ⇒ 裸子串判据（`"X" in src`）对前缀注入**恒真** ⇒ ⇒ 变异体根本没生效
#   ⇒ ⇒⇒ 而这正是本批撞到的第二个仪器 bug ⇒ ⇒ 所以必须**当场证明**新形状有牙。
_prefix_ok = False
try:
    _src = Path(__file__).read_text(encoding="utf-8")
    _tok = '"P1_gate_goes_red_when_probe_crashes_1032b3"'
    _mut = _src.replace("P1_gate_goes_red_when_probe_crashes_1032b3",
                         "P1_gate_goes_red_when_probe_crashes_1032b3_BROKEN")
    _prefix_ok = ((_tok in _src) and (_tok not in _mut))
except Exception:  # noqa: BLE001
    _prefix_ok = False
out["P"]["P5_quoted_token_survives_prefix_mutation_1032b3"] = bool(_prefix_ok)

out["n_checks"] = len(out["P"])
out["n_failed"] = sum(1 for v in out["P"].values() if v is not True)
out["all_ok"] = out["n_failed"] == 0
out["detail"] = {"rc": _rc, "P1": _p1, "probe_run": _data.get("probe_run"),
                 "probe_crashed": _data.get("probe_crashed"),
                 "P1_detail": _detail}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print("P =", json.dumps(out["P"], ensure_ascii=False))
print("为假的：", ("、".join(k for k, v in out["P"].items() if v is not True) or "无"),
      "| 共 %d 条" % out["n_checks"])
print("PROBE_1032B3_CRASH_SELFTEST_DONE ->", OUT)
sys.exit(0 if out["all_ok"] else 1)
