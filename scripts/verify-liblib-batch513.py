#!/usr/bin/env python3
"""Verify Batch 513: VR-010 Slice A — pure graph-document codec, strict V1
reader and the §9.2 pure corpus.

Contract: docs/research/components/LibTVGraphDocument.contract.md §4-§10.
The codec lives in src/lib/libtvGraphDocument.ts (pure, no store/DOM);
policies (edge policy, media budget, document limits) are injected so no
product number is invented. The corpus is exposed as
window.__libtv_graph_document_corpus.

Scenes:
- document_corpus: all §9.2 corpus cases report ok (empty/demo round-trip,
  group parent, future version, duplicate/dangling, parent missing/cycle,
  blob non-portable, oversized embedded, edge policy unresolved, limit);
- pipeline_reasons: a direct string-input parse surfaces MALFORMED_JSON.
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
    / "liblib-canvas-batch513-2026-09-14"
    / "runtime-audit.json"
)


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

        corpus = page.evaluate("() => window.__libtv_graph_document_corpus()")
        failed = {k: v for k, v in corpus.items() if not v["ok"]}
        assert not failed, failed
        assert len(corpus) == 10, sorted(corpus)

        malformed = page.evaluate(
            """() => {
              const parse = window.__libtv_graph_document_parse;
              return parse ? parse('{ not json') : null;
            }"""
        )
        assert malformed is not None, "parse helper not exposed"
        assert malformed["reason"] == "MALFORMED_JSON", malformed

        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "PURE_CODEC_RECORDED_PASS",
        "slice": "VR-010 Slice A — pure graph-document codec, strict V1 "
        "reader, runtime-field writer whitelist, §9.2 pure corpus",
        "scenes": {"document_corpus": corpus, "malformed_json": malformed},
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 513 verification passed: §9.2 pure corpus 10/10 green "
        "(round-trip, order/ID retention, runtime stripping, stable "
        "rejection reasons, media diagnostics, injected limits); "
        "recorded in runtime-audit.json."
    )


if __name__ == "__main__":
    main()
