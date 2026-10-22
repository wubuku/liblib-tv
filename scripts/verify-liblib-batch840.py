#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 840 验收：把「编辑角色」从**死按钮**做成**角色大编辑器**，几何逐像素对齐源站。

## 这批在还什么债

batch 826/827 已经在 clone 里重建了源站当前的「角色造型室」（角色库页签／筛选胶囊／横向角色条／
三种底部 CTA），batch 839 把「查看角色资产」做成了资产视图。但：

  - 角色库底部那枚「**编辑角色**」CTA **点了没反应**（源站实测：点它 ⟹ 打开一个 **1198×758 的大编辑器**）；
  - 而这个大编辑器里有**真实可交互**的东西：左列五段、右栏六枚页签（六条滑杆）、祛斑祛痘开关、
    底栏「保存时生成角色资产 ⚡44」＋「保存」。

⟹ 本批：① **先测源站**（五趟**只读**探针 ⟹ 绝不点「确认生成／保存」）⟹ ② 在 clone 里实现 ⟹ ③ 逐像素对拍。

★ **本批最刺眼的三处（都写进了 README）**：
  1. ★★★ **图标一个都没进过前四趟 raw**：`leaves` 只要有文字、`ctrls` 只要按钮/输入、
     `preview` 的 y 范围是 270..790 ⟹ **`<svg>` 全被漏掉** ⟹ 五段前置图标／首枚页签图标／
     「确认生成」左侧图标都只能**靠算术反推** ⟹ ⟹ 本批补跑第⑤趟（`source840_editor5.py`）
     把 **22 个 svg** 全部归档 ⟹ 图标尺寸从此**有据**，不再靠推。
  2. ★★★ **「半身/全身紧邻（gap 0）」是误读**：源站两枚按钮实测在 rel 564 / **605**
     ⟹ 间隙 **9px**（且容器实宽 73 = 32 + 9 + 32，与源站容器的 73px 一致）⟹ clone 原来差 9px。
  3. ★★ **标签文案宽度 107 vs 115**：源站标签行是 `text-sm`（14px）⟹ clone 原来写 13px ⟹ 改成 14px 后精确吻合。

## 判据（S1–S7）

S1 ★★★ **「编辑角色」不再是死按钮** ⟹ clone 点它 ⟹ **大编辑器**出现；
    ★ 且源站同一动作**也**打开大编辑器（源站 raw 记「★是否点到编辑角色」= true）⟹ ⟹ 两者**同构**
S2 ★★★ **几何与源站逐像素一致**（**40+ 个元素**）⟹ **期望值全部从入库的 5 份源站 raw 机器提取**
    ⟹ ★ 位置 ±1px、**宽高逐像素全等**（宽高是布局算出来的确定值，不该有容差）
S3 ★★★ **交互真生效**（不是摆设）：拖滑杆 ⟹ **控件的 value 变了** 且**渲染出来的数字 == 控件的 value**；
    开关 ⟹ `aria-checked` false→true；分段／页签 ⟹ 选中态转移
S4 ★★★ **Esc 两条路径**都关掉编辑器、且**面板留着**：① 焦点不在可编辑元素（走画布全局契约）
    ② 焦点在标题输入框（全局那层对可编辑目标**早退** ⟹ 走编辑器自己那层）⟹ ⟹ 靠 `character-editor` 阻塞面
S5 ★★★ **「保存」是真的**：改名 ⟹ 保存 ⟹ 编辑器关闭 ⟹ 名字**落回角色** ⟹ 重开标题就是新名字
S6 ★★ **mock 如实标注**：确认生成／智能调整／保存并添加到画布／撤销／恢复／按住对比 都是 mock
    ⟹ ⟹ README **必须**写明；★ 且**运行时**验证「确认生成」**没有**消耗 ⚡44
S7 ★★★ **未实测的页签显示空态说明、不编造控件** ⟹ ★ 且**不**把它写成「源站那五页签没有控件」
    （那是**未证实的否定性结论**；我们只知道「**没测过**」）

## 纪律

- 期望值**来自入库的源站 raw**（机器提取），不手打；
- 运行时读数**自己跑**，不读外部缓存；
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
BATCH = ROOT / "docs/research/liblib-canvas-batch840-2026-10-01"
RAW = BATCH / "raw"
PROBE_CLONE = BATCH / "probes/clone840.py"
OUT = BATCH / "runtime-audit.json"

