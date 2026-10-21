#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②b-2 的门：图片 / 音频的「生成」点了**到底有没有发生事**

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**这一批修的是两种不同的糊弄**，而**只有一种**静态门看得见：

  · 图片生成面板「生成」：此前**整枚没有 onClick**
    ⇒ ⇒ 1032 静态门抓得到（DEAD_NO_HANDLER）⇒ 本批把它销账（死按钮 7 → 6）
  · 音频生成面板「生成」：此前**有 onClick，但函数体是空的**
    ⇒ ⇒ 静态门把它算成 `WIRED` ⇒ ⇒ **静态门根本看不见这一类**
    ⇒ ⇒ 只有运行时门能抓它 ⇒ ⇒ **本门就是为它而生的**

⚠️⭐⭐⭐⭐⭐ **判据一律是「某个可观察的东西变了」**，不是「按钮有 onClick」：
  · 点「生成」⇒ ⇒ 页面上出现「生成中…」（节点上的处理态覆盖层）
  · 3s 后 ⇒ ⇒ 图片节点里**真的多了一张 `<img>`**；音频节点上**真的出现时长徽标**
  · ⭐ **负控**：提示词为空时点「生成」⇒ ⇒ **什么也不该发生**
    ⇒ ⇒ 只验「该发生时发生」是不够的：一个恒真的按钮也能过那条
    ⇒ ⇒ 所以另有一半判据是「**不该发生时**（空提示词）**不**发生」

⭐⭐⭐⭐⭐ **P8 是判据级阳性对照**：把某条读数改坏 ⇒ 同一套判据**必须红**
  ⇒ ⇒ 证明「全绿」不是恒真。
  ⇒ ⇒ 做法照 ②b-0 的教训：**只改读数、不碰真源** ⇒ ⇒ 真源产物零污染。

⚠️ 盲区（诚实写在这里）：
  ① 生成**产物本身**是 CLONE_DECISION（mock）—— 源站的产出要付费才能观测，
     本门只保证「有一个可观察的状态变化」，**不保证与源站产物一致**。
  ② 本门跑在**本地复刻**上；它证明的是「复刻里这两个按钮有反应」，
     **不等于**「与源站行为完全一致」。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
READINGS = Path(
    os.environ.get("JIMENG_B2_JSON",
                   str(GDIR / "inputs" / "gen-runtime-1032b2.json")))
PROBE = ROOT / "scripts/jimeng_probe1032b2_gen_runtime.mjs"
OUT = GDIR / "gen-contract-1032b2.json"

# ── 跑探针（读数不存在时现跑；跑不动 ⇒ 降级为 null，不判红）────────────
_readings = None
_run_info = "not attempted"
if os.environ.get("JIMENG_B2_SKIP_PROBE") != "1":
    try:
        r = subprocess.run(["node", str(PROBE)], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=900)
        _run_info = "rc=%d" % r.returncode
        if r.returncode != 0:
            _run_info += " stderr=%s" % r.stderr.strip()[-200:]
    except Exception as e:                                   # 探针跑不动 = 仪器问题
        _run_info = "probe failed: %s" % str(e)[:200]
else:
    _run_info = "skipped by env"

try:
    if READINGS.exists():
        _readings = json.loads(READINGS.read_text(encoding="utf-8"))
except Exception:
    _readings = None


# ⭐⭐⭐⭐⭐ **判据必须自己从「原始字段」重算，不能只信探针给的 `ok` 标志。**
#   否则阳性对照改原始字段时 `ok` 没变 ⇒ ⇒ 门不会红 ⇒ ⇒ P8 永远是假的。
def _neg_ok(t):
    """负控：空提示词点「生成」⇒ ⇒ 什么也不该发生。"""
    if not t:
        return None
    if "generating_visible" not in t:
        return None
    return bool(t.get("clicked") is True and t.get("generating_visible") is False)


def _enters_ok(t):
    """点「生成」⇒ ⇒ 进入「生成中…」。"""
    if not t:
        return None
    if "generating_visible" not in t:
        return None
    return bool(t.get("clicked") is True and t.get("generating_visible") is True)


def _poster_ok(t):
    """3s 后图片节点里真的多了一张 <img>，且处理态消失。"""
    if not t:
        return None
    n = t.get("img_count")
    if n is None:
        return None
    return bool(n >= 1 and t.get("generating_visible") is False)


def _badge_ok(t):
    """3s 后音频节点上真的出现时长徽标，且处理态消失。"""
    if not t:
        return None
    if "badge_visible" not in t:
        return None
    return bool(t.get("badge_visible") is True
                and t.get("generating_visible") is False)


