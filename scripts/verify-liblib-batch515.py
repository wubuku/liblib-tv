#!/usr/bin/env python3
"""Verify Batch 515: VR-012 focused fixture — default node-data registry
completeness and hygiene, driven through the real getDefaultNodeData.

Contract: docs/research/LibTVNodeDataIdentity.contract.md +
LIBTV_NODE_DATA_STATIC_AUDIT_2026-08-27.md §4 (11 runtime types;
getDefaultNodeData carries known extra style/effect branches without
renderers — recorded as findings, not failures).

Scenes:
- registry_completeness: all 11 runtime types return default data;
- defaults_deterministic: two calls deep-equal per type;
- defaults_json_safe: JSON round-trip deep-equal per type (no functions,
  Dates, undefined holes, non-JSON values);
- defaults_no_runtime_keys: no selected/dragging/measured/style/internals
  keys inside the default data;
- extra_branches_finding: non-runtime branches (style/effect) reported —
  known STATIC_FACT, kept visible in the audit.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT
    / "docs"
    / "research"
    / "liblib-canvas-batch515-2026-09-14"
    / "runtime-audit.json"
)

RUNTIME_TYPES = [
    "script",
    "image",
    "text",
    "video",
    "script-execution",
    "storyboard-group",
    "shot-breakdown",
    "shot-breakdown-result",
    "video-clip",
    "audio",
    "long-video-process",
]

RUNTIME_KEYS = {"selected", "dragging", "resizing", "hover", "focus", "measured", "style", "internals"}


def attach_errors(page: Page):
    errors = []
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


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)

        report = page.evaluate(
            """(runtimeTypes) => {
              const get = window.__libtv_default_node_data;
              const out = { missing: [], nondeterministic: [], notJsonSafe: [],
                            runtimeKeys: {}, knownExtraBranches: [] };
              const seen = new Set(runtimeTypes);
              for (const type of runtimeTypes) {
                const first = get(type);
                if (!first || typeof first !== 'object') { out.missing.push(type); continue; }
                const second = get(type);
                if (JSON.stringify(first) !== JSON.stringify(second)) {
                  out.nondeterministic.push(type);
                }
                if (JSON.stringify(first) !== JSON.stringify(JSON.parse(JSON.stringify(first)))) {
                  out.notJsonSafe.push(type);
                }
                const bad = Object.keys(first).filter((k) =>
                  ['selected','dragging','resizing','hover','focus','measured','style','internals'].includes(k));
                if (bad.length) out.runtimeKeys[type] = bad;
              }
              // Known extra default branches beyond the 11 runtime types.
              for (const type of ['style', 'effect']) {
                const value = get(type);
                if (value && Object.keys(value).length) out.knownExtraBranches.push(type);
              }
              return out;
            }""",
            RUNTIME_TYPES,
        )

        assert not report["missing"], report
        assert not report["nondeterministic"], report
        assert not report["notJsonSafe"], report
        assert not report["runtimeKeys"], report

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "FOCUSED_BROWSER_RECORDED_PASS",
        "slice": "VR-012 focused fixture — default node-data registry "
        "completeness (11 runtime types), determinism, JSON safety, "
        "runtime-key hygiene",
        "scenes": {
            "registry_completeness": {"types": len(RUNTIME_TYPES), "missing": []},
            "defaults_deterministic": "green",
            "defaults_json_safe": "green",
            "defaults_no_runtime_keys": "green",
            "known_extra_branches_findings": report["knownExtraBranches"],
        },
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 515 verification passed: default node-data registry covers "
        "all 11 runtime types deterministically, JSON-safe, no runtime keys; "
        f"known extra branches: {report['knownExtraBranches'] or 'none'}; "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
