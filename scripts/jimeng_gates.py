"""Jimeng 门禁汇总器 — 把「我以为的门禁结果」和「真实退出码」对齐。

## 为什么要有这个工具

批 825 在收尾时查出：我在 §31.8 / §32.7 / §33.7 / §34.4 **连续四个批次**
写了「`npm run check` EXIT=0」，而那四次**没有一次是真的**。原因小得可笑：

```bash
npm run check 2>&1 | tail -4; echo "EXIT=$?"     # ← $? 是 tail 的码，永远 0
```

`check` 当时确实是红的（批 805 留下的 `Date.now()` 触发
`react-hooks/purity`），也就是说**门禁红着，我却写了四次「已验收」**。

靠自律解决不了 —— 报错的那一行我每批都写，每批都写错。所以让工具来读：

- **不过管道**：`subprocess.run(cmd, capture_output=True)` 直接拿 `returncode`。
- **逐个门禁独立跑**：一个挂了就报那一个，不因为前面的失败丢掉后面的读数。
- **区分「我坏了」和「别人在途挡路」**：这是本工具最要紧的一条。
  共享工作区里，别人写一半的文件会让 typecheck / build 失败
  （本工具开发时就撞上 `DirectorTimeline.tsx` 有个未闭合的 `<div>`）。
  这两种状态**不该混为一谈**：
    - FAIL  = 门禁真红，多半是我改坏了 → 必须修
    - BLOCKED = 红在**我没碰过的文件**里 → 是别人在途，不代改，但要**喊出来**
  把 BLOCKED 静默当成 PASS，是另一种假绿；当成 FAIL 则是错责。必须单独一类。

## 用法

    ~/.venvs/liblib-harness/bin/python scripts/jimeng_gates.py            # 全部
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_gates.py lint typecheck
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_gates.py --mine src/store/jimengStore.ts
        # --mine <path…>：声明本批我改过的文件。typecheck 报错若**全部**落在
        # 这些文件之外 → 判 BLOCKED（别人在途）；有落在里面 → 判 FAIL（我坏的）。

退出码：0 = 全绿；1 = 有 FAIL；2 = 无 FAIL 但有 BLOCKED（结论不完整，不能算过）。

⚠️ `--mine` **只用来缩小范围，不能单独当 BLOCKED 的理由**：BLOCKED 还要求
那些报错文件**当前确实有未提交改动**。否则「我自己改坏了却没申报」会被
误判成「别人在途」—— 那是一条比原 bug 更隐蔽的假绿。
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable or "python3"
NODE_BIN = "/Users/yangjiefeng/.nvm/versions/node/v24.6.0/bin"

# (门禁名, 命令, 超时秒)
GATES = [
    ("lint", ["npm", "run", "lint"], 300),
    ("typecheck", ["npm", "run", "typecheck"], 300),
    ("assertions", [PY, "scripts/verify-assertions.py"], 180),
    ("build", ["npm", "run", "build"], 600),
]

PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"


def run_gate(name: str, cmd: list[str], timeout: int) -> tuple[str, str]:
    """跑一个门禁，返回 (状态, 详情)。

    ⚠️ 这里**故意不经过 shell、不接管道** —— 批 825 的教训就是 `$?` 取错了对象。
    """
    env = dict(os.environ)
    env["PATH"] = f"{NODE_BIN}:{env.get('PATH', '')}"
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return FAIL, f"超时 {timeout}s（命令：{' '.join(cmd)}）"
    except FileNotFoundError as e:
        return FAIL, f"命令不存在：{e}"
    dt = time.time() - t0
    if r.returncode == 0:
        return PASS, f"{dt:.0f}s"
    out = (r.stdout or "") + (r.stderr or "")
    return FAIL, f"退出码 {r.returncode}，{dt:.0f}s\n" + tail(out)


def tail(text: str, n: int = 14) -> str:
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return "\n        ".join(lines[-n:]) if lines else "(无输出)"


ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
# 路径 + 行列。两种形态都要吃：
#   tsc  : src/foo.ts(12,5): error TS…
#   next : ./src/foo.tsx:845:10   （路径外面还常包着 ANSI 色码）
# 字符类排除 `(` `:` 与空白，于是 `(12,5)` 天然不会被吞进路径里。
# ⚠️ 第一版用「行首匹配 + 按 ( 和 : 切」写了两个分支，第二个分支本是为 next
#    形态准备的，却把 tsc 形态也匹配上了，切出 `foo.ts(12,5)` 这种带行列的
#    假路径 —— 拿它去和 git status 比对当然对不上，BLOCKED 判定于是全部落空。
#    **同一个解析器同时服务两种输出格式时，判据要一次写对，不能靠两个分支。**
ERR_PATH = re.compile(r"(?:\./)?((?:src|app|scripts|docs)/[^\s:(]+)")


def error_files(text: str) -> set[str]:
    """从 typecheck / build 输出里抽出报错的源文件路径。"""
    hits = set()
    for raw in text.splitlines():
        m = ERR_PATH.search(ANSI.sub("", raw))
        if m:
            hits.add(m.group(1))
    return hits


def dirty_in_worktree(paths: set[str]) -> set[str]:
    """哪些文件**当前**有未提交改动（含未跟踪）。

    这是 BLOCKED 判定的**证据**，不是我的自我申报 ——
    第一版只用 `--mine`（我自己列的改动范围），那等于把判据交给被审者：
    我要是漏报一个自己改坏的文件，它会被标成「别人在途」，
    **这就是一条新的假绿通道**，比原来那个更隐蔽。
    改成取证：只有「确实还没提交、正在被写」的文件才配叫别人在途。
    已经提交进去还红着的，那是真红。"""
    if not paths:
        return set()
    r = subprocess.run(["git", "status", "--porcelain", "--"] + sorted(paths),
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        return set()
    out = set()
    for line in r.stdout.splitlines():
        if len(line) > 3:
            out.add(line[3:].strip().strip('"'))
    return out


def main() -> int:
    argv = sys.argv[1:]
    mine: set[str] = set()
    if "--mine" in argv:
        i = argv.index("--mine")
        mine = {a.replace(str(ROOT) + "/", "").lstrip("./") for a in argv[i + 1:]}
        argv = argv[:i]
    wanted = set(argv) if argv else None
    gates = [g for g in GATES if wanted is None or g[0] in wanted]
    if not gates:
        print(f"没有匹配的门禁。可选：{[g[0] for g in GATES]}")
        return 1

    results: list[tuple[str, str, str]] = []
    for name, cmd, timeout in gates:
        print(f"… 跑 {name}", flush=True)
        status, detail = run_gate(name, cmd, timeout)
        # BLOCKED 判定需要**两个条件同时成立**：
        #   ① 报错的文件不在本批改动范围内（--mine）
        #   ② 且该文件**当前确实有未提交改动**（有人在写）
        # 缺 ② 就判 FAIL —— 已提交进去还红着，那是真红，不是谁的在途。
        if status == FAIL and name in ("typecheck", "build"):
            files = error_files(detail)
            if files:
                outside = files - mine
                inflight = dirty_in_worktree(outside)
                if outside and inflight == outside:
                    status = BLOCKED
                    detail = (f"报错文件 {sorted(outside)} 既不在本批范围 {sorted(mine)} 内，"
                              f"又确实有未提交改动 ⇒ 判为**别人在途**，不代改。\n        ") + detail
                elif outside:
                    bad = sorted(outside - inflight)
                    if bad:
                        detail = (f"注意：报错文件 {bad} 虽不在本批范围内，"
                                  f"但**没有未提交改动** ⇒ 已提交代码就是红的，"
                                  f"不算别人在途。\n        ") + detail
        results.append((name, status, detail))

    print()
    print("— 门禁汇总（退出码均为直接读回，未经管道）—")
    n_fail = n_block = 0
    for name, status, detail in results:
        mark = {PASS: "✓", FAIL: "✗", BLOCKED: "⛔"}[status]
        print(f"  {mark} {name:<12} {status}")
        if status == FAIL:
            n_fail += 1
        elif status == BLOCKED:
            n_block += 1
        if status != PASS:
            print(f"        {detail}")

    print()
    if n_fail:
        print(f"结论：{n_fail} 个门禁**真红**（多半是本批改坏了）—— 必须修。")
        return 1
    if n_block:
        print(f"结论：无真红，但 {n_block} 个门禁**被别人在途的文件挡着**。")
        print("      这不等于通过：结论不完整，等对方写完必须重跑。")
        print("      把它当 PASS 就是 §36.8 记的那种假绿 —— 别这么干。")
        return 2
    print("结论：全绿。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