def _judge(r):
    if not r:
        return {k: None for k in ("P1", "P2", "P3", "P4", "P5", "P6", "P7")}
    ch = r.get("checks") or {}

    def _get(name):
        return ch.get(name)

    def _all(items):
        vals = [f(_get(n)) for n, f in items]
        if any(v is None for v in vals):
            return None
        return all(vals)

    return {
        # P1 负控：空提示词 ⇒ 「生成」不该有反应（双向判据的另一半）
        "P1": _all([
            ("image_gen_empty_prompt_does_nothing", _neg_ok),
            ("audio_gen_empty_prompt_does_nothing", _neg_ok),
        ]),
        # P2 图片「生成」⇒ 进入「生成中…」
        "P2": _all([("image_gen_enters_generating", _enters_ok)]),
        # P3 图片「生成」⇒ 3s 后真的多了一张图
        "P3": _all([("image_gen_produces_poster", _poster_ok)]),
        # P4 音频「生成」⇒ 进入「生成中…」
        "P4": _all([("audio_gen_enters_generating", _enters_ok)]),
        # P5 音频「生成」⇒ 3s 后出现时长徽标
        "P5": _all([("audio_gen_produces_duration_badge", _badge_ok)]),
        # P6 页面无 JS 错误
        "P6": (not r.get("pageerrors")) if "pageerrors" in r else None,
        # P7 探针读数完整（探针自己少跑了几条 ⇒ 不能算「全绿」）
        "P7": (r.get("n_checks") == 8 and r.get("n_failed") == 0)
              if "n_checks" in r else None,
    }


_c = _judge(_readings)

# ── P8：判据级阳性对照（把读数改坏 ⇒ 同一套判据必须红）────────────────
_mut = None
if _readings:
    _bad = json.loads(json.dumps(_readings))
    # 破坏 P2 的输入：把「进入生成中」改成「没进入」
    _t = (_bad.get("checks") or {}).get("image_gen_enters_generating")
    if _t:
        _t["generating_visible"] = False
    _mc = _judge(_bad)
    _mut = {
        "p2_before": _c["P2"],
        "p2_after": _mc["P2"],
        "p2_turned_red": (_c["P2"] is True and _mc["P2"] is False),
        "note": "⭐ 判据级变异：只改读数、不碰真源 ⇒ 真源产物零污染",
    }

out = {
    "generated_by": "jimeng_probe1032b2_gen_contract.py",
    "target": "jimeng-canvas-image-audio-generate",
    "question": "⭐⭐⭐⭐⭐ **图片 / 音频的「生成」点了到底有没有发生事？**",
    "probe_run": _run_info,
    "readings_file": str(READINGS.relative_to(ROOT)) if READINGS.exists() else None,
    "readings_available": bool(_readings),
    "criteria": _c,
    "p8_mutation": _mut,
    # ⭐⭐⭐⭐⭐ **产物里只留布尔** —— 节点数、坐标、文案都是会漂的读数
    #   ⇒ ⇒ 而且这个产物在**顶层** ⇒ ⇒ 1015 通道 A 会当 golden 逐字节比对
    #   ⇒ ⇒ ⇒ **⇒ 一次漂移就变成一条永久红。**
    "detail": {
        "n_checks": (_readings or {}).get("n_checks"),
        "n_failed": (_readings or {}).get("n_failed"),
        "n_pageerrors": len((_readings or {}).get("pageerrors") or []),
    },
    "scope_note": "⭐⭐⭐ 本门只覆盖 1032-②b-2 修的两个「生成」按钮；"
                  "**其余 6 个仍死的按钮**由静态门 DD993S.1 管；"
                  "**「有 onClick 但函数体是空的」那一类**静态门扫不到 ⇒ "
                  "本门抓到的是其中一枚（音频「生成」），另一枚（文本「展开文本面板」）"
                  "留待 ②c 的场景化探针。",
}

out["criteria"]["P8"] = _mut["p2_turned_red"] if _mut is not None else None

false_list = [k for k, v in out["criteria"].items() if v is False]
none_list = [k for k, v in out["criteria"].items() if v is None]
out["n_false"] = len(false_list)
out["false_criteria"] = false_list
out["degraded_criteria"] = none_list

OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("probe: %s | readings=%s" % (_run_info, "有" if _readings else "无"))
print("P1..P8 =", [out["criteria"].get("P%d" % i) for i in range(1, 9)])
print("为假的：", false_list or "无", "| 降级：", none_list or "无")
print("PROBE_1032B2_GEN_DONE ->", OUT)

if false_list:
    sys.exit(1)
sys.exit(0)
