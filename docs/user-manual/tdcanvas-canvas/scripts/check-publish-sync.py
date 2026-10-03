#!/usr/bin/env python3
"""发布文档一致性校验：`PUBLISH.md` 描述的门禁集合必须与 `build-site.sh` 实际调用的一致。

背景（M106）：`PUBLISH.md` 用一整节表格描述"构建时的门禁"——门禁叫什么、拦什么、
哪一批发现的。这张表是**维护者据以排查的唯一索引**：构建挂了先看它。

但这张表是**手写的**，脚本才是事实源，两者之间**没有任何机制相连**。实测本批
打开它就抓到一处已经漂移的描述（标题写"十道门禁"，表里却列了 12 行）。这类漂移
的特点是**永远不会自己报错**：脚本照跑、门禁照过，只有照着文档排查的人会被误导。

本门禁做两件事：

1. 从 `build-site.sh` 里抽出**实际被调用**的 `scripts/*.py`（排除纯工具脚本
   `update-build-stats.py`，它不是门禁）；
2. 从 `PUBLISH.md` 的门禁表首列抽出**文档声称**的门禁名；
3. 断言两个集合**完全相等**，并单独核对 `build-site.sh` 声明的步骤总数与
   `PUBLISH.md` 步骤表里的行数。

**为什么用"集合相等"而不是"文档 ⊇ 脚本"**：少写一个门禁同样有害——排查的人
按文档走，漏掉的那道门禁根本不会出现在他的排查清单里。多写一个则是把不存在的
门禁写进文档，一样是误导。两个方向都得拦住。

===== M193 新增第三件事：文档里**声称的数量**也要对 =====

集合相等有个它自己看不见的盲区：**门禁表里"几道"这个数字没人管**。
实测本批打开它就抓到三处一起漂：标题写「十二道」、正文写「十六道」、
实际二十一；而专门守这张表的门禁**一直是绿的**——
因为它数的是"哪几个门禁"，数不到"几个字"。

这类漂移比漏一个门禁更隐蔽：门禁表是**维护者排查的唯一索引**，
照着"十六道门禁"去理解构建流程的人，拿到的是一份三年前的快照。

所以本门禁另外核对两处**当前数量**的声称：

- 文档里所有「N 道门禁」「N 道 + 一道自检」里的 N，必须等于实际门禁数
  （不含自检脚本本身）；
- `selftest-gates.py` 那行「注入 N 类故障」的 N，必须等于自检里实际的用例条数
  （用 `ast` 数，不靠正则猜）。

★ **只认「当前数量」，不认历史陈述**：门禁表的「由来」列里满是
「七道门禁下全部通过」「此前的十六道门禁无一扫它」这类**描述当时**的话，
拿今天的数量去判它们会全线误报。所以判据跳过门禁表本体，只看标题、导语
与自检那一行。

用法：

    python3 scripts/check-publish-sync.py .
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

PUBLISH = "PUBLISH.md"
BUILD = "build-site.sh"
SELFTEST = "selftest-gates.py"

# 工具脚本而非门禁：它只负责回填 README 的构建统计，不拦任何东西
NOT_GATES = {"update-build-stats.py"}

# 中文数字只到 99 就够用；门禁数量不会超过这个量级
CN_DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

# 「N 道门禁」/「N 道 + 一道自检」/「N 道门禁自检」——**都带限定词**，
# 免得把「它带三道保险」这类句子也算进来
COUNT_RE = re.compile(
    r"([零一二三四五六七八九十]+)道(?P<tail>\s*门禁自检|\s*门禁|\s*\+\s*一道自检)"
)
# 门禁表的「由来」列里的数字是**历史陈述**，跳过整张表
GATE_TABLE_HEADER = "| 门禁 | 拦什么 | 由来 |"
FAULT_RE = re.compile(r"注入\s*(\d+)\s*类故障")


def cn_to_int(text: str) -> int | None:
    """中文数字转整数；不是纯数字写法就返回 None（「这两道」不解析）。"""
    if not text or any(ch not in CN_DIGITS and ch != "十" for ch in text):
        return None
    if "十" not in text:
        return CN_DIGITS[text] if len(text) == 1 else None
    head, _, tail = text.partition("十")
    tens = CN_DIGITS[head] if head else 1
    ones = CN_DIGITS[tail] if tail else 0
    return tens * 10 + ones


def gate_table_span(text: str) -> tuple[int, int]:
    """门禁表在全文里的区间（含表头），里面的数字是历史陈述。"""
    start = text.find(GATE_TABLE_HEADER)
    if start < 0:
        return (-1, -1)
    end = start
    for line in text[start:].splitlines(keepends=True):
        if line.startswith("|"):
            end += len(line)
        elif line.strip():
            break
    return (start, end)


def quoted_spans(text: str) -> list[tuple[int, int]]:
    """「……」引起来的片段——**引号里的是举例，不是声明**。

    这条是 M193 被自己的新判据打回来之后补的：那段解释「历史陈述不该被判错」
    的文字本身就得举例，于是引号里出现了「七道门禁」「此前的十六道门禁」，
    判据把它们当成了当前数量的声明，**当场把作者自己写的说明判错**。

    排除引号是有依据的，不是为了放过错误：真正声明当前数量的地方
    （章节标题、导语、构建步骤表）**都不在引号里**。
    """
    spans: list[tuple[int, int]] = []
    pos = 0
    while True:
        start = text.find("「", pos)
        if start < 0:
            break
        end = text.find("」", start + 1)
        if end < 0:
            break
        spans.append((start, end + 1))
        pos = end + 1
    return spans


def selftest_case_count(root: Path) -> int | None:
    """用 `ast` 数出自检的用例条数——不靠正则数括号，数不准就返回 None。"""
    script = root / "scripts" / SELFTEST
    if not script.is_file():
        return None
    try:
        for node in ast.parse(script.read_text(encoding="utf-8")).body:
            targets = (node.targets if isinstance(node, ast.Assign)
                       else [node.target] if isinstance(node, ast.AnnAssign) else [])
            if any(getattr(t, "id", None) == "CASES" for t in targets):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    return len(node.value.elts)
    except SyntaxError:
        return None
    return None



def strip_comments(sh: str) -> str:
    """去掉整行注释。

    **这不是洁癖，是本门禁的第一个真实陷阱**：M106 实测 `audit_manual.py` 在
    `build-site.sh` 里出现 3 次，**全部在注释里**（都是解释历史事故的长注释），
    构建脚本从来没有执行过它。若不剥注释，它会被当成"脚本调用的门禁"，
    门禁表里那行就永远查不出问题——而事实上 PUBLISH.md 把它同时写成
    「手动单跑的审计步骤」和「构建时的门禁」，是**文档内部自相矛盾**。
    """
    return "\n".join(
        line for line in sh.splitlines() if not line.lstrip().startswith("#")
    )


def gates_in_build(build_sh: str) -> set[str]:
    body = strip_comments(build_sh)
    names = {Path(m).name for m in re.findall(r"scripts/[A-Za-z0-9_.-]+\.py", body)}
    return {n for n in names if n not in NOT_GATES}


def gates_in_publish(text: str) -> set[str]:
    """只取「构建时的门禁」那张表的**首列**——``脚本名`` 单元格。

    按表头定位到那一节再取，避免把文档里别处提到的脚本名算进来。
    """
    start = text.find("### 构建时的")
    if start < 0:
        return set()
    body = text[start:]
    names: set[str] = set()
    for line in body.splitlines():
        m = re.match(r"^\|\s*`([A-Za-z0-9_.-]+\.py)`\s*\|", line)
        if m:
            names.add(m.group(1))
    return names


def steps_in_build(build_sh: str) -> int:
    total = re.findall(r"步骤 \d+/(\d+)", build_sh)
    return max((int(n) for n in total), default=0)


def steps_in_publish(text: str) -> int:
    """步骤表里形如 `| 1/6 | 环境检查 | ...` 的行数。"""
    return len(re.findall(r"^\|\s*\d+/(\d+)\s*\|", text, re.M))


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    pub = root / PUBLISH
    build = root / BUILD

    for p in (pub, build):
        if not p.exists():
            print(f"[FAIL] 找不到 {p.name}")
            return 1

    text = pub.read_text(encoding="utf-8")
    sh = build.read_text(encoding="utf-8")

    real = gates_in_build(sh)
    doc = gates_in_publish(text)

    ok = True

    missing = sorted(real - doc)          # 脚本跑了、文档没写
    extra = sorted(doc - real)            # 文档写了、脚本没跑
    if missing:
        print("[FAIL] 以下门禁被 build-site.sh 调用，但 PUBLISH.md 的门禁表里没有：")
        for n in missing:
            print(f"    {n}")
        ok = False
    if extra:
        print("[FAIL] 以下门禁写在 PUBLISH.md 的门禁表里，但 build-site.sh 并没有调用：")
        for n in extra:
            print(f"    {n}")
        ok = False

    steps_real = steps_in_build(sh)
    steps_doc = steps_in_publish(text)
    if steps_real and steps_doc and steps_real != steps_doc:
        print(f"[FAIL] 构建步骤数不一致：build-site.sh 声明 {steps_real} 步，"
              f"PUBLISH.md 步骤表写了 {steps_doc} 行")
        ok = False

    # --- M193：文档里「几道门禁」「注入几类故障」这两个数字也要对 ---
    # 自检脚本本身不是门禁，文档里「N 道门禁 + 一道自检」的 N 不含它。
    real_gates = real - {SELFTEST}
    lo, hi = gate_table_span(text)
    quotes = quoted_spans(text)
    for m in COUNT_RE.finditer(text):
        if lo <= m.start() < hi:
            continue                      # 「由来」列里的是历史陈述，不是当前数量
        if any(a <= m.start() < b for a, b in quotes):
            continue                      # 引号里的是举例，同样不是声明
        claimed = cn_to_int(m.group(1))
        if claimed is None:
            continue
        # 「N 道门禁自检」里的 N 说的是**自检那 1 道**，不是门禁总数——
        # 判据必须区分这两种，否则「一道门禁自检」会被当成「一道门禁」而误报。
        tail = m.group("tail").strip()
        expected = 1 if tail.endswith("门禁自检") else len(real_gates)
        if claimed != expected:
            line = text.count("\n", 0, m.start()) + 1
            want = "1 道自检" if expected == 1 else f"{expected} 道门禁"
            print(f"[FAIL] PUBLISH.md 第 {line} 行说「{m.group(1)}道{tail}」，"
                  f"而实际是 {want}（不含 {SELFTEST}）")
            ok = False

    cases = selftest_case_count(root)
    fault = FAULT_RE.search(text)
    if cases is not None and fault and int(fault.group(1)) != cases:
        print(f"[FAIL] PUBLISH.md 说自检注入 {fault.group(1)} 类故障，"
              f"而 scripts/{SELFTEST} 里实际有 {cases} 条用例")
        ok = False

    if not ok:
        print("    门禁表是维护者排查的唯一索引，两边对不上会直接误导排查。")
        return 1

    print(f"[ ok ] 发布文档一致性：{len(real)} 道门禁的文档与脚本集合一致，"
          f"声称的门禁数（{len(real_gates)}）与自检用例数（{cases}）也对得上"
          f"（构建步骤 {steps_real} 步，文档 {steps_doc} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
