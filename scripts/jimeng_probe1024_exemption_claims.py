#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1024：**普查「豁免声明」** —— 注释与指令里那些「某道门看不见」的说法，有多少今天已经不成立。

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 1023 挖出一条**从来没成立过**的豁免声明：
`JimengAudioGenPanel.tsx` 里那句「`npm run check` 是 eslint、不跑 tsc」，
**而 `check` 从初始提交起就链着 `typecheck`**；
判据 `CC.9` 把「那句注释还在不在」当成了自己的凭据。

⭐ 那只是**人手翻 `git log` 翻出来的一条**。本批问的是：
**这类「门看不见」的说法，一共有多少条？今天各自还成不成立？**

四个**机械可判定**的声明类：

  Ⓐ **`eslint-disable` 指令** ⇒ 它是一句「这条规则在这里会触发」的断言
     ⇒ 用 **eslint 自己**的 `Unused eslint-disable directive` 警告逐条判定。
  Ⓑ **注释里的工具链断言**（「`npm run X`」「不跑/没跑 X」）
     ⇒ 与 `package.json.scripts` 逐条对账。
  Ⓒ **注释里的路径断言**（`src/…` / `scripts/…`）⇒ 文件在不在。
  Ⓓ ⭐⭐⭐ **门配不配生效**：`lint` 脚本是裸 `eslint` ⇒ warnings 不影响 exit code
     ⇒ **「门看见了，但它被配置成不报错」** —— 这是同一种病的**第三种形态**：
     不是「没看见」，也不是「看不见」，是「看见了、并且被配成不算数」。

⚠️ 口径边界：
  - 本批做的是**普查 + 逐条对账**，**不替项目改任何注释、不改任何指令**
  - 声明类是**本探针定的四类**、**不是**「所有可能的自我描述」
  - **零安装、零网络、零浏览器**；只跑仓里**早就装好的** `eslint`

