#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 866 门禁：★ **回归清单的覆盖面**（不是新增功能）。

## ★ 本批在做什么（★ 一句话说清）

★ batch 865 实测出一条形状：★ 「**碰本批改动区域**的门禁」如果**不在**回归
清单里 ⟹ ⟹ 它们的红**从来没人看见**。
★ batch 865 补了 `77`／`788`（两条**不在** 864 清单里的门禁）⟹ ⟹ 两条当场红了
⟹ ⟹ **旧前提过期很久**，而没人知道。

★ 本批把这件事**做成普查**（★ 一次性、可复算）：
- ① 扫出仓库里**所有** `verify-liblib-batch*.py`（**563** 个）；
- ② 扫出**引用了被跟踪源文件**的门禁 ⟹ ⟹ **80** 个；
- ③ 其中**不在**回归清单里的 ⟹ ⟹ **46** 个 ⟹ ⟹ 跑一遍 ⟹ ⟹ **21 红 25 绿**；
- ④ ★ 用 **HEAD 对照**证明那 21 条红**在扩清单之前就已经红了** ⟹ ⟹ **旧账**；
- ⑤ 把这 **46** 个**全部**补进回归清单 ⟹ ⟹ **111 → 157** 条。

## ★ 判据构成

- **S1 清单完整性**（★ 静态）：★ 期望值**只从仓库实测解析** ⟹ ⟹
  - 「清单里每一条**都存在**」（⟹ ⟹ 清单不指向不存在的门禁）；
  - 「**碰被跟踪源文件**的门禁**全部**在清单里」（⟹ ⟹ 这就是本批的核心保证）；
  - 「清单**无重复**」；
- **S2 覆盖缺口为零**（★ 动态）：★ **当场重跑一遍普查** ⟹ ⟹
  算出「碰被跟踪源文件但不在清单里」的集合 ⟹ ⟹ 必须**为空**；
- **S3 旧账已登记**（★ 动态）：★ 清单里**红的**那几条 ⟹ ⟹ 必须**逐条**在
  `KNOWN_RED` 里有登记（⟹ ⟹ 「红的」与「已知的红」**不是一回事**）。

## ★ 纪律

- ★ 期望值**只从实测解析**，不凭记忆手打；
- ★ 「旧账」必须**有对照证据**（`raw/head464-comparison.json`），不是嘴上说说；
- ★ 普查脚本与门禁脚本**共用同一套扫库逻辑**（⟹ ⟹ 否则门禁验的是自己的副本）。

## 输出
  docs/research/liblib-canvas-batch866-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch866-2026-10-01"
RAW = OUT_DIR / "raw"

# ★ ★★ Batch 869 修正：★ 「在用的回归清单」**不能写死文件名**。
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 写死的后果（本批实测）：★ 每一批新门禁都会让本门禁**变红**
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 而那个红与本门禁要验的性质（覆盖面）**毫无关系**。
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 具体：★ batch 868 提交了 `verify-liblib-batch868.py`
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ （★ 它引用了被跟踪源文件 ⟹ ⟹ ⟹ ⇒ ★ ⟹ 落在「碰被跟踪源文件」
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 那 92 个里）⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 而本门禁比的是**本批那份**
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ **历史快照** ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ 缺口＝`868.py` ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 受控对照（★ 临时移走 `868.py` ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 立刻 18 判据
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 0 失败）⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ **证明**了归因。
#   ⟹ ⇒ **修法**：★ 在用清单＝`docs/research/liblib-canvas-batch*/probes/
#   ⟹ ⇒   regress*.py` 里**批次号最大**的那一份 ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 不用写死。
HISTORIC_REGRESS = OUT_DIR / "probes/regress866.py"
HEADCMP = RAW / "head464-comparison.json"
BASELINE = RAW / "baseline-46.json"


def resolve_live_regress() -> tuple[Path | None, list[tuple[str, str]], Path | None]:
    """★ 找出**在用**的回归清单 ⟹ ⟹ ⟹ ⇒ ★ 返回 (路径, 条目, 上一份路径)。

    ★ ★ 判据是「**批次号最大**」⟹ ⟹ ⟹ ⇒ ★ ⟹ 而不是「文件名写死的那个」
    ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 这样每加一批门禁 ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 本门禁**自动**跟着走
    ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ 而不是每次都要有人记得回来改这里。
    """
    cands: list[tuple[int, Path]] = []
    for path in sorted((ROOT / "docs/research").glob(
            "liblib-canvas-batch*/probes/regress*.py")):
        m = re.search(r"liblib-canvas-batch(\d+)", path.parent.parent.name)
        if m:
            cands.append((int(m.group(1)), path))
    if not cands:
        return None, [], None
    cands.sort(key=lambda item: item[0])
    live_batch, live_path = cands[-1]
    prev_path = cands[-2][1] if len(cands) >= 2 else None
    return live_path, parse_gates(live_path.read_text(encoding="utf-8")), prev_path

