#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★ batch 867 负控：★ 证明「修正后的判据」**有牙**。

## ★ 为什么必须有这一步

★ 「七条门禁全绿」这句话本身**不能证明**任何事 ⟹ ⟹
★ 它同样可能是「**恒绿**」⟹ ⟹ 也就是判据根本不读任何会变的东西。
★ ⇒ **必须**用阴性对照证明：★ 把源码改成**坏的** ⟹ ⟹ 门禁**必须翻红**。

## ★ ★★ 纪律：★ 变异必须落在【被断言读的那个量】上

★ Batch 866 记过的坑：★ 负控没打红 ⟹ ⟹ **先查变异落点** ⟹ ⟹ 再怀疑判据。
★ 本批已经撞过一次：★ 第一次负控改的是 `includeExternalEdges`（**参数名**）
⟹ ⟹ 而判据读的是 `requestedIds.length === 1 && !includesGroup` ⟹ ⟹ 没打红
⟹ ⟹ ⟹ ⟹ **不是**判据没牙 ⟹ ⟹ ⟹ ⟹ 而是**变异没落在点上**。
★ ⇒ 所以本脚本对每条负控都**写明「判据读的是哪个量」**。

## ★ ★★ 每条负控都必须**复原源码**

★ Batch 866 记过的坑：★ 变异层失败时源码不复原 ⟹ ⟹ 门禁带着污染退出。
★ ⇒ 本脚本用 `try/finally` ⟹ ⟹ **无条件**复原 ⟹ ⟹ 且复原后做**字节级**自检。
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUT = ROOT / "docs/research/liblib-canvas-batch867-2026-10-01/raw/negative-audit.json"


class Mutation:
    """★ 一条负控：★ 改哪个文件、改成什么、期望哪条门禁翻红。

    ★ ★★ `old2`/`new2`：**第二处替换** ⟹ ⟹ 用于「**对调**两行」这类变异
    ⟹ ⟹ （★ 单处替换做不出对调 ⟹ ⟹ 而「只挪注释」不改变顺序 ⟹ ⟹ 门禁不会红）
    """

    def __init__(self, name, gate, relpath, old, new, expect_label,
                 old2=None, new2=None):
        self.name = name
        self.gate = gate
        self.relpath = relpath
        self.old = old
        self.new = new
        self.old2 = old2
        self.new2 = new2
        self.expect_label = expect_label


