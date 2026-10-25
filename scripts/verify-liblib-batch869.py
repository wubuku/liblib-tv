#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 869 门禁：★ 「当前帧关键帧」的**命中窗口**必须等于源站逐字的 ±0.05s。

## ★ 本批在做什么（★ 一句话说清）

★ 源站 chunk `cZ`（★ 逐字在库）里三处都用**同一个 0.05 秒窗口**：
  命中（`f`）⟹ `.05>=Math.abs(e.time-h)`；
  上一（`m`）⟹ `n.time<t-.05`；
  下一（`x`）⟹ `e.time>h+.05`。
★ 而 clone 把这三处**分散在两个文件里、各写各的**、且用的是 **1e-3** ⟹ ⟹ ⟹ ⟹ ⇒ ★
★ **差 50 倍** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 后果（★ 逐字）：★ 播头在 `0.04s`、关键帧在 `0s`
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 源站判「当前帧**有**关键帧」（★ 可点它＝**移除**那一枚）
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而 clone 判「**无**」⟹ ⟹ ⟹ ⟹ ⇒ ★ 可点它＝**再加一枚**
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 两边**决策相反**；★ 且「上一关键帧」在源站是 **disabled**
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而 clone 给它点亮了。

★ 本批把「命中／取点」收成**一个出处**（`directorKeyframeWindow.ts`），
★ 并把 **±0.05s** 写成**从源站原文解析出来的数**（★ 不许手打）。

## ★ 判据构成

- **S1–S4 源站证据在库**：★ `cZ` 逐字、★ i18n 逐字、★ batch36 逐字规格
- **S5–S6 ★★ 窗口常量与源站同源**：★ 常量值 **等于从 `cZ` 解析出的数**
  ⟹ ⟹ ⟹ ⟹ ⇒ ★ 且**命中窗口 ≠ upsert 容差**（★ 两个容差必须分开）
- **S7–S8 ★★ 命中只有一个出处**：★ 时间轴与检查器都 import 共享函数；
  ⟹ ⟹ ⟹ ⟹ ⇒ ★ 且这两个文件里**不再有**裸的 `0.001` 命中容差
- **S9 ★★ 工具条「添加关键帧」仍是 upsert**：★ ★ 本批**撤回**了
  「改成切换」的错误方向 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 这条是**守住修复**
- **S10–S12 ★★ 运行时读数在库**：★ 13 条判据全绿、★ 播头**真的**被放到
  ★ +0.04s／+0.2s、★ 读回的 aria 文案**等于源站 i18n 逐字**
- **S13 ★★ 负控证据在库**：★ 含**运行时负控**（★ 改回 1e-3 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 探针必须报红）
- **S14–S15 ★★ 866 门禁已改成动态解析在用清单**

## ★ 纪律

- ★ 期望值**只从实测解析**（★ 从 `raw/` 里的源站原文解析），不凭记忆手打；
- ★ 「全文含某串」类判据 ⟹ ⟹ ⟹ ⟹ ⇒ ★ **必须剥掉注释**再查；
- ★ **不写死判据条数** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 改成**结构性断言**
  （★ 「非空 ∧ 每条为真 ∧ 失败数与实际统计一致」）；
- ★ 判据**不许**写死行号（★ 定位靠 needle 唯一命中）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch869-2026-10-01"
RAW = OUT_DIR / "raw"

CZ = RAW / "source-869-cz-toggle.txt"
I18N = RAW / "source-869-i18n-dictionary.txt"
SPEC = RAW / "source-869-batch36-spec.md"
CORRECTION = RAW / "source-869-correction.md"
RUNTIME = RAW / "keyframe-window-869.json"
NEGATIVE = RAW / "negative-audit-869.json"

WINDOW_MODULE = ROOT / "src/components/director/directorKeyframeWindow.ts"
TIMELINE = ROOT / "src/components/director/DirectorTimeline.tsx"
INSPECTOR = ROOT / "src/components/director/DirectorInspector.tsx"
STORE = ROOT / "src/store/directorStore.ts"
GATE866 = ROOT / "scripts/verify-liblib-batch866.py"
REGRESS869 = OUT_DIR / "probes/regress869.py"
REGRESS868 = (ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
              / "probes/regress868.py")


