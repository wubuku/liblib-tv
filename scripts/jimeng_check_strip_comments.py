#!/usr/bin/env python3
r"""batch 942 的自查工具：`strip_comments()` 到底在**哪类输入**上干活？

## 为什么要单独一个文件

942 修 `strip_comments()` 里一个**真 bug**（`c == nxt2` 漏了第 2 个 ⇒
`with open(OUT, "w")` 里的双引号被当成三引号开头）。修的过程中撞出：

⚠️⚠️ **我一直在拿 `.py` 当它的输入测** ⇒ 修完看到「剥掉 0 字符」，
一度以为**修坏了**。真相是：**`.py` 里那些 `//` 不是注释位置**
（审计脚本把内联 JS 装在 Python 三引号字符串里，`//` 在字符串里只是普通字符）
⇒ **剥掉 0 字符才是正确结果**。

⇒ ⭐ 这就是「**『我没检测到』必须先确认『我够得着』**」的又一次应验：
我量了「剥除量」，却没确认**输入是不是它该处理的那一类**。

⚠️ 而且「剥除量」这个指标本身**是空的**：对 `.py` 它恒为 0、对 `.tsx` 它成千上万
⇒ ⇒ **一个指标在两类输入上差 4 个数量级，就不能单独用它判对错**。

## 这个脚本量三件事

| # | 量什么 | 为什么 |
| --- | --- | --- |
| ① | 对 `.py`（审计脚本）剥掉多少 | **应当接近 0** —— `.py` 里的 `//` 在字符串里，剥了反而破坏代码 |
| ② | 对 `.tsx`（复刻组件）剥掉多少、**残留多少行 `//`** | 这才是它的**设计目标**；**残留必须为 0**，否则就是漏剥 |
| ③ | 取若干**探针句**，看**原本存在的**那些**剥完后还在不在** | ⭐ 防「剥过头」：剥注释不能把代码也剥了 |

⚠️ ③ 是**反向**检查：940 那个错误条件的危险在于**过度剥离**
（把 `if (inside) return {` 这种代码都清掉）⇒ 必须有「该留的还在」这一列。

## 门禁

- `tsx_residual_zero`：**所有** `.tsx` 剥完后残留 `//` 行注释**必须为 0**
  （非 0 ⇒ 有漏剥 ⇒ 门红）
- `py_preserved`：`.py` 输入下**必须保留**所有探针句
  （被剥掉 ⇒ 剥过头 ⇒ 门红）
- `tsx_preserved`：`.tsx` 输入下**同样**必须保留探针句
- `stripped_nonzero_on_tsx`：`.tsx` 上剥除量**必须 > 0**
  （⚠️ 这条防的正是 942 之前那个状态：**它什么都不剥**）
- `two_input_classes_differ`：`.py` 与 `.tsx` 的剥除量**必须差一个数量级以上**
  ⇒ 把「剥除量不是一个能单独判对错的指标」这条**钉成门**

跑法：
  /opt/miniconda3/bin/python3 scripts/jimeng_check_strip_comments.py
退出码 0 = 全通。
"""

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERIFIER = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
AUDIT = ROOT / "scripts/jimeng_unclickable_audit.py"
TSX_DIR = ROOT / "src/components/jimeng"

# `//` 行注释的正则：`(?<![:/*])` 排除 `://`（URL）与 `/*`（块注释起点）
LINE_COMMENT = re.compile(r"(?<![:*/])\s//\s")


def load_strip_comments():
    """把 verifier 里的 `strip_comments` **原样**取出来执行
    ⚠️ 不复制实现 —— 复制一份就会出现「两份漂移」（936 栽过）。"""
    src = VERIFIER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "strip_comments")
    ns: dict = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                 "<strip_comments>", "exec"), ns)
    return ns["strip_comments"]


# ⭐ 探针句：**代码里**的真实片段。剥注释**绝不能**把它们清掉
#    （剥过头的典型症状就是这些消失）。
#
# ⚠️⚠️⚠️ 【选探针的纪律 —— 第二版才选对】
# 第一版我用了 `onClick` / `className` / `useJimengStore` ⇒ 门红了。
# 查下来**不是剥过头** —— 那两个 `onClick` **本来就在注释里**
# （一处 JSX 块注释 `{/* … onClick 是 toggle … */}`、一处行注释）
# ⇒ 被剥掉是**正确行为**，是**探针选错了**。
#
# ⇒ ⭐ **探针必须是「不可能只出现在注释里」的结构性片段**
#（关键字、声明形式），而不是**业务标识符**
# —— 业务标识符完全可能只在一句解释性注释里被提到。
PROBES_PY = ["SOURCE_BASELINE = {", "def _bucket(", "coveredByLayer",
             "LAYER_SEL = (", "FORBIDDEN_TIDS"]