# ★ ★★ 每条负控都**逐字**对应到判据实际读的那个量
MUTATIONS = [
    Mutation(
        "N1: 753 的 setEdges 判据 —— 把实现改成声明形态",
        "753", "src/store/canvasStore.ts",
        "  setEdges: (edges: Edge[], options?: SetGraphOptions) => {",
        "  setEdges: (edges: Edge[], options?: SetGraphOptions) => void;",
        "setEdges",
    ),
    Mutation(
        "N2: 753 的 includeExternalEdges 判据 —— 改判据真正读的那个表达式",
        "753", "src/store/canvasStore.ts",
        "requestedIds.length === 1 && !includesGroup",
        "requestedIds.length === 2 && !includesGroup",
        "includeExternalEdges",
    ),
    Mutation(
        "N3: 754 的高清预设判据 —— 把绝对坐标改回相对坐标（batch 802 修的 bug）",
        "754", "src/store/canvasStore.ts",
        "position: { x: sourceAbsolute.x + 320, y: sourceAbsolute.y - 60 }",
        "position: { x: source.position.x + 320, y: source.position.y - 60 }",
        "绝对坐标",
    ),
    Mutation(
        "N4: 754 的「守住 802 修复」判据 —— 删掉 getAbsoluteNodePosition 那行",
        "754", "src/store/canvasStore.ts",
        "const sourceAbsolute = getAbsoluteNodePosition(source, nodesById);",
        "const sourceAbsolute = { x: source.position.x, y: source.position.y };",
        "绝对坐标",
    ),
    Mutation(
        "N5: 755/759 的行内菜单判据 —— 把 fixed 改回 absolute right-2 top-full",
        "755", "src/components/CanvasTabDropdown.tsx",
        "className=\"fixed z-[60] w-36",
        "className=\"absolute right-2 top-full z-[60] w-36",
        "batch 790",
    ),
    Mutation(
        "N6: 759 的回收站判据 —— 把「按剩余天数过滤」改成不过滤",
        "759", "src/app/project/page.tsx",
        "remainingDays(canvas.removedAt) > 0",
        "remainingDays(canvas.removedAt) >= -99999",
        "batch 805",
    ),
    Mutation(
        # ★ ★★ 第一版这条负控**写错了**：★ 只在 `setActiveCanvas` 前面加了行注释
        #   ⟹ ⟹ **顺序根本没变** ⟹ ⟹ 门禁当然不红
        #   ⟹ ⟹ ⟹ ⟹ ★ 这是「负控的变异没落在被断言读的量上」⟹ ⟹ 不是判据没牙
        #   ⟹ ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 正确做法：★ **对调**两行（★ 单处替换做不出对调）
        "N7: 759 的 openCanvas 顺序判据 —— 把 window.open 与 setActiveCanvas **对调**",
        "759", "src/app/project/page.tsx",
        "    setActiveCanvas(canvasId);",
        "    window.open(`/?canvas=${encodeURIComponent(canvasId)}`, \"_blank\");",
        "openCanvas",
        old2="    window.open(`/?canvas=${encodeURIComponent(canvasId)}`, \"_blank\");",
        new2="    setActiveCanvas(canvasId);",
    ),
    Mutation(
        "N8: 756 的 GROUP_PADDING 判据 —— 改成不是 20 的倍数",
        "756", "src/store/canvasStore.ts",
        "const GROUP_PADDING = 40;",
        "const GROUP_PADDING = 37;",
        "整数倍",
    ),
    Mutation(
        "N9: 758 的 dblclick 捕获阶段判据 —— 改回冒泡阶段",
        "758", "src/app/page.tsx",
        'container.addEventListener("dblclick", handleDoubleClick, true);',
        'container.addEventListener("dblclick", handleDoubleClick);',
        "捕获阶段",
    ),
    Mutation(
        "N10: 758 的 pane 闸判据 —— 把 classList.contains 改回 closest",
        "758", "src/app/page.tsx",
        'target?.classList.contains("react-flow__pane")',
        'target?.closest(".react-flow__pane")',
        "就是",
    ),
]


def run_gate(batch: str) -> tuple[int, str]:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=900, cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ★ ★★ 门禁自身的负控（G1／G2）⟹ ⟹ **测的是「本批门禁」本身** ⟹ ⟹
# ★ 判据读的是 `scripts/verify-liblib-batch867.py` 里的 `parse_gates()`
# ⟹ ⟹ 它从**回归清单** `probes/regress867.py` 里解析出条目 ⟹ ⟹
# ⟹ ⟹ 然后断言「依赖已消失 /tmp 文件的门禁**全部**在清单里」⟹ ⟹
# ⟹ ⟹ ⇒ **把清单里的一条删掉** ⟹ ⟹ 门禁**必须翻红** ⟹ ⟹ 否则它没牙。
GATE_SELF_TARGET = (ROOT / "docs/research/liblib-canvas-batch867-2026-10-01"
                    / "probes/regress867.py")
GATE_SELF_ANCHOR = '    ("761", "py"),\n'
# ★ ★★ G2 的注入：★ 把**同一个条目**写进**注释**里 ⟹ ⟹
# ★   ⇒ 判据**必须**仍然翻红 ⟹ ⟹ 因为 `parse_gates()` **先剥注释**再解析
# ★   ⇒ ⇒ ★ 这正是本批**实际踩到**的假绿：★ 第一版做负控时在注释里写了
# ★   ⇒ ⇒   `("761","py")` ⟹ ⟹ 被当成了清单里的一条 ⟹ ⟹ 缺口恒空
# ★   ⇒ ⇒   ⟹ ⟹ 门禁**假绿** ⟹ ⟹ 反而「证明」了它没牙
GATE_SELF_COMMENT = '    # ★ 负控注入：("761", "py")  ← ★ 注释里的假条目\n'


