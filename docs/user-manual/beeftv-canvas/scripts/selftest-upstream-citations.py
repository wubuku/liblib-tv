#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 47 的反向验证：**只装语料，代码从真树跑**。

**为什么反验只摆语料、不摆闸的代码**（Batch 336 实测）：那一次把判据的根写成了
`os.path.dirname(HERE)`，而页面清单来自 `scope.published_paths()`（认 `BEEFTV_MANUAL_ROOT`）——
**于是清单读夹具、正文读真手册，3 个用例全部报绿且输出为真**。
**把 `scripts/` 一起搬进沙箱的话，那一类「核错对象」的回归根本测不出来**：
沙箱里的判据与沙箱里的语料会自洽地一起错。

用例分成**必须成对**的几对（纪律 264）：

  · **方向一（引用必须能解析）**：能抓（路径改成不存在的）↔ 不误伤（两个版本都有的引用、
    且那一段**故意不带任何版本词**——**它本来就不该被要求带**）。
  · **方向二（单边引用必须点名版本）**：能抓（把版本词删掉）↔ 不误伤（版本词留着）。
  · **表格行不继承**：能抓（上一行写了版本、本行没写，**必须报**）
    ↔ 不误伤（同一行自己写了版本）。
  · **rc=2**：沙箱里没有 `20-reference.md` → 基线读不出来 → **必须报 rc=2，不是 rc=1**。
    **「本轮根本没开始核」与「核出不一致」在结果里长得一样时，修法会被引向完全不同的方向**
    （`baseline.py` 的 docstring 整段在讲这件事）。
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from stagedeps import child_env                                        # noqa: E402

ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-upstream-citations.py")
CONFIG = os.path.join(ROOT, ".vitepress", "config.mjs")
PAGE = "10-tasks/probe-page.md"
REFERENCE = "20-reference.md"

#: 语料里用的三条真实上游路径，**分别在两个 ref 上实测过存在性**：
#: `BOTH` 两个版本都有；`CUR` 只有 `origin/main` 有；`BASE` 只有基线有。
BOTH = "web/src/main.tsx"
CUR = "web/src/pages/agents/index.tsx"
BASE = "web/src/components/canvas/canvas-creative-interaction.tsx"
GONE = "web/src/definitely-not-here-341.tsx"

BASE_PAGE = """# 探针页

这一段引用一个两个版本都有的文件（`%s`），**而这一段故意不带任何版本词**——
因为两个版本都有的引用本来就不该被要求点名版本。

这一段引用一个只有当前版本才有的文件（`%s`），
**所以这一段必须点名版本**，下面就点名：v1.7.3 起才有。
""" % (BOTH, CUR)

#: **方向一的不误伤那半**：整页只有一条「两个版本都有」的引用，且不带版本词。
BOTH_ONLY_PAGE = """# 只有两边都有的引用

这一段引用 `web/src/main.tsx`，**两个版本都有它**，
**所以这一段连版本词都不该有**——要求它点名版本就是误伤。
"""

#: **方向二的不误伤那半**：整页只有一条「只有当前有」的引用，且本段点了名。
CUR_ONLY_PAGE = """# 只有当前才有的引用

这一段引用 `web/src/pages/agents/index.tsx`，**基线上没有这个文件**，
**所以本段必须点名版本**：v1.7.3 起才有。
"""

#: **同一段、同一个文件，只把版本词拿掉**——方向二的能抓那半。
CUR_ONLY_NOVER_PAGE = """# 只有当前才有的引用

这一段引用 `web/src/pages/agents/index.tsx`，**基线上没有这个文件**，
**所以本段必须点名版本**——而下面这份语料**偏偏就不点名**。
"""

#: **只在基线才有的那条**，方向二的另一半（当前那半之外）。
BASE_ONLY_PAGE = """# 只在基线才有的文件

这一段引用 `web/src/components/canvas/canvas-creative-interaction.tsx`，
**v1.7.3 已经把这个文件整个删掉了**，所以本段点名的是基线：v1.6.22 上它在。
"""

BASE_ONLY_NOVER_PAGE = """# 只在基线才有的文件

这一段引用 `web/src/components/canvas/canvas-creative-interaction.tsx`，
**而下面这份语料偏偏不点名任何版本**——读者就不知道该去哪一版找它。
"""

TABLE_PAGE = """# 表格探针

| 路由 | 说明 |
| --- | --- |
| `/agents` | **这一行点名了版本**：v1.7.3 才有，引用 `web/src/pages/dev/assistant-panel-lab.tsx` |
| `/quiet` | **这一行引用了只有当前才有的文件，却故意不点名版本**（`web/src/pages/agents/index.tsx`）——而上一行点名了，**表格行不继承上一行的版本词** |
"""

TABLE_PAGE_OK = """# 表格探针

| 路由 | 说明 |
| --- | --- |
| `/agents` | **这一行点名了版本**：v1.7.3 才有，引用 `web/src/pages/dev/assistant-panel-lab.tsx` |
| `/quiet` | **这一行自己点名版本**：v1.7.3 起才有，引用 `web/src/pages/agents/index.tsx` |
"""

REFERENCE_TEXT = """# 参考：探针

### 取证基线

- **版本**：v1.6.22
- **提交**：bcc3b05
"""

PASS = VOID = FAIL = 0