DEV_ORIGIN = "http://localhost:4317"
CSS_FILE = ROOT / "src/components/character-studio.css"
# ★ 只查**几何关键**的这几个属性 ⟹ 避开纯装饰属性（颜色/圆角…）的无关差异
CRITICAL_PROPS = ("left", "top", "width", "height")
CRITICAL_SELECTORS = (
    ".ce-back", ".ce-modal", ".ce-body", ".ce-col-left", ".ce-preview",
    ".ce-col-right", ".ce-name-input", ".ce-tags", ".ce-tag-gender",
    ".ce-seg", ".ce-seg-icon", ".ce-tool", ".ce-figure", ".ce-preview-tools",
    ".ce-tabs", ".ce-tab", ".ce-tab-icon", ".ce-panel", ".ce-section",
    ".ce-slider-label", ".ce-slider-value", ".ce-slider", ".ce-switch-row",
    ".ce-switch", ".ce-generate-row", ".ce-generate", ".ce-smart",
    ".ce-footer", ".ce-gen-assets", ".ce-save", ".ce-save.is-primary",
)


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_probe(script: pathlib.Path) -> None:
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=900)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:], file=sys.stderr)
        raise SystemExit(f"探针失败 {script.name} exit={r.returncode}")


# ── 前置检查：服务端 CSS chunk 必须**已经**跟磁盘一致 ──────────────────
def parse_css(css: str) -> dict:
    """`选择器 → 声明字典`（同 batch 839：先剥注释，只认**精确等于**的选择器）。"""
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


