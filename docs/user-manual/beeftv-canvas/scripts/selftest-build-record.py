#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 17 之外的一条判据的反向验证：「本次提交新增的批次行，有没有为它跑过一次绿构建」。

**它守的是什么**：Batch 252/253 的构建实测各有一个 `[ FAIL ]` 且都停在闸 18，
**闸 19 到 36 与全部文档闸一次都没运行**，而我照常提交了，
批次行里写的验收结论是「构建仍全绿」（纪律 280）。
**整套体系里唯一没有被机械化的一环是「有人看了构建的退出码」——
而这一份反验守的就是它的替代物：`build-site.sh` 走到末尾时自己写下记录，
提交前钩子据此拒绝。**

用例清单：
  1  新增批次行 > 记录里的批次号   → 必报（**能抓**，这正是 253 那一次）
  2  新增批次行 == 记录里的批次号   → **不得**报（不误伤）
  3  完全没有记录文件               → 必报（**「没查过」不等于「没问题」**）
  4  diff 里没有新增批次行          → **不得**报（普通文档提交不受影响）
  5  记录文件坏了（batch 不是整数） → 必报（**坏记录按没有绿构建处理**）
  6  新增批次行 < 记录里的批次号   → **不得**报（回填旧批次是合法操作）
  7  `added_batch_numbers` 的形态   → 认 `| 255 |`、忽略 `+++ b/…` 头、
                                      忽略已存在的 `-` 行、认 `+|| 255 |` 之外的空格变体
  8  `newest_batch()` 不被字符串序骗 → 字符串 max 是 `99`（子批次 `17c` 与非排序表），
                                      **纯数字 max 必须是 254**
  9  `ok`/`warn` 计数器 == 实际打印行数 → **从真 `build-site.sh` 里抠出函数真跑**
 10  传 `--counts 0,0,0`            → **rc=2 且不写记录**
     （**本批当场撞上的真缺陷**：第一版从日志正则数 `[ ok ]`，
      `^\[\s*ok\s*\]` 与真格式 `[  ok  HH:MM:SS]` 失配，
      **写下了 `0 ok / 0 warn / 0 FAIL` 而 rc=0**——一个自洽的假数比没有数更坏）
 12  `build-site.sh` 里没有 `| while` → **子 shell 会吞掉计数器**；
     实测第一次全绿构建记的是 `45 ok` 而日志里有 **82** 行 `[ ok ]`
 13  herestring 循环里计数器累加     → **12 的行为对照**（只测 12 的话，
     把 herestring 写成空循环也能全过）
 11  `fail()` 仍然 `exit 1`        → **整套机制的前提是「构建能红」**；
     本批改过这三个函数，**改坏了 `fail()` 会让构建永远绿，
     于是记录永远写着「绿」——那比没有这个机制更坏**

