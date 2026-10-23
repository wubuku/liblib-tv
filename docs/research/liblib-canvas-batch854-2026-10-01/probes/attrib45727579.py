#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 854 **定点归因**：回归清单里新出现的红（`45`／`72`／`75`／`79`）
⟹ ⟹ 到底是**本批引入的**、还是**既有旧账**？

★ 做法（沿用 853 的 `attrib8791.py` 形态）：
  1. 把本批改过的三个源文件**按字节**备份；
  2. `git checkout --` 换回 HEAD（**白名单**，不碰别人的 WIP）；
  3. 在 HEAD 上跑这四条门禁 ⟹ ⟹ 记读数；
  4. **字节级**复原工作副本；
  5. 在工作副本上再跑一遍 ⟹ ⟹ 比读数。

★ 判定：
  - HEAD 上**也红**、且**报错逐字相同** ⟹ ⟹ **既有旧账**，不是本批引入；
  - HEAD 上**绿** ⟹ ⟹ **本批引入** ⟹ ⟹ 必须整改。

★ ★ 归因要**同时**给两条证据：**读数逐字相同** ＋ **该路径不经过本批新增的入口**。
"""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

CHANGED = [
    "src/lib/directorProjectDocument.ts",
    "src/store/directorStore.ts",
    "src/components/director/DirectorObjectTree.tsx",
]

TARGETS = [("45", "py"), ("72", "mjs"), ("75", "mjs"), ("79", "mjs")]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(batch: str, ext: str) -> str:
    script = ROOT / ("scripts/verify-liblib-batch%s.%s" % (batch, ext))
    cmd = ([str(NODE), str(script)] if ext == "mjs"
           else [sys.executable, str(script)])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                       cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    keep = [ln.strip() for ln in out.splitlines()
            if ("Error" in ln or "assert" in ln.lower() or "通过" in ln
                or "判据" in ln or "AssertionError" in ln)]
    tail = keep[-6:] if keep else [ln.strip() for ln in out.splitlines() if ln.strip()][-3:]
    return "rc=%s | %s" % (r.returncode, " ／ ".join(tail)[:400])


def main() -> int:
    backups = {ROOT / rel: (ROOT / rel).read_bytes() for rel in CHANGED}
    before = {p: sha(p) for p in backups}
    print("将要换回 HEAD 的文件（白名单）：")
    for rel in CHANGED:
        print("   ", rel)

    head_reads = {}
    try:
        subprocess.run(["git", "checkout", "--"] + CHANGED, cwd=str(ROOT),
                       check=True)
        print("已换回 HEAD")
        for b, e in TARGETS:
            head_reads["%s.%s" % (b, e)] = run(b, e)
            print("  HEAD %-8s ⟹ %s" % ("%s.%s" % (b, e), head_reads["%s.%s" % (b, e)]),
                  flush=True)
    finally:
        for p, data in backups.items():
            p.write_bytes(data)
        print("已复原工作副本")
        for p in backups:
            assert sha(p) == before[p], "★ 复原后哈希不一致：%s" % p
            print("  复原校验 OK %s" % p.name)

    print("\n=== 工作副本上再跑一遍 ===")
    out_rows = []
    for b, e in TARGETS:
        key = "%s.%s" % (b, e)
        work = run(b, e)
        same = work == head_reads.get(key)
        head_red = head_reads.get(key, "").startswith("rc=1")
        work_red = work.startswith("rc=1")
        verdict = ("既有旧账" if (head_red and work_red and same)
                   else ("★ 本批引入" if (not head_red and work_red)
                         else "（其它情况）"))
        out_rows.append({"门禁": key, "HEAD": head_reads.get(key),
                         "工作副本": work, "读数逐字相同": same,
                         "HEAD红": head_red, "工作副本红": work_red,
                         "归因": verdict})
        print("  %-8s %s ｜ %s" % (key, "读数相同 ✓" if same else "★★不同",
                                  verdict))
        print("      HEAD : %s" % head_reads.get(key))
        print("      工作 : %s" % work)

    result = {
        "批次": 854,
        "说明": "回归清单里新出现的红 ⟹ ⟹ 定点对照（换回 HEAD 再跑）",
        "结果": out_rows,
    }
    (ROOT / "docs/research/liblib-canvas-batch854-2026-10-01/raw/attrib-45-72-75-79.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