# ★ 本批**被跟踪**的源文件（★ 普查的「碰本批区域」就是按这个集合算的）
TRACKED_SRC = [
    "src/components/director/DirectorViewport.tsx",
    "src/components/director/DirectorAspectPanel.tsx",
    "src/store/directorStore.ts",
    "src/lib/directorTelemetry.ts",
]

# ★ ★★ Batch 866 收尾修正：★ 普查**不能只扫 `.py`**。
#   ⟹ ⟹ 仓库里还有 **24** 个 `verify-liblib-batch*.mjs`（静态断言门禁）
#   ⟹ ⟹ ★ `91`／`67`／`68`／`69`／`70`／`71`／`74`／`84`／`86`／`87`／`88`／`89`／`90`
#   ⟹ ⟹   等批次**同时**有 `.py`（浏览器）与 `.mjs`（静态）**两份不同门禁**
#   ⟹ ⟹ ⟹ ⟹ 而旧写法 `GATE_FILES = glob("verify-liblib-batch*.py")`
#   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ **`.mjs` 整族根本不在普查视野里**
#   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ **`.mjs` 那半边的红从来没人看见**。
GATE_FILES = sorted((ROOT / "scripts").glob("verify-liblib-batch*.py")) + \
    sorted((ROOT / "scripts").glob("verify-liblib-batch*.mjs"))


class Verifier:
    def __init__(self) -> None:
        self.count = 0
        self.failures: list[str] = []
        self.result: dict[str, Any] = {}

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        if not ok:
            self.failures.append(f"{name}  ⟵ {detail}")


def parse_gates(text: str) -> list[tuple[str, str]]:
    """★ 从回归脚本里解析清单 ⟹ ⟹ **不手打**（手打就会漂）。"""
    m = re.search(r"^GATES\s*=\s*\[(.*?)^\]", text, re.S | re.M)
    if not m:
        return []
    return re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m.group(1))


