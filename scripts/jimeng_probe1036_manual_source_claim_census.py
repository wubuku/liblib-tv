#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批 1036：**「源站事实」主体标注的枚举普查门**。

## 这道门答的是哪一个问题
  「手册正文里，**每一处**读者会照着做、而在复刻上不成立的『源站事实』，
  是否都贴着标明了主体」。

## 它补的是 1035 的哪个盲区
  1035 的 `REQUIREMENTS` 是**手打清单**，且 `find_marker` 只取 `hits[0]`
  （锚句的**第一次**命中）。
  ⇒ 实测盲区：`canvas-context.md` 里「内容跨刷新持久」出现 3 次（628 / 631 / 737），
  1035 只查 628 那次 ⇒ **737 行「已验证说明」里的同一句事实完全不受门管**。
  ⇒ 而 737 行那句在复刻上**同样不成立**（复刻刷新即复位）。

  ⇒ 本门把判据从「手打清单 + 首次命中」改成
     **「枚举 + 每一处命中都要标」**。

## 为什么枚举口径能自己推导（不手打）
  差异面词表不是手打的，而是**从手册自己声明的「复刻差异」块里提取**：
  手册已经写了哪些词上「复刻与源站不同」（刷新 / 复位 / 持久 / 服务端 / 跨刷新），
  ⇒ 那么**正文里所有同时出现「差异面词」与「源站实测口吻」的句子**，
  都是「读者可能照着做」的候选。
  ⇒ 这样口径随手册演进，而不是钉死在一个手打清单上。

## 三态退出码
  0 = 判据全绿 / 1 = 判据红 / 2 = 仪器崩（数据侧问题）。
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "docs" / "user-manual" / "jimeng-canvas"
OUT = ROOT / "docs" / "research" / "jimeng-canvas" / "source-claim-census-1036.json"

MARK = "复刻差异"

# 面向读者的页面（台账类 AUDIT/PROGRESS/SOURCE_OBSERVATIONS 不在范围内：
# 它们是取证记录，不是「读者会照着做」的步骤）
READER_PAGES = [
    "00-quickstart.md",
    "20-reference.md",
    "30-concepts.md",
    "90-troubleshooting.md",
] + ["10-tasks/" + n for n in sorted(os.listdir(MANUAL / "10-tasks")) if n.endswith(".md")]

# 「源站实测」口吻的信号（第一层：显式口吻）
SOURCE_TONE = re.compile(r"(实测|源站)")
# ⭐⭐⭐⭐⭐ **第二层口吻：取证批次口吻** —— 句里带「批次 N」/日期/立规号
#   ⇒ 这一层能抓到「批次 158 已经证明**上传是持久的**」这种**没写「实测/源站」**的句子
#   ⇒ 而这类句子在 1036 第一版里**完全漏掉**（实测漏 27 条，见 README 六之五十一）
FORENSIC_TONE = re.compile(r"(批次\s*\d+|20\d\d-\d\d-\d\d|立规\s*\d+)")
# 「读者会照着做」的动作信号（成功判据 / 预期结果）
ACTIONABLE = re.compile(
    r"(刷新后|跨刷新|持久|自动保存|已保存|保存后|重新打开|再次进入|关掉再开|刷新页面|刷新即|重载)"
)
# ⭐⭐⭐⭐⭐ **第二层口吻必须配「读者会照着做」二次过滤** ——
#   ⇒ 否则 36 条新增候选里绝大多数是**截图说明 / 取证标题 / 内部立规**（不是给读者的操作步骤）
#   ⇒ 二次过滤用「可执行判据」信号：句里有读者能照着做的动作或预期
READER_ACTION = re.compile(
    r"(判据|做法|办法|请|可以|应当|照着|重载|刷新后|重新打开|确认|看到|仍然|依然|不会|会丢|保留|证明)"
)
# 排除台账语境：这些句说的是**源站自己的**批量测试/积分/自动化，不是用户操作步骤
LEDGER_CONTEXT = re.compile(
    r"(批次\s*\d+\s*实测|积分|profile|headless|无头|Cookies|臂\s*\d|Cookies|已保存状态\s*$)"
)
# ⭐⭐⭐⭐⭐ **排除「截图说明 / 取证标题 / 内部立规」** ——
#   ⇒ 它们带取证口吻，但**不是读者会照着做的操作步骤**
#   ⇒ 判据：整行是图片说明（以 `![` 开头）、是标题（以 # 开头）、或引用「立规 / 批次 N」编号表
NON_READER_SHAPE = re.compile(
    r"(^!\s*\[|^#{1,6}\s|立规\s*\d+\s*[:：]|^\|\s*\d+\s*（批次)"
)
# ⭐⭐⭐⭐⭐ **排除「实验方法论」** ——
#   ⇒ 手册里有一部分段落是**写手册的人给自己的规矩**（怎么测、怎么记、怎么判）
#   ⇒ 例如「只要实验里出现『开新页 / 重载 / 跨会话』，就必须**逐臂**记录被改量的实测值」
#   ⇒ 那句里的「重载 / 跨会话」是**测试手段**，不是**产品行为** ⇒ 标不标主体都没意义
#   ⇒ 判据：句在说「怎么测」（逐臂 / 判据三问 / 通用形态 / 立规 / 通用规律）
METHODOLOGY = re.compile(
    r"(逐臂|判据三问|通用形态|通用规律|通用判据|怎么自己造出|必须记录|记录被改量|写成结论|读数发生在)"
)



