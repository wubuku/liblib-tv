#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""副本树绿构建的**承重核对**——一份实现，带自检与自测。

**为什么它该进仓库，而不是每批手抄一遍**：
Batch 311–320 的绿构建 wrapper 里各有一组「搭完树当场核对」，
**十批十份、每份手抄**。而这一组核对恰恰是**这个项目里抓到缺陷最多的代码**：
它先后抓到过非幂等编辑留下的重复插入、表格被劈成第 5 格、批次行漏叠加、
闸清单表行序错位、方向计数悄悄变成 0……

**而它自己的缺陷率是全项目最高的**。2026-10-07 一天之内，
**同一批里三条承重核对有两条第一次写就写错了**：
  ① 「副本树有没有第 50/51 例」用了 `grep -q "^50)"`，
     而用例行以 `run_file_case "50)` 开头 —— **它在用例明明在文件里（683/687 行）
     的情况下报「没有」，把构建拦下了**。**拦下总比放过好，但一条恒假的承重核对
     比没有更坏**：它会把人训练成「这条总报红，忽略它」。
  ② 「本批改了哪些文件都叠了吗」写成 bash 内嵌 heredoc，
     **`${FILES[@]}` 在那种位置只传得进去第一个元素**，
     **而报错长到看不出是哪一条对不上**——离真实原因太远的诊断比没有诊断更费时间。
  ③ 第一版把「KNOWN_WIP 里当前没有改动的条目」这条提示**说反了**：
     它遍历的是「在 `changed` 里、且不在 `mine` 里」的条目，
     **也就是「确实有改动」的那些**，却打印「当前没有改动（同事可能已经提交/撤销）」。
     **说反的那一半恰恰是排除名单是否仍然有效这条信息**，
     **而排除名单一旦悄悄过期，下一批会把同事的 WIP 当成「本批漏叠加」而报错**。

**所以本脚本照纪律 355 的形状写**：形态归一化是**一个**函数、
**内部当场用已知答案自检**；整套核对另有一个 `--self-test`
（**一正一负成对的已知答案样本**，纪律 350：判别式没被样本验过就只是写法）。

**Batch 322 补的 `--expect-case`（纪律 357）**：把上面 ① 那条恒假的
「副本树有没有第 N 例」收进来。**而收它之前先量了三件事**：
  · 真实的 `selftest-meta.sh` 实跑是「**通过 51**」，
    **而只认执行器形态的探针只数出 47**——漏掉的 12/16/19/20 是**手写内联块**
    （自己 `echo "  ✓ N) …"` 再 `PASS=$((PASS+1))`，其中 20 那条连标记都没有）。
  · **`^N)` 恒假，而它的反面 `N)` 恒真**：`selftest-meta.sh` 头部有一份
    **22 行的计划清单**（`#   50) 能抓：…`），**和可执行行长得几乎一样**。
    **两种直觉写法一假一真、方向相反，而「都报绿」这个后果完全一样。**
  · 对应关系表 47 行里，**只有 1 行的「例数」能被静态重数**——
    其余 46 份是 Python 驱动，形态各不相同。
    **所以「例数重数」这个闸否掉了**：立了会 46/47 恒为「未能核对」，
    **而一条恒为「未能核对」的闸等于没有（纪律 352⑤ / 310）**。

**它不检查什么（如实说明）**：
  · **不跑构建**（那是 wrapper 的事，4 分钟）；
  · **不核批次专用的断言**（「副本树的方向十三必须报 34/10」那种每批不同）——
    **把它们塞进来会让这个脚本每批都要改，于是它又回到「手抄」的状态**。
  · **`--expect-case` 只认两支形态**（执行器 / 手写内联块），
    **对 Python 驱动的用例形态一律不认**——
    **而它对认不出的东西必须报「未能核对」而不是「不存在」**（纪律 101）：
    实测 `selftest-meta.sh` 的**例号 12 只存在于头部注释计划清单里，
    从来没有可执行实现**，判据如实报它「只在注释行里出现过」。
    **这条不是判据的缺陷，是本项目用例编号的一个真事实（纪律 357 如实记下）。**
