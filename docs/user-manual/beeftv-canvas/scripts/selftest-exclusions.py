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

Batch 226 再加 2 例（14→16），钉的是方向七（逐节祈使句）：
  能抓 1 条：
    15) 把不可用页里的就地提示删掉 → 必须报
  不误伤 1 条：
    16) 提示块**挪到小节末尾**（首句变回祈使句、但小节内仍有提示）→ 必须放行
  **16 钉的是本批踩到的一个统计失真**：判据若拿「第一行」当首句，
  提示一加上去那一节就成了「本来不是祈使句」——
  **notes 报「共核 0 个」而实际核了 2 个**；再往后只要提示**换个位置**，
  计数就一直停在 0，**看着像「这一节本来就干净」**。

Batch 224 再加 3 例（11→14），钉的是**判据分不分得清两种相反的意思**：
  能抓 2 条：
    12) 注入「页面基于源码静态证据」（某一部分只有源码）→ 必须报
    14) 把一个**靠这一族词才入面**的 excluded 页面告知抹掉 → 必须报
  不误伤 1 条：
    13) **同一个任务、同一个位置**，只把主语换成「所有断言均有运行时**或**源码证据」
        → 必须放行
  **12/13 是全份反验里最要紧的一对**：只因主语从「本页的一部分」变成
  「本页所有断言」，结论就该相反。**少 13 的话，12 可能只是「逢源码必报」**——
  那种判据把「全覆盖声明」也当降级后，就会开始要求页面写没必要的免责话术。

Batch 223 再加 2 例（9→11），钉的是**读取范围**：
  能抓 1 条：
    10) 降级自述**只**写在 `finding` 字段 → 必须报
  不误伤 1 条：
    11) 同一个注入，但目标页面**已经告知**取证边界 → 必须放行
  **10/11 的起因是一个真缺陷**：两处「付费红线」自述只存在于 `finding` 里，
  **而判据当时只读另外四个字段**——**读不到字段的判据，与不存在的判据在账面上完全一样。**

Batch 222 又加了「证据降级告知」方向，于是那时从 4 例变 9 例。
**新加的 4 例成对，验的是同一件事的两侧**：
  能抓 2 条：
    6) 把某一页上的告知**逐词抹掉** → 必须报「读者看不到」
    7) 凭空加一句降级自述，而目标页面确实没告知 → 必须报
  不误伤 2 条：
    8) 同样的注入，但目标页面**已经告知** → 必须放行
    9) 只往页面插一句与证据等级无关的正文 → 必须放行
  **8 和 6 缺一不可**：只有 6 的话，「能抓」可能只是「逢降级必报」。

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

try:
    import yaml
except ImportError:  # 反验需要按账本找出该复制哪些页面
    yaml = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(HERE, "verify-exclusions.py")
BATCHREAD = os.path.join(HERE, "batchread.py")
BASELINE = os.path.join(HERE, "baseline.py")
BEEFSRC = os.path.join(HERE, "beefsrc.py")
INVENTORY_REL = "task-inventory.yml"

PASS = VOID = FAIL = 0


def _manual_pages(inventory_text):
    """账本里全部 `manual_pages`（**不限 status**——降级自述不只出现在 excluded）。"""
    if yaml is None:
        return []
    data = yaml.safe_load(inventory_text)
    items = data if isinstance(data, list) else (data or {}).get("tasks", data)
    if isinstance(items, dict):
        items = list(items.values())
    out = []
    for it in items or []:
        if isinstance(it, dict):
            for p in (it.get("manual_pages") or []):
                out.append(str(p))
    return out


