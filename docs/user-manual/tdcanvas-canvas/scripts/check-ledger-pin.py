#!/usr/bin/env python3
"""账本锁定校验：`SOURCE_OBSERVATIONS.md` 声明锁定的提交必须等于应用仓 HEAD。

背景（M105）：账本开头用一句「版本锁定：TDCanvas `v0.14.0`，提交 `<40 位 sha>`」
把整本账本的证据**锚死在一个具体提交上**。这是这份账本成立的前提——§4 的节点尺寸、
§6 的连线校验、§11 的 i18n 死文案清单，全都是"在那个提交上观察到的"。

但这句话**没有任何机制守着它**。应用仓一旦被别的开发者推进，账本会继续以
"版本锁定"的口吻陈述旧观察，**而全部源码层门禁都不会报错**——它们只看手册自己的
文本，看不见应用仓。读者据此认为"这些结论对当前版本成立"，实际早已漂移。

本门禁把那句声明变成可验证的断言：

* 从账本里抽出 40 位 sha；
* 若应用仓路径在本机存在，比对 `git rev-parse HEAD`；
* **路径不存在时跳过并显式说明**——手册仓会被 clone 到不同机器，硬编码本地路径
  不能变成"在别人机器上必然失败"的门禁。

用法：

    python3 scripts/check-ledger-pin.py .
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

APP_REPO = Path("/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas")
LEDGER = "SOURCE_OBSERVATIONS.md"

# 账本开头那段固定以 40 位 sha 声明锁定提交；取第一处即可。
SHA_RE = re.compile(r"提交\s*`([0-9a-f]{40})`")


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    ledger = root / LEDGER

    if not ledger.exists():
        print(f"[FAIL] 找不到账本 {LEDGER}")
        return 1

    text = ledger.read_text(encoding="utf-8")
    m = SHA_RE.search(text)
    if not m:
        print(f"[FAIL] {LEDGER} 的「版本锁定」声明里没有 40 位提交号——锁都没锁住，谈不上校验")
        return 1

    pinned = m.group(1)

    if not APP_REPO.exists():
        # 手册仓会被 clone 到别的机器，那台机器上没有应用仓副本。
        # 这时**不能报错**，否则门禁在别人机器上必然红。
        print(f"  [skip] 本机没有应用仓副本（{APP_REPO}），跳过锁定校验")
        print(f"[ ok ] 账本锁定校验：账本声明锁定 {pinned[:7]}；本机无应用仓，已跳过比对")
        return 0

    try:
        head = subprocess.run(
            ["git", "-C", str(APP_REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"[FAIL] 无法读取应用仓 HEAD：{exc}")
        return 1

    if head != pinned:
        print(f"[FAIL] 账本锁定的提交与应用仓 HEAD 不一致")
        print(f"    账本 {LEDGER} 声明锁定：{pinned}")
        print(f"    应用仓 {APP_REPO} 当前 HEAD：{head}")
        print("    账本通篇以「版本锁定」的口吻陈述旧观察。两种处理：")
        print("      ① 若这些结论在新提交上仍成立 → 把账本的 sha 更新为新 HEAD；")
        print("      ② 若已漂移 → 逐条复核受影响的结论，并登记订正")
        return 1

    print(f"[ ok ] 账本锁定校验：账本声明锁定 {pinned[:7]}，与应用仓 HEAD 一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