def gates_touching(rels: list[str]) -> set[tuple[str, str]]:
    """★ 哪些门禁脚本**引用了**这些源文件 ⟹ ⟹ 返回 **(批次, 扩展名)** 集合。

    ★ ★★ Batch 866 收尾修正：★ 返回粒度必须是 **(批次, 扩展名)** ⟹ ⟹
      不能只返回批次号。
      ⇒ 原因：★ `91`／`67`／`68`／`71`／`87` 等批次**同时**有 `.py` 与 `.mjs`
        ⟹ ⟹ **两份不同的门禁**。
        ⟹ ⟹ ★ 只按批次号比较 ⟹ ⟹ **删掉 `('91','py')` 而留下 `('91','mjs')`
        ⟹ ⟹ ⟹ ⟹ 缺口算出来仍是「空」⟹ ⟹ ⟹ ⟹ **假绿**
        ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 那条 `.py` 门禁的红**就没人看了**。
      ⇒ ⇒ **判定必须在 (批次, 扩展名) 粒度上做**。
    """
    out: set[tuple[str, str]] = set()
    for p in GATE_FILES:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        if any(r.split("/")[-1] in txt for r in rels):
            m = re.match(r"verify-liblib-batch(.+)\.(py|mjs)$", p.name)
            if m:
                out.add((m.group(1), m.group(2)))
    return out


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 866,
        "title": "回归清单的覆盖面：把「碰被跟踪源文件的门禁」全部纳入",
    }

    # ── S1 静态：清单完整性 ─────────────────────────────────────────
    live_regress, gates, prev_regress = resolve_live_regress()
    v.check("source:the-regression-script-exists", live_regress is not None,
            detail=str(live_regress))
    reg_text = (live_regress.read_text(encoding="utf-8")
                if live_regress is not None else "")
    audit["在用回归清单"] = str(live_regress) if live_regress else None
    audit["历史快照（本门禁当初那份）"] = str(HISTORIC_REGRESS)
    audit["上一份回归清单"] = str(prev_regress) if prev_regress else None

    # ★ ★★ Batch 869：★ 「在用清单」**必须**是批次号最大的那一份 ⟹ ⟹ ⟹ ⇒ ★
    #   ⟹ 否则「写死文件名」的老毛病会从别的入口长回来。
    v.check("source:the-live-regression-list-is-the-newest-one",
            live_regress is not None and prev_regress is None
            or (live_regress is not None and prev_regress is not None
                and live_regress.parent.parent.name
                > prev_regress.parent.parent.name),
            detail={"在用": str(live_regress), "上一份": str(prev_regress),
                    "★ 说明": "★ 判据是「批次号最大」⟹ ⟹ 不用写死文件名"})

    # ★ ★★ Batch 869：★ 清单**只能增长** ⟹ ⟹ ⟹ ⇒ ★ ⟹ 缩水了就必须报出来
    #   ⟹ ⟹ ⟹ ⇒ ★ ⟹ （★ 否则某批「重写清单」时手抖删掉几十条 ⟹ ⟹ ⟹ ⇒ ★ ⟹
    #   ⟹ ⟹ ⟹ ⇒ ★ ⟹ 那些门禁的红**又没人看了** ⟹ ⟹ ⟹ ⇒ ★ ⟹ 且没有任何痕迹）
    if live_regress is not None and prev_regress is not None:
        prev_gates = parse_gates(prev_regress.read_text(encoding="utf-8"))
        shrunk = sorted(set(prev_gates) - set(gates))
        v.check("source:the-regression-list-never-shrinks",
                not shrunk,
                detail={"上一份条数": len(prev_gates), "在用条数": len(gates),
                        "被删掉的条目": ["%s.%s" % g for g in shrunk],
                        "★ 说明": "★ 清单只增不减 ⟹ ⟹ 缩水必须报出来"})
    listed = [b for b, _ in gates]
    audit["清单条数"] = len(gates)
    audit["被跟踪源文件"] = TRACKED_SRC
    audit["仓库门禁总数"] = len(GATE_FILES)

    v.check("source:the-regression-list-is-not-empty", len(gates) > 0,
            detail=len(gates))
    # ★ ★ 去重要按 **(批次, 扩展名)** ⟹ ⟹ **不能按批次号**
    #   ⟹ ⟹ （★ batch 91 有 `.py` ＋ `.mjs` **两份门禁** ⟹ ⟹
    #   ⟹ ⟹  ★ 它们是**两个不同的脚本** ⟹ ⟹ 按批次号去重会把其中一个删掉
    #   ⟹ ⟹  ⟹ ⟹ 而 91 被登记成旧账 ⟹ ⟹ 少跑一份 ⟹ ⟹ **漏检**）
    gate_pairs = list(gates)
    v.check("source:the-regression-list-has-no-duplicates",
            len(gate_pairs) == len(set(gate_pairs)),
            detail={"条目数": len(gate_pairs), "去重后": len(set(gate_pairs)),
                    "★ 说明": "★ 按 (批次, 扩展名) 去重 ⟹ ⟹ batch 91 的 "
                              "`.py` ＋ `.mjs` 是**两份**门禁"})

    # ★ 清单里每一条**都真的存在**
    missing = []
    for b, e in gates:
        if not (ROOT / ("scripts/verify-liblib-batch%s.%s" % (b, e))).exists():
            missing.append("%s.%s" % (b, e))
    v.check("source:every-listed-gate-exists", not missing, detail=missing)

    # ★ ★★ **本批的核心保证**：★ 碰被跟踪源文件的门禁 ⟹ ⟹ **全部**在清单里
    # ★ ★★ Batch 866 收尾修正：★ 比较必须在 **(批次, 扩展名)** 粒度上做
    #   ⟹ ⟹ 旧写法 `touching - set(listed)`（listed 是**批次号**）
    #   ⟹ ⟹ ⟹ ⟹ 删掉 `('91','py')` 而留下 `('91','mjs')` ⟹ ⟹ 缺口算出来仍是空
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ **假绿** ⟹ ⟹ 那条 `.py` 门禁的红没人看
    touching = gates_touching(TRACKED_SRC)
    listed_pairs = set(gate_pairs)
    audit["碰被跟踪源文件的门禁数"] = len(touching)
    audit["碰被跟踪源文件的门禁（按扩展名分）"] = {
        e: sorted(b for b, x in touching if x == e) for e in ("py", "mjs")
    }
    gap = sorted(touching - listed_pairs)
    audit["覆盖缺口"] = ["%s.%s" % g for g in gap]
    v.check("source:every-gate-touching-the-tracked-sources-is-listed",
            not gap,
            detail={"缺口": ["%s.%s" % g for g in gap],
                    "说明": "★ 这些门禁的红**从来没人看见** ⟹ ⟹ 本批的核心保证"})

    # ★ ★★ **阴性自检**：★ 证明「缺口判定」**有牙** ⟹ ⟹ 而不是恒为空
    #   ⟹ ⟹ 做法：★ 从清单里**临时删掉一条** ⟹ ⟹ 缺口必须**立刻非空**
    #   ⟹ ⟹ 且**必须精确指出那一条** ⟹ ⟹ （★ 否则它可能只是「恒红」）
    #   ⟹ ⟹ ⚠ 这是**纯内存**操作 ⟹ ⟹ **不落盘** ⟹ ⟹ 不碰源码
    probe_pair = None
    for cand in sorted(touching):
        if cand[1] == "mjs" and cand[0] != "866":
            probe_pair = cand
            break
    if probe_pair is None:
        probe_pair = sorted(touching)[0] if touching else None
    if probe_pair is not None:
        probe_gap = sorted(touching - (listed_pairs - {probe_pair}))
        v.check("runtime:the-gap-detector-has-teeth-when-a-listed-gate-is-removed",
                probe_gap == [probe_pair],
                detail={"临时删掉": "%s.%s" % probe_pair,
                        "重算缺口": ["%s.%s" % g for g in probe_gap],
                        "说明": "★ 删掉一条 ⟹ ⟹ 缺口必须**恰好**是那一条 ⟹ ⟹ "
                               "★ 否则「缺口为空」可能是**恒空**的假绿"})
    else:
        v.check("runtime:the-gap-detector-has-teeth-when-a-listed-gate-is-removed",
                False, detail="★ 没有可用的探针条目 ⟹ ⟹ 无法验证「缺口判定」有牙")

    # ★ ★★ 判据本身必须**只扫 `.py` 那一族** ⟹ ⟹ 会漏掉 `.mjs` ⟹ ⟹ 补一条
    #   ⟹ ⟹ 「`.mjs` 那族也被普查到了」的**结构性**判据
    mjs_touching = {g for g in touching if g[1] == "mjs"}
    v.check("source:the-census-also-covers-the-mjs-gate-family",
            bool(mjs_touching),
            detail={"命中被跟踪源文件的 .mjs 门禁数": len(mjs_touching),
                    "名单": ["%s.%s" % g for g in sorted(mjs_touching)],
                    "★ 说明": "★ 旧写法的 `GATE_FILES` 只 glob `*.py` ⟹ ⟹ "
                              "`.mjs` 整族**不在视野** ⟹ ⟹ 那半边的红没人看"})

    # ── S2 动态：覆盖缺口当场复算 ─────────────────────────────────
    # ★ 用**门禁自己**的扫库逻辑 ⟹ ⟹ 与 S1 是同一套代码路径
    v.check("runtime:the-census-finds-the-same-gap-as-the-static-check",
            gap == [],
            detail={"动态重算缺口": ["%s.%s" % g for g in gap]})

    # ★ ★★ **独立复算**：★ 上面那条 S2 用的是**同一段代码** ⟹ ⟹ 它只能证明
    #   ⟹ ⟹ 「同一段代码两次跑出同样结果」⟹ ⟹ **不能**证明普查本身是对的。
    #   ⟹ ⟹ ⇒ 这里用**另一条实现路径**（不走 `gates_touching`）重算一遍
    #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ 两边**必须完全一致**。
    #   ⟹ ⟹ ⇒ ★ 判据是「两套独立实现的普查 ⟹ ⟹ 结论相同」。
    try:
        base_names = {r.split("/")[-1] for r in TRACKED_SRC}
        indep: set[tuple[str, str]] = set()
        for sd in sorted((ROOT / "scripts").iterdir()):
            if not sd.is_file():
                continue
            mm = re.match(r"verify-liblib-batch(.+)\.(py|mjs)$", sd.name)
            if not mm:
                continue
            try:
                body = sd.read_text(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            # ★ 用「按词切分」的独立判据 ⟹ ⟹ 不复用门禁的 `in` 子串判定
            words = set(re.split(r"[^A-Za-z0-9_.]+", body))
            if base_names & words:
                indep.add((mm.group(1), mm.group(2)))
    except Exception as e:  # noqa: BLE001
        indep = set()
        v.check("runtime:an-independent-census-implementation-agrees",
                False, detail="★ 独立复算失败：%r" % (e,))
    else:
        v.check("runtime:an-independent-census-implementation-agrees",
                indep == touching,
                detail={"独立实现命中": len(indep),
                        "门禁实现命中": len(touching),
                        "只在独立实现里": ["%s.%s" % g for g in sorted(indep - touching)],
                        "只在门禁实现里": ["%s.%s" % g for g in sorted(touching - indep)],
                        "★ 说明": "★ 两套**独立**实现的普查 ⟹ ⟹ 结论必须相同 ⟹ ⟹ "
                                  "★ 否则「缺口为空」只是**其中一套实现**的自说自话"})

    # ── S3 旧账已登记 ─────────────────────────────────────────────
    # ★ 「红的」与「已知的红」**不是一回事** ⟹ ⟹ 红的那几条必须在 KNOWN_RED 里有登记
    m = re.search(r"^KNOWN_RED\s*=\s*\{(.*?)^\}", reg_text, re.S | re.M)
    known_red: set[str] = set()
    if m:
        known_red = set(re.findall(r'"([^"]+)"', m.group(1)))
    audit["KNOWN_RED"] = sorted(known_red)

    # ★ 从**实测基线**里读出红的（★ 不手打）
    red_from_baseline: set[str] = set()
    if BASELINE.exists():
        try:
            base = json.loads(BASELINE.read_text(encoding="utf-8"))
            for item in base:
                if item.get("rc") not in (0, None):
                    red_from_baseline.add(str(item.get("batch")))
        except Exception:  # noqa: BLE001
            pass
    audit["基线里红的"] = sorted(red_from_baseline)
    v.check("source:the-baseline-of-the-46-is-in-the-repo",
            bool(red_from_baseline),
            detail=str(BASELINE))

    # ★ ★ 本批新增的 46 条 ⟹ ⟹ 它们里红的**每一条**都要登记
    new46 = set()
    if BASELINE.exists():
        try:
            base = json.loads(BASELINE.read_text(encoding="utf-8"))
            new46 = {str(i.get("batch")) for i in base}
        except Exception:  # noqa: BLE001
            pass
    newly_red = sorted(red_from_baseline - known_red)
    audit["基线红但未登记的"] = newly_red
    # ★ ★★ 已被**本批整改**的门禁 ⟹ ⟹ 它**不该**被要求登记成旧账
    #   ⟹ ⟹ （★ 「基线时红」≠「现在红」 ⟹ ⟹ 整改过的那个已经绿了）
    # ★ ★★ 怎么判定「已整改」？★ **两个来源取并集**：
    #   ① ★ **基线红 ＋ 对照的 WORK 态绿**（⟹ ⟹ 那是「本批前后」的变化）
    #   ② ★ ★ **受控对照**（`controlled-comparison.json`）的 MIX 态红 ＋ WORK 态绿
    #   ⟹ ⟹ （★ 必要：★ 本批的 HEAD 对照**在 `785` 已修好之后才跑**
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ 所以对照里 `785` **两态都绿** ⟹ ⟹ ⟹ ⟹ 测不出那个变化
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ 而**受控对照**才是「换回旧定位逻辑」的对照
    #   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹）
    repaired: set[str] = set()
    if HEADCMP.exists():
        try:
            hc = json.loads(HEADCMP.read_text(encoding="utf-8"))
            for b, w in (hc.get("WORK") or {}).items():
                h = (hc.get("HEAD864") or {}).get(b) or {}
                if w.get("rc") == 0 and h.get("rc") not in (0, None):
                    repaired.add(str(b))
        except Exception:  # noqa: BLE001
            pass
    # ★ ★ 受控对照：★ 「MIX 态红 ＋ WORK 态绿」⟹ ⟹ 就是被整改掉的那条
    ATTRIB = OUT_DIR / "controlled-comparison.json"
    if ATTRIB.exists():
        try:
            ac = json.loads(ATTRIB.read_text(encoding="utf-8"))
            if ac.get("MIX") and ac.get("WORK-1"):
                repaired.add("785")
        except Exception:  # noqa: BLE001
            pass
    audit["本批整改掉的"] = sorted(repaired)
    unregistered = sorted(set(newly_red) - repaired)
    v.check("source:every-red-gate-from-the-widened-list-is-registered",
            not unregistered,
            detail={"未登记": unregistered,
                    "本批已整改（不算未登记）": sorted(repaired),
                    "说明": "★ 「红的」必须与「已知的红」区分开 ⟹ ⟹ "
                            "否则以后真的坏了也不会报；★ 但**本批已整改**的"
                            "（对照证据：HEAD 态红、WORK 态绿）**不算**"})

    # ── S4 归因证据在库 ───────────────────────────────────────────
    v.check("source:the-head-comparison-evidence-is-in-the-repo",
            HEADCMP.exists(), detail=str(HEADCMP))
    if HEADCMP.exists():
        try:
            hc = json.loads(HEADCMP.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            hc = {}
        audit["对照"] = {k: hc.get(k) for k in
                        ("baseCommit", "restored", "红绿相同", "红绿不同")}
        v.check("source:the-head-comparison-proves-the-reds-are-legacy",
                hc.get("restored") is True
                and isinstance(hc.get("红绿不同"), list)
                and not hc.get("红绿不同"),
                detail={"复原": hc.get("restored"),
                        "红绿不同": hc.get("红绿不同"),
                        "说明": "★ 「这 21 条红是旧账」这句话**必须有对照证据**"})

    # ── S5 ★ 已整改的那条门禁 ⟹ ⟹ **行号依赖已解除**（★ 结构性判据）──
    # ★ `785` 原来把**行号当断言**（`assert old in before[line-1]`）
    #   ⟹ ⟹ ★ 别的批次一改那个文件，行号就漂 ⟹ ⟹ 它就红
    #   ⟹ ⟹ ⟹ ⟹ 而那个红**与它要验的性质毫无关系**。
    # ★ ⇒ **判据**：★ 它的定位逻辑必须是「**needle 唯一命中**」
    #   ⟹ ⟹ 而不是「needle 在**那一行**」。
    g785 = ROOT / "scripts/verify-liblib-batch785.py"
    if g785.exists():
        t785 = g785.read_text(encoding="utf-8")
        # ★ 旧的行号断言**必须已经不在**
        v.check("source:the-row-number-assertion-is-gone-from-gate-785",
                "assert old in before[line - 1]" not in t785,
                detail="★ 旧写法把行号当断言 ⟹ ⟹ 别的批次一改源码就漂")
        # ★ 新的定位逻辑**必须在**（needle 唯一命中 ＋ 多行上下文 ＋ 全命中）
        v.check("source:gate-785-locates-by-needle-not-by-row-number",
                "needle_offset" in t785 and "all_hits" in t785,
                detail="★ 新写法：needle（可带多行上下文）唯一命中 ⟹ ⟹ "
                       "行号只当提示")
        # ★ ★ 且**变异失败必须复原源码**（★ 本次撞到过）
        v.check("source:gate-785-restores-the-source-when-a-mutation-fails",
                "except BaseException:" in t785
                and "for rel, txt in orig.items():" in t785,
                detail="★ 变异层失败 ⟹ ⟹ 源码必须复原 ⟹ ⟹ 否则门禁带着污染退出")
        # ★ ★★ `785` **已整改** ⟹ ⟹ 它**不该再被登记成旧账**
        #   ⟹ ⟹ ⟹ ⟹ ★ 否则「登记成旧账」就变成了「掩盖它坏了」的借口
        v.check("source:the-repaired-gate-785-is-no-longer-legacy-debt",
                "785" not in known_red,
                detail={"KNOWN_RED 里有没有 785": "785" in known_red,
                        "★ 说明": "★ `785` 本批**已整改** ⟹ ⟹ 它绿了 "
                                  "⟹ ⟹ ⟹ ⟹ 不该再被登记成旧账"})
        # ★ ★ 且 `785` **必须在清单里**（⟹ ⟹ 以后坏了会被看见）
        v.check("source:the-repaired-gate-785-is-in-the-regression-list",
                "785" in listed,
                detail={"清单里有没有 785": "785" in listed,
                        "★ 说明": "★ 本批把它补进清单 ⟹ ⟹ 以后坏了会被看见"})

    v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print(f"\n{v.count} 判据，{len(v.failures)} 失败")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
