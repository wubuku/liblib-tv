#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四十道闸（`verify-baseline-landmark.py`）的反向验证。

**它守的是一条纪律的机器化**：**「本手册核到哪一版」是半条信息**——
另一半是「**那之后上游改了什么，而本手册对此一无所知**」。
手册原先只说了前半句，于是一个跑在 v1.7.3 上的读者会把「手册没写」读成「产品没有」。

**九例，五个方向**（假阴性必须成对钉：能抓 + 不误伤，纪律 166）：

  能抓 3 条（正向漏报）：
    1) 从落点小节里删掉 v1.7.2 那一行 → 必须点名报出它
    2) v1.7.3 那一行只留版本号、说明删空 → 必须报「说明不足」
       （**这一条钉的是纪律 166**：点名 ≠ 讲清楚；闸 32 第一版就是栽在这里）
    3) 整个「基线之后」小节删掉 → 必须 rc=1 且报出 4 个漏报
       （**钉的是 rc 语义**：「没有落点声明」是**可判定的漏报**，不是「核不了」——
       写成 rc=2 会让这道闸在手册最需要它的时候把自己说成「核不了」）

  能抓 1 条（反向幻觉）：
    6) 点名一个上游没有的版本 v1.6.99 → 必须报出来
       （**少了这一半，「版本地图」就是个可以随便写的地方**：
       读者按手册给的版本号去找，会找不到）

  能抓 1 条（**判据自己坏掉的那一半**）：
    5) 无论注入什么，输出里必须出现 Unreleased 那条提示
       （**Batch 272 上线前实测踩到的真 bug**：Unreleased 的条目数是在遇到标题的
       那一行**就地**数缓冲区的，数到的是**文件头那 4 行说明文字**，
       于是计数恒为 0、**那条提示一次都没打印过**。
       **它不会让闸变红**——Unreleased 压根不参与判定，
       **所以「一个不参与判定的东西坏了」没有任何症状可循，只能靠用例钉住**）

  不误伤 1 条：
    4) 落点小节里额外提到**更早**的 v1.6.14 作对照 → 必须放行
       （反向判据只该拦「不存在的版本」，不该拦「存在但更早的版本」）

  边界 1 条（**rc 语义那一层**）：
    7) 把基线声明改成上游根本没有的 v9.9.9 → 必须 rc=2。
       **这一条替换掉的是本文件初版里的「版本号边界」用例，
       而那个用例的理由经实测是错的**（见下方「本文件订正」一节）。
       现在钉的是「**基线声明与上游自己的发布记录对不上时必须说核不了**」：
       摘掉那道检查，`(9,9,9)` 就会让全部 36 个版本都算成「基线之后」，
       闸会报 rc=1 + 32 个漏报——**一个「核不了」被报成「手册漏了 32 处」**，
       而修法完全相反（该去查基线声明，不是去补 32 行落点说明）。

  **潜伏的假阴性 1 条**：
    8) 基线挪到 v1.7.3（`after` 变空）**且**留一条上游没有的 v9.9.9 → 仍必须 rc=1。
       **闸的初版在这里会报绿**：「无事可判」那一支写在反向检查之前，
       而 `after` 一空就 return 0、**反向诊断整个被跳过**。
       **今天触发不了**（真树还有 4 个基线之后的版本）——
       **而「今天触发不了」正是潜伏的假阴性最常见的形态**（纪律 307 推论一）。

  **订阅契约 3 条（Batch 273 新增；这三条是闸在自己文档里立下、此前 0 例覆盖的断言）**：
    9) **合成上游多发一版 v1.7.4、落点小节没提** → 必须 rc=1 且点名 v1.7.4。
       **这一条量的是「上游一发新版本，这一小节立刻变红」**——
       **而那句话是 Batch 272 写进 `20-reference.md` 给读者看的**，
       读者会照它行事（照着补一行），**而它此前一次都没被跑过**（纪律 307）。
    10) **合成上游没有 `origin/main` 这个 ref（只有 `HEAD`）** → 必须 rc=2，
       且输出里必须出现「**不是「上游没有新版本」**」。
       **这一条量的是「绝不退回 `HEAD`」**——
       **而退回 `HEAD` 是本闸最坏的失败形态**：拿一份停在几个月前的检出
       算出「上游没有新版本」并报绿，**那会让落点声明显得比实际更完整**（纪律 101）。
    11) **基线改成 v1.7.4（追平合成上游）** → 必须 rc=0，
       且输出里必须出现「**读到且结论为空，不是「读空了也算通过」**」。
       **这一条钉的是两种「空」必须分开**：「读不到 CHANGELOG」是 rc=2，
       「读到 CHANGELOG 且基线之后为空」是 rc=0（纪律 101）。
       **而它是手册追上上游之后才会出现的那个局面**——
       **今天触发不了，而「今天触发不了」的用例最容易被当成多余的删掉**（纪律 307）。

  基线 1 条：真树原样 → rc=0。