#: **被测闸门与它的本地依赖闭包，必须一起搬进沙箱**（闸 17 方向一）。
#: 闭包是量出来的、不是猜的：`verify-upstream-citations.py` 本地 import `scope` 与
#: `baseline`，而 `baseline` 再 import `beefsrc`——**漏掉最后一层，临时目录里
#: import 失败，而 `build-site.sh` 仍然全绿**（闸 17 自己的报法，Batch 178 实测 34 例）。
#:
#: **而搬代码进来不违反 Batch 336 那条「反验只装语料」**：
#: 那一条针对的是**判据自己把根从脚本位置推出来**（`os.path.dirname(HERE)`），
#: 于是清单读夹具、正文读真手册。本闸的根来自 `scope.ROOT`（认 `BEEFTV_MANUAL_ROOT`），
#: **所以它在沙箱里读的就是沙箱**——**这恰恰是搬进来才能验的那件事**。
GATE_DEPS = ("scope.py", "baseline.py", "beefsrc.py")


def run(desc, want_rc, want_substr, page_text=BASE_PAGE, with_reference=True):
    """跑一轮。`want_rc` 钉死，**不靠「非 0 即算过」**。"""
    global PASS, VOID, FAIL
    tmp = tempfile.mkdtemp(prefix="beef-citation-selftest.")
    try:
        os.makedirs(os.path.join(tmp, ".vitepress"), exist_ok=True)
        shutil.copyfile(CONFIG, os.path.join(tmp, ".vitepress", "config.mjs"))
        os.makedirs(os.path.join(tmp, os.path.dirname(PAGE)), exist_ok=True)
        with open(os.path.join(tmp, PAGE), "w", encoding="utf-8") as fh:
            fh.write(page_text)
        if with_reference:
            with open(os.path.join(tmp, REFERENCE), "w", encoding="utf-8") as fh:
                fh.write(REFERENCE_TEXT)
        gate = os.path.join(tmp, "scripts", os.path.basename(GATE))
        os.makedirs(os.path.dirname(gate), exist_ok=True)
        shutil.copyfile(GATE, gate)
        for dep in GATE_DEPS:
            shutil.copyfile(os.path.join(HERE, dep), os.path.join(tmp, "scripts", dep))
        env = child_env(tmp)
        r = subprocess.run([sys.executable, gate], cwd=tmp,
                           capture_output=True, text=True, env=env)
        out = r.stdout + r.stderr
        if r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际输出：" % (desc, r.returncode, want_rc))
            print("      " + out.strip().replace("\n", "\n      ")[:400])
            FAIL += 1
            return
        if want_substr and want_substr not in out:
            print("  ✗ %s：退出码对了但输出里没有 %r —— **它没在做它声称的事**"
                  % (desc, want_substr))
            print("      " + out.strip().replace("\n", "\n      ")[:400])
            FAIL += 1
            return
        print("  ✓ %s" % desc)
        PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def swap(old, new):
    def _f(text):
        assert old in text, "语料里没有 %r —— 语料改过了，注入会空转" % old
        out = text.replace(old, new, 1)
        assert out != text, "替换前后逐字相同 → **本用例作废**（静默空转）"
        return out
    return _f


def main():
    print("闸 47 反向验证：10 例（1 基线 / 4 能抓 / 4 不误伤 / 1 未能核对 rc=2）")

    # 基线：一条两 ref 都有的引用（无版本词）+ 一条只有当前有的引用（本段点了名）。
    run("基线：引用都能解析、单边引用本段已点名版本", 0, "每条引用都能在两个 ref 之一逐字找到")

    # ── 方向一（引用必须能解析）成对 ──
    run("不误伤（方向一）：两个版本都有的引用、本段不带版本词 → 必须放行",
        0, "每条引用都能在两个 ref 之一逐字找到", page_text=BOTH_ONLY_PAGE)
    run("能抓（方向一）：路径改成不存在的 → 必须报并点名",
        1, GONE, page_text=swap(BOTH, GONE)(BOTH_ONLY_PAGE))

    # ── 方向二（单边引用必须点名版本）成对，两侧各一对 ──
    run("不误伤（方向二·当前侧）：只有当前才有的引用、本段点了名 → 必须放行",
        0, "每条引用都能在两个 ref 之一逐字找到", page_text=CUR_ONLY_PAGE)
    run("能抓（方向二·当前侧）：同一段拿掉版本词 → 必须报并点名",
        1, "没有点名任何版本", page_text=CUR_ONLY_NOVER_PAGE)
    run("不误伤（方向二·基线侧）：只有基线才有的引用、本段点了基线 → 必须放行",
        0, "每条引用都能在两个 ref 之一逐字找到", page_text=BASE_ONLY_PAGE)
    run("能抓（方向二·基线侧）：同一段拿掉版本词 → 必须报并点名",
        1, "没有点名任何版本", page_text=BASE_ONLY_NOVER_PAGE)

    # ── 表格行不继承：成对 ──
    run("能抓（表格行）：上一行点名了版本、本行没点名 → 必须报",
        1, "没有点名任何版本", page_text=TABLE_PAGE)
    run("不误伤（表格行）：本行自己点名了版本 → 放行",
        0, "每条引用都能在两个 ref 之一逐字找到", page_text=TABLE_PAGE_OK)

    # rc=2：沙箱里没有 20-reference.md。
    run("rc=2：沙箱里没有 20-reference.md → 基线读不出来，必须报「未能核对」",
        2, "[skip]", with_reference=False)

    total = PASS + VOID + FAIL
    print("闸 47 反验：通过 %d / 失败 %d / 作废 %d = %d" % (PASS, FAIL, VOID, total))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
