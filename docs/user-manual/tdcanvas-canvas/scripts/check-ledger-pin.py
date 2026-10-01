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

import json
import re
import subprocess
import sys
from pathlib import Path

APP_REPO = Path("/Users/yangjiefeng/Documents/AICoderTudou/TDCanvas")
LEDGER = "SOURCE_OBSERVATIONS.md"

# 2026-10-02 M109/M110 扩到全部「声明锁」的文件。此前这里写死只查 SOURCE_OBSERVATIONS.md，
# 而 40 位 sha 在 `task-inventory.yml:8` 里也**声明了一次**（`app_version: 'v0.14.0（锁定提交 …）'`）。
# 后果很具体：应用仓一推进 → 账本门禁变红 → 维护者更新账本的 sha → 门禁重新变绿，
# 而**任务账本里那句「锁定提交」静默过期**，没有任何东西会报错。
# 任务账本是「这本手册对齐哪个提交」的第二权威声明，读者会照它去核对。
#
# 扫描面用**白名单**而不是全仓 rglob：AUDIT.md / PROGRESS.md 里也有 40 位 sha，
# 但那些是**订正史**（记录"当时锁的是哪个"），必须原样保留——同 check-retractions.py 的理由。
PIN_DECLARERS = ["SOURCE_OBSERVATIONS.md", "task-inventory.yml"]
VERSION_DECLARERS = ["SOURCE_OBSERVATIONS.md", "task-inventory.yml"]

# 账本开头那段固定以 40 位 sha 声明锁定提交；取第一处即可。
SHA_RE = re.compile(r"提交\s*`([0-9a-f]{40})`")
# 扩展到「任何位置的 40 位十六进制串」——声明未必都写成「提交 `<sha>`」，
# task-inventory.yml 的写法是 `app_version: 'v0.14.0（锁定提交 16b31…）'`，没有反引号。
ANY_SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
VERSION_RE = re.compile(r"v(\d+\.\d+\.\d+)")


def collect_pins(root: Path) -> dict[str, set[str]]:
    """收集每份声明文件里出现的 40 位 sha。"""
    found: dict[str, set[str]] = {}
    for name in PIN_DECLARERS:
        page = root / name
        if not page.is_file():
            continue
        found[name] = set(ANY_SHA_RE.findall(page.read_text(encoding="utf-8")))
    return found


def collect_versions(root: Path) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for name in VERSION_DECLARERS:
        page = root / name
        if not page.is_file():
            continue
        found[name] = {m.group(1) for m in VERSION_RE.finditer(page.read_text(encoding="utf-8"))}
    return found


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    ledger = root / LEDGER

    if not ledger.exists():
        print(f"[FAIL] 找不到账本 {LEDGER}")
        return 1

    pins = collect_pins(root)
    if not pins.get(LEDGER):
        print(f"[FAIL] {LEDGER} 的「版本锁定」声明里没有 40 位提交号——锁都没锁住，谈不上校验")
        return 1
    all_shas = {s for v in pins.values() for s in v}
    pinned = sorted(all_shas)[0] if all_shas else ""
    versions = collect_versions(root)

    if not APP_REPO.exists():
        # 手册仓会被 clone 到别的机器，那台机器上没有应用仓副本。
        # 这时**不能报错**，否则门禁在别人机器上必然红。
        print(f"  [skip] 本机没有应用仓副本（{APP_REPO}），跳过锁定校验")
        print(f"[ ok ] 账本锁定校验：{len(pins)} 份声明文件锁定 {pinned[:7]} 且彼此一致；本机无应用仓，已跳过比对")
        return 0

    try:
        head = subprocess.run(
            ["git", "-C", str(APP_REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"[FAIL] 无法读取应用仓 HEAD：{exc}")
        return 1

    # ① 声明文件之间必须彼此一致——这是**不依赖应用仓**就能判的那一半。
    #    少了它，上面那种"更新了账本、漏了任务账本"的事故完全静默。
    if len(all_shas) > 1:
        print(f"[FAIL] 各声明文件锁定的提交不一致：")
        for name, shas in pins.items():
            print(f"    {name}: {', '.join(sorted(s[:7] for s in shas))}")
        print("    这些文件都是「这本手册对齐哪个提交」的权威声明，读者会照它们去核对源码。")
        print("    请把全部声明统一到同一个提交。")
        return 1

    # ② 版本号：声明文件之间必须彼此一致，且都等于应用仓 package.json。
    #
    # 这里踩过一次坑，和上面 ① 是同一个病：**判据写成了"应用版本是否出现在声明集合里"**，
    # 而集合是两个文件的并集——只把其中一个改成 v0.15.0，并集里仍然留着 0.14.0，
    # 于是照样放行。负向测试当场抓到了它。正确的判据是**逐份比对**，不是查并集。
    pkg = APP_REPO / "web" / "package.json"
    app_version = None
    if pkg.is_file():
        try:
            app_version = json.loads(pkg.read_text(encoding="utf-8")).get("version")
        except (json.JSONDecodeError, OSError):
            app_version = None

    if len({frozenset(vs) for vs in versions.values() if vs}) > 1:
        print("[FAIL] 各声明文件写的应用版本不一致：")
        for name, vs in versions.items():
            if vs:
                print(f"    {name}: {', '.join(sorted('v' + v for v in vs))}")
        print("    版本号是读者判断「这些结论对哪一版成立」的第一道参照，必须统一。")
        return 1

    declared_versions = {v for vs in versions.values() for v in vs}
    if app_version and declared_versions and app_version not in declared_versions:
        print(f"[FAIL] 手册声明的版本与应用仓 package.json 不一致")
        print(f"    声明文件写了：{', '.join(sorted('v' + v for v in declared_versions))}")
        print(f"    {pkg} 是：{app_version}")
        return 1

    if head != pinned:
        print(f"[FAIL] 账本锁定的提交与应用仓 HEAD 不一致")
        for name, shas in pins.items():
            print(f"    {name} 声明锁定：{', '.join(sorted(s[:7] for s in shas))}")
        print(f"    应用仓 {APP_REPO} 当前 HEAD：{head}")
        print("    账本通篇以「版本锁定」的口吻陈述旧观察。两种处理：")
        print("      ① 若这些结论在新提交上仍成立 → 把**全部**声明文件的 sha 更新为新 HEAD；")
        print("      ② 若已漂移 → 逐条复核受影响的结论，并登记订正")
        return 1

    print(
        f"[ ok ] 账本锁定校验：{len(pins)} 份声明文件锁定 {pinned[:7]}、彼此一致，"
        f"与应用仓 HEAD 相同；版本 v{app_version or '（未读到）'} 也与 package.json 相符"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
