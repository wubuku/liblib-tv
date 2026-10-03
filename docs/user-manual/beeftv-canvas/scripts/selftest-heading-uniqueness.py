#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十九道闸（verify-heading-uniqueness.py）的反向验证。

  能抓 3 条：
    1) 页内出现同名标题 → 必须报，并报出**两处行号**
    2) 标题层级跳级（h2 直接到 h4）→ 必须报
    3) 页内有两个 H1 → 必须报
  不误伤 2 条：
    4) **同名的容器标题必须放行** —— 本批量到 `30-concepts.md` 有两处
       `::: warning 这张表是可以被推翻的`，读完原文确认是**有意的措辞复用**
       （两张不同的表各自需要这句告诫），而容器标题渲染成
       `<p class="custom-block-title">`、**不生成锚点**，撞不了。
       **把有意的复用报成缺陷就是判据过宽**——这一条是本闸最要紧的不误伤用例。
    5) 围栏代码块里的 `#` 注释必须放行（那是代码，不是标题）
  基线 1 条。

⚠️ 注入一律用 `assert` 钉死锚点，锚点失配即判**作废**（VOID++），作废让退出码非零
（Batch 225 实测过漏掉 `VOID++` 的后果：用例静默消失、闸门在干净树上跑绿、报告却写 ✓）。
本闸不读上游，临时树只需 `scripts/` + 全部正文页。
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-heading-uniqueness.py")

PASS = FAIL = VOID = 0


