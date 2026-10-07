#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四十六道闸（verify-list-selfcount.py）的反向验证。

**本闸的覆盖面只有一种形态**，所以反验的重点不是「它抓不抓得到那两行」，
而是**「它会不会去抓它不该抓的那些」**——
本批实测：全库 44 处自述数里，**只有 1 处真错，其余 43 处全是指代别的东西**。
**这一族判据的失败模式几乎必然是过宽，而不是过窄。**

  能抓 2 条：
    1) 自述的数与列表行数不符（「这 3 条」对上 2 行）→ 必须报
    2) **列表多了一条而自述没跟着改**（升版那一批的真实形态）→ 必须报
  不误伤 3 条：
    3) **自述上方是表格**（`20-reference.md` 实测那处「快捷键中心共 24 条」）→ 必须放行
    4) **被 `srcExclude` 排除的账本里回指自己的列表**
       （`AUDIT.md:1252` 实测是这形态，**把判据开成全库第一处误伤就是它**）→ 必须放行
    5) 列表里带**缩进续行**（子条目）→ 行数只数顶层，必须放行
       （**由用例 1 顺带钉住，不另开用例**：基准语料里就有 `  甲的续行`，
       **判据若把续行也数成条目，用例 1 立刻变成 rc=1**——
       义务的测法该用「一碰到就坏」的最小样本，而不是复制一份只测一半的样本）
  未能核对 3 条：
    6) 语料里一处「这 N 条」都没有 → 必须 rc=2（下限守卫，**不许报绿**）
    7) 读不到 `.vitepress/config.mjs` → 必须 rc=2
    8) **判据自己的正则被改坏** → 必须 rc=2（纪律 101）

**为什么夹具不复制 `scripts/`（Batch 336 的写法选择）**：
闸的输入是「发布面里各页的正文」，而 `scope.py` 让 `BEEFTV_MANUAL_ROOT`
**优先于 `__file__` 推断**（Batch 178）——于是**子进程跑真树的判据、
把环境变量指向夹具树**，就得到「真判据 + 假语料」。
**代价是判据代码改不动**，所以只有用例 8 单独走「复制依赖闭包」那条重路。

**为什么不改真树注入（与 `selftest-current-version.py` 相反的做法）**：
那份反验改的是 `00-quickstart.md`；而本批工作区里有同事正在改的手册页，
**改真树意味着注入期间那两个文件处于被改写状态**。
**沙箱只装语料、不装代码**这条更省，也顺带避开了「注入空转」的老坑。

