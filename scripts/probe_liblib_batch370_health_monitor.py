#!/usr/bin/env python3
"""Batch 370 自检: 证明 runner 的 dev server 健康监测**两个方向都有效**。

## 为什么需要它

`run-liblib-verifiers.sh` 新增了「运行中探活, 抖过就声明结果不可信」。
但这种监测最常见的失败是**恒绿** —— 探针写错了地方、或者条件永远不成立,
于是「跑歪了会告警」这句话是**空断言**, 而门禁全绿恰恰证明不了这一点。
所以必须有阳性对照: **真的让服务器挂掉, 断言 runner 一定报**。

## 怎么做出「会挂的服务器」而不打扰别人

真实 dev server 不能碰 —— 4317 上还有并行 session 在用。所以起一个
**假服务器**在临时端口上:

- 前 N 个请求正常返回 200(骗过 runner 的**前置探活**);
- 之后开始返回 503 —— 运行中健康监测必须抓到。

这比「直接指向死端口」更严: 死端口会被前置探活挡住(exit 2), 压根进不到
运行阶段, 验证不到新加的那段逻辑。

## 双向

- **阳性**: 服务器中途挂 => 汇总**必须**出现 WARNING 且指明 probe log;
- **阴性**: 服务器一直健康 => 汇总**必须不**出现 WARNING(否则是噪声, 没人看)。
"""

from __future__ import annotations

import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run-liblib-verifiers.sh"
OUT = ROOT / "docs" / "research" / "liblib-batch370-2026-10-02" / "health-monitor-selfcheck.json"

FAIL_AFTER = int(os.environ.get("ZZ_FAIL_AFTER", "6"))
BATCHES = ["7", "8"]
PORT = 4399


class FlakyHandler(http.server.BaseHTTPRequestHandler):
    hits = 0

    def do_GET(self):  # noqa: N802
        FlakyHandler.hits += 1
        if FlakyHandler.hits > FAIL_AFTER:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"rebuilding")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

    def log_message(self, *args):  # 静音
        return


def run_runner(base_url: str) -> str:
    env = dict(os.environ, LIBLIB_BASE_URL=base_url)
    proc = subprocess.run(
        ["bash", str(RUNNER), "-j", "1", *BATCHES],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=600,
    )
    return proc.stdout + proc.stderr


def main() -> int:
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    # ---- 阳性: 中途挂掉 ----
    FlakyHandler.hits = 0
    with socketserver.TCPServer(("127.0.0.1", PORT), FlakyHandler) as httpd:
        httpd.allow_reuse_address = True
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        time.sleep(0.3)
        out_fail = run_runner(f"http://127.0.0.1:{PORT}")
    has_warning = "WARNING: dev server was UNREACHABLE" in out_fail
    add(
        "health-monitor:warns-when-server-dies",
        has_warning,
        f"服务器中途 503, 汇总必须告警。命中={has_warning}",
    )
    add(
        "health-monitor:warning-names-probe-log",
        bool(re.search(r"probe log: \S+", out_fail)),
        f"告警必须指出 probe log 位置, 否则无法复核: {out_fail[-400:]}",
    )
    add(
        "health-monitor:tally-still-printed",
        "liblib verifiers:" in out_fail,
        "即使抖了也仍要报数字 —— 只是必须同时声明不可信",
    )
    add(
        "health-monitor:preflight-still-passes-first",
        "not reachable" not in out_fail,
        f"前置探活必须放过前几个 200(否则只验到 exit 2 那条老路径): {out_fail[:300]}",
    )

    # ---- 阴性: 一直健康 ----
    class HealthyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *args):
            return

    with socketserver.TCPServer(("127.0.0.1", PORT + 1), HealthyHandler) as httpd:
        httpd.allow_reuse_address = True
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        time.sleep(0.3)
        out_ok = run_runner(f"http://127.0.0.1:{PORT + 1}")
    add(
        "health-monitor:quiet-when-healthy",
        "WARNING: dev server was UNREACHABLE" not in out_ok,
        f"服务器健康时不得告警(否则是噪声, 久了没人看): {out_ok[-300:]}",
    )

    payload = {
        "failAfterRequests": FAIL_AFTER,
        "checks": checks,
        "outputWhenServerDies": out_fail[-1500:],
        "outputWhenHealthy": out_ok[-600:],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failed = [c for c in checks if not c["ok"]]
    if failed:
        print(f"Batch 370 self-check: {len(checks) - len(failed)}/{len(checks)} passed")
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
        print("---- 服务器挂掉时的输出尾部 ----")
        print(out_fail[-1500:])
        return 1
    print(
        f"Batch 370 self-check passed: {len(checks)} checks. The runner's dev-server "
        "health monitor provably fires when the server dies mid-run and stays silent "
        "when it is healthy, and the preflight still lets a flaky-but-alive server "
        "through so the run-time path is what is actually exercised."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
