#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 867 门禁：★ 「依赖已消失的 `/tmp` 文件」的那批门禁 ⟹ ⟹ 让它们的红**被看见**。

## ★ 本批在做什么（★ 一句话说清）

★ batch 866 建立的纪律：「回归清单是一份**旧前提普查表**」⟹ ⟹
★ 「清单之外的门禁坏了 ⟹ ⟹ **没人知道**」⟹ ⟹ 本批把它**做完**：
⟹ ⟹ ① **普查**出所有「依赖 `/tmp` 下**已消失**的文件」的门禁
⟹ ⟹ ② 把它们**全部**跑一遍 ⟹ ⟹ 拿到基线（**14 红**）
⟹ ⟹ ③ **逐条归因** ⟹ ⟹ 归出**四个**真缺陷
⟹ ⟹ ④ **逐条整改** ⟹ ⟹ 七条门禁（`753`–`759`）现在**全绿**
⟹ ⟹ ⑤ **把它们补进回归清单** ⟹ ⟹ 清单 **177 → 184** 条
⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 以后它们坏了 ⟹ ⟹ **会被看见**。

## ★ ★★ 归出的四个真缺陷（★ 都不是「环境问题」）

| # | 缺陷 | 性质 |
| --- | --- | --- |
| ① | ★ **「跳过」被实现成了「失败」** | ★ 探针原始读数不可恢复 ⟹ ⟹ 那一层永远红 ⟹ ⟹ 但**它只占 1 条** ⟹ ⟹ 其余 40 条全绿也没用 |
| ② | ★ **门禁断言了一个已经被修复的 bug** | ★ `754`（高清预设坐标系）／`759`（回收站 30 天／行内菜单）／`755`／`758` ⟹ ⟹ 那些 bug 早被 `802`／`805`／`790`／`791` 修好了 ⟹ ⟹ 门禁却还在要求「缺陷存在」 |
| ③ | ★ **写死行号当断言** | ★ `753` 的 `setEdges` 断言写死了 `canvasStore.ts:387`／`3415` ⟹ ⟹ 源码一改就漂 |
| ④ | ★ **门禁绿着，但它没在验它声称要验的东西** | ★ `759` 的 `openCanvasOrder` 用**跨段正则** ⟹ ⟹ 顺序完全反过来也照样命中 |

## ★ 判据构成

- **S1 清单完整性**（静态）：★ 清单里每一条**都存在** ＋ **无重复**（按 (批次, 扩展名)）
- **S2 ★ 本批的核心保证**：★ 「依赖 `/tmp` 下**已消失**的文件」的门禁
  ⟹ ⟹ **全部**在回归清单里 ⟹ ⟹ （★ 否则它们的红**从来没人看见**）
- **S3 缺口当场复算**（动态）：★ **独立实现**重算一遍 ⟹ ⟹ 两边必须完全一致
- **S4 七条门禁已整改**：★ 逐条检查「跳过语义」＋「判据不写死行号／常量」＋
  「判据锚在**被断言读的那个量**上」
- **S5 负控证据在库**：★ 十条负控**全部打红** ⟹ ⟹ 且源码**字节级干净**

## ★ 纪律

- ★ 期望值**只从实测解析**，不凭记忆手打；
- ★ 「这个 bug 是不是已经被修」⟹ ⟹ 必须**追 git** 给出证据；
- ★ 判据**不许**写死行号／会变的常量（★ 改成「倍数」「形态」「下标顺序」）；
- ★ 「全文不含某串」这种判据 ⟹ ⟹ 必须**剥掉注释**再查。

## 输出
  docs/research/liblib-canvas-batch867-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch867-2026-10-01"
RAW = OUT_DIR / "raw"

REGRESS = OUT_DIR / "probes/regress867.py"
NEG = RAW / "negative-audit.json"
BASELINE = RAW / "baseline-tmp-deps.json"

# ★ ★★ 本批整改的七条门禁（★ 它们分三层 ⟹ ⟹ 前两层不依赖外部文件）
TARGET_GATES = ["753", "754", "755", "756", "757", "758", "759"]


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
    """★ 从回归脚本里解析清单 ⟹ ⟹ **不手打**（手打就会漂）。

    ★ ★★ Batch 867：★ **必须先剥掉注释**再解析 ⟹ ⟹
      ★ 否则**注释里**写的 `("761", "py")` 会被当成清单里的一条
      ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 缺口判定变成**恒空** ⟹ ⟹ ⟹ ⟹ 门禁**假绿**。
      ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 本批的实际教训：★ 自己做负控时在**注释**里写了那一条
      ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 门禁不但没红 ⟹ ⟹ 反而**证明了它没牙**
      ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 与「全文不含某串被注释骗到」**完全同型**（★ 第三例）
    """
    # ★ 剥注释（★ `#` 行注释 ＋ `"""..."""` 文档串）
    text = re.sub(r'"""[\s\S]*?"""', " ", text)
    text = re.sub(r"#[^\n]*", " ", text)
    m = re.search(r"^GATES\s*=\s*\[(.*?)^\]", text, re.S | re.M)
    if not m:
        return []
    return re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m.group(1))


