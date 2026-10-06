#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 44 `verify-gate-registry.py` 的反向验证（Batch 311）。

**七例：五支能抓 + 一支 rc 语义 + 一支不误伤**，加一支基线前提守卫算在五支里。

**本闸判的不是手册正文，是「关于闸的一份登记」**——
所以能抓用例必须去改**闸脚本本身**与**登记本身**，
而**不能像闸 43 的反验那样只改内容页**（那会变成一条与本闸无关的用例）。
沙箱带整份 `scripts/` + `AUDIT-RULES.md`，注入全部发生在临时树上，**真树一个字节都不动**。

  0) **基线前提守卫**：未注入 → 必须 rc=0 且 0 条 ✗。
     **没有它，「所有用例都红」与「判据根本没跑」在结果上长得一样。**
  1) **能抓·指纹（本闸存在的理由）**：把一道**已登记**的闸
     （`verify-quota-tables.py`）在沙箱里改一个字节 → 必须 rc=1 并说
     「登记已作废」。**这一条就是 Batch 304 那件事的形状**——
     改闸不改表，表照样绿着。
  2) **能抓·悬空**：给登记加一行指向一个不存在的闸 → 必须 rc=1 并说「没有这个文件」。
  3) **能抓·合计不自洽**：把 `total` 改掉而各行不动 → 必须 rc=1 并说「合计不自洽」。
  4) **能抓·形态残缺**：删掉某行的 `green_sentence` → 必须 rc=1 并说
     「只登记一半形态」。**这一条守的是 Batch 311 实测出来的那个坑**：
     红绿两态句句首逐字相同而数字含义相反，只登记一半就会在下一次重测上数错。
  5) **能抓·订正不见了**：把 `AUDIT-RULES.md` 里那行「闸门登记现状」删掉
     → 必须 rc=1 并说「订正不见了」。**纪律 332② 的 8/32 必须原样留着**，
     所以唯一能让读的人看见订正的办法，就是把「订还在不在」变成可判的事实。
  6) **rc 语义**：把登记文件删掉 → 必须 **rc=2 而不是 rc=1**。
     「读不出登记」不是「查出问题」，是「根本没得查」（纪律 101）。
  7) **不误伤**：改一道**未登记**的闸（`verify-tables.py`）**并在 AUDIT-RULES.md
     末尾追加一段不碰标记行的文字** → 必须 rc=0。
     **这一支比「不误伤」更重要**：它证明本闸只钉住登记里那 8 道，
     **不会退化成「任何编辑都报错」的噪声源**——
     而一个天天误报的判据，人就会学会忽略它（纪律 297）。

**注入没打中判用例失败，不判通过**：每个 `edit_one` 都断言锚点在改前改后
**各出现且只出现一次**，打不中当场抛错（漂亮的 0 是一个探针故障，纪律 155）。
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

from stagedeps import child_env

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = "verify-gate-registry.py"
REGISTRY = "gate-registry.json"
RULES = "AUDIT-RULES.md"
_STATES = ("通过", "失败", "作废")
results = []


def record(name, ok, detail=""):
    results.append((name, "通过" if ok else "失败", detail))


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(s)


