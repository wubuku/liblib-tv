#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版对账：**同一棵手册树 × 两个上游 ref，逐道闸对比**。

**它不是闸，是工具**——理由写在这里，免得下一个人把它接进构建：
上游每发一版它就会红一批，**而「上游动了」不是本手册的缺陷**；
**一条天天报红的闸会把人训练成忽略它**（纪律 356②① 的同一个道理）。
**用法是：升版之前跑一遍，拿到一份带条数的工作清单，
而不是「上游改了 274 个文件」这句话。**

**为什么零新判据就能做**：`scripts/baseline.py` 的 `resolve_ref()` 已经让
`BEEFTV_REF` 环境变量优先于手册声明的基线（那是 Batch 163 为反向验证留的）。
**于是「把闸指向 v1.7.3」不需要改任何一行判据。**

**为什么不用登记表指明要跑哪些闸**（纪律 242）：
**闸的集合是扫出来的**——`verify-*.py` 里出现 `resolve_ref(` / `module_ref(` /
`BEEFTV_REF` / `git_grep` / `beefsrc` 的那道才会读上游，
**而「哪道闸读上游」是那 20 行代码的事实，不该另抄一份**。
多写几遍是病因不是解药（纪律 355）。

**Batch 329 修的漏：`module_ref(` 曾经不在标记里，于是 4 道闸被漏扫**：
Batch 197 把 `REF = os.environ.get("BEEFTV_REF") or resolve_ref()`（**模块级每次调用都解析**）
改成了模块级缓存的 `REF = module_ref()`，**而这份标记表没跟着加**。
实测漏掉的是 `verify-runtime-policy.py` / `verify-feature-flags.py` /
`verify-route-notation.py` / `verify-screenshots-literals.py` —— **闸 12、闸 13 都在其中**。
**这个漏的失效形态是零告警**：工具照常输出一份「升版要过的门」清单，
**只是少了几行**，而报告读起来完全正常。
**它已经造成了读者可见的后果**：`20-reference.md`「已经对不上的地方」那份清单
**少了 `verify-screenshots-literals` 的 2 处**——因为那道闸压根没被跑。
**而这类漏不可能靠「再小心」避免**：标记表是一张**手工维护的清单**，
**它的形状必须跟着代码演化而变，而没有任何东西会提醒它**（纪律 364）。

**第一版栽在哪（2026-10-07，如实记下）**：它数「输出里带 `✗` / `⚠` 的行数」，
**而 `verify-line-counts.py` 与 `verify-quota-tables.py` 的明细行不带任何前缀**
（它们只在自己那行汇总里给数：5/7 条、3 处）。
**于是第一版对这两道闸打「问题行 0 → 0」——明明有 5 条和 3 条，它数出 0。**
**这正是纪律 101 的形状：解析器覆盖范围无人验，「读不出来」被渲染成「数出零」。**
**处置不是再补一条正则，是干脆不数**：**只比退出码，并原样转述闸自己的输出。**
**判据少一个，就少一处能悄悄退化的解析。**

**退出码**：0 对账跑完了；2 某个闸连基线那遍都跑不起来
（**那不是「对账无发现」**，按纪律 101 必须分开）。

**`--ref` 为什么必填、不给默认值**：闸 14（取证基线）方向四禁止任何闸脚本
在**可执行代码**里硬写上游的默认 ref ——**理由是「那样这道闸会把『上游走了』
报成『手册错了』」**。本脚本第一版把 `default="origin/main"` 写进了 argparse，
**绿构建当场被方向四拦下（rc=1）**，而那条判据是对的：
**一个默认 ref 就是一个「我以为的基线」，而基线在本项目里只能有一个答案**
（`20-reference.md` 开头那段明写着）。
**所以：那个字面量只许出现在 docstring 与注释里，不许出现在代码里；
`--help` 的说明文字同样不行——它也是字面量。**
**被闸当场拦下比事后自己发现好**，而这也是本批少数几个「闸在建好之前就抓到新东西」的实例。
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: **本脚本自己的文件名**——`upstream_gates()` 必须把它排除掉。
#: **2026-10-07 实测踩到**：它自己叫 `verify-*.py`，而扫描条件是
#: 「文件里有 `resolve_ref(` / `BEEFTV_REF` / … 这些痕迹」——
#: **而那些痕迹恰恰写在它自己的源码里**（UPSTREAM_MARKERS 那个元组）。
#: **于是它把自己算成了「一道会读上游的闸」，扫出 18 而不是 17**，
#: **而 `run_gate()` 会真的去跑它——也就是它会再跑一遍自己，递归下去。**
#: **排除写成「按自己的文件名」，不硬编码字符串**，
#: **因为硬编码的那一份迟早会跟真正的文件名对不上**（纪律 274：共享概念只能有一份实现）。
SELF_NAME = os.path.basename(__file__)