def _prepare(tmp, inventory_text, gate_text=None, page_edits=None):
    os.makedirs(os.path.join(tmp, "scripts"))
    # **必须连同 baseline.py 一起复制**（Batch 178 修，闸 17 抓出）：
    # 自 Batch 175 起被测闸门会 `from baseline import resolve_ref`；
    # 临时目录里没有它 → 闸门启动即 ModuleNotFoundError，**每一例都失败**，
    # **而 build-site.sh 仍然全绿**——反验坏掉不产生任何构建期信号。
    shutil.copy(BASELINE, os.path.join(tmp, "scripts", "baseline.py"))
    # **必须连同 batchread.py 一起复制**（Batch 181 修，闸 17 抓出）：
    # 闸 5/闸 3 改为用 `batchread.read_many` 批量读上游（原来每个文件一次
    # `git show` 子进程，闸门本体各 10 秒）。临时目录里没有它 →
    # ModuleNotFoundError，**该反验的每一例都失败**，而 build-site.sh 仍全绿。
    # **这正是闸 17 建成后第一次真的派上用场**：改动落地几分钟内就被抓到。
    shutil.copy(BATCHREAD, os.path.join(tmp, "scripts", "batchread.py"))
    #: **Batch 197**：`verify-exclusions.py` 现在 import `beefsrc`（路径解析的单一来源），
    #: 临时目录里没有它就会 import 失败，**该反验每一例都会失败而构建仍然全绿**。
    shutil.copy(BEEFSRC, os.path.join(tmp, "scripts", "beefsrc.py"))
    shutil.copy(GATE, os.path.join(tmp, "scripts", "verify-exclusions.py"))
    if gate_text is not None:
        with open(os.path.join(tmp, "scripts", "verify-exclusions.py"), "w", encoding="utf-8") as fh:
            fh.write(gate_text)
    with open(os.path.join(tmp, INVENTORY_REL), "w", encoding="utf-8") as fh:
        fh.write(inventory_text)

    # **Batch 222 新增：把 `manual_pages` 指向的发布页也复制进来。**
    # 起因是本批新增的「证据降级告知」方向要读页面——**临时目录里没有那些文件**，
    # 于是它判定「页面读不到」并把退出码抬到 2，而下面 5 个老用例的判定是
    # 「本应放行却报错（误伤）」，**每一例都会失败**，
    # **而 build-site.sh 仍然全绿**（反验坏掉不产生任何构建期信号，Batch 178）。
    for rel in _manual_pages(inventory_text):
        src_page = os.path.join(ROOT, rel)
        if not os.path.isfile(src_page):
            continue
        dst = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src_page, dst)

    for rel, fn in (page_edits or {}).items():
        path = os.path.join(tmp, rel)
        assert os.path.isfile(path), f"页面没被复制进来，注入无处可下：{rel}"
        with open(path, encoding="utf-8") as fh:
            body = fh.read()
        new_body = fn(body)
        assert new_body != body, f"页面注入空转：{rel}"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_body)


def run(desc, want, expect_fail=True, transform=None, gate_text=None,
        inventory_text=None, page_edits=None):
    global PASS, VOID, FAIL
    base_inventory = open(os.path.join(ROOT, INVENTORY_REL), encoding="utf-8").read()
    base_gate = open(GATE, encoding="utf-8").read()

    inv = inventory_text if inventory_text is not None else base_inventory
    gt = gate_text if gate_text is not None else base_gate
    pe = page_edits
    if transform is not None:
        try:
            out = transform(inv, gt)
            # transform 可返回 (inv, gate) 或 (inv, gate, page_edits) 三元组
            if len(out) == 3:
                inv, gt, pe = out
            else:
                inv, gt = out
        except AssertionError as exc:
            print("  ✗ %s：锚点未命中，注入空转 → **本用例作废**（%s）" % (desc, exc))
            VOID += 1
            return

    tmp = tempfile.mkdtemp(prefix="beef-excl-selftest.")
    try:
        _prepare(tmp, inv, gt, pe)
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


def t_missing_reason(inv, _gate):
    """把 art-critique 的 exclusion_reason 整段删掉 → 必须报「没写理由」。

    **这一例钉的是 Batch 187 新增的那条方向**：上线首跑就抓到 art-critique
    的理由写在 `review_note` 里、而**没有任何脚本读那个字段**。
    注入时**连 review_note 一起留着**——因为真实缺陷的性质正是「写在了别处」，
    只删 exclusion_reason 会退化成「两条理由都没有」，测的就不是同一件事了。
    """
    m = re.search(r"  - id: art-critique\n(.*?)(?=\n  - id: )", inv, re.S)
    assert m, "锚点未命中：找不到 art-critique 任务块"
    block = m.group(0)
    assert "exclusion_reason:" in block, "前提失配：art-critique 已经没有 exclusion_reason 了"
    assert "review_note:" in block, "前提失配：art-critique 没有 review_note，测的就不是同一件事"
    stripped = re.sub(r"    exclusion_reason: >-\n(      .*\n)+", "", block, count=1)
    assert stripped != block, "前提失配：注入没生效"
    return inv.replace(block, stripped, 1), _gate


def t_benign(inv, _gate):
    """只改 excluded 任务的无关字段：id 与 status 都不动。"""
    anchor = "    exclusion_reason: 版本族需真实生成才能产生，受付费边界限制"
    assert anchor in inv, "锚点未命中：找不到 media-versions 的排除理由"
    return inv.replace(anchor, anchor + "（反验注入：只改这段文字，id 与 status 均不动）", 1), _gate


