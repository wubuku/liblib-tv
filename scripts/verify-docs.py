from pathlib import Path
import re
import sys
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = [
    path
    for path in ROOT.rglob("*.md")
    if "node_modules" not in path.parts
    and ".next" not in path.parts
    and ".git" not in path.parts
    and ".agents" not in path.parts
]

LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
ROOT_RELATIVE_SOURCES = {
    Path(".continue/rules/project.md"),
    Path(".github/copilot-instructions.md"),
    Path(".amazonq/rules/project.md"),
}


def is_external(target: str) -> bool:
    return (
        target.startswith(("http://", "https://", "mailto:", "data:"))
        or target.startswith("#")
    )


def candidate_paths(source: Path, target: str):
    target = target.strip().strip("<>")
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target or is_external(target):
        return []

    decoded = Path(unquote(target))
    relative_source = source.relative_to(ROOT)
    base = ROOT if relative_source in ROOT_RELATIVE_SOURCES else source.parent
    resolved = (base / decoded).resolve()
    if resolved.is_dir():
        return [resolved / "README.md", resolved / "index.md"]
    return [resolved]


def is_expected_missing(target: str) -> bool:
    """判断一个「缺失」链接是否属于**预期缺失的产物**（Batch 338）。

    两类来源，它们在干净 checkout（= CI 环境）里必然不存在，但不代表链接写错：

    1. submodule 内容 —— `research/upstream/*` 由 .gitmodules 声明，
       需要 `git submodule update --init` 才会出现；
    2. gitignore 的截图产物 —— `.gitignore` 排除了手册/验证截图
       （`docs/user-manual/*/screenshots/*.png` 等），只在本地工作区存在。

    这两类若按 error 处理，会让 verify-docs.py **在 CI 上永远失败**。
    故降级为 warning 并单独计数；真正的「链接写错」仍然 return 1。
    """
    if target.startswith(("../", "./")) and "research/upstream/" in target:
        return True
    # 手册截图产物：既可能是 `screenshots/x.png`（相对手册根），
    # 也可能是 `../screenshots/x.png`（相对上级目录）
    stripped = target.lstrip("./")
    if "screenshots/" in stripped and stripped.lower().endswith(
        (".png", ".jpg", ".jpeg", ".webp", ".gif")
    ):
        return True
    return False


def main() -> int:
    missing = []
    expected = []
    checked = 0

    for source in MARKDOWN_FILES:
        # 并行构建会临时增删目录（如 vitepress 的 .temp），读不到就跳过该文件，
        # 不能让整个门禁因瞬时状态崩溃（Batch 338 实测）。
        try:
            text = source.read_text(encoding="utf-8")
        except OSError:
            continue
        for raw_target in LINK_PATTERN.findall(text):
            candidates = candidate_paths(source, raw_target)
            if not candidates:
                continue
            checked += 1
            if not any(candidate.exists() for candidate in candidates):
                if is_expected_missing(raw_target):
                    expected.append((source.relative_to(ROOT), raw_target))
                else:
                    missing.append((source.relative_to(ROOT), raw_target))

    if expected:
        print(
            f"Note: {len(expected)} link(s) point at artifacts absent in a clean "
            "checkout (submodules / gitignored screenshots). Not treated as errors."
        )
        for source, target in expected[:10]:
            print(f"  [expected-missing] {source}: {target}")
        if len(expected) > 10:
            print(f"  ... and {len(expected) - 10} more")
        print()

    if missing:
        print("Missing local documentation links:")
        for source, target in missing:
            print(f"  {source}: {target}")
        return 1

    print(
        f"Documentation link check passed: {len(MARKDOWN_FILES)} Markdown files, "
        f"{checked} local targets, {len(expected)} expected-missing artifact link(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
