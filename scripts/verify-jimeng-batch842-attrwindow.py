#!/usr/bin/env python3
"""Jimeng clone batch 842 verifier —— role 层扫描器的属性窗口，以及**自检的可证伪性**。

## 这一批修的是工具，不是产品

`jimeng_role_layer_scan.py` 报「`JimengAiDrawer` 有 4 处 role 浮层无 data-testid」。
回去读源码，**锚点明明就在上一行**：

    <div className="mx-3 mb-2 …" data-testid="canvas-agent-session-menu"
         role="dialog" aria-label="会话列表">

根因：扫描器的属性窗口是 `role="…"` **之后**到下一个 `>` 那一段。
`data-testid` 写在 `role=` **前面**的标签，**整类**漏掉。

**属性顺序不该影响结论。** 这已经是同一个洞的第三种形状：

| 版次 | 写法 | 症状 |
|---|---|---|
| 一 | `src[m.end():]`（整个标签**之后**） | 56 处全报「无名无锚点」 |
| 二 | `mid` = `role=` 之后那一段 | `testid` 在 `role` 之前的全漏（本批） |
| 三 | **整个开标签** | —— |

## 更要紧的是：原有自检**盖不住**这个 bug

832 的 17 个锚点恰好都写在 `role=` 后面，于是自检一路绿灯。
**自检覆盖不到的那一半，等于没有自检。** 本批补一条合成夹具：
三种属性顺序（在前 / 在后 / 跨行在前）必须全部认出。

而且这条新自检本身**可证伪**（verifier §D 会验）：拿批 842 之前那个
有 bug 的窗口逻辑去跑同一组夹具，必须认错 —— 认不错就说明这条自检抓不住那个
bug，那它就是一条装饰。

## 还有一条性能护栏

改成"从每个 `<` 起匹配"之后，贪婪版全仓跑到 >180s 超时、惰性版 2m3s。
现在反过来做（`role=` 在全仓是稀有的，先定位它再往回走标签起点）= **0.1s**。
verifier §E 把这条钉住，免得有人哪天"顺手改回去"。
"""
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN = ROOT / "scripts" / "jimeng_role_layer_scan.py"

# 合成夹具：属性顺序的三种写法。与扫描器内置自检同一组，但**独立**重新实现一遍
# —— 复制粘贴同一份代码到两处，两处会一起错，自检就成了同义反复。
CASES = [
    ('<div data-testid="a" role="dialog" aria-label="X" />', "a"),
    ('<div role="dialog" data-testid="b" aria-label="X" />', "b"),
    ('<div className="c"\n  data-testid="c2"\n  role="listbox"\n/>', "c2"),
]

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


ROLE_RE = re.compile(r'role="(dialog|menu|listbox|popover)"')
WIN_RE = re.compile(r'(?:[^<>]|\{[^{}]*\})*')
TID_RE = re.compile(r'data-testid=("([^"]*)"|\{([^}]*)\})')


def _tid(own: str) -> str:
    t = TID_RE.search(own)
    return (t.group(2) or t.group(3)) if t else "—"


def probe_fixed(frag: str) -> str:
    """批 842 之后的窗口：整个开标签。"""
    m = ROLE_RE.search(frag)
    if not m:
        return "—"
    lt = frag.rfind("<", 0, m.start())
    gt = frag.rfind(">", 0, m.start())
    if lt < 0 or lt < gt:
        return "—"
    mm = WIN_RE.match(frag, m.end())
    return _tid(frag[lt:m.start()] + " " + (mm.group(0) if mm else ""))


def probe_buggy(frag: str) -> str:
    """批 842 **之前**的窗口：只有 `role=` 之后那一段。故意保留。"""
    m = ROLE_RE.search(frag)
    if not m:
        return "—"
    mm = WIN_RE.match(frag, m.end())
    return _tid(mm.group(0) if mm else "")


