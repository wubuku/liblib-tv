#!/usr/bin/env python3
"""Mechanical checks for a generated LibTV/FrameOS Markdown user manual."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import unquote

IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+[^)]*)?\)")
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
MANIFEST_FILE_RE = re.compile(r"^\s{2}-\s+file:\s*(.+)$")
MANIFEST_FIELD_RE = re.compile(r"^\s{4}([a-z0-9_]+):\s*(.*)$")
TASK_ID_RE = re.compile(r"^\s{2}-\s+id:\s*(.+)$")
TASK_FIELD_RE = re.compile(r"^\s{4}([a-z0-9_]+):\s*(.*)$")
TASK_LIST_ITEM_RE = re.compile(r"^\s{6}-\s+(.+)$")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|Lorem ipsum|Test Client)\b", re.IGNORECASE)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
TASK_STATUSES = {"pending", "in_progress", "documented", "verified", "excluded"}
TASK_FREQUENCIES = {"core", "common", "occasional", "rare"}
TASK_IMPACTS = {"critical", "high", "medium", "low"}
TASK_COVERAGES = {"flagship", "full", "rescue", "concise", "reference"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_manifest_records(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        file_match = MANIFEST_FILE_RE.match(line)
        if file_match:
            if current is not None:
                records.append(current)
            current = {"file": yaml_scalar(file_match.group(1))}
            continue

        field_match = MANIFEST_FIELD_RE.match(line)
        if current is not None and field_match:
            current[field_match.group(1)] = yaml_scalar(field_match.group(2))

    if current is not None:
        records.append(current)
    return records


def parse_task_records(text: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    active_list: str | None = None
    for line in text.splitlines():
        id_match = TASK_ID_RE.match(line)
        if id_match:
            if current is not None:
                records.append(current)
            current = {"id": yaml_scalar(id_match.group(1))}
            active_list = None
            continue

        field_match = TASK_FIELD_RE.match(line)
        if current is not None and field_match:
            key = field_match.group(1)
            value = yaml_scalar(field_match.group(2))
            if value:
                current[key] = value
                active_list = None
            else:
                current[key] = []
                active_list = key
            continue

        list_match = TASK_LIST_ITEM_RE.match(line)
        if current is not None and active_list and list_match:
            values = current.setdefault(active_list, [])
            if isinstance(values, list):
                values.append(yaml_scalar(list_match.group(1)))

    if current is not None:
        records.append(current)
    return records


def audit(root: Path, phase: str) -> list[str]:
    errors: list[str] = []
    required = [
        root / "task-inventory.yml",
        root / "PROGRESS.md",
        root / "AUDIT.md",
        root / "screenshots" / "manifest.yml",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(root)}")

    task_file = root / "task-inventory.yml"
    tasks: list[dict[str, object]] = []
    task_ids: set[str] = set()
    if task_file.is_file():
        tasks = parse_task_records(task_file.read_text(encoding="utf-8"))
        if not tasks:
            errors.append("task-inventory.yml: no task records found")
        for task in tasks:
            task_id = str(task.get("id", "")).strip()
            if not task_id:
                errors.append("task-inventory.yml: task missing id")
                continue
            if task_id in task_ids:
                errors.append(f"task-inventory.yml: duplicate task id: {task_id}")
            task_ids.add(task_id)

            for required_field in (
                "title",
                "role",
                "frequency",
                "impact",
                "coverage",
                "status",
            ):
                if not task.get(required_field):
                    errors.append(
                        f"task-inventory.yml: {task_id}: missing {required_field}"
                    )

            status = str(task.get("status", ""))
            if status and status not in TASK_STATUSES:
                errors.append(f"task-inventory.yml: {task_id}: invalid status {status}")
            for field, allowed_values in (
                ("frequency", TASK_FREQUENCIES),
                ("impact", TASK_IMPACTS),
                ("coverage", TASK_COVERAGES),
            ):
                value = str(task.get(field, ""))
                if value and value not in allowed_values:
                    errors.append(
                        f"task-inventory.yml: {task_id}: invalid {field} {value}"
                    )
            allowed_statuses = (
                {"documented", "verified", "excluded"}
                if phase == "gate-a"
                else {"verified", "excluded"}
            )
            if status in TASK_STATUSES and status not in allowed_statuses:
                errors.append(
                    f"task-inventory.yml: {task_id}: status {status} is not "
                    f"allowed in phase {phase}"
                )

            if status == "excluded":
                if not task.get("exclusion_reason"):
                    errors.append(
                        f"task-inventory.yml: {task_id}: excluded task needs exclusion_reason"
                    )
                continue

            manual_pages = task.get("manual_pages")
            if not isinstance(manual_pages, list) or not manual_pages:
                errors.append(
                    f"task-inventory.yml: {task_id}: documented task needs manual_pages"
                )
                continue
            for raw_page in manual_pages:
                page = (root / str(raw_page)).resolve()
                try:
                    page.relative_to(root.resolve())
                except ValueError:
                    errors.append(
                        f"task-inventory.yml: {task_id}: manual page escapes root: {raw_page}"
                    )
                    continue
                if not page.is_file():
                    errors.append(
                        f"task-inventory.yml: {task_id}: missing manual page: {raw_page}"
                    )

    markdown_files = sorted(
        path for path in root.rglob("*.md")
        if "node_modules" not in path.parts
    )
    if not markdown_files:
        errors.append("no Markdown files found")

    referenced_images: set[Path] = set()
    for markdown in markdown_files:
        text = markdown.read_text(encoding="utf-8")
        relative_markdown = markdown.relative_to(root)
        if PLACEHOLDER_RE.search(text):
            errors.append(f"{relative_markdown}: contains placeholder text")

        previous_level = 0
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = HEADING_RE.match(line)
            if not match:
                continue
            level = len(match.group(1))
            if previous_level and level > previous_level + 1:
                errors.append(
                    f"{relative_markdown}:{line_number}: heading jumps "
                    f"from H{previous_level} to H{level}"
                )
            previous_level = level

        for alt, raw_target in IMAGE_RE.findall(text):
            if not alt.strip():
                errors.append(f"{relative_markdown}: image has empty alt text")
            if raw_target.startswith(("http://", "https://", "data:")):
                errors.append(f"{relative_markdown}: image must use a local relative path: {raw_target}")
                continue
            target = (markdown.parent / raw_target).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{relative_markdown}: image escapes manual root: {raw_target}")
                continue
            if not target.is_file():
                errors.append(f"{relative_markdown}: missing image: {raw_target}")
            else:
                referenced_images.add(target)

        for _, raw_target in LINK_RE.findall(text):
            if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = unquote(raw_target.split("#", 1)[0])
            if not path_part:
                continue
            target = (markdown.parent / path_part).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{relative_markdown}: link escapes manual root: {raw_target}")
                continue
            if not target.exists():
                errors.append(f"{relative_markdown}: broken local link: {raw_target}")

    manifest = root / "screenshots" / "manifest.yml"
    manifest_images: set[Path] = set()
    manifest_task_ids: set[str] = set()
    if manifest.is_file():
        text = manifest.read_text(encoding="utf-8")
        seen_files: set[str] = set()
        records = parse_manifest_records(text)
        if not records:
            errors.append("screenshots/manifest.yml: no screenshot records found")
        for record in records:
            value = record["file"]
            if value in seen_files:
                errors.append(f"screenshots/manifest.yml: duplicate file: {value}")
            seen_files.add(value)

            target = (root / value).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                errors.append(f"screenshots/manifest.yml: file escapes manual root: {value}")
                continue
            try:
                target.relative_to((root / "screenshots").resolve())
            except ValueError:
                errors.append(
                    f"screenshots/manifest.yml: file is outside screenshots directory: {value}"
                )
            manifest_images.add(target)
            if not target.is_file():
                errors.append(f"screenshots/manifest.yml: missing file: {value}")
                continue

            task_id = record.get("task_id", "")
            if task_id and task_id not in task_ids:
                errors.append(
                    f"screenshots/manifest.yml: {value}: unknown task_id {task_id}"
                )
            elif task_id:
                manifest_task_ids.add(task_id)

            for required_field in (
                "task_id",
                "step",
                "route",
                "viewport",
                "locale",
                "captured_at",
                "verified_locator",
                "visible_text",
                "alt",
                "sha256",
            ):
                if not record.get(required_field):
                    errors.append(
                        f"screenshots/manifest.yml: {value}: missing {required_field}"
                    )
            expected_hash = record.get("sha256", "").lower()
            if expected_hash and not SHA256_RE.fullmatch(expected_hash):
                errors.append(f"screenshots/manifest.yml: {value}: invalid sha256")
            elif expected_hash:
                actual_hash = sha256(target)
                if actual_hash != expected_hash:
                    errors.append(
                        f"screenshots/manifest.yml: {value}: sha256 mismatch "
                        f"(expected {expected_hash}, actual {actual_hash})"
                    )

    for image in sorted(referenced_images - manifest_images):
        errors.append(f"image missing from manifest: {image.relative_to(root)}")
    for image in sorted(manifest_images - referenced_images):
        errors.append(f"manifest image is not referenced by Markdown: {image.relative_to(root)}")

    for task in tasks:
        task_id = str(task.get("id", ""))
        if task.get("status") == "excluded":
            continue
        if (
            task.get("frequency") == "core"
            or task.get("coverage") == "flagship"
        ) and task_id not in manifest_task_ids:
            errors.append(
                f"task-inventory.yml: {task_id}: core/flagship task needs a screenshot"
            )

    screenshot_root = root / "screenshots"
    actual_images = (
        {
            path.resolve()
            for path in screenshot_root.rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        }
        if screenshot_root.is_dir()
        else set()
    )
    for image in sorted(actual_images - manifest_images):
        errors.append(f"screenshot file missing from manifest: {image.relative_to(root)}")

    if not errors:
        print(
            f"OK ({phase}): {len(tasks)} tasks, {len(markdown_files)} Markdown "
            f"files, {len(referenced_images)} images"
        )
        for image in sorted(referenced_images):
            print(f"{image.relative_to(root)}  sha256={sha256(image)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manual_root", type=Path)
    parser.add_argument("--phase", choices=("gate-a", "final"), default="final")
    args = parser.parse_args()
    root = args.manual_root.resolve()
    if not root.is_dir():
        print(f"ERROR: manual root does not exist: {root}", file=sys.stderr)
        return 2
    errors = audit(root, args.phase)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
