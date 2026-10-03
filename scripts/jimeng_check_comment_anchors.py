#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""普查：verifier 里那些**打在 `strip_comments()` 派生变量上**的锚文，
逐条判定它读的是**代码**还是**注释**；并要求「读注释的必须是 0 条」。

⚠️ 为什么要有这道门（批 942 的由来）：
    941 之前 `strip_comments` 对 `.tsx` 几乎不生效（错误的引号条件把普通
    双引号当成三引号开头 ⇒ 后面整段被当成字符串跳过）。于是**判据读的
    一直是没有剥过的原文**。修好之后，全套判据里**恰好一条**变红：AA.3。
    查下去发现它钉的是**源码注释里的一句散文**
    （「刻意**不** `stopPropagation()`」）——
    ⭐ 那句注释只要还在就绿，**就算有人真的往 Clear 的 Esc 分支加上
    `stopPropagation()` 也照样绿**。一个恒真的判据比没有判据更坏。
    这道门把「判据锚在注释散文上」从**一次性事故**变成**可查项**。

两道「不许复制实现」的纪律：
    · `strip_comments` 从 verifier 的 AST 里取**原样**执行（936 栽过
      「两份漂移」，936 记：复制一份就会出现两份实现慢慢分家）。
    · `_aa3_ok`（AA.3 的判据函数）同样用 `ast.unparse` 取**原样**执行，
      这样阳性对照测的就是**判据本体**，不是这里抄的一份。

自己不许把自己测成空门（承 940 的阳性对照纪律）：
    · `census_nonempty` —— 扫不到锚文就是「什么都没测」，判红。
    · `aa3_positive_control` —— 判据函数必须**能被证伪**：未变异 True，
      且 8 个变异全部 False。其中「全文件从不调用 stopPropagation」
      是**空洞写法**，只看否定判据必被它白送（承 940：阴阳对照门的两个
      答案必须来自两个不同的集合）。
    · `mutations_all_applied` —— **每个变异都必须真的改动了文本**。
      ⚠️⚠️ 本工具第一版就栽在这里：三个 `re.sub` 因为 `.` 不跨行而
      **静默没匹配**，判据因此「正确地」保持 True ⇒ 看起来是阳性对照
      通过，其实是**空白对照**。变异没发生必须当失败，不许当通过。

跑法： /opt/miniconda3/bin/python3 scripts/jimeng_check_comment_anchors.py
退出码 0 = 六道门全通。
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 允许指向**另一份** verifier 副本 —— 唯一用途是**证伪本工具**：
# 把旧版 AA.3 那条「读注释的锚文」塞回副本里跑一遍，G3 必须变红。
# 「一道恒绿的门比没有门更坏」——所以每道门都要有一份**专为推翻它**
# 造出来的反例。
VERIFIER = (pathlib.Path(sys.argv[1]) if len(sys.argv) > 1
            else ROOT / "scripts/verify-jimeng-batch841-unclickable.py")
OUT = pathlib.Path("/tmp/jimeng-comment-anchors.json")

# 「剥除器自测」那个内联合成用例的绑定名 —— 它量的是剥除器自己，
# 不是任何真实源文件，所以它的锚文不参与「读代码 / 读注释」分类。
SYNTH_BINDINGS = {"_sc_out"}

SOURCE_EXT = re.compile(r"\.(?:tsx|ts|py)$")

# 判据锚文至少要有这么多条，否则本工具测的是空气。
MIN_ANCHORS = 40
# ⚠️ 阈值用**关系式**（承「预算类要求用关系式，不钉实测常量」）：
#   941→942 期间锚文总数从 60 降到 56（AA.3 内联字面量被收进 `_aa3_ok`），
#   钉绝对数就会在正常演进时假红。这里钉「读代码的占比」+ 一个地板值。
MIN_CODE_ANCHORS = 40
MIN_CODE_RATIO = 0.85

GATES: list[tuple[str, str, bool]] = []


def gate(name: str, ok: bool, detail: str = "") -> bool:
    GATES.append((name, detail, bool(ok)))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" —— {detail}" if detail else ""))
    return bool(ok)


# ── 一、从 verifier 里原样取两个实现（不许复制）────────────────────
def load_strip_comments():
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "strip_comments")
    ns: dict = {}
    exec(ast.unparse(fn), ns)
    return ns["strip_comments"]