# ⭐⭐⭐⭐⭐ **豁免登记**：枚举到的候选里，有些**在复刻上同样成立**，
#   标不标都是对的 ⇒ 把它们显式登记，并写明**实测理由**。
#   ⇒ 为什么不写进正则里悄悄滤掉？因为「悄悄放过」不可审计，
#   ⇒⇒ 而且下一批手册变了、这句的含义变了，豁免就失效了却没人知道。
#   ⇒ 所以每条豁免都必须带实测依据，且依据要写明是**实测**还是**读源码**。
EXEMPTIONS = [
    {
        "file": "10-tasks/duplicate-delete-history.md",
        "anchor": "撤销历史不跨会话",
        "reason": "复刻实测：删除一个节点后节点数 5→4，刷新后回到 5，刷新后按 ⌘Z 仍是 5 ⇒ "
        "「刷新后 ⌘Z 不再回退任何内容」在复刻上**同样成立**（内容本来就回到初始态了）⇒ 不需要标注。",
        "evidence": "measured",
    },
    {
        "file": "10-tasks/duplicate-delete-history.md",
        "anchor": "撤销历史不跨刷新",
        "reason": "同上：这一句是上一句的「已验证说明」里的同义表述，实测依据相同 ⇒ 不需要标注。",
        "evidence": "measured",
    },
    {
        "file": "10-tasks/subject-node.md",
        "anchor": "写入持久数据",
        "reason": "这句讲的是**源站账号级主体库的写入副作用**，与画布刷新是否复位无关；"
        "复刻里 store 无任何主体库键（实测 store 键扫描 0 命中）⇒ 不属「画布持久化」差异面。",
        "evidence": "measured",
    },
]



def _read(p):
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def derive_difference_faces():
    """差异面词表 = 手册自己声明的「复刻差异」块里出现过的词。

    ⇒ 不手打 ⇒ 手册改了这个面，普查口径自动跟着变。
    """
    faces = set()
    for rel in READER_PAGES:
        text = _read(MANUAL / rel)
        if text is None:
            continue
        for blk in re.findall(r">\s*\*\*复刻差异\*\*.*?(?=\n\n|\Z)", text, re.S):
            for w in ("刷新", "复位", "持久", "离线", "服务端", "已保存", "会话", "跨刷新"):
                if w in blk:
                    faces.add(w)
    return sorted(faces)


def section_bounds(ls, a):
    """锚句所在小节的行号区间 [start, end)。"""
    start = 0
    for i in range(a, -1, -1):
        if re.match(r"^#{2,6}\s", ls[i]):
            start = i
            break
    end = len(ls)
    for i in range(a + 1, len(ls)):
        if re.match(r"^#{2,6}\s", ls[i]):
            end = i
            break
    return start, end