**而「只装语料」这个选择顺带钉住了一个真缺陷（本批最值钱的一处）**：
闸的根一度写成 `os.path.dirname(HERE)`（脚本所在目录），
而页面清单来自 `scope.published_paths()`（`BEEFTV_MANUAL_ROOT` 决定的那棵树）。
**两处根不是同一处**，于是「清单按夹具算、正文按真手册读」——
**用例 2、3、6 全部报绿，因为它们根本没碰到夹具里那页。**
**如果反验照抄「改真树 + 沙箱装 scripts/`」那条路，这个缺陷一次都测不出来**：
沙箱里 `scripts/` 在场，脚本位置和语料位置**本来就是同一棵树**，那个 bug 自然不显形。
**判据能测出自己的哪类回归，取决于反验把判据放在什么位置**——
**这是「用夹具而不是用副本」这条选择的实测收益，不只是省事。**
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from stagedeps import child_env

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-list-selfcount.py")
CONFIG = os.path.join(ROOT, ".vitepress", "config.mjs")
#: 夹具里那本**不是真手册的探针页**。**刻意自造而不复制真 `20-reference.md`**：
#: 真页正在被本批改动，而反验要的恰恰是「一份**钉死的**语料」——
#: 复制真页会让反验的期望值随正文一起漂（那不叫反验，叫搭便车）。
PAGE = "20-reference.md"
AUDIT = "AUDIT.md"
#: 用例 8 要改坏判据的正则。**锚点用完整的一行**，少一个字符就 assert 拦住。
GATE_ANCHOR = 'CLAIM_RE = re.compile(r"这\\s*(\\d+)\\s*条")'
GATE_BROKEN = 'CLAIM_RE = re.compile(r"这\\s*(\\d+)\\s*条\\s*（永不可能同时出现）")'

#: 夹具页的基准语料：一小节 + 两行列表 + 一处「这 2 条」回指。
BASE_PAGE = """# 探针页

## 一个小节

- 甲
  甲的续行
- 乙

> 而这 2 条说的是上面那两行。
"""

PASS = VOID = FAIL = 0

#: 用例 8 要连同判据一起复制的那几个模块——
#: **`beefsrc` 也在内**：第一版只复制了 `scope.py` 与 `baseline.py`，
#: 而 `baseline` 顶上 `import beefsrc`，于是夹具里判据直接 ImportError、
#: rc=1 被当成了「判据报出不一致」。**这正是纪律 101 要防的那类混淆。**
GATE_DEPS = ("scope.py", "baseline.py", "beefsrc.py", "stagedeps.py")


def cksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(tmp, page_text, with_config=True, with_audit=None, broken_gate=False):
    """把这一轮要的语料摆进沙箱。**只摆语料**，代码默认从真树跑。"""
    os.makedirs(os.path.join(tmp, ".vitepress"), exist_ok=True)
    if with_config:
        shutil.copyfile(CONFIG, os.path.join(tmp, ".vitepress", "config.mjs"))
    with open(os.path.join(tmp, PAGE), "w", encoding="utf-8") as fh:
        fh.write(page_text)
    if with_audit is not None:
        with open(os.path.join(tmp, AUDIT), "w", encoding="utf-8") as fh:
            fh.write(with_audit)
    if broken_gate:
        d = os.path.join(tmp, "scripts")
        os.makedirs(d, exist_ok=True)
        for name in GATE_DEPS:
            shutil.copyfile(os.path.join(HERE, name), os.path.join(d, name))
        with open(GATE, encoding="utf-8") as fh:
            src = fh.read()
        assert GATE_ANCHOR in src, "判据源码里找不到 CLAIM_RE 那一行——**闸改过了，本反验作废**"
        with open(os.path.join(d, "verify-list-selfcount.py"), "w", encoding="utf-8") as fh:
            fh.write(src.replace(GATE_ANCHOR, GATE_BROKEN, 1))
        return os.path.join(d, "verify-list-selfcount.py")
    return GATE


def run(desc, want_rc, want_substr, page_text=BASE_PAGE, expect_substr=None,
        with_config=True, with_audit=None, broken_gate=False, edit_page=None):
    """跑一轮。`want_rc` 是本用例要求的退出码，**钉死不靠"非 0 即算过"**。"""
    global PASS, VOID, FAIL
    if edit_page is not None:
        try:
            page_text = edit_page(page_text)
        except AssertionError as exc:
            print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
            VOID += 1
            return
        if cksum(page_text) == cksum(BASE_PAGE):
            print("  ✗ %s：注入前后逐字相同 → **本用例作废**（静默空转）" % desc)
            VOID += 1
            return
    tmp = tempfile.mkdtemp(prefix="beef-selfcount-selftest.")
    try:
        gate = build(tmp, page_text, with_config, with_audit, broken_gate)
        env = child_env(tmp)
        r = subprocess.run([sys.executable, gate], cwd=tmp,
                           capture_output=True, text=True, env=env)
        out = r.stdout + r.stderr
        if r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际输出：" % (desc, r.returncode, want_rc))
            print("      " + out.strip().replace("\n", "\n      ")[:300])
            FAIL += 1
            return
        probe = expect_substr if expect_substr is not None else want_substr
        if probe and probe not in out:
            print("  ✗ %s：退出码对了但输出里没有 %r —— **它没在做它声称的事**" % (desc, probe))
            print("      " + out.strip().replace("\n", "\n      ")[:300])
            FAIL += 1
            return
        print("  ✓ %s" % desc)
        PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def bump(said, to):
    """把自述的数改掉——**锚点写死**，不命中就 assert。"""
    def _f(text):
        assert "这 %d 条" % said in text, "语料里没有「这 %d 条」" % said
        return text.replace("这 %d 条" % said, "这 %d 条" % to, 1)
    return _f


def main():
    print("=== 第四十六道闸（清单自述条数）反验 ===")

    run("1) 基准：自述与列表行数一致 → 放行", 0, "核对通过")
    run("2) 能抓：自述 3 而列表 2 行", 1, "这 3 条", edit_page=bump(2, 3))
    # 用例 3 是**升版那一批的真实形态**：动列表、不动自述。
    run("3) 能抓：列表多一条而自述没改", 1, "而它上面那份清单是 3 条",
        edit_page=lambda t: t.replace("- 乙\n", "- 乙\n- 丙\n", 1))
    run("4) 不误伤：自述上方是表格（实测那处「共 24 条」）", 0, "核对通过",
        page_text=BASE_PAGE + "\n## 另一小节\n\n| 键 | 行为 |\n|---|---|\n| A | B |\n\n"
                           "> 而这 24 条指的是界面里的条目，与本表行数无关。\n")
    run("5) 不误伤：账本 AUDIT.md 里的同形态回指（判据开成全库第一处误伤就是它）",
        0, "核对通过",
        with_audit="# 账本\n\n## 环境记录一\n\n- 甲\n- 乙\n- 丙\n- 丁\n- 戊\n- 己\n- 庚\n- 辛\n- 壬\n- 癸\n- 子\n- 丑\n- 寅\n- 卯\n- 辰\n- 巳\n- 午\n- 未\n\n> 而这 16 条是那个批次当时记下的。\n")
    run("6) 未能核对：语料里一处「这 N 条」都没有 → 必须 rc=2", 2, "[skip]",
        page_text="# 探针页\n\n## 一个小节\n\n- 甲\n- 乙\n\n> 这里没有任何自述条数。\n")
    run("7) 未能核对：读不到 config.mjs → 必须 rc=2", 2, "[skip]", with_config=False)
    run("8) 未能核对：判据自己的正则被改坏 → 必须 rc=2", 2, "[skip]", broken_gate=True)

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
