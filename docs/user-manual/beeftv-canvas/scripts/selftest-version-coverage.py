#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十二道闸（verify-version-coverage.py）的反向验证。

**本闸的判据在写完第一版之后被鉴别力验证改掉了**（纪律 166：
判据上线前必须证明它抓得住那个它声称要抓的缺陷）。
第一版判「版本号出现在任一发布页里」——把 `generate-video.md` 里的
「v1.6.21」抹掉，闸**照样绿**，因为那个版本号在 `director-basics.md` 的
「v1.6.21 及更早的导演台弹窗」里出现过。
**「某处提到过这个版本」不等于「读者能顺着找到这次改了什么」**，
所以判据收紧到「必须列进 README 的增量清单」。
**用例 4 就是把这个教训钉成用例**：那是第一版会放行、改严之后必须报的形态。

  能抓 2 条：
    1) 从增量清单里删掉一个改了用户可见文案的版本 → 必须报
    2) **该版本在别的页面被提到、只是不在清单里** → 必须报
       （**这一条钉的就是第一版的漏洞**，改严之后绝不许再退回「任一页出现即可」）
  不误伤 3 条：
    3) 0 增减的版本不在清单里（**v1.6.18 / v1.6.20 就是天然样本**）→ 必须放行
    4) 把 0 增减的版本**加进**清单并写明「无界面变化」→ 必须放行
       （读者有权知道「这版没什么」，而那与「没人查过」不是一回事）
    5) 清单下界与「取证基线」声明的截图版本分家 → 必须 **rc=2**
       （两端对不上时判据不能挑对自己有利的那个继续跑）

⚠️ 第 5 条守的是「判据会不会偷偷换下界」：下界取错了，整个区间就变了，
而**换下界这件事在输出上完全看不出来**——除非有判据盯着它。

每条注入都用 `assert` 钉死锚点，**并且在跑之前 `cksum` 比对前后**
（Batch 229：`str.replace` 锚点不中时静默无操作，而「用例通过」与
「用例根本没跑起来」输出上完全一样）。
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-version-coverage.py")
BASELINE = os.path.join(HERE, "baseline.py")
BEEFSRC = os.path.join(HERE, "beefsrc.py")
README = "README.md"
REFERENCE = "20-reference.md"
MANIFEST = os.path.join("screenshots", "manifest.yml")

PASS = VOID = FAIL = 0


