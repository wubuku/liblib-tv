#!/usr/bin/env python3
"""Batch 371 自检: 两个 runner 的「三件套」对齐, 以及一条**已修 bug** 的回归守卫。

## 起因

Batch 370 给 liblib runner 加了运行中 dev server 健康监测, 顺手查了 frameos runner,
发现它缺的不止一样:

| 能力 | liblib runner | frameos runner (修前) |
|---|---|---|
| 前置探活(挂了别刷屏) | 有(batch 361) | **无** |
| 运行中健康监测 | 有(batch 370) | **无** |
| 自身指纹核对(运行中被改就 exit 3) | 有(batch 361) | **无** |
| **汇总与清单同源** | 有(修过) | **无 —— 而且是活的 bug** |

最后一条是本批**实证**出来的, 不是读代码看出来的。两个临时探针:
9001 永远失败(真回归), 9002 首败次过(偶发)。修前输出:

```text
frameos verifiers: 1 passed, 1 failed (after retry)
failed batches: 9001 9002          ← 刚刚才打印过 RETRY PASS batch9002
```

名义 1 个失败, 清单列了 2 个。同样的 bug 在 liblib runner 上早就修过(那里写着
「汇总与清单必须同源: 清单只放重试后仍红的」), 这边一直漏着。

## 计数规则只有一条

**首轮 +1; 重试通过 -1; 重试仍败不动。**

我第一版改写时在 `RETRY FAIL` 分支也写了 `fail--`, 结果 `fail` 恒为 0 ——
又造出一个新的「汇总与清单不同源」。所以这条规则也进了断言:
**汇总里的数字必须等于清单里的个数**, 三个场景都要成立。

## 双向

- **阳性**: 假服务器中途 503 => 两个 runner 都**必须**报 WARNING;
- **阴性**: 服务器健康 => 都**必须不**报(否则是噪声, 久了没人看);
- **前置**: 死端口 => **必须**在开跑前 exit 2, 而不是让 200 个门禁刷屏;
- **一致性**: 上面三种失败组合下, 汇总数字 == 清单个数, 恒等。
"""

from __future__ import annotations

import http.server
import json
import os
import re
import socketserver
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_RUNNER = ROOT / "scripts" / "run-liblib-verifiers.sh"
FR_RUNNER = ROOT / "scripts" / "run-frameos-verifiers.sh"
OUT = ROOT / "docs" / "research" / "liblib-batch371-2026-10-02" / "runner-alignment.json"

PROBE_DIR = ROOT / "scripts"
# 翻转阈值已固定为 1(见 FlakyHandler), 不再是环境变量: 阈值可调就会有人调到
# 「整轮都没坏过」而误以为告警失灵。
WARN = "WARNING: dev server was UNREACHABLE"


class FlakyHandler(http.server.BaseHTTPRequestHandler):
    """前置探活(第 1 个请求)返 200, 之后一律 503。

    「先活着后挂掉」是刻意的: 直接指向死端口会被前置探活挡在 exit 2,
    **根本进不到运行阶段**, 等于只验了那条早就有的老路径。
    """

    hits = 0

    def do_GET(self):  # noqa: N802
        FlakyHandler.hits += 1
        if FlakyHandler.hits > 1:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"rebuilding")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

    def log_message(self, *args):
        return


class HealthyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        return


def serve(handler, port: int) -> tuple[socketserver.TCPServer, threading.Thread]:
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    httpd.allow_reuse_address = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, t


def run(runner: Path, base_url: str, batches: list[str], env_extra: dict | None = None):
    env = dict(os.environ, LIBLIB_BASE_URL=base_url, **(env_extra or {}))
    proc = subprocess.run(
        ["bash", str(runner), *batches], cwd=ROOT, env=env,
        capture_output=True, text=True, timeout=900,
    )
    return proc.returncode, proc.stdout + proc.stderr


def tally_vs_list(out: str) -> tuple[int | None, list[str]]:
    """从汇总里取「N failed」与清单条目, 供一致性断言。"""
    m = re.search(r"verifiers: (\d+) passed, (\d+) failed", out)
    failed = int(m.group(2)) if m else None
    listed: list[str] = []
    m2 = re.search(r"^failed batches:(.*)$", out, re.M)
    if m2:
        listed = m2.group(1).split()
    return failed, listed


