#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 835：给 748 的 C1／C3／C4 三条红做**逐项归因**——每个多出来的 `data-*`
属性名归属到**具体是哪个批次引入的**。

★ 为什么不能「重跑一次 748、把新数字抄进期望值」：
  748 的 C1／C3 判的是**绝对快照数字**（并集 446、按文件求和 460、运行时 200→250…），
  而**任何**新增 `data-*` 的批次都会把它推高 ⟹ 每加一批就红 ⟹ 抄新数字只是把
  「快照过期」推迟到下一批，**并没有说明白数字为什么变**。
  ⟹ 本探针先回答「**多出来的每个属性名是哪一批加的**」，
     再据此决定 748 的判据该怎么改。

★ 做法（不改源码、不用 stash、不用 worktree）：
  ① 用 git 逐个 commit 取出 `src/components/director/*.tsx` 的**当时版本**，
     按 748 的**同一套正则与同一套计数口径**算并集；
  ② 与相邻两个 commit 比对 ⟹ 得到「这一批新增了哪些属性名、删了哪些」；
  ③ 与 748 当时的基线（`git show 956ff15d:scripts/verify-liblib-batch748.py`
     里的 446/460）逐项对齐。

★ 748 的静态口径必须**逐字照抄**（`\\b(data-[a-z0-9-]+)` 逐行扫、每文件去重、再并集），
  否则算出来的数与 748 不可比。
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
DESK = ROOT / "src/components/director"
ATTR = re.compile(r"\b(data-[a-z0-9-]+)")
DATASET = re.compile(r"\.dataset\.([A-Za-z0-9_]+)\s*=")

# 导演台目录出现过的批次（自 748 基线起到 HEAD）
COMMITS = [
    ("956ff15d", "batch 748 基线"),
    ("e5d25d52", "batch 825 跟随横幅"),
    ("da7b7043", "batch 831 帮助→快捷键面板"),
    ("15837b7f", "batch 832 添加机位·机位预设面板"),
    ("75b5af1d", "batch 833 机位预设语义 ＋ 命名"),
    ("8074234d", "batch 834 时间轴引导 5 步"),
]


def git_show(commit, path):
    p = subprocess.run(["git", "show", "%s:%s" % (commit, path)],
                       cwd=str(ROOT), capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def static_of(commit):
    """在**给定 commit** 上，按 748 的同一口径算静态统计。"""
    files = subprocess.run(["git", "ls-tree", "--name-only", commit,
                            "src/components/director/"],
                           cwd=str(ROOT), capture_output=True, text=True).stdout.split()
    per_file, union = {}, set()
    ds_names = set()
    for f in files:
        if not f.endswith(".tsx"):
            continue
        text = git_show(commit, f)
        if text is None:
            continue
        names = set()
        for line in text.split("\n"):
            names.update(ATTR.findall(line))
        per_file[pathlib.Path(f).name] = sorted(names)
        union |= names
        for line in text.split("\n"):
            for m in DATASET.finditer(line):
                kebab = re.sub(r"([A-Z])", lambda x: "-" + x.group(1).lower(), m.group(1))
                ds_names.add("data-" + kebab)
    return {
        "fileCount": len(per_file),
        "sumByFile": sum(len(v) for v in per_file.values()),
        "unionCount": len(union),
        "unionNames": sorted(union),
        "effectiveUnionCount": len(union | ds_names),
        "datasetDerived": sorted(ds_names),
        "perFileCount": {k: len(v) for k, v in per_file.items()},
    }


def main():
    out = []
    prev = None
    for commit, label in COMMITS:
        st = static_of(commit)
        row = {"commit": commit, "label": label,
               "fileCount": st["fileCount"], "sumByFile": st["sumByFile"],
               "unionCount": st["unionCount"],
               "effectiveUnionCount": st["effectiveUnionCount"],
               "perFileCount": st["perFileCount"]}
        if prev is not None:
            cur = set(st["unionNames"])
            old = set(prev["unionNames"])
            row["added"] = sorted(cur - old)
            row["removed"] = sorted(old - cur)
            row["addedCount"] = len(row["added"])
            row["removedCount"] = len(row["removed"])
        out.append(row)
        print("%-10s %-34s 文件 %2d 求和 %3d 并集 %3d 有效 %3d%s" % (
            commit[:8], label, st["fileCount"], st["sumByFile"], st["unionCount"],
            st["effectiveUnionCount"],
            "" if prev is None else ("  +%d/-%d" % (row["addedCount"], row["removedCount"]))))
        prev = st

    # 748 基线到现在，净增的属性名清单（按引入批次归属）
    base = static_of(COMMITS[0][0])
    cur = static_of(COMMITS[-1][0])
    net_added = sorted(set(cur["unionNames"]) - set(base["unionNames"]))
    net_removed = sorted(set(base["unionNames"]) - set(cur["unionNames"]))

    # 归属：每个新增名最早出现在哪个 commit
    owner = {}
    for commit, label in COMMITS:
        names = set(static_of(commit)["unionNames"])
        for n in net_added:
            if n in names and n not in owner:
                owner[n] = label

    print("\n=== 748 基线 ⟶ HEAD 净增 %d 个属性名（按引入批次归属）===" % len(net_added))
    by_batch = {}
    for n in net_added:
        by_batch.setdefault(owner.get(n, "?"), []).append(n)
    for label in sorted(by_batch):
        print("\n[%s]  %d 个" % (label, len(by_batch[label])))
        for n in by_batch[label]:
            print("   ", n)
    if net_removed:
        print("\n净减 %d 个：%s" % (len(net_removed), net_removed))

    payload = {"每批静态统计": [{k: v for k, v in r.items()
                                  if k not in ("unionNames",)} for r in out],
               "净增属性名": net_added,
               "净减属性名": net_removed,
               "净增归属": owner,
               "★注意": "本探针只做**静态侧**归因；运行时侧（首屏 200→250、"
                        "rail 每枚带出多少种）要用 748 的浏览器脚本量，"
                        "归因见 probes/attrib835.py。"}
    outp = pathlib.Path("/tmp/b835-static-attrib.json")
    outp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n写入", outp)


if __name__ == "__main__":
    sys.exit(main())
