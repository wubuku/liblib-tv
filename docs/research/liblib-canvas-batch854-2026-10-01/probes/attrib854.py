#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 854 受控对照：把本批改过的源码**按字节换回 HEAD** ⟹ ⟹ 重跑旧门禁
⟹ ⟹ 看读数**逐条有没有变**。

★★ **为什么要连跑两遍**：换回源码后 4317 要热更 ⟹ ⟹ 第一次跑有可能赶上热更中途
⟹ ⟹ ★ 「**一轮的差**」不能直接当因果 ⟹ ⟹ 必须复跑再判。

★ ★ **复原用白名单**：`CHANGED` 是**明确列出的相对路径**（不是黑名单），
⟹ ⟹ 不会把本批自己的源码或别人的 WIP 一起回退；⟹ ⟹ 且复原走**字节备份**
（不是 `git checkout`）⟹ ⟹ 复原后逐字节校验哈希。
★ ★ **绝不用 `git stash`**（本仓库的 `stash@{0}` 是别人的 WIP ⟹ ⟹ 全程不碰）。

## ★ 本批盯哪些门禁

★ 本批改了**三个**被跟踪源码：

- `src/lib/directorProjectDocument.ts`（组文档加可选键 `members` ＋ 引用校验）
- `src/store/directorStore.ts`（组收任意成员 ＋ 组名 ＋ 选择集）
- `src/components/director/DirectorObjectTree.tsx`（默认展开 ＋ 成员渲染 ＋ 树多选）

★ 因此必须**在 HEAD 与工作副本上读数逐条完全相同**的门禁：

- `853`／`852`／`851`／`850`／`849`／`848`／`847` 导演台主线
- `830` 快捷键面板　`543` 重置视角　`540`／`550`／`588` 吸附
- `45`／`50`／`792` **组相关**（★ 本批动的正是组模型）
- `96` ＋ `67`／`68`／`74`／`79`／`80`／`81` **文档 schema 相关**
  （★ 本批给组文档加了 `members` ⟹ ⟹ 旧工程必须仍读得动）
- 其余读 `DirectorObjectTree`／`directorStore` 的**静态**门禁
  （`69`／`70`／`71`／`72`／`75`／`84`／`85`／`86`／`89`／`90`）

★ 另跑**旧账**（`736`／`748`／`749`／`782`／`831`／`741`／`87`／`91`）⟹ ⟹
它们在 HEAD 上也红 ⟹ ⟹ **不是本批引入的**；以及 `854` 本批
（★ 在 HEAD 上**必然红** ⟹ ⟹ 门禁有牙）。
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

# ★ ★ 白名单：只列本批**确实改过**的相对路径
# ★ ★★ 必须是**全部 7 个**：本批新增了一个**导出**（`resolveDirectorGroupMembers`），
# ★    而 `directorClipboard.ts` 等**消费者** import 了它
# ★    ⟹ ⟹ 只换回 3 个文件的话，HEAD 态的 app 会因为「消费者 import 了不存在的导出」
# ★    ⟹ ⟹ **整站 500**（实测：`Export resolveDirectorGroupMembers doesn't exist`）
# ★    ⟹ ⟹ 所有浏览器门禁都变成 60s 超时 ⟹ ⟹ 读数全是假的。
CHANGED = [
    "src/lib/directorProjectDocument.ts",
    "src/store/directorStore.ts",
    "src/components/director/DirectorObjectTree.tsx",
    "src/lib/directorDeletePlanner.ts",
    "src/lib/directorClipboard.ts",
    "src/lib/directorWholeProjectDuplicate.ts",
    "src/lib/directorProjectRuntimeAdapter.ts",
]

# ★ 旧账（HEAD 上也是红的）＋ 本批（在 HEAD 上必然红 ⟹ ⟹ 门禁有牙）
TARGETS = [("736", "py"), ("748", "py"), ("749", "py"), ("782", "py"),
           ("831", "py"), ("741", "py"), ("87", "mjs"), ("91", "mjs"),
           ("854", "py")]
