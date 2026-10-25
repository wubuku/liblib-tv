#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1037：**「仪器故障被伪装成绿」的普查门**。

## 这道门答的是哪一个问题
  「仓里每一本产物，在**仪器已经故障**的同时，是不是还在声称**全绿**？」

## 为什么必须有这道门（1032-⑨ 实测出来的）
  1032-⑨ 那一轮跑册子（1015）时，**node 不在 PATH**
  （`launchctl submit` 不继承 nvm 的 PATH ⇒ 而那正是那一轮的启动方式）。
  ⇒ 6 本依赖 node 的探针产物因此降级。
  ⇒ 其中 4 本（b2/b3/b4/c）把判据降级成 `None` ⇒ **降级是可见的** ⇒ 没问题。
  ⇒ ⇒⇒ 而 **1032a 与 1032b1 却「继续读上一轮留下的读数文件」**
  ⇒ ⇒⇒ ⇒ 于是它们算出 **P1..P7 / P1..P8 全 true**、rc=0
  ⇒ ⇒⇒ ⇒ ⇒ 1015 把它们记成 `state=reproduced` ⇒ ⇒ ⇒ ⇒ **零红判据 ⇒ 假绿**
  ⇒ ⇒⇒ ⇒ ⇒ ⇒ ★ 那两本产物的形状是：**「探针自己说它失败了」＋「判据全 true」**。

  ⭐⭐⭐⭐⭐ **本门不查「哪本探针跑过」⇒ ⇒ 而查「产物的自述之间自相矛盾吗」**
  ⇒ ⇒ ⇒ ⇒ 因为「产物说自己失败了、却同时说自己全过了」是**自相矛盾**
  ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而矛盾不需要知道当时发生了什么 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ★ **可普查、可回归**

## 判据口径
  · **失败信号**（产物自己说「这轮没测成」）：
      - `probe_crashed` 为 true
      - `readings_available` 为 false
      - `readings_fresh` 为 false
      - `probe_run` 里出现 `probe failed` / `INSTRUMENT_CRASH` / `instrument-crash`
        / `No such file or directory` / `rc=2`
  · **绿信号**：某个判据集合**非空且全部为 true**
  · **假绿** = 失败信号 ∧ 绿信号 ⇒ ⇒ 「没测到」与「测过了」被写进了同一本产物

## 三态退出码
  0 = 判据全绿 / 1 = 判据红 / 2 = 仪器崩（数据侧问题）。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs" / "research" / "jimeng-canvas"
OUT = GDIR / "instrument-fake-green-census-1037.json"

# ── 「这轮探针没跑成」的文本信号 ───────────────────────────────────────
FAIL_RUN_RE = re.compile(
    r"(probe failed|INSTRUMENT_CRASH|instrument-crash"
    r"|No such file or directory|^rc=2)", re.M)

# ── 判据集合放在哪几个字段里 ───────────────────────────────────────────
CRIT_HOLDERS = ("criteria", "criteria_1015", "P")
TOP_P_RE = re.compile(r"^P\d+_")


def _crit_sets(obj):
    """产物里的判据集合 ⇒ [(名字, 判据dict)]。"""
    out = []
    if not isinstance(obj, dict):
        return out
    for h in CRIT_HOLDERS:
        v = obj.get(h)
        if isinstance(v, dict) and v:
            out.append((h, v))
    top = {k: v for k, v in obj.items()
           if TOP_P_RE.match(k) and isinstance(v, bool)}
    if top:
        out.append(("<顶层 P*>", top))
    return out


def _failure_signals(obj):
    """产物自报的「这轮没测成」信号 ⇒ 列表（空列表 = 没这类自述）。"""
    sig = []
    if not isinstance(obj, dict):
        return sig
    if obj.get("probe_crashed") is True:
        sig.append("probe_crashed=true")
    if obj.get("readings_available") is False:
        sig.append("readings_available=false")
    if obj.get("readings_fresh") is False:
        sig.append("readings_fresh=false")
    pr = obj.get("probe_run")
    if isinstance(pr, str) and FAIL_RUN_RE.search(pr):
        sig.append("probe_run=%s" % pr[:160])
    det = obj.get("detail")
    if isinstance(det, dict):
        pr2 = det.get("probe_run")
        if isinstance(pr2, str) and FAIL_RUN_RE.search(pr2):
            sig.append("detail.probe_run=%s" % pr2[:160])
    return sig


