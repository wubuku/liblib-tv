#!/usr/bin/env python3

"""Verify Batch 113 uniform character strip spacing against the 2026-09-05 source rhythm.

★ Batch 827 改写：面板按源站**当前**形态重建后，卡片轨道的**具体**间距被钉住了。
  源站 2026-10-21 活体读数（batch 827 raw，source-827-structure.json）：
  卡片图 244×434 @y=321，相邻 x 差**恒 246**（源站 raw 里 11 张常规卡片的
  x 序列是 1330 / 1576 / 1822 / … 的 246 等差）。
  ⟹ 本门禁从「间距均匀」**加强**为「间距 == 246 且均匀」。
  ★ 旧门禁只判 `len(set(gaps)) == 1` ⟹ 哪怕整体错位 100px 也照样全绿。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch113-2026-09-05"
    / "runtime-audit.json"
)

# ★ Batch 827：源站实测的卡片轨道间距（详见上面的 docstring）
SOURCE_STRIP_PITCH = 246
SOURCE_CARD_SIZE = (244, 434)
SOURCE_CARD_TOP = 321


def attach_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.on(
        "requestfailed",
        lambda request: errors.append(
            f"requestfailed:{request.method}:{request.url}:{request.failure}"
        ),
    )
    return errors


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool) -> None:
        assert ok, f"batch113 check failed: {name}"
        result["checks"].append(name)

    errors = attach_errors(page)
    page.goto(BASE_URL, wait_until="networkidle")
    page.wait_for_timeout(400)

    page.get_by_role("button", name="角色造型室").click()
    modal = page.locator('[data-liblib-overlay="primary:character"]')
    assert modal.is_visible()

    gaps = modal.evaluate("""() => {
      const cards = Array.from(modal_query());
      function modal_query() {
        return document.querySelectorAll("[data-character-strip-card]");
      }
      const xs = Array.from(document.querySelectorAll("[data-character-strip-card]")).map((el) => el.getBoundingClientRect().x);
      const deltas = [];
      for (let i = 1; i < Math.min(xs.length, 6); i++) deltas.push(Math.round(xs[i] - xs[i - 1]));
      return deltas;
    }""")
    card_boxes = modal.evaluate(
        """() => Array.from(document.querySelectorAll("[data-character-strip-card]"))
             .slice(0, 3)
             .map((el) => { const r = el.getBoundingClientRect();
               return { w: Math.round(r.width), h: Math.round(r.height),
                        y: Math.round(r.y) }; });"""
    )
    check("strip:cards-visible", len(gaps) >= 4)
    check("strip:uniform-pitch", len(set(gaps)) == 1)
    # ★ Batch 827 加强：间距的具体值 == 源站实测的 246
    check("strip:pitch-246", gaps and set(gaps) == {SOURCE_STRIP_PITCH})
    # ★ Batch 827 加强：卡片本身 244×434（源站实测值）
    #   ★★ 卡片顶边的 y 是**视口相关**的：900 高视口下
    #   y = (900-760)/2 + 1(border) + 70(header) + 32(toolbar) + 16(mt-4) + 42(viewport) = 231
    #   （1920×1080 下才是 321）⟹ ★★ 绝对 y 读数不能跨视口复用。
    expected_card_top = (900 - 760) // 2 + 1 + 70 + 32 + 16 + 42
    check(
        "strip:card-size",
        all(
            (b["w"], b["h"]) == SOURCE_CARD_SIZE and b["y"] == expected_card_top
            for b in card_boxes
        )
        and bool(card_boxes),
    )

    check("diagnostics:zero", not errors)
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 113,
        "title": "Uniform character strip spacing",
        "evidence": "docs/research/liblib-live-2026-09-05/original-character-library-modal.png",
        "results": [],
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        desktop = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        audit["results"].append(run_desktop(desktop))
        desktop.close()
        browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    checks = audit["results"][0]["checks"]
    print(
        "Batch 113 verification passed: "
        f"{len(checks)} checks, 0 diagnostics. "
        "Uniform strip card pitch recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
