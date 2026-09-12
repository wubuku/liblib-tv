#!/usr/bin/env python3
"""Verify Batch 445: VR-022 Slice A — pure profile/session/history model.

Contract: docs/research/LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT.md
§5 named editor profiles + §5.2 invalid combinations, §7 session state
machine, §9 semantic normalization/no-op, §10.7/§10.2 history budget and
gesture coalescing. Slice A is pure: no React/store/runtime changes.

Implementation: src/lib/libtvEditorSession.ts exposed read-only via
window diagnostics.

Scenes:
- profile_registry: ten declared profiles, each passing its invariants;
- profile_invariants: mutating the evidence-gated/multiline/live profiles
  surfaces the §5.2 violations;
- session_state_machine: open -> edit(dirty) -> commit-sync -> accepted;
  cancel path; edit back to baseline is a no-op; commit on clean and
  invalid transitions are stably rejected;
- normalization_noop: INLINE_SCALAR trims (whitespace-only edit is a
  no-op), INLINE_MULTILINE preserves meaningful whitespace;
- history_budget_coalescing: same-kind entries inside the window merge,
  the budget caps the length.
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
    / "liblib-canvas-batch445-2026-09-13"
    / "runtime-audit.json"
)
SCREENSHOT_PATH = (
    ROOT
    / "docs"
    / "design-references"
    / "liblib-clone-batch445-editor-session-929-2026-09-13.png"
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


def assert_no_overflow(page: Page):
    assert page.evaluate(
        "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )
    assert page.evaluate(
        "() => document.body.scrollWidth <= document.body.clientWidth"
    )


def run_profile_registry(page: Page):
    result = page.evaluate(
        """() => {
          const profiles = window.__libtv_editor_profiles;
          const violationsOf = window.__libtv_editor_profile_violations;
          const ids = Object.keys(profiles);
          const violations = ids
            .map((id) => ({ id, v: violationsOf(profiles[id]) }))
            .filter((entry) => entry.v.length > 0);
          return { ids, violations };
        }"""
    )
    assert len(result["ids"]) == 10, result
    assert not result["violations"], result
    return {"profileCount": len(result["ids"]), "violations": []}


def run_profile_invariants(page: Page):
    result = page.evaluate(
        """() => {
          const violationsOf = window.__libtv_editor_profile_violations;
          const gated = {
            ...window.__libtv_editor_profiles.EMPTY_EVIDENCE_GATED,
            commitTriggers: ['explicit-submit'],
          };
          const multiline = {
            ...window.__libtv_editor_profiles.INLINE_MULTILINE,
            commitTriggers: ['enter'],
          };
          const live = {
            ...window.__libtv_editor_profiles.LIVE_COALESCED_INSPECTOR,
            historyOwner: 'custom',
          };
          return {
            gated: violationsOf(gated),
            multiline: violationsOf(multiline),
            live: violationsOf(live),
          };
        }"""
    )
    assert len(result["gated"]) == 1, result
    assert len(result["multiline"]) == 1, result
    assert len(result["live"]) == 1, result
    return result


def run_session_state_machine(page: Page):
    result = page.evaluate(
        """() => {
          const reduce = window.__libtv_editor_session_reduce;
          const closed = {
            state: 'CLOSED', profileId: 'INLINE_SCALAR',
            baseline: '', draft: '', dirty: false,
          };
          const opened = reduce(closed, {
            type: 'open', profileId: 'INLINE_SCALAR', baseline: '标题',
          });
          const dirty = reduce(opened.snapshot, {
            type: 'edit', value: '新标题',
          });
          const committing = reduce(dirty.snapshot, { type: 'commit-sync' });
          const accepted = reduce(committing.snapshot, {
            type: 'commit-accepted',
          });
          const cancelled = reduce(opened.snapshot, { type: 'cancel' });
          const disposed = reduce(cancelled.snapshot, { type: 'disposed' });

          const noOpEdit = reduce(opened.snapshot, { type: 'edit', value: '标题' });
          const cleanCommit = reduce(opened.snapshot, { type: 'commit-sync' });
          const doubleOpen = reduce(opened.snapshot, {
            type: 'open', profileId: 'INLINE_SCALAR', baseline: 'x',
          });
          const invalidated = reduce(dirty.snapshot, { type: 'invalidate' });
          const staleCommit = reduce(invalidated.snapshot, {
            type: 'commit-sync',
          });

          return {
            openedState: opened.snapshot.state,
            dirtyState: dirty.snapshot.state,
            dirtyFlag: dirty.snapshot.dirty,
            committingState: committing.snapshot.state,
            acceptedState: accepted.snapshot.state,
            cancelledState: cancelled.snapshot.state,
            disposedState: disposed.snapshot.state,
            noOpEditOutcome: noOpEdit.outcome,
            noOpEditState: noOpEdit.snapshot.state,
            cleanCommit: cleanCommit,
            doubleOpen: doubleOpen,
            invalidatedState: invalidated.snapshot.state,
            staleCommit: staleCommit,
          };
        }"""
    )
    assert result["openedState"] == "OPEN_CLEAN"
    assert result["dirtyState"] == "OPEN_DIRTY" and result["dirtyFlag"]
    assert result["committingState"] == "COMMITTING_SYNC"
    assert result["acceptedState"] == "ACCEPTED"
    assert result["cancelledState"] == "DISPOSING"
    assert result["disposedState"] == "CLOSED"
    assert result["noOpEditOutcome"] == "handled-noop"
    assert result["noOpEditState"] == "OPEN_CLEAN"
    assert result["cleanCommit"]["outcome"] == "rejected-transition"
    assert result["doubleOpen"]["outcome"] == "rejected-transition"
    assert result["invalidatedState"] == "INVALIDATED"
    assert result["staleCommit"]["outcome"] == "rejected-transition"
    return result


def run_normalization_noop(page: Page):
    result = page.evaluate(
        """() => {
          const profiles = window.__libtv_editor_profiles;
          const normalize = window.__libtv_editor_normalize;
          return {
            scalarTrim: normalize(profiles.INLINE_SCALAR, '  标题  '),
            multilineKept: normalize(profiles.INLINE_MULTILINE, '  保留  '),
          };
        }"""
    )
    assert result["scalarTrim"] == "标题", result
    assert result["multilineKept"] == "  保留  ", result
    return result


def run_history_budget_coalescing(page: Page):
    result = page.evaluate(
        """() => {
          const mk = window.__libtv_editor_local_history_entry;
          const push = window.__libtv_editor_local_history_push;
          // coalescing: same kind within the window merges into one entry
          let merged = [];
          merged = push(merged, mk('title-edit', 0, 'a'));
          merged = push(merged, mk('title-edit', 200, 'ab'));
          merged = push(merged, mk('title-edit', 1200, 'abc'));
          // budget: 62 pushes cap the retained history at 50 entries
          let budgeted = [];
          for (let i = 0; i < 62; i += 1) {
            budgeted = push(budgeted, mk('body-edit', 2000 + i * 1000, 'x' + i));
          }
          return {
            coalescedLength: merged.length,
            coalescedLast: merged[1]?.value ?? null,
            budgetedLength: budgeted.length,
          };
        }"""
    )
    # two same-kind entries inside the 600ms window merge into one;
    # the third (past the window) starts a new entry; the 50-entry
    # budget caps the 62 pushed entries.
    assert result["coalescedLength"] == 2, result
    assert result["coalescedLast"] == "abc", result
    assert result["budgetedLength"] == 50, result
    return result


def main():
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 929, "height": 874}, device_scale_factor=1
        )
        errors.extend(attach_errors(page))
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(450)

        registry = run_profile_registry(page)
        invariants = run_profile_invariants(page)
        machine = run_session_state_machine(page)
        normalization = run_normalization_noop(page)
        history = run_history_budget_coalescing(page)

        page.screenshot(path=str(SCREENSHOT_PATH))
        assert_no_overflow(page)
        browser.close()
    assert not errors, errors

    audit = {
        "url": URL,
        "status": "SCRIPT_RECORDED_PASS",
        "slice": "VR-022 Slice A — pure editor profile/session/history model",
        "profile_registry": registry,
        "profile_invariants": invariants,
        "session_state_machine": machine,
        "normalization_noop": normalization,
        "history_budget_coalescing": history,
        "errors": {"console": [], "page": [], "request": []},
    }
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(
        "Batch 445 Playwright verification passed: ten-profile registry with "
        "invariant checks, session state machine transitions and stable "
        "rejections, semantic normalization no-op, local-history budget and "
        "gesture coalescing, diagnostics clean."
    )


if __name__ == "__main__":
    main()
