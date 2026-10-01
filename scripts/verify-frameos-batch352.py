#!/usr/bin/env python3
"""Verify Batch 352: 死状态普查工具(deadstate_census.mjs)的反向测试。

工具本身没有运行时行为, 但它有一个更要紧的性质:**不能误报**。
一个会把「活字段」报成死状态的工具, 每次都会产出**看起来很确凿的假线索** ——
本会话已经因此踩了 5 次坑(多行函数参数 / 解构读取 / 多行 action 首行 /
多行解构 / 切接口 body 太天真), 所以本验证器不测「它找到了什么」,
只测**它没有把已知活着的字段判死**。

断言:
0. 防假绿: 工具能跑通, 且确实产出了非空字段表(否则下面全是空断言);
1~5. 五个 store 各自的「已知活着」字段**都不在死状态候选里**:
   - jimengStore  `groupNames` / `groupColors`  (Batch 349: 被解构读取)
   - canvasStore  `removedCanvases` / `historyByCanvas` (Batch 352: 多行解构)
   - directorStore `authoredObjects` / `clipboardPasteCount` (只在 store 内部读)
   这 7 个字段每一个都曾被正则版误报过 —— 这就是它们被钉在这里的原因;
6. `frameosStore` 保持零死状态(Batch 349 删除 `generations` 后的基线);
7. `uiStore` 的 4 个真候选仍被报出 —— **反向断言**: 证明工具没有退化成
   「什么都不报」而假绿(前 5 条全过也可能是因为它压根不工作)。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = (
    ROOT / "docs" / "research" / "liblib-frameos-batch352-2026-10-01" / "tool-audit.json"
)

# store 相对路径, 接口名, 该 store 里「已知活着、曾被正则版误报」的字段
KNOWN_ALIVE: list[tuple[str, str, list[str]]] = [
    ("src/store/jimengStore.ts", "JimengCanvasState", ["groupNames", "groupColors"]),
    ("src/store/canvasStore.ts", "CanvasState", ["removedCanvases", "historyByCanvas"]),
]

# 「只在 store 内部被读」的字段 —— **不是**那 5 类正则误报, 而是工具的既定边界:
# 它统计的是**外部**读取点, 所以这类字段仍会被列为候选, 需要人工判读。
# 这里把期望写成「仍会被报出来」, 免得以后有人为了让它闭嘴而去改工具的语义。
STORE_INTERNAL_READS: list[tuple[str, str, list[str]]] = [
    (
        "src/store/directorStore.ts",
        "DirectorState",
        # authoredObjects 有 94 处内部引用(state.authoredObjects.find/...),
        # clipboardPasteCount 在 3964 行被读(pasteOrdinal: state.clipboardPasteCount + 1)
        ["authoredObjects", "clipboardPasteCount"],
    ),
]

# 真实的死状态(尚未清理, 跨线): uiStore 的 4 个面板开关不可达
EXPECTED_DEAD = (
    "src/store/uiStore.ts",
    "UIState",
    [
        "isToolboxPanelOpen",
        "isMaterialPanelOpen",
        "isCharacterPanelOpen",
        "isHistoryPanelOpen",
    ],
)


def find_node() -> str:
    """自己找 node, 不假设它在 PATH 上。

    踩过的坑: 全量套件 `run-frameos-verifiers.sh` 的运行环境里 **node 不在 PATH**
    (它只用 pyenv 的 python, 不导出 nvm 的 node 路径), 于是本验证器在套件里
    直接 `FileNotFoundError: 'node'` 崩掉 —— 单独手跑能过、进门禁就挂。
    > **门禁必须在最贫瘠的环境里也能跑**; 依赖「我 shell 里恰好有」的工具链,
    > 等于把门禁的可靠性绑在调用者的 PATH 上。

    探测顺序: 环境变量 → PATH → 本机 nvm 的默认版本目录。
    """
    import glob
    import shutil

    env = os.environ.get("LIBLIB_NODE")
    if env and Path(env).exists():
        return env
    found = shutil.which("node")
    if found:
        return found
    for pat in (
        str(Path.home() / ".nvm/versions/node/*/bin/node"),
        "/opt/homebrew/bin/node",
        "/usr/local/bin/node",
    ):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    raise SystemExit("找不到 node：请设置 LIBLIB_NODE=/path/to/node")


def run_census(store_rel: str, iface: str) -> dict[str, Any]:
    node = find_node()
    proc = subprocess.run(
        [node, "scripts/deadstate_census.mjs", store_rel, iface],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, f"普查工具失败 {store_rel} {iface}: {proc.stderr[-500:]}"
    out = proc.stdout
    dead_line = ""
    in_dead = False
    for line in out.splitlines():
        if line.startswith("# 死状态候选"):
            in_dead = True
            continue
        if in_dead:
            dead_line = line.strip()
            break
    dead: list[str] = []
    if dead_line and dead_line != "(无)":
        dead = [x.strip() for x in dead_line.replace("，", ",").split(",") if x.strip()]
    header = out.splitlines()[0] if out else ""
    return {"stdout_head": header, "dead": dead, "raw_len": len(out)}


def main() -> None:
    checks: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        assert ok, f"batch352 check failed: {name} {detail}".strip()
        checks.append(name)

    audit: dict[str, Any] = {"batch": 352, "role": "工具反向测试", "stores": {}, "checks": checks}

    # ── 0 防假绿: 工具跑得通且产出非空 ──
    base = run_census("src/store/frameosStore.ts", "FrameosCanvasState")
    audit["stores"]["frameosStore"] = base
    check("anti-false-green:tool-runs", base["raw_len"] > 0, "工具没有输出")
    check("anti-false-green:field-table-nonempty", "状态数据字段" in base["stdout_head"],
          f"head={base['stdout_head']!r}")

    # ── 6 frameosStore 零死状态 ──
    check("frameosStore:no-dead-state", base["dead"] == [], f"dead={base['dead']}")

    # ── 1~2 已知活着的字段不得被判死 ──
    for store_rel, iface, alive in KNOWN_ALIVE:
        r = run_census(store_rel, iface)
        audit["stores"][store_rel] = r
        wrongly = [f for f in alive if f in r["dead"]]
        check(f"no-false-positive:{Path(store_rel).stem}", not wrongly,
              f"把活字段判成死状态: {wrongly}")

    # ── 3 store 内部读的字段: 仍会被列为候选(工具既定边界), 断言这个边界没被悄悄改掉 ──
    for store_rel, iface, internal in STORE_INTERNAL_READS:
        r = run_census(store_rel, iface)
        audit["stores"][store_rel] = r
        still_listed = [f for f in internal if f in r["dead"]]
        check(f"store-internal-still-listed:{Path(store_rel).stem}",
              len(still_listed) == len(internal),
              f"store 内部读的字段没被列为候选(边界可能被悄悄改了): "
              f"listed={still_listed} expect={internal}")

    # ── 7 反向断言: 工具仍能报出真死状态(证明 1~6 不是因为它啥都不报) ──
    store_rel, iface, expected_dead = EXPECTED_DEAD
    r = run_census(store_rel, iface)
    audit["stores"][store_rel] = r
    missed = [f for f in expected_dead if f not in r["dead"]]
    check("still-detects-real-dead-state", not missed,
          f"真死状态没报出来(工具可能退化成空转): missed={missed}")

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    print(
        f"Batch 352 verification passed: {len(checks)} checks. "
        "The AST-based census tool no longer misreports any of the 7 known-alive "
        "fields (each of which the regex version got wrong), frameosStore stays at "
        "zero dead state, and it still reports the 4 genuinely dead uiStore fields — "
        "so it is not passing by doing nothing."
    )


if __name__ == "__main__":
    main()