"""
import argparse
import ast
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
#: **「是不是注入夹具」只有一份判据**（Batch 258 收敛进 `selftestnames`）——
#: **本判据用它而不用自己重刻一个正则**：本批先按「文件名不以 `fix-` 开头即反验」
#: 扫了一遍，得出「80 份未登记」——**而那 80 份全是 `selftest-*-fix-*` 夹具**
#: （Batch 256 记过同一个坑：58 份夹具被当成反验，判据报了 58 处）。
#: **而它与闸 18 用的是同一个模块**——本判据与闸 18 判「反验还是夹具」的口径
#: **因此不可能对不上**（纪律 355：同一份判据只写一份）。
#: **注意它 import 的是这个纯常量模块、不是闸 18 本身**：
#: 闸 42 记过「两道闸不该互相 import，因为 import 会执行对方模块顶层的代码」。
from selftestnames import FIXTURE_RE

REPO_DEFAULT = "/Users/yangjiefeng/Documents/wubuku/liblib-tv"


# ── 形态归一化：一个函数 + 当场自检（纪律 355） ──────────────────────────
def norm_rel(path):
    """任意一种写法 → 相对仓库根的规范路径（无 `./`、无重复斜线、无尾斜线）。"""
    b = path.strip().replace("\\", "/")
    while b.startswith("./"):
        b = b[2:]
    while "//" in b:
        b = b.replace("//", "/")
    b = b.rstrip("/")
    assert b, "空路径"
    return b


#: **当场自检**：一组已知答案（**这四个是 2026-10-07 当天真的栽过的形态**）。
#: **它不是仪式**——本函数的第一版把自检写成 `norm_rel._probe(...)`，
#: **而函数对象上的属性在模块里取不到，当场 `AttributeError`**；
#: 写成下面这几行 assert 之后，它才真的在验「变换本身」而不是在验「属性存在」。
for _raw, _want in [
    ("./docs/x.md", "docs/x.md"),
    ("docs//x.md", "docs/x.md"),
    ("docs/sub/", "docs/sub"),
    ("  docs/x.md  ", "docs/x.md"),
]:
    _got = norm_rel(_raw)
    assert _got == _want, ("归一化自检失败", _raw, _got, _want)
#: **幂等**：归一化两次必须与一次相同
assert norm_rel(norm_rel("./a//b/")) == "a/b"
print("形态归一化自检：4 个已知答案 + 幂等，全过")


# ── 「第 N 例真的存在」：两支形态，各带当场自检 ──────────────────────────
#: **为什么是两支**：2026-10-07 实测 `selftest-meta.sh` 真跑「通过 51」，
#: 而只认执行器形态的探针只数出 **47**——漏掉的 12/16/19/20 是
#: **手写内联块**（自己 `echo "  ✓ N) …"` 再 `PASS=$((PASS+1))`）。
#: **这不是假设，是当场量出来的差**。
CASE_HELPER_RE = re.compile(r'^\s*run_(?:file_)?(?:fail_|pass_)?case\s+"?(\d+)\)')
CASE_INLINE_RE = re.compile(r'^\s*(?:echo|printf)\b.*?[✓✗]\s(\d+)\)')
#: **注释里的例号**：`#   50) 能抓：…` 这种形态在 `selftest-meta.sh` 里有 22 行。
COMMENT_NUM_RE = re.compile(r'(?:^#\s*|\s)(\d+)\)')

#: **当场自检（纪律 355：一个函数 + 已知答案，不许「两份各写一遍」）**。
#: 逐字照抄真实文件里的行；`\` 在行尾是 shell 续行。
for _txt, _want in [
    ('run_file_case "50) 闸脚本 docstring 自称的闸号被改错" \\', 50),
    ('run_file_pass_case "51) 只改说明、闸号不动" \\', 51),
    ('run_fail_case "6) 标题的闸数与表行数差 1" "道闸"，清单表却有" \\', 6),
    ('run_pass_case "9) 索引里的「标题（提示）」形态（必须不报）" \\', 9),
]:
    _m = CASE_HELPER_RE.match(_txt)
    assert _m and int(_m.group(1)) == _want, ("执行器形态自检失败", _txt, _m)
for _txt, _want in [
    ('    echo "  ✓ 16) 模式非法：闸门正确报出 [判据执行异常]"; PASS=$((PASS+1))', 16),
    ('    echo "  ✗ 20) 去掉首页豁免后仍报通过"; FAIL=$((FAIL+1))', 20),
]:
    _m = CASE_INLINE_RE.match(_txt)
    assert _m and int(_m.group(1)) == _want, ("内联形态自检失败", _txt, _m)
#: **反向自检（这一条才是本函数存在的理由）**：
#: 注释行**不许**被两支形态认领，裸数字也不许——
#: **Batch 320 栽的 `grep -q "^50)"` 是恒假**（用例行以 `run_file_case` 开头），
#: **而它的反面 `grep -q "50)"` 是恒真**（撞上头部注释那 22 行）。
#: **两种直觉写法一假一真，方向相反，而「都报绿」这个后果一样。**
assert not CASE_HELPER_RE.match("#   50) 能抓：把闸清单表的第 9、10 两行对调")
assert not CASE_INLINE_RE.match("#  12) 能抓：把被引用的那句「运行时实证」改掉")
assert COMMENT_NUM_RE.search("#   50) 能抓：把闸清单表的第 9、10 两行对调")
print("用例定位自检：执行器 4 个 + 内联 2 个 + 注释反向 3 个，全过")


def find_case(path, n):
    """第 `n` 例在这个驱动里到底怎么出现的。

    返回 `(状态, 说明)`，状态 ∈ `{"ok", "missing", "unreadable"}`：
      · `ok`         = 在**可执行行**里找到了
      · `missing`    = 没有（**并区分「只在注释里」**——那是最容易骗过人的一种）
      · `unreadable` = **读不出来**（文件不在 / 打不开）

    **后两个必须分开**：纪律 101 说解析器退化的表现必须是「未能核对」而不是
    「不一致」——**一次形态错会把真信号淹掉**。
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
    except OSError as e:
        return "unreadable", "打不开：%s" % e
    saw_comment = False
    for line in lines:
        if line.lstrip().startswith("#"):
            m = COMMENT_NUM_RE.search(line)
            if m and int(m.group(1)) == n:
                saw_comment = True
            continue
        m = CASE_HELPER_RE.match(line) or CASE_INLINE_RE.match(line)
        if m and int(m.group(1)) == n:
            how = "执行器形态" if CASE_HELPER_RE.match(line) else "手写内联块形态"
            return "ok", how
    if saw_comment:
        return "missing", "**只在注释行里出现过**——注释不是执行"
    return "missing", "可执行行里找不到"


def read_list(path):
    with open(path, encoding="utf-8") as fh:
        return [norm_rel(ln) for ln in fh if ln.strip()]


