#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四道闸（verify-shortcuts.py）Batch 166 两处修正的反向验证。

本批修了两个**互相独立**的问题，各自都必须钉住：

  A. 输入范围靠 cwd（曾「0 个文件 → 判定通过」）
     · 下限守卫：手册文件读到的太少 → 必须 rc=2，**不许**报「通过」
     · 崩栈：从别处运行曾因读到已消失的文件抛 FileNotFoundError

  B. 抑制规则过宽（曾掩盖手册里一处真实缺陷）
     · `Ctrl/Cmd+Z / Shift+Z` 同行 → 必须报出后半段漏了前缀
     · `Ctrl/Cmd+Z / Ctrl/Cmd+Shift+Z` 连写 → **必须放行**（收窄不能过头）

⚠️ 注入 A/B 的用例必须先把真实正文**复制**进临时仓：否则文件数不足，
下限守卫会先以 rc=2 短路，**测到的就不是前缀检测本身**——
这是 Batch 163 探针空转那类坑：闸门「对了」，但没测到想测的东西。
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-shortcuts.py")

PASS = VOID = FAIL = 0
GATE_SRC = open(GATE, encoding="utf-8").read()
MIN_SCANNED = None
for line in GATE_SRC.split("\n"):
    if line.startswith("MIN_SCANNED_FILES"):
        MIN_SCANNED = int(line.split("=")[1].strip())
        break
assert MIN_SCANNED, "锚点未命中：闸门里找不到 MIN_SCANNED_FILES"


def make_manual(tmp, copy_all=True, extra=None):
    """搭一个临时手册仓。copy_all=True 时复制全部真实 .md（保证文件数过下限）。"""
    os.makedirs(os.path.join(tmp, "scripts"), exist_ok=True)
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-shortcuts.py"))
    if copy_all:
        for p in os.listdir(ROOT):
            if p.endswith(".md"):
                shutil.copy(os.path.join(ROOT, p), os.path.join(tmp, p))
        sub = os.path.join(ROOT, "10-tasks")
        if os.path.isdir(sub):
            shutil.copytree(sub, os.path.join(tmp, "10-tasks"), dirs_exist_ok=True)
    for name, text in (extra or {}).items():
        path = os.path.join(tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)


def run(desc, want, expect_fail=True, want_rc=1, mutate=None):
    global PASS, VOID, FAIL
    tmp = tempfile.mkdtemp(prefix="beef-shortcut-selftest.")
    try:
        extra = {}
        if mutate is not None:
            try:
                extra = mutate()
            except AssertionError as exc:
                print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
                VOID += 1
                return
        make_manual(tmp, copy_all=True, extra=extra)
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-shortcuts.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc); FAIL += 1
        elif expect_fail and r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际：%s" % (desc, r.returncode, want_rc, out.strip()[-120:]))
            FAIL += 1
        elif expect_fail and want not in out:
            print("  ✗ %s：报错了但不是 [%s]；实际：%s" % (desc, want, out.strip()[-120:])); FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤，rc=%d）：%s" % (desc, r.returncode, out.strip()[-150:]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc); PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_same_line_missing_prefix():
    return {"99-selftest.md": "键位：Ctrl/Cmd+Z / Shift+Z / Y\n"}


def m_bare_no_prefix():
    return {"99-selftest.md": "重做键位：Shift+Z\n"}


def m_adjacent_ok():
    return {"99-selftest.md": "键位：Ctrl/Cmd+Z / Ctrl/Cmd+Shift+Z / Ctrl/Cmd+Y\n"}


def run_min_files():
    """下限守卫：临时仓只有 2 个 md（远低于 MIN_SCANNED_FILES）→ 必须 rc=2。"""
    global PASS, VOID, FAIL
    tmp = tempfile.mkdtemp(prefix="beef-shortcut-min.")
    try:
        make_manual(tmp, copy_all=False, extra={
            "a.md": "占位\n", "b.md": "占位\n",
        })
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-shortcuts.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if r.returncode == 0:
            print("  ✗ 下限守卫：只读到 2 个文件却判通过（本闸 Batch 166 修的正是这个）"); FAIL += 1
        elif r.returncode != 2 or "未能核对" not in out:
            print("  ✗ 下限守卫：退出码 %d 期望 2 且输出含「未能核对」；实际：%s" % (r.returncode, out.strip()[-120:]))
            FAIL += 1
        else:
            print("  ✓ 下限守卫：只读到 2 个文件（下限 %d）→ 正确报未能核对（rc=2）" % MIN_SCANNED); PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_cwd_independent():
    """从别处运行结果必须一致（自定位生效）。"""
    global PASS, VOID, FAIL
    elsewhere = tempfile.mkdtemp(prefix="beef-shortcut-elsewhere.")
    try:
        r = subprocess.run([sys.executable, GATE], cwd=elsewhere, capture_output=True, text=True)
        if r.returncode != 0:
            print("  ✗ cwd 无关性：从无关目录运行 rc=%d（应 0）" % r.returncode); FAIL += 1
        elif "需带 Ctrl/Cmd" in r.stdout:
            print("  ✗ cwd 无关性：从无关目录运行竟报出前缀问题"); FAIL += 1
        else:
            print("  ✓ cwd 无关性：从无关目录运行仍扫到正确正文并通过"); PASS += 1
    finally:
        shutil.rmtree(elsewhere, ignore_errors=True)


def main():
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ 基线：真实手册通过（%s）" % r.stdout.strip()[:60])
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：真实手册应当通过，rc=%d：%s" % (r.returncode, r.stdout.strip()[:150]))
        globals()["FAIL"] = globals()["FAIL"] + 1

    run("1) 同行后半段漏前缀（Ctrl/Cmd+Z / Shift+Z，必须报）", "Shift+Z", mutate=m_same_line_missing_prefix)
    run("2) 裸 Shift+Z 无任何前缀（必须报）", "Shift+Z", mutate=m_bare_no_prefix)
    run("3) 不误伤：相邻连写都带前缀（必须放行）", "", expect_fail=False, mutate=m_adjacent_ok)
    run_min_files()
    run_cwd_independent()

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