def _cksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(desc, want, expect_fail=True, want_rc=1, edits=None):
    global PASS, VOID, FAIL
    reads = [os.path.join(ROOT, README), os.path.join(ROOT, REFERENCE),
             os.path.join(ROOT, MANIFEST)]
    base = {p: open(p, encoding="utf-8").read() for p in reads}
    texts = dict(base)

    if edits:
        try:
            for path, fn in edits.items():
                texts[path] = fn(texts[path])
        except AssertionError as exc:
            print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
            VOID += 1
            return
        changed = [p for p in edits if _cksum(texts[p]) != _cksum(base[p])]
        if not changed:
            print("  ✗ %s：注入前后内容逐字相同 → **本用例作废**（静默空转）" % desc)
            VOID += 1
            return

    tmp = tempfile.mkdtemp(prefix="beef-vercov-selftest.")
    try:
        os.makedirs(os.path.join(tmp, "scripts"), exist_ok=True)
        os.makedirs(os.path.join(tmp, "screenshots"), exist_ok=True)
        shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
        shutil.copy(BEEFSRC, os.path.join(tmp, "scripts", "beefsrc.py"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-version-coverage.py"))
        for p, t in texts.items():
            rel = os.path.relpath(p, ROOT)
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(t)
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-version-coverage.py")],
                           cwd=tmp, capture_output=True, text=True)
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


V2121 = "；**v1.6.21** 视频**时长多了「自动」**"


# ------------------------------------------------------------------ 能抓

def t_drop_from_list(s):
    assert V2121 in s, "锚点未命中：增量清单里找不到 v1.6.21 那一段"
    i = s.index(V2121)
    j = s.index("；**v1.6.22**", i)
    return s[:i] + s[j:]


def t_mentioned_elsewhere_only(s):
    assert V2121 in s, "锚点未命中：增量清单里找不到 v1.6.21 那一段"
    out = s[:s.index(V2121)] + s[s.index("；**v1.6.22**"):]
    #: **在别处补上这个版本号**——模拟「别处提到了、清单里没有」。
    #: **第一版判据会放行这一例**（它只要求「任一页出现」），
    #: **改严之后必须报**——「某处提到过」不等于「读者能顺着找到这次改了什么」。
    return out + "\n> 补充：v1.6.21 另有一处无关的版本边界说明。\n"


# -------------------------------------------------------------- 不误伤

def t_zero_change_stays_unlisted(s):
    #: **本闸只读 README 里含「之后的增量」的那一行**，不是整份文件——
    #: 下面这个前置条件就是它的证据：v1.6.18 确实出现在 README 里（另一行写着
    #: 「v1.6.18 与 v1.6.20 没有界面变化」），**但它不在增量清单那一行里**。
    #: **0 增减的版本本来就不该被要求进清单**（v1.6.18 / v1.6.20 实测增减都是 0），
    #: 而这一例证明判据**没有偷偷把范围扩大到整份 README**——
    #: **判据读得比声称的宽，就会在某天报出一个它其实不该管的版本。**
    line = [ln for ln in s.split("\n") if "之后的增量" in ln]
    assert len(line) == 1, "前置条件不符：「之后的增量」应恰好一行，实得 %d" % len(line)
    assert "v1.6.18" in s, "前置条件不符：README 里应当找得到 v1.6.18（在另一行）"
    assert "v1.6.18" not in line[0], "前置条件不符：v1.6.18 已经在增量清单行里了"
    return s + "\n（反验注入：整份 README 再提一次 v1.6.18，闸不该因此收紧）\n"


def t_list_zero_change_version(s):
    a = "；**v1.6.22**"
    assert a in s, "锚点未命中：找不到 v1.6.22 那一段"
    #: 读者有权知道「v1.6.18 这版没什么」——**那是与「没人查过」不同的一件事**，
    #: 判据不能因为「它 0 增减」就把读者想知道的答案拦在门外。
    return s.replace(a, "；**v1.6.18** 无界面变化；**v1.6.22**", 1)


def t_list_floor_mismatch(s):
    assert "之后的增量" in s, "锚点未命中：找不到「之后的增量」"
    #: **下界与「取证基线」声明的截图版本分家**——此时判据若自己挑一个下界继续跑，
    #: 整个区间就变了，**而换下界这件事在输出上完全看不出来**。
    return s.replace("v1.6.14 之后的增量", "v1.6.10 之后的增量", 1)


def main():
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ 基线：真实手册通过（%s）" % r.stdout.strip().split("\n")[-1][:70])
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, r.stdout.strip()[:200]))
        globals()["FAIL"] = globals()["FAIL"] + 1

    rd = os.path.join(ROOT, README)
    run("1) 增量清单里删掉一个改了用户可见文案的版本（必须报）", "而 README 的「增量」清单里没有它",
        edits={rd: t_drop_from_list})
    run("2) 该版本在别处被提到、只是不在清单里（必须报——**这是第一版的漏洞**）",
        "而 README 的「增量」清单里没有它", edits={rd: t_mentioned_elsewhere_only})
    run("3) 不误伤：0 增减的版本不在清单里（天然样本，必须放行）", "版本覆盖核对通过",
        expect_fail=False, edits={rd: t_zero_change_stays_unlisted})
    run("4) 不误伤：把 0 增减的版本加进清单并写明「无界面变化」（必须放行）",
        "版本覆盖核对通过", expect_fail=False, edits={rd: t_list_zero_change_version})
    run("5) 清单下界与取证基线声明的截图版本分家（必须 rc=2）", "两端对不上",
        want_rc=2, expect_fail=True, edits={rd: t_list_floor_mismatch})

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