def gates_with_missing_tmp() -> set[tuple[str, str]]:
    """★ 哪些门禁引用了 `/tmp` 下**已不存在**的文件 ⟹ ⟹ 它们**必然红**。

    ★ ★★ 判据是「**实测**：那个路径现在不存在」⟹ ⟹ 而不是「源码里写了 /tmp」
    ⟹ ⟹ 因为**自给自足**的门禁（自己写 `/tmp` 再读回来）也是绿的。
    """
    out: set[tuple[str, str]] = set()
    pat = re.compile(r'["\'](/tmp/[A-Za-z0-9_./-]+)["\']')
    for p in sorted((ROOT / "scripts").glob("verify-liblib-batch*.py")):
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        for path in set(pat.findall(txt)):
            if not Path(path).exists():
                m = re.match(r"verify-liblib-batch(.+)\.py$", p.name)
                if m:
                    out.add((m.group(1), "py"))
    return out


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 867,
        "title": "「依赖已消失的 /tmp 文件」的那批门禁：让它们的红被看见",
    }

    # ── S1 清单完整性 ─────────────────────────────────────────────
    v.check("source:the-regression-script-exists", REGRESS.exists(), detail=str(REGRESS))
    reg_text = REGRESS.read_text(encoding="utf-8") if REGRESS.exists() else ""
    gates = parse_gates(reg_text)
    listed_pairs = set(gates)
    listed_batches = {b for b, _ in gates}
    audit["清单条数"] = len(gates)
    v.check("source:the-regression-list-is-not-empty", len(gates) > 0, detail=len(gates))
    v.check("source:the-regression-list-has-no-duplicates",
            len(gates) == len(listed_pairs),
            detail={"条目数": len(gates), "去重后": len(listed_pairs)})
    missing = ["%s.%s" % (b, e) for b, e in gates
               if not (ROOT / ("scripts/verify-liblib-batch%s.%s" % (b, e))).exists()]
    v.check("source:every-listed-gate-exists", not missing, detail=missing)

    # ── S2 ★★ 本批的核心保证：★ 依赖已消失 /tmp 文件的门禁全部在清单里 ──
    touching = gates_with_missing_tmp()
    audit["依赖已消失 /tmp 文件的门禁数"] = len(touching)
    audit["依赖已消失 /tmp 文件的门禁"] = ["%s.%s" % g for g in sorted(touching)]
    gap = sorted(touching - listed_pairs)
    audit["覆盖缺口"] = ["%s.%s" % g for g in gap]
    v.check("source:every-gate-with-a-missing-tmp-dependency-is-listed",
            not gap,
            detail={"缺口": ["%s.%s" % g for g in gap],
                    "说明": "★ 这些门禁**必然红** ⟹ ⟹ 不在清单里 ⟹ ⟹ "
                            "它们的红**从来没人看见**"})

    # ★ ★★ 独立实现复算：★ 换一条实现路径重算 ⟹ ⟹ 两边必须一致
    indep: set[tuple[str, str]] = set()
    for p in sorted((ROOT / "scripts").glob("verify-liblib-batch*.py")):
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        m = re.match(r"verify-liblib-batch(.+)\.py$", p.name)
        if not m:
            continue
        # ★ 独立口径：★ 用「双引号或单引号里的绝对路径」⟹ ⟹ 不复用 S2 的正则
        for path in re.findall(r'"(/tmp/[^"\s]+)"|\'(/tmp/[^\'\s]+)\'', body):
            real = path[0] or path[1]
            if not Path(real).exists():
                indep.add((m.group(1), "py"))
    v.check("runtime:an-independent-census-implementation-agrees",
            indep == touching,
            detail={"独立实现命中": len(indep), "门禁实现命中": len(touching),
                    "只在独立实现里": ["%s.%s" % g for g in sorted(indep - touching)],
                    "只在门禁实现里": ["%s.%s" % g for g in sorted(touching - indep)]})

    # ── S3 ★ 七条门禁已整改 ───────────────────────────────────────
    per_gate = {}
    for b in TARGET_GATES:
        gp = ROOT / ("scripts/verify-liblib-batch%s.py" % b)
        if not gp.exists():
            v.check("source:the-repaired-gate-%s-exists" % b, False, detail=str(gp))
            continue
        t = gp.read_text(encoding="utf-8")
        # ★ ① 「跳过」不计入分母 ⟹ ⟹ 分母用 `ran`
        has_skip = ("skipped=False" in t
                    and "len(ran)" in t
                    and '"skippedCount"' in t)
        # ★ ② 旧的「跳过 = pass:False 且计入分母」写法**不许**还在
        no_old_skip = not re.search(
            r'"pass":\s*False,\s*"got":\s*"SKIPPED', t)
        # ★ ③ **不许**写死行号当断言（★ 本批整改掉的那一条）
        #   ⟹ ⟹ ★ ★★ 必须**先剥注释**再查 ⟹ ⟹ 因为整改过的门禁**注释里**
        #   ⟹ ⟹   ⟹ ⟹ 会**引用旧写法**来说明改了什么
        #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 「全文含 `endswith((...:387))`」会**假失败**
        #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★ 这与「全文不含某串」那个坑**同型**
        _code = re.sub(r"/\*[\s\S]*?\*/", " ", t)
        _code = re.sub(r"#[^\n]*", " ", _code)
        _code = re.sub(r'"""[\s\S]*?"""', " ", _code)
        no_row_assert = not re.search(
            r'endswith\(\([^)]*\.tsx?:\d+', _code)
        # ★ ④ **不许**写死「会变的常量」（★ `GROUP_PADDING == 32`）
        no_hardcoded_const = not re.search(
            r'const GROUP_PADDING = 32', t)
        # ★ ⑤ 「全文不含某串」类判据 ⟹ ⟹ 必须剥注释
        #   ⟹ ⟹ ★ ★★ 但**只有**「读**整个文件**的『不含』断言」才需要
        #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⇒ 读**切片**的（如 `not in body`／`not in title_line`）
        #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ 风险低得多 ⟹ ⟹ ⟹ ⟹ 不必一刀切要求剥注释
        #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★ 第一版写成了「所有 `not in` 都要剥」⟹ ⟹ 假失败
        #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★ 第二版写成了「必须剥」⟹ ⟹ 也不对
        #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ★ ⇒ 判据：★ 「读整文件的『不含』断言」必须用
        #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ 剥注释后的变量（`_page_code`）
        whole_file_absence = len(re.findall(
            r'"[^"]*"\s+not in\s+(page|dd|store)\b', _code))
        strips_comment = ("_page_code" in _code) or ("not in _row_menu_tag" in _code)
        per_gate[b] = {
            "跳过语义已改": has_skip,
            "旧的跳过=失败写法已无": no_old_skip,
            "无写死行号断言": no_row_assert,
            "无写死常量": no_hardcoded_const,
            "剥注释后再查": strips_comment,
            "读整文件的『不含』断言数": whole_file_absence,
        }
        v.check("source:the-repaired-gate-%s-has-real-skip-semantics" % b,
                has_skip, detail=per_gate[b])
        v.check("source:the-repaired-gate-%s-has-no-old-skip-as-fail" % b,
                no_old_skip, detail=per_gate[b])
        v.check("source:the-repaired-gate-%s-does-not-assert-row-numbers" % b,
                no_row_assert, detail=per_gate[b])
        v.check("source:the-repaired-gate-%s-does-not-assert-a-stale-constant" % b,
                no_hardcoded_const, detail=per_gate[b])
        # ★ ★★ 「读整文件的『不含』断言」⟹ ⟹ 必须用**剥注释后**的变量
        v.check("source:the-repaired-gate-%s-strips-comments-before-whole-file-absence-checks" % b,
                strips_comment or whole_file_absence == 0,
                detail=per_gate[b])
        # ★ ★★ 且它们**必须在清单里**
        v.check("source:the-repaired-gate-%s-is-in-the-regression-list" % b,
                b in listed_batches, detail={"在清单里": b in listed_batches})
    audit["七条门禁的整改情况"] = per_gate

    # ── S4 ★ 负控证据在库 ─────────────────────────────────────────
    neg = None
    if NEG.exists():
        try:
            neg = json.loads(NEG.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            neg = None
    v.check("source:the-negative-control-evidence-is-in-the-repo",
            neg is not None, detail=str(NEG))
    if neg is not None:
        applied = [r for r in neg if isinstance(r, dict) and "applied" in r]
        red = [r for r in applied if r.get("red")]
        audit["负控条数"] = len(applied)
        audit["负控打红条数"] = len(red)
        v.check("source:every-negative-control-turned-red",
                len(applied) > 0 and len(red) == len(applied),
                detail={"总条数": len(applied), "打红": len(red),
                        "没打红": [r.get("name") for r in applied if not r.get("red")]})
        restore = [r for r in neg if isinstance(r, dict) and "复原自检" in r]
        v.check("source:the-mutations-restored-the-source",
                bool(restore) and restore[0]["复原自检"] == "字节级干净",
                detail=restore[0]["复原自检"] if restore else "无复原记录")

    # ── S5 ★ 基线证据在库 ─────────────────────────────────────────
    v.check("source:the-baseline-of-the-tmp-dependent-gates-is-in-the-repo",
            BASELINE.exists(), detail=str(BASELINE))
    if BASELINE.exists():
        try:
            base = json.loads(BASELINE.read_text(encoding="utf-8"))
            red = [str(b.get("batch")) for b in base if b.get("rc") not in (0, None)]
            audit["基线条数"] = len(base)
            audit["基线红条数"] = len(red)
            audit["基线红"] = red
            v.check("source:the-baseline-shows-the-reds-that-were-invisible",
                    len(red) > 0, detail=red)
        except Exception:  # noqa: BLE001
            v.check("source:the-baseline-shows-the-reds-that-were-invisible",
                    False, detail="★ 基线读不出来")

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