def git_changed(repo, sub):
    """`git status --porcelain -- <sub>` → **{规范相对路径: 状态码}**。

    **porcelain 格式是「两位状态 + 一个空格 + 路径」**，
    而第一版按前 3 字符切之后又对 `??` 行**再切一次**，把首字符也切掉了
    （`ocs/user-manual/…`）——**当时那份报错没有任何一处指向真正的原因**。

    **返回状态码而不是只返回路径，是因为下面两条检查必须分开**：
      · ` M` = **已入库**但被改 → **副本树里应该有** HEAD 版（那正是我们要的隔离）；
      · `??` = **未跟踪**（新文件） → **副本树里绝不该有**，因为它没进过任何提交。
    **第二版把两者混成一条「副本树里出现了同事的文件」，于是在真仓库上立刻误报 3 处**
    （`10-tasks/README.md` 等三个已入库文件）——
    **而那三个文件恰恰是必须出现在副本树里的**。
    """
    out = subprocess.run(["git", "-C", repo, "status", "--porcelain", "--", sub],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("git status 失败：%s" % out.stderr.strip())
    paths = {}
    for line in out.stdout.split("\n"):
        if len(line) < 4:
            continue
        status = line[:2].strip()
        p = line[3:].strip()
        if p.startswith('"') and p.endswith('"'):
            p = p[1:-1]
        paths[norm_rel(p)] = status
    return paths


def run_gate(out_dir, sub, script):
    r = subprocess.run([sys.executable, "scripts/" + script], cwd=os.path.join(out_dir, sub),
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def registered_costs(gate18_path):
    """从**闸 18 的源码**读出 `SLOW` 与 `SELFTEST_COSTS` 两张表的键。

    **用 `ast` 而不 `import`**（闸 42 记过：两道闸不该互相 import，
    因为 import 会执行对方模块顶层的代码——而 `verify-selftest-bootable.py` 顶上
    `import beefsrc`，那会让本工具**依赖上游检出是否存在**，
    **而本工具的职责只是搭副本树，不该多出一个环境前提**）。

    **只认 `ast.Dict` 形态的赋值**：闸 42 那条判据读 SLOW 名单用的也是这个办法
    （`SLOW.seconds` 那种写法本函数读不出来——**而那正是它该报「未能核对」而不是
    悄悄返回空集的情形**）。
    """
    with open(gate18_path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    out = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets
                 if isinstance(t, ast.Name) and t.id in ("SLOW", "SELFTEST_COSTS")]
        if not names or not isinstance(node.value, ast.Dict):
            continue
        for k in node.value.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                out.add(k.value)
    if not out:
        raise ValueError("闸 18 源码里没有 `SLOW` / `SELFTEST_COSTS` 的字典字面量"
                         "（**读不出来不等于「一个都没登记」**，纪律 101）")
    return out


def preflight(repo, sub, out, files, wip, run_tables_gate=True, expect_case=(),
              expect_batch_row=None):
    """返回 (问题列表, 信息行列表)。**信息行与问题行必须分开**——
    2026-10-07 第一版把两者混在一个列表里，于是「说反」的错误没人当场发现。

    `expect_case` 是 `["<相对路径>:<例号>", …]`，每一项去**副本树**里核那一例。
    """
    problems, notes = [], []
    mine = set(files)
    wip_set = set(wip)
    changed = git_changed(repo, sub)
    changed_set = set(changed)

    # ① 漏叠加：本批改了却不在 FILES 里（减去显式排除的同事 WIP）
    missing = sorted(p for p in changed_set if p not in mine and p not in wip_set)
    for p in missing:
        problems.append("本批改了却不在 FILES 里 → 副本树会跑上一批的版本：%s" % p)
    if not missing:
        notes.append("工作区 %d 处改动全部落在 FILES（%d 项）或 KNOWN_WIP（%d 项）里"
                     % (len(changed), len(mine), len(wip_set)))

    # ② KNOWN_WIP 的有效性——**方向必须对**：在 `changed` 里的是「仍然有改动」，
    #    不在的才是「同事可能已经提交/撤销」
    still_dirty = sorted(wip_set & changed_set)
    stale = sorted(wip_set - changed_set)
    for p in still_dirty:
        how = "未跟踪的新文件" if changed[p] == "??" else "已入库文件被改"
        notes.append("KNOWN_WIP 生效中：%s 仍是同事的%s（已排除，不算漏叠加）"
                     % (p, how))
    for p in stale:
        notes.append("⚠ KNOWN_WIP 条目 %s 当前**没有**改动——同事可能已提交/撤销。"
                     "**排除名单一旦过期，下一批会把它当成「本批漏叠加」而报错**" % p)

    # ③ 逐文件：副本树必须逐字节等于工作区
    for p in sorted(mine):
        src, dst = os.path.join(repo, p), os.path.join(out, p)
        if not os.path.exists(dst):
            problems.append("副本树里没有 %s" % p)
            continue
        a = subprocess.run(["cmp", "-s", src, dst]).returncode
        if a != 0:
            problems.append("副本树与工作区的 %s 不一致" % p)

    # ④ 副本树里绝不能出现同事的**未跟踪**文件
    #    （**已入库但被改的文件，副本树里必须有 HEAD 版**——那正是隔离的目的。
    #     第二版没分这两者，在真仓库上立刻误报 3 处。）
    for p in sorted(wip_set & changed_set):
        if changed[p] != "??":
            continue
        if os.path.exists(os.path.join(out, p)):
            problems.append("副本树里出现了同事的**未跟踪**文件 %s —— 叠加写错了" % p)

    # ⑥ 「第 N 例真的存在」——**副本树里查，不是工作区**
    #    （查工作区就是查「我这批改了没有」，而副本树查的才是「构建跑的那份」）
    for spec in expect_case:
        drv, _, num = spec.rpartition(":")
        n = int(num)
        state, why = find_case(os.path.join(out, drv), n)
        if state == "ok":
            notes.append("反验第 %d 例在副本树里存在（%s）：%s" % (n, drv, why))
        elif state == "unreadable":
            problems.append("反验第 %d 例**未能核对**（%s）：%s —— "
                            "读不出来不等于不存在（纪律 101）" % (n, drv, why))
        else:
            problems.append("副本树的 %s 里第 %d 例%s" % (drv, n, why))

    # ⑨ **新增的反验必须在闸 18 的实测耗时表里有条目**（Batch 337）——
    #    **本条治的正是本批自己付过的那笔账**：Batch 336 加了闸 46 与它的反验，
    #    而那 8 例没登记 `SELFTEST_COSTS`，于是闸 18 方向四d 报红，
    #    **绿构建跑满 12 分钟、还作废了一次矩阵重测（红基线上量的行不算证据）**，
    #    **而这条义务在闸 18 自己的报错原话里写着**（「跑一次把秒数填进去即可」）。
    #    **而闸 18 是构建里最靠后的一道**：它要真跑所有反验，排在最后。
    #    **也就是说：一条要在 12 分钟后才报的义务，等于没有及时提醒。**
    #    **本条把同一个判断挪到第 30 秒**（preflight 在副本树建好后就跑）。
    #
    #    **只核「新增的」，不核存量**：存量 49 份早就在表里，
    #    而「已存在反验的耗时漂了」是闸 18 方向四d 在跑时核的另一族（它的判据是运行时实测）。
    new_relt = sorted(
        p for p in changed_set
        if p.startswith(os.path.join(sub, "scripts", "selftest-"))
        and changed[p] == "??"
        and FIXTURE_RE.match(os.path.basename(p)) is None)
    if new_relt:
        gate18 = os.path.join(out, sub, "scripts", "verify-selftest-bootable.py")
        if not os.path.exists(gate18):
            problems.append("副本树里没有闸 18（%s）—— **判据⑨ 读不到事实源即未能核对**，"
                            "本批新增反验 %s 有没有登记无从核对（纪律 101）"
                            % (os.path.join(sub, "scripts", "verify-selftest-bootable.py"),
                               [os.path.basename(x) for x in new_relt]))
        else:
            try:
                reg = registered_costs(gate18)
            except (OSError, SyntaxError, ValueError) as exc:
                problems.append("闸 18 源码里读不出 `SLOW` / `SELFTEST_COSTS`（%s）——未能核对"
                                % exc)
            else:
                miss = [os.path.basename(x) for x in new_relt
                        if os.path.basename(x) not in reg]
                if miss:
                    problems.append(
                        "本批新增反验 %s 没有在闸 18 的 `SELFTEST_COSTS` / `SLOW` 里登记 —— "
                        "**不登记的后果是闸 18 方向四d 报红，而那要等构建跑满全程才看得到；"
                        "先跑一次它、把秒数填进去即可**（`seconds` 是上限，宁大勿小，纪律 204）"
                        % miss)
                else:
                    notes.append("本批新增反验 %d 份都已在闸 18 的实测耗时表里登记"
                                 % len(new_relt))
    else:
        notes.append("判据⑨：本批没有新增反验（存量不在本判据范围内，"
                     "「已存在反验的耗时漂了」由闸 18 方向四d 在运行时核）")

    # ⑦ 纪律编号连续（9..max 无缺漏、无重复）——**原先是每批 wrapper 里手抄的一段**，
    #    **而 wrapper 住在 /tmp，下一批就没有了**（纪律 371：判据写在会被丢掉的地方，
    #    等于没有判据）。**它必须住在这个入仓的工具里。**
    rules = os.path.join(out, sub, "AUDIT-RULES.md")
    if os.path.exists(rules):
        text = open(rules, encoding="utf-8").read()
        seen = {}
        for m in re.finditer(r"^(\d+)\. ", text, re.M):
            k = int(m.group(1))
            seen[k] = seen.get(k, 0) + 1
        top = max(seen) if seen else 0
        dup = sorted(k for k, v in seen.items() if k >= 9 and v > 1)
        gap = [n for n in range(9, top + 1) if n not in seen]
        if gap or dup:
            problems.append("纪律编号 9..%d 缺失 %s、重复 %s（副本树的 AUDIT-RULES.md）"
                            % (top, gap, dup))
        else:
            notes.append("纪律编号 9..%d 连续无缺漏、无重复（读的是副本树那份）" % top)
    else:
        notes.append("纪律编号连续性：**跳过**（副本树里没有 AUDIT-RULES.md）"
                     "——**没跑就是没跑，不当通过**")

    # ⑧ 本批的批次行必须在副本树里（`--expect-batch-row N`）
    if expect_batch_row:
        prog = os.path.join(out, sub, "PROGRESS.md")
        if not os.path.exists(prog):
            problems.append("**未能核对**本批批次行：副本树里没有 PROGRESS.md"
                            "（读不出来不等于存在，纪律 101）")
        else:
            ptext = open(prog, encoding="utf-8").read()
            if re.search(r"^\|\s*%d\s*\|" % expect_batch_row, ptext, re.M):
                notes.append("副本树含 Batch %d 的批次行" % expect_batch_row)
            else:
                problems.append("副本树的 PROGRESS.md 里**没有** Batch %d 的批次行"
                                "—— 构建跑的那棵树里没有这一批的账本行，"
                                "**而提交后它就成了唯一一份记录**" % expect_batch_row)

    # ⑤ 闸 8（表格结构）：0.5 秒，而它在本项目里至少抓到过三处我自己写坏的表格
    if run_tables_gate:
        rc, out_text = run_gate(out, sub, "verify-tables.py")
        if rc != 0:
            problems.append("副本树上闸 8 rc=%d：%s" % (rc, out_text.strip().split("\n")[0]))
        else:
            notes.append("副本树上闸 8 通过（表格结构）")

    return problems, notes


# ── 自测：一正一负两个已知答案样本（纪律 350） ──────────────────────────
def self_test():
    """**不碰真仓库**：在临时目录里造两棵极小的树。

    负样本 = FILES 覆盖全部改动 → 必须 0 问题；
    正样本 = 漏掉一个文件 + 同事 WIP 过期 → 必须恰好报出那两个问题。
    **两个样本都有已知答案，这一组判别式才算被验过。**
    """
    import tempfile
    import shutil
    base = tempfile.mkdtemp(prefix="preflight-selftest.")
    repo, sub = os.path.join(base, "repo"), "sub"
    os.makedirs(os.path.join(repo, sub, "scripts"))
    subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.name", "t"], check=True)
    # 一个被跟踪的闸脚本（闸 8 要能跑）
    with open(os.path.join(repo, sub, "scripts", "verify-tables.py"), "w",
              encoding="utf-8") as fh:
        fh.write("import sys\nprint('ok')\nsys.exit(0)\n")
    #: **闸 18 夹具**——判据⑨ 的事实源。**必须在 commit 之前造**：
    #: 它是已入库文件，真实的 `git archive HEAD` 必然带上它，
    #: **而副本树里没有它就意味着「副本树建错了」或「闸 18 被删了」**（那正是判据⑨ 该报的）。
    #: **第一版没造它，于是判据⑨ 把反验⑤ 专门造的 `selftest-1.sh` 报成
    #: 「读不到事实源」**——**那个失败是对的，而缺的是夹具不是判据**（纪律 344）。
    #: 登记 `selftest-1.sh` 是**如实**：在夹具的设定里它确实是一份新增反验。
    with open(os.path.join(repo, sub, "scripts", "verify-selftest-bootable.py"), "w",
              encoding="utf-8") as fh:
        fh.write('SLOW = {\n    "selftest-slow-one.py": {"seconds": 30},\n}\n'
                 'SELFTEST_COSTS = {\n    "selftest-1.sh": 1.0,\n'
                 '    "selftest-new-thing.py": 1.0,\n}\n')
    # 两个本批文件（会被改脏）
    for name in ("mine-a.md", "mine-b.md"):
        with open(os.path.join(repo, sub, name), "w", encoding="utf-8") as fh:
            fh.write("x\n")
    #: **已入库但被同事改了的文件**——它在 `git archive HEAD` 里**本来就该有**。
    #: **必须有这个夹具**，否则判据④（副本树里绝不能出现未跟踪文件）
    #: 就没有「不误伤」的那一半：**2026-10-07 真仓库上正是这条误报了 3 处**
    #: （`10-tasks/README.md` 等三个已入库文件），而**那三个恰恰必须出现在副本树里**。
    with open(os.path.join(repo, sub, "wip-tracked.md"), "w", encoding="utf-8") as fh:
        fh.write("t\n")
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-qm", "base"], check=True)
    # **同事的未跟踪 WIP 必须在提交之后建**——
    # 第一版把它写在 commit 之前，于是它进了 `HEAD`、`git archive` 也带上它，
    # **副本树里就「出现了同事的文件」**，负样本当场判失败。
    # **而那个失败是对的**：判据抓到了「副本树里混进了不该有的文件」，
    # **错的是夹具的搭法**——**这正是自测该有的样子：负样本失败时，
    # 先怀疑夹具，再怀疑判据**（纪律 344）。
    with open(os.path.join(repo, sub, "wip.md"), "w", encoding="utf-8") as fh:
        fh.write("w\n")
    # wip-tracked.md 被改脏 ⇒ 状态是 ` M`（**已入库**），副本树里**应当有** HEAD 版
    with open(os.path.join(repo, sub, "wip-tracked.md"), "w", encoding="utf-8") as fh:
        fh.write("t-edited\n")
    # 把 mine-b 改脏
    with open(os.path.join(repo, sub, "mine-b.md"), "w", encoding="utf-8") as fh:
        fh.write("changed\n")
    # wip.md 保持 untracked ⇒ 它在 changed 里，却不该在 `git archive HEAD` 里

    out = os.path.join(base, "out")
    #: **`tar -C` 要的是已存在的目录**——第一版忘了建，
    #: 报出来的是 `tar: could not chdir to …/out`，
    #: **而真实原因是「目标目录没建」**，离得很远（纪律 157 同族）。
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(base, "a.tar"), "wb") as fh:
        subprocess.run(["git", "-C", repo, "archive", "HEAD", sub], check=True, stdout=fh)
    subprocess.run(["tar", "-xf", os.path.join(base, "a.tar"), "-C", out], check=True)
    for name in ("mine-a.md", "mine-b.md"):
        with open(os.path.join(repo, sub, name)) as s, \
                open(os.path.join(out, sub, name), "w") as d:
            d.write(s.read())

    # 夹具：纪律表与账本（判据⑦⑧ 的输入）——**必须造，否则那两条判据在自测里
    # 只会走「跳过」分支，等于没被验过**（纪律 265：覆盖范围只等于被造出来的形态）
    rules_body = "".join("%d. 第 %d 条\n    说明\n\n" % (n, n) for n in range(1, 13))
    with open(os.path.join(repo, sub, "AUDIT-RULES.md"), "w", encoding="utf-8") as fh:
        fh.write(rules_body)
    with open(os.path.join(repo, sub, "PROGRESS.md"), "w", encoding="utf-8") as fh:
        fh.write("| 7 | 有一批 | x |\n| 8 | 有一批 | x |\n")
    for name in ("AUDIT-RULES.md", "PROGRESS.md"):
        shutil.copyfile(os.path.join(repo, sub, name), os.path.join(out, sub, name))

    #: **刚造的两个夹具文件也在 `files` 里**——它们是在 commit **之后**建的，
    #: **所以在判据①（漏叠加）眼里就是「本批改了却没登记」**（第一版就栽在这里，
    #: 负样本当场判失败）。**而那个失败是对的**：判据抓到了「副本树会跑上一批的版本」，
    #: **错的是夹具没把它们登记成「本批文件」**——**在夹具的设定里它们确实是**。
    files = [os.path.join(sub, "mine-a.md"), os.path.join(sub, "mine-b.md"),
             os.path.join(sub, "AUDIT-RULES.md"), os.path.join(sub, "PROGRESS.md")]
    #: **`??`（未跟踪）与 ` M`（已入库但被改）两种状态都要在名单里**——
    #: 它们在判据①②里待遇相同，在判据④里**必须分开**。
    wip = [os.path.join(sub, "wip.md"), os.path.join(sub, "wip-tracked.md")]

    # 负样本：两个本批文件都叠了 → 0 问题。
    # **它同时是判据④的「不误伤」那一半**：`wip-tracked.md`（` M`）
    # 此刻**就在副本树里**（HEAD 版），若判据④不按状态码分开就会误报。
    p1, n1 = preflight(repo, sub, out, files, wip)
    assert not p1, ("负样本本该 0 问题，却报了：%s" % p1)
    assert any("KNOWN_WIP 生效中" in x and "未跟踪的新文件" in x for x in n1), n1
    assert any("KNOWN_WIP 生效中" in x and "已入库文件被改" in x for x in n1), n1

    # 正样本①：FILES 漏掉 mine-b → 必须点名它
    # **只摘掉 mine-b 一个**——`files[:1]` 在夹具加了纪律表与账本之后会**连那两个一起摘掉**，
    # **于是这条断言从「1 个问题」变成「3 个问题」而失败**；
    # **而那个失败又一次是对的**：判据①忠实地报出了全部三个漏登记的文件，
    # **错的是样本想表达的「只漏一个」**（纪律 344：负样本失败时先怀疑夹具）。
    only_b_dropped = [f for f in files if not f.endswith("mine-b.md")]
    p2, _ = preflight(repo, sub, out, only_b_dropped, wip)
    assert len(p2) == 1 and "mine-b.md" in p2[0], p2

    # 正样本②：把同事的 WIP 从名单里去掉 → 必须报「漏叠加」并点名它们
    p3, _ = preflight(repo, sub, out, files, [])
    assert len(p3) == 2, p3
    assert any("wip.md" in x for x in p3) and any("wip-tracked.md" in x for x in p3), p3

    # 正样本③：排除名单过期（同事已撤销）→ 必须出「⚠ 名单失效」那条提示，
    # **而且它必须是 notes 而不是 problems**——失效本身不该让构建失败。
    # **必须把仍在生效的 WIP 一起留着**——第一版只写 `wip_stale = ["sub/gone.md"]`，
    # **把 wip.md 从名单里挤掉了，于是它变成「漏叠加」**，
    # **而我要验的那条（名单失效）根本没被单独验到**。
    wip_stale = [os.path.join(sub, "gone.md")] + wip
    p4, n4 = preflight(repo, sub, out, files, wip_stale)
    assert not p4, p4
    assert any("没有**改动" in x and "gone.md" in x for x in n4), n4

    # 正样本④：判据④的「能抓」那一半——**同事的未跟踪文件被叠进了副本树**
    # （模拟叠加脚本写错，把整个工作区 cp 过去那种手滑）→ 必须点名它。
    # **注意这里只能 cp 未跟踪的 wip.md**：`wip-tracked.md` 本来就在副本树里，
    # **而那是对的**，判据④按状态码分开正是不许把它当成同一件事。
    shutil.copyfile(os.path.join(repo, sub, "wip.md"), os.path.join(out, sub, "wip.md"))
    p5, _ = preflight(repo, sub, out, files, wip)
    assert len(p5) == 1 and "wip.md" in p5[0] and "未跟踪" in p5[0], p5
    #: 反向再确认一次：**删掉这个多余文件后就恢复 0 问题**——
    #: 否则上面那条可能只是「碰巧报了别的东西」
    os.remove(os.path.join(out, sub, "wip.md"))
    p6, _ = preflight(repo, sub, out, files, wip)
    assert not p6, p6

    # ── 反验⑤：「第 N 例真的存在」四支样本 ──────────────────────────
    #: 夹具刻意照抄 `selftest-meta.sh` 的**两种真实形态**：
    #: 执行器调用、头部注释里的同名例号、手写内联块。
    drv_rel = os.path.join(sub, "scripts", "selftest-1.sh")
    drv_body = (
        "# 反验 1\n"
        "#   1) 能抓：把标题数改小 —— **这一行是注释，但它长得跟可执行行一样**\n"
        "run_fail_case \"1) 能抓：标题数改小\" \"实际 9\" \\\n"
        "  \"true\"\n"
        "#   3) 能抓：**这一例只写在注释里**（夹具刻意造的，对应真文件里\n"
        "#        头部那 22 行 `#   N)` 计划清单）\n"
        "    echo \"  ✓ 7) 内联块形态也算存在\"; PASS=$((PASS+1))\n"
    )
    drv = os.path.join(repo, sub, "scripts", "selftest-1.sh")
    with open(drv, "w", encoding="utf-8") as fh:
        fh.write(drv_body)
    shutil.copyfile(drv, os.path.join(out, sub, "scripts", "selftest-1.sh"))

    # 负样本：执行器形态的第 1 例 + 内联块形态的第 7 例，都必须判「存在」
    # **它必须同时进 `files`**——夹具是在 commit 之后造的，所以它是未跟踪的，
    # **而判据①（漏叠加）会当场把它报出来**（第一版就栽在这里）。
    # **在夹具的设定里它确实就是「本批文件」**，所以放进 `files` 是如实的，
    # **不是为了让断言过而放宽判据**。
    files2 = files + [drv_rel]
    p7, n7 = preflight(repo, sub, out, files2, wip, run_tables_gate=False,
                       expect_case=["%s:1" % drv_rel, "%s:7" % drv_rel])
    assert not p7, p7

    assert any("执行器形态" in x for x in n7), n7
    assert any("内联块形态" in x for x in n7), n7

    # 正样本⑤：**第 3 例只写在注释里** → 必须点名它，且必须说清「只在注释里」。
    #: **这是本组判据存在的全部理由**：Batch 320 写的 `grep -q "^50)"` 是恒假，
    #: 而它的反面 `grep -q "50)"` 是恒真（撞上头部注释那 22 行）——
    #: **两种直觉写法一假一真，方向相反，而「都报绿」这个后果一样。**
    p8, _ = preflight(repo, sub, out, files2, wip, run_tables_gate=False,
                      expect_case=["%s:3" % drv_rel])
    assert len(p8) == 1 and "第 3 例" in p8[0] and "只在注释行里" in p8[0], p8

    # 正样本⑥：例号根本不存在 → 报「可执行行里找不到」
    p9, _ = preflight(repo, sub, out, files2, wip, run_tables_gate=False,
                      expect_case=["%s:99" % drv_rel])
    assert len(p9) == 1 and "可执行行里找不到" in p9[0], p9

    # 正样本⑦：驱动文件不在副本树里 → **必须报「未能核对」而不是「不存在」**
    #: （纪律 101：解析器退化的表现是 rc=2「未能核对」，不是 rc=1「不一致」）
    p10, _ = preflight(repo, sub, out, files2, wip, run_tables_gate=False,
                       expect_case=["%s:1" % os.path.join(sub, "scripts", "没有这个.sh")])
    assert len(p10) == 1 and "未能核对" in p10[0], p10

    # ── 反验⑦⑧：纪律编号连续 / 本批批次行 ──────────────────────────
    # 负样本：夹具里纪律 1..12 连续、账本里有第 7、8 批 → 0 问题
    #: **用 `files2` 而不是 `files`**——`selftest-1.sh` 是上面反验⑤造的夹具（commit 之后），
    #: **它也在「本批改动」里**，而用 `files` 会让判据①报它（第一版就栽在这里）
    p11, n11 = preflight(repo, sub, out, files2, wip, run_tables_gate=False,
                         expect_batch_row=8)
    assert not p11, p11
    assert any("纪律编号 9..12 连续" in x for x in n11), n11
    assert any("副本树含 Batch 8" in x for x in n11), n11

    # 正样本⑧：**纪律表里挖掉第 11 条** → 必须报「缺失 11」并点名
    # **两棵树都要挖**——只挖副本树的话，判据③（逐字节 cmp）会先报「不一致」，
    # **于是这条样本量到的其实是③而不是⑦**（第一版就栽在这里：断言写的是「1 个问题」，
    # **而实测是 2 个，而多出来的那个是对的**——**注入必须只让目标判据失败**，
    # 否则「样本过了」证明不了任何事，纪律 344）。
    needle = "11. 第 11 条\n    说明\n\n"
    #: **注入前先把干净内容存下来**——两棵树都被挖过，
    #: **而「补回去」那一步只补了副本树的话，工作区那份仍然是缺的**，
    #: **于是反向样本报的仍然是「缺失 11」**（第一版就栽在这里：
    #: **反向验证的失败形态是「我以为复原了，其实只复原了一半」**）。
    pristine = open(os.path.join(repo, sub, "AUDIT-RULES.md"), encoding="utf-8").read()
    assert needle in pristine, "注入锚点不存在（纪律 344：先怀疑夹具）"
    for tree in (repo, out):
        with open(os.path.join(tree, sub, "AUDIT-RULES.md"), "w", encoding="utf-8") as fh:
            fh.write(pristine.replace(needle, "", 1))
    p12, _ = preflight(repo, sub, out, files2, wip, run_tables_gate=False)
    assert len(p12) == 1 and "缺失 [11]" in p12[0], p12
    # **反向再确认一次**：补回去就恢复 0 问题——否则上面那条可能只是「碰巧报了别的东西」
    for tree in (repo, out):
        with open(os.path.join(tree, sub, "AUDIT-RULES.md"), "w", encoding="utf-8") as fh:
            fh.write(pristine)
    p13, _ = preflight(repo, sub, out, files2, wip, run_tables_gate=False)
    assert not p13, p13

    # 正样本⑨：**问一个账本里没有的批次** → 必须点名它
    p14, _ = preflight(repo, sub, out, files2, wip, run_tables_gate=False,
                       expect_batch_row=99)
    assert len(p14) == 1 and "没有" in p14[0] and "Batch 99" in p14[0], p14

    # 正样本⑩：**PROGRESS.md 不在副本树里** → 必须报「未能核对」而不是「不存在」
    #: **这里只断言「目标那条在」，不钉问题总数**——删掉一个已登记的文件会**同时**触发
    #: 判据③（逐字节 cmp 报「副本树里没有它」），**而那一条是对的**。
    #: **钉总数会把「顺手多报一条」变成失败，而那可能不是缺陷**（纪律 344 的姊妹条：
    #: **断言要钉目标判据，钉总数钉的是巧合**）。
    os.remove(os.path.join(out, sub, "PROGRESS.md"))
    p15, _ = preflight(repo, sub, out, files2, wip, run_tables_gate=False,
                       expect_batch_row=8)
    assert any("未能核对" in x and "PROGRESS.md" in x for x in p15), p15
    shutil.copyfile(os.path.join(repo, sub, "PROGRESS.md"),
                    os.path.join(out, sub, "PROGRESS.md"))

    # ── 反验⑪（Batch 337 新增）：「新增反验有没有登记实测耗时」四支样本 ──
    #: **两份新增文件，一份是反验、一份是注入夹具**——**夹具那一份刻意不登记**：
    #: 判据⑨ 若不认夹具，它会被要求登记，于是**「不误伤」那一半根本验不到**
    #: （判据⑨ 用 `selftestnames.FIXTURE_RE` 而不是自己重刻正则，
    #: **而那正是本批先栽过的地方**：第一遍按「文件名不以 `fix-` 开头即反验」扫，
    #: 得出「80 份未登记」，**而那 80 份全是夹具**——Batch 256 记过同一个坑）。
    new_real = os.path.join(sub, "scripts", "selftest-new-thing.py")
    new_fix = os.path.join(sub, "scripts", "selftest-9-fix-3-thing.py")
    for rel, body in ((new_real, "print('x')\n"), (new_fix, "print('fixture')\n")):
        with open(os.path.join(repo, rel), "w", encoding="utf-8") as fh:
            fh.write(body)
        shutil.copyfile(os.path.join(repo, rel), os.path.join(out, rel))
    #: **`new_real` / `new_fix` 已经是「相对仓库根」的路径**（`sub` 已在里面），
    #: **所以只拼 `repo` / `out`，不多拼一次 `sub`**：
    #: 第一版写成 `os.path.join(repo, sub, rel)`，路径变成 `repo/sub/sub/scripts/…`，
    #: 报出来的是 `FileNotFoundError`——**而真实原因离得很远**
    #: （纪律 157 同族：「目录不存在」听着像环境问题，其实是这一行多拼了一段）。
    #: **闸 18 也要进 `files`**：下面正样本会把它改脏，而它在夹具里是 commit 之前造的
    #: 已入库文件——**忘了加，判据① 就会如实多报一条「漏叠加」**。
    g18_rel = os.path.join(sub, "scripts", "verify-selftest-bootable.py")
    files3 = files2 + [new_real, new_fix, g18_rel]

    # 负样本：反验已登记、夹具不在表里（而它不该被要求登记）→ 0 问题
    p16, n16 = preflight(repo, sub, out, files3, wip, run_tables_gate=False)
    assert not p16, p16
    #: **是「至少 1 份」不是「1 份」**：反验⑤ 那个 `selftest-1.sh` 也是一份未跟踪的
    #: 新增反验（它刻意照抄 `selftest-meta.sh` 的执行器形态），**而它在闸 18 夹具里已登记**。
    #: **第一版断言写成「1 份」而判据如实报了 2 份**——
    #: **失败的是断言不是判据**（纪律 344：先怀疑夹具与样本，再怀疑判据）。
    assert any("都已" in x and "登记" in x for x in n16), n16

    # 正样本⑪-a：把那份新增反验从闸 18 的表里删掉 → 必须点名它，且**不能**点名那个夹具
    g18_repo = os.path.join(repo, g18_rel)
    g18 = os.path.join(out, g18_rel)
    orig = open(g18_repo, encoding="utf-8").read()
    with open(g18_repo, "w", encoding="utf-8") as fh:
        fh.write(orig.replace('    "selftest-new-thing.py": 1.0,\n', ""))
    shutil.copyfile(g18_repo, g18)
    p17, _ = preflight(repo, sub, out, files3, wip, run_tables_gate=False)
    assert any("selftest-new-thing.py" in x and "登记" in x for x in p17), p17
    #: **这一条是「不误伤」的反向断言**：那个 `-fix-` 夹具从头到尾就不在表里，
    #: **而判据不许要求它登记**——**若报的是它的名字，说明判据把夹具也管起来了**。
    assert not any("fix-3" in x for x in p17), p17
    with open(g18_repo, "w", encoding="utf-8") as fh:
        fh.write(orig)
    shutil.copyfile(g18_repo, g18)

    # 正样本⑪-b（退化）：副本树里没有闸 18 → 必须报「未能核对」
    #: **只钉目标那一条，不钉问题总数**（沿用正样本⑩ 写下的约定）：
    #: 判据③（副本树里必须有 `FILES` 的每个文件）**也会报**，而那一条是对的；
    #: **第一版钉了「1 个问题」于是数到 2 当场失败**——**那是样本期望值写错，不是判据**。
    #: **而 ⑨ 那一支不可省**：闸 18 若没被本批改动就不在 `FILES` 里，
    #: 副本树里可能有它的 HEAD 版，**那时 ③ 不会报、只有 ⑨ 会报**。
    os.remove(g18)
    p18, _ = preflight(repo, sub, out, files3, wip, run_tables_gate=False)
    assert any("未能核对" in x and "闸 18" in x for x in p18), p18
    shutil.copyfile(g18_repo, g18)
    p19, _ = preflight(repo, sub, out, files3, wip, run_tables_gate=False)
    assert not p19, p19

    shutil.rmtree(base, ignore_errors=True)
    print("自测 19 个样本全过：负样本 0 问题（且 ` M` 的 WIP 在副本树里**不**误报）；"
          "正样本①漏叠加、正样本②名单漏了 WIP、"
          "正样本③名单过期（走 notes 不走 problems）、"
          "正样本④副本树混进未跟踪文件（抓得到，且拿掉就恢复 0 问题）、"
          "⑤例号只在注释里（恒真的反面）、⑥例号根本不存在、"
          "⑦驱动读不出来（报未能核对而非不存在）、"
          "⑧纪律表挖掉一条（且**两棵树都挖**，否则量到的是 cmp 那条）、"
          "⑨问一个账本里没有的批次、⑩账本文件不在副本树里（报未能核对）；"
          "**另有一对反向**：补回去 / 放回去都必须恢复 0 问题，"
          "**而第一版的反向样本报的仍然是缺陷——因为「补回去」只补了副本树那一棵**；"
          "**⑪新增反验未登记实测耗时（负样本 + 能抓 + **反向断言不许把注入夹具也管起来** "
          "+ 退化必报未能核对）**")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO_DEFAULT)
    ap.add_argument("--sub", default="docs/user-manual/beeftv-canvas")
    ap.add_argument("--out", help="副本树根目录")
    ap.add_argument("--files", help="一行一个相对路径：本批要叠加的文件")
    ap.add_argument("--wip", help="一行一个相对路径：同事的未提交 WIP（显式排除）")
    ap.add_argument("--no-gate", action="store_true", help="不跑闸 8")
    ap.add_argument("--expect-case", action="append", default=[],
                    metavar="驱动:例号",
                    help="在副本树里核「第 N 例真的存在」，可重复。"
                         "**两支形态都认**（执行器 / 手写内联块），"
                         "**且注释行不算存在**")
    ap.add_argument("--expect-batch-row", type=int, default=None, metavar="N",
                    help="副本树的 PROGRESS.md 里必须有 Batch N 的批次行。"
                         "**原先它只活在每批的临时 wrapper 里，而 wrapper 住在 /tmp，"
                         "下一批就没有了**（纪律 371）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        self_test()
        return 0
    if not (a.out and a.files and a.wip):
        ap.error("需要 --out --files --wip（或用 --self-test）")

    problems, notes = preflight(a.repo, a.sub, a.out, read_list(a.files),
                                read_list(a.wip), run_tables_gate=not a.no_gate,
                                expect_case=a.expect_case,
                                expect_batch_row=a.expect_batch_row)
    for n in notes:
        print("  ℹ " + n)
    for p in problems:
        print("  ✗ " + p)
    if problems:
        print("承重核对失败（%d 处），不跑构建" % len(problems))
        return 1
    print("承重核对通过：%d 条信息、0 处问题" % len(notes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