def load_aa3_ok():
    """AA.3 的判据函数。942 之前 AA.3 是内联布尔表达式、无处可测，
    942 把它收成 `_aa3_ok(s)` 才好做阳性对照 —— 「可被证伪」这件事
    本身要求判据是**一个可调用的东西**。"""
    tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_aa3_ok")
    ns: dict = {}
    exec(ast.unparse(fn), ns)
    return ns["_aa3_ok"]


# ── 二、把 `X = strip_comments(Y)` 的 Y 解析成磁盘上的源文件 ─────────
def _path_from_segment(seg: str) -> str | None:
    """从一条赋值语句里取出**路径字面量**。

    ⚠️ 必须把**路径那几段**拼起来看：`AUDIT = ROOT / "scripts" /
    "jimeng_unclickable_audit.py"` 是两段，只截第一段匹配到的那个会得到
    `jimeng_unclickable_audit.py`（少一级目录）⇒ 拼出来才认得出。

    ⚠️ 但**不能无脑全拼**：`(ROOT / "src/…Panel.tsx").read_text(
    encoding="utf-8")` 里还有一个 `"utf-8"`（编码参数，不是路径），
    全拼会得到 `src/…Panel.tsx/utf-8`、结尾不再是源码后缀 ⇒ 又解析不出来。
    ⇒ 取**最短的那个能以源码后缀结尾的前缀拼接**：路径字面量总是紧挨在
    扩展名之前结束，编码参数之类的一概不带。
    本工具前两版各栽在这半边一次（「一个恒真的字段比没有字段更坏」两次）。
    """
    parts = re.findall(r'"([^"]*)"', seg)
    for i in range(len(parts)):
        joined = "/".join(p for p in parts[:i + 1] if p)
        if SOURCE_EXT.search(joined):
            return joined
    return None


def collect_bindings():
    src = VERIFIER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    # 第 1 遍：把**路径字面量**赋给变量的那些直接记下来
    #   （`chrome = (ROOT / "src/…/jimengMenuChrome.tsx")`）。
    paths: dict[str, str] = {}
    for n in ast.walk(tree):
        if not isinstance(n, ast.Assign):
            continue
        rel = _path_from_segment(ast.get_source_segment(src, n) or "")
        if not rel:
            continue
        for t in n.targets:
            if isinstance(t, ast.Name):
                paths[t.id] = rel
    # 第 2 遍：**追别名**。verifier 里大半是
    #   `hm = ROOT / "…HistoryMenu.tsx"`  →  `hsrc = hm.read_text(…)`
    #   这种两段式；本工具第一遍只做了第一段，于是 6 个绑定解析不出来、
    #   它们名下的 19 条锚文被**误判成合成用例** ⇒ 「读注释 0 条」这道门
    #   对那 19 条**根本没测**。它自己没察觉，是 G4 拒了这次运行
    #   （「一个恒真的字段比没有字段更坏」当场复发）。
    #   ⚠️ 别名那一行常写成 `X = Y.read_text(…) if Y.exists() else ""`
    #   —— 那是 `IfExp` 不是 `Call`，只认 Call 会**再漏一半**。
    #   ⚠️ 追到定为止：别名可能套多层。
    alias: dict[str, str] = {}
    for n in ast.walk(tree):
        if not isinstance(n, ast.Assign):
            continue
        v = n.value.body if isinstance(n.value, ast.IfExp) else n.value
        if not isinstance(v, ast.Call):
            continue
        if not (isinstance(v.func, ast.Attribute) and v.func.attr == "read_text"):
            continue
        base = v.func.value
        if not isinstance(base, ast.Name):
            continue
        for t in n.targets:
            if isinstance(t, ast.Name):
                alias[t.id] = base.id
    for _ in range(len(alias) + 1):
        changed = False
        for var, ref in alias.items():
            if var in paths:
                continue
            if ref in paths:
                paths[var] = paths[ref]
                changed = True
        if not changed:
            break
    # stripped var -> 实参变量名
    binding: dict[str, str] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            f = n.value.func
            if getattr(f, "id", None) == "strip_comments" and n.value.args:
                a = n.value.args[0]
                tgt = next((t.id for t in n.targets if isinstance(t, ast.Name)), None)
                if tgt and isinstance(a, ast.Name):
                    binding[tgt] = a.id
    return src, tree, paths, binding


