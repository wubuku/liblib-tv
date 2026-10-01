#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二道闸（verify-screenshots.py）四方对账的反向验证。

Batch 167 普查发现：本闸与闸 6 是**十道闸里仅有的两道没有任何反向验证的**。
（闸 1 是第三道，但它内联在 `build-site.sh` 的 heredoc 里，结构上无法独立验证。）

本闸有**五条独立的判据**，每一条都要能抓，也都要能放行：

| 用例 | 注入 | 期望 |
|---|---|---|
| 1 基线 | 四方一致 | rc=0 |
| 2 未登记 | 库内有图、manifest 没登记 | 必报 |
| 3 空登记 | manifest 登记了、库内没这张图 | 必报 |
| 4 孤儿图 | 库内有图、没有任何发布页引用 | 必报 |
| 5 缺图 | 页面引用了、库内没有 | 必报 |
| 6 未打包 | 库内有图、dist 里没有 | 必报 |
| 7 不误伤 | 只在内部账本（PROGRESS.md）里引用 | 必须放行 |

⚠️ 第 7 条是**真的不误伤**而不是「顺手加的」：闸 6 明确规定 `PROGRESS/AUDIT/
task-inventory/PUBLISH/FINAL-REPORT/manifest` 里的引用**不计入发布页引用**
（它们不对读者可见）。若这条判据坏掉，账本里提到截图就会把孤儿图判成「已被引用」，
**孤儿图检查随即失效**——而孤儿图正是本闸（Batch 94）当初要抓的那一类。

⚠️ 第一版把第 7 条写成了「只被 PROGRESS.md 引用 → 应放行」，**闸门判我错了**：
那张图**确实是孤儿图**，报它是完全正确的。闸 6 有 7 处这样的「闸门对、测试错」。
**写不误伤用例时先问：我要证明的到底是「判据不误伤」还是「我以为的形态」？**
现在这条只断言真正想证明的东西：**账本里的重复引用既不改变判账、也不被算进发布页引用**。
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-screenshots.py")

PASS = VOID = FAIL = 0

A = "aa-first.png"
B = "bb-second.png"


def manifest_entry(name):
    return ("  - file: screenshots/%s\n"
            "    task_id: selftest\n"
            "    step: '反验注入用条目'\n"
            "    route: '/x'\n"
            "    viewport: 1280x720\n"
            "    locale: zh-CN\n"
            "    captured_at: '2026-01-01'\n"
            "    verified_locator: 'generic x'\n"
            "    visible_text: '反验注入'\n"
            "    alt: '反验注入用图'\n"
            "    sha256: 0\n" % name)


def build(manifest_names, library, page_refs, dist_names, extra_pages=None):
    """搭一个最小的临时手册仓，返回路径。"""
    tmp = tempfile.mkdtemp(prefix="beef-shot-selftest.")
    os.makedirs(os.path.join(tmp, "scripts"))
    os.makedirs(os.path.join(tmp, "screenshots"))
    os.makedirs(os.path.join(tmp, ".vitepress", "dist"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-screenshots.py"))
    for n in library:
        open(os.path.join(tmp, "screenshots", n), "wb").write(b"\x89PNG\r\n\x1a\n")
    with open(os.path.join(tmp, "screenshots", "manifest.yml"), "w", encoding="utf-8") as fh:
        fh.write("screenshots:\n")
        for n in manifest_names:
            fh.write(manifest_entry(n))
    with open(os.path.join(tmp, "00-page.md"), "w", encoding="utf-8") as fh:
        fh.write("# 页面\n\n" + "".join(f"![x](../screenshots/{n})\n" for n in page_refs))
    for path, body in (extra_pages or {}).items():
        with open(os.path.join(tmp, path), "w", encoding="utf-8") as fh:
            fh.write(body)
    for n in dist_names:
        stem = n[:-4]
        open(os.path.join(tmp, ".vitepress", "dist", f"{stem}.AbCd1234.png"), "wb").write(b"\x89PNG\r\n\x1a\n")
    return tmp


def run(desc, expect_fail=True, want=None, **kw):
    global PASS, VOID, FAIL
    tmp = build(**kw)
    try:
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-screenshots.py")],
                           cwd=tmp, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc); FAIL += 1
        elif expect_fail and want and want not in out:
            print("  ✗ %s：报错了但不是 [%s]；实际：%s" % (desc, want, out.strip()[-160:])); FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤，rc=%d）：%s" % (desc, r.returncode, out.strip()[-200:]))
            FAIL += 1
        else:
            print("  ✓ %s" % desc); PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ok = dict(manifest_names=[A, B], library=[A, B], page_refs=[A, B], dist_names=[A, B])
    run("1) 基线：四方一致（必须通过）", expect_fail=False,
        want="四方一致", **ok)
    run("2) 库内有图但 manifest 没登记（必须报）", want="[未登记]",
        manifest_names=[A], library=[A, B], page_refs=[A, B], dist_names=[A, B])
    run("3) manifest 登记了但库内没有（必须报）", want="[空登记]",
        manifest_names=[A, B], library=[A], page_refs=[A, B], dist_names=[A, B])
    run("4) 库内有图但没有任何发布页引用（必须报）", want="[孤儿图]",
        manifest_names=[A, B], library=[A, B], page_refs=[A], dist_names=[A, B])
    run("5) 页面引用了但库内没有（必须报）", want="[缺图]",
        manifest_names=[A, B], library=[A, B], page_refs=[A, B, "cc-missing.png"], dist_names=[A, B])
    run("6) 库内有图但 dist 没打包（必须报）", want="[未打包]",
        manifest_names=[A, B], library=[A, B], page_refs=[A, B], dist_names=[A])
    run("7) 不误伤：账本 PROGRESS.md 重复引用不影响判账（必须放行）", expect_fail=False,
        want="四方一致",
        manifest_names=[A, B], library=[A, B], page_refs=[A, B], dist_names=[A, B],
        extra_pages={"PROGRESS.md": f"# 台账\n\n![x](screenshots/{A})\n![x](screenshots/{B})\n"})

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
