#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十道闸（verify-quota-tables.py）的反向验证。

Batch 233 给 `storage-quota.md` 的配额表建了这道闸，而**这道闸的全部价值在方向①
「上游有的、手册必须有」**——它上线首跑就抓出两处真缺陷（漏了整条 `TaskDataGB`、
漏了 `GeneratedFileMB` 的第二种措辞）。所以本反验最要紧的不是「它能报」，
而是**「它报的是不是真问题」**：配额表是要给读者当排查依据用的，
**把正确的东西报成缺陷，危害比缺陷本身大**（纪律 248）。

  能抓 5 条：
    1) 删掉「任务历史数据（文本）」整行 → 必须报「表里没有这条文案」
    2) 删掉「单个生成资源超过 64MB」那半句 → 必须报漏写
       （**这正是本批真实修掉的第二个缺陷**，判据抓不抓得到它要单独钉）
    3) 默认值 20 GB 改成 30 GB → 必须报「默认值格写…而它的文案绑定 StoredFileGB=20」
       （方向③：两列各说各话时必须能抓）
    4) 某行文案改一个字 → 必须报「上游渲染不出这句」
    5) 规范表的表头改掉 → 必须 **rc=2 未能核对**，而**不是**「没找到表所以通过」
  不误伤 3 条：
    6) 改第一列的配额名称 → 必须放行（判据核的是文案与数值，不是叫法）
    7) 默认值 `**20 GB**` 改成 `**20GB**` → 必须放行（**核的是数字不是写法**）
    8) 调换两行顺序 → 必须放行（判据不核顺序）

⚠️ 第 5 条守的是「闸门有没有真的在查」：若表头一改解析器就退化，最危险的结果不是报错，
而是**静悄悄地全部通过**（Batch 157 的「工具失败被当成零命中」，这次发生在判据自己身上）。

每条注入都用 `assert` 钉死锚点，**并且在跑之前 `cksum` 比对前后**：
`str.replace` 锚点不中时**静默无操作**，而「用例通过」与「用例根本没跑起来」
在输出上完全一样（Batch 229 的 6 个注入用例里 3 个在空跑）。只加 `assert` 不够——
`assert` 只能钉「改之前锚点在」，钉不住「改之后内容真的变了」。
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
GATE = os.path.join(HERE, "verify-quota-tables.py")
BASELINE = os.path.join(HERE, "baseline.py")
BEEFSRC = os.path.join(HERE, "beefsrc.py")
MANUAL_REL = os.path.join("10-tasks", "storage-quota.md")
#: **基线是读出来的，不是写死的**（闸 14 的纪律 107）——所以沙箱里必须带上这一页，
#: 否则 `@baseline_guard` 连基线都定不下来，闸门会以 rc=2 拒绝核对。
BASELINE_REL = "20-reference.md"

PASS = VOID = FAIL = 0


def _cksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(desc, want, expect_fail=True, want_rc=1, transform=None):
    global PASS, VOID, FAIL
    with open(os.path.join(ROOT, MANUAL_REL), encoding="utf-8") as fh:
        base = fh.read()
    text = base
    if transform is not None:
        try:
            text = transform(base)
        except AssertionError as exc:
            print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
            VOID += 1
            return
        #: **Batch 229 的教训**：`str.replace` 锚点不中时静默无操作，
        #: 而「用例通过」与「用例什么都没做」输出上完全一样。
        #: `assert a in s` 只能证明改之前锚点在，证明不了改之后内容真的变了——
        #: **所以必须比对前后 cksum**，这一条兜住的是「assert 写了但没起作用」。
        if _cksum(text) == _cksum(base):
            print("  ✗ %s：注入前后内容逐字相同 → **本用例作废**（静默空转）" % desc)
            VOID += 1
            return

    tmp = tempfile.mkdtemp(prefix="beef-quota-selftest.")
    try:
        os.makedirs(os.path.join(tmp, "scripts"))
        os.makedirs(os.path.join(tmp, "10-tasks"))
        #: **必须连 baseline.py 与 beefsrc.py 一起复制**（闸 17 的由来）：
        #: 被测闸门 `from baseline import …`，而 baseline 自己 `import beefsrc`。
        #: 少搬一个 → 闸门启动即 ModuleNotFoundError，**每一例都失败，
        #: 而 build-site.sh 仍然全绿**——反验坏掉不产生任何构建期信号。
        shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
        shutil.copy(BEEFSRC, os.path.join(tmp, "scripts", "beefsrc.py"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-quota-tables.py"))
        #: **还要搬 `20-reference.md`**（第一版漏了它，8 例全崩）：被测闸门带 `@baseline_guard`，
        #: 而**基线是从参考页的「取证基线」小节读出来的**——没有那个文件，闸门启动即
        #: 「读不到 20-reference.md」并 rc=2，**每一例都失败**。
        #: 值得记的是它**没有假装通过**（rc=2 而不是 0），所以这批失败是可见的；
        #: **但闸 17 只核 Python 模块的搬运，看不见数据文件**——反验的沙箱不只有一种坏法。
        shutil.copy(os.path.join(ROOT, BASELINE_REL), os.path.join(tmp, BASELINE_REL))
        with open(os.path.join(tmp, MANUAL_REL), "w", encoding="utf-8") as fh:
            fh.write(text)

        #: **Batch 260**：`baseline.py` / `scope.py` 让 `BEEFTV_MANUAL_ROOT`
        #: **优先于 `__file__` 推断**，而本闸的 `ROOT` 是 `dirname(HERE)`——
        #: **不设它就凑巧对，设错了就整棵读错**（实测见纪律 289 / 闸 17 方向一之二）。
        #: **沙箱自己就是这一轮的手册根**。
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-quota-tables.py")],
                           cwd=tmp, capture_output=True, text=True,
                                   env=child_env(tmp))
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc)
            print("      " + out.strip()[:200])
            FAIL += 1
        elif expect_fail and r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际：" % (desc, r.returncode, want_rc))
            print("      " + out.strip()[:200])
            FAIL += 1
        elif expect_fail and want not in out:
            print("  ✗ %s：报错了但不是 [%s]；实际：" % (desc, want))
            print("      " + out.strip()[:200])
            FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤，rc=%d）：%s"
                  % (desc, r.returncode, out.strip()[:200]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc)
            PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ 能抓