# ── 断言器（★ 失败要能看清「读的是哪个量」）────────────────────────────
class Verifier:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def check(self, name: str, ok: bool, detail: Any = None) -> bool:
        self.rows.append({"判据": name, "通过": bool(ok), "证据": detail})
        return bool(ok)

    def report(self) -> int:
        bad = [r for r in self.rows if not r["通过"]]
        print("★ batch 869 门禁：%d 条判据，%d 失败" % (len(self.rows), len(bad)))
        for r in self.rows:
            print("  %s %s" % ("PASS" if r["通过"] else "FAIL", r["判据"]))
            if not r["通过"]:
                print("      证据：%s" % json.dumps(r["证据"], ensure_ascii=False))
        (RAW / "gate-869.json").write_text(
            json.dumps({"判据": self.rows,
                        "失败数": len(bad),
                        "总条数": len(self.rows)},
                       ensure_ascii=False, indent=1),
            encoding="utf-8")
        return 1 if bad else 0


def strip_comments(text: str) -> str:
    """★ 剥掉 `//` 与 `/* */`（★ 状态机 ⟹ ⟹ ⟹ ⇒ ★ 不把字符串里的 `//` 当注释）。"""
    out: list[str] = []
    i, n = 0, len(text)
    quote: str | None = None
    while i < n:
        ch = text[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "\"'`":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def num(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_gates(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in
            re.finditer(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', text)]


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {}

    # ── S1 源站证据在库 ────────────────────────────────────────────────
    for path, label in ((CZ, "cZ 逐字"), (I18N, "i18n 逐字"),
                        (SPEC, "batch36 逐字规格"), (CORRECTION, "更正记录")):
        v.check("source:the-%s-evidence-is-in-the-repo" % label.split()[0],
                path.exists(),
                detail={"路径": str(path.relative_to(ROOT)), "存在": path.exists()})

    cz = CZ.read_text(encoding="utf-8") if CZ.exists() else ""
    i18n = I18N.read_text(encoding="utf-8") if I18N.exists() else ""
    spec = SPEC.read_text(encoding="utf-8") if SPEC.exists() else ""

    # ★ ★★ S2：★ 三处窗口必须**同数** ⟹ ⟹ ⟹ ⇒ ★ 且那个数要从原文**解析**
    m_hit = re.search(r"([\d.]+)>=Math\.abs\(e\.time-h\)", cz)
    m_prev = re.search(r"n\.time<t-([\d.]+)", cz)
    m_next = re.search(r"e\.time>h\+([\d.]+)", cz)
    nums = {
        "命中": num(m_hit.group(1)) if m_hit else None,
        "上一": num(m_prev.group(1)) if m_prev else None,
        "下一": num(m_next.group(1)) if m_next else None,
    }
    audit["源站三处窗口"] = nums
    v.check("source:the-three-source-windows-agree-on-one-number",
            all(x is not None for x in nums.values())
            and len(set(nums.values())) == 1,
            detail={"解析结果": nums,
                    "★ 出处": "★ `raw/source-869-cz-toggle.txt` 里源站 chunk 的 `cZ`"})

    window = nums["命中"]
    v.check("source:the-source-toggle-action-is-verbatim",
            'action:f?"remove":"add"' in cz,
            detail={"needle": 'action:f?"remove":"add"', "命中": 'action:f?"remove":"add"' in cz})
    v.check("source:the-source-disabled-rules-are-verbatim",
            "disabled:!m" in cz and "disabled:!x" in cz,
            detail={"disabled:!m": "disabled:!m" in cz,
                    "disabled:!x": "disabled:!x" in cz})

    # ── S3 i18n 逐字 ───────────────────────────────────────────────────
    m_vis = re.search(r'"directorTimelineCurrentKeyframeVisible":"([^"]+)"', i18n)
    m_hid = re.search(r'"directorTimelineCurrentKeyframeHidden":"([^"]+)"', i18n)
    aria_visible = m_vis.group(1) if m_vis else None
    aria_hidden = m_hid.group(1) if m_hid else None
    audit["源站 aria 文案"] = {"可见": aria_visible, "不可见": aria_hidden}
    v.check("source:the-source-aria-copy-is-in-the-repo",
            aria_visible is not None and aria_hidden is not None,
            detail={"可见": aria_visible, "不可见": aria_hidden})

    # ── S4 batch36 逐字规格 ───────────────────────────────────────────
    needles = [
        "◆ 添加关键帧",
        "captures the selected track object's complete current value",
        "same-time add replaces the existing keyframe value",
    ]
    missing = [n for n in needles if n not in spec]
    v.check("source:the-source-batch36-spec-is-in-the-repo",
            not missing,
            detail={"缺的片段": missing,
                    "★ 出处": "★ `raw/source-869-batch36-spec.md`（★ 源站逐字规格）"})

    # ── S5 ★★ 共享窗口常量 == 源站解析出的数 ─────────────────────────
    wm = WINDOW_MODULE.read_text(encoding="utf-8") if WINDOW_MODULE.exists() else ""
    wm_code = strip_comments(wm)
    m_const = re.search(
        r"DIRECTOR_SOURCE_KEYFRAME_HIT_WINDOW\s*=\s*([\d.]+(?:e-?\d+)?)",
        wm_code)
    const_val = num(m_const.group(1)) if m_const else None
    audit["共享窗口常量"] = const_val
    v.check("source:the-shared-window-constant-equals-the-source-number",
            const_val is not None and window is not None
            and abs(const_val - window) < 1e-12,
            detail={"源码常量": const_val, "源站解析值": window,
                    "★ 说明": "★ 期望值**从源站原文解析** ⟹ ⟹ 不手打"})

    # ── S6 ★★ 命中窗口 ≠ upsert 容差（★ 两个容差必须分开）────────────
    m_eps = re.search(
        r"DIRECTOR_KEYFRAME_EPSILON\s*=\s*([\d.]+(?:e-?\d+)?)", wm_code)
    eps_val = num(m_eps.group(1)) if m_eps else None
    audit["upsert 容差"] = eps_val
    v.check("source:the-hit-window-and-the-upsert-epsilon-are-different-numbers",
            eps_val is not None and const_val is not None
            and abs(eps_val - const_val) > 1e-12,
            detail={"命中窗口": const_val, "upsert 容差": eps_val,
                    "★ 出处": "★ `SOURCE_ANALYSIS.md` §23.3 ＝ upsert epsilon"})

    # ── S7 ★★ 命中只有一个出处 ───────────────────────────────────────
    tl = strip_comments(TIMELINE.read_text(encoding="utf-8")) \
        if TIMELINE.exists() else ""
    ins = strip_comments(INSPECTOR.read_text(encoding="utf-8")) \
        if INSPECTOR.exists() else ""
    imports_shared = {
        "DirectorTimeline.tsx": "directorKeyframeHit" in tl,
        "DirectorInspector.tsx": "directorKeyframeHit" in ins,
    }
    v.check("source:the-hit-window-has-a-single-origin",
            all(imports_shared.values()),
            detail=imports_shared)

    # ── S8 ★★ UI 两处不再有裸的 1e-3 命中容差 ─────────────────────────
    bare = {
        "DirectorTimeline.tsx": re.findall(r"0\.001|1e-3", tl),
        "DirectorInspector.tsx": re.findall(r"0\.001|1e-3", ins),
    }
    v.check("source:the-timeline-and-the-inspector-carry-no-bare-hit-epsilon",
            not bare["DirectorTimeline.tsx"]
            and not bare["DirectorInspector.tsx"],
            detail={"残留": bare,
                    "★ 说明": "★ **剥注释后**查 ⟹ ⟹ 注释里提到 0.001 不算"})

    # ── S9 ★★ 工具条「添加关键帧」仍是 upsert（★ 守住本批的撤回）─────
    m_add = re.search(
        r"data-director-add-keyframe", tl)
    add_block = tl[m_add.start(): m_add.start() + 900] if m_add else ""
    store_code = strip_comments(STORE.read_text(encoding="utf-8")) \
        if STORE.exists() else ""
    store_upsert = re.search(
        r"addTimelineKeyframe:.*?upsertTrackKeyframe", store_code, re.S)
    v.check("source:the-toolbar-add-keyframe-stays-an-upsert",
            bool(m_add) and "addTimelineKeyframe" in add_block
            and bool(store_upsert),
            detail={"工具条命中 data-director-add-keyframe": bool(m_add),
                    "工具条块里走 addTimelineKeyframe":
                        "addTimelineKeyframe" in add_block,
                    "store 里 addTimelineKeyframe→upsertTrackKeyframe":
                        bool(store_upsert),
                    "★ 出处": "★ batch36 逐字规格：「取当前值、同时刻覆盖」"})

    # ── S10 ★★ 运行时读数在库且全绿 ──────────────────────────────────
    runtime: dict[str, Any] = {}
    if RUNTIME.exists():
        runtime = json.loads(RUNTIME.read_text(encoding="utf-8"))
    rows = runtime.get("判据") or []
    failed_rows = [r for r in rows if not r.get("通过")]
    v.check("runtime:the-keyframe-window-probe-readings-are-in-the-repo",
            bool(rows) and not failed_rows
            and runtime.get("失败数") == len(failed_rows)
            and isinstance(runtime.get("失败数"), int),
            detail={"判据条数": len(rows), "失败条数": len(failed_rows),
                    "读数自记的失败数": runtime.get("失败数"),
                    "★ 说明": "★ **不写死条数** ⟹ ⟹ 改成「非空 ∧ 全真 ∧ 自洽」"})

    # ── S11 ★★ 播头真的被放到 +0.04s ／ +0.2s（★ 证明不是空判）────────
    init = runtime.get("初始") or {}
    t0 = (init.get("关键帧时间") or [None])[0]
    inside = runtime.get("窗口内_+0.04s") or {}
    outside = runtime.get("窗口外_+0.2s") or {}
    d_in = (inside.get("当前时间") - t0) if (t0 is not None
                                          and inside.get("当前时间") is not None) else None
    d_out = (outside.get("当前时间") - t0) if (t0 is not None
                                            and outside.get("当前时间") is not None) else None
    v.check("runtime:the-probe-placed-the-playhead-where-it-claims",
            d_in is not None and abs(d_in - 0.04) < 5e-3
            and d_out is not None and abs(d_out - 0.2) < 5e-3,
            detail={"关键帧时刻 t0": t0, "窗口内实际差": d_in,
                    "窗口外实际差": d_out})

    # ── S12 ★★ 读回的 aria 文案 == 源站 i18n 逐字 ─────────────────────
    v.check("runtime:the-probe-read-the-source-aria-copy",
            inside.get("中键aria") == aria_visible
            and outside.get("中键aria") == aria_hidden
            and inside.get("中键pressed") == "true"
            and outside.get("中键pressed") == "false",
            detail={"窗口内 aria": inside.get("中键aria"),
                    "源站逐字（可见）": aria_visible,
                    "窗口外 aria": outside.get("中键aria"),
                    "源站逐字（不可见）": aria_hidden,
                    "窗口内 pressed": inside.get("中键pressed"),
                    "窗口外 pressed": outside.get("中键pressed")})

    # ── S13 ★★ 负控证据在库（含运行时负控）──────────────────────────
    neg: dict[str, Any] = {}
    if NEGATIVE.exists():
        neg = json.loads(NEGATIVE.read_text(encoding="utf-8"))
    neg_rows = neg.get("负控") or []
    runtime_neg = [r for r in neg_rows if r.get("类别") == "运行时"]
    v.check("runtime:the-negative-control-is-in-the-repo",
            bool(neg_rows)
            and all(r.get("通过") for r in neg_rows)
            and bool(runtime_neg),
            detail={"负控条数": len(neg_rows),
                    "其中运行时负控": len(runtime_neg),
                    "全通过": all(r.get("通过") for r in neg_rows) if neg_rows else None,
                    "★ 说明": "★ 运行时负控＝把窗口改回 1e-3 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 探针必须报红"})

    # ── S14 ★★ 866 门禁动态解析在用清单 ──────────────────────────────
    g866 = GATE866.read_text(encoding="utf-8") if GATE866.exists() else ""
    g866_code = strip_comments(g866)
    has_resolver = "def resolve_live_regress" in g866_code
    hardcoded = re.search(r'^\s*REGRESS\s*=\s*OUT_DIR\s*/\s*"probes/regress\d+\.py"',
                          g866_code, re.M)
    v.check("source:the-regression-list-resolves-the-live-one-dynamically",
            has_resolver and not hardcoded,
            detail={"有 resolve_live_regress": has_resolver,
                    "仍写死 REGRESS 路径": bool(hardcoded),
                    "★ 说明": "★ 在用清单＝批次号最大的那份 ⟹ ⟹ 不用写死文件名"})

    # ── S15 ★★ 回归清单只增不减（★ 869 ＝ 868 ＋ 一条）────────────────
    g869 = parse_gates(REGRESS869.read_text(encoding="utf-8")) \
        if REGRESS869.exists() else []
    g868 = parse_gates(REGRESS868.read_text(encoding="utf-8")) \
        if REGRESS868.exists() else []
    dropped = sorted(set(g868) - set(g869))
    v.check("source:the-live-regression-list-never-shrinks",
            bool(g869) and not dropped
            and set(g868).issubset(set(g869)),
            detail={"869 条数": len(g869), "868 条数": len(g868),
                    "被删掉的条目": ["%s.%s" % g for g in dropped],
                    "869 新增": ["%s.%s" % g for g in sorted(set(g869) - set(g868))]})

    (RAW / "audit-869.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    return v.report()


if __name__ == "__main__":
    sys.exit(main())