def neg_gate_itself() -> list[dict]:
    """★ G1／G2：★ **门禁自身的负控** ⟹ ⟹ 证明「缺口检测」与「剥注释」都**有牙**。

    ★ ★★ 为什么要单独做：★ Batch 866 记过的坑「**门禁自己也要经得起同样的检查**」
    ⟹ ⟹ ★ 本批的门禁断言的是「清单的覆盖面」⟹ ⟹
    ⟹ ⟹ 若它**恒绿** ⟹ ⟹ 它证明不了任何事 ⟹ ⟹ ⟹ ⟹ 必须**自己打自己**。
    """
    out: list[dict] = []
    orig = GATE_SELF_TARGET.read_bytes()
    text = orig.decode("utf-8")
    if text.count(GATE_SELF_ANCHOR) != 1:
        raise SystemExit("★ G1：清单锚点不唯一（%d 处）" % text.count(GATE_SELF_ANCHOR))

    cases = [
        ("G1: 门禁自身的负控 —— 把 761.py 从回归清单里删掉 ⟹ ⟹ 缺口必须被指出",
         False),
        ("G2: 门禁自身的负控 —— 删掉 761.py **并且**把同一条写进**注释**里 "
         "⟹ ⟹ 仍必须翻红（★ 验证 parse_gates 先剥注释）",
         True),
    ]
    try:
        for name, inject_comment in cases:
            mutated = text.replace(GATE_SELF_ANCHOR, "", 1)
            if inject_comment:
                # ★ 注入点必须落在 `GATES = [` 与收尾 `]` **之间** ⟹ ⟹
                # ⟹ ⟹ 否则旧版（不剥注释的）解析器**根本扫不到**它 ⟹ ⟹ ⟹ ⟹
                # ⟹ ⟹ ⟹ ⟹ 那这条负控就**测不出**要测的东西
                mutated = mutated.replace(
                    "    (\"760\", \"py\"),\n]",
                    "    (\"760\", \"py\"),\n" + GATE_SELF_COMMENT + "]",
                    1)
                if GATE_SELF_COMMENT not in mutated:
                    raise SystemExit("★ G2：注入点没命中（清单结构变了？）")
            GATE_SELF_TARGET.write_text(mutated, encoding="utf-8")
            rc, gout = run_gate("867")
            red = rc != 0
            gap_named = "761.py" in gout
            out.append({
                "name": name, "gate": "867", "applied": True,
                "rc": rc, "red": red, "expectLabelSeen": gap_named,
                "verdict": ("★ 门禁有牙（变异后翻红 ＋ 缺口精确指出 761.py）"
                            if red and gap_named
                            else "★ ★ 没翻红或缺口没指准 ⟹ ⟹ 门禁没牙"),
            })
            print("%s %-70s rc=%s %s" % ("★" if red else " ", name, rc,
                                        "翻红 ✔" if red else "★ 没翻红"))
    finally:
        GATE_SELF_TARGET.write_bytes(orig)
        after = GATE_SELF_TARGET.read_bytes()
        if after != orig:
            raise SystemExit("★ G1／G2 复原失败：回归清单脚本")
    out.append({"复原自检": "字节级干净（回归清单脚本）"})
    return out