PROBES_TSX = ["export ", "const ", "return ", "function ", "import "]
# ⚠️ 门必须**自己知道探针有效**：若某文件里命中的探针太少，那道「不许丢」
#    门在它身上**没有判别力** ⇒ 记下来（而不是默默当作通过）。
MIN_PROBES_HIT = 3


def n_line_comments(text: str) -> int:
    return sum(1 for l in text.split("\n") if LINE_COMMENT.search(l))


def measure(strip, text: str, probes):
    out = strip(text)
    # ⚠️⚠️ 第一版这里写的是 `all(p in out for p in probes)` ⇒ **门红了**。
    #    真因不是剥过头，而是**我的门要求「每个文件都含全部探针句」**
    #    —— 而 `useJimengStore` 本来就不在每个 .tsx 里。
    # ⇒ ⭐ 正确判据（也是「剥过头」该问的那一件）：
    #    **原本存在的**探针句，剥完后**不许丢**。
    #    ⚠️ **不许**反过来要求「原本不存在的探针句要出现」——
    #    那是把「门该问的」换成了「门好写的」。
    present = [p for p in probes if p in text]
    lost = [p for p in present if p not in out]
    return {
        "chars_in": len(text),
        "chars_out": len(out),
        "stripped": len(text) - len(out),
        "line_comments_in": n_line_comments(text),
        "line_comments_out": n_line_comments(out),
        "probes_present": present,
        "probes_lost": lost,
        "probes_all_kept": not lost,
        # ⚠️ 探针命中太少 ⇒ 这道「不许丢」门在它身上**没有判别力**
        "probes_enough": len(present) >= MIN_PROBES_HIT,
    }


def main() -> int:
    if not VERIFIER.exists() or not AUDIT.exists():
        print("✗ 找不到 verifier / 审计脚本")
        return 2
    strip = load_strip_comments()

    # ① `.py`（审计脚本）—— **应当接近 0 剥除**
    py_text = AUDIT.read_text(encoding="utf-8")
    py = measure(strip, py_text, PROBES_PY)

    # ② `.tsx`（复刻组件）—— 这才是它的设计目标
    tsx_files = sorted(TSX_DIR.glob("*.tsx"))
    if not tsx_files:
        print(f"✗ {TSX_DIR} 下没有 .tsx")
        return 2
    per_file = []
    for f in tsx_files:
        m = measure(strip, f.read_text(encoding="utf-8"), PROBES_TSX)
        m["name"] = f.name
        per_file.append(m)

    tsx_stripped = sum(m["stripped"] for m in per_file)
    tsx_residual = sum(m["line_comments_out"] for m in per_file)
    tsx_all_kept = all(m["probes_all_kept"] for m in per_file)
    py_all_kept = py["probes_all_kept"]
    tsx_enough = all(m["probes_enough"] for m in per_file)
    n_thin = [m["name"] for m in per_file if not m["probes_enough"]]

    # ③ 两类输入的剥除量必须**差一个数量级以上**
    #    ⇒ 把「剥除量不是能单独判对错的指标」这条钉成门
    ratio = (tsx_stripped / max(py["stripped"], 1))

    res = {
        "py": py,
        "tsx": {"n_files": len(per_file), "stripped_total": tsx_stripped,
                "residual_line_comments": tsx_residual,
                "all_probes_kept": tsx_all_kept,
                "n_files_probes_too_thin": len(n_thin),
                "files_probes_too_thin": n_thin[:5],
                "per_file_top": sorted(per_file, key=lambda m: -m["stripped"])[:5]},
        "ratio_tsx_over_py": round(ratio, 1),
    }

    checks = {
        # ⭐ 剥干净：所有 .tsx 剥完后不得残留任何 `//` 行注释
        "tsx_residual_zero": tsx_residual == 0,
        # ⭐ 别剥过头：探针句（真代码）必须全部保留，两类输入都要
        "py_preserved": py_all_kept,
        "tsx_preserved": tsx_all_kept,
        # ⭐ 它必须**真的在干活**（防 942 之前那个「什么都不剥」的状态）
        "stripped_nonzero_on_tsx": tsx_stripped > 0,
        # ⭐ 两类输入差一个数量级以上 ⇒ 剥除量不能单独用来判对错
        "two_input_classes_differ": ratio >= 10.0,
        # ⚠️ 探针在**每个** .tsx 上都够多 ⇒ 那道「不许丢」才有判别力
        "probes_effective_on_every_tsx": tsx_enough,
    }
    res["checks"] = checks
    ok = all(checks.values())
    res["ok"] = ok

    print(json.dumps(res, ensure_ascii=False, indent=2))
    print()
    for k, v in checks.items():
        print(("  OK  " if v else "  ✗✗  ") + k)
    print(f"\n{'全通 ✓' if ok else '有门为红 ✗'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
