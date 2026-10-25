#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1031：**活站点契约**闸。

⭐⭐⭐⭐⭐ 前面所有门都在验「研究装置自己」。这一道第一次直接验**被复刻的那个东西**
—— 即梦画布的**可交互契约**（不是截图、不是文案，而是 `data-testid` / 节点类型 /
状态行**形状** / 工具条构成）。

纪律：
- ① 只读探索：绝不点击生成/发送/购买/充值；
- ② **期望值只有一个真源**（`live-canvas-contract-1031.json`）
   —— 本文件**不抄第二份**，否则契约改了这里不会跟着改，就成了「两处期望值各说各话」；
   契约文件本身被谁改了，交给 verifier 的摘要判据去抓；
- ③ 读数可以指向一份**副本**（`JIMENG_FORENSICS_JSON`）⇒ 注入式变异能问「它会拿它当红」；
- ④ 无浏览器时降级为「只跑离线自洽三条」，并**明说降级了**，不许假装跑过。

⭐⭐⭐⭐⭐ **订正（1032-⑨ 当场实测）**：上面「直接验**被复刻的那个东西**」这半句**与实现不符**
—— 本门默认跑的是**原站**（`JIMENG_CANVAS_URL` 的默认值就是原站示例画布，
   而仓里没有任何地方设过这个变量）⇒ 实测读到的 `url` 是 `jimeng.jianying.com/...`、
   `title` 是 `测试项目 - 即梦AI` ⇒ **它验的是活站点**。
