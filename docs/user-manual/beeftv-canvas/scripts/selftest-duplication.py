#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 37「同一段解析逻辑被手写了几遍」的反向验证（Batch 256 新增）。

用例清单：
  1  真实现状 → 不报（三条重复都在登记表里且带理由）
  2  新增一处**未登记**的重复 → 必报（能抓）
  3  登记过的重复**涉及文件变了**而理由没改 → 必报（**过期的理由会替新的重复背书**）
  4  注释里贴一份正则原文 → **不得**报（不误伤：注释不是代码）
  5  一段**短**字面量（`$want` 那种变量名）在几份文件里都出现 → **不得**报
     （**这一条是首跑当场撞出来的假阳性**，见闸的文件头）
  6  收敛掉一条已登记的重复 → 登记表里那条**变成孤儿** → 必报
     （**「登记表只能变短」从 Batch 257 起是判据而不只是说说**：
     收敛了不删，理由就开始替不存在的东西背书）
  7  收敛掉一条**并同步从登记表删掉** → **不得**报
     （**6/7 必须成对**：只钉 6 的话，那条判据可能只是「凡有收敛就报」，
     而做完正确动作之后它必须闭嘴）
"""

import ast
import hashlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE_SRC = os.path.join(HERE, "verify-duplication.py")
PROBE = "dupselftest"

results = []
_TMP = tempfile.mkdtemp(prefix=PROBE)
_real_accepted = None
_real_scan = None


def load_gate():
    import importlib.util
    spec = importlib.util.spec_from_file_location("vd", GATE_SRC)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(gate):
    r = subprocess.run([sys.executable, gate], capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def probe_root(files, accepted=None, accepted_file=None):
    """建一个临时 scripts/ 副本：整份 `copytree`，然后只替换指定文件。

    **Batch 256 首版这里是一个手写的逐文件循环**
    （`for f in os.listdir(…): if f.endswith((".py", ".sh")): shutil.copy2(…)`），
    **而闸 17 认不出它**——`copies_whole_scripts()` 只认 `shutil.copytree`
    实参里带 `scripts` 这个末段，于是闸 17 把这份反验报成 7 处
    「没搬 `baseline` / `batchread` / `beefsrc` / `pngstat` / `scope`」，
    **连带 `selftest-selftest-deps.py` 12 例里 7 例转红、闸 18 因此报红**。

    **可这份反验明明搬了整份 `scripts/`，一行依赖都没漏。**
    **这是「判据认写法不认事实」的第五次复发**
    （前四次：Batch 190 两处、Batch 239、Batch 247）。

    **⚠️ Batch 288 更正这个计数与上面这句的适用范围**：
    **上面写的是「第五次」的那件事发生在 Batch 256，而 Batch 287 又复发了一次——第六次**，
    **形态同样是把 `os.path.join(tmp, "scripts")` 从 `copytree(...)` 实参里拆出去**
    （新反验 `selftest-slow-bootable.py` 的 `sandbox()`）。
    **而 Batch 288 实测的差集是 0 份**：把「认写法」与「认事实」两版 `copies_whole_scripts()`
    在**全量 171 份反验与闸**上对跑，**答案完全一致（各 6 份判 True）**——
    **因为第六次那次的代码在上一个批次就已经改对了**。
    **所以「第五处缺陷」到今天为止没有留下任何一份被误报的反验**，
    **判据的修改是纯预防性的，且已实测是严格超集（只 False→True，不 True→False）**。
    **纪律 323**。

    **本批改代码侧而不是改判据侧**——理由是 `stagedeps.py` 早就写明
    「凡是『搬整目录』这个事实，都写成一次调用，**而不是去猜一个
    `for … os.listdir(…)` 的循环搬了些什么**」。
    **这里为什么不用 `stage_all()`**：本反验的意义**就是普查整棵树**，
    **而 `stage_all()` 只搬非反验的 `.py`**（实测 47 份，`.sh` 与
    `selftest-*` 全不在内），**临时树的普查从 88 条掉到 74 条**；
    `copytree` 搬 157 份 `.py`+`.sh` 齐全，**与真树输出逐字节相同**。
    **两种写法都被闸 17 认，换之前必须量等价（纪律 250）。**
    """
    d = os.path.join(_TMP, "tree")
    if os.path.isdir(d):
        shutil.rmtree(d)
    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(d, "scripts"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, body in files.items():
        p = os.path.join(d, "scripts", name)
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
    g = os.path.join(d, "scripts", "verify-duplication.py")
    if accepted is not None or accepted_file is not None:
        t = io.open(g, encoding="utf-8").read()
        if accepted is not None:
            i = t.find("ACCEPTED = {")
            j = t.find("\n}\n", i)
            assert i != -1 and j > i
            t = t[:i] + "ACCEPTED = " + accepted + t[j + 3:]
        if accepted_file is not None:
            t = t.replace('ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))',
                          'ROOT = %r' % d, 1)
        with io.open(g, "w", encoding="utf-8") as fh:
            fh.write(t)
    return d, g


def extract_re_line(path):
    """**从真文件里原样抽一行 `re.compile(…)`**。

    **为什么必须抽而不是手写**：用例 2/3 的第一版是**手打那条正则**，
    **而我打出来的比原文多一个收尾引号**——**于是注入的正则与原文不同，
    闸当然不报，而用例红了**。
    **那一红是注入无效，不是判据坏了**（纪律 281 推论一的又一次形态）。
    **所以：凡是要造「同一段字面量出现两次」，就从文件里抽，不要手打。**
    """
    with io.open(path, encoding="utf-8") as fh:
        for line in fh:
            if "re.compile(" in line and not line.lstrip().startswith("#"):
                return line.rstrip("\n")
    raise AssertionError("前提失配：%s 里找不到一行 re.compile(" % path)


def synth(tag):
    """现造一条**现实里绝不会存在**的正则行，返回 `(key, 字面量, 那一行)`。

    **Batch 264：三个用例改为自造，不再从真实登记表取素材。**
    **为什么不能问「表里有哪一条」**——
    上一批刚把夹具从「写死那一条」改成「取表里第一条」，
    **而本批把登记表清零了，于是三个用例整批作废**：
    「登记表是空的——没有任何一条可当夹具」。
    **那个修法只解开了「绑定某一条」，却仍然绑定在「表里有东西」上**，
    **而表会被清零恰恰是这套制度想要的结果**——
    **让夹具的正确性依赖于「还有重复没收掉」，那是在给「收了也不对」埋雷**。
    **合成字面量带一个只有这里才会写出来的记号**，
    **所以「造一条孤儿」不需要知道任何真实字面量，也不需要现场有重复**。
    """
    body = 'B262_SYNTH_%s\\("(/b262-synth/%s)' % (tag, tag)
    key = hashlib.md5(body.encode("utf-8")).hexdigest()[:12]
    return key, body, "SYNTH_%s = re.compile(r'%s')\n" % (tag, body)


def add_accepted(gate_src, key, files, why="**反验合成的夹具，不是真的重复**"):
    """往 `ACCEPTED = {…}` 里**插一条**登记，**并断言真的插进去了**。

    **`str.replace` 静默无操作是纪律 294 记过的坑**（Batch 256 与 262 各一次），
    **而这里它一旦静默，用例会造出一个「什么都没插」的沙箱**——
    **于是用例红在它没打算核的那件事上**（纪律 281 推论四）。
    """
    marker = "ACCEPTED = {"
    assert marker in gate_src, "闸里找不到 %r" % marker
    entry = ('    "%s": (\n        "反验合成夹具",\n        %r,\n'
             '        "%s"),\n') % (key, list(files), why)
    out = gate_src.replace(marker, marker + "\n" + entry, 1)
    assert out != gate_src, "插入静默无操作（纪律 294）"
    assert out.count('"%s": (' % key) == 1, "插进去的不是那一条，或插了不止一条"
    return out


def record(name, ok, detail=""):
    """`ok` 既可以是布尔，**也可以直接是状态词**（`"通过"` / `"失败"` / `"作废"`）。

    **这一条是 Batch 200 那个 bug 的原样复现，而它就写在隔壁那份反验的 `record` 里。**
    **本文件第一版的 `record` 只写了 `("通过" if ok else "失败")`**，
    **于是 `main()` 里的 `record(t.__name__, "作废", ...)` 被记成了「通过」、打 ✓**
    ——**一份作废的用例在输出里长得和通过一模一样**（纪律 178 的字面形态）。
    **实测**：用例 2 的前提失配在输出里是 `✓`，而汇总说「通过 6、失败/作废 0」。
    **而 Batch 200 已经在 `selftest-selftest-bootable.py` 里修过同一个函数**
    ——**同一个修法在一个文件里存在、在另一个文件里不存在**，
    **这与 Batch 178/181/197/251/252 五次漏搬是同一个病**。
    """
    status = ok if isinstance(ok, str) else ("通过" if ok else "失败")
    results.append((name, status, detail))


# ── 1 真实现状 ──────────────────────────────────────────────────────
def m_clean():
    rc, out = run(GATE_SRC)
    record("1 真实现状 → 不报", rc == 0, "rc=%d" % rc)


# ── 2 新增未登记的重复 → 必报 ───────────────────────────────────────
def m_unregistered_duplicate_reported():
    # **源文件必须是 `tablerow.py`**——**第一版抽的是 `verify-endpoints.py`，
    # 而它那条 GET/POST 正则正在白名单里**，于是闸报的是「涉及的文件变了」
    # 而不是「没有登记」——**而那条也是红，用例仍然抓到了东西，却抓错了那一件**。
    # **一个用例红在它没打算核的那件事上，等于没核**（纪律 281 推论四）。
    a = os.path.join(ROOT, "scripts", "tablerow.py")
    line = extract_re_line(a)          # **原样抽，不手打**
    target = os.path.join(ROOT, "scripts", "verify-shot-integrity.py")
    body = io.open(target, encoding="utf-8").read() + "\n# 注入\n" + line + "\n"
    _, g = probe_root({"verify-shot-integrity.py": body})
    rc, out = run(g)
    ok = rc == 1 and "登记表里没有它" in out
    record("2 新增一处未登记的重复（同一行正则落到第二个文件）→ 必报", ok, "rc=%d" % rc)


# ── 3 登记过的重复涉及文件变了 → 必报 ──────────────────────────────
def m_stale_acceptance_reported():
    """**登记了那条，可它在另一个文件里也出现了**——
    于是「涉及文件」与登记时不同，**而理由是照着旧的那份写的**。

    **Batch 264：素材自造**——现算一条现实里不存在的正则，
    把它注入**两个**文件造出跨文件重复，**而登记只列其中一个**。
    **先前两版分别踩过两个坑**：①抽真实文件里第一行 `re.compile(`
    （**改动前那恰好是登记那条，是巧合不是设计**，收敛后红在另一件事上）；
    ②从登记表动态取第一条（**本批清零登记表后整批作废**）。
    """
    key, _body, line = synth("STALE")
    f1, f2 = "verify-endpoints.py", "verify-exclusions.py"
    gate_src = add_accepted(io.open(GATE_SRC, encoding="utf-8").read(), key, [f1])
    _, g = probe_root({
        f1: io.open(os.path.join(ROOT, "scripts", f1), encoding="utf-8").read() + line,
        f2: io.open(os.path.join(ROOT, "scripts", f2), encoding="utf-8").read() + line,
        "verify-duplication.py": gate_src})
    rc, out = run(g)
    ok = rc == 1 and "涉及的文件变了" in out
    record("3 已登记的重复涉及文件变了 → 必报（过期的理由不背书）", ok, "rc=%d" % rc)


# ── 4 注释里贴正则 → 不得报 ─────────────────────────────────────────
def m_comment_not_counted():
    src = io.open(os.path.join(ROOT, "scripts", "verify-line-counts.py"), encoding="utf-8").read()
    inject = src + '\n# 参考：re.compile(r"Batch\\s*254\\s*有一条")\n'
    _, g = probe_root({"verify-line-counts.py": inject})
    rc, out = run(g)
    record("4 注释里贴一份正则原文 → 不得报", rc == 0, "rc=%d" % rc)


# ── 5 短字面量 → 不得报 ─────────────────────────────────────────────
def m_short_literal_not_counted():
    body = 'X=1\n'
    files = {n: body for n in ("verify-probe-a.py", "verify-probe-b.py", "verify-probe-c.py")}
    _, g = probe_root(files)
    rc, out = run(g)
    record("5 短字面量（变量名形态）在几份文件里 → 不得报", rc == 0, "rc=%d" % rc)


def drop_accepted_key(text, key):
    """从 `ACCEPTED = {…}` 里**原样**删掉一条登记（不手打内容）。

    **为什么要原样删而不是重新拼一份 dict**：手打会打错内容，
    **而「打错的内容」造出来的孤儿与真实孤儿长得一模一样**——
    **那样测的就不是判据了，是我手打的准不准**。
    """
    marker = '    "%s": (' % key
    start = text.index(marker)
    end = text.index("),\n", start) + len("),\n")
    out = text[:start] + text[end:]
    assert marker not in out, "删完还在"
    assert len(out) < len(text)
    return out


# ── 6 收敛掉一条却没从登记表删 → 必报（登记成了孤儿）────────────────
def m_orphan_acceptance_reported():
    """**登记条目指向一个现实里不存在的字面量** → 必报，且要点名是哪一条。

    **Batch 257 立的反向核对**（「本闸管不了」与「本闸已经有那个数却没用」是两回事），
    **而它的反验素材原先取自真实登记表——本批清零登记表后它整批作废**。
    **现在素材自造**：合成的 key 现实里必然不存在，
    **所以「孤儿」这个状态不需要任何真实重复在场**。
    """
    key, _body, _line = synth("ORPHAN")
    gate_src = add_accepted(
        io.open(GATE_SRC, encoding="utf-8").read(), key,
        ["verify-endpoints.py", "verify-exclusions.py"])
    _, g = probe_root({"verify-duplication.py": gate_src})
    rc, out = run(g)
    #: **必须点名那一条**，不能只看 rc——
    #: **「报了红但没说是哪一条」对人没有任何用处**，
    #: **而一条判据若只会说「有问题」，下一个人只能自己去数**。
    ok = rc == 1 and key in out and "对不上现实" in out
    record("6 收敛掉一条却没从登记表删 → 必报（且要点名是哪一条）", ok, "rc=%d" % rc)


# ── 7 收敛掉一条并同步删了登记 → 不得报（做完正确动作必须闭嘴）──────
def m_converged_and_deregistered_ok():
    """**6 的配对另一半**：同样造一条孤儿，**但把登记也一起删掉**。

    **为什么必须成对**：只钉 6 的话，那条判据可能只是
    「凡有 `ACCEPTED` 条目比现实多就报」——
    **而正确做法（收敛 + 删登记）之后它也照样会报**，
    **那样的判据会把人逼回去重新登记一条**（纪律 260 的同一形状：
    **逼它归零的压力会催生「为了让闸闭嘴而做错事」**）。
    """
    key, _body, _line = synth("CLEANED")
    gate_src = add_accepted(
        io.open(GATE_SRC, encoding="utf-8").read(), key,
        ["verify-endpoints.py", "verify-exclusions.py"])
    _, g = probe_root({"verify-duplication.py": drop_accepted_key(gate_src, key)})
    rc, out = run(g)
    record("7 收敛掉一条并同步删了登记 → 不得报（做完正确动作闸必须绿）",
           rc == 0, "rc=%d" % rc)


def main():
    tests = [m_clean, m_unregistered_duplicate_reported,
             m_stale_acceptance_reported, m_comment_not_counted,
             m_short_literal_not_counted, m_orphan_acceptance_reported,
             m_converged_and_deregistered_ok]
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            record(t.__name__, "作废", "前提失配：%s" % exc)
        except Exception as exc:                          # noqa: BLE001
            record(t.__name__, "失败", "用例自身抛异常：%s: %s" % (type(exc).__name__, exc))
    failed = 0
    for name, status, detail in results:
        mark = {"通过": "✓", "失败": "✗", "作废": "—"}[status]
        print("  %s %s  %s" % (mark, name, detail))
        if status != "通过":
            failed += 1
    print("闸 37 反验：%d 例，通过 %d，失败/作废 %d"
          % (len(results), len(results) - failed, failed))
    shutil.rmtree(_TMP, ignore_errors=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
