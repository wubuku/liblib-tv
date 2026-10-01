#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第一道闸（`verify-deadlinks.py`）的反向验证——**它是二十来个 batch 之后第一次有反验**。

原判据内联在 `build-site.sh` 的 heredoc 里，因此结构上无法被验证。Batch 168 抽成独立脚本，
顺带修掉了内联写法的老毛病：`python3 … 2>/dev/null || true` 一旦失败，
计数取到 0，于是输出「站内链接全部可达」——**工具失败被当成没有问题**。
抽出来之后这类失败一律走三段退出码（`0` 无死链 / `1` 有死链 / `2` 未能核对）。

  能抓 4：
    1) href 指向不存在的文件 → rc=1
    2) 目录链接但目录下没有 index.html → rc=1
    3) dist 不存在 → **rc=2**（不是 0）
    4) dist 存在却一个 html 都没有 → **rc=2**（不是 0）
  不误伤 3：
    5) 外链 / mailto: / 页内锚点 / **相对**目录索引（`guide/`）→ 必须通过
    6) **绝对**目录索引（`/guide/`）→ 必须通过
    7) 绝对目录链接但该目录没有 index.html（`/sub/`）→ 必须报 rc=1

**为什么 5/6/7 三条缺一不可**（Batch 168 拿数据量出来的）：
旧逻辑先 `normpath` 再判结尾斜杠，而 `normpath` **会把结尾斜杠吃掉**——
于是**相对**目录链接 `guide/` 被当成「名叫 guide 的文件」去找，**误报成死链**；
而**绝对** href `/guide/` 走 `lstrip("/")`、**不经 normpath**，结尾斜杠还在，
**旧逻辑本来就判对**。**真缺陷不是「分支是死代码」，而是两种 href 形态行为不一致。**
（我第一版的说法过头了，是这条对照把它纠正回来的。）
所以 6/7 要单独钉住**绝对形态**：那是旧逻辑本来就对的地方，
**改动它就可能把对的地方弄坏**——这正是「不误伤」那一半的意义。
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "verify-deadlinks.py")

PASS = VOID = FAIL = 0

PAGE = '<html><body><a href="{h}">x</a></body></html>'


def build(pages, dirs=(), make_dist=True):
    """搭一个最小产物目录。pages: {相对路径: [href, …]}；dirs: 需要建空目录的相对路径。"""
    tmp = tempfile.mkdtemp(prefix="beef-deadlink-selftest.")
    os.makedirs(os.path.join(tmp, "scripts"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-deadlinks.py"))
    if make_dist:
        dist = os.path.join(tmp, ".vitepress", "dist")
        os.makedirs(dist, exist_ok=True)
        for rel, hrefs in pages.items():
            path = os.path.join(dist, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                for h in hrefs:
                    fh.write(PAGE.format(h=h) + "\n")
        for d in dirs:
            os.makedirs(os.path.join(dist, d), exist_ok=True)
    return tmp


def run(desc, expect_fail=True, want_rc=1, want=None, **kw):
    global PASS, VOID, FAIL
    tmp = build(**kw)
    try:
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-deadlinks.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if expect_fail and r.returncode != want_rc:
            print("  ✗ %s：退出码 %d 期望 %d；实际：%s" % (desc, r.returncode, want_rc, out.strip()[-140:]))
            FAIL += 1
        elif expect_fail and want and want not in out:
            print("  ✗ %s：输出里找不到 [%s]；实际：%s" % (desc, want, out.strip()[-140:])); FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤，rc=%d）：%s" % (desc, r.returncode, out.strip()[-180:]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc); PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    run("1) href 指向不存在的文件（必须报 rc=1）", want_rc=1,
        pages={"index.html": ["guide/missing.html"]})
    run("2) 目录链接但该目录没有 index.html（必须报 rc=1）", want_rc=1,
        pages={"index.html": ["sub/"]}, dirs=["sub"])
    run("3) dist 不存在（必须 rc=2 未能核对，不是 0）", want_rc=2,
        want="未能进行", pages={}, make_dist=False)
    run("4) dist 存在却一个 html 都没有（必须 rc=2，不能静默通过）", want_rc=2,
        want="一个 html 都没有", pages={"notes.txt": []}, make_dist=True)
    run("5) 不误伤：外链 / mailto / 页内锚点 / **相对**目录索引 guide/（必须放行）", expect_fail=False,
        pages={
            "index.html": ["https://example.com/x", "mailto:a@b.c", "#section",
                           "guide/", "guide/index.html"],
            "guide/index.html": ["../index.html"],
        }, dirs=["guide"])
    # 6/7 钉住**绝对**形态：旧逻辑在这条路径上本来就判对，改动不得把它弄坏。
    # 缺了这两条，修「相对目录链接」时很容易顺手把绝对的也改错，而**误伤不会自己报警**。
    run("6) 不误伤：**绝对**目录索引 /guide/（必须放行）", expect_fail=False,
        pages={"index.html": ["/guide/"], "guide/index.html": []}, dirs=["guide"])
    run("7) **绝对**目录链接但该目录没有 index.html（必须报 rc=1）", want_rc=1,
        pages={"index.html": ["/sub/"]}, dirs=["sub"])

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