def _tell_terms(gate_text):
    """从**被测闸自己**里读告知词表——**不在这里手抄一份**（纪律 224/226）。

    手抄的后果不是「抄错」，是**抄对了也会漂**：闸里加了词而这里没加，
    用例就会拿着旧的短名单去抹页面，**抹不干净，判据仍报绿，测试却通过了**。
    """
    m = re.search(r"PAGE_TELL_TERMS = \((.*?)\n\)", gate_text, re.S)
    assert m, "锚点未命中：找不到 PAGE_TELL_TERMS"
    terms = re.findall(r'"([^"]+)"', m.group(1))
    assert terms, "PAGE_TELL_TERMS 解析出 0 项——注入必然空转"
    return terms


def t_silent_page(_inv, gate):
    """把某一页上的告知**逐词抹掉** → 判据必须报「读者看不到」。

    **只删一句是不够的，而这一点是量出来的**：被测页 `storage-quota` 同时命中
    「没有运行时」和「不可用」，后者出自页内一张故障对照表的单元格。
    删掉那句最强的提示，它照样判绿——**而那正是假阴性的形状**：
    测试报告「通过」，真缺陷还在。所以这里按被测闸自己的词表逐词抹，
    不挑一个好看的锚点。
    """
    terms = _tell_terms(gate)

    def edit(body):
        out = body
        for w in terms:
            out = out.replace(w, "")
        return out

    return _inv, gate, {"10-tasks/storage-quota.md": edit}


def t_injected_downgrade(inv, _gate):
    """给一个**页面完全没告知**的任务凭空加一句降级自述 → 必须报。

    这一例钉的是**输入侧**：判据看得见「账本说了」，也要看得见「页面没说」。
    靶子选 `create-nodes`——实测它的页面不含任何告知词，而它此刻在账本里
    **本就没有**降级自述，所以干净树下这一条不成立（**不误伤**由用例 4 保证）。
    """
    m = re.search(r"  - id: create-nodes\n(.*?)(?=\n  - id: )", inv, re.S)
    assert m, "锚点未命中：找不到 create-nodes 任务块"
    block = m.group(0)
    assert "review_note:" not in block, \
        "前提失配：create-nodes 已有 review_note，注入的不是同一个位置"
    return (inv.replace(block, block + "\n    review_note: 反验注入：本节只有源码证据，没有运行时实证。\n", 1),
            _gate)


def t_downgrade_already_told(inv, _gate):
    """给一个**页面已经告知**的任务加降级自述 → 必须放行（不误伤）。

    与上一例成对：**同一个注入，只因为目标页面的实际状态不同就得出相反结论**。
    没有这一对，「能抓」就可能只是「逢降级必报」——那种判据一样绿，但一文不值。
    """
    m = re.search(r"  - id: generate-audio\n(.*?)(?=\n  - id: )", inv, re.S)
    assert m, "锚点未命中：找不到 generate-audio 任务块"
    block = m.group(0)
    assert "仅有源码" in block, \
        "前提失配：该任务账本里本就有降级自述，注入的不是同一个位置"
    return (inv.replace(block, block + "\n    review_condition: 反验注入：本节只有源码证据，没有运行时实证。\n", 1),
            _gate)


def t_benign_page(inv, gate):
    """只往页面上插一句与证据等级无关的正文 → 必须放行。"""
    def edit(body):
        anchor = "## 账号有十项配额"
        assert body.count(anchor) == 1, "锚点未命中：找不到「## 账号有十项配额」"
        return body.replace(anchor, anchor + "\n\n（反验注入：与证据等级无关的一句正文。）", 1)

    return inv, gate, {"10-tasks/storage-quota.md": edit}