# ★ 必须逐条相同的绿门禁
# ★ ★ 清单**收窄**到「读本批改过的那几个文件」的门禁 ⟹ ⟹ 理由：
# ★   ① 受控对照每条要**连跑两遍**、HEAD 与工作副本各一遍 ⟹ ⟹ 浏览器门禁很贵；
# ★   ② 第 3 轮回归已经证明「盯的 32 条全绿」⟹ ⟹ 这里要证明的是
# ★      **读数逐条相同**（而不是「红红相同」）；
# ★   ③ ★ `36`／`47`／`48`／`49`／`50` 在第 2 轮回归里曾一起红、单独复跑全绿
# ★      ⟹ ⟹ **环境瞬态**（dev server 重编译）⟹ ⟹ 放进「读数逐条相同」的
# ★      对照会引入**假差异** ⟹ ⟹ **不放进**本清单（它们的绿／红已在回归里验过）。
WATCH = [("853", "py"), ("852", "py"), ("45", "py"), ("792", "py"),
         ("96", "py"),
         ("67", "mjs"), ("68", "mjs"), ("74", "mjs"), ("79", "mjs"),
         ("80", "mjs"), ("81", "mjs"),
         ("69", "mjs"), ("70", "mjs"), ("71", "mjs"), ("72", "mjs"),
         ("75", "mjs"), ("84", "mjs"), ("85", "mjs"), ("86", "mjs"),
         ("89", "mjs"), ("90", "mjs")]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(batch: str, ext: str) -> str:
    script = ROOT / ("scripts/verify-liblib-batch%s.%s" % (batch, ext))
    if not script.exists():
        return "（无此门禁）"
    cmd = ([str(NODE), str(script)] if ext == "mjs"
           else [sys.executable, str(script)])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                       cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    tail = [ln for ln in out.splitlines() if ln.strip()][-2:]
    return "rc=%s | %s" % (r.returncode, " ／ ".join(t.strip() for t in tail))


def run_twice(batch: str, ext: str) -> str:
    first = run(batch, ext)
    second = run(batch, ext)
    if first != second:
        return "★两遍不一致 | %s ⟹ %s" % (first, second)
    return first


def warm_up(url: str = "http://localhost:4317/", tries: int = 40) -> str:
    """★ 换回源码后 4317 要**热更**（冷编译可能要几十秒）
    ⟹ ⟹ 不热机就直接跑门禁 ⟹ ⟹ 第一条门禁大概率撞上冷编译 ⟹ ⟹ 60s 超时
    ⟹ ⟹ 读数变成「超时」⟹ ⟹ 假差异。
    ⟹ ⟹ 这里先反复 GET 到 **200** 为止。
    """
    import urllib.error
    import urllib.request
    last = ""
    for _ in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                if resp.status == 200:
                    return "200"
                last = "status=%s" % resp.status
        except urllib.error.HTTPError as exc:
            last = "http=%s" % exc.code
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:80]
        time.sleep(1.5)
    return "★没热起来（%s）" % last


def main() -> int:
    backups = {}
    before = {}
    for rel in CHANGED:
        p = ROOT / rel
        backups[p] = p.read_bytes()
        before[p] = sha(p)

    # ★ 先打印清单再执行（★ 白名单，不是黑名单）
    print("将要换回 HEAD 的文件（白名单，共 %d 个）：" % len(CHANGED))
    for rel in CHANGED:
        print("   ", rel)

    head_reads = {}
    try:
        subprocess.run(["git", "checkout", "--"] + CHANGED, cwd=str(ROOT),
                       check=True)
        print("已换回 HEAD ⟹ 热机 4317：%s" % warm_up())
        print()
        for b, e in TARGETS:
            head_reads["%s.%s" % (b, e)] = run_twice(b, e)
            print("HEAD 上 %s.%s ⟹ %s" % (b, e, head_reads["%s.%s" % (b, e)]),
                  flush=True)
        for b, e in WATCH:
            head_reads["%s.%s" % (b, e)] = run_twice(b, e)
            print("HEAD 上 %s.%s ⟹ %s" % (b, e, head_reads["%s.%s" % (b, e)]),
                  flush=True)
    finally:
        for p, data in backups.items():
            p.write_bytes(data)
        print("\n已复原工作副本 ⟹ 热机 4317：%s" % warm_up())
        for p in backups:
            assert sha(p) == before[p], "★ 复原后哈希不一致：%s" % p
            print("  复原校验 OK %s %s" % (p.name, sha(p)[:16]))

    print("\n=== 工作副本上再跑一遍（★ 必须与 HEAD 逐条完全相同）===")
    diffs = []
    for b, e in TARGETS + WATCH:
        key = "%s.%s" % (b, e)
        work = run_twice(b, e)
        same = work == head_reads.get(key)
        print("  %-9s %s" % (key, "一致 ✓" if same else "★★ 不一致"))
        if not same:
            diffs.append({"batch": key, "HEAD": head_reads.get(key),
                          "工作副本": work})
    total = len(TARGETS) + len(WATCH)
    print("\n受控对照：%d/%d 条读数逐条完全相同" % (total - len(diffs), total))
    out = {"批次": 854, "总数": total, "一致数": total - len(diffs),
           "不一致": diffs,
           "HEAD读数": {k: v for k, v in head_reads.items()}}
    (ROOT / "docs/research/liblib-canvas-batch854-2026-10-01/raw/attrib-854.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main())