**这三条为什么需要「合成上游仓」而不能靠改手册那一侧**：
闸 40 的判据输入是**上游 `origin/main` 上的 `CHANGELOG.md`**，
而「上游多发了一版」这件事**只在上游那侧**。
**手册侧能造出来的只有「漏写一行」，造不出「上游多了一版」。**
**而且绝不能拿真检出造**——`origin/main` 上有同事在用的状态，
**Batch 272 刚被它坑过一轮**（那次 fetch 落在两批之间，把三条用例的前提打没了）。
**所以本文件造一个最小合成仓**（`git init` + 一份 CHANGELOG + 一个 `refs/remotes/origin/main`），
**用 `BEEFTV_SRC` 指过去**。实测合成仓完全够用：
**闸 40 只需要 SRC 是个能解出 `origin/main` 的 git 检出**，
不需要那 34 个提交、不需要 1263 个文件、不需要真 tag（Batch 273 实测）。

**每条注入都用 `assert` 钉死锚点，并在跑之前 `cksum` 比对前后**
（Batch 229：`str.replace` 锚点不中时静默无操作，
而「用例通过」与「用例根本没跑起来」输出上完全一样）。

**本文件订正（Batch 272，写完判据后当场量的）**：
初版里有一条用例 7，理由写的是「基线声明改成 `v1.6.2`（`v1.6.22` 的前缀），
**版本号若没加边界，同一份输入会得到 rc=0**」。
**实测摘掉 `(?![\d.])` 之后，两条正则的枚举结果逐字相同**——
贪婪的 `\d+` 本来就吃掉 `22`，而本闸从不做字面子串搜索。
**所以那条用例守的是一件今天不存在的事，而它的理由听起来完整**——
**一个站不住的解释比一个 plainly 的 bug 更贵**，因为它会让人去改别的东西（纪律 307）。
用例 7 已换成「基线声明改成上游没有的 v9.9.9 → 必须 rc=2」，
**那一层是这道闸真正要守的**（纪律 101：核不了 ≠ 不一致）。
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from stagedeps import child_env, stage_gate

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
#: 被测闸的**模块名（不带 `.py`）**——`stage_gate()` 收的就是这个形态。
#: **闸 17 的 `staged_gates()` 只认 `stage_gate(...)` 实参里的字符串字面量**
#: （「变量、拼接、推导出来的闸名一律不认」），所以下面那次调用必须**写死字面量**，
#: 而不是 `stage_gate(tmp, GATE)`。
GATE = "verify-baseline-landmark"
REFERENCE = "20-reference.md"
LANDMARK_HEADING = "### 基线之后：上游又改了什么"
NEXT_HEADING = "## 画布快捷键全表"

PASS = VOID = FAIL = 0

#: **合成上游用的 CHANGELOG**（Batch 273）。
#: **刻意只放最小的形态**：6 个发布段落 + 1 个 Unreleased 段。
#: **为什么不需要真上游那 34 个提交 / 1263 个文件 / 3 个 tag**：
#: 闸 40 的判据输入只有**「`origin/main` 上 `CHANGELOG.md` 的段落集合」**这一样东西，
#: **实测一个 `git init` 出来的空仓加一份 CHANGELOG 就够它跑完四种结局**。
#: **而夹具越贴近真上游，它就越多一份「真上游变了它也得跟着改」的维护债**
#: ——**那正是 Batch 272 被上游坑的那一刀**（纪律 265：夹具要够用，不要够真）。
SYNTH_CHANGELOG = """# Changelog

All notable public changes to BeefTV are documented in this file.

## Unreleased

- 还没发布的一条。

## v1.7.3

- 引导式模型服务接入。

## v1.7.2

- Windows MCP。

## v1.7.1

- 消息框旁选模型。

## v1.6.23

- 画布助手。

## v1.6.22

- 导演台工作台。
"""

