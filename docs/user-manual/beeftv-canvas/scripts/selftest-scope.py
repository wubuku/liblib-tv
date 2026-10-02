#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 24 `verify-scope.py` 的反向验证（Batch 190 新增）。

**必须成对**：既有「能抓到」的用例，也有「不该误伤」的用例。
只测前者，判据可以靠恒真通过全部用例；只测后者，判据可能已经坏了。
（Batch 189 纪律 152：反验失效只是沉默，比判据失效更隐蔽。）

**为什么在临时树里造样本，而不是改真手册**：被注入的缺陷必须能随意造、随意撤销，
而真手册是别的开发者也在读的东西。临时树还顺带验证了 `BEEFTV_MANUAL_ROOT`
这条注入路径本身可用——**闸 17 的方向二就是为它存在的**
（被搬运的模块不得靠 `__file__` 推断仓根，除非支持外部注入）。

五例：

  1. **能抓**：读者页清单里混进一个 `srcExclude` 排除的文件 → 必须 rc=1 且点名该文件；
  2. **能抓**：`srcExclude` 写了一个手册树里不存在的名字 → 必须 rc=1（方向二）；
  3. **能抓**：清单里点名一个**谁都没有**的文件（拼错的基名）→ 必须 rc=1；
  4. **不误伤**：干净树。含「排除集完整副本」「排除集的一个子集」「纯发布页清单」
     三种形态的清单，全部必须放过——**这一例是本闸假阳性率的量尺**：
     第一版判据（核所有出现的 md 文件名）在这一例上会报 5 处，全是假的；
  5. **rc=2**：`config.mjs` 读不到 → 必须 rc=2「未能核对」，**不是 rc=0**。
     **不能让判据在事实源读空时安静地全绿**（纪律 101，
     与 Batch 157「工具失败被当成零命中」同一个病）。

退出码：0 全部通过；1 有用例失败。
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = "verify-scope.py"
MODULE = "scope.py"

# 一棵最小的手册树：3 个会发布的页面 + 2 个内部资料。
PUBLISHED = ("README.md", "20-reference.md", "10-tasks/generate-video.md")
EXCLUDED = ("AUDIT.md", "PUBLISH.md")
CONFIG = "srcExclude: ['**/AUDIT.md', '**/PUBLISH.md'],\n"

# 干净树里的三种清单形态——用例 4 要它们全部被放过。
CLEAN_LISTS = """
# 发布页清单：全是会发布的文件
PAGES = ["README.md", "20-reference.md"]
# 排除集的完整副本
SRC_EXCLUDE_BASENAMES = ["AUDIT.md", "PUBLISH.md"]
# 排除集的一个子集（闸 9 的 EXTRA_SCAN_FILES 就是这个形状）
EXTRA_SCAN_FILES = ["PUBLISH.md"]
"""


def build_tree(root, config=CONFIG, files=PUBLISHED + EXCLUDED):
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(root, ".vitepress"), exist_ok=True)
    os.makedirs(os.path.join(root, "10-tasks"), exist_ok=True)
    if config is not None:
        with open(os.path.join(root, ".vitepress", "config.mjs"), "w",
                  encoding="utf-8") as fh:
            fh.write(config)
    for rel in files:
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# %s\n" % rel)
    # **两份都显式搬，目标路径里写死文件名，不用 `for name in (GATE, MODULE)`**
    # （Batch 190）：循环搬运对闸 17 是**静态不可判定**的——它的方向一要核
    # 「这个本地模块有没有被搬」，而模块名在循环里只是元组里的一个字符串，
    # AST 看不到它和 copy 动作之间的关系（闸 17 会报成「没搬」，
    # **而反验实测把两份都搬了——判据红不等于事实红**）。
    # **与其为一个写法新增一套必须维护的契约，不如把写法写成可判定的。**
    # 目标里写死 `"scope.py"` 也是更清楚的写法：搬到哪里本来就是确定的事。
    # （闸 17 本批修的三处都是同一个病的反面：判据认写法。**别再制造第四种写法。**）
    shutil.copy(os.path.join(HERE, GATE), os.path.join(root, "scripts", GATE))
    shutil.copy(os.path.join(HERE, MODULE), os.path.join(root, "scripts", "scope.py"))


def write_list(root, const, values):
    with open(os.path.join(root, "scripts", "verify-demo.py"), "w",
              encoding="utf-8") as fh:
        fh.write("%s = %r\n" % (const, values))


def run(root):
    env = dict(os.environ)
    env["BEEFTV_MANUAL_ROOT"] = root          # 反验搬了闸门，必须显式指回这棵树
    env["PYTHONDONTWRITEBYTECODE"] = "1"      # 别在临时树里留 __pycache__
    p = subprocess.run([sys.executable, os.path.join(root, "scripts", GATE)],
                       capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    failures = []
    root = tempfile.mkdtemp(prefix="scope-selftest-")
    try:
        def case(name, want_rc, want_in, prepare):
            tree = os.path.join(root, name)
            os.makedirs(tree, exist_ok=True)
            prepare(tree)
            rc, out = run(tree)
            ok = (rc == want_rc) and (want_in in out)
            print("  %s 用例 %-22s rc=%d（期望 %d）%s"
                  % ("✅" if ok else "❌", name, rc, want_rc,
                     "" if ok else "\n      输出:\n      " + out.strip().replace("\n", "\n      ")))
            if not ok:
                failures.append(name)

        def clean(tree):
            build_tree(tree)
            write_list(tree, "PAGES", ["README.md"])

        # 1 —— 能抓：读者页清单混进被排除的文件（这正是本批抓到的真缺陷形状）
        def mixed(tree):
            clean(tree)
            write_list(tree, "PAGES", ["README.md", "AUDIT.md"])
        case("mixed-list", 1, "混装", mixed)

        # 2 —— 能抓：srcExclude 指向一个不存在的文件
        case("ghost-exclude", 1, "方向二",
             lambda tree: (build_tree(
                 tree, config=CONFIG.replace("**/AUDIT.md", "**/GHOST.md")),
                 write_list(tree, "PAGES", ["README.md"])))

        # 3 —— 能抓：清单点名一个谁都没有的文件（拼错的基名）
        case("absent-name", 1, "不存在", lambda tree: (
            clean(tree), write_list(tree, "PAGES", ["README.md", "GONE.md"])))

        # 4 —— 不误伤：三种合法清单形态全部放过（假阳性率的量尺）
        def tidy(tree):
            build_tree(tree)
            with open(os.path.join(tree, "scripts", "verify-demo.py"), "w",
                      encoding="utf-8") as fh:
                fh.write(CLEAN_LISTS)
        case("no-false-positive", 0, "发布范围一致", tidy)

        # 5 —— 事实源读不到必须 rc=2，不能是 rc=0
        case("no-config-rc2", 2, "未能核对",
             lambda tree: build_tree(tree, config=None))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print()
    if failures:
        print("❌ %d/%d 例失败：%s" % (len(failures), 5, "、".join(failures)))
        return 1
    print("✅ 5/5 例通过（3 例能抓 + 1 例不误伤 + 1 例 rc=2）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