def _green_sets(obj):
    """「声称全绿」的判据集合 ⇒ [(名字, 判据dict)]。"""
    return [(n, d) for n, d in _crit_sets(obj)
            if all(v is True for v in d.values())]


def fake_green_reasons(obj):
    """这本产物是不是「仪器故障却声称全绿」？⇒ 理由列表。"""
    sig = _failure_signals(obj)
    if not sig:
        return []
    greens = _green_sets(obj)
    return [{"signals": sig, "green_holder": n, "n_criteria": len(d),
             "criteria": sorted(d.keys())} for n, d in greens]


# ── ⭐⭐⭐⭐⭐ 注入式反证：**探测器自己必须能失败、也必须放过干净样本** ──
#   ⇒ ⇒ ⇒ 只拿真实产物验，验不出「探测器恒真」⇒ ⇒ ⇒ ⇒ 所以要注入已知答案的样本
#   ⇒ ⇒ ⇒ 阳性对照 = 已知是假绿的样本 ⇒ ⇒ 必须全被抓到
#   ⇒ ⇒ ⇒ 阴性对照 = 已知不是假绿的样本 ⇒ ⇒ 必须全不被抓到
INJECT_FAKE = [
    {"name": "旧形状：probe_run 说失败、判据全 true",
     "artifact": {"generated_by": "inject-1037",
                  "probe_run": "probe failed: [Errno 2] No such file or directory: 'node'",
                  "criteria": {"P1": True, "P2": True}}},
    {"name": "自报崩 + 顶层 P 全 true",
     "artifact": {"generated_by": "inject-1037", "probe_crashed": True,
                  "P1_x": True, "P2_y": True}},
    {"name": "读数不可用 + criteria_1015 全 true",
     "artifact": {"generated_by": "inject-1037", "readings_available": False,
                  "criteria_1015": {"P1_hold_1015": True}}},
    {"name": "读数不新鲜 + P 集合全 true",
     "artifact": {"generated_by": "inject-1037", "readings_fresh": False,
                  "P": {"P1": True, "P2": True}}},
    {"name": "rc=2 仪器崩 + 判据全 true",
     "artifact": {"generated_by": "inject-1037", "probe_run": "rc=2 instrument-crash",
                  "criteria": {"P1": True}}},
]
INJECT_HEALTHY = [
    {"name": "全绿且仪器正常",
     "artifact": {"generated_by": "inject-1037", "probe_run": "rc=0",
                  "probe_crashed": False, "readings_available": True,
                  "readings_fresh": True,
                  "criteria": {"P1": True, "P2": True}}},
    {"name": "降级但不声称绿（判据 None）",
     "artifact": {"generated_by": "inject-1037", "probe_crashed": True,
                  "readings_available": False,
                  "criteria": {"P1": None, "P2": None}}},
    {"name": "判据红（不是假绿）",
     "artifact": {"generated_by": "inject-1037", "probe_run": "rc=1",
                  "criteria": {"P1": False, "P2": True}}},
    {"name": "只有静态判据、没有运行时自述",
     "artifact": {"generated_by": "inject-1037",
                  "criteria": {"P1_static": True}}},
]

# ── 结构性纪律：统一工具链 ─────────────────────────────────────────────
NODE_SPAWN_RE = re.compile(r'subprocess\.run\(\s*\[\s*"node"')


def node_toolchain_structure():
    """「node 可用性只有一个实现」的结构读数。

    ⇒ ⇒ ⇒ **凡是 import 了 `jimeng_node_toolchain` 的脚本** ⇒ ⇒ 不许自己 spawn node
    ⇒ ⇒ ⇒⇒ 而「还在直接 spawn node」的脚本清单 ⇒ ⇒ 必须**发布**（迁移待办）
    ⇒ ⇒ ⇒⇒ ⇒ ⇒ ★ 清单会随整改变短 ⇒ ⇒ ⇒⇒ ⇒ ⇒ 而它进产物 ⇒ ⇒ ⇒⇒ 就是可回归的
    """
    direct = []
    migrated_but_direct = []
    for p in sorted((ROOT / "scripts").glob("*.py")):
        if p.name == "jimeng_node_toolchain.py":
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        if not NODE_SPAWN_RE.search(txt):
            continue
        direct.append(p.name)
        if "jimeng_node_toolchain" in txt:
            migrated_but_direct.append(p.name)
    return direct, migrated_but_direct