#: **会在源码里读上游的判据痕迹**——扫出来的那一道才会读上游
UPSTREAM_MARKERS = ("resolve_ref(", "module_ref(", "BEEFTV_REF", "git_grep", "beefsrc")


def upstream_gates(root):
    """扫出所有会读上游的闸的文件名。**只认文件名，不认闸号**——
    闸号是 `AUDIT-RULES.md` 闸清单表的行序，那是闸 9 方向十三的活，
    **在这里再实现一遍中文数字解析就是「同一概念的第二份实现」（纪律 355）。**"""
    out = []
    for name in sorted(os.listdir(os.path.join(root, "scripts"))):
        if not (name.startswith("verify-") and name.endswith(".py")):
            continue
        if name == SELF_NAME:
            continue
        try:
            src = open(os.path.join(root, "scripts", name), encoding="utf-8").read()
        except OSError:
            continue
        if any(m in src for m in UPSTREAM_MARKERS):
            out.append(name)
    return out


def run_gate(root, name, ref):
    """跑一道闸。返回 `(rc, 输出, 错误说明)`；`rc=None` 表示没跑起来。"""
    env = dict(os.environ)
    if ref:
        env["BEEFTV_REF"] = ref
    else:
        env.pop("BEEFTV_REF", None)
    try:
        r = subprocess.run([sys.executable, os.path.join("scripts", name)],
                           cwd=root, capture_output=True, text=True,
                           env=env, timeout=420)
    except subprocess.TimeoutExpired:
        return None, "", "超时（420 秒）"
    return r.returncode, r.stdout + r.stderr, ""


def tail_lines(text, n):
    """原样转述输出的末尾 n 个非空行。**不解析、不数、不猜。**"""
    ls = [l.rstrip() for l in text.split("\n") if l.strip()]
    return ls[-n:] if n > 0 else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(HERE),
                    help="手册根目录（默认取本脚本的上一级）")
    ap.add_argument("--ref", required=True,
                    help="要对比的上游 ref（**必填**：本脚本刻意不给默认值，"
                         "理由见本文件开头与纪律 358）")
    ap.add_argument("--detail", type=int, default=4,
                    help="每道变红的闸原样转述末尾 N 行（默认 4）")
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    gates = upstream_gates(root)
    print("会读上游的闸：%d 道（扫出来的，不是登记的）" % len(gates))
    print("基线 = 手册声明的提交；对账目标 = %s\n" % a.ref)

    changed, same, broke = [], 0, []
    #: **Batch 329 新增**：两个 ref 上**都是非 0** 的闸。
    #: 它们**不算「变红」**（rc 没变），但**绝不代表没问题**——
    #: rc 上只有「0」与「非 0」两种，**「非 0 → 非 0」在 rc 上与「0 → 0」长得一样**，
    #: 所以只按「rc 变没变」分类，就会把它们混进「两版一致」那一堆里。
    both_red = []
    for name in gates:
        rc_b, _, err_b = run_gate(root, name, None)
        if rc_b is None or err_b:
            broke.append((name, err_b or "rc=%s" % rc_b))
            print("  ?   %-30s 基线那遍没跑起来：%s" % (name, err_b or rc_b))
            continue
        rc_n, out_n, _ = run_gate(root, name, a.ref)
        if rc_n == rc_b:
            same += 1
            if rc_b != 0:
                both_red.append(name)
            print("  %-4s %-30s 基线 rc=%d → %s rc=%d%s"
                  % ("= !" if rc_b != 0 else "=", name, rc_b, a.ref, rc_n,
                     "　← **两个 ref 上都是红的**（不是变红，但也不代表没问题）"
                     if rc_b != 0 else ""))
        else:
            changed.append(name)
            print("  ≠   %-30s 基线 rc=%d → %s rc=%d" % (name, rc_b, a.ref, rc_n))
            for l in tail_lines(out_n, a.detail):
                print("         %s" % l[:200])

    print("\n==== 汇总 ====")
    print("共 %d 道：%d 道两版一致、%d 道在 %s 上变红、%d 道基线那遍没跑起来"
          % (len(gates), same, len(changed), a.ref, len(broke)))
    if both_red:
        print("**其中 %d 道在两个 ref 上都是 rc≠0**（%s）——"
              % (len(both_red), "、".join(both_red)))
        print("**它们不在「变红」那一类里（rc 没变），但它们也不代表没问题。**")
        print("**红的原因可能是上游、也可能是工作区里的未提交改动或环境**——")
        print("**而本工具只比对 ref、不比对工作区，所以它分不出来，也不替它猜。**")
    print("**变红不等于手册写错了**：多数是「上游真的变了」，而这正是升版要处置的活；")
    print("**但也不等于「全都能算进升版工单」**——")
    print("**本工具唯一能替你做的就是把三种状态分开列出来**"
          "（变红 / 两版都红 / 两版都绿），**逐道分类仍然是人的活**。")
    if broke:
        for n, e in broke:
            print("  ! %s：%s" % (n, e))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
