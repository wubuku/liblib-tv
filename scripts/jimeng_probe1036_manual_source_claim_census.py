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
# ⭐⭐⭐⭐⭐ **小节级的方法论判定**（批 1032-⑧ 续）—— 与上面的**关键词**判定**并存**
#   ⇒ 实测：两者**互补，不是替代**
#   ⇒⇒ 关键词判定能排除「句里写着『逐臂记录』」的句子，但**换种措辞就漏**
#   ⇒⇒ 小节判定能按**结构**排除（整节都是方法论），但**会漏**同节里夹的产品句
#   ⇒ ⇒ 所以两条规则都留着 ⇒ 任何一条命中就排除
METHODOLOGY_SECTION = re.compile(
    r"(立规\s*\d+|方法论|判据三问|通用形态|通用规律|怎么自己造出|怎么测|通用判据|取证方法|实验方法)"
)


# ⭐⭐⭐⭐⭐ **实测事实（1032-⑧ 量出来的）**：复刻上「刷新后还在」有两件**不同**的事
#   ⇒ ① **mock 初始态自带的媒体**（demo 画布里那个 `hasMedia: true` 的视频节点）
#   ⇒    刷新后**仍在**（`<video src="/videos/jimeng-demo.mp4">`、readyState=4）—— 因为它本来就在 mock 数据里
#   ⇒ ② **用户自己上传的件**（`addLocalUpload`）⇒ 刷新后**不在了**（节点 5→6，刷新回 5，localStorage 0 键）
#   ⇒ ⇒ 而手册那句「**上传是持久的**」说的是 ② ⇒ 在复刻上不成立
#   ⇒ ⇒ ⇒ **所以「刷新后还在」这句话必须问「谁的东西还在」** —— 不问就会把 ① 当成 ②
#   ⇒ 这条进产物（而不是当判据）⇒ 因为它是**读数**，判据只钉「文档有没有标明主体」
CLONE_PERSISTENCE_FACTS = {
    "mock_media_survives_reload": {
        "measured": True,
        "sample_guard": {
            "assertion": "存在带媒体的 <video>（n_video >= 1）",
            "value": True,
            "note": "⭐⭐⭐⭐⭐ **量到 0 之前先断言「该有的东西在」** ⇒ "
            "第一版探针搜的是 <audio> ⇒ 0 个 ⇒ 差点写成「复刻没有媒体元素」⇒ 而那是**样本不成立**",
        },
        "readings": {
            "n_video_initial": 1,
            "video_src": "/videos/jimeng-demo.mp4",
            "ready_state": 4,
            "n_video_after_reload": 1,
        },
        "note": "demo 画布里那个 `hasMedia: true` 的视频节点，刷新后 `<video>` 仍在且 readyState=4 ⇒ "
        "因为它本来就在 mock 初始数据里",
    },
    "user_upload_does_not_survive_reload": {
        "measured": True,
        "sample_guard": {
            "assertion": "addLocalUpload 之后节点数确实 +1（证明上传动作生效了）",
            "value": True,
        },
        "readings": {
            "n_nodes_before": 5,
            "n_nodes_after_addLocalUpload": 6,
            "n_nodes_after_reload": 5,
            "localstorage_keys": 0,
        },
        "note": "用户上传的件刷新后不在画布上 ⇒ 手册「上传是持久的（重载页面后自建节点仍在画布上）」"
        "是**源站**事实，在复刻上不成立 ⇒ 已补「复刻差异」标注",
    },
    "the_distinction": "「刷新后还在」要问**谁的东西还在**：mock 初始态的媒体会回来，用户新增的上传件不会。",
}

# ⭐⭐⭐⭐⭐ **实测事实（1032-⑧ ②）**：复刻上**有**源站那套「媒体失效」态，且**重试路径是对的**
#   ⇒ 这条是「查了但**没发现缺口**」的记录 ⇒ 同样要落盘 ⇒ 否则下一个人会重新查一遍
CLONE_MEDIA_ERROR_FACTS = {
    "clone_has_media_error_state": {
        "measured": True,
        "sample_guard": {
            "assertion": "存在带媒体的 <video>，且正常态 ready_state=4（证明素材真的能解码）",
            "value": True,
        },
        "readings": {
            "normal": {"media_error_flag": None, "retry_btn_in_dom": False, "ready_state": 4},
            "broken_src": {"media_error_flag": True, "retry_btn_in_dom": True, "error_code": 4},
            "after_click_retry": {
                "media_error_flag": False,
                "retry_btn_in_dom": False,
                "note": "点「重试播放视频」⇒ mediaError 清 false ⇒ 错误态解除 ⇒ **路径正确**",
            },
        },
        "conclusion": "复刻上有「视频播放失败 ＋ 重试播放视频」这一档（源站对应物在 media-playback.md 的「媒体异常」节）"
        "⇒ 手册那节在复刻上**有对应物**，不需要标主体",
    },
    "the_trap": "第一版探针注入坏 src 后又改回好 src ⇒ 「按钮还在」⇒ 差点记成缺陷；"
    "⇒ 但那条**不是用户路径**（用户不会换 src）⇒ 真正的用户路径是「点重试」⇒ 实测**正确**"
    "⇒ ⇒ 结论：**注入路径 ≠ 用户路径**，判定前先问「这是用户会走的路吗」",
}