#: 合成上游「多发了一版」的形态。**插在最前面**——CHANGELOG 是新版本在上，
#: 而闸 40 的 `changelog_sections()` **不依赖顺序**（它按版本元组比大小）。
#: **而这一条也顺带量了一次「解析器与顺序无关」**：
#: 第一版把它追加到最末尾，输出一样，**所以那不是闸宽容，是两种顺序都被覆盖了**。
SYNTH_CHANGELOG_PLUS_174 = """## v1.7.4

- 上游刚发的一版，落点小节还没提它。

"""


def _git(args, cwd, check=True):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("git %s → rc=%d：%s" % (" ".join(args), r.returncode,
                                                   r.stderr.strip()[:200]))
    return r


def make_upstream(path, changelog, origin_main=True):
    """造一个合成上游 git 仓，返回它的路径。

    `origin_main=False` 用来量「拿不到 `origin/main`」那一支——
    **而那正是「绝不退回 `HEAD`」这句话唯一能被验的地方**：
    只有「`HEAD` 在、而 `origin/main` 不在」这个形态，
    才真的逼判据在两个 ref 之间选一个（纪律 101）。
    """
    os.makedirs(path)
    _git(["init", "-q", path], cwd=path)
    _git(["config", "user.email", "selftest@example.com"], cwd=path)
    _git(["config", "user.name", "selftest"], cwd=path)
    with open(os.path.join(path, "CHANGELOG.md"), "w", encoding="utf-8") as fh:
        fh.write(changelog)
    _git(["add", "CHANGELOG.md"], cwd=path)
    _git(["commit", "-q", "-m", "synthetic upstream"], cwd=path)
    if origin_main:
        head = _git(["rev-parse", "HEAD"], cwd=path).stdout.strip()
        _git(["update-ref", "refs/remotes/origin/main", head], cwd=path)
    return path


def _cksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(desc, want, expect_fail=True, want_rc=1, edits=None, unwanted=None,
        upstream=None):
    global PASS, VOID, FAIL
    ref_path = os.path.join(ROOT, REFERENCE)
    base = {ref_path: open(ref_path, encoding="utf-8").read()}
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

    tmp = tempfile.mkdtemp(prefix="beef-landmark-selftest.")
    try:
        # **用 `stage_gate()` 搬依赖闭包，不手写搬运清单**——
        # **而这正是闸 17 在本批上线构建里当场报出来的**：
        # 第一版写的是 `for src in (BASELINE, BEEFSRC, HEADINGKEY, GATE): shutil.copy(...)`，
        # **闸 17 看不见那个循环**（它的循环搬运只认「可迭代对象是模块级常量的名字」，
        # 而这里是个 Name 元组表达式），于是报「反验没有把 baseline / beefsrc / headingkey
        # 复制进临时 scripts/」。
        # **而那份反验实跑是 8/8 全绿的**——正因为闸 17 判的是**「有没有那几行搬运代码」**，
        # 而我这个循环里搬运**真的发生了**。
        # **所以这一次闸 17 报的不是假阳性，是它按自己的口径忠实地报了**：
        # 它要防的正是「清单没跟着加 import 改」，
        # **而「跑起来是好的」证明不了「清单是对」**（纪律 274）。
        # **这是同一形状的第 6 次**（178 baseline / 181 batchread / 197 beefsrc /
        # 251 headingkey→闸5 / 252 headingkey→闸14 / 272 本次）。
        stage_gate(tmp, "verify-baseline-landmark")
        for p, t in texts.items():
            rel = os.path.relpath(p, ROOT)
            dst = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write(t)

        #: 沙箱自己就是这一轮的手册根（Batch 260 / 纪律 289）。
        #: **`upstream` 给了就改指合成仓**——那是「上游那一侧变了」的用例专用。
        #: **不设 `BEEFTV_SRC` 时走 `beefsrc` 的候选表**，那才是真检出。
        env = child_env(tmp)
        up_dir = None
        try:
            if upstream is not None:
                up_dir = make_upstream(os.path.join(tmp, "upstream"),
                                       upstream.get("changelog", SYNTH_CHANGELOG),
                                       origin_main=upstream.get("origin_main", True))
                env["BEEFTV_SRC"] = up_dir
            r = subprocess.run([sys.executable,
                                os.path.join("scripts", GATE + ".py")],
                               cwd=tmp, capture_output=True, text=True, env=env)
        finally:
            if up_dir:
                shutil.rmtree(up_dir, ignore_errors=True)
        out = r.stdout + r.stderr

        if expect_fail and r.returncode != want_rc:
            print("  ✗ %s：退出码 %d，期望 %d；实际：" % (desc, r.returncode, want_rc))
            print("      " + out.strip()[:300])
            FAIL += 1
            return
        if not expect_fail and r.returncode != 0:
            print("  ✗ %s：闸门本应通过，却退出 %d；实际：" % (desc, r.returncode))
            print("      " + out.strip()[:300])
            FAIL += 1
            return
        if want and want not in out:
            print("  ✗ %s：输出里没有 [%s]；实际：" % (desc, want))
            print("      " + out.strip()[:300])
            FAIL += 1
            return
        if unwanted and unwanted in out:
            print("  ✗ %s：输出里**不该出现** [%s]；实际：" % (desc, unwanted))
            print("      " + out.strip()[:300])
            FAIL += 1
            return
        print("  ✓ %s" % desc)
        PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def drop_line(version):
    """把落点小节里以 `- **vX.Y.Z**` 开头的那一整行删掉。"""
    def fn(text):
        head = text.index(LANDMARK_HEADING)
        tail = text.index(NEXT_HEADING, head)
        seg = text[head:tail]
        lines = seg.split("\n")
        keep = [ln for ln in lines if not ln.startswith("- **%s**" % version)]
        assert len(keep) == len(lines) - 1, \
            "注入空转：没找到恰好一行 `- **%s**`（该行数 %d → %d）" % (version, len(lines), len(keep))
        return text[:head] + "\n".join(keep) + text[tail:]
    return fn