def volatile_violations(obj):
    """`volatile: true` ⇒ 必须有非空 `volatile_why` ⇒ 否则「不稳定」没有出处。"""
    if not isinstance(obj, dict):
        return []
    if obj.get("volatile") is not True:
        return []
    why = obj.get("volatile_why")
    if isinstance(why, str) and why.strip():
        return []
    return ["volatile=true 但 volatile_why 缺失或为空"]


def main():
    # ── 扫产物目录（顶层 *.json；`inputs/` 是原始读数、`contracts/` 是契约快照）──
    files = sorted(p for p in GDIR.glob("*.json") if p.name != OUT.name)
    n_files_dir = len(list(GDIR.glob("*.json")))

    verdicts = []
    fake_rows = []
    r2_rows = []
    r3_rows = []
    r4_rows = []
    n_with_criteria = 0
    n_unreadable = 0

    for p in files:
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:                                # noqa: BLE001
            verdicts.append({"file": p.name, "readable": False,
                             "note": "JSON 读不出：%s" % str(e)[:120]})
            n_unreadable += 1
            continue
        sig = _failure_signals(obj)
        greens = _green_sets(obj)
        cs = _crit_sets(obj)
        if cs:
            n_with_criteria += 1
        reasons = fake_green_reasons(obj)
        if reasons:
            fake_rows.append({"file": p.name, "reasons": reasons})
        # ⭐⭐⭐⭐⭐ R2：**可用性与新鲜度必须同时声明** ⇒ ⇒ 不许半截
        #   ⇒ ⇒ 「有读数」却不新鲜 = 半个真相 ⇒ ⇒ 而半个真相正是假绿的温床
        #   ⇒ ⇒ ⇒⇒ 而这条与字段布局无关 ⇒ ⇒ ⇒⇒ 所以对所有产物一视同仁
        _has_avail = "readings_available" in obj
        _has_fresh = "readings_fresh" in obj
        if _has_avail != _has_fresh:
            r2_rows.append({"file": p.name,
                            "readings_available": obj.get("readings_available"),
                            "readings_fresh": obj.get("readings_fresh")})
        # R3：读数不新鲜 ⇒ 不许说「读数可用」
        if obj.get("readings_fresh") is False and obj.get("readings_available") is not False:
            r3_rows.append({"file": p.name,
                            "readings_fresh": False,
                            "readings_available": obj.get("readings_available")})
        # R4：volatile 声明必须有出处
        for v in volatile_violations(obj):
            r4_rows.append({"file": p.name, "why": v})
        verdicts.append({
            "file": p.name,
            "readable": True,
            "has_failure_signal": bool(sig),
            "failure_signals": sig,
            "n_criteria_sets": len(cs),
            "green_holders": [n for n, _ in greens],
            "verdict": "FAKE_GREEN" if reasons else "ok",
        })

    # ── 注入式反证 ──────────────────────────────────────────────────────
    inj_fake = [{"name": c["name"], "caught": bool(fake_green_reasons(c["artifact"]))}
                for c in INJECT_FAKE]
    inj_healthy = [{"name": c["name"], "flagged": bool(fake_green_reasons(c["artifact"]))}
                    for c in INJECT_HEALTHY]
    all_fake_caught = all(c["caught"] for c in inj_fake)
    no_healthy_flagged = not any(c["flagged"] for c in inj_healthy)

    direct, migrated_but_direct = node_toolchain_structure()

    crit = {
        # ⭐ 覆盖：每个产物都必须有 verdict ⇒ 不许「漏扫」
        #   ⇒ ⇒ 而「读不出 JSON」也是漏扫的一种 ⇒ ⇒ ⇒ 所以它也必须为 0
        "P1_scan_coverage_1037": (len(verdicts) == len(files)
                                  and n_unreadable == 0),
        # ⭐⭐⭐ 核心：没有产物在仪器故障的同时声称全绿
        "P2_no_fake_green_1037": len(fake_rows) == 0,
        # ⭐ 运行时产物必须**同时**声明「有读数」与「读数是本轮的」
        "P3_reading_declaration_complete_1037": len(r2_rows) == 0,
        "P4_stale_readings_not_available_1037": len(r3_rows) == 0,
        # ⭐ 注入式反证：探测器必须能失败、也必须放过干净样本
        "P5_injection_fake_all_caught_1037": all_fake_caught,
        "P6_injection_healthy_none_flagged_1037": no_healthy_flagged,
        "P7_volatile_declares_why_1037": len(r4_rows) == 0,
        # ⭐ 结构性纪律：已迁移到统一工具链的脚本不许自己 spawn node
        "P8_migrated_scripts_use_toolchain_1037": len(migrated_but_direct) == 0,
    }
    out = {
        "generated_by": "jimeng_probe1037_instrument_fake_green_census.py",
        "target": "jimeng-canvas-instrument-fake-green",
        "question": "⭐⭐⭐⭐⭐ **有没有产物在仪器故障的同时声称全绿？**",
        "n_artifacts_scanned": len(files),
        "n_artifacts_with_criteria": n_with_criteria,
        "n_fake_green": len(fake_rows),
        "fake_green": fake_rows,
        "verdicts": verdicts,
        "violations_r2_crashed_but_available": r2_rows,
        "violations_r3_stale_but_available": r3_rows,
        "violations_r4_volatile_without_why": r4_rows,
        "injection": {"fake": inj_fake, "healthy": inj_healthy,
                      "all_fake_caught": all_fake_caught,
                      "no_healthy_flagged": no_healthy_flagged},
        "node_toolchain_1037": {
            "n_direct_spawn_scripts": len(direct),
            "direct_spawn_scripts": direct,
            "migrated_but_direct_spawn": migrated_but_direct,
            "note": "⭐ 清单是**迁移待办**⇒ ⇒ 凡是 import 了 jimeng_node_toolchain "
                    "的脚本 ⇒ ⇒ 就必须走统一入口 ⇒ ⇒ ⇒ 而自己 spawn node 的 ⇒ ⇒ 判红。",
        },
        "excluded": {"file": OUT.name,
                     "why": "⭐ 本门扫的就是这个目录 ⇒ ⇒ 而它自己也在目录里 ⇒ ⇒ "
                            "自引用会让自己不收敛 ⇒ ⇒ ⇒ 所以排除自己、且登记为什么。"},
        "criteria": crit,
        "criterion_kinds_1037": {k: "failure" for k in crit},
    }
    out["criterion_kinds_complete_1037"] = (
        set(out["criterion_kinds_1037"]) == set(crit))

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    red = [k for k, v in crit.items() if v is False]
    print("扫产物 %d 本（目录里顶层 json %d 本、本门自己的产物不扫自己）/ 带判据 %d 本"
          % (len(files), n_files_dir, n_with_criteria))
    print("假绿 %d 本 %s"
          % (len(fake_rows), [r["file"] for r in fake_rows] or ""))
    print("注入式反证：阳性 %d/%d 抓到 | 阴性 %d/%d 放过"
          % (sum(1 for c in inj_fake if c["caught"]), len(inj_fake),
             sum(1 for c in inj_healthy if not c["flagged"]), len(inj_healthy)))
    print("直接 spawn node 的脚本 %d 个（已迁移却自己 spawn 的 %d 个）"
          % (len(direct), len(migrated_but_direct)))
    print("判据逐条 = " + " | ".join("%s=%s" % (k, crit[k]) for k in crit))
    print("P 为假的： " + (", ".join(red) if red else "无"))
    print("PROBE_1037_INSTRUMENT_FAKE_GREEN_CENSUS_DONE -> %s" % OUT)
    return 0 if not red else 1


if __name__ == "__main__":
    sys.exit(main())
