#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十道闸：账号配额表——**它宣称穷举了全部配额，那就必须真的穷举**。

**为什么要有这道闸（Batch 233 的由来）**：`10-tasks/storage-quota.md` 有一节叫
「账号有**九**项配额」，那是个**穷举声明**——读者正是靠它判断「我撞到的这条在不在手册里」。
可回源一数，上游 `RuntimeResourcePolicy` 有 **10 个配额字段**、绑在它们身上的
**用户可见报错文案有 13 条**，手册只写了 11 条。漏掉的两条都会真的撞到读者身上：

  · **整条配额缺失**：`TaskDataGB`（默认 **1GB**）在 `storage_quota.go:63-68` 有真实校验、
    三个调用点（建任务 / 记请求日志 / 任务完成）、上游还自带单测
    （`storage_quota_test.go:40`），报错是「账号任务历史数据已达到 1GB 上限，请联系管理员归档」。
    **全手册检索这条零命中**——读者撞到它，手册里没有这条，也没有那张表能让他推断出来。
  · **同配额的第二种措辞缺失**：`GeneratedFileMB` 有**两条**文案——`upload_quota.go:36`
    的「单个生成**文件**不能超过 64MB」和 `resource.go:743` 的「单个生成**资源**超过 64MB」，
    前者走预留路径、后者走 data URL 解码路径。手册只写了前一条。
    **讽刺的是同一页下面就有一个 tip 专门讲「两种写法、同一条限制」**，
    而它举的例子只有素材数与画布数——**现象存在，只是漏认了一处**。

**本闸判什么**（**五个方向**，缺一不可）：
  ① **完整**：上游每一条渲染出来的配额报错文案，手册表里必须都出现
     （这一条就是本批真缺陷的来源——**它抓的是「手册没写」，而单边判据抓不到**）；
  ② **准确**：手册表里每一条文案，上游必须真的渲染得出
     （防上游改文案后手册留着旧版，**与①方向相反，两边都核**）；
  ③ **数值**：每行的「默认值」格必须等于该行文案所绑定字段的上游默认取值
     （防「默认值」列与「报错」列各说各话）；
  ④ **行数**（Batch 233 加，与①③同期）：表里的**行数**必须等于**上游有文案的字段数**
     ——①②③逐条核，但**表里少一整行、且那一行对应的文案上游还没写**时三条都发现不了，
     而「一共就这 N 条」仍然是假的（**穷举声明的形状**）；
  ⑤ **个数（Batch 318 新增）**：**全树读者页里「N 项配额 / N 个配额」的 N，
     必须等于本表实际行数**（实测命中 4 处，全是「十项配额」）。

     **它接的是纪律 351④ 说的第二种形状**：**信息已经在本闸的输出里**
     ——「配额表 10 行」这句话每次构建都在打——**而手册在另外 4 处把它写成
     「十项配额」，中间没有任何东西把两者连起来**。
     **不接的后果可以逐字推演**：上游加第 11 个字段 → 方向四红 → 人加第 11 行表 →
     **那 4 句「十项」原地不动地变成假话，而构建照绿。**

     **而本闸自己的报错文案里一直写着「把「N 项配额」的 N 改成表的实际行数」**
     ——**那句话从 Batch 233 起就在指使人，而从没有自己动手。**

**合法集从上游自己算出来，不建人工登记表**（纪律 242）：字段集取自
`RuntimeResourcePolicy` 结构体定义、文案集取自**绑定到这些字段的字面量**，
上游加字段或改文案，本闸的期望值跟着变。

**覆盖不到什么（如实说明）**：
  · 只在**单行内**抽取绑定关系（实测上游 13 条候选全是单行；跨行的会触发下面的自检报 rc=2）；
  · 排除 `*_test.go`（单测里的字符串不是用户会看到的文案）；
  · **只核 `storage-quota.md` 那张规范表**。`90-troubleshooting.md` 另有一段缩写式散文列举
    （「存储总量 20GB、结构化数据 256MB…」），**刻意不核**——它把 2048MB 写成「2GB」是合法编辑选择，
    要匹配就得手工维护一张「缩写名 → 字段」的登记表，**而登记表正是纪律 242 禁止的东西**。
    **判据把正确的东西报成缺陷，危害比缺陷本身大**（纪律 248）；
    **⚠️ Batch 318 把这条边界说准了**：**上面说的「不核」针对的是那段散文的「条目」，
    不是它的「个数」。** 方向五核的是 `90-troubleshooting.md` 里那句
    「服务端强制**十项**配额」的**十**——**而核一个数不需要任何登记表**，
    那个数就写在句子里。**改那段列举的条目数值仍然放行**（反验第 10 例钉住这一半）。
  · 不核「本地部署那一套取值」——那是闸 12 `verify-runtime-policy.py` 的职责（它在 20-reference 上核两套）。