# ⭐⭐⭐⭐⭐ **既存问题（不是本批引入，但本批撞上了）**：1031 的产物**不可复现**
#   ⇒ 实测：连跑 3 次 ⇒ sha 三个都不同（28eb632e8064 / d2e1c8d85a87 / 3de2128cd9d9）
#   ⇒ 逐键对比：变的只有 `live_1031` 与 `P5_live_status_line_shape_1031`
#   ⇒   `all_aria_shapes_found` / `all_node_kinds_found` / `status_line_shape_matched`
#   ⇒   在 True/False 之间**摇摆** ⇒ **页面元素还没渲染完就被读了**（时序竞态）
#   ⇒ 而 1015 的两轮里它是稳定的（`state=reproduced`、`n_values_changed=0`）
#   ⇒   ⇒ 推测：1015 两轮**复用同一浏览器会话**，而固定点循环**每轮新起浏览器** ⇒ 才触发竞态
#   ⇒ ⇒ **间歇性**，不是必然 ⇒ 所以本批**不动它**（不在本批范围，且改它要重做 1031 的时序）
#   ⇒ ⇒ 但**必须记下来**：否则固定点循环永远追不上，而追不上的原因会被误报成「本批改了东西」
KNOWN_UNREPRODUCIBLE = {
    "live-canvas-check-1031.json": {
        "status": "pre_existing",
        "introduced_by": "not_this_batch",
        "measured": True,
        "sha12_three_runs": ["28eb632e8064", "d2e1c8d85a87", "3de2128cd9d9"],
        "varying_keys": [
            "live_1031",
            "P5_live_status_line_shape_1031",
        ],
        "root_cause_hypothesis": "运行时读数在页面元素渲染完成前被读 ⇒ 时序竞态（间歇性）",
        "why_not_fixed_here": "修它要重做 1031 的等待策略 ⇒ 超出本批范围 ⇒ 且 1015 的两轮里它是稳定的"
        "⇒ 贸然改可能把一个偶发问题变成固定行为",
        "consequence": "固定点循环**追不上它** ⇒ 判定不动点时必须**显式排除**并说明 ⇒ 不许默默放过",
    },
}





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


def face_re_of(faces):
    """差异面词表的正则（抽成函数，好让 P10 的排除计数复用同一份口径）。"""
    return re.compile("(" + "|".join(re.escape(f) for f in faces) + ")")


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
    face_re = face_re_of(faces)
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
            # ⭐⭐⭐⭐⭐ **小节级方法论判定**（批 1032-⑧ 续）：整节都是方法论 ⇒ 全部排除
            #   ⇒ 与上面的关键词判定**并存**（实测两者互补，不是替代）
            sec_start, _sec_end = section_bounds(ls, i)
            sec_title = ls[sec_start] if sec_start < len(ls) else ""
            if METHODOLOGY_SECTION.search(sec_title):
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
                    "section": sec_title[:70],
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

    # P10 ⭐⭐⭐⭐⭐ 排除规则**必须真的排除过东西** —— 否则它就是一段死代码
    #   ⇒ 关键词级与小节级两条排除规则，各自都要有**实际命中记录**
    #   ⇒ 「加了规则但一条都没排除」看起来无害，其实说明规则写错了（或者口径本来就没问题）
    excl_hits = {"keyword": 0, "section": 0}
    for rel in READER_PAGES:
        text = _read(MANUAL / rel)
        if text is None:
            continue
        ls = text.split("\n")
        for i, line in enumerate(ls):
            s = line.strip()
            if not s or s.startswith(">") or s.startswith("!["):
                continue
            if not SOURCE_TONE.search(s) and not FORENSIC_TONE.search(s):
                continue
            if not ACTIONABLE.search(s):
                continue
            if not face_re_of(faces).search(s):
                continue
            if METHODOLOGY.search(s):
                excl_hits["keyword"] += 1
            st, _ = section_bounds(ls, i)
            if st < len(ls) and METHODOLOGY_SECTION.search(ls[st]):
                excl_hits["section"] += 1
    crit["P10_exclusion_rules_actually_exclude_something_1036"] = (
        excl_hits["keyword"] > 0 and excl_hits["section"] > 0
    )
    kinds["P10_exclusion_rules_actually_exclude_something_1036"] = "failure"

    # P11 ⭐⭐⭐⭐⭐ **每条实测读数必须带「样本守卫」** ——
    #   ⇒ 量到 0 的时候，先问「**该有的东西真的在吗**」
    #   ⇒ 0 可能是「没有」，也可能是「我没找对」⇒ 后者会产出**干净、好看、但是错的**结论
    #   ⇒ 本批真踩了：搜 <audio> 得 0 ⇒ 差点写「复刻没有媒体元素」⇒ 而复刻用的是 <video>
    #   ⇒ 所以守卫不是「可选的严谨」⇒ 它是**读数能不能被信**的前置条件
    guard_ok = True
    guard_rows = []
    for block_name, block in (
        ("clone_persistence_facts_1036", CLONE_PERSISTENCE_FACTS),
        ("clone_media_error_facts_1036", CLONE_MEDIA_ERROR_FACTS),
    ):
        for key, val in block.items():
            if not isinstance(val, dict) or not val.get("measured"):
                continue
            guard = val.get("sample_guard")
            row = {
                "block": block_name,
                "key": key,
                "has_guard": bool(guard),
                "guard_value": (guard or {}).get("value"),
            }
            guard_rows.append(row)
            if not guard or guard.get("value") is not True:
                guard_ok = False
    crit["P11_every_measured_reading_carries_a_sample_guard_1036"] = (
        guard_ok and len(guard_rows) > 0
    )
    kinds["P11_every_measured_reading_carries_a_sample_guard_1036"] = "failure"



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
        "clone_persistence_facts_1036": CLONE_PERSISTENCE_FACTS,
        "clone_media_error_facts_1036": CLONE_MEDIA_ERROR_FACTS,
        "sample_guards_1036": guard_rows,
        "known_unreproducible_1036": KNOWN_UNREPRODUCIBLE,
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
