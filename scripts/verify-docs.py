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


def main() -> int:
    missing = []
    checked = 0

    for source in MARKDOWN_FILES:
        text = source.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(text):
            candidates = candidate_paths(source, raw_target)
            if not candidates:
                continue
            checked += 1
            if not any(candidate.exists() for candidate in candidates):
                missing.append((source.relative_to(ROOT), raw_target))

    if missing:
        print("Missing local documentation links:")
        for source, target in missing:
            print(f"  {source}: {target}")
        return 1

    print(
        f"Documentation link check passed: {len(MARKDOWN_FILES)} Markdown files, "
        f"{checked} local targets."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
