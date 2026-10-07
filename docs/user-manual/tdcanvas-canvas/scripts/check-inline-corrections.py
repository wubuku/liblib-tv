#!/usr/bin/env python3
"""就地订正必须登记 R（第 29 道门禁，M299 新增，F136 的门禁化）。

**它守的是一类很隐蔽的失效**：**「就地订正只在被改的那一页留痕，而门禁靠的是 R 表。**

★ **M298 抓到的那处就是这么漏下来的**：★ **M280 查清了「左侧面板的高度其实是视口高的函数」，
★ **并在 `30-concepts.md` 就地更正过**——★ **★ 但那次订正没有登记 R。**
★ **于是 `create-nodes.md` 里同一件事的旧说法一直活着**（它把某个窗口高度下的读数
★ **和两个真常数并排列成「实测四档一模一样」），★ **而订正回归门禁从未报过它，
★ **因为那道门禁根本不知道这个错误说法存在过。**

★ **第二层后果更麻烦**：★ **账本上没有「有多少条就地订正没登记」这个数，
★ **所以连「该查哪些」都列不出来。** ★ **本门禁就是那个数。

---

**判据：扫正文页里的「就地订正痕迹」，★ **每一条都必须能找到它的 R 登记。**

**「归属」有三条口径**（★ **M299 实测：★ **这三条缺一条就误报，★ **而每一条都有活样本**）：

| 口径 | 怎么认 | 为什么需要它 |
|---|---|---|
| ★ **一** | ★ **那段引述被某个 `wrong`（needle）覆盖** | ★ **最常见的一类** |
| ★ **二** | ★ **订正块自己写了「见 Rxx」且该编号真实存在** | ★ **★ R44 就是这样**：★ **它的 needle 记的是「未选中 15 → 16 → 15」，★ **而 `create-canvas-project.md` 的订正块引述的却是「别指望它、走右键菜单」这一条**——★ **★ 同一条 R 覆盖两种错法，★ **而 needle 只记了其中一种**（F137） |
| ★ **三** | ★ **那段引述出现在某条 R 的 `why` 里** | ★ **同理，`why` 记的错法也可能与 needle 不同** |

★ **★ R 表不在本脚本里手抄**：★ **它用 `importlib` 直接加载 `check-retractions.py`
★ **读那个模块的 `RETRACTIONS`，★ **★ 所以两处永远一致**（`check-internal-lists.py`
★ **管的就是「唯一事实源不许手抄」那一族）。

**M299 建这道门禁时的实测覆盖面**：★ **正文 5 处就地订正痕迹，逐条有归属、0 漏网。**
★ **窄到没有误报余地**（M195 立的规矩：不误报且能全对，才配当门禁）。

用法：
    python3 scripts/check-inline-corrections.py .
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

# 就地订正的引述痕迹：动词 + 可选冒号 + 一对引号里的原话
QUOTE_PAT = re.compile(
    r"(?:原写|此前写|原先写|原来写|此前记|此前说|此前断言|此前标为)"
    r"\s*[：:]?\s*「([^」]{4,60})」"
)
# 订正块自报的 R 编号
SELF_REPORT = re.compile(r"见\s*(R\d+)")


def strip_md(text: str) -> str:
    return text.replace("**", "").replace("`", "").replace("\n", "")


def load_retractions(root: Path) -> list[dict]:
    """从 check-retractions.py 直接读 RETRACTIONS，不在本脚本里手抄一份。"""

    target = root / "scripts" / "check-retractions.py"
    if not target.is_file():
        raise SystemExit(f"[fail] 找不到 {target}，本门禁要读它的 R 表")
    spec = importlib.util.spec_from_file_location("_cr_for_inline", target)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # 该模块有 __main__ 保护，import 无副作用
    return list(mod.RETRACTIONS)


def body_pages(root: Path) -> list[Path]:
    out = [root / n for n in ("README.md", "00-quickstart.md", "20-reference.md",
                              "30-concepts.md", "90-troubleshooting.md")]
    out += sorted((root / "10-tasks").glob("*.md"))
    return [p for p in out if p.is_file()]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    retractions = load_retractions(root)

    needles = [strip_md(str(r.get("wrong", ""))) for r in retractions]
    whys = " ".join(strip_md(str(r.get("why", ""))) for r in retractions)
    rids = {str(r.get("id")) for r in retractions}

    problems: list[str] = []
    total = 0
    for page in body_pages(root):
        rel = page.relative_to(root).as_posix()
        for ln, line in enumerate(page.read_text(encoding="utf-8").split("\n"), 1):
            for m in QUOTE_PAT.finditer(line):
                total += 1
                quote = m.group(1)

                # 口径二：订正块自报的 R 编号（编号必须真实存在）
                tail = strip_md(line[m.end(): m.end() + 180])
                hit_self = SELF_REPORT.search(tail)
                if hit_self and hit_self.group(1) in rids:
                    continue

                # 口径一 / 三：needle 或 why 覆盖这段引述
                frags = [f for f in re.split(r"[\s，。、；：!?,]", quote) if len(f) >= 6]
                best = max(frags, key=len) if frags else quote[:6]
                if any(best in n or n in best for n in needles):
                    continue
                if best and best in whys:
                    continue

                problems.append(
                    f"[{rel}:{ln}] 这处就地订正找不到对应的 R 登记：「{quote[:40]}」\n"
                    f"        → 它只在这一页留了痕，★ **而门禁靠的是 R 表**——\n"
                    f"          ★ **门禁不知道这个错误说法存在过，就抓不到它在别处的残留**（F136）。\n"
                    f"          **修法：登记一条 R（kind 填 conclusion 或 wording），"
                    f"★ **并把这里的引述改写成不复现 needle 的措辞**（M205）"
                )

    if problems:
        print(f"[fail] 就地订正的 R 登记校验未通过（{len(problems)} 项）：")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        f"[ ok ] 就地订正的 R 登记校验：正文 {total} 处订正痕迹全部能追溯到 R"
        f"（共 {len(retractions)} 条），★ **无「只有痕迹没有守卫」的条目**"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())