def main() -> int:
    # ── A. 跑一遍 ─────────────────────────────────────────────────
    print("— A. 扫描器跑通 —")
    t0 = time.time()
    r = subprocess.run([sys.executable, str(SCAN), "jimeng"],
                       capture_output=True, text=True, cwd=str(ROOT), timeout=120)
    dt = time.time() - t0
    out = (r.stdout or "") + (r.stderr or "")
    check("A.0 退出码 0", r.returncode == 0, f"rc={r.returncode}")
    m_layers = re.search(r"共 (\d+) 处 role 浮层", out)
    check("A.1 扫到了 role 浮层（不是 0 层）",
          bool(m_layers) and int(m_layers.group(1)) > 0,
          f"共 {m_layers.group(1) if m_layers else '?'} 处")

    # ── B. 三条自检都要在输出里 ────────────────────────────────────
    print("\n— B. 自检真的跑了，而且结论是绿的 —")
    check("B.1 832 的 17 个锚点全部命中",
          "832 的 17 个锚点全部命中" in out,
          [l for l in out.splitlines() if "832 的" in l][:1])
    m_both = re.search(r"「两样都无」= (\d+)", out)
    check("B.2 「两样都无」= 0（非 0 说明扫描器自己坏了）",
          bool(m_both) and int(m_both.group(1)) == 0,
          f"实测={m_both.group(1) if m_both else '?'}")
    check("B.3 属性顺序自检在输出里（且判绿）",
          "属性顺序不影响结论" in out and "全部认出 ✓" in out,
          [l for l in out.splitlines() if "属性顺序" in l][:1])

    # ── C. jimeng 侧：不该再有「有 role 无锚点」 ───────────────────
    print("\n— C. jimeng 侧无锚点必须为 0 —")
    # ⚠️ 必须**按段落切开**再判：第一版直接 grep 所有 `components/jimeng/` 行，
    #    结果把「无可访问名」那 4 行也算进来了 —— 那 4 处**有**锚点（tid= 显示在
    #    右边），缺的是名字，性质完全不同。判据自己张冠李戴过一次。
    sec = ""
    no_tid_jimeng: list[str] = []
    for line in out.splitlines():
        if line.startswith("无 data-testid"):
            sec = "no_tid"
            continue
        if line.startswith("无可访问名"):
            sec = "no_name"
            continue
        if line.startswith("两样都无"):
            sec = "both"
            continue
        if sec == "no_tid" and "components/jimeng" in line:
            no_tid_jimeng.append(line.strip())
    check("C.1 「无 data-testid」段落里没有 jimeng 自己的",
          not no_tid_jimeng, f"还有={no_tid_jimeng[:2]}")
    m_nt = re.search(r"无 data-testid（(\d+) 处）", out)
    check("C.2 缺锚点计数能被读出来（判据不是恒空）",
          bool(m_nt) and int(m_nt.group(1)) >= 0,
          f"实测={m_nt.group(1) if m_nt else '?'}")

    # ── D. 自检**可证伪**：老写法必须认错 ──────────────────────────
    print("\n— D. 这条自检抓得住那个 bug（否则它是装饰）—")
    bad_new = [(f, probe_fixed(f), w) for f, w in CASES if probe_fixed(f) != w]
    check("D.1 修好的窗口三种写法全认得出", not bad_new, f"认错={bad_new}")
    bad_old = [(f, probe_buggy(f), w) for f, w in CASES if probe_buggy(f) != w]
    check("D.2 **有 bug 的老窗口**必须认错至少一处（否则这条自检白写）",
          len(bad_old) > 0, f"老写法认错 {len(bad_old)}/{len(CASES)} 处")
    specifically = [c for c in bad_old if c[1] == "—"]
    check("D.3 老窗口确实栽在「testid 写在 role 之前」这个形状上",
          bool(specifically), f"{len(specifically)} 处认成无锚点")

    # ── E. 源码侧的防阉割契约（含性能护栏）─────────────────────────
    print("\n— E. 源码侧的防阉割契约 —")
    s = SCAN.read_text(encoding="utf-8")
    check("E.1 窗口是整个开标签（往回找 `<`，再往后取到 `>`）",
          'src.rfind("<", 0, m.start())' in s
          and 'src.rfind(">", 0, m.start())' in s)
    check("E.2 先定位稀有的 role= 再往回走（不是从每个 `<` 起匹配）",
          'ROLE.finditer(src)' in s and "<[A-Za-z][A-Za-z0-9._]*" not in s,
          "从 `<` 起匹配的写法会全仓跑到超时")
    check("E.3 剥掉 JSX 里的 `//` 注释（否则注释里的 testid 会冒充真锚点）",
          're.sub(r"//[^\\n]*", "", own)' in s)
    check("E.4 位置属性顺序的合成夹具在源码里",
          "ORDER_CASES" in s and "属性顺序不影响结论" in s)
    check("E.5 性能护栏：全仓扫描 < 20s（贪婪回溯版实测 >180s 超时）",
          dt < 20, f"实测 {dt:.2f}s")

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 842-attrwindow OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