def t_finding_only_downgrade(inv, _gate):
    """把降级自述**只**写进 `finding` 字段 → 判据必须报。

    **这一例钉的是 Batch 223 的真缺陷形态**：两处「付费红线」自述
    （`create-workspace` 的「未触发任何真实生成」、`model-channels` 的
    「未配置任何 Provider Key」）**只存在于 `finding` 里**，
    而判据当时只读 `exclusion_reason` / `review_note` / `review_condition` /
    `evidence.note` 四个字段。
    **读不到字段的判据，与不存在的判据在账面上完全一样**——
    所以必须钉住「`finding` 也在读取范围里」，否则加回去没人知道。

    靶子 `navigate-canvas`：实测它的页面不含任何已登记的告知措辞，
    且账本里此刻**没有** `finding` 字段（**不误伤**由用例 12 保证）。
    """
    m = re.search(r"  - id: navigate-canvas\n(.*?)(?=\n  - id: )", inv, re.S)
    assert m, "锚点未命中：找不到 navigate-canvas 任务块"
    block = m.group(0)
    assert "finding:" not in block, \
        "前提失配：navigate-canvas 已有 finding 字段，注入的不是同一个位置"
    return (inv.replace(block, block + "\n    finding: 反验注入：付费红线——未触发任何真实生成。\n", 1),
            _gate)


def t_finding_downgrade_already_told(inv, _gate):
    """同一个注入，但目标页面**已经告知**取证边界 → 必须放行。

    与上一例成对。**少了它，「能抓」可能只是「逢 `finding` 必报」**。
    """
    m = re.search(r"  - id: generate-audio\n(.*?)(?=\n  - id: )", inv, re.S)
    assert m, "锚点未命中：找不到 generate-audio 任务块"
    block = m.group(0)
    assert "finding:" not in block, \
        "前提失配：generate-audio 已有 finding 字段，注入的不是同一个位置"
    return (inv.replace(block, block + "\n    finding: 反验注入：付费红线——未触发任何真实生成。\n", 1),
            _gate)


def _nav_block(inv):
    m = re.search(r"  - id: navigate-canvas\n(.*?)(?=\n  - id: )", inv, re.S)
    assert m, "锚点未命中：找不到 navigate-canvas 任务块"
    block = m.group(0)
    assert "review_note:" not in block, \
        "前提失配：navigate-canvas 已有 review_note，注入的不是同一个位置"
    return block


def t_statement_source_must_report(inv, _gate):
    """注入「**页面基于源码静态证据**」→ 必须报。

    **这一例钉的是 Batch 224 补的那一族词**：全库 5 处真降级长这样
    （`media-versions` / `cloud-agent` / `agent-memory-skills` / `local-runtime`），
    **而否定式词表一条都认不出**——它们说的是「这一部分基于源码」，
    不是「某一部分没有运行时证据」。不钉住这一族，
    下一个人精简词表时会以为它没有用。
    """
    block = _nav_block(inv)
    return (inv.replace(block, block + "\n    review_note: 反验注入：本页**页面基于源码静态证据**。\n", 1),
            _gate)


def t_all_claims_must_not_report(inv, _gate):
    """**同一个任务、同一个位置**，只把主语从「页面的一部分」换成
    「页面**所有断言**」并接一个「或」→ **必须放行**。

    这是全份反验里最要紧的一条。它证明的不只是「排除式规则没坏」，
    而是**判据分得清两种相反的意思**：

      · 「本页**基于源码静态证据**」= 有一部分只有源码 → 降级，要盯
      · 「本页**所有断言均有**运行时**或**源码证据」= 每一部分都有证据 → 不是降级

    **少这一对，用例 12 就可能只是「逢『源码』必报」**——
    那样的判据一样绿，但把「全覆盖声明」也当降级后，
    它就会开始要求页面写没必要的免责话术。
    """
    block = _nav_block(inv)
    return (inv.replace(block, block + "\n    review_note: 反验注入：本页所有断言均有运行时或源码证据。\n", 1),
            _gate)


def t_excluded_page_silent_must_report(inv, gate):
    """把一个 **excluded 页面**上的告知逐词抹掉 → 必须报。

    **这一例钉的是覆盖面本身**：Batch 224 之后判据认领 **14 个任务**，
    其中 8 个是本批新入面的 excluded 页面（它们的账本写「页面基于源码静态证据」）。
    **这 8 个在 Batch 223 结束时判据是看不见的**——
    「4 个 excluded 页面都有告知」那句结论当时是**人工核对**出来的，
    本批把它变成了会自己喊的东西。**钉住它，才不会有人日后把词表收窄回去。**
    """
    terms = _tell_terms(gate)

    def edit(body):
        out = body
        for w in terms:
            out = out.replace(w, "")
        return out

    return inv, gate, {"10-tasks/cloud-agent.md": edit}