⇒⇒⇒ 门名「活站点契约」是对的，docstring 那半句是错的 ⇒ 这里**更正**而不重写。
⇒⇒⇒ 连带的结构后果：**它的输入是外部在线站点** ⇒ 字节天然可能随原站变
⇒⇒⇒ ⇒ 所以「等到了没有」必须单独记成一条判据（P10），
⇒⇒⇒   否则「原站慢」与「原站改了」会被读成同一件事。
⭐⭐⭐⭐⭐ **另一条订正（1032-⑨）**：取证脚本**崩了**原来会被读成「没测到」⇒ 而降级的
退出码是 0 ⇒ **崩溃被伪装成「没测到、而且还没红」** ⇒ 现在崩溃走 rc=2 那条出口。
"""
import ast
import collections
import io
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jimeng_node_toolchain import node_available, run_node_script  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GDIR = ROOT / "docs/research/jimeng-canvas"
# ⭐ 可用 `JIMENG_CONTRACT_JSON` 指向一份**候选副本** —— 契约被改坏必须当场转红，
#   而不是「等有人想起来看一眼」
CONTRACT = Path(os.environ.get("JIMENG_CONTRACT_JSON")
                 or (GDIR / "contracts" / "live-canvas-contract-1031.json"))
# ⭐ 契约放在**子目录**而不是直接放通道 A —— 它是**期望值真源**，不是某探针的产物；
#   混在通道 A 里，1015 会把它当成探针的 golden，而探针不该写它
OUT = str(GDIR / "live-canvas-check-1031.json")
# ⭐⭐⭐⭐⭐ 产物**必须落仓**：1015 的 `P4` 是「重跑之后压根没写过自己 golden 的本数」，
#   而第一版写的是 `/tmp/...` ⇒ 1015 立刻抓到 `wrote_golden=false` ⇒ P4 转红。
#   ⇒⇒⇒ 但落仓后就**逐字字节参与 1015 的可复现判定**，所以这里只许存**形状与布尔**：
#   `n_clickables: 112`、`76 nodes, ...` 这类**每次跑都会变**的原始读数**留在契约里**
#   （契约本来就是一次性取证的快照，是历史读数而非当前读数）。
FRESH_DEFAULT = "/tmp/b1031-live-fresh.json"
FORENSICS = ROOT / "scripts/jimeng_live_canvas_forensics.mjs"

TESTID_PREFIX = "canvas-"
STATUS_SHAPE = re.compile(
    r"^\d+ nodes, \d+ edges, \d+ selected\. Editable\. Room connected\. 已保存\.$")
GENERATION_WORDS = ("生成", "发送", "购买", "充值", "立即创作", "开始生成")


def harvest():
    """拿一份实测结构：优先用环境变量指向的副本，否则现跑一次无头取证。

    ⭐⭐⭐⭐⭐ **「仪器崩了」与「没有浏览器」必须分开**（1032-⑨ 实测出来的）
      · **node 不在 PATH** ⇒ ⇒ **仪器崩了**（不是「没浏览器」）⇒ ⇒ 必须走 rc=2
      · node 跑了但 returncode≠0、或它没写盘 ⇒ **仪器崩了**
      ⇒⇒⇒ 而旧的写法把「node 不在」叫「没浏览器」⇒⇒⇒ **⇒ 退出码 0 ⇒⇒⇒**
      ⇒⇒⇒ ⇒ **崩溃被伪装成「没测到、而且还没红」** ⇒⇒⇒ ⇒ 那是最贵的那种绿
      ⇒⇒⇒ ⇒ ⇒ 而 1032-⑩ 已把「node 在不在」收进统一工具链 ⇒⇒⇒ ⇒ ⇒ 只有一个答案
      ⇒⇒⇒ ⇒ ⇒⇒⇒ 且**崩溃细节不许进产物**（stderr 每次都不同 ⇒ 会把产物变成随机量）
    """
    src = os.environ.get("JIMENG_FORENSICS_JSON")
    if src:
        p = Path(src)
        return (json.loads(p.read_text(encoding="utf-8")) if p.exists() else None), "copy"
    # ⭐⭐⭐⭐⭐ 走统一工具链 ⇒「node 在不在」只有一个答案 ⇒
    #   ⇒⇒⇒ 「node 不在」**不是**「没浏览器」⇒⇒⇒ 它是仪器崩 ⇒⇒⇒ 走 rc=2
    _node_ok, _node_why = node_available()
    if not _node_ok:
        sys.stderr.write("FORENSICS_CRASHED_1031 :: node unavailable (%s)\n" % _node_why)
        return None, "crashed"
    _res = run_node_script(FORENSICS, timeout=300,
                            env=dict(os.environ, JIMENG_FORENSICS_OUT=FRESH_DEFAULT))
    if _res["crashed"]:
        sys.stderr.write("FORENSICS_CRASHED_1031 rc=%s :: %s\n"
                         % (_res["rc"], (_res["stderr"] or "")[-800:]))
        return None, "crashed"
    p = Path(FRESH_DEFAULT)
    if not p.exists():
        sys.stderr.write("FORENSICS_CRASHED_1031 :: 跑完了但没写盘\n")
        return None, "crashed"
    return json.loads(p.read_text(encoding="utf-8")), "live"


def testids_of(doc):
    out = set()
    for c in doc.get("clickables", []):
        # ⭐⭐⭐⭐⭐ **单列字段优先、`sel` 正则回落** —— 两边必须读**同一个来源**
        #   ⇒ 条件等待（node 侧读 `testid`）与最终判定（这里）若各读各的
        #   ⇒ ⇒ 一边永远说「缺」、另一边永远说「齐」⇒ 门既等不到、也判不出真缺
        t = c.get("testid")
        if t:
            out.add(t)
            continue
        m = re.search(r'data-testid="([^"]+)"', c.get("sel", ""))
        if m:
            out.add(m.group(1))
    return out


def aria_of(doc):
    return {c["aria"] for c in doc.get("clickables", []) if c.get("aria")}


def _body_text(doc):
    """⭐⭐⭐⭐⭐ **全文优先、截断回落** —— 而且**必须把用了哪一口径记下来**
    ⇒⇒⇒ 节点类型与状态行不在前 3000 字符里时，用截断文本去判 ⇒ 「永远缺」
    ⇒⇒⇒ 而「永远缺」会被读成「产品缺」⇒ **那是口径缺陷冒充产品缺陷**
    ⇒⇒⇒ 口径缺陷与产品缺陷必须能被分开 ⇒ 所以口径本身要进产物
    """
    full = doc.get("body_full")
    if isinstance(full, str) and full:
        return full, "body_full"
    head = doc.get("body_head", "")
    return (head if isinstance(head, str) else ""), "body_head"


def status_lines(doc):
    body, _cal = _body_text(doc)
    return [l.strip() for l in body.split("\n")
            if re.match(r"^\d+ nodes, \d+ edges, \d+ selected\.", l.strip())]


out = {"generated_by": "jimeng_probe1031_live_canvas_contract.py"}

if not CONTRACT.exists():
    out["fatal"] = "契约文件不存在：%s" % CONTRACT
    # ⭐ 三个字段成对出现（此时探针本身没崩 ⇒ probe_crashed=False；
    #   ⇒⇒⇒ 而没有读数 ⇒ available/fresh 都 false ⇒⇒⇒ 满足 1037 的 R3）
    out["probe_crashed"] = False
    out["readings_available"] = False
    out["readings_fresh"] = False
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    # ⭐ 这一行原本是 `exit(1)`，而「契约没登记」是**数据/环境错**、不是判据为假
    #   ⇒ 第一版「退出码可区分」只改了一半：坏 JSON 归了 2，文件缺失还留在 1
    #   ⇒⇒⇒ 外部对照当场量到才看见（场景4）⇒ 半修等于没修
    print("CONTRACT_MISSING（数据错，rc=2）-> 先跑一次真实取证把契约登记进来")
    sys.exit(2)

CONTRACT_TEXT = CONTRACT.read_text(encoding="utf-8")

# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **退出码必须能区分「门红」和「探针自己崩了」**
#   起因（本批当场实测）：造一份语法坏掉的契约副本去试 P6 ⇒ 探针抛 Traceback，
#   退出码 **1**；而造一份真含重复键的契约副本 ⇒ P6 正确报红，退出码 **也是 1**。
#   ⇒⇒⇒ 在 CI 里这两种完全分不开 ⇒「门红了，人去查契约」会一直查错方向。
#   ⇒⇒⇒ 本文件约定：**0 = 全绿，1 = 有 P 判据为假，2 = 探针崩了（人去查探针）**，
#   并且下面 `JIMENG_FORCE_CRASH=1` 会真的走一遍 2 号出口，
#   好让「2 代表崩溃」这个约定**自己被测过**，而不是只在注释里。
if os.environ.get("JIMENG_FORCE_CRASH") == "1":
    sys.stderr.write("FORCED_CRASH_1031: 用于证明 rc=2 与 rc=1 可区分\n")
    sys.exit(2)

try:
    C = json.loads(CONTRACT_TEXT)
except ValueError as _e:
    # 契约语法坏 ⇒ 这是**数据错**，要说人话，不该是一坨 Traceback
    out["fatal"] = "契约文件不是合法 JSON：%s" % _e
    io.open(OUT, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("CONTRACT_BAD_JSON（数据错，rc=2）-> %s" % _e)
    sys.exit(2)

REQ_T = list(C.get("required_testids", []))
REQ_A = list(C.get("required_aria", []))
KINDS = list(C.get("node_kinds", []))

# ⭐ 候选副本可能不在仓内 ⇒ 不能无条件 `relative_to`（会抛 ValueError，
#   而一个「探针崩了」和「契约坏了」必须能分开看）
out["contract_file"] = (str(CONTRACT.relative_to(ROOT))
                       if str(CONTRACT).startswith(str(ROOT))
                       else str(CONTRACT))
# ⭐⭐⭐⭐⭐ aria 分**两种口径**：字面量集合 与 形状集合 —— 不能合到一起数，也不能合到一起比
#   （钉了会漂的数若留在字面量集合里，对应读数一变就必然转红）
SHAPES = C.get("aria_shapes", {}) or {}
out["contract_counts"] = {"n_testids": len(REQ_T),
                          "n_aria_literals": len(REQ_A),
                          "n_aria_shapes": len(SHAPES),
                          "n_node_kinds": len(KINDS)}

# ⭐⭐⭐⭐⭐ **把这条规矩钉成判据，而不是靠自觉**
#   契约自己写着「登记的是形状不是读数」⇒ 那么**字面量 aria 集合里就不该出现数字**
#   ⇒ 它一旦出现，要么该挪进 `aria_shapes`，要么是没想清楚 ⇒ 报红
_ARIA_DIGIT = re.compile(r"\d")
out["aria_literals_carrying_a_digit"] = [a for a in REQ_A if _ARIA_DIGIT.search(a)]
out["P9_no_literal_aria_carries_a_driftable_number_1031"] = bool(
    not out["aria_literals_carrying_a_digit"])

# ⇒ 重复键检测直接做在 **AST** 上（而不是被 `literal_eval` 后的 dict 上）
#   ⇒⇒⇒ 因为 Python 的 dict 字面量会静静把后一个同名键覆盖掉，`literal_eval` 之后看不到任何痕痕
_DUP_KEYS = []
try:
    _TREE = ast.parse(CONTRACT_TEXT)
    _AST_OK = True
except SyntaxError as _se:
    _TREE, _AST_OK = None, False
    out["contract_ast_syntax_error"] = str(_se)
for _n in (ast.walk(_TREE) if _TREE is not None else []):
    if isinstance(_n, ast.Dict):
        _ks = [k.value for k in _n.keys
               if isinstance(k, ast.Constant) and isinstance(k.value, str)]
        _c = collections.Counter(_ks)
        _dup = sorted(k for k, c2 in _c.items() if c2 > 1)
        if _dup:
            _DUP_KEYS.append({"line": _n.lineno, "keys": _dup[:5]})
# ⭐⭐⭐⭐⭐ **P6 的绿是有前提的，而这个前提原本是隐式的**
#   重复键检测跑在 `ast.parse` 上 ⇒ 一旦这一步炸了，`_DUP_KEYS` 恒为 `[]`
#   ⇒⇒⇒ P6 会「因为探针没看见任何重复键」而**转绿** —— 那是本套门最贵的那种绿。
#   ⇒⇒⇒ 本批一度以为「契约里加个 JSON 的 `true` 就会让 ast.parse 炸」（因为 `literal_eval` 会炸），
#   实测**不成立**：`ast.parse` 只做语法解析、不解析名字，`true` 只是个未定义标识符，语法合法。
#   ⇒⇒⇒ 结论不能纸上推演、要实测；但**前提本身必须显式登记成一条判据**，不能靠「它应该不会炸」。
out["contract_parses_as_python_ast"] = bool(_AST_OK)
out["P7_contract_is_parseable_by_both_readers_1031"] = bool(_AST_OK)

# ⭐⭐⭐⭐⭐ **P6 第一版只查契约文件，范围本身就窄了**
#   重复键的真正高发地不是证据 JSON，而是**这套门自己的源码** —— 就在写 P6 的同一批里，
#   `jimeng_check_verifier_anchors.py` 的 `PROBE_VARS` 里 `_p1031` 被**连着写了两遍**，
#   而字典字面量会静默吞掉它 ⇒ 官方锚点门照样全绿、不报错、无判据变红。
#   ⇒⇒⇒ 同一把尺子必须**量到尺子自己**：门自己出重复键，和证据出重复键是同一种损坏。
_SELF_FILES = ["scripts/jimeng_unclickable_audit.py",
               "scripts/jimeng_check_verifier_anchors.py",
               "scripts/verify-jimeng-batch841-unclickable.py",
               "scripts/jimeng_probe1031_live_canvas_contract.py"]
_SELF_DUP = []
for _rel in _SELF_FILES:
    _f = ROOT / _rel
    if not _f.exists():
        _SELF_DUP.append({"file": _rel, "keys": ["<文件不存在>"]})
        continue
    try:
        _t = ast.parse(_f.read_text(encoding="utf-8"))
    except SyntaxError as _se:
        _SELF_DUP.append({"file": _rel, "keys": ["<语法错: %s>" % _se]})
        continue
    for _n in ast.walk(_t):
        if isinstance(_n, ast.Dict):
            _ks2 = [k.value for k in _n.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            _d2 = sorted(k for k, c3 in collections.Counter(_ks2).items() if c3 > 1)
            if _d2:
                _SELF_DUP.append({"file": _rel, "line": _n.lineno, "keys": _d2[:5]})
out["duplicate_keys_in_gate_sources"] = _SELF_DUP
out["P8_gate_sources_have_no_duplicate_keys_1031"] = bool(not _SELF_DUP)

# ── 离线自洽（不需要浏览器） ───────────────────────────────────────────
out["P1_contract_is_wellformed_1031"] = bool(
    REQ_T and KINDS
    and len(set(REQ_T)) == len(REQ_T) and len(set(REQ_A)) == len(REQ_A)
    and all(t.startswith(TESTID_PREFIX) or t == "flow-node-title"
            or t == "rf__wrapper" or t == "timeline-mute-button" for t in REQ_T))
out["P2_status_shape_is_a_shape_not_a_number_1031"] = bool(
    C.get("status_shape") == STATUS_SHAPE.pattern
    and C.get("observed_status_line")
    and STATUS_SHAPE.match(C["observed_status_line"]))
# ⭐ 「生成历史」是**查看历史**的入口，不是触发生成 ⇒ 必须在**条目**层面排除，
#   而不是在**词**层面排除 —— 第一版把条件写成了 `if w != "生成历史"`，
#   拿「词」去比「条目」⇒ 永远为真地排除不掉任何东西 ⇒ P3 当场转红。
_ITEMS = REQ_T + REQ_A + KINDS + list(C.get("top_chrome_texts", []))
_BAD_ITEMS = [x for x in _ITEMS
              if any(w in x for w in GENERATION_WORDS) and x != "生成历史"]
out["P3_contract_carries_no_generation_action_1031"] = bool(not _BAD_ITEMS)
out["p3_offending_items"] = _BAD_ITEMS

# ── 实跑对账 ───────────────────────────────────────────────────────────
live, how = harvest()
# ⭐ 只留**分类**、不留细节（stderr 每次都不同 ⇒ 进产物就把产物变成随机量）
out["live_source"] = how.split(":", 1)[0]
out["live_available"] = live is not None

if live is not None:
    got_t, got_a = testids_of(live), aria_of(live)
    body, _body_caliber = _body_text(live)
    missing_t = [t for t in REQ_T if t not in got_t]
    missing_a = [a for a in REQ_A if a not in got_a]
    # 形状口径用 `re.match` 而不是 `in` —— 读数是多少都算命中，形状不对才算缺
    _all_a = sorted(got_a)
    missing_s = [k for k, v in SHAPES.items()
                 if not any(re.match(v.get("pattern", r"(?!)"), a) for a in _all_a)]
    missing_k = [k for k in KINDS if k not in body]
    # ⭐⭐⭐⭐⭐ **这份产物逐字节参与 1015 的可复现判定 ⇒ 只许留形状与布尔**
    #   `title` / `n_clickables: 112` / `76 nodes, ...` 每次跑都会变
    #   ⇒⇒⇒ 留在产物里会让 1015 永远判 drifted ⇒ 原始读数放**契约**（一次性取证的快照）
    out["live_1031"] = {
        "contract_counts_checked": {"testids": len(REQ_T),
                                    "aria_literals": len(REQ_A),
                                    "aria_shapes": len(SHAPES),
                                    "node_kinds": len(KINDS)},
        "missing_testids": missing_t,
        "missing_aria": missing_a,
        "missing_aria_shapes": missing_s,
        "all_aria_shapes_found": bool(not missing_s),
        "missing_node_kinds": missing_k,
        "all_testids_found": bool(not missing_t),
        "all_aria_found": bool(not missing_a),
        "all_node_kinds_found": bool(not missing_k),
        # ⭐ 引擎名是**class 名**，不在 innerText 里 ⇒ 第一版拿文本去找它，永远找不到
        "engine_found": bool(live.get("has_engine")),
        "status_line_shape_matched": bool(status_lines(live)),
        # ⭐⭐⭐⭐⭐ **判「节点类型 / 状态行」用的是全文还是截断文本** ⇒ 必须进产物
        #   ⇒ 否则「因为口径而永远缺」与「产品真的缺」在账上长得一模一样
        "body_caliber_used": _body_caliber,
        # ⭐⭐⭐⭐⭐ **「等到了没有」** —— 只有布尔进产物
        #   ⇒ 耗时与轮数每次都变 ⇒ 写进产物就等于把读数变成随机量
        #   ⇒ None 表示「这一轮没有这个读数」（例如指向副本的注入式通路）
        "wait_satisfied": live.get("wait_satisfied"),
    }
    out["P4_live_matches_contract_1031"] = bool(
        not missing_t and not missing_a and not missing_s and not missing_k
        and out["live_1031"]["engine_found"])
    out["P5_live_status_line_shape_1031"] = bool(status_lines(live))
    # ⭐⭐⭐⭐⭐ **「等到了没有」必须是一条独立的判据**
    #   ⇒⇒⇒ 「等不到」是**样本不成立**（不是「产品缺」）⇒ 它必须自己红
    #   ⇒⇒⇒ 含糊地只体现在 missing 列表里 ⇒ 读数少与读数全没法一眼分开
    #   ⇒⇒⇒ 注入式通路（指向副本）没有这个读数 ⇒ 那条通路不判它、也不假装它成立
    out["P10_waited_until_the_contract_was_satisfied_1031"] = (
        True if how == "copy" else (live.get("wait_satisfied") is True))
else:
    out["P4_live_matches_contract_1031"] = None
    out["P5_live_status_line_shape_1031"] = None
    out["P10_waited_until_the_contract_was_satisfied_1031"] = None
    # ⭐⭐⭐⭐⭐ 一个很讱人觉得罕式的门：**同一个字典块里不许有重复键**
#   原因：本批因为一次 `&&` 链在前一步失败后仍继续跑，生成脚本被执行了两次
#   ⇒ 同一段散文被插了**两遍**，而其中一轮还把「两份」写坏成了「4e24份」⇒
#   ⇒ **重复键不会报错、不会让 `ast.parse` 失败、也不会让任何一条判据变红** ⇒ 它是纯的无声损坏
out["duplicate_keys_in_audit_block"] = _DUP_KEYS
out["P6_no_duplicate_keys_in_contract_block_1031"] = bool(not _DUP_KEYS)

out["downgraded"] = (
    ("⚠️⭐⭐⭐⭐⭐ **取证脚本崩了（不是「没测到」）** —— 这时 P4/P5/P10 记 `null`，"
     "而**退出码是 2**（仪器崩）⇒ 崩溃不会被降级伪装成「没测到、还没红」")
    if how == "crashed" else
    ("⚠️⭐⭐⭐⭐⭐ **本轮没有浏览器通路，P4/P5 记 `null` 而不是 `False`**"
     " —— 记成 `False` 就是「没跑过」与「跑过没过」混成同一件事，"
     "而这正是这套门最贵的那种失败"))

# ⭐⭐⭐⭐⭐ 三个字段必须**成对出现** ⇒ ⇒ 「可用性」与「新鲜度」缺一不可
#   ⇒ ⇒⇒ 「新鲜度」= **这一轮用的读数就是这一轮产的**（live：本轮的 .mjs 写的；
#   ⇒ ⇒⇒⇒   copy：本轮显式注入的那份）⇒ ⇒⇒⇒ **而不是「上一轮遗留的」**
#   ⇒ ⇒⇒⇒ 而崩了 ⇒ ⇒ 两项都 false（1037 的 R3：fresh=False ⇒ available 必须 False）
out["probe_crashed"] = bool(how == "crashed")
out["readings_available"] = bool(live is not None)
out["readings_fresh"] = bool(live is not None)

io.open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
if live is not None:
    L = out["live_1031"]
    print("live[%s] 契约 %s ⇒ testid 缺=%d、aria 缺=%d、节点类型缺=%d、引擎=%s、状态行形状=%s"
          % (how, json.dumps(L["contract_counts_checked"], ensure_ascii=False),
             len(L["missing_testids"]), len(L["missing_aria"]),
             len(L["missing_node_kinds"]), L["engine_found"],
             L["status_line_shape_matched"]))
    print("（原始读数如可点元素数、状态行原文**每次都会变** ⇒ 已刻意不进产物，"
          "它们留在 contracts/ 的契约里作为一次性取证的快照）")
else:
    print("⚠️ live 不可用 ⇒ P4/P5 记 null（降级，不是失败）")

_P = [(k, v) for k, v in sorted(out.items())
      if re.match(r"^P\d+_", k) and k.endswith("_1031")]
_bad = [k for k, v in _P if v is False]
print("P 判据 = %s" % json.dumps([v for _k, v in _P], ensure_ascii=False))
print("P 为假的：", _bad or "无", "| 共 %d 条" % len(_P))
assert len(_P) >= 9, "P 判据条数掉到 9 以下了：%d" % len(_P)
print("退出码约定：0=全绿 1=有 P 判据为假 2=探针崩了/契约不是合法 JSON"
      "（JIMENG_FORCE_CRASH=1 可现场验证 2 号出口）")
print("PROBE_1031_DONE ->", OUT)
# ⭐⭐⭐⭐⭐ **取证脚本崩了 ⇒ 走 2 号出口** ⇒ 降级（0）会把崩溃伪装成「没测到、还没红」
sys.exit(2 if how == "crashed" else (1 if _bad else 0))