def sandbox():
    """临时树 = 整份 `scripts/` + `AUDIT-RULES.md`。

    **为什么必须带 `AUDIT-RULES.md`**：本闸的方向五要读它，
    而方向五恰好是「订正还在不在」——**少搬这一份，方向五会因「读不到」而恒真**，
    用例 5 就会假绿。

    **为什么不能用 `copytree` 搬整棵手册树**：手册树 132M，其中
    `node_modules` 99M + `.vitepress` 16M + `screenshots` 12M 与本闸毫无关系。
    本闸只读 `scripts/` 下的 9 个文件与一份账本。

    **⚠️ `scripts/` 那一步必须一行写完**：`copytree(HERE, os.path.join(tmp,"scripts"))`
    ——拆成上一行 `dst = ...` 再 `copytree(HERE, dst)`，闸 17 的
    `copies_whole_scripts()` 只在前两个实参里找 `"scripts"`，于是报「不自洽」。
    **本文件按既有写法改自己的代码，不去动那条判据**（纪律 284）。
    """
    tmp = tempfile.mkdtemp(prefix="gate-registry-selftest.")
    shutil.copytree(HERE, os.path.join(tmp, "scripts"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(os.path.join(ROOT, RULES), os.path.join(tmp, RULES))
    return tmp


def run_in(tmp):
    env = child_env(tmp)          # **沙箱自己就是这一轮的手册根**
    r = subprocess.run([sys.executable, os.path.join(tmp, "scripts", GATE)],
                       capture_output=True, text=True, cwd=tmp, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def edit_one(path, old, new):
    """**锚点必须改前改后都存在且唯一**——打不中当场抛错，不许静默当通过。

    **唯一性由 `count(old) == 1` 保证，替换是否真的发生由 `out != s` 保证。**
    刻意**不加** `old not in out`——「新串包含旧串」是插入式注入的常态，
    那条断言会恒假，把一条本来能过的用例判成失败（闸 43 的反验踩过）。
    """
    s = read(path)
    n = s.count(old)
    assert n == 1, "前提失配：锚点在 %s 里出现 %d 次（应为 1）" % (
        os.path.basename(path), n)
    out = s.replace(old, new, 1)
    assert out != s, "注入没有生效——判该用例失败"
    write(path, out)


def edit_registry(tmp, mutate):
    """按结构改登记（加行 / 改数 / 删字段）。改完当场读回来核对。"""
    p = os.path.join(tmp, "scripts", REGISTRY)
    reg = json.loads(read(p))
    mutate(reg)
    write(p, json.dumps(reg, ensure_ascii=False, indent=2) + "\n")
    return json.loads(read(p))          # **读回来**：写坏了当场就炸


def expect_red(tmp, want, case):
    rc, out = run_in(tmp)
    if rc != 1:
        record(case, False, "期望 rc=1，实测 rc=%d；输出末尾：%s"
               % (rc, out.strip().split("\n")[-1][:110]))
        return False
    if want not in out:
        record(case, False, "rc=1 但输出里没有「%s」" % want)
        return False
    record(case, True, "rc=1 且点名「%s」" % want)
    return True


TAIL = 'if __name__ == "__main__":\n    sys.exit(main())\n'
INJECT_COMMENT = "# 反验注入：模拟「产出登记的那道闸在测量之后被改过」\n"


def main():
    try:
        # 0) 基线前提守卫
        tmp = sandbox()
        try:
            rc, out = run_in(tmp)
            ok = (rc == 0 and "✗" not in out)
            record("基线前提守卫", ok,
                   "rc=%d、%d 条 ✗" % (rc, out.count("✗"))
                   if ok else "期望 rc=0 且 0 条 ✗，实测 rc=%d" % rc)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        # 1) 能抓·指纹
        tmp = sandbox()
        try:
            edit_one(os.path.join(tmp, "scripts", "verify-quota-tables.py"),
                     TAIL, TAIL + INJECT_COMMENT)
            expect_red(tmp, "登记已作废", "能抓·指纹（改闸不改编登记）")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        # 2) 能抓·悬空
        tmp = sandbox()
        try:
            def add_dangling(reg):
                reg["gates"].append({
                    "gate": "verify-gate-does-not-exist.py",
                    "upstream_items": 1, "measured_form": "红态",
                    "red_sentence": "x", "green_sentence": "y",
                    "gate_sha256": "0" * 64,
                })
            edit_registry(tmp, add_dangling)
            expect_red(tmp, "scripts/ 下没有这个文件", "能抓·悬空（登记指名不存在的闸）")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        # 3) 能抓·合计不自洽
        tmp = sandbox()
        try:
            def bump_total(reg):
                reg["total"] = reg["total"] + 1
            after = edit_registry(tmp, bump_total)
            assert after["total"] != 30, "注入没有生效——判该用例失败"
            expect_red(tmp, "合计不自洽", "能抓·合计不自洽")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        # 4) 能抓·形态残缺
        tmp = sandbox()
        try:
            def drop_green(reg):
                del reg["gates"][0]["green_sentence"]
            after = edit_registry(tmp, drop_green)
            assert "green_sentence" not in after["gates"][0], "注入没有生效——判该用例失败"
            expect_red(tmp, "只登记一半形态", "能抓·形态残缺（缺绿态句）")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        # 5) 能抓·订正不见了
        tmp = sandbox()
        try:
            edit_one(os.path.join(tmp, RULES),
                     "**闸门登记现状：8 道 / 7 红态 / 30 条（measured_at Batch 311）**",
                     "**（本行已被反验删除）**")
            expect_red(tmp, "订正不见了", "能抓·订正不见了")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        # 6) rc 语义：登记读不到 → rc=2
        tmp = sandbox()
        try:
            os.remove(os.path.join(tmp, "scripts", REGISTRY))
            rc, out = run_in(tmp)
            ok = (rc == 2 and "未能核对" in out)
            record("rc 语义·登记读不到", ok,
                   "rc=2 且说明未能核对" if ok
                   else "期望 rc=2 且含「未能核对」，实测 rc=%d" % rc)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        # 7) 不误伤：改未登记的闸 + 追加不碰标记行的正文
        tmp = sandbox()
        try:
            edit_one(os.path.join(tmp, "scripts", "verify-tables.py"),
                     TAIL, TAIL + "# 反验注入：改一道**未登记**的闸\n")
            rules_p = os.path.join(tmp, RULES)
            write(rules_p, read(rules_p) + "**反验注入：末尾追加一段普通文字。**\n")
            rc, out = run_in(tmp)
            ok = (rc == 0)
            record("不误伤·未登记的闸随便改", ok,
                   "rc=0" if ok else "期望 rc=0，实测 rc=%d：%s"
                   % (rc, out.strip().split("\n")[-1][:110]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        # ---- 收尾自检：必须接住一切异常 ----
        n = len(results)
        assert n == 8, "收尾自检：用例数应为 8，实测 %d" % n
        bad = [r for r in results if r[1] == "失败"]
        void = [r for r in results if r[1] == "作废"]
        print("=" * 68)
        for name, st, detail in results:
            print("  [%s] %-40s %s" % (st, name, detail[:64]))
        print("=" * 68)
        print("闸 44 反验：通过 %d / 失败 %d / 作废 %d = %d"
              % (n - len(bad) - len(void), len(bad), len(void), n))
        print("收尾自检过了：每支用例各自一棵全新沙箱，真树未动")
        return 1 if bad else 0
    finally:
        for name, st, detail in list(results):
            assert st in _STATES, "状态只能是 %s，收到 %r" % ("、".join(_STATES), st)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:               # 收尾必须接住一切异常
        print("[反验框架异常] %s: %s" % (type(exc).__name__, exc))
        print("已跑完 %d 例：" % len(results))
        for name, st, detail in results:
            print("  [%s] %s — %s" % (st, name, detail[:70]))
        sys.exit(1)