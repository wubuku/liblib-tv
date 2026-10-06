#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 22「手册正文引号文案标点漂移」的反向验证（Batch 185）。

用例清单：
  1  注入一处标点漂移（把正确文案改成少一个逗号）   → 必报
  2  注入一处**括号**漂移                            → 必报
  3  **不误伤**：手册自己的术语（「画布文件夹」这类两词撞出来的）→ 不得报
  4  **不误伤**：`/` 与 `→` 并列两个独立文案的写法    → 不得报
  5  自检探针失配（ref 指到没有该文案的版本）        → 必须 rc=2「未能核对」
  6  **任务页也在扫描范围内**（Batch 186 扩进来的）  → 往任务页注入漂移必须报
  7  真实现状                                        → 不报
  8  **不误伤**（Batch 304）：那个「证人字面量」只住在 `web/test/` → 不得报
  9  **能抓**（Batch 304）：同一个字面量搬进 `web/src/` → 必须报

**用例 3 是本闸第一版真实误报过的一条**：第一版把**整份语料**归一化后做子串匹配，
于是「画布文件夹」也能在上游对上（某处「画布」后面紧接着出现「文件夹」）——
**一条根本没有标点可漂移的纯文字被报成标点漂移**。修法是归一化比对落在
**源码的字符串字面量集合**上（字面量内部不会出现拼接）。用例 3 钉住这个修法。

**用例 5 单独存在的理由**：判据的方向二拿一条**只存在于 backend 的**已知文案当探针，
若它在上游语料里找不到，说明语料读取或 ref 出了问题。**此时必须 rc=2**——
**不能让判据在一个空语料上安静地全绿**（纪律 101：解析器退化必须表现为失败，不是通过）。

