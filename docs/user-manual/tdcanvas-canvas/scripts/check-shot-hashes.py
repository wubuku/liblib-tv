#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""截图清单的 sha256 与图片实物逐张对账——第 25 道构建门禁（M235 新建）。

**为什么需要这道门禁**：清单里每张图都带一个 `sha256`，
**它声称「这张 PNG 的内容指纹是这串十六进制」**——
而 `sha256` 是本清单里**唯一一个能被完美机检的字段**：
读图、算哈希、与登记值比，三步都不会出错、没有解释空间、不依赖任何 OCR。
★ **而它从来没被任何门禁碰过**：
`check-inventory-freshness.py` 只数**条目数**（`screenshot_count` 对不对），
`check-dist-links.py` 只查**文件在不在**，
**没有任何一道门禁核对过「这张图的内容是不是登记的那一张」。**

★ **为什么这个空白值得补**：
清单里的 `step` / `alt` / `verified_locator` 每一句都可能在漫长的增补里**张冠李戴**——
A 图的描述被挂到 B 图上，从内容上极难发现，
**而 sha256 正是唯一能把这种错位一网打尽的字段**：
把 A 图的哈希填进 B 图的条目，这道门禁当场报出来。

**判据只有一条，而且是双向的（这是本门禁与前 24 道的不同）**：

    清单登记的 sha256  !=  图片实物算出的 sha256   ⇒  报出来
    清单登记的 sha256  ==  图片实物算出的 sha256   ⇒  放行

- **为什么这里可以双向**：这一族字段（`captured_at` 那种）之所以只能单向，
  是因为「早于」和「晚于」都有可能说得通（跨零点、次日提交）；
  **而内容指纹没有解释空间**——图的内容变了，哈希就一定变，没有例外。
- **M235 实测**：112 张**逐张全对**（0 个不符、0 个重复、0 个格式异常）。
  **阳性对照**：故意翻转某张 PNG 的最后 1 个字节，门禁立刻点名那张图。
- **代价**：**112 张全量对账 0.057–0.099 秒**，比 M231 那次「拍摄日 vs 入库日」
  的 0.63 秒还快一个数量级，**所以它进得了构建门禁**（零 git 依赖、瞬时）。

**退出码**：0 = 全部一致；1 = 有不符 / 缺文件 / 格式异常 / 清单里没有哈希。
用法：python3 scripts/check-shot-hashes.py <手册目录>
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

MANIFEST = "screenshots/manifest.yml"
_SHA_LINE = re.compile(r"^    sha256: ([0-9a-f]{64})\s*$")
_FILE_LINE = re.compile(r"^  - file: (\S+)\s*$")
# 任何一行里出现了 sha256 键、但不是合法的 64 位小写十六进制 —— 那本身是格式异常
_SHA_KEY = re.compile(r"^\s*sha256:\s*(.*)$")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    mf = root / MANIFEST
    if not mf.is_file():
        print(f"[FAIL] 找不到 {mf}")
        return 1

    text = mf.read_text(encoding="utf-8")
    lines = text.split("\n")

    entries: list[tuple[str, int, str]] = []      # (相对路径, file 行号, sha256)
    odd_format: list[tuple[int, str]] = []         # 写了 sha256 键但格式不对
    all_files: list[tuple[str, int]] = []          # 所有 - file: 行（用于「每条都必须有哈希」）
    no_hash: list[tuple[str, int]] = []            # 有 file 行却没有 sha256 的条目
    cur: str | None = None
    cur_line = 0
    seen_hash_in_entry = False
    for i, line in enumerate(lines, 1):
        mf_ = _FILE_LINE.match(line)
        if mf_:
            if cur is not None and not seen_hash_in_entry:
                # ★ M235 第 5 次应用 F41：上一版把「删掉一整条哈希」当成了正常情况——
                #   清单从 112 条变 111 条，门禁照样报「全部一致」，
                #   **因为它只数自己解析到了多少，没问「本来该有多少」**。
                #   正确判据不是写死 112（重拍会让它漂移），
                #   而是**每一条 - file: 都必须带自己的 sha256**。
                no_hash.append((cur, cur_line))
            cur, cur_line, seen_hash_in_entry = mf_.group(1), i, False
            all_files.append((mf_.group(1), i))
            continue
        mkey = _SHA_KEY.match(line)
        if mkey:
            val = mkey.group(1).strip().strip("'\"")
            m = _SHA_LINE.match(line)
            if m and cur and not seen_hash_in_entry:
                entries.append((cur, cur_line, m.group(1)))
                seen_hash_in_entry = True
            else:
                # 要么格式不对，要么同一条目里出现了第二个哈希 —— 两种都得报
                odd_format.append((i, line.strip()[:60]))
    if cur is not None and not seen_hash_in_entry:
        no_hash.append((cur, cur_line))

    problems: list[str] = []

    for rel, fln in no_hash:
        problems.append(
            f"{MANIFEST}:{fln} 这一条（{rel}）**没有 sha256 字段** —— "
            f"每条条目都必须有：这张图的身份证明不能整条缺失，"
            f"而缺了它这道门禁就看不见这张图")

    if odd_format:
        for ln, frag in odd_format:
            problems.append(
                f"{MANIFEST}:{ln} 的 sha256 不是「64 位小写十六进制」：{frag!r} —— "
                f"**格式异常本身就是错**，别让它混过去")
    if not entries:
        problems.append(f"{MANIFEST} 里一条 sha256 都没解析出来 —— "
                        f"**清单里没有哈希，这道门禁就什么也没看**")
        print(f"[FAIL] 截图哈希对账失败：{len(problems)} 项")
        for p in problems:
            print(f"  ★ {p}")
        return 1

    # ---- 逐张实算 ----
    mismatched: list[tuple[str, int, str, str]] = []
    missing: list[tuple[str, int]] = []
    for rel, fln, want in entries:
        p = root / rel
        if not p.is_file():
            missing.append((rel, fln))
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != want:
            mismatched.append((rel, fln, want, got))

    for rel, fln in missing:
        problems.append(f"{MANIFEST}:{fln} 登记的截图不存在：{rel}")
    for rel, fln, want, got in mismatched:
        problems.append(
            f"{MANIFEST}:{fln} 登记的 sha256 是 {want[:16]}…，"
            f"但 {rel} 的实物是 {got[:16]}… —— "
            f"**要么图被换了，要么哈希被抄错了**")

    # 同一张图被登记两次、或两条目抄了同一个哈希 —— 也要报
    seen: dict[str, int] = {}
    dup: list[tuple[str, int, int]] = []
    for rel, fln, want in entries:
        if want in seen:
            dup.append((rel, fln, seen[want]))
        else:
            seen[want] = fln
    for rel, fln, first in dup:
        problems.append(
            f"{MANIFEST}:{fln} 的 sha256 与第 {first} 行重复 —— "
            f"**两条目指向同一张内容不同的图，或其中一条抄错了**")

    if problems:
        print(f"[FAIL] 截图哈希对账失败：{len(problems)} 项")
        for p in problems:
            print(f"  ★ {p}")
        print("\n  提示：sha256 是这张图唯一能机检的身份证明。")
        print("        重算：python3 -c \"import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())\" <图片路径>")
        return 1

    print(f"  [ ok ] 截图哈希对账：{len(entries)}/{len(all_files)} 条 "
          f"（清单共 {len(all_files)} 条 `- file:`）的 sha256 与实物逐张一致，"
          f"无重复、无格式异常、无缺哈希"
          f"（{sum((root / r).stat().st_size for r, _, _ in entries) / 1048576:.1f} MB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