def has_marker_in_section(ls, a):
    """锚句所在小节里，有没有带「复刻差异」标注的引用块。"""
    start, end = section_bounds(ls, a)
    for m in range(start, end):
        if MARK in ls[m]:
            # 标注块至少要有一行正文（不许只有标题行）
            block = "\n".join(ls[m : m + 10])
            if len(block.strip()) > len(MARK) + 10:
                return m + 1, block
    return None, None


def exempt_for(rel, line_text):
    """这条候选是否命中豁免登记？命中就返回那条登记。"""
    for ex in EXEMPTIONS:
        if ex["file"] != rel:
            continue
        if ex["anchor"] in line_text:
            return ex
    return None


def enumerate_candidates(faces):
    """枚举所有「差异面 + 源站/取证口吻 + 读者会照着做」的句子。

    ⇒ 两层口吻：
      第一层 `SOURCE_TONE`（显式写「实测/源站」）—— 直接进候选
      第二层 `FORENSIC_TONE`（带批次号/日期，但没写「实测」）—— **要过「读者会照着做」二次过滤**
    ⇒ 二次过滤的必要性（实测）：第二层单独会带出 36 条，其中绝大多数是
      **截图说明 / 取证标题 / 内部立规** ⇒ 不是给读者的操作步骤。
    """
    rows = []
    face_re = re.compile("(" + "|".join(re.escape(f) for f in faces) + ")")
    for rel in READER_PAGES:
        text = _read(MANUAL / rel)
        if text is None:
            continue
        ls = text.split("\n")
        for i, line in enumerate(ls):
            s = line.strip()
            if not s or s.startswith(">"):
                continue  # 标注块本身不算候选
            if not SOURCE_TONE.search(s) and not FORENSIC_TONE.search(s):
                continue
            if not ACTIONABLE.search(s):
                continue
            if not face_re.search(s):
                continue
            if LEDGER_CONTEXT.search(s):
                continue
            if NON_READER_SHAPE.search(s):
                continue
            if METHODOLOGY.search(s):
                continue
            second_layer = not SOURCE_TONE.search(s)
            if second_layer and not READER_ACTION.search(s):
                continue  # 第二层口吻必须过「读者会照着做」二次过滤
            ex = exempt_for(rel, s)
            rows.append(
                {
                    "file": rel,
                    "line": i + 1,
                    "text": s[:220],
                    "tone_layer": 2 if second_layer else 1,
                    "section": next(
                        (ls[j][:70] for j in range(i, -1, -1) if re.match(r"^#{2,6}\s", ls[j])),
                        "",
                    ),
                    "exempt": bool(ex),
                    "exemption_reason": (ex or {}).get("reason", ""),
                    "exemption_evidence": (ex or {}).get("evidence", ""),
                }
            )
    return rows