**用例 8/9 是一对，钉的是 Batch 304 那条语料范围修法**：判据第二臂读的是
**带引号的字符串字面量集合**，而**JSX 文本没有引号**——于是「这条文案在上游存不存在」
在第二臂上只能靠**别处恰好有个同字字面量**来回答，而**测试文件正是最容易提供这种巧合的地方**。
真上游就是这么误报的：上游 `web/test/canvas-folder-storage.test.ts` 里有 4 处恰好是 `新建`
的字面量，把一条从未触发过的分支激活，误报手册两处「+ 新建」——**而上游渲染的是
`{<Plus />}>新建</Button>`，那个 `+` 是图标**。修法是语料剔掉测试文件。
**而这条修法必须钉成一对**：只有 8 不写 9，「剔测试」就是把判据改瞎了也没人知道的改法；
只有 9 不写 8，修法没上线就已经是绿的。**两侧各跑一次，唯一变量是那个字面量住在哪个文件。**
"""

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "verify-quote-punct.py")
README = os.path.join(ROOT, "README.md")
CONCEPTS = os.path.join(ROOT, "30-concepts.md")
TASKPAGE = os.path.join(ROOT, "10-tasks", "timeline-export.md")
DRIFT_BASE = "视频已生成，但暂时无法取回"     # 上游逐字原文
INJECTED = "视频已生成但暂时无法取回"        # 少一个逗号 —— 本闸要抓的形态

# ── Batch 304：语料范围（测试文件里的字面量不算「上游存在」）────────────
#: 上游**带引号**的原文。逗号在里面，而判据要抓的正是「逗号没了」。
PRESET_LITERAL = "保存当前画布为预设，请确认"
#: 手册抄成的形态：少一个逗号。**归一化之后与上面那个逐字相同**——
#: 所以它在第二臂上必然命中，区别只在**那个命中它的字面量住在哪个文件里**。
PRESET_INJECT = "保存当前画布为预设请确认"
SANDBOX_PAGE = "30-concepts.md"
#: 判据方向二的自检探针，**必须逐字在合成仓的产品侧**——否则两道新用例会得到 rc=2
#: 而不是它们各自要断言的那个值，而**rc=2 长得和「没报」一样**，用例就废了。
GATE_PROBE = "云端画布已有更新，已停止覆盖；请保留本地草稿并加载最新版本"

results = []


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, t):
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def run(env=None):
    e = dict(os.environ)
    e.update(env or {})
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True, env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def check_anchor():
    t = read(README)
    assert DRIFT_BASE in t, "前提失配：README.md 里找不到上游逐字原文 %s" % DRIFT_BASE
    c = read(CONCEPTS)
    assert "画布文件夹" in c, "前提失配：30-concepts.md 里找不到「画布文件夹」样本"


# ── 1 少一个逗号 → 必报 ─────────────────────────────────────────────
def m_missing_comma_must_report():
    check_anchor()
    orig = read(README)
    try:
        write(README, orig.replace(DRIFT_BASE, INJECTED))
        assert INJECTED in read(README), "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "标点漂移" in out
        record("1 少一个逗号 → 必报", ok, f"rc={rc}")
    finally:
        write(README, orig)


# ── 2 多一个括号 → 必报 ─────────────────────────────────────────────
def m_extra_paren_must_report():
    check_anchor()
    orig = read(README)
    try:
        injected = DRIFT_BASE.replace("，尚未", "（尚未")
        bad = "本地任务保存失败（尚未提交生成）"
        write(README, orig.replace(DRIFT_BASE, bad))
        assert bad in read(README), "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "标点漂移" in out
        record("2 多一个括号 → 必报", ok, f"rc={rc}")
    finally:
        write(README, orig)


# ── 3 手册自己的术语不得误报（两词撞出来的纯文字）────────────────────
def m_own_term_must_not_report():
    check_anchor()
    rc, out = run()
    ok = rc == 0 and "画布文件夹" not in out
    record("3 手册自己的术语 → 不得误报（第一版真实误报过）", ok, f"rc={rc}")


# ── 4 `/` 与 `→` 并列写法不得误报 ────────────────────────────────────
def m_joined_writing_must_not_report():
    check_anchor()
    # 样本**跨全部页面**找：`/` 写法在 90-troubleshooting.md、`→` 在 README/快速开始。
    # 第一版只在 README 里找，于是这一例**作废**——而作废必须计入失败，
    # 否则「不误伤」那一半就等于没测（Batch 178：反验静悄悄失效只产生沉默）。
    pages = ["README.md", "00-quickstart.md", "20-reference.md",
             "30-concepts.md", "90-troubleshooting.md", "PUBLISH.md"]
    all_text = "".join(read(os.path.join(ROOT, x)) for x in pages)
    assert re.search(r"「[^」]*→[^」]*」", all_text), "前提失配：全部页面里找不到 → 并列样本"
    assert re.search(r"「[^」]*\u002f[^」]*」", all_text), "前提失配：全部页面里找不到 / 并列样本"
    rc, out = run()
    ok = rc == 0
    record("4 「/」「→」并列写法 → 不得误报", ok, f"rc={rc}")


# ── 5 自检探针失配 → 必须 rc=2 ──────────────────────────────────────
def m_probe_mismatch_must_be_rc2():
    check_anchor()
    # 指到一个早于该文案的版本：backend 里那条是后加的，
    # 探针应当找不到 → 判据必须说「未能核对」而不是「全部通过」
    rc, out = run(env={"BEEFTV_REF": "be409634"})
    ok = rc == 2 and "未能核对" in out
    record("5 自检探针失配 → 必须 rc=2 未能核对", ok, f"rc={rc}")


# ── 6 任务页也在扫描范围内（Batch 186 把范围从 6 个文件扩到 36 个）──
def m_task_page_in_scope():
    check_anchor()
    t = read(TASKPAGE)
    assert "视频处理" in t, "前提失配：任务页里找不到「视频处理」样本"
    orig = t
    try:
        # **注入必须是标点漂移，不能是首尾空白**——第一版我在引号尾部塞了个空格，
        # 而判据本来就会 strip() 首尾空白，于是它理直气壮地没报。
        # **用例自己挑了一个判据本来就该忽略的形态，那这一例测的是判据的 strip，不是它。**
        write(TASKPAGE, orig.replace("点「视频处理」下拉", "点「视频处理：」下拉"))
        after = read(TASKPAGE)
        assert "点「视频处理：」下拉" in after, "前提失配：注入没生效"
        rc, out = run()
        ok = rc == 1 and "timeline-export.md" in out and "标点漂移" in out
        record("6 任务页在扫描范围内 → 注入漂移必报", ok, f"rc={rc}")
    finally:
        write(TASKPAGE, orig)


# ── 7 真实现状 ──────────────────────────────────────────────────────
def m_clean_pass():
    check_anchor()
    rc, out = run()
    record("7 真实现状 → 不报", rc == 0, f"rc={rc}")


# ── 8/9 语料范围：证人住在产品侧还是测试侧 ─────────────────────────────
def _git(args, cwd):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, "合成仓 git %s 失败：%s" % (args[0], (r.stderr or "")[:200])
    return r.stdout.strip()


def build_synth_src(dst):
    """造一棵**合成上游仓**：两个 commit，唯一的差别是那个证人字面量住在产品侧还是测试侧。

    返回 `(产品侧 commit, 测试侧 commit)`。

    **为什么要合成，而不是拿真上游那份测试文件当证人**：
    真上游的误伤来自 `web/test/canvas-folder-storage.test.ts`，**而钉住它不能靠那份文件一直在**——
    它哪天改名，这条用例就作废（作废会被计成失败，于是每次上游改名都要有人来改这条用例）。
    合成仓把「**证人放哪**」变成唯一变量，**两侧各跑一次就是一对真正的鉴别力对照**：
    同一份手册、同一段注入文案、同一段判据逻辑，**只有一个字节的归属不同**。

    **另一个刻意：产品侧必须凑够 1200 个字面量**，因为判据有一条
    「字面量少于 1000 个就算提取规则退化、rc=2」的守卫——
    **合成仓太小就会让两道新用例拿 rc=2 冒充 rc=0**（判据的输出里那个 2 与 0 长得不一样，
    但「没报出来的问题」与「没核对」在用例里极易写混，所以这里让用例显式断言 rc 值）。
    """
    os.makedirs(os.path.join(dst, "backend", "handler"))
    os.makedirs(os.path.join(dst, "web", "src", "pages"))
    _git(["-c", "init.defaultBranch=main", "init", "-q"], dst)

    filler_go = "\n".join('    "占位后端-%04d",' % i for i in range(1, 601))
    write(os.path.join(dst, "backend", "handler", "version.go"),
          "package handler\n\nconst VersionProbe = \"%s\"\n\nvar FillerStrings = []string{\n%s\n}\n"
          % (GATE_PROBE, filler_go))
    filler_ts = "\n".join('  "占位网页-%04d",' % i for i in range(1, 601))

    # commit A：证人在**产品**侧（`web/src/pages/demo.tsx`）
    write(os.path.join(dst, "web", "src", "pages", "demo.tsx"),
          'export const PRESET_HINT = "%s";\nexport const Filler = [\n%s\n];\n'
          % (PRESET_LITERAL, filler_ts))
    _git(["add", "-A"], dst)
    _git(["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "A"], dst)
    sha_product = _git(["rev-parse", "HEAD"], dst)

    # commit B：同一个字面量**搬进测试文件**，产品侧换成另一句
    write(os.path.join(dst, "web", "src", "pages", "demo.tsx"),
          'export const PRESET_HINT = "这一版里没有那句提示";\nexport const Filler = [\n%s\n];\n'
          % filler_ts)
    os.makedirs(os.path.join(dst, "web", "test"))
    write(os.path.join(dst, "web", "test", "demo.test.ts"),
          'it("预设提示", () => {\n  expect(PRESET_HINT).toBe("%s");\n});\n' % PRESET_LITERAL)
    _git(["add", "-A"], dst)
    _git(["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "B"], dst)
    sha_test = _git(["rev-parse", "HEAD"], dst)
    return sha_product, sha_test


def build_sandbox_manual(dst):
    """手册树沙箱：整份 `scripts/` + 会被本闸扫到的全部 `.md`。**真手册一个字都不动。**

    **前 7 条用例都是原地改真手册再恢复**（Batch 185 起的写法）。本批改成沙箱，
    理由是这两条用例要跑**两道**判据调用，而原地改两次真手册树就多两次
    「崩在中途留下脏文件」的机会——**而恢复动作写在 `finally` 里，
    可 `finally` 拦不住 `os._exit` 与断电**。
    """
    os.makedirs(dst)
    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(dst, "scripts"))
    for name in sorted(os.listdir(ROOT)):
        if name.endswith(".md"):
            shutil.copy2(os.path.join(ROOT, name), os.path.join(dst, name))
    tasks = os.path.join(dst, "10-tasks")
    os.makedirs(tasks)
    for name in sorted(os.listdir(os.path.join(ROOT, "10-tasks"))):
        if name.endswith(".md"):
            shutil.copy2(os.path.join(ROOT, "10-tasks", name), os.path.join(tasks, name))


def run_range_case(ref_key):
    """在沙箱里造一棵手册树 + 一棵合成上游仓，注入同一段文案，按 `ref_key` 跑一次判据。"""
    tmp = tempfile.mkdtemp(prefix="qp304-")
    try:
        src_dir = os.path.join(tmp, "src")
        os.makedirs(src_dir)
        sha_product, sha_test = build_synth_src(src_dir)
        ref = sha_product if ref_key == "product" else sha_test

        manual_dir = os.path.join(tmp, "manual")
        build_sandbox_manual(manual_dir)
        page = os.path.join(manual_dir, SANDBOX_PAGE)
        orig = read(page)
        try:
            # **注入锚点必须在改前改后都存在**：锚句取自真实正文，且只用一次，
            # 所以注入后「锚句消失、注入句出现」两件事都能断言（纪律：锚点只钉一个方向会空转）。
            assert PRESET_LITERAL not in orig, "前提失配：合成仓那句原文已经出现在正文里"
            anchor = orig.split("\n")[0]
            assert anchor, "前提失配：%s 第一行是空的" % SANDBOX_PAGE
            injected = anchor + "\n\n上句为「%s」。\n" % PRESET_INJECT
            write(page, injected + orig.split("\n", 1)[1])
            after = read(page)
            assert "「%s」" % PRESET_INJECT in after, "前提失配：注入没生效"
            # 锚句在正文里可能出现多次（H1 与标题行），所以比**出现次数**而不是「还在不在」——
            # 「还在不在」会被一个恰好重复出现的锚句变成一个永远为真的断言。
            assert after.count(anchor) == orig.count(anchor), "前提失配：注入动到了锚句以外的内容"

            e = dict(os.environ)
            e["BEEFTV_SRC"] = src_dir
            e["BEEFTV_REF"] = ref
            gate = os.path.join(manual_dir, "scripts", "verify-quote-punct.py")
            r = subprocess.run([sys.executable, gate], cwd=manual_dir,
                               capture_output=True, text=True, env=e)
            return r.returncode, (r.stdout or "") + (r.stderr or "")
        finally:
            # 沙箱整棵会被删掉，这一步只是让「真手册没被动过」不依赖 tmp 的清理时机
            write(page, orig)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def m_witness_in_test_must_not_report():
    """**证人在测试文件里 → 不得报**（Batch 304 钉住的那条修法）。"""
    rc, out = run_range_case("test")
    ok = rc == 0 and "标点漂移核对通过" in out
    record("8 证人只在测试文件里 → 不得报", ok, f"rc={rc}")


def m_witness_in_product_must_report():
    """**同一个字面量搬进产品侧 → 必须报**（钉住「剔测试没有把判据削瞎」）。

    **这一例与用例 8 是一对**：同一段手册注入、同一段判据逻辑、同一棵树，
    唯一差别是那个字面量住在 `web/src/pages/` 还是 `web/test/`。
    **只有用例 8 而没有这一例，「剔测试」就是一条把判据改瞎了也没人知道的改法**——
    而 Batch 303 那条误报恰恰是**潜伏了很久才浮上来**的。
    """
    rc, out = run_range_case("product")
    ok = (rc == 1 and SANDBOX_PAGE in out and PRESET_INJECT in out
          and "标点漂移" in out)
    record("9 证人搬进产品侧 → 必须报（证明没削掉鉴别力）", ok, f"rc={rc}")


def main():
    tests = [m_missing_comma_must_report, m_extra_paren_must_report,
             m_own_term_must_not_report, m_joined_writing_must_not_report,
             m_probe_mismatch_must_be_rc2, m_task_page_in_scope, m_clean_pass,
             m_witness_in_test_must_not_report, m_witness_in_product_must_report]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", f"前提失配：{exc}")
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print(f"  {mark} {name}  {detail}")
        # **「作废」必须计入失败**——它意味着这一例什么都没测，
        # 而反验一旦在某处空转，报出来的是「通过」，不是「我没测」（纪律 102）
        if status != "通过":
            failed += 1
    print(f"闸 22 反验：{len(results)} 例，通过 {len(results) - failed}，失败/作废 {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
