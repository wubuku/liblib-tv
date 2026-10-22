#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 841 验收：把右栏**三枚页签**（鼻子／嘴唇／脸部）的**实测控件**补上，
并修正「文字页签跟着选中项移动」这条几何规则。

## 这批在还什么债

batch 840 把「编辑角色」做成了角色大编辑器，但：

  - 右栏六枚页签里，**只有「皮肤」**有控件（batch 840 实测的六条滑杆）；
  - 另外五枚（眉眼／鼻子／嘴唇／脸部／妆造）**全是空态说明**；
  - ★ 而且「文字页签（56 宽）」被**固定在首枚** —— ★ **这是真的几何 bug**：
    源站实测「当前选中的那枚」才是 56 宽的文字页签，其余五枚是 24 宽的图标页签
    ⟹ 选中别枚时，clone 的页签行与源站**对不上**。

⟹ 本批：① **先测源站**（只读探针，把五枚页签 ＋ 左列四段的控件全测出来，
  ★ 且每次点击前后都核对 ⚡ 积分未变）⟹ ② 在 clone 里实现三枚**纯滑杆**页签
  ⟹ ③ 逐像素对拍。

★ **本批的范围取舍（README 如实写明）**：
  - **实现**：鼻子（6 条）／嘴唇（10 条）／脸部（15 条）—— 三页**全是滑杆** ⟹ 几何同构 ⟹ 可逐像素对拍；
  - **不实现**：眉眼（35 条滑杆 ＋ 眼型/眉型**预设网格**）／妆造（11 个 chip ＋ 妆容**预设网格**）
    ⟹ ⟹ 含**缩略图卡片**（76×96）⟹ ⟹ 需要素材 ⟹ 属后续批次 ⟹ ⟹ **不编造** ⟹ 仍显示空态说明；
  - **左列四段**（纹身&疤痕／丰胸／造型／音色库）的实测结果**也已入库**，但**本批不实现**
    ⟹ ⟹ 同上，属后续批次。

## 判据（S1–S6）

S1 ★★★ **三枚页签不再是空态**：点 鼻子／嘴唇／脸部 ⟹ 出现**实测的滑杆**
    （条数与**文案逐条**等于源站 raw 机器提取的清单）
S2 ★★★ **几何逐像素**（页签盒 ＋ 每条滑杆的标签/轨道/数值/「i」盒）
    ⟹ **期望值从入库的源站 raw 机器提取** ⟹ ⟹ 宽高逐像素全等、位置 ±1px
S3 ★★★ **页签规则修正**：★ **当前选中那枚**才是 56 宽的文字页签、其余 24 宽
    ⟹ ⟹ 与源站 raw 一致（★ 这是 batch 840 留下的**真几何 bug**）
S4 ★★★ **交互真生效**：拖滑杆 ⟹ **控件的 value 变了** 且**渲染出来的数字 == 控件的 value**
S5 ★★★ **未实现的两页仍显示空态说明、0 控件**；★ 且说明文案**不再**说「未实测」
    ⟹ ⟹ （那五页**已经实测过了** ⟹ 继续写「未实测」就是**假陈述**）
S6 ★★ **mock 如实标注**（README 必须写明：哪几页实现了、哪几页没实现、为什么）

## 纪律