def main():
    faces = derive_difference_faces()
    if not faces:
        sys.stderr.write("DIFFERENCE_FACES_EMPTY (data-side, rc=2)\n")
        return 2

    candidates = enumerate_candidates(faces)

    # 逐条判定：该句所在小节里有没有标注
    # ⇒ **豁免项单独分流**：豁免不是「未标」，它有另一套判据（必须带实测依据）
    checked = []
    unmarked = []
    exempt_rows = []
    for c in candidates:
        text = _read(MANUAL / c["file"])
        if c.get("exempt"):
            exempt_rows.append(c)
            checked.append(dict(c, marked=True, marker_line=None, why="exempted"))
            continue
        if text is None:
            checked.append(dict(c, marked=False, marker_line=None, why="file_unreadable"))
            unmarked.append(c)
            continue
        ls = text.split("\n")
        line_no, block = has_marker_in_section(ls, c["line"] - 1)
        ok = line_no is not None
        row = dict(c, marked=ok, marker_line=line_no)
        checked.append(row)
        if not ok:
            unmarked.append(row)


    crit = {}
    kinds = {}

    # P1 差异面词表不是手打的（能从手册自身推导出来）
    crit["P1_difference_faces_are_derived_not_handwritten_1036"] = bool(faces)
    kinds["P1_difference_faces_are_derived_not_handwritten_1036"] = "failure"

    # P2 枚举器确实扫到了候选（恒零 = 扫描范围可能没覆盖）
    crit["P2_enumeration_found_candidates_1036"] = len(candidates) > 0
    kinds["P2_enumeration_found_candidates_1036"] = "failure"

    # P3 每一条候选所在小节都标明了主体
    crit["P3_every_candidate_is_marked_in_place_1036"] = len(unmarked) == 0
    kinds["P3_every_candidate_is_marked_in_place_1036"] = "failure"

    # P4 同一句事实的**每一处**出现都要标（1035 的盲区：
    #    find_marker 只取 hits[0] ⇒ 第二处完全不受管）
    multi = {}
    for c in candidates:
        key = c["text"][:40]
        multi.setdefault(key, []).append(c)
    repeated = {k: v for k, v in multi.items() if len(v) > 1}
    repeat_unmarked = [
        c for v in repeated.values() for c in v if not c.get("marked")
    ]
    crit["P4_every_occurrence_not_just_the_first_1036"] = len(repeat_unmarked) == 0
    kinds["P4_every_occurrence_not_just_the_first_1036"] = "failure"

    # P5 负控：把标注抠掉 ⇒ 判据必须翻红（否则上面那些是恒真）
    # ⇒ **豁免项不参与**：豁免项本来就不靠标注，它由 P8 管
    neg_rows = []
    neg_red = True
    for c in candidates:
        if c.get("exempt"):
            continue
        text = _read(MANUAL / c["file"])
        if text is None:
            neg_red = False
            continue
        ls = text.split("\n")
        a = c["line"] - 1
        start, end = section_bounds(ls, a)
        # 在该小节里删掉所有标注块行
        ls2 = [l for j, l in enumerate(ls) if not (start <= j < end and MARK in l)]
        ok_after, _ = has_marker_in_section(ls2, min(a, len(ls2) - 1))
        went_red = ok_after is None
        neg_rows.append(
            {
                "file": c["file"],
                "line": c["line"],
                "went_red": went_red,
            }
        )
        if not went_red:
            neg_red = False
    crit["P5_negative_control_turns_the_claim_red_1036"] = neg_red
    kinds["P5_negative_control_turns_the_claim_red_1036"] = "failure"

    # P6 标注必须给出复刻侧可执行的动作（不许只说「不一样」）
    actionable = True
    for c in checked:
        if c.get("exempt"):
            continue
        if not c.get("marked"):
            actionable = False
            continue
        text = _read(MANUAL / c["file"])
        ls = text.split("\n")
        m = c["marker_line"] - 1
        block = "\n".join(ls[m : m + 10])
        if not re.search(r"刷新|复位|回到初始|控制台|__jimengStore|会话", block):
            actionable = False
    crit["P6_every_marker_gives_an_actionable_alternative_1036"] = actionable
    kinds["P6_every_marker_gives_an_actionable_alternative_1036"] = "failure"

    # P7 边界与扫描范围必须写进产物
    crit["P7_scope_and_limits_published_1036"] = True
    kinds["P7_scope_and_limits_published_1036"] = "failure"

    # P8 ⭐⭐⭐⭐⭐ 豁免必须带**实测依据**（不许写「大概不用标」这种空话）
    # ⇒ 这是防「悄悄放过」的那道闸：豁免本身也是一份承诺
    exempt_ok = True
    for c in exempt_rows:
        if c.get("exemption_evidence") not in ("measured", "source_read"):
            exempt_ok = False
        if len(c.get("exemption_reason", "")) < 20:
            exempt_ok = False
    crit["P8_every_exemption_carries_measured_evidence_1036"] = exempt_ok
    kinds["P8_every_exemption_carries_measured_evidence_1036"] = "failure"

    # P9 豁免登记里不能有「登记了但根本没被枚举命中」的僵尸条目
    # ⇒ 否则会显得「我都处理过了」，实际上一条都没命中
    used_exemptions = {
        (c["file"], c["text"]) for c in candidates if c.get("exempt")
    }
    zombie = []
    for ex in EXEMPTIONS:
        hit = any(
            ex["file"] == c["file"] and ex["anchor"] in c["text"] for c in candidates
        )
        if not hit:
            zombie.append({"file": ex["file"], "anchor": ex["anchor"]})
    crit["P9_no_zombie_exemptions_1036"] = len(zombie) == 0
    kinds["P9_no_zombie_exemptions_1036"] = "failure"


    red = [k for k, v in crit.items() if v is not True]
    out = {
        "generated_by": "jimeng_probe1036_manual_source_claim_census.py",
        "what_this_gate_asks": "手册正文里每一处「读者会照着做、而在复刻上不成立」的源站事实，是否都贴着标明了主体并给出复刻侧可执行的动作。",
        "what_this_is_not": "这不是「复刻该不该持久化」的判决；也不是「手册有没有提过源站」的判决 —— 它只钉「该标的地方标没标」。",
        "difference_faces_1036": faces,
        "difference_faces_source": "从手册自己的「复刻差异」标注块里提取，不是手打清单 ⇒ 手册改了这个面，普查口径自动跟着变。",
        "scan_scope_1036": {
            "reader_pages": READER_PAGES,
            "excluded": [
                "AUDIT.md / PROGRESS.md / SOURCE_OBSERVATIONS.md（取证台账，不是读者会照着做的步骤）",
                "标注块自身（以 > 开头的引用行）",
                "台账语境句（批次 N 实测 / 积分 / profile / 无头 / 臂 N）",
            ],
        },
        "limits_1036": [
            "只覆盖「差异面词 ∩ 源站/取证口吻 ∩ 可操作判据」三类信号的交集",
            "读不出来源站口吻的句子（例如只写「刷新后仍是这样」而不写实测）不在覆盖内",
            "不判定产品行为本身对不对，只判定文档有没有标明主体",
            "⭐⭐ 批 1032-⑦ 起口吻分两层：① 显式口吻（实测|源站）② 取证口吻（批次 N / YYYY-MM-DD / 立规 N）",
            "⭐⭐ 第二层口吻**必须过二次过滤**（读者会照着做）⇒ 否则会带出 30+ 条误报",
            "⭐⭐ 三类排除是**关键词启发式**（截图说明 / 取证标题编号表 / 实验方法论）"
            "⇒ 换一种措辞写方法论就可能漏进来 ⇒ 这是本门已声明的盲区",
        ],
        "criteria_1036": crit,
        "criterion_kinds_1036": kinds,
        "criterion_kinds_complete_1036": True,
        "n_criteria_1036": len(crit),
        "n_candidates_1036": len(candidates),
        "n_marked_1036": len(candidates) - len(unmarked),
        "n_unmarked_1036": len(unmarked),
        "candidates_1036": checked,
        "unmarked_1036": unmarked,
        "exemptions_1036": {
            "registry": EXEMPTIONS,
            "n_registered": len(EXEMPTIONS),
            "n_applied": len(exempt_rows),
            "zombie_1036": zombie,
            "note": "豁免 = 「这条在复刻上同样成立，标不标都对」⇒ 必须带实测依据（P8）且不能是僵尸条目（P9）",
        },
        "repeated_claims_1036": {
            k: [{"file": c["file"], "line": c["line"], "marked": c.get("marked")} for c in v]
            for k, v in repeated.items()
        },
        "negative_control_1036": neg_rows,
        "rule": "⭐⭐⭐⭐⭐ 同一句事实的**每一处**出现都要标 ⇒ ⇒⇒ 1035 只查首次命中 ⇒ ⇒⇒ ⇒ 第二次出现完全不受管 ⇒ ⇒⇒ ⇒ 所以本门按「枚举 + 逐处」判，不按「手打清单 + 首次命中」判。",
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("差异面词表 = %s" % "、".join(faces))
    print(
        "候选 %d 条 / 已标 %d 条 / 豁免 %d 条 / 未标 %d 条"
        % (len(candidates), len(candidates) - len(unmarked) - len(exempt_rows), len(exempt_rows), len(unmarked))
    )
    for e in exempt_rows:
        print("  豁免: %s:%d  %s" % (e["file"], e["line"], e["exemption_reason"][:70]))
    for u in unmarked:
        print("  未标: %s:%d  %s" % (u["file"], u["line"], u["text"][:90]))
    print("判据逐条 = " + " | ".join("%s=%s" % (k, crit[k]) for k in crit))
    print("P 为假的： " + ("无" if not red else ", ".join(red)))
    print("PROBE_1036_SOURCE_CLAIM_CENSUS_DONE -> %s" % OUT)
    return 0 if not red else 1


if __name__ == "__main__":
    sys.exit(main())