退出码：0 五方向全相符；1 有不符；2 未能核对（找不到源码 / 结构体 / 规范表 / 抽取有解析缺口）。
"""
import os
import re
import subprocess
import sys
from baseline import resolve_ref, BaselineError, module_ref, baseline_guard
from baseline import SRC as _BEEFSRC
from baseline import announce_fallback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUAL = os.path.join(ROOT, "10-tasks/storage-quota.md")
SRC = _BEEFSRC
REF = module_ref()
POLICY_FILE = "backend/internal/platform/runtime_policy.go"

#: 规范表的**表头**就是定位锚——**刻意不用小节标题**（Batch 232 的教训：
#: 把标题从 H3 改成 H2 就打挂了写死 `### 取证基线` 的基线闸。表头是内容的一部分，
#: 改名要改的是结论，而表头三列「配额 / 默认值 / 撞到时的报错」正是本闸要核的对象本身）。
TABLE_HEADER = ["配额", "默认值", "撞到时的报错"]

#: 手册把「同一个上限的两种措辞」写在同一格里，用这个分隔符。
CELL_SPLIT = " / "


def _git_show(path):
    r = subprocess.run(["git", "-C", SRC, "show", f"{REF}:{path}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def _git_grep(pattern):
    """全树搜绑定到配额字段的行。**排除单测**——那里的字符串不是用户会看到的文案。"""
    r = subprocess.run(
        ["git", "-C", SRC, "grep", "-nE", pattern, REF, "--", "*.go",
         ":(exclude)*_test.go"],
        capture_output=True, text=True)
    if r.returncode not in (0, 1):      # 1 = 没匹配到，是正常结果
        return None
    return r.stdout


# ---------------------------------------------------------------- 上游解析

def _const_values(text):
    """const 块里的常量名 → 数值（顺手去掉 Go 的下划线分隔符，如 999_999_999）。"""
    out = {}
    for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s+(?:int64|int)?\s*=\s*([0-9_]+)\s*$",
                         text, re.M):
        try:
            out[m.group(1)] = int(m.group(2).replace("_", ""))
        except ValueError:
            pass
    return out


def _func_body(text, func_name):
    m = re.search(r"^func\s+%s\s*\(\)[^{]*\{" % re.escape(func_name), text, re.M)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


def _struct_fields(text, struct_name):
    """取结构体定义里的 `Name int64|int` 字段名——**字段集从上游自己算，不写死**（纪律 242）。"""
    m = re.search(r"type\s+%s\s+struct\s*\{(.*?)\n\}" % re.escape(struct_name), text, re.S)
    if not m:
        return []
    return re.findall(r"^\s*(\w+)\s+(?:int64|int)\b", m.group(1), re.M)


def _value_of(body, key, consts):
    """在函数体里取 `Key: <值>`。值可能是字面量，也可能是常量名。

    **刻意不收 `envInt(...)` 这类表达式**——它们是**部署方可配置项**；
    解析不了时返回 None，由调用方按「未能核对」处理。
    """
    m = re.search(r"\b%s\s*:\s*([^,\n]+)" % re.escape(key), body)
    if not m:
        return None
    raw = m.group(1).strip().rstrip(",")
    if re.match(r"^\d[\d_]*$", raw):
        return int(raw.replace("_", ""))
    m2 = re.match(r"^([A-Za-z_]\w*)$", raw)
    if m2 and m2.group(1) in consts:
        return consts[m2.group(1)]
    return None


#: 上游的容量换算与展示格式。**照抄语义而不是照抄名字**：
#: `megabytes/gigabytes` 是移位乘，`formatStorageLimit` 在整 GB 时输出 `%dGB`、否则 `%dMB`。
#: **这一段是闸 30 能算对「2GB」而不只是「2048」的原因**——手册的默认值列写 2048MB、
#: 报错列写 2GB，**两个都是对的**，因为上游的渲染函数把前者折成了后者。
def _megabytes(v):
    return v << 20


def _gigabytes(v):
    return v << 30


def _format_storage_limit(v):
    if v % (1 << 30) == 0:
        return "%dGB" % (v >> 30)
    return "%dMB" % (v >> 20)


_WRAPPERS = {
    "megabytes": _megabytes,
    "gigabytes": _gigabytes,
    "formatStorageLimit": _format_storage_limit,
}


def _apply_wrappers(wrappers, value):
    """上游是 `formatStorageLimit(megabytes(policy.X))`：最内层先作用。"""
    for name in reversed(wrappers):
        value = _WRAPPERS[name](value)
    return value


# ---------------------------------------------------------------- 文案抽取

_STR_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _iter_literals(line):
    """逐个吐出这一行里的 Go 双引号字面量（跳过转义引号）。"""
    for m in _STR_RE.finditer(line):
        yield m.group(1), m.end()


#: 宽松形态：只用来做**自检**（判据的解析有缺口时诚实报 rc=2，而不是安静地少算一条）。
_TAIL_LOOSE = re.compile(r"policy(?:\.Resource)?\.(\w+)")

#: 严格形态：逗号之后**紧跟**（可隔若干层函数调用）一个 `policy[.Resource].字段`。
#: 「紧跟」是关键——`Printf("x=%s", a, policy.Y)` 那种只是顺带提到的会被挡掉。
_TAIL_STRICT = re.compile(r"^,\s*((?:[A-Za-z_]\w*\(\s*)*)policy(?:\.Resource)?\.(\w+)")


def _tail_after(line, end):
    """字面量闭合引号之后的那段参数文本，遇到**属于本调用的**右括号为止。

    括号深度从 0 起算：所以停在 `Sprintf(...)` 自己的右括号，
    **不会**把外层 `QuotaExceeded(...)` 的参数吞进来。
    """
    depth = 0
    for j in range(end, len(line)):
        ch = line[j]
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                return line[end:j]
            depth -= 1
    return line[end:]


def extract_messages(grep_out, fields, defaults):
    """从候选行里抽出 (渲染后的文案, 字段, 出处)。抽不动的行一并报出来做自检。"""
    records, gaps = {}, []
    for raw in grep_out.splitlines():
        # git grep -n 的行首是 `<ref>:<路径>:<行号>:`——**必须按冒号数切而不是 partition**，
        # 否则 ref 里那一个冒号会把位置整个吃掉（第一版就是这么崩的）。
        parts = raw.split(":", 3)
        if len(parts) < 4:
            gaps.append(f"无法解析的 grep 行：{raw[:80]}")
            continue
        src, lineno, line = parts[1], parts[2], parts[3]
        found_here = False
        #: 本行**疑似**有绑定却没解析出来的现场。**按行收集而不是按字面量**：
        #: `return "", BadAuthRequest(fmt.Sprintf("…", policy.X))` 的第一个字面量是那个空串，
        #: 它的 tail 里混着**后面另一个调用**的 policy 引用——**按字面量判会把它误报成解析缺口**
        #: （第一版就是这么自报了 3 条假阳性）。同一行里只要有一个字面量解析成功，就算这一行没缺口。
        suspects = []
        for template, end in _iter_literals(line):
            tail = _tail_after(line, end)
            m = _TAIL_STRICT.match(tail)
            if m and m.group(2) in fields and m.group(2) in defaults:
                field = m.group(2)
                wrappers = [w for w in re.findall(r"([A-Za-z_]\w*)\(", m.group(1))
                            if w in _WRAPPERS]
                value = _apply_wrappers(wrappers, defaults[field])
                verbs = re.findall(r"%[a-z]", template)
                if not verbs:
                    # 形如 `reserveChunkedUploadQuota(..., "")`：**故意留空**，不是文案
                    found_here = True
                    continue
                if len(verbs) != 1:
                    suspects.append(f"{src}:{lineno} 模板有 {len(verbs)} 个占位符，本闸只支持 1 个")
                    continue
                rendered = template.replace(verbs[0], str(value), 1)
                if not rendered.strip():
                    found_here = True
                    continue
                found_here = True
                records.setdefault(rendered, (field, f"{src}:{lineno}"))
            else:
                loose = _TAIL_LOOSE.search(tail)
                if loose and loose.group(1) in fields:
                    suspects.append(f"{src}:{lineno} 绑定在「{tail.strip()[:60]}」，"
                                    f"判据解析不了（字段 {loose.group(1)}）")
        if not found_here and '"' in line:
            loose_all = _TAIL_LOOSE.search(line)
            if not (loose_all and loose_all.group(1) in fields):
                gaps.append(f"{src}:{lineno} 含字符串字面量但没抽出绑定关系")
            else:
                gaps.extend(suspects)
        elif not found_here:
            gaps.extend(suspects)
    return records, gaps


# ---------------------------------------------------------------- 手册解析

def _split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_table():
    """定位规范表：**按表头找，不按小节标题找**（见 TABLE_HEADER 上方注释）。"""
    if not os.path.isfile(MANUAL):
        raise ValueError(f"找不到 {MANUAL}")
    lines = open(MANUAL, encoding="utf-8").read().split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = _split_row(line)
        if cells[:3] != TABLE_HEADER:
            continue
        rows = []
        for nxt in lines[i + 1:]:
            if not nxt.startswith("|"):
                break
            if re.match(r"\|\s*:?-", nxt):
                continue
            c = _split_row(nxt)
            if len(c) < 3 or not c[0] or c[0] == TABLE_HEADER[0]:
                continue
            rows.append({"label": c[0], "default": c[1], "errors": c[2]})
        if not rows:
            raise ValueError(f"「{' | '.join(TABLE_HEADER)}」表头下面没有数据行")
        return rows
    raise ValueError(f"{os.path.relpath(MANUAL, ROOT)} 里找不到表头为"
                     f"「{' | '.join(TABLE_HEADER)}」的配额表")


def _has_number(cell, value):
    return re.search(r"(?<!\d)%d(?!\d)" % value, cell) is not None


#: **方向五（Batch 318）**只认这两个紧邻形态，其余一律不看：
#: 「N 项配额」与「N 个配额」。**实测全树命中 4 处，全是「十项配额」**。
QUOTA_COUNT_RE = re.compile(
    r"([一二三四五六七八九十两\d]{1,3})\s*(?:项配额|个配额)")
#: 中文数字→阿拉伯数字。**只够 1～99**，而**读不出来就报「读不出来」而不是当成通过**
#: （纪律 101：解析器退化必须表现为失败）。
_CN_DIGIT = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
             "六": 6, "七": 7, "八": 8, "九": 9}


def _cn_int(s):
    if s.isdigit():
        return int(s)
    if "十" in s:
        a, _, b = s.partition("十")
        tens = _CN_DIGIT.get(a, 1) if a else 1
        ones = _CN_DIGIT.get(b, 0) if b else 0
        return tens * 10 + ones
    if len(s) == 1 and s in _CN_DIGIT:
        return _CN_DIGIT[s]
    return None


def _quota_count_claims():
    """扫**读者页**里「N 项配额 / N 个配额」，产出 `(文件, 行号, 原样文字, 值或 None)`。

    **排除内部台账**（`AUDIT.md` / `AUDIT-RULES.md` / `PROGRESS.md` …）
    ——**它们天然含历史叙述**，而本方向核的是**对读者生效的那句话**。
    """
    import os
    internal = {"AUDIT.md", "AUDIT-RULES.md", "PROGRESS.md", "FINAL-REPORT.md",
                "SOURCE-OBSERVATIONS.md"}
    skip_dirs = {".git", "node_modules", ".vitepress", "dist", ".agents",
                 "__pycache__", "screenshots", "scripts"}
    out = []
    for dp, dn, fns in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in skip_dirs]
        for fn in sorted(fns):
            if not fn.endswith(".md") or fn in internal:
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, ROOT)
            with open(p, encoding="utf-8") as fh:
                for i, line in enumerate(fh.read().split("\n"), 1):
                    for m in QUOTA_COUNT_RE.finditer(line):
                        tok = m.group(0)
                        out.append((rel, i, tok, _cn_int(m.group(1))))
    return out


@baseline_guard
def main():
    announce_fallback()
    if SRC is None:
        print(f"[skip] 未找到 BeefTV 源码 {SRC}，配额核对本轮未能进行")
        return 2
    try:
        rows = parse_table()
    except ValueError as exc:
        print(f"[skip] {exc}，配额核对本轮未能进行")
        return 2

    text = _git_show(POLICY_FILE)
    if text is None:
        print(f"[skip] 读不到 {REF}:{POLICY_FILE}，配额核对本轮未能进行")
        return 2
    fields = _struct_fields(text, "RuntimeResourcePolicy")
    body = _func_body(text, "DefaultRuntimePolicy")
    if not fields or not body:
        print(f"[skip] 在 {POLICY_FILE} 里抽不出 RuntimeResourcePolicy 的字段"
              f"（{len(fields)} 个）或 DefaultRuntimePolicy()，本轮未能核对")
        return 2
    consts = _const_values(text)
    defaults = {}
    for f in fields:
        v = _value_of(body, f, consts)
        if v is not None:
            defaults[f] = v
    if not defaults:
        print("[skip] RuntimeResourcePolicy 的默认值一个都解析不出来，本轮未能核对")
        return 2

    alternation = "|".join(fields)
    grep_out = _git_grep(rf"policy(\.Resource)?\.({alternation})")
    if grep_out is None:
        print(f"[skip] 在 {REF} 全树 grep 配额字段绑定失败，配额核对本轮未能进行")
        return 2
    messages, gaps = extract_messages(grep_out, fields, defaults)

    for g in gaps:
        print(f"[skip] {g}")
    if not messages:
        print("[skip] 上游一条配额报错文案都没抽出来——**判据可能已失效**，本轮未能核对")
        return 2

    # ---- 方向①完整：上游有的，手册必须有
    table_errors = " ¦ ".join(r["errors"] for r in rows)
    missing = []
    for rendered in sorted(messages):
        if rendered not in table_errors:
            field, where = messages[rendered]
            missing.append(f"手册表里没有这条文案（绑定字段 {field}，上游 {where}）：「{rendered}」")

    # ---- 方向②准确：手册有的，上游必须渲染得出
    extra = []
    for row in rows:
        for part in row["errors"].split(CELL_SPLIT):
            part = part.strip()
            if part and part not in messages:
                extra.append(f"「{row['label']}」这格写着「{part}」，"
                             f"上游渲染不出这句——它已不是现行文案")

    # ---- 方向③数值：默认值列必须等于该行文案所绑字段的上游默认值
    numbad = []
    for row in rows:
        fields_here = []
        for part in row["errors"].split(CELL_SPLIT):
            part = part.strip()
            if part in messages:
                fields_here.append(messages[part][0])
        for f in dict.fromkeys(fields_here):
            if not _has_number(row["default"], defaults[f]):
                numbad.append(f"「{row['label']}」默认值格写「{row['default']}」，"
                              f"而它的文案绑定 {f}={defaults[f]}")

    # ---- 方向④行数：表的行数须等于上游有文案的字段数（穷举声明的形状）
    fields_in_upstream = {f for f, _ in messages.values()}
    if len(rows) != len(fields_in_upstream):
        extra.append(f"表里 {len(rows)} 行，上游有配额文案的字段却只有 "
                     f"{len(fields_in_upstream)} 个：{sorted(fields_in_upstream)}")

    # ---- 方向五（Batch 318 新增）：正文里「N 项配额」的 N 必须等于表的实际行数
    # **而本方向只核那一个数，不核 `90-troubleshooting.md` 那段散文列举的条目**
    # ——**文件头声明的边界针对的是「条目」，不是「个数」**：
    # 要核条目就得维护一张「缩写名 → 字段」登记表，**而登记表正是纪律 242 禁止的**；
    # **核一个数不需要任何登记表**，那个数就写在句子里。
    # **这正是纪律 351④ 说的第二种形状**：**信息已经在本闸的输出里**
    # （「配额表 10 行」），**而手册在另外 4 处把它写成了「十项配额」，
    # 中间没有任何东西把两者连起来**。
    # **不接的后果具体可推演**：上游加第 11 个字段 → 本闸方向四红 →
    # 人加第 11 行表 → **那 4 句「十项」原地不动地变成假话**，而构建照绿。
    countbad = []
    n_rows = len(rows)
    for rel, lineno, tok, val in _quota_count_claims():
        if val is None:
            countbad.append(f"{rel} 第 {lineno} 行：「{tok}」的个数读不出来")
            continue
        if val != n_rows:
            countbad.append(
                f"{rel} 第 {lineno} 行写「{tok}」，**而配额表实际有 {n_rows} 行**"
                "——**这个数是「一共就这 N 项」的读者依据**"
                "（本闸的报错文案里一直写着「把「N 项配额」的 N 改成表的实际行数」，"
                "**而那句话一直是在指使人，不是在自己动手**）")
    bad = missing + extra + numbad + countbad
    if bad:
        print(f"账号配额核对：{len(bad)} 处声明与上游不符"
              f"（漏写 {len(missing)} / 多写或行数不符 {len(extra)} / "
              f"数值不符 {len(numbad)} / 个数不符 {len(countbad)}）")
        for b in bad:
            print("  " + b)
        print("→ 更新 10-tasks/storage-quota.md 的配额表：**每一条上游文案都要在表里出现**，"
              "同一个上限的两种措辞写进同一格（用「 / 」分隔），"
              "并把「N 项配额」的 N 改成表的实际行数")
        return 1
    if gaps:
        print(f"[skip] {len(gaps)} 行本轮未能解析，"
              f"其余 {len(messages)} 条文案五方向都相符 —— **不是全部通过**")
        return 2
    print(f"账号配额核对通过：上游 {len(fields_in_upstream)} 个配额字段 / "
          f"{len(messages)} 条报错文案，与配额表 {len(rows)} 行在"
          f"**完整性、准确性、数值、行数、个数**五个方向都与 {REF} 相符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