def build_tree():
    tmp = tempfile.mkdtemp(prefix="beef-hu-selftest.")
    os.makedirs(os.path.join(tmp, "scripts"))
    os.makedirs(os.path.join(tmp, "10-tasks"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-heading-uniqueness.py"))
    # **Batch 248：闸 29 开始 import `headingkey`。**
    # **不搬它的话临时目录 import 失败、每一例都会红，而 `build-site.sh` 仍然全绿**
    # （闸 17 守的就是这件事，它会在本批的构建里当场报出来）。
    shutil.copy(os.path.join(HERE, "headingkey.py"),
                os.path.join(tmp, "scripts", "headingkey.py"))
    for f in ("00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md"):
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(tmp, f))
    for name in sorted(os.listdir(os.path.join(ROOT, "10-tasks"))):
        if name.endswith(".md"):
            shutil.copy(os.path.join(ROOT, "10-tasks", name),
                        os.path.join(tmp, "10-tasks", name))
    return tmp


def run(desc, want_sub, want_rc=1, expect_fail=True, transform=None, page="20-reference.md"):
    global PASS, FAIL, VOID
    tmp = build_tree()
    try:
        target = os.path.join(tmp, page)
        if transform is not None:
            base = open(target, encoding="utf-8").read()
            try:
                text = transform(base)
            except AssertionError as exc:
                print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
                VOID += 1
                return
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(text)
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-heading-uniqueness.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际：" % (desc, r.returncode, want_rc))
            print("      " + out.strip()[:300].replace("\n", "\n      "))
            FAIL += 1
        elif want_sub and want_sub not in out:
            print("  ✗ %s：输出里没有 [%s]；实际：" % (desc, want_sub))
            print("      " + out.strip()[:300].replace("\n", "\n      "))
            FAIL += 1
        else:
            verb = "正确报出" if expect_fail else "**未误报**"
            print("  ✓ %s：闸门%s [%s]（退出码 %d）" % (desc, verb, want_sub, r.returncode))
            PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_dup_heading(base):
    old = "## 取证基线"
    assert base.count(old) == 1, f"锚点不唯一: {old}（出现 {base.count(old)} 次）"
    return base.replace(old, old + "\n\n## 取证基线", 1)


def t_level_jump(base):
    old = "## 主要页面路由"
    assert base.count(old) == 1, f"锚点不唯一: {old}"
    return base.replace(old, "#### 主要页面路由", 1)


def t_two_h1(base):
    first = base.split("\n")[0]
    assert first.startswith("# "), f"前提失配：首行不是 H1: {first[:40]}"
    return base.replace(first, first + "\n\n# 又一个 H1", 1)


def t_dup_container_title(base):
    """**什么都不改**：保留 `30-concepts.md` 里那两处同名的容器标题。

    本批读到原文才判定它是**有意的措辞复用**（两张不同的表各自需要
    「这张表是可以被推翻的」），而容器标题不生成锚点。**闸门若把它报成缺陷，
    就会有人去改掉一句本来正确的提醒。**
    """
    return base


def t_fenced_hash(base):
    """围栏代码块里的 `# 注释` 不是标题。"""
    marker = "## 取证基线"
    assert marker in base, f"锚点未命中: {marker}"
    return base.replace(marker, "```\n# 这不是标题，是代码注释\n# 也不是\n```\n\n" + marker, 1)


def t_closing_hashes(base):
    """能抓：`## 相关页面 ##` 与 `## 相关页面`。

    **真渲染器把它们算同名**（slug 去重成 `-1`），而改前的判据拿**源码原始行**当键，
    看到的是「相关页面 ##」与「相关页面」——**判据问的键不是它声称在问的那件事**。
    改前实测 rc=0（静默）。
    """
    marker = "## 主要页面路由"
    assert base.count(marker) == 1, f"锚点不唯一: {marker}"
    return base.replace(marker, "## 主要页面路由 ##\n\n" + marker, 1)


def t_link_in_heading(base):
    """能抓：`## [相关页面](x.md)` 与 `## 相关页面`——真渲染器同样算同名。"""
    marker = "## 主要页面路由"
    assert base.count(marker) == 1, f"锚点不唯一: {marker}"
    return base.replace(marker, "## [主要页面路由](x.md)\n\n" + marker, 1)


def t_fullwidth_space(base):
    """不误伤：井号后是**全角空格**时，那一行不是标题。

    **实测改前会凭空造出两处缺陷**：两个 `#　全角空格标题` 被判成两个同名 h1，
    **而真渲染器给出的是零个标题**——页面上一个标题都没有。
    Python 的 `\s` 匹配全角空格，CommonMark 的 ATX 开头只认 ASCII 空格与制表符。
    """
    marker = "## 主要页面路由"
    assert base.count(marker) == 1, f"锚点不唯一: {marker}"
    return base.replace(marker, "#\u3000全角空格标题\n\n#\u3000全角空格标题\n\n" + marker, 1)


def main():
    global PASS, FAIL, VOID
    print("=== 能抓 ===")
    run("1) 页内同名标题（必须报，并给两处行号）", "同名", want_rc=1, transform=t_dup_heading)
    run("2) 标题层级跳级 h2→h4（必须报）", "跳到 h4", want_rc=1, transform=t_level_jump)
    run("3) 页内两个 H1（必须报）", "个 H1", want_rc=1, transform=t_two_h1)
    run("3b) ATX 尾部闭合井号与同名标题并存（真渲染器算同名，必须报）",
        "同名", want_rc=1, transform=t_closing_hashes)
    run("3c) 标题里带链接与同名标题并存（真渲染器算同名，必须报）",
        "同名", want_rc=1, transform=t_link_in_heading)

    print("=== 不误伤 ===")
    run("4) 同名的容器标题（本批判定为有意复用，必须放行）", "无同名标题",
        want_rc=0, expect_fail=False, transform=t_dup_container_title, page="30-concepts.md")
    run("5) 围栏代码块里的 # 注释（必须放行）", "无同名标题",
        want_rc=0, expect_fail=False, transform=t_fenced_hash)
    run("5b) 井号后是全角空格（真渲染器：零个标题，必须放行）", "无同名标题",
        want_rc=0, expect_fail=False, transform=t_fullwidth_space)

    print("=== 基线：真实手册应当通过 ===")
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ 基线：真实手册通过（%s）" % r.stdout.strip().split("\n")[0][:70])
        PASS += 1
    else:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, r.stdout.strip()[:200]))
        FAIL += 1

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
