#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第五道闸（verify-exclusions.py）覆盖完整性检查的反向验证。

闸门名承诺「excluded 页解禁条件核对」，而 Batch 164 的起因正是：
**6 条 excluded 里 art-critique 从未被它提及，也没有任何机制会提醒。**
所以这里要验的是**新加的那条双向检查本身抓不抓得住**：

  能抓 3 条：
    1) 账本新增一条**未登记**的 excluded → 必须报「未被本闸认领」
    2) 登记表里有一条**已不再是** excluded 的 → 必须报「过期登记」
    3) 条件判据块数与 MECHANICAL_CONDITIONS 条目数不符 → 必须报
  不误伤 1 条：
    4) 只改 excluded 任务的其他字段（不动 id、不动 status）→ 必须照旧通过

⚠️ 每条注入都用 `assert` 钉死锚点。**锚点失配会静默产出「什么都没改」的输入**，
然后用例把「闸门没报错」当成结论——Batch 162 为此专门加了通用空转检测，
这里从源头避开：锚点没命中就直接判作废，不进 PASS 也不进 FAIL。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-exclusions.py")
BASELINE = os.path.join(HERE, "baseline.py")
INVENTORY_REL = "task-inventory.yml"

PASS = VOID = FAIL = 0


def _prepare(tmp, inventory_text, gate_text=None):
    os.makedirs(os.path.join(tmp, "scripts"))
    # **必须连同 baseline.py 一起复制**（Batch 178 修，闸 17 抓出）：
    # 自 Batch 175 起被测闸门会 `from baseline import resolve_ref`；
    # 临时目录里没有它 → 闸门启动即 ModuleNotFoundError，**每一例都失败**，
    # **而 build-site.sh 仍然全绿**——反验坏掉不产生任何构建期信号。
    shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-exclusions.py"))
    if gate_text is not None:
        with open(os.path.join(tmp, "scripts", "verify-exclusions.py"), "w", encoding="utf-8") as fh:
            fh.write(gate_text)
    with open(os.path.join(tmp, INVENTORY_REL), "w", encoding="utf-8") as fh:
        fh.write(inventory_text)


def run(desc, want, expect_fail=True, transform=None, gate_text=None, inventory_text=None):
    global PASS, VOID, FAIL
    base_inventory = open(os.path.join(ROOT, INVENTORY_REL), encoding="utf-8").read()
    base_gate = open(GATE, encoding="utf-8").read()

    inv = inventory_text if inventory_text is not None else base_inventory
    gt = gate_text if gate_text is not None else base_gate
    if transform is not None:
        try:
            inv, gt = transform(inv, gt)
        except AssertionError as exc:
            print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
            VOID += 1
            return

    tmp = tempfile.mkdtemp(prefix="beef-excl-selftest.")
    try:
        _prepare(tmp, inv, gt)
        # baseline.py 用 BEEFTV_MANUAL_ROOT 定位手册根（Batch 178）：
        # 临时仓里没有 20-reference.md，不传就抛「读不到 20-reference.md」。
        env={**os.environ, "BEEFTV_MANUAL_ROOT": ROOT}
        r = subprocess.run([sys.executable, os.path.join("scripts", "verify-exclusions.py")],
                           cwd=tmp, env=env, capture_output=True, text=True)
        out = r.stdout + r.stderr
        if expect_fail and r.returncode == 0:
            print("  ✗ %s：闸门本应报错，却通过了" % desc); FAIL += 1
        elif expect_fail and want not in out:
            print("  ✗ %s：报错了但不是 [%s]；实际：" % (desc, want))
            print("      " + out.strip().split("\n")[-1][:120]); FAIL += 1
        elif not expect_fail and r.returncode != 0:
            print("  ✗ %s：本应放行却报错（误伤）：%s" % (desc, out.strip()[:160])); FAIL += 1
        elif not expect_fail and want not in out:
            print("  ✗ %s：虽通过但输出里找不到 [%s]" % (desc, want)); FAIL += 1
        else:
            print("  ✓ %s" % desc); PASS += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_add_unregistered(inv, _gate):
    """新增一条 excluded 任务，但闸门的两张登记表里都没有它。"""
    anchor = "\n  - id: cloud-agent"
    assert anchor in inv, "锚点未命中：找不到 - id: cloud-agent"
    injected = (
        "\n  - id: selftest-ghost-task\n"
        "    title: 反验注入：一条没有任何人认领的 excluded 任务\n"
        "    status: excluded\n"
        "    exclusion_reason: 反验注入\n"
    )
    return inv.replace(anchor, injected + anchor, 1), _gate


def t_stale_registry(inv, _gate):
    """把 art-critique 从 excluded 改成 verified → EXEMPT 里的登记就成了过期条目。"""
    m = re.search(r"  - id: art-critique\n(.*?)(?=\n  - id: )", inv, re.S)
    assert m, "锚点未命中：找不到 art-critique 任务块"
    block = m.group(0)
    assert "status: excluded" in block, "锚点未命中：art-critique 不是 excluded"
    return inv.replace(block, block.replace("status: excluded", "status: verified", 1), 1), _gate


def t_condition_count(_inv, gate):
    """往判据脚本里塞一个条件块，但不同步 MECHANICAL_CONDITIONS → 两者对不上。"""
    anchor = "    # —— 条件 1："
    assert anchor in gate, "锚点未命中：找不到条件 1 的判据块"
    return _inv, gate.replace(anchor, "    # —— 条件 5：反验注入的假条件块 ——\n" + anchor, 1)


def t_benign(inv, _gate):
    """只改 excluded 任务的无关字段：id 与 status 都不动。"""
    anchor = "    exclusion_reason: 版本族需真实生成才能产生，受付费边界限制"
    assert anchor in inv, "锚点未命中：找不到 media-versions 的排除理由"
    return inv.replace(anchor, anchor + "（反验注入：只改这段文字，id 与 status 均不动）", 1), _gate


def main():
    r = subprocess.run([sys.executable, GATE], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✓ 基线：真实账本通过（%s）" % r.stdout.strip().split("\n")[-1][:60])
        globals()["PASS"] = globals()["PASS"] + 1
    else:
        print("  ✗ 基线：真实账本应当通过，实际 rc=%d" % r.returncode); globals()["FAIL"] = globals()["FAIL"] + 1

    run("1) 账本新增一条未登记的 excluded（必须报）", "未被本闸认领", transform=t_add_unregistered)
    run("2) 登记表条目已不再是 excluded（必须报过期）", "过期登记", transform=t_stale_registry)
    run("3) 条件判据块数与清单不符（必须报）", "条件清单与实际判据块数不符", transform=t_condition_count)
    run("4) 不误伤：只改 excluded 任务的无关字段（必须放行）", "全部已认领",
        expect_fail=False, transform=t_benign)

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
