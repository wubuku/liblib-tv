#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 门禁：★ 「看着可点、点了没反应」的那批控件 ⟹ ⟹ 让它们**没有下一次**。

## ★ 本批在做什么（★ 一句话说清）

★ 目标里有一条硬要求：★ 「**检查之前已有的复刻成果**，如发现『糊弄』之处，
★ 如有检出必须整改到位」⟹ ⟹ 本批**先普查**，**再整改**，**再上锁**。

★ ★★ 本批挖出**两个**层级的问题：
  ① **两处真糊弄**（点了什么也不发生、却长得像按钮）
     ⟹ ⟹ `CharacterLibraryPanel.tsx` 的「生成其他年龄版本」（★ 源站**有**这个功能）
     ⟹ ⟹ 导演台右栏的「⟳ 预设运镜」「创建运动轨迹」
  ② **两道门禁的普查口径有洞** ⟹ ⟹ 于是那些洞里的红**从来没人看见**
     ⟹ ⟹ `367` 的 `CROSS_LINE` 含 `"Director"` ⟹ ⟹ **导演台整片失明**
     ⟹ ⟹ `866` 的「碰被跟踪源文件」只看**文件名** ⟹ ⟹ **目录型门禁**失明
     ⟹ ⟹ ⟹ ⟹ ⇒ 清单外 **93** 条门禁在碰导演台源文件 ⟹ ⟹ ⟹ ⟹ ⇒ 红的藏得住

## ★ 判据构成

- **S1 运行时证据在库**：★ 两处整改的**运行时**读数（★ 10 条核对 0 失败）
- **S2 ★★ 结构性判据**：★ 两处整改点**必须**有 `onClick`
  ⟹ ⟹ ⟹ ⟹ ★ 且**必须剥掉注释**再查（★ 注释里写 `onClick` 会假绿）
- **S3 ★★ 导演台零死控件**：★ `src/components/director/**` 里
  ⟹ ⟹ 可点元素 ⟹ ⟹ **要么有行为**、**要么已标惰性**
  ⟹ ⟹ ⟹ ⟹ ⇒ ★ 这条**补上**了 `367` 因 `CROSS_LINE` 而失明的整片
- **S4 ★★ 清单不许再有洞**：★ 用**放宽后的口径**（文件名 ∪ 目录名 ∪ `src` 上的
  `glob`/`rglob`）重算「碰被跟踪源文件的门禁」⟹ ⟹ ⟹ ⟹ ⇒ **必须全在回归清单里**
- **S5 ★ 静态普查在库**：★ 本批自己的静态扫描读数 ⟹ ⟹ 且**候选必须全在**已登记白名单
- **S6 ★ 负控证据在库**

## ★ 纪律

- ★ 期望值**只从实测解析**，不凭记忆手打；
- ★ 「这个按钮本该有行为」的**依据**必须来自**源站证据**（i18n 逐字／源站截图）；
- ★ 判据**不许**写死行号（★ 定位靠 needle 唯一命中）；
- ★ 「全文含某串」类判据 ⟹ ⟹ **必须剥掉注释**再查。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
RAW = OUT_DIR / "raw"

# ★ ★★ Batch 869 修正：★ 「在用的回归清单」**不能写死文件名**。
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 写死的后果（本批实测）：★ 本批新增了 `verify-liblib-batch869.py`
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而它**碰被跟踪源文件** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 于是本门禁报「缺口＝869.py」
#   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而那个红与本门禁要验的性质（覆盖面）**毫无关系**。
#   ⟹ ⇒ **修法**：★ 在用清单＝`docs/research/liblib-canvas-batch*/probes/
#   ⟹ ⇒   regress*.py` 里**批次号最大**的那一份 ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 不用写死。
HISTORIC_REGRESS = (OUT_DIR / "probes/regress868.py")
RUNTIME = RAW / "runtime-868.json"
STATIC = RAW / "static-scan-868.json"
NEWGATES = RAW / "new-gates-868.json"

# ★ ★★ 放宽后的「碰被跟踪源文件」口径（★ 本批的核心修正之一）
TRACKED_SRC = [
    "src/components/director/DirectorViewport.tsx",
    "src/components/director/DirectorAspectPanel.tsx",
    "src/store/directorStore.ts",
    "src/lib/directorTelemetry.ts",
]
TRACKED_DIRS = ["src/components", "src/store", "src/lib"]