def t_drop_taskdata_row(s):
    a = "| 任务历史数据（文本） | **1 GB** | 账号任务历史数据已达到 1GB 上限，请联系管理员归档 |\n"
    assert a in s, "锚点未命中：找不到「任务历史数据（文本）」整行"
    return s.replace(a, "", 1)


def t_drop_second_wording(s):
    a = "单个生成文件不能超过 64MB / 单个生成资源超过 64MB"
    assert a in s, "锚点未命中：找不到单个生成文件那格的两种措辞"
    return s.replace(a, "单个生成文件不能超过 64MB", 1)


def t_wrong_default(s):
    a = "| 账号存储总量 | **20 GB** |"
    assert a in s, "锚点未命中：找不到「账号存储总量」行"
    return s.replace(a, "| 账号存储总量 | **30 GB** |", 1)


def t_fabricated_copy(s):
    a = "账号画布和素材数据已达到 256MB 上限，请先删除不需要的内容"
    assert a in s, "锚点未命中：找不到结构化数据那格"
    return s.replace(a, "账号画布和素材数据已达 256MB 上限，请先清理", 1)


def t_rename_header(s):
    a = "| 配额 | 默认值 | 撞到时的报错 |"
    assert a in s, "锚点未命中：找不到配额表的表头"
    return s.replace(a, "| 限制项 | 阈值 | 撞到时的提示 |", 1)


# -------------------------------------------------------------- 不误伤

def t_rename_label(s):
    a = "| 上游请求日志 | **100000 条** |"
    assert a in s, "锚点未命中：找不到「上游请求日志」行"
    return s.replace(a, "| 上游请求日志条数（反验注入：只改叫法） | **100000 条** |", 1)


def t_number_same_unit_style(s):
    a = "| 账号存储总量 | **20 GB** |"
    assert a in s, "锚点未命中：找不到「账号存储总量」行"
    #: **核的是数字不是写法**：把「20 GB」写成「20GB」是纯排版，判据必须放行。
    #: 反过来若判据改成整格字符串比对，这一条就会误伤——**而误伤配额表比漏项更坏**。
    return s.replace(a, "| 账号存储总量 | **20GB** |", 1)


def t_swap_two_rows(s):
    a = "| 画布数量 | **1000 个** | 账号画布数量已达到 1000 个上限 / 账号画布数量不能超过 1000 个 |\n"
    b = "| 任务历史条数 | **20000 条** | 账号任务历史已达到 20000 条上限，请联系管理员归档 |\n"
    assert a in s and b in s, "锚点未命中：找不到要互换的那两行"
    return s.replace(a + b, b + a, 1)


def main():

    #: **Batch 260 同族第二处**（纪律 289 推论二）：这一条跑的是**真树**，
    #: **而它同样要显式指回真树**——调用者若把那个变量指向别处，
    #: **这一条就会拿一个错误的根去核真树**。**只修沙箱那一处，它仍然红。**
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True,
                                                       env=child_env(ROOT))
    if r.returncode == 0:
        print("  ✓ 基线：真实手册通过（%s）" % r.stdout.strip().split("\n")[0][:70])
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, r.stdout.strip()[:200]))
        globals()["FAIL"] = globals()["FAIL"] + 1

    run("1) 删掉整条「任务历史数据」配额（必须报漏写）",
        "手册表里没有这条文案", transform=t_drop_taskdata_row)
    run("2) 删掉同配额的第二种措辞「单个生成资源超过 64MB」（必须报漏写）",
        "手册表里没有这条文案", transform=t_drop_second_wording)
    run("3) 默认值列与上游默认值不符（必须报数值不符）",
        "默认值格写", transform=t_wrong_default)
    run("4) 文案被改写成上游没有的措辞（必须报多写）",
        "上游渲染不出这句", transform=t_fabricated_copy)
    run("5) 规范表的表头被改（必须 rc=2 未能核对，不能静默通过）",
        "配额核对本轮未能进行", want_rc=2, transform=t_rename_header)
    run("6) 不误伤：只改第一列的配额叫法（必须放行）",
        "账号配额核对通过", expect_fail=False, transform=t_rename_label)
    run("7) 不误伤：默认值 20 GB 写成 20GB（同数不同写法，必须放行）",
        "账号配额核对通过", expect_fail=False, transform=t_number_same_unit_style)
    run("8) 不误伤：调换两行顺序（必须放行）",
        "账号配额核对通过", expect_fail=False, transform=t_swap_two_rows)

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
