#!/usr/bin/env python3
"""每道真门禁都必须在自检框架里可达（第 30 道门禁，M303 新增，F141）。

**它守的是什么**：一道门禁如果自检框架跑不到它，那它坏了不会有任何人知道——
而「坏了但看起来还在」正是最难发现的一类。

**M303 的由来（本批实测）**：29 道门禁里，`check-shot-hashes.py`
在 `run_gate` 里连字符串都没出现过——也就是说它此前一条自检用例都没有，
而它偏偏是唯一一道「靠读图片实物」的门禁（清单里的 sha256 与 PNG 逐张对账）。

**同一批还查出一个更隐蔽的形态**：`run_gate` 原本的兜底分支是
「没列进分支的一律跑 check-claims.py」——
后果：新加一道门禁 + 新加一条用例、却忘了加分支时，那条用例实际在跑另一道门禁。
它要么报出别的理由（被「错因」抓到，算运气好），要么理由字样恰好相同
（那就是彻底的假通过）。本批把那个兜底改成了 raise（F141），
未知 which 现在是编程错误、当场炸出来。

---

**判据（必须有窄到能全对，所以这里有一张显式例外表）**：

每道 `scripts/check-*.py` 要满足下面两条中的任意一条：

1. **在 `run_gate` 里有自己的 `which == "..."` 分支**，且至少被一条 CASES 用到；或
2. **被登记进 `NOT_GATES`**，并写明它为什么不需要自检用例。

**唯一的例外是 `check-ledger-sync.py`**：它的**退出码恒为 0**，
它本来就是提示性检查、不阻断构建（账本内容的完整性由 `check-inventory-evidence.py` 负责）——
而「永远通过的门禁」没法用「注入故障、断言它拦住」的方式自检。

**判据为什么能全对**：M303 实测，登记这一条例外之后，29 道门禁全部满足。

---

**本脚本自己被自己的首跑打回来三次，三次都是判据的问题、不是被考的门禁坏了**（F127）：

- **F142**：`src.index("def run_gate(")` 取的是**文件里第一处**文本出现的位置。
  而本批新写的注入函数里就有一句 `text.index("def run_gate(")`——**于是「函数体」
  从注入函数中间开始、跨了 27000 多字符、含 3 个 `else:`**，
  兜底检测因此报出了一道八竿子打不着的门禁名。
  **判据用文本切代码，就必须能容忍同名文本；本版改用 AST 取真实函数定义。**
- **分支正则的 `\\s*` 跨不过注释行**：我给 `gateself` 分支加了两行注释说明，
  分支就被判成「不存在」——**判据比它要考的东西还脆。** 本版同样改走 AST。
- **F143**：F141 的检测第一版挂在「这个分支有没有自己的门禁」的 `elif` 上，
  于是**「最后一个分支自己有门禁」把兜底检测整段变成死代码**——
  而最后一个分支恰恰总是有门禁的（它是最新加的那道）。
  **`if A: … elif B: …` 等于给 B 加了个「A 为假」的前提；当 A 和 B 是两个独立事实时，
  这么写等于给其中一个装了一道永不触发的保险丝。**

**F141 的检测必须独立成一条问题**：本脚本第一版还把兜底分支里识别到的门禁
塞进了 `covered` 字典（当作一个 `which` 存进去），而那条 `which` 没有任何 CASES
指向它，于是它只给 `covered` 加了 0、永远不会报——**一段看起来在做事的死代码**。
两版死代码形态不同、位置不同，**但都是「读起来在做检查」的代码**；
它们不是被自检抓出来的，是被「逐行读自己写了什么」抓出来的（F139）。

**已声明盲区**：兜底检测只看「有没有给 `cmd` 赋一个门禁脚本」。
若有人写成 `raise ValueError("…… 参见 scripts/check-foo.py")`，本门禁看不见。

用法：
    python3 scripts/check-gate-self-coverage.py .
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# 不是门禁 / 不需要自检用例的，连理由一起登记——
#   不留空白的理由栏，是为了让「以后新增一道提示性检查」必须在这里留一笔。
NOT_GATES = {
    "check-ledger-sync.py": (
        "**退出码恒为 0 的提示性检查**，它不阻断构建"
        "（账本内容的完整性由 check-inventory-evidence.py 负责）——"
        "而一道永远通过的门禁没法用「注入故障、断言它拦住」的方式自检。"
    ),
}

_SCRIPT_RE = re.compile(r"scripts/(check-[a-z0-9\-]+\.py)")


def gates_of(root: Path) -> list[str]:
    return sorted(p.name for p in (root / "scripts").glob("check-*.py"))


def _which_of(node: ast.If) -> str | None:
    """If.test 形如 `which == "xxx"` 时返回 "xxx"，否则返回 None。"""
    t = node.test
    if not isinstance(t, ast.Compare) or len(t.ops) != 1 or len(t.comparators) != 1:
        return None
    if not isinstance(t.ops[0], ast.Eq):
        return None
    left, right = t.left, t.comparators[0]
    if not (isinstance(left, ast.Name) and left.id == "which"):
        return None
    if isinstance(right, ast.Constant) and isinstance(right.value, str):
        return right.value
    return None


def _cmd_gate_in(stmts: list[ast.stmt]) -> str | None:
    """在这组语句里找 `cmd = [... "scripts/check-x.py" ...]`，找到就返回门禁名。

    ★ **刻意只认「给 cmd 赋门禁脚本」这一种形态**：★★ **F141 要防的是
    ★ **「未知 which 静默去跑另一道门禁」，★ **而那必须表现为一个实际的赋值。**
    ★ **若放宽到「语句里出现过门禁名」，★★ **连注释里提一句别的门禁都会误报。**
    """

    for st in stmts:
        if not isinstance(st, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "cmd" for t in st.targets):
            continue
        for sub in ast.walk(st.value):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                m = _SCRIPT_RE.fullmatch(sub.value)
                if m:
                    return m.group(1)
    return None


def branches_and_cases(root: Path):
    """从 selftest-gates.py 里解析出「分支覆盖的脚本」「用到分支的 which」「兜底分支」。

    ★ **★ 走 AST 而不是文本切片（F142）**：★ **`def run_gate(` 这个字符串在本文件里
    ★ **不止出现一次**——★ **★ 本脚本配套的注入函数里就有一句 `text.index("def run_gate(")`。**
    ★ **★ 文本切片会从那一句开始切，★★ **切出来的「函数体」里会混进别的函数的 `else:`。**

    第三个返回值是 F141 的检测面。它绝不能混进 which2gate——混进去就等于让它
    给 covered 加 0，等于没有检测。
    """
    src = (root / "scripts" / "selftest-gates.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    fn = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run_gate":
            fn = node
            break
    if fn is None:
        raise SystemExit("[fail] selftest-gates.py 里找不到 def run_gate(...)")

    which2gate: dict[str, str] = {}
    fallback_gate = None
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        which = _which_of(node)
        if which is None:
            continue
        gate = _cmd_gate_in(node.body)
        if gate:
            which2gate[which] = gate
        # ★ **★ 「这个分支有没有自己的门禁」与「它后面是不是 else 兜底」是两个独立事实，
        # ★ **★ 所以它们不能共用一个 if/elif（F143）**——
        # ★ **★ elif 等于给后半句加了个「前半句为假」的前提，★★ **而最后一个分支
        # ★ **恰恰总是有门禁的，★★ **于是兜底检测成了一段永不执行的死代码。**
        #
        # 判据：orelse 的第一个语句若不是「下一个 elif」，那它就是 else 兜底分支。
        if node.orelse:
            nxt = node.orelse[0]
            if not (isinstance(nxt, ast.If) and _which_of(nxt) is not None):
                fallback_gate = _cmd_gate_in(node.orelse) or fallback_gate

    cases = None
    for node in tree.body:
        targets = (
            node.targets if isinstance(node, ast.Assign)
            else ([node.target] if isinstance(node, ast.AnnAssign) else [])
        )
        if any(getattr(t, "id", None) == "CASES" for t in targets):
            cases = node.value
    used: dict[str, list[str]] = {}
    if cases is not None:
        for el in cases.elts:
            el = el.value if isinstance(el, ast.Constant) else el
            if isinstance(el, (ast.Tuple, ast.List)) and len(el.elts) >= 3:
                used.setdefault(el.elts[2].value, []).append(el.elts[0].value)
    return which2gate, used, fallback_gate


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    which2gate, used, fallback_gate = branches_and_cases(root)

    covered: dict[str, int] = {}
    for which, gate in which2gate.items():
        covered[gate] = covered.get(gate, 0) + len(used.get(which, []))

    problems: list[str] = []

    if fallback_gate is not None:
        problems.append(
            f"[run_gate 的 else 兜底分支] 兜底分支里给 cmd 赋了具体门禁 {fallback_gate}（F141）\n"
            f"        → 后果：任何没列进分支的 which 都会被当成「跑它」——"
            f"新加一道门禁却忘了加分支时，那条用例会静默地去跑别的门禁。\n"
            f"          修法：兜底分支应当 raise KeyError，不给未知 which 任何默认行为。"
        )

    total = 0
    for g in gates_of(root):
        total += 1
        if g in NOT_GATES:
            continue
        if covered.get(g, 0) == 0:
            # ★ **★ 分开报两种形态（F139）**：★ **「连分支都没有」与「分支在、但没有用例指向它」
            # ★ **★ 是两种不同的失效**——★★ **前者通常是有人删了代码，
            # ★ **★ 后者通常是 which 字符串拼错了一个字（而拼错的那道门禁自己完全正常）。**
            # ★ **★ 报同一句话的话，★★ **查的人得自己回去 diff 才知道是哪种。**
            has_branch = g in which2gate.values()
            if has_branch:
                why = "run_gate 里有它的分支，但没有任何 CASES 用例指向那个 which"
                how = (
                    "修法：补至少一条 CASES 用例；或核对分支里的 which 字符串与用例里的第三个字段\n"
                    "          是否逐字一致（拼错一个字就会变成这一格，而门禁自己完全正常）"
                )
            else:
                why = "run_gate 里没有它的分支（自检框架压根跑不到它）"
                how = (
                    "修法：在 run_gate 里加一条 elif 分支，并至少加一条 CASES 用例；"
                    "若它确实是提示性检查，请登记进本脚本的 NOT_GATES 并写明理由"
                )
            problems.append(
                f"[{g}] 自检框架跑不到这道门禁：{why}\n"
                f"        → 一道门禁坏了却仍然「看起来还在」，是最难发现的一类。\n"
                f"          {how}"
            )

    if problems:
        print(f"[fail] 门禁自检覆盖校验未通过（{len(problems)} 项）：")
        for p in problems:
            print(f"  {p}")
        return 1

    excluded = ", ".join(sorted(NOT_GATES)) or "无"
    print(
        f"[ ok ] 门禁自检覆盖校验：{total} 道门禁全部在自检框架里可达，"
        f"且 run_gate 的兜底分支不指向任何具体门禁（登记为例外：{excluded}）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