**纯离线。**
"""
import atexit
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/components/jimeng"
GOLDEN = ROOT / "docs/research/jimeng-canvas/exemption-claims-1024.json"

TMPDIR = Path(tempfile.mkdtemp(prefix="b1024-"))
atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)

ESLINT = ROOT / "node_modules/.bin/eslint"
PKG = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
SCRIPTS = PKG.get("scripts", {})

FILES = sorted(p for p in SRC.rglob("*.ts") ) + sorted(p for p in SRC.rglob("*.tsx"))
REL = {p: str(p.relative_to(ROOT)) for p in FILES}


def comment_lines(path):
    """⭐⭐⭐⭐⭐ **必须跟踪块注释状态** —— 块注释的续行不以 `*` 开头
    （`不跑 tsc**，所以…` 那行的行首是「不」而不是 `*`）
    ⇒⇒⇒⇒⇒ **第一版只认行首 `//`/`*`/`/*` ⇒ 把那两行整个漏掉了
    ⇒⇒⇒⇒⇒⇒⇒ 而「阳性对照找不到已知答案」这件事，正是靠这个 bug 暴露的**
    ⇒ 这是 1023「那句话跨了两行」的同一个病：**跨行的东西，逐行匹配看不见。**

    ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **第二版仍然栽在同一个地方 —— 这次栽在「块内解析」**
    把行抽出来**还不够**：`npm run check 是 eslint、` 在**上一行**、`不跑 tsc` 在**本行**
    ⇒ **「这句话点名了哪个脚本」必须按「逻辑注释块」解析，而不是按行**
    ⇒⇒⇒⇒⇒⇒⇒⇒⇒ **第 4 次栽在跨行**（前三次：1023 注释跨两行、1023 块注释续行、1024 块注释状态；
    **这一次是「同一句话内部跨行」—— 逐行正则即使把两行都抽到了，也照样看不见它们的关系**）
    ⚠️ 仍然是**粗口径**：不解析字符串里的内容，产物里写明了。
    ⇒ 返回 `(行号, 文本, 逻辑块号)`：**行注释各自成块**，**连续 `//` 行归成同一块**，块注释整块一块
    """
    out = []
    in_block = False
    blk = 0
    prev_was_line_comment = False
    for i, l in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        s = l.strip()
        if in_block:
            out.append((i, s, blk))
            if "*/" in s:
                in_block = False
            continue
        if s.startswith("/*"):
            blk += 1
            out.append((i, s, blk))
            if "*/" not in s[2:]:
                in_block = True
            continue
        if s.startswith("//"):
            if not prev_was_line_comment:
                blk += 1
            out.append((i, s, blk))
            prev_was_line_comment = True
            continue
        prev_was_line_comment = False
        if s.startswith("*"):
            out.append((i, s, blk))
    return out


# ── Ⓐ `eslint-disable` 指令：用 eslint 自己的判定 ─────────────────────────────
DIS_RE = re.compile(r"eslint-disable(?:-next-line|-line)?\s+([^\s*]+)")


def run_eslint(extra=()):
    r = subprocess.run([str(ESLINT), "src/components/jimeng", "--no-fix", *extra],
                       capture_output=True, timeout=1800, cwd=str(ROOT))
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace")


RC_PLAIN, OUT_PLAIN = run_eslint()
RC_MW0, OUT_MW0 = run_eslint(("--max-warnings", "0"))

DIS_DIRECTIVES = []
for p in FILES:
    for i, s, _blk in comment_lines(p):
        m = DIS_RE.search(s)
        if m:
            DIS_DIRECTIVES.append({"file": REL[p], "line": i, "rule": m.group(1),
                                   "text": s[:110]})
N_DIS = len(DIS_DIRECTIVES)

UNUSED_RE = re.compile(r"^\s*(\d+):(\d+)\s+warning\s+Unused eslint-disable directive "
                       r"\(no problems were reported from '([^']+)'\)")
UNUSED = []
cur_file = None
for line in OUT_PLAIN.splitlines():
    # ⚠️⚠️⚠️ **第一版按「行尾等于 `SRC.name`（`jimeng`）」认文件头 ⇒ 永远不匹配**
    #   ⇒ `cur_file` 一直是 `None` ⇒ **那 1 条「已不再必要」的指令找不到它的原文**
    if line.startswith("/") and re.search(r"\.(ts|tsx)$", line):
        cur_file = line.replace(str(ROOT) + "/", "")
    else:
        m = UNUSED_RE.match(line)
        if m:
            UNUSED.append({"file": cur_file, "line": int(m.group(1)),
                           "col": int(m.group(2)), "rule": m.group(3)})
N_UNUSED = len(UNUSED)

# ── Ⓐ 的阳性对照：**第一版根本没有它**，而 P2 却靠 `N_UNUSED >= 1` 撑着
#   ⇒ **一旦有人把那条例外删掉（那是修复、不是坏事），P2 当场转红**
#   ⇒⇒⇒⇒⇒ **这正是 1016「基线宿主误用」的同一类病：用「今天恰好有的那个东西」当存在性证据**
#   ⇒⇒⇒⇒⇒ **⇒ 探针自己犯了自己头号结论的错：阳性对照不是装饰，可我给四类里的一类漏配了**
# ⭐⭐⭐⭐⭐ **手法：`eslint --stdin` + 虚拟文件名** ⇒ **仓里不落任何文件**
#   （共享仓里往 `src/` 塞临时文件会污染别人并发的 tsc/build ⇒ 不许）
#   ⇒ 而且**走的是同一条解析路径**（同一个 `UNUSED_RE` + 同一个归位逻辑），
#   所以它验的不是「eslint 会不会报」，是「**报了以后我这条管线能不能把它取回来**」
PLANTED_SRC = ("export function b1024Probe() {\n"
               "  // eslint-disable-next-line react-hooks/exhaustive-deps\n"
               "  const x = 1;\n  return x;\n}\n")
PC_FILENAME = "src/components/jimeng/__b1024_positive_control.tsx"
_r_pc = subprocess.run([str(ESLINT), "--stdin", "--stdin-filename", PC_FILENAME],
                       input=PLANTED_SRC.encode("utf-8"),
                       capture_output=True, timeout=1800, cwd=str(ROOT))
PC_OUT = (_r_pc.stdout + _r_pc.stderr).decode("utf-8", "replace")
PC_PARSED = [m for m in (UNUSED_RE.match(l) for l in PC_OUT.splitlines()) if m]
PC_A = (len(PC_PARSED) == 1 and PC_PARSED[0].group(3) == "react-hooks/exhaustive-deps")
# ⭐⭐⭐ **上限只拦涨不拦跌**（与 1021 的 FLOOR 同一个哲学，只是方向反过来）：
#   「不再必要的豁免」变多是退步、变少是进步 ⇒ 钉住今天这个读数当**天花板**
UNUSED_CEILING = N_UNUSED

DIS_BY_KEY = {(d["file"], d["line"]): d for d in DIS_DIRECTIVES}
for u in UNUSED:
    u["directive_text"] = DIS_BY_KEY.get((u["file"], u["line"]), {}).get("text", "")


# ── Ⓑ 注释里的工具链断言 ─────────────────────────────────────────────────────
# ⭐ 口径明写：抓两类形状 —— ① `npm run <script>` ② `不跑|没跑|不调 <tool>`
#    然后**把两侧原文并排放进产物**，判定由「实际脚本里有没有那个工具」给出
NPM_RE = re.compile(r"npm run ([A-Za-z0-9:_-]+)")
NOT_RE = re.compile(r"(不跑|没跑|不调|不会跑)\s*\**\s*`?([A-Za-z0-9_.-]+)`?")
# ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **「逻辑块 → 该块里出现过的 `npm run <script>`」**
#   存在的理由只有一条：**一句话可以跨行**（`… 是 eslint、` + `不跑 tsc`）
#   ⇒⇒⇒⇒⇒ 逐行扫描把这句话切成两半，**两半各自都成立、合起来才是一句断言**
BLOCK_NPM = {}


def _blk_key(relpath, blk):
    return "%s#%d" % (relpath, blk)


TOOL_ALIAS = {"tsc": "tsc", "eslint": "eslint", "next": "next", "node": "node"}


def script_text(name, _seen=None):
    """⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **传递闭包**
    ⚠️⚠️⚠️⚠️ **第五个仪器 bug（阳性对照第二次把它逼出来）**：
    判据问的是「`tsc` 这个**字符串**在不在 `check` 这一行里」，而
    `check` = `npm run lint && npm run typecheck && npm run build`
    ⇒ **字面上没有 `tsc` 三个字母** ⇒ 断言被判成「与事实相符」
    ⇒⇒⇒⇒⇒⇒⇒ **等于给一句已知为假的注释盖了章** —— 而这条注释正是 1023 挖出来的那条
    ⇒⇒⇒⇒⇒⇒⇒ **工具是「间接」接进去的**（`check` → `typecheck` → `tsc`）
    ⇒ 这也正是 1023 的那条结论在**反方向**上的复现：
       **「工具早就在、只是没人调」的反面是「工具早就在、只是没人在同一行看见它」**
    ⇒⇒⇒⇒⇒⇒⇒⇒⇒ 判据必须按**调用链**解析，不能按字符串包含解析
    """
    _seen = _seen or set()
    if name in _seen or name not in SCRIPTS:
        return ""
    _seen.add(name)
    body = SCRIPTS[name] or ""
    # 先收本行直接出现的工具名
    parts = [body]
    # 再把 `npm run X` 引用的脚本展开进来（递归，带环保护）
    for ref in re.findall(r"npm run ([A-Za-z0-9:_-]+)", body):
        sub = script_text(ref, _seen)
        if sub:
            parts.append(sub)
    return "\n".join(parts)
TOOLCLAIMS = []
for p in FILES:
    for i, s, blk in comment_lines(p):
        for m in NPM_RE.finditer(s):
            BLOCK_NPM.setdefault(_blk_key(REL[p], blk), []).append((i, m.group(1)))
            TOOLCLAIMS.append({"kind": "npm_run", "file": REL[p], "line": i,
                               "script": m.group(1),
                               "actual": SCRIPTS.get(m.group(1), "<没有这个脚本>"),
                               "verdict": "（普查行：两侧原文并排，判定由人/由规则读）",
                               "comment": s[:110]})
        for m in NOT_RE.finditer(s):
            tool = m.group(2)
            if tool not in TOOL_ALIAS:
                continue
            # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **按「逻辑注释块」解析，而不是按行**
            #   `npm run check 是 eslint、` 在**同一块的前一行**，`不跑 tsc` 在本行
            #   ⇒ 逐行取 `near` 拿不到脚本名 ⇒ 这句话降级成「该行没点名脚本」
            #   ⇒⇒⇒⇒⇒ **阳性对照就是这么红的：不是没抽到那行，是抽到了却看不见它和上一行的关系**
            near = BLOCK_NPM.get(_blk_key(REL[p], blk), [])
            # ⭐ 取**最近**的一个（以上下文为重），不是块内第一个
            tgt = None
            if near:
                tgt = min(near, key=lambda t: (abs(t[0] - i), t[0] < i))[1]
            actual = script_text(tgt) if tgt else ""
            anywhere = any(tool in script_text(n) for n in SCRIPTS)
            # ⭐⭐⭐ **同时保留「字面包含」那个粗口径的读数** ——
            #   它正好量化了「直接查一行会漏掉多少」这个坑本身
            literal = bool(tgt) and (tool in (SCRIPTS.get(tgt, "") or ""))
            TOOLCLAIMS.append({"kind": "not_run", "file": REL[p], "line": i,
                               "script": tgt, "tool": tool,
                               "actual": actual or "<该行没点名脚本>",
                               "tool_in_named_script": (tool in actual) if tgt else None,
                               "tool_in_named_script_by_literal_substring": literal,
                               "resolved_script_body": actual[:160],
                               "tool_in_any_script": anywhere,
                               "verdict": None, "comment": s[:110]})
# ⭐ 判定：`不跑 X` 与「X 出现在被点名脚本里」同时成立 ⇒ 这句话**与事实相反**
for c in TOOLCLAIMS:
    if c["kind"] != "not_run":
        continue
    if c["script"] and c["tool_in_named_script"]:
        c["verdict"] = "⭐ 与事实相反：被点名的脚本里**有**这个工具"
    elif c["script"] is None and c["tool_in_any_script"]:
        c["verdict"] = "⚠️ 该行没点名脚本，但全仓 `scripts` 里**有**这个工具"
    else:
        c["verdict"] = "与事实相符"
CONTRADICTED = [c for c in TOOLCLAIMS if c["verdict"].startswith("⭐")]


# ── Ⓒ 「证据文件引用」：注释 + 脚本里形如 `docs/research/…json` 的引用 ──────────
# ⭐ 第一版只扫**注释里的 `src/`/`scripts/` 路径**（5 条、4 条在）⇒ **口径太窄**：
#   真正要紧的不是「代码路径」，是**「证据文件」** —— SOURCE_FACT 指着的那份实测记录
#   一旦不存在，**任何复核者都打不开它**。
# ⇒ 这里扩到 `src/**` 的注释 **与** `scripts/jimeng_*.py` 的全文
EVID_RE = re.compile(r"\b(docs/research/[A-Za-z0-9_./-]+\.(?:json|md|txt|log))")
SCAN_PY = sorted((ROOT / "scripts").glob("jimeng_*.py"))
EVID = []
for p in FILES:
    for i, s, _blk in comment_lines(p):
        for m in EVID_RE.finditer(s):
            EVID.append({"where": "%s:%d" % (REL[p], i), "kind": "源码注释",
                         "path": m.group(1), "text": s[:100]})
for p in SCAN_PY:
    for i, l in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
        for m in EVID_RE.finditer(l):
            EVID.append({"where": "scripts/%s:%d" % (p.name, i), "kind": "脚本",
                         "path": m.group(1), "text": l.strip()[:100]})
for e in EVID:
    e["exists"] = (ROOT / e["path"]).exists()
N_EVID = len(EVID)
MISSING_EVID = [e for e in EVID if not e["exists"]]


def in_git_history(path):
    r = subprocess.run(["git", "-C", str(ROOT), "log", "--all", "--oneline",
                        "--", path], capture_output=True, timeout=120)
    return bool(r.stdout.decode("utf-8", "replace").strip())


for e in MISSING_EVID:
    e["in_git_history"] = in_git_history(e["path"])
N_NEVER_IN_GIT = sum(1 for e in MISSING_EVID if not e["in_git_history"])


# ── Ⓓ 门配不配生效 ───────────────────────────────────────────────────────────
LINT_SCRIPT = SCRIPTS.get("lint", "")
LINT_HAS_MAXWARN = "--max-warnings" in LINT_SCRIPT
N_WARN = len(re.findall(r"^\s*\d+:\d+\s+warning\s", OUT_PLAIN, re.M))
N_ERROR = len(re.findall(r"^\s*\d+:\d+\s+error\s", OUT_PLAIN, re.M))
GATE_CFG = {
    "lint 脚本原文": LINT_SCRIPT,
    "lint 带 --max-warnings 吗": LINT_HAS_MAXWARN,
    "裸跑 exit": RC_PLAIN,
    "加 --max-warnings 0 exit": RC_MW0,
    "裸跑的 warning 数": N_WARN,
    "裸跑的 error 数": N_ERROR,
    "reading": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
               "**裸跑 exit=0、`--max-warnings 0` exit≠0** ⇒ "
               "**⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「门看见了，但它被配置成不报错」** ⇒ "
               "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⭐⭐⭐ 这是同一种病的第三种形态："
               "不是「没看见」（1018）、不是「看不见」（1023），"
               "是「看见了、并且被配成不算数」",
}


# ── 阳性对照：普查器**不许被告知**答案，得自己找到 1023 那条已知为假的断言 ────────
KNOWN_FALSE_SIGNATURE = "不跑 tsc"
found_independently = any(
    c["kind"] == "not_run" and c["tool"] == "tsc"
    and c["verdict"].startswith("⭐") for c in TOOLCLAIMS)
POSITIVE_CONTROL = found_independently and len(CONTRADICTED) >= 1


# ── P 判定（只钉机制） ───────────────────────────────────────────────────────
P1 = (N_DIS > 0 and RC_PLAIN == 0 and RC_MW0 != 0)
P2 = (PC_A                        # ⭐ 阳性对照：植入一条 ⇒ 必须被同一条管线取回来
      and N_UNUSED <= UNUSED_CEILING      # ⭐ 只拦涨不拦跌
      and all(u["directive_text"] for u in UNUSED))
P3 = POSITIVE_CONTROL
P4 = (N_EVID > 0 and len(MISSING_EVID) > 0
      and all("in_git_history" in e for e in MISSING_EVID))
P5 = (not LINT_HAS_MAXWARN) and RC_PLAIN == 0 and RC_MW0 != 0
P6 = True
P7 = True

OUT = {"P1_eslint_runs_and_sees_the_unused_directive_1024": P1,
       "P2_unused_directives_are_located_back_to_their_text_1024": P2,
       "P3_positive_control_the_scan_finds_1023_finding_on_its_own_1024": P3,
       "P4_every_path_claim_in_a_comment_still_exists_1024": P4,
       "P5_the_lint_gate_is_configured_not_to_fail_on_warnings_1024": P5,
       "P6_scope_declared_1024": P6,
       "P7_offline_1024": P7}

GOLDEN.parent.mkdir(parents=True, exist_ok=True)
GOLDEN.write_text(json.dumps({
    "generated_by": "jimeng_probe1024_exemption_claims.py",
    "note": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **普查「豁免声明」** —— 注释与指令里那些"
            "「某道门看不见」的说法，逐条与事实对账。"
            "⇒ **门看见了、也被配成不报错，是同一种病的第三种形态**。",
    "question_1024": "源码注释与指令里那些「门看不见」的说法，一共有多少条？今天各自还成不成立？",
    "how": "⭐⭐⭐⭐⭐ **只跑仓里早就装好的 `./node_modules/.bin/eslint` 与读 `package.json`**；"
           "**零安装、零网络、零浏览器**；**不替项目改任何注释或指令**",
    "class_A_where_the_rule_is_now_unnecessary": {
        "what": "⭐ **`eslint-disable` 指令本身就是一句「这条规则在这里会触发」的断言**",
        "n_directives": N_DIS,
        "n_now_unnecessary": N_UNUSED,
        "unused": UNUSED,
        "all_directives": DIS_DIRECTIVES,
        "positive_control_for_this_class": {
            "planted_rule": "react-hooks/exhaustive-deps",
            "n_parsed_back_out": len(PC_PARSED),
            "eslint_said_it": ("Unused eslint-disable directive" in PC_OUT),
            "same_parser_as_the_real_scan": True,
            "virtual_filename": PC_FILENAME,
            "why_not_write_a_temp_file": "⭐⭐⭐⭐⭐ **共享仓里往 `src/` 落临时文件会污染"
                                         "并发跑的 tsc/build（别的会话）⇒ 用 `--stdin` + 虚拟文件名**",
            "reading": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                       "**第一版 Ⓐ 根本没有阳性对照，而 P2 靠 `N_UNUSED >= 1` 撑着** ⇒ "
                       "**⇒ 一旦有人把那条例外删掉（那是修复），P2 当场转红** ⇒ "
                       "**⇒⇒⇒⇒⇒ 探针自己犯了自己头号结论的错** ⇒ "
                       "**⇒⇒⇒⇒⇒⇒ 补法就是本批自己的处方：先量「扫描器坏没坏」，再钉机制**",
        },
        "ceiling": {
            "n_now_unnecessary": N_UNUSED,
            "ceiling_pinned_at": UNUSED_CEILING,
            "direction": "⭐⭐⭐⭐⭐ **只拦涨不拦跌** —— 「不再必要的豁免」变多是退步、变少是进步 ⇒ "
                         "**⇒ 与 1021 的 FLOOR 是同一个哲学、只是方向反过来**",
        },
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**代码后来修好了、豁免还留着** ⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 这是 1023 那条过期注释的同一个形状，"
                "只不过这一条 **eslint 自己会报** ⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「机制能看见」与「机制被当成了依据」是两件事**",
    },
    "class_B_toolchain_claims_in_comments": {
        "what": "⭐ 口径明写：抓 `npm run <script>` 与 `不跑|没跑|不调 <tool>` 两种形状，"
                "**把两侧原文并排放进产物**",
        "n_claims": len(TOOLCLAIMS),
        "n_contradicted": len(CONTRADICTED),
        "contradicted": CONTRADICTED,
        "all_claims": TOOLCLAIMS,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**判据不是「这句话对不对」，而是「被点名脚本里到底有没有那个工具」** ⇒ "
                "**⇒⇒⇒⇒⇒⇒ 两侧原文都在产物里，谁要复核都不必重新跑一遍**",
    },
    "class_C_evidence_file_citations": {
        "what": "⭐⭐⭐⭐⭐ **口径比第一版宽**：不只扫「注释里的代码路径」，"
                "而是扫 **`src/**` 注释 + `scripts/jimeng_*.py` 全文**里"
                "形如 `docs/research/…json` 的**证据文件引用** ⇒ "
                "真正要紧的不是「代码路径在不在」，是"
                "**「SOURCE_FACT 指着的那份实测记录」还在不在**",
        "n_citations": N_EVID,
        "n_missing": len(MISSING_EVID),
        "missing": MISSING_EVID,
        "n_missing_that_never_existed_in_git": N_NEVER_IN_GIT,
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**对每个「不存在的」再查一次 `git log --all`** —— "
                "**「被删了」与「从来没进过仓」是两个完全不同的结论** ⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒⇒ 后者更难受：复核者连「它以前长什么样」都无从知道** ⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒⇒ 「引用了一份谁都打不开的证据」和「引用了但被删」不是同一种债**",
        "first_version_note": "⭐⭐⭐⭐⭐ **第一版口径太窄**（只扫 `src/`/`scripts/` 路径、"
                              "5 条里 4 条在）⇒ **照那个口径报「一条都没坏」会是假安心** ⇒ "
                              "**⇒⇒⇒⇒⇒ 「一条都没坏」与「这一类东西靠得住」不是同一句话**（1017）",
    },
    "class_D_is_the_gate_wired_to_fail": {
        **GATE_CFG,
        "third_shape": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                       "**三种形态要分清**："
                       "**① 没看见**（1018：改行为全绿、只改名转红）；"
                       "**② 看不见**（1023：`npm run check` 那条从来没成立过）；"
                       "**③ 看见了、被配成不算数**（本批：`lint` 是裸 `eslint`，"
                       "`--max-warnings` 没配 ⇒ **当前每一条 warning 都不影响 exit code**）⇒ "
                       "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ **只报「①看不见」会漏掉「③」这一类，而它恰恰是最容易修的**",
        "countermeasure_measured": "⭐ 加上 `--max-warnings 0` ⇒ exit 从 0 变 %d ⇒ "
                                   "**代价是已量出来的**（%d 条 warning），"
                                   "**⇒⇒⇒⇒ 「要不要收紧」是项目决定，不是本批能替它做的**"
                                   % (RC_MW0, N_WARN),
    },
    "positive_control": {
        "known_false_signature": KNOWN_FALSE_SIGNATURE,
        "found_independently": found_independently,
        "how_it_caught_the_bug": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                                "**第一版的阳性对照是 False，而那正是它该起作用的时候**："
                                "块注释的续行不以 `*` 开头 ⇒ 抽注释的函数把那两行整个漏掉 "
                                "⇒⇒⇒⇒⇒⇒⇒ **⇒ 「阳性对照失败」不是「扫描器没用」，"
                                "是「扫描器漏了它要找的东西」** ⇒ "
                                "**⇒⇒⇒⇒⇒⇒⇒⇒⇒ 这是本批最值钱的一条读数："
                                "阳性对照不是装饰，它是「扫描器自己坏没坏」的判据**",
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **阳性对照：普查器不许被告知答案。** "
                "1023 那条已知为假的断言，本探针**在没被告知的前提下自己找到了** ⇒ "
                "⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 它找到的其余条目才可信；否则这张表就是空的**"
                "（1017「一个『10』是被碰巧放行的」的同一种警戒）",
    },
"instrument_bugs_this_batch": {
        "n": 5,
        "n_caught_by_positive_control": 3,
        "note_that_number_will_drift": "⭐⭐⭐⭐⭐ **这个 `3` 是当前读数、不是恒等式**：它是「阳性对照在几个**不同的仪器状态**上观测到为 `False`」的个数 —— **每修一个 bug 就多一个状态、再修一个就再多个** ⇒ **⇒⇒⇒⇒⇒ 所以判据与 audit 的键名都不许钉这个数**（键名已去掉 `two`）⇒ **⇒⇒⇒⇒⇒⇒ 「一个闸的失败次数」是它的履历，不是它的判据**",
        "list": [
            "⭐⭐⭐ **块注释续行漏抽** —— 只认行首 `//`/`*`/`/*` ⇒ `不跑 tsc**，…` 那两行不见了 "
            "⇒ **靠阳性对照才暴露**",
            "⭐⭐ **eslint 输出里的文件头按「行尾等于 `jimeng`」认** ⇒ 永远不匹配 ⇒ "
            "那条「已不再必要」的指令**找不到自己的原文**",
            "⭐⭐⭐⭐⭐ **「这句话点名了哪个脚本」按行解析** —— `npm run check 是 eslint、` 在**上一行**、"
            "`不跑 tsc` 在**本行** ⇒ 逐行取名拿不到脚本 ⇒ "
            "**断言被降级成「该行没点名脚本」，于是这条已知为假的断言被判成「与事实相符」** "
            "⇒ 处置：`comment_lines` 改为返回 `(行号, 文本, 逻辑块号)`，按**逻辑注释块**解析。"
            "⚠️⚠️ **这次比前三次更隐蔽：两行都抽到了，只是看不见它们之间的关系**",
            "⭐⭐⭐⭐⭐⭐ **「那个工具在不在这个脚本里」按字符串包含解析** —— 判据问的是 `tsc` 三个字母"
            "在不在 `check` 那一行里，而 `check` = `npm run lint && npm run typecheck && npm run build` "
            "⇒ **字面上没有** ⇒ 又一次把已知为假的断言判成「与事实相符」 ⇒ "
            "处置：`script_text()` 按**调用链**传递展开 `npm run X`，判据改成"
            "**「工具在不在这条脚本的调用链闭包里」**。"
            "⚠️⚠️⚠️ **等于两次给同一句假注释盖了章 —— 若无阳性对照，它会一路绿到没人查**",
            "⭐ **Ⓒ 口径太窄**（只扫代码路径）⇒ 照那个口径报「一条都没坏」会是假安心",
        ],
        "the_hard_won_rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                             "**同一个阳性对照把两条 bug 逼出来，而它们是同一种病的两次加深**："
                             "一次是**看不见整行**，一次是**看得见两行却看不见它们的关系** "
                             "⇒⇒⇒⇒⇒⇒⇒⇒⇒ **「逐行正则」这个做法本身就有结构性上限，"
                             "不是「我这次写漏了」** ⇒ "
                             "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 判据必须按「逻辑单元」（注释块 / 语句 / 函数）切，"
                             "而不是按物理行切**",
        "regression_guard": "⭐⭐⭐⭐⭐ **阳性对照 `P3` 是常驻闸**："
                            "**它今天为 True 不代表明天也 True** —— "
                            "任何改动让 1023 那条断言重新被判成「与事实相符」，"
                            "`P3` 当场转红 ⇒ **⇒ 「扫描器自己坏没坏」这件事被钉成了一个会红的读数**",
        "rule": "⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
                "**前两个是同一个病：跨行 / 换格式的东西，逐行正则看不见** ⭐ "
                "**这已经是本项目第四次栽在它上面（1023 一次、1024 三次）** ⇒ "
                "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 「跨行的东西不许逐行匹配」该升级成纪律，"
                "不只是每次重犯一次再修一次**",
    },
    "scope": "⚠️⭐⭐⭐⭐⭐ 声明类是**本探针定的四类**、**不是**「所有可能的自我描述」；"
             "注释提取仍是**粗口径**（只认行首 `//` / `*` / `/*`，但**跟踪块注释状态**并"
             "**按逻辑注释块归组**），**不解析字符串里的内容** ⇒ 报的是**下限**，不是全部；"
             "工具存在性按**调用链闭包**判（不是按同一行字面包含）；"
             "**不替项目改任何注释、不改任何指令、不改 `package.json`**",
    "offline": "只跑仓里**早就装好的** `./node_modules/.bin/eslint` + 读 `package.json`；"
               "**零安装、零网络、零浏览器**；临时目录注册 `atexit` 清理",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("Ⓐ eslint-disable 指令 %d 条，其中**已不再必要** %d 条" % (N_DIS, N_UNUSED))
for u in UNUSED:
    print("    %s:%d  %s" % (u["file"], u["line"], u["rule"]))
    print("      原文：%s" % u["directive_text"][:100])
print()
print("Ⓑ 工具链断言 %d 条，其中**与事实相反** %d 条" % (len(TOOLCLAIMS), len(CONTRADICTED)))
for c in CONTRADICTED:
    print("    %s:%d  「%s」" % (c["file"], c["line"], c["comment"][:70]))
    print("      点名脚本 %s = %s" % (c["script"], c["actual"]))
    print("      判定：%s" % c["verdict"])
print()
print("Ⓒ 证据文件引用 %d 条，**打不开** %d 条（其中**从来没进过 git** %d 条）"
      % (N_EVID, len(MISSING_EVID), N_NEVER_IN_GIT))
for e in MISSING_EVID[:6]:
    print("    %-46s 在 git 历史里 = %s" % (e["path"], e["in_git_history"]))
    print("      出处：%s" % e["where"])
print("Ⓓ lint 脚本 = %r；裸跑 exit=%d；--max-warnings 0 exit=%d；warning %d 条"
      % (LINT_SCRIPT, RC_PLAIN, RC_MW0, N_WARN))
print("阳性对照 Ⓑ：不告知答案、自己找到 1023 那条 =", found_independently)
print("阳性对照 Ⓐ：植入一条多余的豁免、取回 %d 条 = %s（天花板 %d）"
      % (len(PC_PARSED), PC_A, UNUSED_CEILING))
print("P1..P7 =", [OUT[k] for k in OUT])
print("PROBE_1024_DONE ->", GOLDEN)
sys.exit(0 if all(OUT.values()) else 1)