# ★ ★★ 本批整改的两处（★ 期望值来自源站证据 ⟹ ⟹ 见 README）
FIXES = [
    {
        "id": "quick-age",
        "relpath": "src/components/CharacterLibraryPanel.tsx",
        "needle": 'aria-label="生成其他年龄版本"',
        "why": "★ 源站 i18n 逐字：characterStudioQuickAgeTip / "
               "characterStudioAgeVersionName = {name}{age}版",
    },
    {
        "id": "motion-preset",
        "relpath": "src/components/director/DirectorCameraMotionTab.tsx",
        "needle": "data-director-motion-preset-button",
        "why": "★ 源站截图 50/51 的右栏就是这两个入口",
    },
    {
        "id": "motion-create-path",
        "relpath": "src/components/director/DirectorCameraMotionTab.tsx",
        "needle": "data-director-motion-create-path",
        "why": "★ 同上",
    },
]

# ★ ★★ 已登记的「够不着」白名单（★ 与 367/368 的登记**一致** ⟹ ⟹ 不重复开口子）
ALLOWED_UNREACHABLE = {
    ("src/components/CameraConfigDialog.tsx", 102),
    ("src/components/CameraConfigDialog.tsx", 140),
    ("src/components/CameraConfigDialog.tsx", 178),
    ("src/components/CameraConfigDialog.tsx", 216),
    ("src/components/VideoGenerationPanel.tsx", 499),
    # ★ 「查看框选去字幕说明」是**hover 目标**（★ 悬停它会弹出说明浮层）
    # ⟹ ⟹ 它不是死控件 ⟹ ⟹ ⟹ ⟹ ⇒ 登记为「不是候选」
    ("src/components/SubtitleErasePanel.tsx", 472),
}


class Verifier:
    def __init__(self) -> None:
        self.count = 0
        self.failures: list[str] = []
        self.result: dict[str, Any] = {}

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        if not ok:
            self.failures.append(f"{name}  ⟵ {detail}")