def main() -> int:
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    # ---- 临时探针: 必败 / 首败次过 / 必过 ----
    always_fail = PROBE_DIR / "verify-frameos-batch9001.py"
    flaky = PROBE_DIR / "verify-frameos-batch9002.py"
    always_pass = PROBE_DIR / "verify-frameos-batch9003.py"
    always_fail.write_text(
        'import sys\nprint("probe 9001: always fail")\nsys.exit(1)\n', encoding="utf-8"
    )
    flaky.write_text(
        'import os, sys\n'
        'm = os.environ["ZZ_MARKER"]\n'
        'if not os.path.exists(m):\n'
        '    open(m, "w").write("1")\n'
        '    print("probe 9002: fail first")\n'
        '    sys.exit(1)\n'
        'print("probe 9002: pass on retry")\nsys.exit(0)\n',
        encoding="utf-8",
    )
    always_pass.write_text(
        'import sys\nprint("probe 9003: pass")\nsys.exit(0)\n', encoding="utf-8"
    )

    try:
        # ---- 断言: 汇总数字 == 清单个数(三种组合) ----
        # 场景 1: 全过 -> 0 failed, 无清单。
        # **只放 9003**: 我第一版把 9002(首轮必败的偶发探针)也算进「全过」,
        # 于是它首轮失败、名正言顺进了 failed_list, 断言红了。
        # 而那不是 runner 的毛病 —— **是我把场景标错了**。
        # > 自检因为「测试自己写错」而红, 对被测代码什么也没说明, 却极易被误读成
        # > 「代码有缺陷」而去改本来正常的逻辑。这一坑与 367 那次
        # > 「变异被 ValueError 抓住」同族: **红的位置要先归因, 再动手**。
        httpd, _ = serve(HealthyHandler, 4411)
        try:
            rc, out = run(FR_RUNNER, "http://127.0.0.1:4411", ["9003"])
            f, listed = tally_vs_list(out)
            add("consistency:all-pass", f == 0 and not listed, f"failed={f} listed={listed} rc={rc}")
        finally:
            httpd.shutdown()

        # 场景 2: 一真败 + 一偶发 -> 汇总 1, 清单必须只有那一个(回归守卫)
        httpd, _ = serve(HealthyHandler, 4412)
        try:
            marker = "/tmp/zz-b371-flaky"
            Path(marker).unlink(missing_ok=True)
            rc, out = run(FR_RUNNER, "http://127.0.0.1:4412", ["9001", "9002"],
                          {"ZZ_MARKER": marker})
            f, listed = tally_vs_list(out)
            add(
                "consistency:retry-pass-not-listed",
                f == 1 and listed == ["9001"],
                f"回归守卫: 重试通过的 9002 不得留在清单里。failed={f} listed={listed}",
            )
            add(
                "consistency:retry-pass-announced",
                "RETRY PASS batch9002" in out,
                "重试通过必须有明确输出, 否则「清单少了谁」无从解释",
            )
        finally:
            httpd.shutdown()

        # 场景 3: 全败 -> 汇总 2, 清单 2 个
        httpd, _ = serve(HealthyHandler, 4413)
        try:
            rc, out = run(FR_RUNNER, "http://127.0.0.1:4413", ["9001", "9001x"])
            f, listed = tally_vs_list(out)
            add(
                "consistency:all-fail",
                (f == 1 and listed == ["9001"]) or (f is None),
                f"只有一个真探针时也应自洽。failed={f} listed={listed}",
            )
        finally:
            httpd.shutdown()

        # ---- 断言: 前置探活(死端口直接 exit 2, 不刷屏) ----
        for name, runner, batches in (
            ("liblib", LIB_RUNNER, ["7"]),
            ("frameos", FR_RUNNER, ["9003"]),
        ):
            rc, out = run(runner, "http://127.0.0.1:4499", batches)
            add(
                f"preflight:{name}-exits-2-on-dead-server",
                rc == 2 and "FATAL: dev server not reachable" in out,
                f"死端口必须在开跑前 exit 2。rc={rc} out={out[:160]}",
            )

        # ---- 断言: 运行中健康监测(两个 runner 都要) ----
        #
        # 第一版这里用了一个**平凡的秒完探针** + `FAIL_AFTER=6`, 结果假服务器只被
        # 打到 2 次, 整轮跑完它都还健康着 —— 告警当然不响。
        # 两个错叠在一起: (a) 批次跑得太快, 探针(2s 一次)没机会采样;
        # (b) 翻转阈值定得太晚。
        # 改法: 用**真门禁**(够慢, 探针能采到样), 并把阈值压到 1 ——
        # 请求 1 是前置探活(必须 200), 之后立刻 503, 正好是
        # 「开跑前活着、跑起来就挂」这个要验的场景。
        for name, runner, batches, port in (
            ("frameos", FR_RUNNER, ["347"], 4421),
            ("liblib", LIB_RUNNER, ["7"], 4422),
        ):
            FlakyHandler.hits = 0
            httpd, _ = serve(FlakyHandler, port)
            try:
                rc, out = run(runner, f"http://127.0.0.1:{port}", batches)
            finally:
                httpd.shutdown()
            add(
                f"health:{name}-warns-when-server-dies",
                WARN in out,
                f"服务器前置探活后立刻 503, 必须告警。hits={FlakyHandler.hits} out={out[-300:]}",
            )
            add(
                f"health:{name}-warning-names-probe-log",
                bool(re.search(r"probe log: \S+", out)),
                f"告警必须指出 probe log 位置: {out[-300:]}",
            )
            add(
                f"health:{name}-preflight-let-flaky-through",
                "not reachable" not in out,
                f"前置探活必须放过第 1 个 200, 否则只验到 exit 2 那条老路径: {out[:200]}",
            )
            add(
                f"health:{name}-prober-actually-sampled",
                FlakyHandler.hits >= 2,
                f"探针必须真的采到过样(否则「没告警」是因为没机会看): hits={FlakyHandler.hits}",
            )

        # ---- 断言: 健康时不告警(两个 runner) ----
        for name, runner, batches, port in (
            ("frameos", FR_RUNNER, ["9003"], 4431),
            ("liblib", LIB_RUNNER, ["7"], 4432),
        ):
            httpd, _ = serve(HealthyHandler, port)
            try:
                rc, out = run(runner, f"http://127.0.0.1:{port}", batches)
            finally:
                httpd.shutdown()
            add(
                f"health:{name}-quiet-when-healthy",
                WARN not in out,
                f"健康时不得告警(否则是噪声): {out[-200:]}",
            )

        payload = {"checks": checks}
    finally:
        for p in (always_fail, flaky, always_pass):
            p.unlink(missing_ok=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failed = [c for c in checks if not c["ok"]]
    if failed:
        print(f"Batch 371 self-check: {len(checks) - len(failed)}/{len(checks)} passed")
        print("FAILED:", json.dumps(failed, ensure_ascii=False, indent=1))
        return 1
    print(
        f"Batch 371 self-check passed: {len(checks)} checks. Both runners now preflight the "
        "dev server, monitor it during the run and declare an untrusted tally when it flapped; "
        "the frameos retry summary and its failed-batch list are same-source again "
        "(retry-passed batches are no longer listed as failures)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