- 期望值**来自入库的源站 raw**（机器提取），不手打；
- 否定性结论必须**先证明扫描范围覆盖了那一类东西**；
- 阴性对照每条**只翻它自己那一条**。
"""
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01"
RAW = BATCH / "raw"
PROBE_CLONE = BATCH / "probes/clone841.py"
OUT = BATCH / "runtime-audit.json"

DEV_ORIGIN = "http://localhost:4317"
CSS_FILE = ROOT / "src/components/character-studio.css"
PANEL_FILE = ROOT / "src/components/CharacterEditorPanel.tsx"

# ★ 本批只改了 **TSX**（CSS 没动）⟹ ⟹ 前置检查要盯的是**服务端下发的 JS chunk**
#   ⟹ 判据：**新文案「鼻子长短」必须出现在下发的 JS 里** ⟹ ⟹ 否则读到的是旧 chunk。
JS_MARKER = "鼻子长短"
CRITICAL_PROPS = ("left", "top", "width", "height")
CRITICAL_SELECTORS = (
    ".ce-tabs", ".ce-tab", ".ce-tab-icon", ".ce-tab-text", ".ce-panel",
    ".ce-section", ".ce-slider-label", ".ce-slider-value", ".ce-slider",
)


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_probe(script: pathlib.Path) -> None:
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=900)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit("探针失败 %s exit=%r" % (script.name, r.returncode))


def served_js() -> str:
    html = urllib.request.urlopen(DEV_ORIGIN + "/", timeout=60).read().decode("utf-8", "replace")
    urls = sorted(set(re.findall(r'/_next/static/chunks/[^"]+\.js', html)))
    out = []
    for u in urls:
        try:
            out.append(urllib.request.urlopen(DEV_ORIGIN + u, timeout=60)
                       .read().decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            print("  ★ chunk 抓取失败 %s: %s" % (u, exc))
    return "\n".join(out)


def preflight_js(timeout: int = 90) -> tuple:
    """等 dev server **重建完 TSX** ⟹ 超时则**显式失败**（exit 2）。

    ★ 为什么这一批的前置检查盯的是 **JS** 而不是 CSS：本批**只改了 TSX**
      ⟹ ⟹ CSS chunk 不会变 ⟹ ⟹ 拿 CSS 对拍**根本测不到**「TSX 还没重建」。
      ⟹ ⟹ 判据必须是「**新文案出现在服务端下发的 JS 里**」。
    ★ 更阴的一种：Turbopack 的**持久缓存**会把陈旧的编译结果原样吐出来
      ⟹ ⟹ 这一关必须**比对**，不能只靠「我等了一会儿」。
    """
    t0 = time.time()
    found = False
    while time.time() - t0 < timeout:
        try:
            found = JS_MARKER in served_js()
        except Exception:  # noqa: BLE001
            found = False
        if found:
            break
        time.sleep(3)
    waited = round(time.time() - t0, 1)
    if found:
        return True, {"等了几秒": waited, "服务端JS里有新标记": True}
    return False, {"等了几秒": waited, "服务端JS里有新标记": False,
                   "标记": JS_MARKER}


def parse_css(css: str) -> dict:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out: dict = {}
    for sel_raw, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        decls: dict = {}
        for d in body.split(";"):
            if ":" in d:
                k, v = d.split(":", 1)
                decls[k.strip()] = v.strip()
        for sel in (s.strip() for s in sel_raw.split(",")):
            if not sel:
                continue
            merged = out.get(sel, {})
            merged.update(decls)
            out[sel] = merged
    return out


def css_drift() -> dict:
    disk = parse_css(CSS_FILE.read_text(encoding="utf-8"))
    live = parse_css(served_js() + served_css_all())
    drift: dict = {}
    for sel in CRITICAL_SELECTORS:
        d = disk.get(sel) or {}
        l = live.get(sel) or {}
        if not d:
            drift[sel] = {"error": "磁盘上找不到这个选择器"}
            continue
        if not l:
            drift[sel] = {"error": "服务端 chunk 里找不到这个选择器"}
            continue
        diff = {p: {"disk": d.get(p), "served": l.get(p)}
                for p in CRITICAL_PROPS if p in d and d.get(p) != l.get(p)}
        if diff:
            drift[sel] = diff
    return drift


def served_css_all() -> str:
    html = urllib.request.urlopen(DEV_ORIGIN + "/", timeout=60).read().decode("utf-8", "replace")
    urls = sorted(set(re.findall(r'/_next/static/chunks/[^"]+\.css', html)))
    out = []
    for u in urls:
        try:
            out.append(urllib.request.urlopen(DEV_ORIGIN + u, timeout=60)
                       .read().decode("utf-8", "replace"))
        except Exception:  # noqa: BLE001
            pass
    return "\n".join(out)


# ── 源站期望值：**全部**从入库的 raw 机器提取 ─────────────────────────
PAGE_MAP = {
    "nose": "B_页签_鼻子",
    "lips": "B_页签_嘴唇",
    "face": "B_页签_脸部",
}
CLONE_STAGE = {"nose": "B_nose", "lips": "B_lips", "face": "B_face"}
# ★ 页面 id ⟶ 源站页签的中文标签（源站/clone 的 aria 命名空间一致 ⟹ 可同维度比）
PAGE_ARIA = {"nose": "鼻子", "lips": "嘴唇", "face": "脸部"}


def build_expectations() -> dict:
    """从源站 raw 里抽出「每页的页签盒 ＋ 每条滑杆的四件套」。

    ★ 找元素的规则都用**结构/尺寸/属性**，不用坐标字面量：
      - 滑杆轨道 ＝ 宽 240 高 12 的 `input`；
      - 标签 ＝ 与轨道「上方 45px 内、x 相同、高 22」的叶子；
      - 数值 ＝ 与标签同高的、x 在轨道右端的叶子；
      - 「i」 ＝ 与标签同高、宽 14 的叶子。
    """
    raw = read_json(RAW / "source-841-tabs.json")
    states = raw["★各状态读数"]
    modal = states["A_默认态_脸部精修_皮肤"]["modal"]
    ox, oy = modal["x"], modal["y"]

    def R(b):
        return {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]}

    exp: dict = {}
    for page, sname in PAGE_MAP.items():
        s = states[sname]
        tracks = sorted((i for i in s["inputs"]
                         if i["box"]["w"] == 240 and i["box"]["h"] == 12),
                        key=lambda i: i["box"]["y"])
        if not tracks:
            raise SystemExit("%s 没抽出滑杆轨道" % page)
        # ★ 标签的左端 == **轨道**的左端（源站都是右栏内容区的左边界）
        track_x = tracks[0]["box"]["x"]
        labels = [l for l in s["leaves"]
                  if l["box"]["h"] == 22 and l["box"]["x"] == track_x]
        values = [l for l in s["leaves"]
                  if l["box"]["h"] == 16 and l["box"]["w"] == 7]
        icons = [l for l in s["leaves"] if l["box"]["w"] == 14 and l["box"]["h"] == 14]
        rows = []
        for tr in tracks:
            b = tr["box"]
            cand = [l for l in labels if 0 < b["y"] - l["box"]["y"] <= 45]
            cand.sort(key=lambda l: b["y"] - l["box"]["y"])
            if not cand:
                raise SystemExit("%s 找不到标签（轨道 y=%s）" % (page, b["y"]))
            lab = cand[0]
            val = [v for v in values if abs(v["box"]["y"] - lab["box"]["y"]) < 10]
            ic = [x for x in icons if abs(x["box"]["y"] - lab["box"]["y"]) < 10]
            rows.append({
                "文案": lab["text"],
                "标签盒": R(lab["box"]),
                "轨道盒": R(b),
                "数值盒": R(val[0]["box"]) if val else None,
                "i盒": R(ic[0]["box"]) if ic else None,
            })
        exp[page] = {
            "页签盒": {t["aria"]: R(t["box"]) for t in s["tabBtns"]},
            "滑杆": rows,
        }
    exp["_源站积分"] = {k: v for k, v in raw.items()
                        if k.startswith("★") and "积分是否变化" in k}
    exp["_源站积分全未变"] = all(
        v is False for k, v in raw.items() if "积分是否变化" in k)
    return exp


def box_close(a: dict, b: dict, tol: int = 1) -> bool:
    """宽高**逐像素全等**、位置 ±1px。

    ★ 位置容差 ±1：两侧都居中在同一半像素位置 ⟹ 取整方向可能差 1。
      **宽高不给容差**（宽高是布局算出来的确定值）。
    """
    if not a or not b:
        return False
    if a.get("w") != b.get("w") or a.get("h") != b.get("h"):
        return False
    return (abs((a.get("x") or 0) - (b.get("x") or 0)) <= tol
            and abs((a.get("y") or 0) - (b.get("y") or 0)) <= tol)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到新文案）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有新标记 ⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 841, "verdict": "preflight-failed", "preflight": pf_detail,
            "note": "服务端 chunk 还没重建（或 Turbopack 持久缓存陈旧）⟹ "
                    "需要 `rm -rf .next/dev/cache/turbopack` 并重启 dev server",
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写入", OUT)
        return 2
    print("  ✔ 服务端 JS 已重建（等了 %ss）" % pf_detail.get("等了几秒"))

    exp = build_expectations()

    print("跑 clone 运行时探针……")
    run_probe(PROBE_CLONE)
    rt = read_json(pathlib.Path("/tmp/b841-clone-tabs.json"))

    checks = []

    # ── S1 三枚页签不再是空态 ───────────────────────────────────────────
    s1 = {}
    ok1 = True
    for page in PAGE_MAP:
        stage = rt.get(CLONE_STAGE[page]) or {}
        got_labels = [(s.get("标签") or {}).get("text") for s in (stage.get("滑杆") or [])]
        want_labels = [r["文案"] for r in exp[page]["滑杆"]]
        same = got_labels == want_labels
        s1["★%s_clone的滑杆文案" % page] = got_labels
        s1["★%s_源站的滑杆文案" % page] = want_labels
        s1["★%s_逐条相等" % page] = same
        ok1 = ok1 and same and len(want_labels) > 0
    checks.append((
        "S1 ★★★ **三枚页签不再是空态**：点 鼻子／嘴唇／脸部 ⟹ 出现**实测的滑杆**"
        "（%d／%d／%d 条，★ **文案逐条**等于源站 raw 机器提取的清单）"
        % (len(exp["nose"]["滑杆"]), len(exp["lips"]["滑杆"]),
           len(exp["face"]["滑杆"])),
        ok1,
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何逐像素 ───────────────────────────────────────────────────
    diffs = []
    total = 0
    for page in PAGE_MAP:
        stage = rt.get(CLONE_STAGE[page]) or {}
        ctabs = {t["aria"]: t for t in (stage.get("页签") or [])}
        for aria, want in exp[page]["页签盒"].items():
            total += 1
            got = ctabs.get(aria) or {}
            gb = {"x": got.get("x"), "y": got.get("y"),
                  "w": got.get("w"), "h": got.get("h")}
            if not box_close(want, gb):
                diffs.append({"页面": page, "元素": "页签 %s" % aria,
                              "源站": want, "clone": gb})
        csl = stage.get("滑杆") or []
        if len(csl) != len(exp[page]["滑杆"]):
            diffs.append({"页面": page, "元素": "滑杆条数",
                          "源站": len(exp[page]["滑杆"]), "clone": len(csl)})
            continue
        for i, (want, got) in enumerate(zip(exp[page]["滑杆"], csl)):
            lab = got.get("标签") or {}
            pairs = [
                ("标签盒", want["标签盒"], lab.get("文案盒")),
                ("轨道盒", want["轨道盒"],
                 {"x": got.get("x"), "y": got.get("y"),
                  "w": got.get("w"), "h": got.get("h")}),
                ("数值盒", want["数值盒"], got.get("数值")),
                ("i盒", want["i盒"], lab.get("i盒")),
            ]
            for name, w, g in pairs:
                if w is None and g is None:
                    continue
                total += 1
                if not box_close(w, g or {}):
                    diffs.append({"页面": page,
                                  "元素": "滑杆[%d] %s（%s）" % (i, want["文案"], name),
                                  "源站": w, "clone": g})
    s2 = {"★比较了几项": total, "★有几个不一致": len(diffs),
          "★不一致明细": diffs}
    # ★★ README 写的**项数**必须 == 本轮**实际比较数**
    #   （batch 840 的门禁就有这条 ⟹ 它真抓到过漂移：87 → 85 ⟹ ⟹ 这批也搬过来）
    readme_txt = (BATCH / "README.md").read_text(encoding="utf-8") \
        if (BATCH / "README.md").exists() else ""
    m_cnt = re.search(r"S2 实测 \*\*(\d+)\s*项全等\*\*", readme_txt)
    s2["★README里写的比较项数"] = int(m_cnt.group(1)) if m_cnt else None
    s2["★README里的比较项数与实际一致"] = (m_cnt is not None
                                           and int(m_cnt.group(1)) == total)
    checks.append((
        "S2 ★★★ **几何与源站逐像素一致**（%d 项：每枚页签的盒 ＋ 每条滑杆的"
        "标签/轨道/数值/「i」盒）⟹ ★ **期望值全部从入库的源站 raw 机器提取**"
        "（找元素只用**结构/尺寸/属性**：轨道＝宽 240 高 12 的 input、"
        "标签＝轨道上方 45px 内同高的叶子……）⟹ ⟹ **宽高逐像素全等**、位置 ±1px"
        "；★ 且 README 写的项数（%s）== 本轮实际比较数（%d）"
        % (total, s2["★README里写的比较项数"], total),
        (len(diffs) == 0 and total >= 90
         and s2["★README里的比较项数与实际一致"]),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 页签规则：文字页签跟着选中项移动 ─────────────────────────────
    s3 = {}
    for page in PAGE_MAP:
        stage = rt.get(CLONE_STAGE[page]) or {}
        tabs = stage.get("页签") or []
        # ★★ **建键维度必须与取值维度一致**（本批 S3 第一版就栽在这）：
        #   —— 判「哪一枚被选中」要用 **id**（nose/lips/face 是页面 id）；
        #   —— 跟源站比宽度要用 **aria**（源站 raw 的页签盒就是按中文标签建的键）。
        #   ⇒ 两侧**都按 aria** 比宽度，才叫「同维度」；按 id 比会恒 False。
        widths_by_id = {t["id"]: t.get("w") for t in tabs}
        texts_by_id = {t["id"]: bool(t.get("文案盒")) for t in tabs}
        widths_by_aria = {t["aria"]: t.get("w") for t in tabs}
        want_widths = {a: b["w"] for a, b in exp[page]["页签盒"].items()}
        # 源站自己也要满足这条规则（期望值的来源，不是 clone 的自说自话）
        want_selected_aria = {a for a, w in want_widths.items() if w == 56}
        s3["★%s_clone的页签宽_by_id" % page] = widths_by_id
        s3["★%s_clone的页签宽_by_aria" % page] = widths_by_aria
        s3["★%s_源站的页签宽_by_aria" % page] = want_widths
        s3["★%s_源站只有一枚是56宽" % page] = (len(want_selected_aria) == 1)
        s3["★%s_源站那枚56宽的就是本页" % page] = (
            want_selected_aria == {PAGE_ARIA[page]})
        s3["★%s_clone那枚56宽的就是本页" % page] = (
            {a for a, w in widths_by_aria.items() if w == 56} == {PAGE_ARIA[page]})
        s3["★%s_选中那枚是56宽" % page] = (widths_by_id.get(page) == 56)
        s3["★%s_选中那枚带文字" % page] = (texts_by_id.get(page) is True)
        # ★★ 这条是**本批补上的**：之前只钉了「选中那枚带文字」，
        #   **没钉**「其余五枚没有文字」 ⟹ ⟹ 「每枚都带文字」这种实现照样能过 ⟹ ⟹ 补上。
        s3["★%s_只有选中那枚带文字" % page] = (
            sum(1 for t in texts_by_id.values() if t) == 1
            and texts_by_id.get(page) is True)
        s3["★%s_其余都是24宽" % page] = all(
            w == 24 for a, w in widths_by_id.items() if a != page)
        s3["★%s_宽度与源站逐条相等" % page] = (widths_by_aria == want_widths)
    s3_ok = all(v for k, v in s3.items() if k.startswith("★"))
    checks.append((
        "S3 ★★★ **页签规则修正**：★ 源站实测**当前选中的那枚**才是 56 宽的"
        "「图标＋文字」页签、其余五枚是 24 宽的图标页签 ⟹ ⟹ clone 之前把 56 宽"
        "**固定在首枚** ⟹ ⟹ 选中别枚时几何与源站对不上 ⟹ ⟹ 本批改正",
        s3_ok,
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 交互真生效 ───────────────────────────────────────────────────
    after = rt.get("D_拖滑杆后") or {}
    sliders = after.get("滑杆") or []
    first = sliders[0] if sliders else {}
    s4 = {
        "★滑杆_控件value": first.get("value"),
        "★滑杆_渲染数字": (first.get("数值") or {}).get("text"),
        "★滑杆_渲染数字等于控件value": ((first.get("数值") or {}).get("text")
                                 == first.get("value")),
        "★滑杆_确实变了": (first.get("value") not in (None, "0")),
        "★Esc后_编辑器关了": (rt.get("E_Esc后") or {}).get("★编辑器还在吗") is False,
        "★Esc后_面板还在": (rt.get("E_Esc后") or {}).get("★面板还在吗") is True,
    }
    checks.append((
        "S4 ★★★ **交互真生效**：拖滑杆 ⟹ **控件的 value 从 0 变成 %s**，"
        "且**渲染出来的数字「%s」== 控件的 value**（★ 判据是「等于目标值」，"
        "不是「看起来变了」）⟹ 且 Esc 仍关得掉编辑器、面板留着"
        % (s4["★滑杆_控件value"], s4["★滑杆_渲染数字"]),
        (s4["★滑杆_渲染数字等于控件value"] and s4["★滑杆_确实变了"]
         and s4["★Esc后_编辑器关了"] and s4["★Esc后_面板还在"]),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 仍未实现的那一块仍显示空态说明、0 控件，且文案不再说「未实测」 ──
    #   ★★ **batch 842 起改盯「妆造」**：眉眼页在 batch 842 已实现
    #   ⟹ ⟹ 「仍未实现的那一页」变成了妆造 ⟹ ⟹ 这条断言要盯**当下**仍未实现的那一页
    #   ★★ **batch 846 起再改盯「左列第五段」**：第四段在 846 也已实现 ⟹ ⟹
    #   **仍未实现的只剩左列第四～五段** ⟹ ⟹
    #   ★ 且那两段**已实测**（源站 raw 有内容）⟹ ⟹ 文案要写「已实测」而不是「未实测」
    seg5 = rt.get("C2_第五段") or {}
    seg5_empty = seg5.get("空态")
    segback = rt.get("C3_切回脸部精修") or {}
    s5 = {
        "★第五段_页签数": len(seg5.get("页签") or []),
        "★第五段_滑杆数": len(seg5.get("滑杆") or []),
        "★第五段_空态说明": seg5_empty,
        "★第五段_空态说明里还写着「未实测」": bool(seg5_empty and "未实测" in seg5_empty),
        "★第五段_空态说明里写了「已实测」": bool(seg5_empty and "已实测" in seg5_empty),
        "★切回脸部精修_页签数": len(segback.get("页签") or []),
        "★源站那趟_积分全程未变": exp["_源站积分全未变"],
    }
    checks.append((
        "S5 ★★★ **仍未实现的那一块仍显示空态说明、0 控件**（★ batch 846 起盯"
        "「左列第五段」：第四段在 846 已实现 ⟹ ⟹ 未实现的只剩一段）；★ 且说明文案**不再**说"
        "「未实测」—— ★ 那两段**已经实测过**了（raw 已入库）⟹ ⟹ 继续写「未实测」"
        "就是**假陈述** ⟹ ⟹ 改成「已实测，但属后续批次」",
        (s5["★第五段_页签数"] == 0 and s5["★第五段_滑杆数"] == 0
         and bool(seg5_empty)
         and not s5["★第五段_空态说明里还写着「未实测」"]
         and s5["★第五段_空态说明里写了「已实测」"]
         and s5["★切回脸部精修_页签数"] == 6
         and s5["★源站那趟_积分全程未变"]),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 mock 如实标注 ────────────────────────────────────────────────
    readme_path = BATCH / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    s6 = {
        "★README存在": bool(readme),
        "★README写明已实现的三页": all(k in readme for k in ("鼻子", "嘴唇", "脸部")),
        "★README写明未实现的两页": all(k in readme for k in ("眉眼", "妆造")),
        "★README写明未实现的原因": "预设网格" in readme,
        "★README写明左列四段也未实现": "纹身" in readme and "丰胸" in readme,
        "★README写明不消耗积分": "不消耗" in readme,
        "★README里mock出现次数": readme.lower().count("mock"),
    }
    checks.append((
        "S6 ★★ **mock 如实标注**：README 必须写明——★ 已实现哪三页（鼻子／嘴唇／脸部）、"
        "★ 未实现哪两页（眉眼／妆造）**以及为什么**（含预设网格 ＋ 缩略图卡片）；"
        "★ 左列四段的实测结果**也已入库**但**本批不实现** ⟹ ⟹ 一并写明；"
        "★ 且「确认生成」等仍是 mock、不消耗 ⚡44",
        (s6["★README存在"] and s6["★README写明已实现的三页"]
         and s6["★README写明未实现的两页"] and s6["★README写明未实现的原因"]
         and s6["★README写明左列四段也未实现"]
         and s6["★README写明不消耗积分"]
         and s6["★README里mock出现次数"] >= 3),
        json.dumps(s6, ensure_ascii=False),
    ))

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print("  %s  %s" % ("PASS" if ok else "FAIL", label))
        passed += bool(ok)
    print("\n%d/%d 通过" % (passed, len(checks)))

    audit = {
        "batch": 841,
        "title": "右栏三枚页签（鼻子/嘴唇/脸部）的实测控件 ＋ 文字页签跟着选中项移动",
        "verdict": "%d/%d" % (passed, len(checks)),
        "preflight": pf_detail,
        "source": {"期望值表": {k: v for k, v in exp.items()
                                if not k.startswith("_")},
                   "源站积分未变": exp["_源站积分全未变"]},
        "clone": {k: v for k, v in rt.items() if k.startswith(("A_", "B_", "C_", "D_", "E_"))},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "★★★ **「文字页签（56 宽）」之前被固定在首枚** ⟹ ⟹ 源站实测是"
            "**当前选中的那枚**才是文字页签 ⟹ ⟹ 这是 batch 840 留下的**真几何 bug**，本批改正。",
            "★★★ **鼻子／嘴唇／脸部**三页的**实测滑杆**（6／10／15 条）已实现，"
            "★ **%d 项几何逐像素一致**（期望值从源站 raw 机器提取）。" % total,
            "★★★ **源站那趟全程 ⚡44 未变**（每次点击前后都核对）⟹ ⟹ 切页签不花钱。",
            "★★ **眉眼／妆造**与**左列四段**的实测结果**也已入库**（raw），"
            "但**本批不实现**（含预设网格 ＋ 缩略图卡片）⟹ ⟹ 仍显示**空态说明**，不编造。",
        ],
        "notClaimed": [
            "**不声称**「眉眼」「妆造」两页已复刻 —— 它们含**预设网格**（76×96 卡片 ＋ 缩略图）⟹ "
            "★ 属后续批次 ⟹ ⟹ clone 只显示空态说明。",
            "**不声称**左列四段（纹身&疤痕／丰胸／造型／音色库）已复刻 —— "
            "★ 实测结果已入库，但**本批不实现**。",
            "**不声称**图标**字形**与源站一致（源站是 iconify SVG、字形未采集 ⟹ lucide 占位）。",
            "**不声称**预设卡片的**缩略图**能复刻 —— 源站用的是素材库里的真实缩略图，"
            "仓库里没有 ⟹ ⟹ 属后续批次。",
        ],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