# ── 三、把每条 `锚文 in <stripped 变量>` / `<变量>.count(锚文) == N` 抽出来 ──
def collect_anchors(src: str, tree, stripped_vars: set[str]):
    rows = []

    def push(lineno, var, lit, shape, title):
        rows.append({"lineno": lineno, "var": var, "lit": lit,
                     "shape": shape, "title": title[:90]})

    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
        if fn != "check" or len(n.args) < 2:
            continue
        title = ast.get_source_segment(src, n.args[0]) or ""
        cond = n.args[1]
        for m in ast.walk(cond):
            if not isinstance(m, ast.Compare):
                continue
            # 「锚文」in 变量
            if (len(m.ops) == 1 and isinstance(m.ops[0], ast.In)
                    and isinstance(m.left, ast.Constant)
                    and isinstance(m.left.value, str)
                    and isinstance(m.comparators[0], ast.Name)
                    and m.comparators[0].id in stripped_vars):
                push(m.lineno, m.comparators[0].id, m.left.value, "in", title)
            # 变量.count(「锚文」) == N
            if (len(m.ops) == 1 and isinstance(m.ops[0], ast.Eq)
                    and isinstance(m.left, ast.Call)
                    and isinstance(m.left.func, ast.Attribute)
                    and m.left.func.attr == "count"
                    and isinstance(m.left.func.value, ast.Name)
                    and m.left.func.value.id in stripped_vars
                    and m.left.args
                    and isinstance(m.left.args[0], ast.Constant)
                    and isinstance(m.left.args[0].value, str)):
                push(m.lineno, m.left.func.value.id, m.left.args[0].value,
                     "count", title)
    return rows


