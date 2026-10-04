#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十五道闸：`captured_version` 的**依据**有没有被核过（Batch 241 新增）。

## 它的由来：一句写在文件头里、从来没有被兑现过的规定

`screenshots/manifest.yml` 的文件头自己写着：

> `captured_version` = **拍这张图时前端 dev server 跑的是哪个版本**……
> ⚠️ 本字段的值**不是从图上读出来的**，而是依据 `task-inventory.yml` 里
> **同期运行时走查记录的版本声明**填的；改版本号前请先核那条记录，别只改这里。

**Batch 241 照着这句话去核了一遍，结果是 67 张里 28 张的登记与事实不符。**

两条互相独立、结论完全一致的推导：

  ① **提交区间**——本仓的提交信息自己就写着版本：
     `570d6579`「batch 26 — director workbench runtime walkthrough **on v1.6.13**,
     screenshots 30-36」、`04b292aa`「**v1.6.6** 构建重摄视频生成 composer」、
     `35142b38`「**v1.6.6** 补拍——规格二维弹层/浅色模式/项目列表三图入册」、
     `93698b77`「batch 51 — vite restart reveals **v1.6.14** badge」。

  ② **日期时间线**——`AUDIT.md` 环境记录九/十写死了工作树的换版时刻：
     Batch 26（2026-09-29）`5b1c060`(**v1.6.6**) → `69fbf9b`(**v1.6.13**)，
     Batch 27（2026-09-30）→ `852961a`(**v1.6.14**)。
     **而 manifest 里有 28 张拍摄日期是 2026-09-29 的图登记着 v1.6.14**——
     那个版本当天还不存在。

**两条推导给出的 28 条完全相同，而 39 条相符的没有一条例外。**
**错的方向是「把更旧的图说成更新的」——那正是这个字段被建立起来要防的那件事**
（Batch 177 的原话：「一张拍于 v1.6.21 的截图，在 v1.6.22 里对应的界面已被上游删掉，
而 manifest 里没有任何东西能让人看出这件事」）。

## 三个方向

  方向一：**`captured_version` 必须等于「最后一次改动该 PNG 的那次提交」所落的版本区间。**
    区间由一个锚点提交切出（`SPAN_ANCHOR`）：锚点之前 = `SPAN_BEFORE`，
    锚点本身 = `SPAN_ANCHOR_VER`，锚点之后 = `SPAN_AFTER`。

  方向二：**锚点自检**。锚点提交必须存在，**且它的提交信息里必须含 `SPAN_ANCHOR_VER`**。
    这不是形式检查——**锚点提交信息里的版本号就是本闸唯一的书面依据**；
    依据不成立时本闸必须 rc=2，**不能安静地按一张失效的区间表继续判**
    （纪律 101：解析器退化必须表现为失败，而不是通过）。

  方向三：**账本交叉核对 + 免检表**。账本里该任务的走查记录声明了版本时，
    登记必须与它相符；不相符的**必须**登记进 `OFF_TASK`，
    **而每条登记必须写明产出那张图的提交，且那个提交必须仍然是该图最后一次被改动的提交**
    ——登记过期就是免死金牌（与闸 16/23 的 `STALE`/`DRIFT` 反向检查同一条纪律）。

  方向四（Batch 244）：**manifest 里出现的每一个 `captured_version`，区间表都必须覆盖。**
    **这条管的就是上面那条能力上限。** 方向二守的是**锚点那一端**——
    锚点提交不见了、或者它的信息里没有那个版本号，都会 rc=2；
    **而「末端」原来是无人管的**：工作树升到 v1.6.22、有人在新版本上重拍了几张图，
    manifest 里就会出现 `v1.6.22`，**而区间表的三段里没有它**——
    方向一于是把那些图一律判成「落在 v1.6.14 区间」，
    **报出来的诊断是错的，而修法（改登记）会把数据改成错的**。
    **本方向零外部依赖**：它只读 manifest 自己的 `captured_version` 集合
    与 `SPAN_*` 三个常量，**不需要 BeefTV 源码、不需要 git 历史之外的任何东西**。
    **它要挡的两种情形都报**：版本不在表里 = 区间表该加一段，
    **或者那条登记本身写错了**——**本闸不判断是哪一种，所以 rc=2 而不是替人选一个。**

