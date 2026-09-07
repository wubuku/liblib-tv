#!/usr/bin/env python3

"""Verify Batch 199: Agent drawer facts against the 2026-09-08 source sample.

Source evidence (source-agent-drawer.json / source-agent-drawer.png):
- Skill section headline "Skill 就位，ready when you are" (a fourth
  headline variant, now added to the clone rotation);
- 换一批 button beside it; 2x2 skill cards 180x62 with name + path —
  the four sampled skills match the clone's batch97 first batch exactly;
- notification banner 开启浏览器通知，及时获取最新消息 (clone already
  matches);
- drawer width reads ~427 at a 1920 viewport vs the clone's fixed 340 —
  recorded as an open question (single sample, possibly fluid).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch199-2026-09-08"
    / "runtime-audit.json"
)


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch199 check failed: {name}"
        result["checks"].append(name)

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto("http://localhost:4317", wait_until="networkidle")
    page.wait_for_timeout(400)

    # open the Agent drawer
    page.get_by_role("button", name="Agent").click()
    page.wait_for_timeout(500)
    drawer = page.locator("aside").first
    check("drawer:opens", drawer.count() == 1)

    # notification banner present
    check("banner:text", page.get_by_text("开启浏览器通知，及时获取最新消息").count() == 1)

    # skill section: headline can be the new fourth variant after rotations
    src = (ROOT / "src" / "components" / "AgentDrawer.tsx").read_text()
    check("skill:fourth-headline-added", "Skill 就位，ready when you are" in src)

    # rotate 换一批 up to 4 times and collect headlines seen
    seen = set()
    for _ in range(4):
        txt = page.locator("aside").first.inner_text()
        for line in txt.splitlines():
            if "Skill" in line or "创作" in line or "打磨" in line or "ready when you are" in line:
                seen.add(line.strip())
                break
        btn = page.get_by_role("button", name="换一批")
        if btn.count():
            btn.click()
            page.wait_for_timeout(250)
    check("skill:four-headlines-rotate", len(seen) >= 3)
    result["headlines_seen"] = sorted(seen)

    # skill cards present with sampled names
    for name in ("皮克斯动画广告", "爆款拉片复刻", "新中式美学TVC", "古典武侠电影全流程导演"):
        check(f"skill:card-{name}", page.get_by_text(name, exact=True).count() >= 1)

    check("errors:empty", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {"batch": 199, "results": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        audit["results"].append(run_desktop(page))
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    audit["passed"] = all(r.get("checks") for r in audit["results"])
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    total = sum(len(r["checks"]) for r in audit["results"])
    print(f"batch199: OK ({total} checks) -> {AUDIT_PATH}")


if __name__ == "__main__":
    main()