**为什么全部在临时记录路径上跑**：`buildrecord.record_path()` 指向真 `.git/`，
**而反验绝不能碰它**——**一条为了验判据而弄坏判据自己的状态，反验就白跑了**
（纪律 156/178）。做法是 monkeypatch 那个函数，**不给生产代码留环境变量后门**。
"""

import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RECORDER = os.path.join(HERE, "record-build-result.py")
BUILD = os.path.join(ROOT, "build-site.sh")


#: **`buildrecord` 用普通 import 而不是 `importlib`**——
#: **闸 18 方向三的 `_imported_modules()` 走 AST、只认真正的 import 语句**，
#: **而第一版用 `spec_from_file_location` 动态加载它，于是判据看不到我在测什么**。
#: **而它本来就该用普通 import**（`HERE` 就在 `sys.path` 上），
#: **动态加载是我自己加的、而且没有任何理由**（纪律 171：不要为了什么而写什么）。
sys.path.insert(0, HERE)
import buildrecord          # noqa: E402


def _load(name, path):
    """**只用于 `record-build-result.py`**——它的文件名带连字符，
    **`import record_build_result` 在语法上就不成立**。
    **这才是 `importlib` 唯一站得住的用法**，其余一律用普通 import。"""
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

results = []
_TMP = tempfile.mkdtemp(prefix="beeftv-buildrecord-selftest.")
_REAL_PATH = buildrecord.record_path


def use_record(text):
    """把 `buildrecord.record_path` 指到临时文件上，**并在用例结束后还原**。"""
    p = os.path.join(_TMP, "record")
    if text is None:
        if os.path.exists(p):
            os.remove(p)
    else:
        with io.open(p, "w", encoding="utf-8") as f:
            f.write(text)
    buildrecord.record_path = lambda: p
    return p


def restore():
    buildrecord.record_path = _REAL_PATH


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def rec(batch, ok=82, warn=0, fail=0, at="2026-10-04 01:10:20", secs=251):
    #: **`secs` 是 Batch 280 加的**：绿记录里必须带构建墙钟。
    #: **默认值 251 取自本批实测**（`/tmp/b280work/build280.wall`：`rc=0 墙钟=251 秒`）
    #: ——**不取整百**，而 `240` 会让人以为这是「估的预算」。
    #: **本助手给所有旧用例都补上了它**：不补的话，那几条「不得报」的用例
    #: 会集体变红，**而它们变红的理由与它们要验的性质毫无关系**。
    return "batch=%d\nok=%d\nwarn=%d\nfail=%d\nsecs=%d\nat=%s\n" % (
        batch, ok, warn, fail, secs, at)


DIFF_NEW = """diff --git a/docs/user-manual/beeftv-canvas/PROGRESS.md b/PROGRESS.md
--- a/PROGRESS.md
+++ b/PROGRESS.md
@@ -1,2 +1,3 @@
+| 255 | 新批次 | ✅ 完成 |
 | 254 | 旧批次 | ✅ 完成 |
"""
DIFF_OLD = """diff --git a/PROGRESS.md b/PROGRESS.md
--- a/PROGRESS.md
+++ b/PROGRESS.md
@@ -1,2 +1,3 @@
+| 250 | 回填旧批次 | ✅ 完成 |
 | 254 | 旧批次 | ✅ 完成 |