def strip_comments(text: str) -> str:
    """★ 剥掉注释 ⟹ ⟹ **保留换行** ⟹ ⟹ 行号仍然对得上。

    ★ ★★ 为什么必须剥（★ 同型第三次）：★ `367` 自己的普查就踩过
    「注释里的 `<button>` 字样被当成真标签」⟹ ⟹ ⟹ ⟹ ⇒ 本批的门禁**也**必须剥。
    """
    text = re.sub(r"\{/\*[\s\S]*?\*/\}", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    text = re.sub(r"/\*[\s\S]*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    text = re.sub(r"//[^\n]*", lambda m: " " * len(m.group(0)), text)
    return text


def scan_tags(text: str):
    """★ 逐字符走 ⟹ ⟹ 找出 JSX 开标签的**完整**属性表（★ 不用 `[^>]*`）。"""
    out = []
    i, n = 0, len(text)
    while i < n:
        j = text.find("<", i)
        if j < 0:
            break
        if text.startswith("<!--", j):
            k = text.find("-->", j)
            i = (k + 3) if k >= 0 else n
            continue
        if text[j + 1:j + 2] == "/" or not text[j + 1:j + 2].isalpha():
            i = j + 1
            continue
        k = j + 1
        while k < n and (text[k].isalnum() or text[k] in "-_:"):
            k += 1
        tag = text[j + 1:k]
        p, depth, quote = k, 0, None
        while p < n:
            ch = text[p]
            if quote:
                if ch == "\\":
                    p += 2
                    continue
                if ch == quote:
                    quote = None
            else:
                if ch in "\"'":
                    quote = ch
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                elif ch == ">" and depth == 0:
                    break
            p += 1
        out.append((tag, text[k:p], j))
        i = p + 1
    return out


def has_prop(attrs: str, name: str) -> bool:
    return re.search(r"(^|[\s{])" + re.escape(name) + r"\s*[=\s/>]", attrs) is not None


def has_behavior_or_inert(attrs: str) -> bool:
    behavior = ("onClick", "onPointerDown", "onMouseDown", "onMouseUp",
                "onDoubleClick", "onChange", "onInput", "onKeyDown", "onSubmit")
    inert = ("data-inert", "disabled", "aria-disabled")
    if any(has_prop(attrs, k) for k in behavior):
        return True
    if has_prop(attrs, "href"):
        return True
    return any(has_prop(attrs, k) for k in inert)


def parse_gates(text: str) -> list[tuple[str, str]]:
    text = strip_comments(text)
    m = re.search(r"^GATES\s*=\s*\[(.*?)^\]", text, re.S | re.M)
    if not m:
        return []
    return re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m.group(1))


def resolve_live_regress() -> tuple[Path | None, list[tuple[str, str]], Path | None]:
    """★ 找出**在用**的回归清单 ⟹ ⟹ ⟹ ⇒ ★ 返回 (路径, 条目, 上一份路径)。

    ★ ★ 判据是「**批次号最大**」⟹ ⟹ ⟹ ⇒ ★ ⟹ 而不是「文件名写死的那个」
    ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 这样每加一批门禁 ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ 本门禁**自动**跟着走
    ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ 而不是每次都要有人记得回来改这里。
    """
    cands: list[tuple[int, Path]] = []
    for path in sorted((ROOT / "docs/research").glob(
            "liblib-canvas-batch*/probes/regress*.py")):
        m = re.search(r"liblib-canvas-batch(\d+)", path.parent.parent.name)
        if m:
            cands.append((int(m.group(1)), path))
    if not cands:
        return None, [], None
    cands.sort(key=lambda item: item[0])
    _live_batch, live_path = cands[-1]
    prev_path = cands[-2][1] if len(cands) >= 2 else None
    return (live_path,
            parse_gates(live_path.read_text(encoding="utf-8")),
            prev_path)


def gates_touching_widened() -> set[tuple[str, str]]:
    """★ ★★ 放宽后的「碰被跟踪源文件」口径。

    ★ ★★ Batch 866 的口径是「门禁**文本里出现**该**文件名**」
      ⟹ ⟹ ⟹ ⟹ ⇒ ★ 对「**按目录扫描**」的门禁**失明**
      ⟹ ⟹ ⟹ ⟹ ⇒ ★ `367` 扫的是整个 `src/components/**` ⟹ ⟹ 从不出现
      ⟹ ⟹ ⟹ ⟹ ⇒ `DirectorViewport.tsx` 这个名字 ⟹ ⟹ ⟹ ⟹ ⇒ 它**没进** 866 的视野
      ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而它**当时已经是红的** ⟹ ⟹ ⟹ ⟹ ⇒ ★ **红的从来没人看见**。
    """
    out: set[tuple[str, str]] = set()
    files = sorted((ROOT / "scripts").glob("verify-liblib-batch*.py")) + \
        sorted((ROOT / "scripts").glob("verify-liblib-batch*.mjs"))
    for p in files:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        hit = (any(r.split("/")[-1] in txt for r in TRACKED_SRC)
               or any(d in txt for d in TRACKED_DIRS)
               or (bool(re.search(r"rglob\(|glob\(", txt)) and "src" in txt))
        if not hit:
            continue
        m = re.match(r"verify-liblib-batch(.+)\.(py|mjs)$", p.name)
        if m:
            out.add((m.group(1), m.group(2)))
    return out


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 868,
        "title": "「看着可点、点了没反应」的那批控件：普查 ＋ 整改 ＋ 上锁",
    }

    # ── S1 运行时证据在库 ─────────────────────────────────────────
    v.check("source:the-runtime-evidence-is-in-the-repo", RUNTIME.exists(),
            detail=str(RUNTIME))
    if RUNTIME.exists():
        try:
            rt = json.loads(RUNTIME.read_text(encoding="utf-8"))
            checks = rt.get("核对", [])
            bad = [c for c in checks if not c.get("通过")]
            audit["运行时核对条数"] = len(checks)
            audit["运行时核对失败"] = len(bad)
            v.check("runtime:every-runtime-check-passed", bool(checks) and not bad,
                    detail={"总条数": len(checks), "失败": [c["判据"] for c in bad]})
        except Exception as e:  # noqa: BLE001
            v.check("runtime:every-runtime-check-passed", False, detail=repr(e))

    # ── S2 ★★ 结构性判据：★ 两处整改点必须真的有 onClick ────────
    per_fix = {}
    for fx in FIXES:
        p = ROOT / fx["relpath"]
        if not p.exists():
            v.check("source:the-fixed-file-%s-exists" % fx["id"], False, detail=str(p))
            continue
        raw = p.read_text(encoding="utf-8")
        code = strip_comments(raw)
        # ★ needle 唯一命中（★ 不写死行号）
        hits = [m.start() for m in re.finditer(re.escape(fx["needle"]), code)]
        # ★ ★★ Batch 868：**判据自身加固**（★ 第一版是假绿 ⟹ ⟹ ⟹ ⟹ ⇒
        #   ★ 第一版：「needle 之后 2000 字符内有没有**任意** onClick」
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而删掉目标那枚按钮的 onClick 之后 ⟹ ⟹ ⟹ ⟹ ⇒
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ **展开面板里那枚**的 onClick 仍在 2000 字符内
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ 负控 N1/N2 **打不红**
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 症状：★ 判据**恒真**
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 修法：★ 用 `scan_tags`
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ **精确解析那个标签自己的属性表**
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ （★ 同一个文件里 S3 就在用）
        wired = False
        tag_attrs = ""
        for tag, attrs, off in scan_tags(code):
            if tag not in ("button", "a"):
                continue
            if fx["needle"] not in attrs:
                continue
            tag_attrs = " ".join(attrs.split())[:200]
            if has_prop(attrs, "onClick"):
                wired = True
            break
        per_fix[fx["id"]] = {"needle": fx["needle"], "命中数": len(hits),
                             "有 onClick": wired, "标签属性表": tag_attrs,
                             "依据": fx["why"],
                             "口径": "★ 用 scan_tags 解析**该标签自己的属性表**"
                                     "（★ 不用「往后 2000 字符」那个宽口径）"}
        v.check("source:the-fixed-control-%s-has-an-onclick" % fx["id"],
                len(hits) == 1 and wired,
                detail=per_fix[fx["id"]])
    audit["两处整改"] = per_fix

    # ── S3 ★★ 导演台零死控件（★ 补上 367 的 CROSS_LINE 盲区）───
    director_dir = ROOT / "src/components/director"
    director_candidates = []
    for p in sorted(director_dir.rglob("*.tsx")):
        raw = p.read_text(encoding="utf-8")
        code = strip_comments(raw)
        for tag, attrs, off in scan_tags(code):
            if tag != "button":
                continue
            if has_behavior_or_inert(attrs):
                continue
            director_candidates.append({
                "file": str(p.relative_to(ROOT)),
                "line": raw[:off].count("\n") + 1,
                "attrs": " ".join(attrs.split())[:160],
            })
    audit["导演台死控件候选"] = director_candidates
    v.check("source:the-director-desk-has-no-dead-buttons",
            not director_candidates,
            detail={"候选": director_candidates,
                    "范围": "src/components/director/**（★ 367 因 CROSS_LINE 跳过了这整片）"})

    # ── S4 ★★ 清单不许再有洞（★ 放宽口径）────────────────────────
    live_regress, gates, prev_regress = resolve_live_regress()
    listed = set(gates)
    touching = gates_touching_widened()
    gap = sorted(touching - listed)
    audit["放宽口径命中"] = len(touching)
    audit["回归清单条数"] = len(listed)
    audit["在用回归清单"] = str(live_regress) if live_regress else None
    audit["历史快照（本门禁当初那份）"] = str(HISTORIC_REGRESS)
    audit["覆盖缺口"] = ["%s.%s" % g for g in gap]
    v.check("source:every-gate-touching-the-tracked-sources-is-listed",
            not gap,
            detail={"缺口": ["%s.%s" % g for g in gap],
                    "口径": "★ 文件名 ∪ 目录名 ∪ src 上的 glob/rglob",
                    "说明": "★ 这些门禁**碰**导演台源文件 ⟹ ⟹ 它们的红**不能藏**"})

    # ★ ★★ Batch 869：★ 「在用清单」**必须**是批次号最大的那一份 ⟹ ⟹ ⟹ ⇒ ★
    #   ⟹ 否则「写死文件名」的老毛病会从别的入口长回来。
    v.check("source:the-live-regression-list-is-the-newest-one",
            live_regress is not None
            and (prev_regress is None
                 or live_regress.parent.parent.name
                 > prev_regress.parent.parent.name)
            # ★ ★★ 第三条（★ 本批负控逼出来的）：★ 光比「上一份」**不够** ——
            # ★   一旦有人把清单**写死回本门禁当初那份快照** ⟹ ⟹ ⟹ ⟹ ⇒ ★
            # ★   `prev_regress` 就变成 **None** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 前两条仍然成立
            # ★   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 判据**照样绿** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 于是它**没有牙**。
            # ★   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 修法＝**同时**要求「在用清单比本门禁的**历史快照**
            # ★   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 更**新**」⟹ ⟹ ⟹ ⟹ ⇒ ★ 写死回去就必然红。
            and live_regress.parent.parent.name
            > HISTORIC_REGRESS.parent.parent.name,
            detail={"在用": str(live_regress), "上一份": str(prev_regress),
                    "本门禁的历史快照": str(HISTORIC_REGRESS),
                    "★ 说明": "★ 判据是「批次号最大」⟹ ⟹ 且必须**新于**本门禁"
                              "的历史快照 ⟹ ⟹ 写死回去就红"})

    # ★ ★★ Batch 869：★ 清单**只能增长** ⟹ ⟹ ⟹ ⇒ ★ ⟹ 缩水了就必须报出来
    #   ⟹ ⟹ ⟹ ⇒ ★ ⟹ （★ 否则某批「重写清单」时手抖删掉几十条 ⟹ ⟹ ⟹ ⇒ ★ ⟹
    #   ⟹ ⟹ ⟹ ⇒ ★ ⟹ 那些门禁的红**又没人看了** ⟹ ⟹ ⟹ ⇒ ★ ⟹ 且没有任何痕迹）
    if live_regress is not None and prev_regress is not None:
        prev_gates = parse_gates(prev_regress.read_text(encoding="utf-8"))
        shrunk = sorted(set(prev_gates) - set(gates))
        v.check("source:the-regression-list-never-shrinks",
                not shrunk,
                detail={"上一份条数": len(prev_gates), "在用条数": len(gates),
                        "被删掉的条目": ["%s.%s" % g for g in shrunk],
                        "★ 说明": "★ 清单只增不减 ⟹ ⟹ 缩水必须报出来"})

    # ── S5 ★ 静态普查在库 ⟹ ⟹ 且候选全在已登记白名单 ─────────────
    v.check("source:the-static-scan-evidence-is-in-the-repo", STATIC.exists(),
            detail=str(STATIC))
    if STATIC.exists():
        try:
            st = json.loads(STATIC.read_text(encoding="utf-8"))
            found = set()
            for c in st.get("候选", []):
                found.add((c["file"], int(c["line"])))
            unexpected = sorted(found - ALLOWED_UNREACHABLE)
            audit["静态普查候选"] = ["%s:%d" % c for c in sorted(found)]
            audit["静态普查未登记"] = ["%s:%d" % c for c in unexpected]
            v.check("source:every-static-candidate-is-registered",
                    not unexpected,
                    detail={"未登记": ["%s:%d" % c for c in unexpected],
                            "已登记": ["%s:%d" % c for c in sorted(found)]})
        except Exception as e:  # noqa: BLE001
            v.check("source:every-static-candidate-is-registered", False, detail=repr(e))

    # ── S6 ★ 新门禁基线在库 ───────────────────────────────────────
    v.check("source:the-new-gates-baseline-is-in-the-repo", NEWGATES.exists(),
            detail=str(NEWGATES))
    if NEWGATES.exists():
        try:
            ng = json.loads(NEWGATES.read_text(encoding="utf-8"))
            audit["清单外门禁数"] = ng.get("清单外")
            audit["其中红的"] = ng.get("红")
            v.check("source:the-new-gates-baseline-was-taken",
                    bool(ng.get("逐条")),
                    detail={"条数": len(ng.get("逐条", [])),
                            "红": ng.get("红")})
        except Exception as e:  # noqa: BLE001
            v.check("source:the-new-gates-baseline-was-taken", False, detail=repr(e))

    v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print(f"\n{v.count} 判据，{len(v.failures)} 失败")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
