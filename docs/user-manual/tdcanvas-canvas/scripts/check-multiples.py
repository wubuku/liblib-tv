#!/usr/bin/env python3
"""倍数与显式算式校验（第二十八道门禁，M297 新增，F133 的门禁化）。

**起因是一处当场可证的算术错**（M296 订正为 R118）：

`connect-references.md` 同一段里先写「命中半宽 = 8 × 缩放、可见线全宽 = 2 × 缩放」，
**这两个数一直是对的**；下一行却推出「能点中的范围永远是你看得见的那条线的 8 倍宽」。
**8 ÷ 2 = 4，不是 8。**

**为什么二十七道门禁一道都没抓到**：M269 立过两条与像素有关的判据——
F100（对称性）与 F101（像素数归类），**两条查的都是「这个值本身对不对」**。
而这一句错的是「**两个都对的值相除之后对不对**」。
倍数是一类独立断言，而**所有按「值」建的判据全都查不到它**。这就是 F133。

---

**本门禁做两件事，边界逐条写明，不夸大**：

**判据一（自动）**：扫正文页里**显式写出来的算式**（`A ÷ B = C`、`A / B = C`、
`A × B = C`，`≈` 与 `=` 都收），逐条验算，容差 `max(0.01, |C| × 0.005)`。
★ **这是本门禁唯一能「自动发现」的一类**——算式自带三个数，不用人登记。
★ **M297 建这道门禁时实测：正文 21 页共 9 处显式算式，逐条验算全部通过、0 处误报**
（`20-reference` 1、`30-concepts` 1、`connect-references` 3、`manage-assets` 3、
以及 M297 补进 `30-concepts` 的那条）。窄到没有误报余地，才配当门禁（M195）。

**判据二（手读建表）**：下面 `MULTIPLES` 里 6 条倍数断言的**结论句逐字在位**，
外加**表自身自洽**（`operands` 按 `relation` 算出来必须等于 `expected`）。

★★ **判据二的能力边界，必须说清楚**：★ **它抓的是「改了正文忘改表」，
★ **抓不到「表里的 operands 写错了」之外的更多东西**——
★ **needle 只锁结论句，★ **分子分母那两个数是台账里手写的，★ **机器不会去正文里核对它们。
★ **换句话说：它不是「自动发现所有倍数错误」的判据，★ **它是「让这 6 条不许悄悄改掉」的护栏。**

**它同样不覆盖「N 倍」这类隐含倍数**：正文里 `N 倍` 只有 7 处（`connect-references` 3、
`30-concepts` 1、`manage-assets` 1、`navigate-canvas` 1、`90-troubleshooting` 1），
★ **其中「把那一行裁出来放大 4 倍」是操作建议、不是测量断言，** 剩 6 条已全部进表。
★ **而「23 倍」那条本批已手算复核：1285 ÷ 55 = 23.36，取整 23，★ **成立（第 7 次否证）。**

用法：
    python3 scripts/check-multiples.py .
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- 正文页口径
# ★ **与 check-source-refs.py 的 BODY_GLOBS 同口径**：读者会读到的那些页。
#   **账本四份（AUDIT / PROGRESS / PUBLISH / SOURCE_OBSERVATIONS）不在其中**——
#   理由是它们记的是历史读数，历史记录里的算式不该被今天的判据重新裁决
#   （M296 已经在自己身上踩过一次：账本里 `8 / 13 = 6` 是「从 2 到 13 共几种」的语境，不是算式）。
BODY_PAGES = [
    "README.md",
    "00-quickstart.md",
    "20-reference.md",
    "30-concepts.md",
    "90-troubleshooting.md",
]

# ---------------------------------------------------------------- 台账
MULTIPLES = [
    {
        "id": "K1",
        "file": "10-tasks/connect-references.md",
        "needle": "能点的半宽正好是可见线全宽的 4 倍",
        "relation": "quotient",
        "operands": [8, 2],
        "expected": 4.0,
        "why": "命中半宽 8、可见线全宽 2。★ **M296 订正前这里写的是 8 倍**",
    },
    {
        "id": "K2",
        "file": "10-tasks/connect-references.md",
        "needle": "都是你看得见的那条线的 4 倍宽",
        "relation": "quotient",
        "operands": [8, 2],
        "expected": 4.0,
        "why": "同一条结论的第二个落点（连线的倍数记法）",
    },
    {
        "id": "K3",
        "file": "10-tasks/connect-references.md",
        "needle": "10 ÷ 4 与 1 ÷ 0.5 恰好都是 2.5 倍和 2 倍",
        "relation": "quotient",
        "operands": [10, 4],
        "expected": 2.5,
        "why": "200% 档被面板截断时的比值。★ **它是「被污染读数不能当结论」的反证**",
    },
    {
        "id": "K4",
        "file": "10-tasks/connect-references.md",
        "needle": "10 ÷ 4 与 1 ÷ 0.5 恰好都是 2.5 倍和 2 倍",
        "relation": "quotient",
        "operands": [1, 0.5],
        "expected": 2.0,
        "why": "同上一句里的 25% 档那一半",
    },
    {
        "id": "K5",
        "file": "30-concepts.md",
        "needle": "前者正好是后者的 4 倍",
        "relation": "quotient",
        "operands": [8, 2],
        "expected": 4.0,
        "why": "★ **M297 新补的像素归类行**——★ **而 M269 早把它归成了画布坐标，正文这张表却一直漏着**",
    },
    {
        "id": "K6",
        "file": "90-troubleshooting.md",
        "needle": "它比节点宽 23 倍",
        "relation": "quotient",
        "operands": [1285, 55],
        "expected": 23.0,
        "rounding": "round",
        "why": "工具条恒 1285px、25% 时节点仅 55px。★ **M297 手算复核 1285 ÷ 55 = 23.36，取整 23 成立**",
    },
    {
        "id": "K7",
        "file": "10-tasks/navigate-canvas.md",
        "needle": "1.1 倍率",
        "relation": "plus",
        "operands": [1.0, 0.1],
        "expected": 1.1,
        "why": "★ **唯一一条不是除法的**（步进 +10%）。★ **带 `relation` 字段就是为了容得下它**",
    },
]

RELATIONS = {"quotient", "plus", "times"}

# 显式算式
EQ = re.compile(
    r"(\d+(?:\.\d+)?)\s*(÷|/|×|x|\*)\s*(\d+(?:\.\d+)?)\s*(≈|=|＝)\s*(\d+(?:\.\d+)?)"
)


def strip_markup(text: str) -> str:
    return text.replace("**", "").replace("`", "")


def compute(relation: str, a: float, b: float) -> float:
    if relation == "quotient":
        return a / b
    if relation == "plus":
        return a + b
    if relation == "times":
        return a * b
    raise ValueError(relation)


def body_pages(root: Path) -> list[Path]:
    out = [root / n for n in BODY_PAGES]
    out += sorted((root / "10-tasks").glob("*.md"))
    return [p for p in out if p.is_file()]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    problems: list[str] = []

    # ---------------------------------------------------------- 判据一：显式算式
    eq_total = 0
    for page in body_pages(root):
        rel = page.relative_to(root).as_posix()
        for ln, line in enumerate(
            page.read_text(encoding="utf-8").split("\n"), 1
        ):
            for m in EQ.finditer(line):
                a, op, b, _rel_sign, c = m.groups()
                a, b, c = float(a), float(b), float(c)
                if op in ("÷", "/"):
                    if b == 0:
                        problems.append(f"[{rel}:{ln}] 算式分母为 0：{m.group(0)!r}")
                        continue
                    calc = a / b
                else:
                    calc = a * b
                eq_total += 1
                tol = max(0.01, abs(c) * 0.005)
                if abs(calc - c) > tol:
                    problems.append(
                        f"[{rel}:{ln}] 算式验算不过：{m.group(0)!r}"
                        f" —— 左边算出来是 {calc:.4f}，右边写的是 {c}（容差 {tol:.4f}）\n"
                        f"        → 要么算式里的某个数被改过，★ **要么结论根本没跟着改**（F133）"
                    )

    # ---------------------------------------------------------- 判据二：台账
    for rec in MULTIPLES:
        rid, rel_path, needle = rec["id"], rec["file"], rec["needle"]
        target = root / rel_path
        if not target.is_file():
            problems.append(f"[{rid}] 指向的文件不存在：{rel_path}")
            continue

        relation = rec["relation"]
        if relation not in RELATIONS:
            problems.append(f"[{rid}] relation 不是合法值：{relation!r}（合法：{sorted(RELATIONS)}）")
            continue
        a, b = rec["operands"]
        calc = compute(relation, a, b)
        expected = rec["expected"]
        if rec.get("rounding") == "round":
            ok = round(calc) == round(expected)
        else:
            ok = abs(calc - expected) <= max(0.01, abs(expected) * 0.005)
        if not ok:
            problems.append(
                f"[{rid}] 台账自身不自洽：{a} 与 {b} 按 {relation} 算得 {calc:.4f}，"
                f"而 expected 写的是 {expected}"
            )

        # needle 在正文里必须逐字存在（剥掉 markdown 标记之后比）
        ttext = strip_markup(target.read_text(encoding="utf-8"))
        if strip_markup(needle) not in ttext:
            problems.append(
                f"[{rid}] 结论句在 {rel_path} 里已找不到：{needle!r}\n"
                f"        → 正文被改写了而台账没跟着改。★ **倍数是最容易「顺手改个数」的一类**"
            )

    if problems:
        print(f"[fail] 倍数与算式校验未通过（{len(problems)} 项）：")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        f"[ ok ] 倍数与算式校验：正文 {eq_total} 处显式算式逐条验算通过，"
        f"{len(MULTIPLES)} 条倍数断言在位且台账自洽"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
