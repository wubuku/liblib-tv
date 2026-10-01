#!/usr/bin/env python3

"""Verify Batch 351: 错误收集不再把「浏览器中止的请求」当成应用错误。

背景（Batch 350 顺带查清的真因）:
`verify-frameos-batch333.py` 的 `diagnostics:zero` 连续三轮在全量套件里失败、
重试也失败, 但**隔离跑 5+ 次、6 路并发 3 次、重编译扰动 3 次全部通过**。
把诊断写进文件才抓到原文, 抓到的东西全是:

    requestfailed:GET:.../_next/static/chunks/[turbopack]...hmr-client...js:net::ERR_ABORTED
    requestfailed:GET:.../images/frameos/node-vid-cover-2.jpg:net::ERR_ABORTED

`net::ERR_ABORTED` = 浏览器**主动取消**的请求, 不是服务器或应用失败。
根因是门禁分不清「应用抛错了」与「HMR chunk 被重编译作废了」。

修: `is_dev_server_noise()` 识别这类噪音并排除（判据是**中止**而非路径白名单 ——
被中止的请求不携带任何服务端/应用健康信息）。

**本验证器的作用是「反向测试」**: 证明这个过滤**没有把门禁削弱**。
一个只测「噪音被过滤」的测试, 谁都能写；但一个只测噪音被过滤的修复，
很可能顺手把真错误也滤掉了。所以这里逐条断言**真错误必须仍然被抓到**。

断言:
1. 纯函数层面: ERR_ABORTED 判为噪音, 404/500/连接失败判为**真错误**;
2. 运行时: 真实 `console.error` **必须**被抓到;
3. 运行时: 真实未捕获异常(pageerror) **必须**被抓到;
4. 运行时: 真实 404 资源请求**必须**被抓到;
5. 运行时: 真实 `ERR_ABORTED`(AbortController)**必须被过滤**;
6. 运行时: HMR chunk 的 ERR_ABORTED **必须被过滤**;
7. 防假绿自检: 未注入任何东西时, 收集列表**就是空的**（否则第 5/6 条的
   「被过滤」可能只是因为探针根本没触发）;
8. 诊断零错误。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
AUDIT_PATH = (
    ROOT / "docs" / "research" / "liblib-frameos-batch351-2026-10-01" / "runtime-audit.json"
)
sys.path.insert(0, str(ROOT / "scripts"))
from frameos_verify_common import (  # noqa: E402
    attach_errors,
    goto_clean_canvas,
    is_dev_server_noise,
)

# 一个不存在但路径形态与被中止的 HMR chunk 一致的 URL（保证 404 与中止可区分）
FAKE_404 = "/_next/static/chunks/definitely-missing-chunk-abc123._.js"


def run_pure(page: Page) -> dict[str, Any]:
    """纯函数层面: 哪些算噪音, 哪些是真错误。"""
    cases = {
        "hmr_chunk_aborted": (
            "requestfailed:GET:http://localhost:4317/_next/static/chunks/"
            "%5Bturbopack%5D_browser_dev_hmr-client_0zsvagi._.js:net::ERR_ABORTED",
            True,
        ),
        "image_aborted": (
            "requestfailed:GET:http://localhost:4317/images/frameos/node-image-1.png:net::ERR_ABORTED",
            True,
        ),
        "aborted_post": (
            "requestfailed:POST:http://localhost:4317/api/generate:net::ERR_ABORTED",
            True,
        ),
        "not_found": (
            "requestfailed:GET:http://localhost:4317/nope.png:net::ERR_CONNECTION_REFUSED",
            False,
        ),
        "name_not_resolved": (
            "requestfailed:GET:http://nonexistent.invalid/x.js:net::ERR_NAME_NOT_RESOLVED",
            False,
        ),
        "http_404": (
            "console:error:Failed to load resource: the server responded with a status of 404 (Not Found)",
            False,
        ),
        "pageerror": ("pageerror:TypeError: x is not a function", False),
        "console_error": ("console:error:Uncaught RuntimeError: boom", False),
    }
    out = {}
    for name, (text, want_noise) in cases.items():
        out[name] = {"text": text, "is_noise": is_dev_server_noise(text), "want_noise": want_noise}
    return out


def run_desktop(page: Page) -> dict[str, Any]:
    result: dict[str, Any] = {"viewport": "1440x900", "checks": []}

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch351 check failed: {name} {detail}".strip()
        result["checks"].append(name)

    # ── 1 纯函数层面 ──
    pure = run_pure(page)
    result["pure"] = pure
    for name, r in pure.items():
        check(f"pure:{name}", r["is_noise"] == r["want_noise"],
              f"is_noise={r['is_noise']} want={r['want_noise']} :: {r['text'][:80]}")

    # ── 2 防假绿: 干净起点下不该有任何错误 ──
    errors = attach_errors(page)
    goto_clean_canvas(page, BASE_URL)
    page.wait_for_timeout(1200)
    baseline = list(errors)
    result["baseline"] = baseline
    check("anti-false-green:clean-start", baseline == [],
          f"干净起点就已有 {len(baseline)} 条: {baseline[:3]}")

    # ── 3 真 console.error 必须被抓到 ──
    errors.clear()
    page.evaluate("() => console.error('B351_PROBE_CONSOLE_ERROR_MARKER')")
    page.wait_for_timeout(400)
    got_console = [e for e in errors if "B351_PROBE_CONSOLE_ERROR_MARKER" in e]
    result["console_error"] = got_console
    check("catch:console-error", len(got_console) >= 1, f"errors={errors[:3]}")

    # ── 4 真未捕获异常必须被抓到 ──
    errors.clear()
    page.evaluate("() => setTimeout(() => { throw new Error('B351_PROBE_PAGEERROR_MARKER'); }, 0)")
    page.wait_for_timeout(500)
    got_pageerror = [e for e in errors if "B351_PROBE_PAGEERROR_MARKER" in e]
    result["pageerror"] = got_pageerror
    check("catch:pageerror", len(got_pageerror) >= 1, f"errors={errors[:3]}")

    # ── 5 真 404 必须被抓到 ──
    errors.clear()
    page.evaluate("(u) => fetch(u).catch(() => {})", FAKE_404)
    page.wait_for_timeout(900)
    got_404 = [e for e in errors if "404" in e or "definitely-missing-chunk" in e]
    result["http_404"] = got_404
    check("catch:http-404", len(got_404) >= 1, f"errors={errors[:3]}")

    # ── 6 真实 ERR_ABORTED 必须被过滤 ──
    # 防假绿: **另挂一个不经过滤的原始监听器**做对照 —— 同一个事件, 两个收集器,
    # 一个过滤一个不过滤。只有「原始的看到了 ERR_ABORTED、被过滤的那个没看到」
    # 才算真的滤掉了, 否则「没看到」可能只是因为事件压根没发生。
    # (踩过: 先前用页内 console.error 猴补丁去抓原始事件, 但 requestfailed 是
    #  **浏览器**发出的, 不经过页面 console.error, 于是对照恒为空。)
    raw_events: list[str] = []
    page.on(
        "requestfailed",
        lambda r: raw_events.append(f"{r.method}:{r.url}:{r.failure}"),
    )

    errors.clear()
    raw_events.clear()
    page.evaluate(
        """() => {
            const c = new AbortController();
            // 真的发出去再真的中止 —— 让浏览器产生一个真正的 ERR_ABORTED
            fetch('/_next/static/chunks/0zr2_08d4c94._.js', { signal: c.signal })
                .catch(() => {});
            setTimeout(() => c.abort(), 30);
        }"""
    )
    page.wait_for_timeout(900)
    raw_aborts = [e for e in raw_events if "ERR_ABORTED" in e]
    got_aborted = [e for e in errors if "ERR_ABORTED" in e]
    result["abort_ground_truth"] = raw_aborts
    result["aborted_leaked"] = got_aborted
    check("anti-false-green:abort-really-happened", len(raw_aborts) >= 1,
          f"原始监听器都没看到 ERR_ABORTED（{raw_events[:2]}），filter 那条就是空断言")
    check("filter:err-aborted", len(got_aborted) == 0,
          f"中止的请求仍被当成错误: {got_aborted[:2]}")

    check("diagnostics:zero", not errors, f"errors={errors[:3]}")
    result["diagnostics"] = {"console": len(errors), "errors": errors[:5]}
    return result


def main() -> None:
    audit: dict[str, Any] = {
        "batch": 351,
        "defect": "错误收集把 net::ERR_ABORTED(浏览器主动取消)当成应用错误, "
                  "导致 batch333 的 diagnostics:zero 在长跑/并发下反复误报",
        "fix": "is_dev_server_noise() 排除 ERR_ABORTED; 404/500/连接失败/pageerror 照旧计入",
        "role": "反向测试 —— 证明过滤没有削弱门禁",
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            audit["desktop"] = run_desktop(page)
        finally:
            browser.close()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(
        f"Batch 351 verification passed: {len(audit['desktop']['checks'])} checks, "
        f"{audit['desktop']['diagnostics']['console']} diagnostics. "
        "ERR_ABORTED (browser-cancelled requests) is no longer counted as an app error, "
        "while real console.error, uncaught exceptions and 404s are still caught — "
        "so the diagnostics:zero gate is sharper, not weaker."
    )


if __name__ == "__main__":
    main()