def main() -> int:
    results = []
    for m in MUTATIONS:
        p = ROOT / m.relpath
        orig = p.read_bytes()
        text = orig.decode("utf-8")
        if m.old not in text:
            results.append({"name": m.name, "gate": m.gate, "applied": False,
                            "reason": "★ 锚点没命中（源码已变 ⟹ ⟹ 负控失效）",
                            "red": False})
            print("★ %s：锚点没命中" % m.name)
            continue
        if m.old2 is not None:
            # ★ ★★ 对调必须**按位置**做 ⟹ ⟹ 不能靠「第一处 / 第二处」
            #   ⟹ ⟹ ★ 第一版踩了这个坑：★ `old2` 与 `new` 是**同一串**
            #   ⟹ ⟹   ⟹ ⟹ 于是 `replace(old2, 占位符)` 吃掉了**刚改的那一处**
            #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ 变异**根本没生效** ⟹ ⟹ 门禁当然不红
            #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ★ 第二版又踩了：★ 在**替换之后**找 `m.old`
            #   ⟹ ⟹   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ 它已经被换掉了 ⟹ ⟹ `i1 = -1`
            #   ⟹ ⟹   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⇒ **位置必须在替换前就记下来**
            if text.count(m.old) != 1 or text.count(m.old2) != 1:
                raise SystemExit("★ %s：锚点不是唯一（old=%d old2=%d）"
                                 % (m.name, text.count(m.old), text.count(m.old2)))
            i1 = text.find(m.old)
            i2 = text.find(m.old2)
            lo, hi = min(i1, i2), max(i1, i2)
            # ★ ★★ 按**字符下标**精确替换 ⟹ ⟹ 不能用 `str.replace`
            #   ⟹ ⟹ ★ 因为 `old2` 与 `new` 是**同一串** ⟹ ⟹ 段内 replace 会**连锁**
            #   ⟹ ⟹   ⟹ ⟹ ⟹ ⟹ ⇒ 直接按切片拼 ⟹ ⟹ 最稳
            if i1 < i2:
                mutated = (text[:i1] + m.old2 + text[i1 + len(m.old):i2]
                           + m.new2 + text[i2 + len(m.old2):])
            else:
                mutated = (text[:i2] + m.new2 + text[i2 + len(m.old2):i1]
                           + m.old2 + text[i1 + len(m.old):])
        else:
            mutated = text.replace(m.old, m.new, 1)
        try:
            p.write_text(mutated, encoding="utf-8")
            rc, out = run_gate(m.gate)
            red = rc != 0
            hit = m.expect_label in out
            results.append({
                "name": m.name, "gate": m.gate, "applied": True,
                "rc": rc, "red": red, "expectLabelSeen": hit,
                "verdict": "★ 判据有牙（变异后翻红）" if red else "★ ★ 没翻红 ⟹ ⟹ 判据没牙",
            })
            print("%s %-58s rc=%s %s" % ("★" if red else " ", m.name, rc,
                                        "翻红 ✔" if red else "★ 没翻红"))
        finally:
            # ★ ★★ **无条件复原** ⟹ ⟹ 字节级
            p.write_bytes(orig)
            after = p.read_bytes()
            if after != orig:
                raise SystemExit("★ 复原失败：%s" % m.relpath)

    # ★ 复原自检：★ 全部源码必须字节级干净
    dirty = []
    for m in MUTATIONS:
        g = subprocess.run(["git", "diff", "--stat", "--", m.relpath],
                           capture_output=True, text=True, cwd=str(ROOT))
        if g.stdout.strip():
            dirty.append(m.relpath)
    # ★ ★★ 门禁自身的负控**也要复原**回归清单脚本 ⟹ ⟹
    # ⟹ ⟹ ★ 但它**不在 git 里**（本批新建 ⟹ ⟹ `git diff` 看不见）
    # ⟹ ⟹ ⟹ ⟹ ⇒ 必须**另外**做一次字节级比对 ⟹ ⟹ 否则等于没复原
    gs = subprocess.run(["git", "status", "--porcelain", "--", str(GATE_SELF_TARGET)],
                        capture_output=True, text=True, cwd=str(ROOT))
    if gs.stdout.strip() and not gs.stdout.strip().startswith("?? "):
        dirty.append("回归清单脚本（非新增状态却仍有改动）")
    results.append({"复原自检": "字节级干净" if not dirty else dirty})

    # ★ ★★ 门禁自身的负控（G1／G2）⟹ ⟹ **门禁自己也要有牙**
    results.extend(neg_gate_itself())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    nred = sum(1 for r in results if r.get("red"))
    ntot = sum(1 for r in results if "applied" in r)
    print("\n★ 负控 %d 条，打红 %d 条" % (ntot, nred))
    print("★ 复原自检：%s" % [r["复原自检"] for r in results if "复原自检" in r])
    print("★ 读数已落盘：%s" % OUT)
    return 0 if nred == ntot and not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