"""
DIFF_NO_BATCH = """diff --git a/docs/user-manual/beeftv-canvas/AUDIT.md b/AUDIT.md
--- a/AUDIT.md
+++ b/AUDIT.md
@@ -1 +1 @@
-旧内容
+新内容
"""


# ── 1 新增批次行 > 记录批次号 → 必报 ───────────────────────────────────
def m_new_batch_without_green_build():
    use_record(rec(254))
    probs = buildrecord.check(DIFF_NEW)
    ok = len(probs) == 1 and "Batch 254" in probs[0] and "纪律 280" in probs[0]
    record("1 新增 255 而绿构建只到 254 → 必报", ok, probs[0][:70] if probs else "无问题")


# ── 2 相等 → 不得报（不误伤）────────────────────────────────────────
def m_equal_batch_not_reported():
    use_record(rec(255))
    probs = buildrecord.check(DIFF_NEW)
    record("2 新增 255 而绿构建已到 255 → 不得报", not probs,
           "报了 %d 条" % len(probs))


# ── 3 完全没有记录 → 必报 ───────────────────────────────────────────
def m_no_record_reported():
    use_record(None)
    probs = buildrecord.check(DIFF_NEW)
    ok = len(probs) == 1 and "没有任何一次全绿构建的记录" in probs[0]
    record("3 没有任何绿构建记录 → 必报", ok, probs[0][:70] if probs else "无问题")


# ── 4 没有新增批次行 → 不得报 ───────────────────────────────────────
def m_no_batch_row_not_reported():
    use_record(None)          # **连记录都没有也不该报**——这一条最容易写错
    probs = buildrecord.check(DIFF_NO_BATCH)
    record("4 普通文档提交（无新增批次行）→ 不得报", not probs,
           "报了 %d 条" % len(probs))


# ── 5 记录坏了 → 必报 ───────────────────────────────────────────────
def m_broken_record_reported():
    use_record("batch=不是数字\nok=82\n")
    probs = buildrecord.check(DIFF_NEW)
    ok = len(probs) == 1 and "记录已坏" in probs[0]
    record("5 记录里的 batch 不是整数 → 必报（按没有绿构建处理）", ok,
           probs[0][:70] if probs else "无问题")


# ── 6 回填旧批次 < 记录 → 不得报 ───────────────────────────────────
def m_backfill_older_not_reported():
    use_record(rec(255))
    probs = buildrecord.check(DIFF_OLD)
    record("6 回填 250（小于 255）→ 不得报", not probs, "报了 %d 条" % len(probs))


# ── 15 绿记录里没有构建墙钟 → 必报（Batch 280）───────────────────────
def m_record_without_secs_reported():
    """能抓①：记录里**根本没有 `secs=` 这个键** → 必报。

    **这一条为什么重要**：它是本批那个病的**回归**——
    全树 8 处都写着「构建只要 25 秒」而实测 251 秒，
    **而那份手抄之所以能活这么久，是因为没有任何一处要求构建把它自己测出来**。

    **注入形态刻意选「键不存在」而不是「值是 0」**：
    `write_record(secs=None)` 写出的是 `secs=`，**读回来是空串**——
    那正是 16 号用例的形态。**两例并存才覆盖得住**，
    **而只写其中一例的人会以为自己覆盖了两种**（纪律 288 的同款：形似而质不同）。
    """
    use_record("batch=255\nok=82\nwarn=0\nfail=0\nat=2026-10-04 01:10:20\n")
    probs = buildrecord.check(DIFF_NEW)
    ok = len(probs) == 1 and "没有正的 `secs=`" in probs[0] and "再跑一次" in probs[0]
    record("15 绿记录里没有 `secs=` → 必报", ok, probs[0][:70] if probs else "无问题")


# ── 16 `secs=` 是空的 → 必报（Batch 280 的第二种形态）────────────────
def m_record_empty_secs_reported():
    """能抓②：`secs=` **在、但是空的** → 一样必报。

    **为什么空值也必须报**：那是 `write_record(secs=None)` 亲手写出来的形态，
    **而空值与「键不存在」在 `rec.get("secs") or 0` 眼里是同一件事**——
    **换句话说，这一例验的不是「键在不在」，而是判据不会把空值当成读过**。

    **如果只判「键在不在」，空值会被读成「测过了」**——
    **而那正是本项目本批之前的形态**：一个读起来像真值的空字段。
    """
    use_record("batch=255\nok=82\nwarn=0\nfail=0\nsecs=\nat=2026-10-04 01:10:20\n")
    probs = buildrecord.check(DIFF_NEW)
    ok = len(probs) == 1 and "没有正的 `secs=`" in probs[0]
    record("16 `secs=` 存在却是空值 → 必报", ok, probs[0][:70] if probs else "无问题")


# ── 7 added_batch_numbers 的形态 ───────────────────────────────────
def m_added_numbers_shapes():
    got = buildrecord.added_batch_numbers(
        "+++ b/docs/user-manual/beeftv-canvas/PROGRESS.md\n"
        "+++ b/PROGRESS.md\n"
        "+| 255 | a |\n"
        "+|   256   | b |\n"
        "+| 17c | 子批次 |\n"
        "+| 不是数字 | d |\n"
        " | 999 | 没有加号 |\n"
        "-| 300 | 被删的 |\n")
    ok = got == {255, 256, 17}
    record("7 认 `| N |` 与空格变体、忽略 `+++` 头与 `-` 行", ok, "得到 %s" % sorted(got))


# ── 8 newest_batch 不被字符串序骗 ──────────────────────────────────
def m_newest_batch_numeric():
    ns = buildrecord.batch_table_numbers()
    plain = [x for x in ns if x.isdigit()]
    naive = max(ns)                      # **字符串序**——这是第一版会踩的
    real = buildrecord.newest_batch()
    ok = (naive != real) and real == max(int(x) for x in plain)
    record("8 newest_batch 取纯数字最大值（字符串 max 是 %s）" % naive, ok,
           "newest_batch=%s" % real)


# ── 9/11 build-site.sh 的三个计数器与它真正打出的行数必须相等 ──────────
#: **`ok`/`warn`/`fail` 是从**真** `build-site.sh` 里抠出来的**（闸 18 方向十三同款手法），
#: **所以这一条核的是真文件，而不是本反验自己重写的一份。**
_FUNCS = {}
_TS = "01:10:20"


def _extract_funcs():
    if _FUNCS:
        return _FUNCS
    with io.open(BUILD, encoding="utf-8") as f:
        t = f.read()
    for name in ("ok", "warn", "fail"):
        m = re.search(r"^%s\(\)\s*\{.*?\}\s*$" % name, t, re.M)
        assert m, "前提失配：build-site.sh 里抠不出 %s()" % name
        _FUNCS[name] = m.group(0)
    return _FUNCS


def _count_expr(label, kinds):
    """**拼一条 `printf` 语句：从计数文件里数出若干类。**

    **为什么要有这个共用函数**（纪律 274 的推论）：
    「用 awk 数文件里的某一类」这条知识在用例 9 与 13 里各需要一次，
    **而 Batch 255 已经在「同一条知识写两遍」这件事上栽过一次**——
    用例 13 漏抄了用例 9 里设过的 `TS`，`set -u` 下整段 rc=127，
    **而 rc=127 长得像「命令找不到」**，我差点读成「herestring 不工作」。
    **所以它必须只有一份拼装逻辑。**
    """
    args = " ".join(
        '"$(awk \'$1==\"%s\"\' "$BEEF_CNT" | wc -l | tr -d \' \')"' % k for k in kinds)
    fmt = " ".join(["%s"] * len(kinds))
    #: **标签直接写进格式串、不占一个 `%s`**——第一版把它当第一个实参，
    #: **于是 `printf '%s COUNTS %s %s'` 把字面量当成了要替换的槽位**，
    #: 输出变成 `COUNTS 3 0`，而两条用例一个按 `split()` 读、一个按 `=(\\d+)` 读，
    #: **两边都读不到自己要的形状**。
    #: **现在统一成 `标签=值 值 …`，两条用例都用正则取。**
    return "printf '" + label + "=" + fmt + " \\n' " + args


def _run_funcs(n_ok, n_warn, n_fail_wo_exit):
    f = _extract_funcs()
    # **`fail()` 会 `exit 1`**——那正是它的职责，所以这里只测它「在被调用前
    # 计数器有没有加上」，用 `ok`/`warn` 测行数，用一个不触发 exit 的方式测 fail。
    cnt = os.path.join(_TMP, "cnt9")
    if os.path.exists(cnt):
        os.remove(cnt)
    script = "\n".join([
        'BEEF_CNT="%s"' % cnt,
        'TS="%s"' % _TS,
        f["ok"], f["warn"],
        "ok 一; ok 二; ok 三; warn 甲; warn 乙",
        # **用 awk 数而不是 `$BEEF_OK`**——**第一版是 shell 变量自增，
        # 而那个方案在子 shell 里会丢**（实测 82 行记成 45）。
        # **`printf` 里嵌 `$( )` 同样是子 shell**——**所以这里数的是文件。**
        _count_expr("COUNTS", ["ok", "warn"]),
    ])
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert r.returncode == 0, "抠出来的函数跑不起来：%s" % (r.stderr or "")[:120]
    lines = [l for l in r.stdout.split("\n") if l.strip()]
    hit = [l for l in lines if l.startswith("COUNTS=")]
    assert hit, "计数器行没打出来：%r" % lines[:3]
    nums = [int(x) for x in hit[0].split("=", 1)[1].split()]
    emitted = [l for l in lines if not l.startswith("COUNTS=")]
    return (nums[0], nums[1], 0), len(emitted)


def m_counters_match_emitted_lines():
    (c_ok, c_warn, _c_fail), emitted = _run_funcs(3, 2, 0)
    ok_lines = emitted - c_warn          # `ok` 3 行 + `warn` 2 行 = 5
    good = (c_ok == 3 and c_warn == 2 and emitted == 5 and ok_lines == 3)
    record("9 ok/warn 计数器 == 实际打印行数（真函数真跑）", good,
           "计数器 %d/%d，实际打印 %d 行" % (c_ok, c_warn, emitted))


def m_fail_still_exits_nonzero():
    """**`fail()` 必须仍然 `exit 1` 且先把计数器加上**——
    **本批改过这三个函数，而「提交前钩子」整套机制的前提就是「构建能红」。**
    **一个改坏了 `fail()` 的版本会让构建永远绿，于是记录永远写着「绿」——
    那比没有这个机制更坏。**"""
    f = _extract_funcs()
    script = "\n".join([
        "BEEF_OK=0; BEEF_WARN=0; BEEF_FAIL=0",
        'TS="%s"' % _TS,
        f["fail"],
        'fail "故意"',
        'echo "不该走到这里"',
    ])
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    ok = r.returncode == 1 and "不该走到这里" not in r.stdout
    record("11 fail() 仍然 exit 1 且不落到后面", ok, "rc=%d" % r.returncode)


# ── 10 传 0 行 ok → rc=2 且不写记录 ──────────────────────────────────
def m_zero_ok_refuses():
    p = use_record(None)
    r = subprocess.run([sys.executable, RECORDER, "--counts", "0,0,0"],
                       capture_output=True, text=True)
    wrote = os.path.exists(p)
    ok = r.returncode == 2 and not wrote and "拒绝写记录" in r.stdout
    record("10 ok=0 → rc=2 且不写记录（自洽的假数比没有数更坏）", ok,
           "rc=%d 写了=%s" % (r.returncode, wrote))


# ── 12/13 `printf … | while` 的子 shell 会吞掉计数器（Batch 255 实测） ──
def m_no_pipe_while_in_build():
    """**静态判据**：`build-site.sh` 里不得再出现 `| while`（管道喂 while 的输入）。

    **实测经过**：加了计数器之后的**第一次全绿构建**（退出码 0、82 行 `[ ok ]`）
    记下的是 **`45 ok`**——**少算了 37**。
    **根因**：`printf '%s\\n' "$X" | while …; do …; done` 里
    **整个 while 循环跑在子 shell 中**，**`ok()` 的 `BEEF_OK=$((…+1))` 自增随之消失**。
    **而 45 是一个完全说得过去的数**——**它比 0 更难发现**，
    因为 0 会被「ok 是 0 就拒绝写记录」挡住，**45 不会**。
    **修法**：改用 herestring（`while …; done <<< "$X"`），**循环体在当前 shell 跑**。
    """
    with io.open(BUILD, encoding="utf-8") as f:
        t = f.read()
    #: **只看整行不是注释的行**——**这条第一版没做，于是本批自己写在
    #: `build-site.sh` 里解释「为什么不能用管道喂 while」的那段注释
    #: 把判据自己弄红了**：**注释里提到一个模式，不等于代码里有那个模式**
    #: （与 `_build_invoked()` 同一个纪律、同一处收紧）。
    hits = [l for l in t.split("\n")
            if not l.lstrip().startswith("#") and re.search(r"\|\s*while\b", l)]
    record("12 build-site.sh 的非注释行里没有「管道喂 while」（子 shell 吞计数器）", not hits,
           "命中 %d 行" % len(hits))


def m_subshell_counter_survives():
    """**本批最要紧的一条**：计数器必须**在子 shell 里也数得动**。

    **为什么它是「最要紧」**：同一个数错了三次——
    ① 日志正则失配 → 记成 `0`（0 会被那道拒绝挡住）；
    ② shell 变量自增 → 子 shell 吞掉，记成 `45`（**45 挡不住**）；
    ③ 改 herestring → 记成 `79`，**仍然差 3，而我没能定位到那 3 行的出处**
    （查过：命令替换里没有 `ok`、5 处 `while` 全是 herestring、`|| fail` 那一类未触发）。
    **所以第三次不再逐个追，改成从构造上免疫：子 shell 改得动普通变量，改不动文件。**
    **这一条就是那个免疫性的可执行证据**——
    **`( ok x )` 里的 `ok` 必须在计数文件里留下痕迹。**
    """
    f = _extract_funcs()
    cnt = os.path.join(_TMP, "cnt14")
    if os.path.exists(cnt):
        os.remove(cnt)
    script = "\n".join([
        "set -u",
        f["ok"],
        'TS="00:00:00"',
        'BEEF_CNT="%s"' % cnt,
        "ok 直呼一",
        "( ok 子壳二 )",                       # **子 shell**
        "printf 'x\\n' | while IFS= read -r l; do ok \"管道三\"; done",   # **管道子 shell**
        _count_expr("COUNTER", ["ok"]),
    ])
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    m2 = re.search(r"COUNTER=(\d+)", r.stdout or "")
    n = int(m2.group(1)) if m2 else -1
    record("14 子 shell 与管道里的 ok 也被计数（构造上免疫，不是逐个追）", n == 3,
           "得到 %s（rc=%d）" % (m2.group(1) if m2 else "无", r.returncode))


def m_herestring_counter_survives():
    """**行为判据**：herestring 喂进去的循环里，计数器必须真的累加。

    **这一条是 12 的对照**——12 说「写法不许出现」，这一条说「换完之后行为对」；
    **只测 12 的话，把 herestring 写成一个空循环也能全过**。
    """
    f = _extract_funcs()
    script = "\n".join([
        "set -u",
        f["ok"],
        # **`ok()` 用了 `$TS`，而抠出来的片段里没有它**——
        # **`set -u` 下那是 `unbound variable`、整段 rc=127**，
        # **而 rc=127 长得像「命令找不到」，第一版差点被我读成「herestring 不工作」**。
        # 用例 9 早就设过 `TS`，本条漏抄了——**同一条知识在两条用例里各写一遍，
        # **就一定会有地方漏**（纪律 274 的推论：宁可共用一个拼装函数）。
        'TS="00:00:00"',
        'BEEF_CNT="%s"' % os.path.join(_TMP, "cnt13"),
        # **第一版写的是 `OUT="一\\n二\\n三"`**——
        # **而 bash 的双引号里 `\\n` 不是转义**（只有 `\\$` `\\`` `\\"` `\\\\` 是），
        # **于是 `$OUT` 只有一行**，循环只跑一次，计数停在 1。
        # **改用 `printf` 造多行**——**造多行这件事也有两种写法，
        # 而选错那一种的形态是「安静地少跑几轮」，不是报错。**
        "OUT=\"$(printf '一\\n二\\n三')\"",
        'while IFS= read -r line; do ok "$line"; done <<< "$OUT"',
        _count_expr("COUNTER", ["ok"]),
    ])
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    m = re.search(r"COUNTER=(\d+)", r.stdout or "")
    n = int(m.group(1)) if m else -1
    record("13 herestring 循环里计数器累加到 3", n == 3,
           "得到 %s（rc=%d）" % (m.group(1) if m else "无", r.returncode))


def main():
    tests = [m_new_batch_without_green_build, m_equal_batch_not_reported,
             m_no_record_reported, m_no_batch_row_not_reported,
             m_broken_record_reported, m_backfill_older_not_reported,
             m_record_without_secs_reported, m_record_empty_secs_reported,
             m_added_numbers_shapes, m_newest_batch_numeric,
             m_counters_match_emitted_lines, m_zero_ok_refuses,
             m_fail_still_exits_nonzero,
             m_no_pipe_while_in_build, m_herestring_counter_survives,
             m_subshell_counter_survives]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", "前提失配：%s" % exc)
        except Exception as exc:                          # noqa: BLE001
            record(t.__name__, "失败", "用例自身抛异常：%s: %s" % (type(exc).__name__, exc))
        finally:
            restore()
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print("  %s %s  %s" % (mark, name, detail))
        if status != "通过":
            failed += 1
    print("构建记录核对反验：%d 例，通过 %d，失败/作废 %d"
          % (len(results), len(results) - failed, failed))
    shutil.rmtree(_TMP, ignore_errors=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