def strip_desc(version):
    """把那一行的说明删空，只留版本号。"""
    def fn(text):
        marker = "- **%s**" % version
        head = text.index(LANDMARK_HEADING)
        tail = text.index(NEXT_HEADING, head)
        seg = text[head:tail]
        out_lines = []
        hit = 0
        for ln in seg.split("\n"):
            if ln.startswith(marker):
                hit += 1
                ln = marker
            out_lines.append(ln)
        assert hit == 1, "注入空转：`- **%s**` 命中 %d 行" % (version, hit)
        return text[:head] + "\n".join(out_lines) + text[tail:]
    return fn


def main():
    ref = os.path.join(ROOT, REFERENCE)

    run("0) 基线：真树原样（4 个基线之后的版本都已被点名）",
        "落点声明核对通过", expect_fail=False)

    run("1) 能抓：从落点小节里删掉 v1.7.2 那一行",
        "v1.7.2 在上游 CHANGELOG 里", edits={ref: drop_line("v1.7.2")})

    run("2) 能抓：v1.7.3 那一行只留版本号、说明删空"
        "（**点名 ≠ 讲清楚**——闸 32 第一版就栽在这一条上）",
        "说明不足", edits={ref: strip_desc("v1.7.3")})

    def t_drop_section(text):
        head = text.index(LANDMARK_HEADING)
        tail = text.index(NEXT_HEADING, head)
        return text[:head] + text[tail:]

    run("3) 能抓：整个「基线之后」小节删掉"
        "（**必须 rc=1 而不是 rc=2**：「没有落点声明」是可判定的漏报，不是「核不了」）",
        "4 个发布版本，0 个已被点名", want_rc=1, edits={ref: t_drop_section})

    def t_mention_older(text):
        head = text.index(LANDMARK_HEADING)
        inject = ("> 对照：本手册 67 张截图里有 37 张拍于 v1.6.14，"
                  "那也是正文大量数字的来源。\n")
        return text[:head + len(LANDMARK_HEADING) + 1] + inject + text[head + len(LANDMARK_HEADING) + 1:]

    run("4) 不误伤：落点小节里额外提到更早的 v1.6.14 作对照"
        "（反向判据只该拦「不存在的版本」，不该拦「存在但更早的版本」）",
        "落点声明核对通过", expect_fail=False, edits={ref: t_mention_older})

    run("5) 能抓：输出里必须有 Unreleased 那条提示"
        "（**判据自己坏掉的那一半**——它不参与判定，坏了不会让闸变红，"
        "而 Batch 272 实测那个计数恒为 0、提示一次都没打印过）",
        "`## Unreleased` 段里还有 4 条", expect_fail=False)

    def t_phantom(text):
        head = text.index(LANDMARK_HEADING)
        inject = "- **v1.6.99** 这一版上游并没有发布。\n"
        return text[:head + len(LANDMARK_HEADING) + 1] + inject + text[head + len(LANDMARK_HEADING) + 1:]

    run("6) 能抓（反向）：点名一个上游没有的版本 v1.6.99",
        "上游 CHANGELOG 里没有这个版本", edits={ref: t_phantom})

    def t_unknown_baseline(text):
        out = text.replace("- **版本**：v1.6.22", "- **版本**：v9.9.9", 1)
        assert out != text, "注入空转：基线版本锚点没换成 v9.9.9"
        return out

    run("7) rc 语义：基线声明改成上游根本没有的 v9.9.9 → 必须 rc=2「核不了」"
        "（**摘掉那道检查就会报 rc=1 + 32 个漏报**，而修法完全相反："
        "该去查基线声明，不是去补 32 行落点说明）",
        "基线声明与上游自己的发布记录对不上", want_rc=2, edits={ref: t_unknown_baseline})

    def t_caught_up_plus_phantom(text):
        """基线挪到上游最新的 v1.7.3（`after` 变空）**且**留一条上游没有的版本号。

        **这一例钉的是一处潜伏的假阴性**：初版把「无事可判」那一支写在反向检查**之前**，
        于是 `after` 为空时直接 return 0、**反向诊断整个被跳过**——
        手册追平上游那天，闸会对一条幻觉版本号报绿。
        **今天触发不了**（真树还有 4 个基线之后的版本），
        **而「今天触发不了」正是潜伏的假阴性最常见的形态**（纪律 307 推论一）。
        """
        out = text.replace("- **版本**：v1.6.22", "- **版本**：v1.7.3", 1)
        assert out != text, "注入空转：基线版本锚点没换成 v1.7.3"
        head = out.index(LANDMARK_HEADING)
        at = head + len(LANDMARK_HEADING) + 1
        return out[:at] + "- **v9.9.9** 这一版上游从来没有发布过。\n" + out[at:]

    run("8) 能抓（反向，**潜伏假阴性**）：基线挪到 v1.7.3（`after` 变空、"
        "本闸本无漏报可查）**且**小节里留着一条上游没有的 v9.9.9 → 仍必须 rc=1。"
        "**初版在这里会报绿**——「无事可判」那一支写在了反向检查之前",
        "上游 CHANGELOG 里没有这个版本", want_rc=1, edits={ref: t_caught_up_plus_phantom})

    # ══════ Batch 273：订阅契约三条 ══════
    # **这三条量的是闸在**自己文档里**立下的三句话，而它们此前 0 例覆盖。**
    # **其中第一句是写进 `20-reference.md` 给读者看的**——读者会照它行事。
    run("9) **订阅契约**：合成上游多发一版 v1.7.4、落点小节没提 → 必须 rc=1 且点名它"
        "（**量的是「上游一发新版本，这一小节立刻变红」那句话**——"
        "**而它此前一次都没被跑过**）",
        "v1.7.4 在上游 CHANGELOG 里", want_rc=1,
        upstream={"changelog": SYNTH_CHANGELOG_PLUS_174 + SYNTH_CHANGELOG})

    run("10) **绝不退回 `HEAD`**：合成上游**只有 `HEAD`、没有 `origin/main`** → 必须 rc=2，"
        "且必须明说「不是「上游没有新版本」」"
        "（**退回 `HEAD` 是本闸最坏的失败形态**：拿一份停在几个月前的检出算出"
        "「上游没有新版本」并报绿，**会让落点声明显得比实际更完整**）",
        "不是「上游没有新版本」", want_rc=2,
        upstream={"changelog": SYNTH_CHANGELOG, "origin_main": False})

    def t_catch_up(text):
        out = text.replace("- **版本**：v1.6.22", "- **版本**：v1.7.4", 1)
        assert out != text, "注入空转：基线版本锚点没换成 v1.7.4"
        return out

    run("11) **两种「空」必须分开**：基线追平合成上游（v1.7.4）→ rc=0，"
        "且必须明说「这是『读到且结论为空』，不是『读空了也算通过』」"
        "（**读不到 CHANGELOG 是 rc=2；读到且基线之后为空是 rc=0**——"
        "**而这个局面今天触发不了，是手册追上上游之后才会出现的**）",
        "这是「读到且结论为空」，不是「读空了也算通过」", want_rc=0, expect_fail=False,
        edits={ref: t_catch_up},
        upstream={"changelog": SYNTH_CHANGELOG_PLUS_174 + SYNTH_CHANGELOG})

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
