#!/usr/bin/env python3
"""第十道闸（verify-screenshots-literals.py）的反向验证。

设计沿用第六/第八道闸的路子：**注入一个真实会触发的违规**，闸门必须报；
再注入一个**看似相关但应放行**的形态，闸门必须不报。

⚠️ 注入方式是**改 manifest 里的 `visible_text`**，而不是改判据脚本——
注入必须落在**判据真的读的那份数据**上。Batch 155/157 都栽过
「注入点不在判据的读取路径上」这一类假通过。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from stagedeps import child_env

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-screenshots-literals.py")
BASELINE = os.path.join(HERE, "baseline.py")
# **Batch 205 补第二个本地依赖**：`baseline.py` 自己 `import beefsrc`，
# **而「被测闸 import 了什么」只看得见一层**（Batch 197 起）。
# 实测形态：临时仓里只有 `baseline.py` 与被测闸，于是 `baseline.py` 一 import 就
# `ModuleNotFoundError: No module named 'beefsrc'`，**本反验 0/N 全红**。
# **闸 17 方向一已升级为依赖闭包**，但搬运这件事本身还得在这儿做。
BEEFSRC = os.path.join(HERE, "beefsrc.py")
MANIFEST_REL = os.path.join("screenshots", "manifest.yml")

PASS = VOID = FAIL = 0


def run(manifest_text, desc, want, expect_fail=True):
    """把改过的 manifest 放到临时仓副本里跑闸门。"""
    global PASS, VOID, FAIL
    tmp = tempfile.mkdtemp(prefix="beef-lit-selftest.")
    try:
        # 闸门用 dirname(dirname(__file__)) 定位手册根，
        # 所以脚本必须放在临时仓的 scripts/ 下（第一版漏了这一层，报「未找到 manifest」）
        os.makedirs(os.path.join(tmp, "scripts"))
        os.makedirs(os.path.join(tmp, "screenshots"))
        # **必须连同 baseline.py 一起复制**（Batch 178 修）：
        # 自 Batch 175 起，被测闸门会 `from baseline import resolve_ref`，
        # 而本反验把闸门**单独**复制进临时目录 —— 于是临时目录里没有 baseline.py，
        # 闸门启动即 ModuleNotFoundError，**每一例都失败**。
        # 更糟的是它**静悄悄坏了三个批次**：闸门本体的 `run_gate` 仍全绿，
        # 没人跑反验就发现不了。**「被测对象多了一个依赖，反验就得跟着搬」**——
        # 而这类回归恰好是「反验能抓、构建抓不到」的那一类。
        shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
        shutil.copy(BEEFSRC, os.path.join(tmp, "scripts", "beefsrc.py"))
        shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-screenshots-literals.py"))
        with open(os.path.join(tmp, MANIFEST_REL), "w", encoding="utf-8") as fh:
            fh.write(manifest_text)
        # baseline.py 用 BEEFTV_MANUAL_ROOT 定位手册根（Batch 178）：
        # 临时目录里没有 20-reference.md，不传就会抛 BaselineError。
        # **指向真实手册根而不是 tmp**（Batch 178）：本反验的临时仓刻意只造
        # scripts/ + screenshots/（它要核的是 manifest 与上游，不涉及 20-reference.md），
        # 而 baseline.py 要从那里读「取证基线」声明。指 tmp 会抛
        # 「读不到 20-reference.md」，**每一例都失败**。
        env = child_env(ROOT)
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-screenshots-literals.py")],
                           cwd=tmp, env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc); FAIL += 1
        elif expect_fail and want not in out:
            print("  ✗ %s：报错了但不是 [%s]；实际：" % (desc, want))
            print("      " + out.strip().split("\n")[-1][:100]); FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤）：%s" % (desc, out.strip()[:100])); FAIL += 1
        else:
            print("  ✓ %s" % desc); PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    src = open(os.path.join(ROOT, MANIFEST_REL), encoding="utf-8").read()

    # 基线：真实 manifest 应当通过
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True, env=child_env(ROOT))
    if r.returncode == 0:
        print("  ✓ 基线：真实 manifest 通过（%s）" % r.stdout.strip().split("\n")[-1][:60])
        globals()["PASS"] += 1
    else:
        print("  ✗ 基线未通过：%s" % r.stdout.strip()[:120]); globals()["FAIL"] += 1

    # 1) 能抓：把一条保守形态的文案换成上游不存在的字样
    #
    # ⚠️ **必须替换整个 `visible_text: '…'` 行，不能只替换值字符串**——
    #    第一版只 replace 了值，而那个值在文件更早的位置（`step` / `verified_locator`）
    #    就出现过，**替换根本没落到判据读的那一处**，闸门通过是**正确的**，
    #    用例却判它失败。**这是本项目第三次栽在「注入点不在判据的读取路径上」**
    #    （Batch 155 用例 27、Batch 157 方向五负向测试，同一个形状）。
    broken = re.sub(r"visible_text:\s*'[^']*'",
                    "visible_text: '这个界面文案上游并不存在囍'", src, count=1)
    assert broken != src, "空转：注入未改变内容"
    run(broken, "1) 保守形态文案在上游消失（必须报）",
        # **刻意只锚稳定片段**（Batch 178 修）：原文写的是「上游 origin/main 的
        # web/src 里已找不到」，可 Batch 175 起闸门改为按**取证基线**读源码，
        # 措辞里的 ref 变成了提交号 → 这条断言跟着过期。
        # **反验的预期必须锚「判据的行为」，不能锚「某个版本下的具体措辞」**
        # ——否则每次换版本都要来改一遍反验，而改的人往往看不出它已经失效了。
        "的 web/src 里已找不到", expect_fail=True)

    # 2) 不误伤：动态计数形态（带数字）本就不该被检查
    dyn = re.sub(r"visible_text:\s*'([^']*)'",
                 lambda mm: "visible_text: '全部 0 / 图片 2 / 已选 2'", src, count=1)
    assert dyn != src, "空转：动态形态注入未改变内容"
    run(dyn, "2) 动态计数形态（必须放行，按形态本就不检查）",
        "", expect_fail=False)

    # 3) 不误伤：登记表里的豁免项必须仍然放行
    exempt = re.sub(r"visible_text:\s*'([^']*)'",
                    lambda mm: "visible_text: '产品片头 / 全部项目'", src, count=1)
    assert exempt != src, "空转：豁免形态注入未改变内容"
    run(exempt, "3) 已登记的豁免项（必须放行）", "", expect_fail=False)

    # 4) 能抓：豁免登记过期（片段已不存在）也必须报——否则豁免表只增不减
    # 删掉**真正含豁免片段的那条记录**——第一版删的是 65-model-channels.png，
    # 而「产品片头」在 53-canvas-library.png 里，于是豁免仍被使用、
    # 闸门通过同样是正确的。豁免归属必须先查清，不能猜。
    trimmed = re.sub(r"-\s+file:\s*screenshots/53-canvas-library\.png.*?(?=\n\s*-\s+file:|\Z)",
                     "", src, flags=re.S)
    if trimmed != src:
        run(trimmed, "4) 豁免登记的片段被删掉（必须报过期豁免）",
            "已无对应片段", expect_fail=True)
    else:
        print("  · 前提不成立：找不到用于删除的记录行；作废该用例")
        globals()["VOID"] += 1

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    sys.exit(1 if (FAIL or VOID) else 0)


if __name__ == "__main__":
    main()