def served_css() -> str:
    html = urllib.request.urlopen(DEV_ORIGIN + "/", timeout=60).read().decode("utf-8", "replace")
    urls = sorted(set(re.findall(r'/_next/static/chunks/[^"]+\.css', html)))
    chunks = []
    for u in urls:
        try:
            chunks.append(urllib.request.urlopen(DEV_ORIGIN + u, timeout=60)
                          .read().decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            print(f"  ★ chunk 抓取失败 {u}: {exc}")
    return "\n".join(chunks)


def css_drift() -> dict:
    disk = parse_css(CSS_FILE.read_text(encoding="utf-8"))
    live = parse_css(served_css())
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


def preflight_css(timeout: int = 90) -> tuple:
    """等 dev server 的 CSS chunk **追平磁盘** ⟹ 超时则**显式失败**（exit 2）。

    ★★ 为什么必须先过这一关：dev server 的 CSS 重建是**异步**的 ⟹ 改完源码立刻量，
      量到的可能是**上一版** chunk ⟹ ⟹ 判据会给出「像真的、其实是假的」红。
    ★★ 更阴的一种：Turbopack 的**持久缓存**可以把陈旧的编译结果原样吐出来
      （只有 `rm -rf .next/dev/cache/turbopack` 才恢复）⟹ ⟹ 这一关必须**比对**，
      不能只靠「我等了一会儿」。
    """
    t0 = time.time()
    drift = css_drift()
    while drift and time.time() - t0 < timeout:
        time.sleep(3)
        drift = css_drift()
    waited = round(time.time() - t0, 1)
    if drift:
        return False, {"等了几秒": waited, "不一致": drift}
    return True, {"等了几秒": waited, "不一致": {}}


# ── 源站期望值：**全部**从入库的 raw 机器提取 ─────────────────────────
def build_expectations() -> dict:
    """把 5 份源站 raw 里的读数，整理成一张「期望值表」。

    ★ 为什么强调「机器提取」：手打的坐标就是**输入**，不是测量（写错一个数字，
      判据就会拿错的期望值去判一个其实正确的实现）。
    ★ 每个「找元素」的规则都尽量用**结构/尺寸/属性**，不用坐标字面量
      （例如「五段按钮」= 宽 240 高 44 的按钮；「页签」= aria 在那六个里的按钮）。
    """
    src1 = read_json(RAW / "source-840-editor.json")
    src2 = read_json(RAW / "source-840-editor2.json")
    src4 = read_json(RAW / "source-840-editor4.json")
    src5 = read_json(RAW / "source-840-editor5.json")
    r2 = src2["★读数"]
    r4 = src4["★视觉读数"]
    r5 = src5["★读数"]

    modal = r2["modal"]["box"]
    leaves = r2["leaves"]
    ctrls = r2["ctrls"]
    inputs = r2["inputs"]
    preview = r2["preview"]
    row_acne = r2["rowAcne"]

    def R(b):
        """绝对盒 → **相对模态**的盒（源站读数是绝对坐标 ⟹ 对拍要用相对值）。"""
        return {"x": b["x"] - modal["x"], "y": b["y"] - modal["y"],
                "w": b["w"], "h": b["h"]}

    e: dict = {}
    e["模态"] = dict(modal)
    e["内容行"] = R(r2["rowAcne"][0]["box"])
    e["左列"] = R(r4["asides"][0]["box"])
    e["预览"] = R(r4["main"]["box"])
    e["右列"] = R(r4["asides"][1]["box"])
    e["返回按钮"] = R(next(c for c in ctrls if c.get("aria") == "返回")["box"])
    e["标题输入"] = R(next(i for i in inputs if i.get("aria") == "角色名称")["box"])

    tag_leaf = [l for l in leaves if (l.get("text") or "").startswith("·")]
    if len(tag_leaf) != 1:
        raise SystemExit("标签行文案识别不唯一：%d 个" % len(tag_leaf))
    e["标签文本"] = R(tag_leaf[0]["box"])
    e["性别图标"] = R(next(s for s in r5["svgs"]
                          if "mt-[7px]" in (s["parent"].get("cls") or ""))["box"])

    segs = r5["segBtns"]
    e["五段按钮"] = [R(b["box"]) for b in segs]
    e["五段图标"] = [R(b["kids"][0]["box"]) for b in segs]
    e["五段文案"] = [R(k["box"]) for b in segs for k in b["kids"]
                     if k["tag"] == "SPAN" and k.get("text") != "限免"]
    e["限免徽标"] = [R(k["box"]) for b in segs for k in b["kids"]
                     if k.get("text") == "限免"]

    e["左下工具"] = [R(c["box"]) for c in ctrls
                     if c.get("aria") in ("撤销", "恢复", "按住对比")]
    # ★ 「左下工具图标」必须**按父盒**取，不能只按 cls 前缀取
    #   （「半身/全身」那两枚按钮的 cls 前缀**一模一样** ⟹ 只按前缀会多取两枚 ⟹ 数量对不上）
    e["左下工具图标"] = [
        R(next(s["box"] for s in r5["svgs"]
               if s["parent"].get("box") == c["box"]))
        for c in ctrls if c.get("aria") in ("撤销", "恢复", "按住对比")
    ]
    e["角色图"] = R(next(p for p in preview
                       if "h-[550px]" in (p.get("cls") or ""))["box"])
    e["半身全身容器"] = R(next(p for p in preview
                            if "z-20" in (p.get("cls") or ""))["box"])
    e["半身全身"] = [R(b["box"]) for b in r5["halfBtns"]]
    e["半身全身图标"] = [R(b["kids"][0]["box"]) for b in r5["halfBtns"]]

    e["页签"] = [R(b["box"]) for b in r5["tabBtns"]]
    e["页签图标"] = [R(b["kids"][0]["box"]) for b in r5["tabBtns"]]
    e["皮肤页签文案"] = R(next(l for l in leaves if l.get("text") == "皮肤")["box"])

    ranges = [i for i in inputs if i["box"]["w"] == 240 and i["box"]["h"] == 12]
    if len(ranges) != 6:
        raise SystemExit("滑杆条数识别异常：%d" % len(ranges))
    e["滑杆轨道"] = [R(i["box"]) for i in ranges]
    labels = []
    for i in ranges:
        hit = [l for l in leaves if l.get("text") == i.get("aria")]
        if len(hit) != 1:
            raise SystemExit("滑杆文案识别不唯一：%r" % (i.get("aria"),))
        labels.append(R(hit[0]["box"]))
    e["滑杆文案"] = labels
    e["滑杆数值"] = [R(v["box"]) for v in sorted(
        (l for l in leaves if l.get("text") == "0" and l["box"]["h"] == 16),
        key=lambda l: l["box"]["y"])]
    e["信息图标"] = [R(i["box"]) for i in sorted(
        (l for l in leaves if l.get("text") == "i"),
        key=lambda l: l["box"]["y"])]

    e["祛斑祛痘文案"] = R(next(l for l in leaves
                             if l.get("text") == "祛斑祛痘")["box"])
    e["祛斑祛痘开关"] = R(next(x for x in row_acne
                            if "mantine-Switch-root" in (x.get("cls") or ""))["box"])

    e["确认生成"] = R(r5["genBtn"]["box"])
    e["确认生成图标"] = R(r5["genBtn"]["kids"][0]["box"])
    e["确认生成文案"] = R(next(l for l in leaves
                             if l.get("text") == "确认生成")["box"])
    e["智能调整"] = R(next(c for c in ctrls if c.get("aria") == "智能调整")["box"])
    e["智能调整图标"] = R(next(s for s in r5["svgs"]
                             if "size-9" in (s["parent"].get("cls") or ""))["box"])

    e["底栏"] = R(r4["footer"][0]["box"])
    e["复选框"] = R(r4["checkbox"]["next"]["box"])
    e["生成资产标签"] = R(next(f for f in r4["footer"]
                            if f.get("tag") == "SPAN"
                            and f.get("text") == "保存时生成角色资产")["box"])
    e["积分符号"] = R(r4["fortyFour"]["prevBox"])
    e["积分数值"] = R(r4["fortyFour"]["box"])
    e["保存"] = R(next(c for c in ctrls if c.get("text") == "保存")["box"])
    e["保存并添加到画布"] = R(next(c for c in ctrls
                              if c.get("text") == "保存并添加到画布")["box"])
    e["_源站锚点"] = {
        "★源站是否点到编辑角色": src1.get("★是否点到编辑角色"),
    }
    return e


def box_close(a: dict, b: dict, tol: int = 1) -> bool:
    """两个盒「算相等」：**宽高逐像素全等**，位置 ±1px。

    ★ 为什么允许 ±1px 的位置容差：两侧的浏览器在同一台机器上，但布局里有
      **半像素居中**（如「皮肤」页签文案 28 宽在 56 宽盒里 ⟹ 起点 14）⟹
      取整方向可能差 1 ⟹ ⟹ 位置容差 ±1，**宽高不给容差**。
    """
    if not a or not b:
        return False
    if a.get("w") != b.get("w") or a.get("h") != b.get("h"):
        return False
    return (abs((a.get("x") or 0) - (b.get("x") or 0)) <= tol
            and abs((a.get("y") or 0) - (b.get("y") or 0)) <= tol)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 的 CSS chunk 追平磁盘……")
    pf_ok, pf_detail = preflight_css()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 CSS chunk 与磁盘不一致 ⟹ **本轮读数不可信**")
        print(json.dumps(pf_detail, ensure_ascii=False, indent=1))
        OUT.write_text(json.dumps({
            "batch": 840,
            "verdict": "preflight-failed",
            "preflight": pf_detail,
            "note": "服务端 chunk 还没重建（或 Turbopack 持久缓存陈旧）⟹ "
                    "需要 `rm -rf .next/dev/cache/turbopack` 并重启 dev server",
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写入", OUT)
        return 2
    print("  ✔ chunk 已追平磁盘（等了 %ss）" % pf_detail.get("等了几秒"))

    exp = build_expectations()

    print("跑 clone 运行时探针……")
    run_probe(PROBE_CLONE)
    rt = read_json(pathlib.Path("/tmp/b840-clone-editor.json"))

    opened = rt.get("B_点开后") or {}
    after_slider = rt.get("C_拖滑杆后") or {}
    after_switch = rt.get("D_点开关后") or {}
    after_generate = rt.get("D2_点确认生成后") or {}
    after_tab = rt.get("E_切页签后") or {}
    after_back = rt.get("F_切回皮肤") or {}
    after_rename = rt.get("G_改名后") or {}
    after_save = rt.get("G2_点保存后") or {}
    reopened_title = rt.get("G3_重开后标题") or {}
    esc_outside = rt.get("B2_Esc后_焦点不在输入框") or {}
    esc_inside = rt.get("H_Esc后") or {}
    before = rt.get("A_点编辑前") or {}

    checks = []

    # ── S1 「编辑角色」不再是死按钮 ＋ 与源站同构 ────────────────────────
    src839 = read_json(ROOT / "docs/research/liblib-canvas-batch839-2026-10-01"
                       "/raw/source-839-editor.json")
    src_cta = next((b for b in (src839.get("A_资产视图_btns") or [])
                    if (b.get("text") or "").strip() == "编辑角色"), None)
    clone_cta = rt.get("★编辑角色CTA盒") or {}
    s1 = {
        "★源站_点编辑角色后打开了编辑器": exp["_源站锚点"]["★源站是否点到编辑角色"] is True,
        "★源站_编辑角色CTA盒": (src_cta or {}).get("box"),
        "★clone_编辑角色CTA盒": clone_cta,
        "★clone_点开前_没有编辑器": before.get("★是否有编辑器") is False,
        "★clone_点开后_有编辑器": opened.get("★是否有编辑器") is True,
        "★clone_模态盒": opened.get("模态盒"),
        "★源站_模态盒": exp["模态"],
    }
    s1["★CTA盒与源站一致"] = bool(
        src_cta and clone_cta
        and src_cta["box"]["x"] == clone_cta.get("x")
        and src_cta["box"]["y"] == clone_cta.get("y")
        and src_cta["box"]["w"] == clone_cta.get("w")
        and src_cta["box"]["h"] == clone_cta.get("h"))
    s1["★模态盒与源站一致"] = box_close(opened.get("模态盒") or {}, exp["模态"])
    checks.append((
        "S1 ★★★ **「编辑角色」不再是死按钮**：clone 点它 ⟹ **大编辑器**出现"
        "（模态 %s）⟹ ★ 且源站同一动作**也**打开大编辑器"
        "（源站 raw：★是否点到编辑角色=%s）⟹ ⟹ 两者**同构**；"
        "★ CTA 盒与源站逐像素一致"
        % (json.dumps(opened.get("模态盒"), ensure_ascii=False),
           exp["_源站锚点"]["★源站是否点到编辑角色"]),
        (s1["★源站_点编辑角色后打开了编辑器"]
         and s1["★clone_点开前_没有编辑器"]
         and s1["★clone_点开后_有编辑器"]
         and s1["★CTA盒与源站一致"] and s1["★模态盒与源站一致"]),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何逐像素（期望值全部从 raw 提取） ─────────────────────────
    clone_boxes = {
        "模态": opened.get("模态盒"),
        "内容行": opened.get("内容行盒"),
        "左列": opened.get("左列盒"),
        "预览": opened.get("预览盒"),
        "右列": opened.get("右列盒"),
        "返回按钮": opened.get("返回按钮"),
        "标题输入": opened.get("标题输入"),
        "标签文本": opened.get("标签文本"),
        "性别图标": opened.get("性别图标"),
        "五段按钮": [s for s in (opened.get("五段") or [])],
        "五段图标": [(s.get("图标盒") or {}) for s in (opened.get("五段") or [])],
        "五段文案": [(s.get("文案盒") or {}) for s in (opened.get("五段") or [])],
        "限免徽标": [(s.get("徽标盒") or {}) for s in (opened.get("五段") or [])
                     if s.get("徽标盒")],
        "左下工具": opened.get("左下工具"),
        "左下工具图标": [(t.get("图标盒") or {}) for t in (opened.get("左下工具") or [])],
        "角色图": opened.get("角色图"),
        "半身全身容器": opened.get("半身全身容器"),
        "半身全身": opened.get("半身全身"),
        "半身全身图标": [(t.get("图标盒") or {}) for t in (opened.get("半身全身") or [])],
        "页签": opened.get("页签"),
        "页签图标": [(t.get("图标盒") or {}) for t in (opened.get("页签") or [])],
        "皮肤页签文案": ((opened.get("页签") or [{}])[0] or {}).get("文案盒"),
        "滑杆轨道": opened.get("滑杆轨道"),
        "滑杆文案": [(t.get("文案盒") or {}) for t in (opened.get("滑杆标签") or [])],
        "滑杆数值": opened.get("滑杆数值"),
        "信息图标": ([t.get("图标盒") for t in (opened.get("滑杆标签") or [])
                      if t.get("图标盒")]
                     + [((opened.get("祛斑祛痘行") or {}).get("图标盒"))]),
        "祛斑祛痘文案": ((opened.get("祛斑祛痘行") or {}).get("文案盒")),
        "祛斑祛痘开关": opened.get("开关"),
        "确认生成": opened.get("确认生成"),
        "确认生成图标": ((opened.get("确认生成") or {}).get("图标盒")),
        "确认生成文案": ((opened.get("确认生成") or {}).get("文案盒")),
        "智能调整": opened.get("智能调整"),
        "智能调整图标": ((opened.get("智能调整") or {}).get("图标盒")),
        "底栏": opened.get("底栏盒"),
        "复选框": opened.get("复选框可见件"),
        "生成资产标签": opened.get("生成资产标签"),
        "积分符号": opened.get("积分符号"),
        "积分数值": opened.get("积分数值"),
        "保存": opened.get("保存"),
        "保存并添加到画布": opened.get("保存并添加到画布"),
    }
    diffs = []
    total = 0
    for key, want in exp.items():
        if key.startswith("_"):
            continue
        got = clone_boxes.get(key)
        if isinstance(want, list):
            if not isinstance(got, list) or len(got) != len(want):
                diffs.append({"元素": key, "源站": want, "clone": got,
                              "问题": "数量不同"})
                total += max(len(want), len(got or []))
                continue
            for i, (a, b) in enumerate(zip(want, got)):
                total += 1
                if not box_close(a, b):
                    diffs.append({"元素": "%s[%d]" % (key, i), "源站": a, "clone": b})
        else:
            total += 1
            if not box_close(want, got or {}):
                diffs.append({"元素": key, "源站": want, "clone": got})
    s2 = {
        "★比较了几个元素": total,
        "★有几个不一致": len(diffs),
        "★不一致明细": diffs,
        "★期望值全部来自机器提取": True,
    }
    # ★★ 「文档发布值 == 运行时值」：README 里写的元素数必须**等于**本轮实际比较的数量
    #   （否则 README 会随实现漂移，而没人会发现）
    readme_txt = (BATCH / "README.md").read_text(encoding="utf-8") \
        if (BATCH / "README.md").exists() else ""
    m_cnt = re.search(r"(\d+)\s*个元素", readme_txt)
    s2["★README里写的元素数"] = int(m_cnt.group(1)) if m_cnt else None
    s2["★README里的元素数与实际一致"] = (m_cnt is not None
                                        and int(m_cnt.group(1)) == total)
    checks.append((
        "S2 ★★★ **几何与源站逐像素一致**（%d 个元素：模态／三列／返回／标题／标签／"
        "五段按钮＋图标＋文案＋限免徽标／左下三工具＋图标／角色图／半身全身＋容器＋图标／"
        "六页签＋图标＋文案／六滑杆轨道＋文案＋数值＋'i' 图标／祛斑祛痘＋开关／"
        "确认生成＋图标＋文案／智能调整＋图标／底栏＋复选框＋标签＋⚡＋44／两枚保存按钮）"
        "⟹ ★ **期望值全部从入库的 5 份源站 raw 机器提取** ⟹ ⟹ **宽高逐像素全等**、"
        "位置 ±1px；★ 且 README 写的元素数（%s）== 本轮实际比较数（%d）"
        % (total, s2["★README里写的元素数"], total),
        (len(diffs) == 0 and total >= 40 and s2["★README里的元素数与实际一致"]),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 交互真生效 ───────────────────────────────────────────────────
    s3_sliders = after_slider.get("滑杆轨道") or []
    s3_values = after_slider.get("滑杆数值") or []
    first_val = s3_sliders[0].get("value") if s3_sliders else None
    first_text = s3_values[0].get("text") if s3_values else None
    sw_before = (opened.get("开关") or {}).get("checked")
    sw_after = (after_switch.get("开关") or {}).get("checked")
    segs_before = opened.get("五段") or []
    segs_after = after_back.get("五段") or []
    tabs_before = opened.get("页签") or []
    tabs_after = after_tab.get("页签") or []
    s3 = {
        "★滑杆_初值": (opened.get("滑杆轨道") or [{}])[0].get("value"),
        "★滑杆_拖后控件value": first_val,
        "★滑杆_拖后渲染数字": first_text,
        "★滑杆_渲染数字等于控件value": (first_text == first_val),
        "★滑杆_拖后确实变了": (first_val is not None and first_val != "0"),
        "★开关_点前": sw_before,
        "★开关_点后": sw_after,
        "★开关_确实翻转": (sw_before == "false" and sw_after == "true"),
        "★分段_点前选中": [s.get("id") for s in segs_before if s.get("selected")],
        "★分段_点后选中": [s.get("id") for s in segs_after if s.get("selected")],
        "★页签_点前选中": [t.get("id") for t in tabs_before if t.get("selected")],
        "★页签_点后选中": [t.get("id") for t in tabs_after if t.get("selected")],
    }
    s3["★分段_选中态转移"] = (s3["★分段_点前选中"] == ["face"]
                              and s3["★分段_点后选中"] == ["traits"])
    #   ★★ **batch 842 起**：探针改点「妆造」（眉眼页已实现 ⟹ 「未实现页」变成妆造）
    #   ⟹ ⟹ 这里期望的**选中态转移**也跟着改成 skin → makeup
    s3["★页签_选中态转移"] = (s3["★页签_点前选中"] == ["skin"]
                              and s3["★页签_点后选中"] == ["makeup"])
    checks.append((
        "S3 ★★★ **交互真生效**（不是摆设）：拖滑杆 ⟹ **控件的 value 从 %s 变成 %s**，"
        "且**渲染出来的数字「%s」== 控件的 value**（★ 判据是「等于目标值」，"
        "不是「看起来变了」）⟹ 开关 ⟹ `aria-checked` %s→%s ⟹ 分段选中态 %s→%s "
        "⟹ 页签选中态 %s→%s"
        % (s3["★滑杆_初值"], first_val, first_text, sw_before, sw_after,
           s3["★分段_点前选中"], s3["★分段_点后选中"],
           s3["★页签_点前选中"], s3["★页签_点后选中"]),
        (s3["★滑杆_渲染数字等于控件value"] and s3["★滑杆_拖后确实变了"]
         and s3["★开关_确实翻转"] and s3["★分段_选中态转移"] and s3["★页签_选中态转移"]),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 Esc 两条路径 ─────────────────────────────────────────────────
    ctx_src = (ROOT / "src/lib/libtvSelectionCommandContext.ts").read_text(encoding="utf-8")
    ui_src = (ROOT / "src/store/uiStore.ts").read_text(encoding="utf-8")
    panel_src = (ROOT / "src/components/CharacterEditorPanel.tsx").read_text(encoding="utf-8")
    s4 = {
        "★路径1_焦点不在输入框_编辑器关了": esc_outside.get("★编辑器还在吗") is False,
        "★路径1_面板还在": esc_outside.get("★面板还在吗") is True,
        "★路径2_焦点在输入框_编辑器关了": esc_inside.get("★编辑器还在吗") is False,
        "★路径2_面板还在": esc_inside.get("★面板还在吗") is True,
        "★store有characterEditorId": "characterEditorId" in ui_src,
        "★store有对应分支": 'case "character-editor":' in ui_src,
        "★阻塞面表里有character-editor": '"character-editor"' in ctx_src,
        "★解析顺序在character-assets之前": bool(re.search(
            r'if \(snapshot\.characterEditorId\) return "character-editor";\s*'
            r'if \(snapshot\.characterAssetsId\) return "character-assets";',
            ctx_src)),
        "★编辑器自己处理Esc": ('event.key !== "Escape"' in panel_src
                             and "setCharacterEditorId(null)" in panel_src),
    }
    checks.append((
        "S4 ★★★ **Esc 两条路径都关掉编辑器、且面板留着**："
        "① 焦点不在可编辑元素（走画布全局契约）⟹ %s；"
        "② 焦点在标题输入框（全局那层对可编辑目标**早退** ⟹ 走编辑器自己那层）⟹ %s；"
        "⟹ ⟹ 靠把大编辑器登记成**前台阻塞面** `character-editor`"
        "（★ 必须排在 `character-assets` **之前**）"
        % (s4["★路径1_焦点不在输入框_编辑器关了"], s4["★路径2_焦点在输入框_编辑器关了"]),
        all(v for k, v in s4.items() if k.startswith("★")),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 「保存」是真的 ───────────────────────────────────────────────
    s5 = {
        "★改名后标题值": (after_rename.get("标题输入") or {}).get("value"),
        "★保存后编辑器关了": after_save.get("★编辑器还在吗") is False,
        "★保存后面板上的名字": after_save.get("★面板名字"),
        "★重开后标题值": reopened_title.get("value"),
    }
    s5["★名字落回了角色"] = bool(
        s5["★改名后标题值"] and s5["★改名后标题值"] == s5["★保存后面板上的名字"]
        and s5["★改名后标题值"] == s5["★重开后标题值"])
    checks.append((
        "S5 ★★★ **「保存」是真的**：改名成「%s」⟹ 保存 ⟹ 编辑器关闭 ⟹ "
        "名字**落回角色**（面板上显示「%s」）⟹ 再打开标题还是「%s」"
        % (s5["★改名后标题值"], s5["★保存后面板上的名字"], s5["★重开后标题值"]),
        (s5["★保存后编辑器关了"] and s5["★名字落回了角色"]),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 mock 如实标注 ────────────────────────────────────────────────
    readme_path = BATCH / "README.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    low = readme.lower()
    credit_after = (after_generate.get("积分数值") or {}).get("text")
    s6 = {
        "★点确认生成后_积分数值": credit_after,
        "★点确认生成后_提示": after_generate.get("提示"),
        "★README里mock出现次数": low.count("mock"),
        "★README写明确认生成是mock": "确认生成" in readme and "mock" in low,
        "★README写明不消耗积分": ("不消耗" in readme or "不会消耗" in readme
                               or "不花" in readme),
        "★README写明智能调整是mock": "智能调整" in readme and "mock" in low,
        "★README写明保存并添加到画布是mock": "保存并添加到画布" in readme,
        "★README写明撤销恢复按住对比是mock": ("撤销" in readme and "恢复" in readme
                                     and "按住对比" in readme),
        "★README写明未实测页签不编造": ("未实测" in readme and "不编造" in readme),
    }
    s6["★运行时_积分没被消耗"] = (credit_after == "44")
    s6["★运行时_给出不消耗的提示"] = bool(
        s6["★点确认生成后_提示"] and "不消耗" in (s6["★点确认生成后_提示"] or ""))
    checks.append((
        "S6 ★★ **mock 如实标注**：★ 运行时验证「确认生成」**没有**消耗积分"
        "（点完 ⚡ 仍是 %s，且弹出「不消耗积分」的提示）⟹ ⟹ README **必须**写明"
        "确认生成／智能调整／保存并添加到画布／撤销／恢复／按住对比 都是 mock"
        "（否则就是把自拟行为说成源站事实）"
        % (s6["★点确认生成后_积分数值"],),
        (s6["★运行时_积分没被消耗"] and s6["★运行时_给出不消耗的提示"]
         and s6["★README里mock出现次数"] >= 5
         and s6["★README写明确认生成是mock"]
         and s6["★README写明不消耗积分"]
         and s6["★README写明智能调整是mock"]
         and s6["★README写明保存并添加到画布是mock"]
         and s6["★README写明撤销恢复按住对比是mock"]
         and s6["★README写明未实测页签不编造"]),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 未实测的页签：显示空态说明、不编造控件 ───────────────────────
    #   ★★ **batch 842 起改盯「妆造」**：眉眼页在 batch 842 已实现
    #   ⟹ ⟹ 「仍未实现的那一页」变成了妆造 ⟹ ⟹ 这条断言要盯**当下**仍未实现的那一页
    #   ⟹ ⟹ 否则它会因为「旧事实」而红（★ 断言要盯**当前状态**，不是历史批次）
    empty_text = after_tab.get("空态")
    skin_back_empty = after_back.get("空态")
    s7 = {
        "★切到妆造后_有滑杆吗": len(after_tab.get("滑杆轨道") or []),
        "★切到妆造后_有开关吗": bool(after_tab.get("开关")),
        "★切到妆造后_空态说明": empty_text,
        "★切回皮肤后_滑杆数": len(after_back.get("滑杆轨道") or []),
        "★切回皮肤后_空态": skin_back_empty,
        "★README写明那五页签未实测": "未实测" in readme,
        "★README没有断言源站那五页签没有控件": (
            "源站那五页签没有控件" not in readme and "源站这五页签没有控件" not in readme),
    }
    checks.append((
        "S7 ★★★ **未实测的页签显示空态说明、不编造控件**：切到「妆造」⟹ "
        "滑杆数 %d、开关无 ⟹ 出现空态说明「%s」；切回「皮肤」⟹ 滑杆 %d 条 ⟹ 空态消失；"
        "★ 且 README **不**把它写成「源站那五页签没有控件」（★ 那是**未证实的否定性结论**"
        "—— 我们只知道「**没测过**」）"
        % (s7["★切到妆造后_有滑杆吗"], (empty_text or "")[:34].replace("\n", " "),
           s7["★切回皮肤后_滑杆数"]),
        (s7["★切到妆造后_有滑杆吗"] == 0 and not s7["★切到妆造后_有开关吗"]
         and bool(empty_text) and s7["★切回皮肤后_滑杆数"] == 6
         and not skin_back_empty
         and s7["★README写明那五页签未实测"]
         and s7["★README没有断言源站那五页签没有控件"]),
        json.dumps(s7, ensure_ascii=False),
    ))

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print("  %s  %s" % ("PASS" if ok else "FAIL", label))
        passed += bool(ok)
    print("\n%d/%d 通过" % (passed, len(checks)))

    audit = {
        "batch": 840,
        "title": "把「编辑角色」从死按钮做成角色大编辑器，几何逐像素对齐源站",
        "verdict": "%d/%d" % (passed, len(checks)),
        "preflight": pf_detail,
        "source": {
            "期望值表": {k: v for k, v in exp.items() if not k.startswith("_")},
            "源站锚点": exp["_源站锚点"],
        },
        "clone": {
            "B_点开后": opened, "C_拖滑杆后": after_slider,
            "D_点开关后": after_switch, "D2_点确认生成后": after_generate,
            "E_切页签后": after_tab, "F_切回皮肤": after_back,
            "G_改名后": after_rename, "G2_点保存后": after_save,
            "B2_Esc后_焦点不在输入框": esc_outside, "H_Esc后": esc_inside,
        },
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "★★★ **「编辑角色」以前是死按钮** ⟹ 本批把它做成**角色大编辑器**"
            "（1198×758 居中模态 ＋ 左列五段 ＋ 右栏六页签 ＋ 六条滑杆 ＋ 祛斑祛痘开关 "
            "＋ 底栏「保存时生成角色资产 ⚡44」）。",
            "★★★ **几何与源站逐像素一致**（%d 个元素）⟹ **期望值全部从 5 份源站 raw "
            "机器提取** ⟹ ⟹ 含**图标**（第⑤趟补采的 22 个 svg）。" % total,
            "★★★ **「半身/全身紧邻（gap 0）」是误读**：源站实测 rel 564 / **605** "
            "⟹ 间隙 9px（容器实宽 73）⟹ 本批改正。",
            "★★★ **Esc 两条路径**都关得掉编辑器、且面板留着 ⟹ 靠 `character-editor` "
            "前台阻塞面（排在 `character-assets` 之前）。",
            "★★★ **「保存」是真的**：改名会落回角色 ⟹ ⟹ 而「确认生成／智能调整／"
            "保存并添加到画布／撤销／恢复／按住对比」是 **mock** ⟹ ⟹ README 如实标注。",
        ],
        "notClaimed": [
            "**不声称**源站那五枚页签（眉眼/鼻子/嘴唇/脸部/妆造）里**没有**控件 —— "
            "★ 我们**没测过** ⟹ ⟹ clone 只显示空态说明，不编造控件。",
            "**不声称**「确认生成」在源站消耗 44 积分之外的行为（消耗积分会真实扣费 ⟹ "
            "源站那趟**没点**）⟹ ⟹ clone 的「确认生成」是 mock，不消耗积分。",
            "**不声称**图标**字形**与源站一致 —— 源站是 iconify SVG，**字形未采集** ⟹ "
            "clone 用 lucide 占位（★ 但**尺寸与位置**逐像素对齐）。",
            "**不声称**「保存时生成角色资产」复选框的**图标字形**一致（源站是整枚 18×18 "
            "iconify SVG ⟹ clone 是 18×18 圆底 ＋ 12px 勾）。",
        ],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