## 能力上限（如实写在这里，不装作覆盖了）

  · **「最后一次字节变更」不等于「最后一次拍摄」。** 若同一次走查重新导出得到
    **逐字节相同**的结果，git 不会留下记录，本闸无从知道——**方向是保守的**
    （把更新的图说旧，不会把旧的图说新）。
  · **`SPAN_AFTER` 成立于「工作树自 Batch 27 起一直停在 v1.6.14」这一事实。**
    **工作树一旦升级，这张区间表必须同步更新**，否则本闸会把新拍的图一律说成 v1.6.14。
    **Batch 244 补上了方向四来管这件事**（见下）——
    **本文件原先在能力上限里写着「方向二发现不了末端该换版本了」，那句话就是本批的选题**：
    **一个已知缺口写在文件头里、被反复引用、却一直没有人动。**
  · **本闸只核登记与提交历史的自洽，不核「这张图拍的时候界面是不是长这样」。**
    后者是闸 10/23 的范围。

退出码：0 全部自洽；1 有不自洽；2 未能核对（读不到 manifest / 抽不出条目 /
 目录不在 git 仓库里 / 锚点提交不存在或其提交信息里没有那个版本号）。
"""

import os
import re
import subprocess
import sys
import shotmanifest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")
LEDGER = os.path.join(ROOT, "task-inventory.yml")
SHOTS_REL = "screenshots"

# ── 版本区间表：一个锚点切三段 ──────────────────────────────────────
#: 锚点提交：**Batch 26**（导演台解禁升级轮）。依据两处，都在本仓里：
#:   · `AUDIT.md` 环境记录九「工作树升级：BeefTV 检出 detached 5b1c060(v1.6.6)→69fbf9b(v1.6.13)」；
#:   · 该提交自己的信息「batch 26 — director workbench runtime walkthrough on v1.6.13,
#:     three director tasks verified (18/7), screenshots 30-36」。
#: 环境变量只为反验留（临时仓里没有这个 hash），生产路径不读它。
SPAN_ANCHOR = os.environ.get("BEEFTV_SHOT_SPAN_ANCHOR", "570d6579")
SPAN_BEFORE = "v1.6.6"     # Batch 26 之前：工作树 5b1c060
SPAN_ANCHOR_VER = "v1.6.13"  # Batch 26 当批：工作树 69fbf9b
SPAN_AFTER = "v1.6.14"     # Batch 27 起：工作树 852961a，至今未再换

# ── 免检表：产出那张图的走查**没有**登记在账本里的情形 ──────────────
# 每条必须写清：产出该图的提交（反向核：它必须仍是该图最后一次被改动的提交）
# 与一句话理由。**写不出提交号的条目不许进来**——那等于一张没有依据的免检证。
OFF_TASK = {
    "screenshots/24-video-process-menu.png": {
        "commit": "761106b9",
        "why": "账本 timeline-export 的走查是 Batch 32（多轨时间线「导出成片」），"
               "而这张图是 09-29「补充走查（真实上传轮）」拍的（提交 761106b9），"
               "**那次走查从未登记进账本**。方向一据提交区间给出 v1.6.6，"
               "方向三据账本给出 v1.6.14——**两条推导指向不同的走查，登记以产出它的那次为准**。",
    },
}

VER_RE = re.compile(r"v1\.6\.(\d+)")


def git(*args):
    p = subprocess.run(("git",) + args, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def parse_manifest():
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    out = []
    for name, block in shotmanifest.blocks(text):
        hit = re.search(r"^\s+captured_version:\s*'?([^'\n]+)'?\s*$", block, re.M)
        out.append({"file": name, "ver": hit.group(1).strip() if hit else None,
                    "task": (re.search(r"^\s+task_id:\s*(\S+)", block, re.M) or [None, None])[1]})
    return out


def ledger_versions():
    """任务 id -> 该任务在账本走查记录里声明的版本（只取唯一值，多值视为「核不了」）。"""
    try:
        with open(LEDGER, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    out = {}
    for m in re.finditer(r"^  - id:\s*(\S+)\n(.*?)(?=^  - id:|\Z)", text, re.S | re.M):
        note = ""
        for key in ("review_note", "finding"):
            mm = re.search(r"^\s{4}" + key + r":(.*?)(?=^\s{4}\w+:|\Z)", m.group(2), re.S | re.M)
            if mm:
                note += " ".join(mm.group(1).split()) + " "
        vs = sorted({v for v in VER_RE.findall(note)}, key=int)
        out[m.group(1)] = ("v1.6." + vs[0]) if len(vs) == 1 else None
    return out


def last_touch_map():
    """{截图相对路径: 最后一次改动它的提交}。**一次 `git log` 走完，不逐张起进程。**

    `git log` 默认按时间倒序输出，所以某个文件**第一次出现**的那次提交就是最后改动它的那次。
    """
    rc, out, _ = git("log", "--format=%H", "--name-only", "--", SHOTS_REL)
    if rc != 0:
        return None
    seen, cur = {}, None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            cur = line
        elif line.startswith("screenshots/") and cur and line not in seen:
            seen[line] = cur
    return seen


def main():
    entries = parse_manifest()
    if not entries:
        print("[skip] 读不到 manifest.yml 或一条截图登记都没有——"
              "「一个都没检查」与「全部都合格」在退出码上必须不同开")
        return 2

    rc, top, err = git("rev-parse", "--show-toplevel")
    if rc != 0:
        print("[skip] 手册目录不在 git 仓库里，本闸无法从提交历史推出拍摄版本："
              + (err.strip().splitlines() or [""])[0])
        return 2

    # —— 方向二：锚点自检（先做，它不成立时后面两个方向都无从谈起）——
    rc, out, _ = git("rev-parse", "--verify", SPAN_ANCHOR + "^{commit}")
    if rc != 0:
        print(f"[skip] 锚点提交 {SPAN_ANCHOR} 在本仓不存在——版本区间表失效，"
              "**不得按一张对不上的表继续判**")
        return 2
    anchor_full = out.strip()
    rc, subj, _ = git("show", "-s", "--format=%s", anchor_full)
    if SPAN_ANCHOR_VER not in subj:
        print(f"[skip] 锚点提交 {SPAN_ANCHOR} 的提交信息里没有 {SPAN_ANCHOR_VER}：\n"
              f"       {subj.strip()}\n"
              "       **那是本闸唯一的书面依据**；依据不成立时必须 rc=2，"
              "不能安静地继续判")
        return 2

    rc, ancestors, _ = git("rev-list", anchor_full)
    anc = set(ancestors.split())

    lmap = last_touch_map()
    if lmap is None:
        print("[skip] 读不到截图目录的提交历史，本闸未能核对")
        return 2
    lt = {}
    for e in entries:
        c = lmap.get(e["file"], "")
        if not c:  # 一次遍历没覆盖到（例如路径带子目录），逐张补一次
            rc, out, _ = git("log", "-1", "--format=%H", "--", e["file"])
            c = out.strip() if rc == 0 else ""
        lt[e["file"]] = c

    # —— 方向四：区间表必须覆盖 manifest 里出现的每一个版本 ——
    # **放在方向一之前**：表一旦过期，方向一报出来的「落在 v1.6.14 区间」是**错的诊断**，
    # **照着它去改登记会把数据改成错的**。所以先问「这张表还成立吗」，再问「每张图对不对」。
    known = {SPAN_BEFORE, SPAN_ANCHOR_VER, SPAN_AFTER}
    used = {}
    for e in entries:
        used[e["ver"]] = used.get(e["ver"], 0) + 1
    unknown = sorted(v for v in used if v not in known)
    if unknown:
        print(f"[skip] manifest 里出现了区间表没有覆盖的版本 {unknown}"
              f"（表覆盖 {sorted(known)}）——**区间表的末端已经过期**，"
              f"而方向一此时会把这些图一律判成「落在 {SPAN_AFTER} 区间」，"
              f"**那是一个错的诊断，照着改登记会把数据改成错的**。"
              f"\n       出现次数：" + "、".join(f"{v} × {used[v]}" for v in unknown))
        print("       两种可能，本闸不替人挑：**要么**取证工作树已经升级、"
              f"这张表该加一段；**要么**某条登记本身写错了。"
              f"\n       确认真相后：表该加就加表（并在本文件里注明新一段的依据），"
              f"登记该改就改登记。")
        return 2

    def span_of(commit):
        if not commit:
            return None
        if commit == anchor_full:
            return SPAN_ANCHOR_VER
        return SPAN_BEFORE if commit in anc else SPAN_AFTER

    problems, undecidable = [], []
    for e in entries:
        c = lt[e["file"]]
        if not c:
            undecidable.append(f"{e['file']}（git 里查不到改动过它的提交）")
            continue
        want = span_of(c)
        if e["ver"] != want:
            problems.append(
                f"方向一：{e['file']} 登记 {e['ver']}，而它最后一次被改动的提交 "
                f"{c[:8]} 落在 **{want}** 区间"
                f"　→ 要么登记写错了，要么那张图被重拍过而登记没跟着改；"
                f"**「把更旧的图说成更新的」正是这个字段要防的那件事**")
    if undecidable:
        print("  [未能核对] 以下截图取不到提交历史：")
        for u in undecidable:
            print("    · " + u)
        return 2

    # —— 方向三：账本交叉核对 ——
    led = ledger_versions()
    if led is None:
        print("[skip] 读不到 task-inventory.yml，方向三本轮未能核对")
        return 2
    decidable = agree = undeclared = offtask_n = unknown_task = 0
    for e in entries:
        if e["file"] in OFF_TASK:
            offtask_n += 1
            continue
        if e["task"] not in led:
            unknown_task += 1  # 账本里查无此任务 id（**那是另一类缺口，不在本闸范围**）
            continue
        lv = led[e["task"]]
        if lv is None:
            undeclared += 1
            continue
        decidable += 1
        if lv == e["ver"]:
            agree += 1
        else:
            problems.append(
                f"方向三：{e['file']} 登记 {e['ver']}，而账本 {e['task']} 的走查记录"
                f"声明的是 {lv}"
                f"　→ 要么登记错了，要么**产出这张图的那次走查根本没登记在账本里**；"
                f"后者要登记进 OFF_TASK 并写明产出该图的提交")
    # 免检表反向核：登记的提交必须仍然是该图最后一次被改动的提交
    for f, info in OFF_TASK.items():
        if f not in lt:            # 这张图已经不在 manifest 里 → 登记失去了对象
            problems.append(
                f"方向三：OFF_TASK 登记了 {f}，而 manifest 里已经没有这张图"
                f"　→ 免检登记必须跟着它的对象一起消失")
            continue
        c = lt.get(f, "")
        if c[:8] != info["commit"]:
            problems.append(
                f"方向三：OFF_TASK 给 {f} 登的产出提交是 {info['commit']}，"
                f"而它最后一次被改动的提交是 {(c[:8] or '（查不到）')}"
                f"　→ 登记过期了：要么那张图已经被重拍过，要么登记写错。"
                f"**免检表只减不增就会变成一张没人敢碰的清单**")

    counts = {}
    for e in entries:
        counts[e["ver"]] = counts.get(e["ver"], 0) + 1
    top_ver = max(counts, key=lambda k: counts[k])
    older = len(entries) - counts[top_ver]
    undeclared_n = len(entries) - decidable - offtask_n - unknown_task
    assert undeclared == undeclared_n, (f"账本里无版本声明的计数对不上："
                                       f"{undeclared} ≠ {undeclared_n}")
    print(f"  版本区间核对：{len(entries) - len(problems)} / {len(entries)} 张"
          f"的登记与提交历史落在同一区间"
          f"（锚点 {SPAN_ANCHOR} = {SPAN_ANCHOR_VER}，之前 {SPAN_BEFORE}，之后 {SPAN_AFTER}）")
    print(f"  账本交叉核对：可核 {decidable} 张、相符 {agree} 张；"
          f"另有 {undeclared_n} 张归属任务在账本里**没有版本声明**、"
          f"{offtask_n} 张登记在 OFF_TASK、{unknown_task} 张在账本里查无此任务"
          f"　→ **「账本没写」不等于「核对过没问题」**")
    print(f"  分布：{dict(sorted(counts.items()))}　→ 众数 {top_ver}，"
          f"比它早的 {older} 张（20-reference.md 的那句声明由闸 16 方向四负责对账）")
    if problems:
        print("  ✗ 截图拍摄版本与依据不自洽 %d 处：" % len(problems))
        for p in problems:
            print("    · " + p)
        return 1
    print("截图拍摄版本依据核对通过：%d 张登记的拍摄版本都落在其最后一次被改动的"
          "提交所处的版本区间；账本能核的 %d 张全部相符" % (len(entries), decidable))
    return 0


if __name__ == "__main__":
    sys.exit(main())
