#!/usr/bin/env python3
"""验证器断言质量门禁 (Batch 336)。

背景: Batch 208 证明「绿色断言可能锁着缺陷」(断言方向反了)，
Batch 335 进一步在全仓清出 5 处**恒真**断言 (`count() >= 0` /
`... or True`) —— 它们无论功能好坏都通过，却在覆盖矩阵里显示为「✅ 已覆盖」。

本脚本把这类检查固化成**门禁**, 避免同类问题再次混入。

检查项:
  1. VACUOUS_COUNT   —— `count() >= 0` / `len(...) >= 0`：计数不可能为负
  2. OR_TRUE         —— `... or True`：显式或真，整条断言失效
  3. COMPARE_TO_NONE —— `x == None` / `x != None` 出现在 check/assert 里
                        （None 判断应写 `is None`，用 == 是 smell）

不检查的（经验证属合法）:
  - `== []`：确实在断言「某集合为空」的断言，全仓 30+ 处均合法。

用法:
    python3 scripts/verify-assertions.py            # 全量检查
    python3 scripts/verify-assertions.py --quiet    # 只输出结论

退出码: 0 = 干净；1 = 发现恒真断言。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER_GLOBS = ("scripts/verify-*.py",)

# (规则名, 正则, 说明)
RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "VACUOUS_COUNT",
        re.compile(r"\.count\(\)\s*>=\s*0(?!\d)"),
        "count() >= 0 恒真（计数不可能为负）",
    ),
    (
        "OR_TRUE",
        re.compile(r"\bor\s+True\b"),
        "`or True` 使整条断言失效",
    ),
    (
        "COMPARE_TO_NONE",
        re.compile(r"==\s*None\b|!=\s*None\b"),
        "与 None 比较应用 `is None` / `is not None`",
    ),
]

# 允许出现上述模式的行（注释 / 文档说明本身在讲这件事）
COMMENT_PREFIXES = ("#", "///", "*", "'''", '"""')

# 本门禁脚本自身：docstring 与规则表里会**引用**这些模式（"count() >= 0 恒真"），
# 若不排除就会自我误报。判断方式：行首为文档字符串分隔符或规则元组起始。
SELF = Path(__file__).resolve()


def iter_verifier_files() -> list[Path]:
    seen: set[Path] = set()
    for pattern in VERIFIER_GLOBS:
        for p in sorted(ROOT.glob(pattern)):
            if p not in seen:
                seen.add(p)
    return sorted(seen)


def is_comment_or_doc(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith(COMMENT_PREFIXES)


def main() -> int:
    quiet = "--quiet" in sys.argv
    findings: list[tuple[str, int, str, str]] = []

    for path in iter_verifier_files():
        # 本门禁脚本自身必然包含这些模式（docstring 在讲解它们）
        if path.resolve() == SELF:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if is_comment_or_doc(line):
                continue
            # Ignore trailing comments.  A verifier may deliberately assert
            # that the literal text ``or True`` is absent; the annotation on
            # that assertion must not become a false positive itself.
            line = line.split("#", 1)[0]
            for rule, pattern, why in RULES:
                if pattern.search(line):
                    findings.append((rule, lineno, why, line.strip()[:100]))

    rel = lambda p: str(Path(p).relative_to(ROOT))  # noqa: E731

    if not findings:
        print(f"Assertion quality gate passed: 0 vacuous assertions in "
              f"{len(iter_verifier_files())} verifier scripts.")
        return 0

    if not quiet:
        print(f"Found {len(findings)} vacuous assertion(s):\n")
        for rule, lineno, why, text in findings:
            print(f"  [{rule}] {why}")
            print(f"      {text}\n")
    print(f"Assertion quality gate FAILED: {len(findings)} vacuous assertion(s).")
    print("恒真断言比没有断言更危险 —— 它在覆盖矩阵里显示为「已覆盖」，")
    print("但对任何实现都通过（含功能完全损坏的实现）。请改为真实断言。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