def main() -> int:
    print("— 批 942：判据锚文到底读代码还是读注释 —")
    strip = load_strip_comments()
    src, tree, paths, binding = collect_bindings()
    stripped_vars = set(binding)
    print(f"  strip_comments 绑定点：{len(stripped_vars)} 个 {sorted(stripped_vars)}")

    # 逐个绑定解析磁盘源文件；解析不到的必须显式是合成用例
    raw: dict[str, str] = {}
    unresolved: list[str] = []
    for var, arg in sorted(binding.items()):
        rel = paths.get(arg)
        if rel and (ROOT / rel).exists():
            raw[var] = (ROOT / rel).read_text(encoding="utf-8")
        elif var in SYNTH_BINDINGS:
            unresolved.append(var)          # 剥除器自测的内联合成用例
        else:
            unresolved.append(var)
            print(f"  ⚠️ 解析不到源文件：{var} <- {arg}")
    stripped = {k: strip(v) for k, v in raw.items()}

    rows = collect_anchors(src, tree, stripped_vars)
    print(f"  锚文总数：{len(rows)}")

    code = comment_only = synth = absent = 0
    for r in rows:
        var, lit = r["var"], r["lit"]
        if var not in stripped:
            r["cls"] = "SYNTH"
            synth += 1
            continue
        if lit in stripped[var]:
            r["cls"] = "CODE"
            code += 1
        elif lit in raw[var]:
            r["cls"] = "COMMENT_ONLY"
            comment_only += 1
            print(f"    ⚠️ 读注释的锚文 L{r['lineno']} {var}：{lit[:60]!r}")
        else:
            r["cls"] = "ABSENT_BOTH"
            absent += 1
    print(f"  分类：CODE={code}  COMMENT_ONLY={comment_only}  "
          f"SYNTH={synth}  ABSENT_BOTH={absent}")

    OUT.write_text(json.dumps(
        {"anchors": len(rows), "code": code, "comment_only": comment_only,
         "synth": synth, "absent_both": absent,
         "unresolved_bindings": unresolved, "rows": rows},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  → {OUT}")

    gate("G1 census_nonempty —— 锚文 ≥ %d 条（防空门）" % MIN_ANCHORS,
         len(rows) >= MIN_ANCHORS, f"扫到 {len(rows)} 条")
    gate("G2 code_anchors_resolved —— 判为 CODE 的 ≥ %d 条且占比 ≥ %.0f%%"
         % (MIN_CODE_ANCHORS, MIN_CODE_RATIO * 100),
         code >= MIN_CODE_ANCHORS and code >= MIN_CODE_RATIO * len(rows),
         f"{code}/{len(rows)} 条")
    gate("G3 comment_only_zero —— **读注释的锚文 0 条**（942 就是它变红的）",
         comment_only == 0, f"{comment_only} 条")
    gate("G4 synth_excluded —— 合成用例只挂在剥除器自测的绑定上、"
         "且不许挂在真实源文件上",
         set(unresolved) <= SYNTH_BINDINGS
         and all(r["cls"] != "SYNTH" or r["var"] in SYNTH_BINDINGS for r in rows),
         f"未解析={unresolved}")
    gate("G5 absent_both_zero —— 锚文在原文与剥后都不存在（判据必红）",
         absent == 0, f"{absent} 条")

    # ── 六、AA.3 的阳性对照：判据函数必须能被证伪 ───────────────────
    ok = run_aa3_positive_control(strip)
    gate("G6 aa3_positive_control —— AA.3 未变异为 True 且 8 个变异全 False"
         "（每个变异都**真的改了文本**）", ok)
    return 0 if all(g[2] for g in GATES) else 1


def run_aa3_positive_control(strip) -> bool:
    tsx = ROOT / "src/components/jimeng/JimengAudioGenPanel.tsx"
    if not tsx.exists():
        print("  ⚠️ 找不到 JimengAudioGenPanel.tsx，跳过阳性对照")
        return False
    try:
        aa3_ok = load_aa3_ok()
    except (StopIteration, SyntaxError) as e:
        print(f"  ⚠️ 取不到 `_aa3_ok`（{e}）—— 阳性对照没法做")
        return False
    s0 = strip(tsx.read_text(encoding="utf-8"))

    # ⚠️ 取窗口必须**照抄判据自己的取法**：这个文件里更早还有别的
    #   `onKeyDown={(e) => {`（面板自己的 Esc handler）——本工具第一版
    #   从文件开头取窗口，取到的是**那一个**，于是所有变异都落空。
    #   「够不着」和「够错了」都会让阳性对照变成空白对照。
    ar = 'aria-label={`Clear ${label} filter`}'
    kd = "onKeyDown={(e) => {"
    _h, _m, tail = s0.partition(ar)
    if not _m:
        print("  ⚠️ 剥后源码里找不到 Clear 按钮的 aria-label")
        return False
    _kd, kdm, after = tail.partition(kd)
    if not kdm:
        print("  ⚠️ Clear 按钮之后找不到它自己的 onKeyDown")
        return False
    esc, lbm, _r = after.partition('role="listbox"')
    if not lbm:
        print("  ⚠️ 找不到后面的音色库 listbox（阳性对照那侧）")
        return False

    def mutate(pattern: str, repl: str) -> str:
        """只在 esc 段内变异，再拼回去；**匹配不到就炸**。"""
        new, k = re.subn(pattern, repl, esc, count=1, flags=re.S)
        if k != 1:
            raise AssertionError(f"变异没发生：{pattern}")
        return s0.replace(esc, new, 1)

    try:
        cases = {
            "1 往 Clear 的 Esc 分支加 stopPropagation":
                (mutate(r'if \(e\.key === "Escape"\) \{',
                        'if (e.key === "Escape") { e.stopPropagation();'), False),
            "2 删掉 Esc 里的清除 setFilterSel":
                (mutate(r"setFilterSel\(\(m\) => \(\{.*?\}\)\);", ""), False),
            "3 全文件都不调 stopPropagation（**空洞写法**）":
                (re.sub(r"e\.preventDefault\(\);\s*e\.stopPropagation\(\);",
                        "e.preventDefault();", s0, count=1), False),
            "4 Clear 按钮整个消失":
                (s0.replace(ar, "aria-label={`Nope`}"), False),
            "5 Esc 分支改成 focus() 芯片、删掉清除":
                (mutate(r"refocusToNodeFromToolbar\(.*?\);",
                        "chipRefs.current[label]?.focus();"), False),
            "6 Esc 分支不关层":
                (mutate(r"setFilterOpen\(\(o\) => \(\{.*?\}\)\);", ""), False),
            "7 阳性对照那侧的 role 改名":
                (s0.replace('role="listbox"', 'role="list"'), False),
            "8 只重排版（缩进压成单空格）—— 必须**仍然** True":
                (" ".join(s0.split()), True),
        }
    except AssertionError as e:
        print(f"  ⚠️ {e}")
        return False

    all_ok = True
    for name, (mutated, want) in sorted(cases.items()):
        # ⚠️⚠️ 变异没发生 == 空白对照，必须当失败（本工具第一版栽在这）
        if want is not True and mutated == s0:
            print(f"    !! 变异**未发生**：{name}")
            all_ok = False
            continue
        got = aa3_ok(mutated)
        if got != want:
            print(f"    !! {name}：得到 {got}，期望 {want}")
            all_ok = False
    if aa3_ok(s0) is not True:
        print("    !! 未变异的源码就没通过 —— 判据本身错了")
        all_ok = False
    print(f"  阳性对照：{len(cases)} 个变异，"
          f"{'全部按预期' if all_ok else '**有变异没被抓住**'}")
    return all_ok


if __name__ == "__main__":
    sys.exit(main())