def _strip_hint_block(body):
    """删掉 cloud-agent.md「## 发起与对话」小节里的 ::: warning 提示块。"""
    lines = body.split("\n")
    i = next((j for j, l in enumerate(lines)
              if l.strip().startswith("::: warning 这一节写的是")), None)
    assert i is not None, "锚点未命中：找不到该提示块"
    j = next((k for k in range(i, len(lines)) if lines[k].strip() == ":::"), None)
    assert j is not None, "提示块没有闭合的 :::"
    del lines[i - 1:j + 2]
    out = "\n".join(lines)
    assert out != body, "前提失配：删除空转"
    return out


def t_imperative_must_report(inv, gate):
    """把不可用页里的就地提示删掉 → 判据必须报。

    **钉的是 Batch 226 的方向七**：页首那句「这是历史机制」只护得住
    **从上往下读**的人；读者用 Ctrl+F 搜到「打开云 Agent 面板」，
    或从右侧页内目录点进「## 发起与对话」时，那一句会被单独送到眼前，
    **而页首声明不会跟着出现**。
    """
    return inv, gate, {"10-tasks/cloud-agent.md": _strip_hint_block}


def t_hint_moved_must_not_report(inv, gate):
    """提示块**挪到小节末尾**（首句变回祈使句，但小节内仍有提示）→ 必须放行。

    **这一例钉的是本批踩到的一个统计失真**：加上提示后，小节的第一行
    变成了 `::: warning …`，若判据拿「第一行」当首句，它会把这一节
    当成「本来就不是祈使句」跳过——**notes 于是报「共核 0 个」，
    而实际核了 2 个**；再往后，只要提示**换个位置**，计数就一直停在 0，
    **看着像「这一节本来就干净」**。

    正确修法是**整块剔除容器**再取首句。本例证明剔除生效：
    提示挪到末尾后，首句重新变成祈使句，**而判据仍放行**——
    因为它看的是「**本小节内有没有提示**」，不是「提示在第几行」。
    """
    def move(body):
        lines = body.split("\n")
        i = next((j for j, l in enumerate(lines)
                  if l.strip().startswith("::: warning 这一节写的是")), None)
        assert i is not None, "锚点未命中：找不到该提示块"
        j = next(k for k in range(i, len(lines)) if lines[k].strip() == ":::")
        block = lines[i - 1:j + 2]
        del lines[i - 1:j + 2]
        k = next(m for m, l in enumerate(lines) if l.startswith("## 审批"))
        lines[k:k] = ["", ""] + block
        out = "\n".join(lines)
        assert out != body, "前提失配：移动空转"
        return out

    return inv, gate, {"10-tasks/cloud-agent.md": move}


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
    run("5) excluded 却没写 exclusion_reason（必须报）", "没写 exclusion_reason",
        transform=t_missing_reason)
    run("6) 页面上的告知被抹掉（必须报）", "只有记账的人看得见",
        transform=t_silent_page)
    run("7) 凭空加的降级自述 + 页面无告知（必须报）", "只有记账的人看得见",
        transform=t_injected_downgrade)
    run("8) 不误伤：降级自述 + 页面已告知（必须放行）", "证据降级告知",
        expect_fail=False, transform=t_downgrade_already_told)
    run("9) 不误伤：只改页面无关正文（必须放行）", "证据降级告知",
        expect_fail=False, transform=t_benign_page)
    run("10) 降级自述只写在 finding 字段 + 页面无告知（必须报）", "找不到任何已登记的告知措辞",
        transform=t_finding_only_downgrade)
    run("11) 不误伤：finding 里的降级自述 + 页面已告知（必须放行）", "证据降级告知",
        expect_fail=False, transform=t_finding_downgrade_already_told)
    run("12) 「页面基于源码静态证据」类降级（必须报）", "找不到任何已登记的告知措辞",
        transform=t_statement_source_must_report)
    run("13) 不误伤：「所有断言均有运行时或源码证据」是全覆盖声明（必须放行）", "证据降级告知",
        expect_fail=False, transform=t_all_claims_must_not_report)
    run("14) excluded 页面（靠本族词入面）上的告知被抹掉（必须报）", "找不到任何已登记的告知措辞",
        transform=t_excluded_page_silent_must_report)
    run("15) 不可用页的就地提示被删掉（必须报）", "以祈使句开头",
        transform=t_imperative_must_report)
    run("16) 不误伤：提示块挪到小节末尾、首句变回祈使句（必须放行）", "证据降级告知",
        expect_fail=False, transform=t_hint_moved_must_not_report)

    print("=== 结果：通过 %d / 失败 %d / 作废 %d ===" % (PASS, FAIL, VOID))
    return 1 if (FAIL or VOID) else 0


if __name__ == "__main__":
    sys.exit(main())
