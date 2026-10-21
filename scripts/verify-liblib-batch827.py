#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 827 验收器 —— 角色造型室（源站当前形态）面板：结构与几何**逐项对齐**。

## ★ 这一批做了什么

batch 826 结束时，「角色造型室」这个面板的**内容**还是 2026-09-07 的旧形态
（1280×720 模态、公共角色库 / 合规素材库两页签、角色筛选面板、应用至画布）。
batch 827 按源站**当前**构建把它**重建**了：
  ★ 页签 → 我的角色库 / 官方角色库
  ★ 筛选 → 三个原生 `<details>` 胶囊（性别 / 年龄段 / 文化区域）
  ★ 主体 → 居中 carousel（当前项居中）＋ 居中名字组 ＋ 底部滚动条
  ★ 底部 → 三种形态（多选态 / 选中角色态 / 什么都没选态）

## ★★ 本批抓到的两个「工具链级」问题

① ★★ **Next 16 默认拦截来自 `127.0.0.1` 的 dev 资源** ⟹
   `/_next/webpack-hmr` 被判跨源并拒绝 ⟹ **整页不 hydration**
   （DOM 上没有 `__react*` props、点击全部无效），而页面**看起来是正常的** ⟹
   ★★ 探针会把「静态 SSR HTML」当成「活体读数」⟹ 门禁可以全绿却毫无意义。
   ⟹ 修法：`next.config.ts` 加 `allowedDevOrigins: ["127.0.0.1", "localhost"]`。
   ⟹ ★★ **S1 就是这条的闸门**：判据先证明「页面确实 hydration 了」，
      否则后面所有读数一律作废。

② ★★ **跑 `npm run build` 会覆盖 dev server 正在用的 `.next/`** ⟹
   跑完 build 之后 4317 的 dev server 会**假死**（页面还能开、200，
   但客户端 bundle 与 dev 的 manifest 对不上 ⟹ 不 hydration）⟹
   ★★ 判据纪律：**build 之后必须重启 dev server**（`npm run dev:restart`）。

## ★★ 本批对 batch 826 §5.3 的更正

batch 826 写的是「源站筛选下拉的祖先 `opacity:0` 骗过可见性检查」——**这是错的**。
真因（batch 827 实测 + bundle 核对）：源站的筛选下拉是**原生 `<details>/<summary>`**，
收起时子节点**仍在 DOM 里**、自身 computed style 报 `display:block / visibility:visible /
opacity:1`，**只有命中测试**（elementFromPoint）判得出「看不见」；
而且**收起态的几何读数是失真的**（面板读数 303 ≠ 展开态真值 271）⟹ 要量下拉位置
必须**展开后**量。详见 batch 827 README §5。

## ★ 判据纪律

- ★ 源站对照**读入库的 raw**（batch 827 自己的三份源站 raw + bundle 片段 + i18n 词表）
- ★ 判据只认**绝对几何**与**DOM 可见读数**
- ★ **真实鼠标**点击（pointerdown），不用程序化 click 代替
- ★ 阴性对照打在**性质真正读取的字段**上，且**每条只翻它自己那一条**
- ★ **S1 先证明页面 hydration 了**，否则整轮读数作废（见上面 ①）
"""
import copy
import json
import os
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch827-2026-10-01"
RAW = BATCH / "raw" / "vb827a.json"
RAW_SRC_STRUCTURE = BATCH / "raw" / "source-827-structure.json"
RAW_SRC_DETAILS = BATCH / "raw" / "source-827-details.json"
RAW_SRC_DROPDOWNS = BATCH / "raw" / "source-827-dropdowns.json"
RAW_SRC_BUNDLE = BATCH / "raw" / "source-827-bundle.json"
RAW_SRC_I18N = BATCH / "raw" / "source-827-i18n.json"
SRC_CHARACTER = ROOT / "src" / "components" / "CharacterLibraryPanel.tsx"
SRC_CSS = ROOT / "src" / "components" / "character-studio.css"
SRC_NEXT_CONFIG = ROOT / "next.config.ts"

PROBE_BEGIN = "# ── ★ 探针区开始"
PROBE_END = "# ── ★ 探针区结束"

BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1920, "height": 1080}

# ── ★ 探针区开始 ────────────────────────────────────────────────────────────────
# ★ 判据 S1 只扫**这一段**：探针（跑浏览器的部分）里不允许出现 store 写调用。
# ★ 阴性对照区在探针区**之后** ⟹ 它的文本**不在**扫描范围内
# ★ （否则「对照里写一个假的 store 调用」会把自己判成红 —— 自指陷阱）。

# ★ 页面**有没有 hydration**：React 会把 props 挂成 `__reactProps$xxx`
READ_HYDRATION = """()=>{
  const b=document.querySelector('button[aria-label="素材库"]');
  if(!b) return {found:false};
  const keys=Object.keys(b).filter(k=>k.startsWith('__react'));
  return {found:true, keys:keys,
          hasOnClick:keys.some(k=>typeof b[k].onClick==='function')};}"""

READ_PANEL = """()=>{
  const modal=document.querySelector('[data-character-studio]');
  if(!modal) return null;
  const r=modal.getBoundingClientRect();
  const cs=getComputedStyle(modal);
  const bl=parseFloat(cs.borderLeftWidth)||0, br=parseFloat(cs.borderRightWidth)||0;
  const bt=parseFloat(cs.borderTopWidth)||0, bb=parseFloat(cs.borderBottomWidth)||0;
  const box=(e)=>{if(!e)return null;const q=e.getBoundingClientRect();
    return {x:Math.round(q.x),y:Math.round(q.y),
            w:Math.round(q.width),h:Math.round(q.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const hit=(e)=>{const q=e.getBoundingClientRect();
    if(q.width<=0||q.height<=0)return false;
    const h=document.elementFromPoint(q.x+q.width/2,q.y+q.height/2);
    return !!(h&&(h===e||e.contains(h)));};

  const tabs=[...modal.querySelectorAll('[data-character-studio-tab]')].map(e=>({
    text:txt(e), box:box(e),
    font:getComputedStyle(e).fontSize+'/'+getComputedStyle(e).fontWeight,
    color:getComputedStyle(e).color}));

  const pills=[...modal.querySelectorAll('details[data-character-filter]')].map(d=>{
    const s=d.querySelector('summary');
    const panel=d.querySelector('.cs-panel');
    return {key:d.getAttribute('data-character-filter'),
      open:d.hasAttribute('open'),
      summary:box(s), summaryText:txt(s),
      panel:panel?box(panel):null,
      options:[...d.querySelectorAll('[data-character-filter-chip]')].map(c=>txt(c))};});

  const tools={};
  for(const b of modal.querySelectorAll('button[aria-label]')){
    const a=b.getAttribute('aria-label');
    if(/^(搜索角色名称或描述|多选|退出多选|列表模式|宫格模式|生成其他年龄版本|上一组角色|下一组角色)$/.test(a))
      tools[a]=box(b);}

  const cards=[...modal.querySelectorAll('[data-character-strip-card]')].map(c=>{
    const img=c.querySelector('img');
    return {name:c.getAttribute('data-character-strip-card'),
            box:box(c), img:box(img)};});

  const cta=[...modal.querySelectorAll('[data-character-studio-cta]')].map(e=>({
    kind:e.getAttribute('data-character-studio-cta'), text:txt(e), box:box(e),
    bg:getComputedStyle(e).backgroundColor, color:getComputedStyle(e).color}));

  const range=modal.querySelector('input[type=range]');
  const nameEl=modal.querySelector('[data-character-studio-name]');
  const quick=modal.querySelector('[data-character-studio-quick]');
  const assets=modal.querySelector('[data-character-studio-view-assets]');

  const opts=[...modal.querySelectorAll('[data-character-filter-chip]')].map(lab=>{
    const cb=lab.querySelector('input[type=checkbox]');
    return {text:txt(lab), box:box(lab), hit:hit(lab),
            cb:box(cb), checkmark:!!lab.querySelector('.cs-check')};});

  return {outer:{x:Math.round(r.x),y:Math.round(r.y),
                 w:Math.round(r.width),h:Math.round(r.height)},
    inner:{x:Math.round(r.x+bl),y:Math.round(r.y+bt),
           w:Math.round(r.width-bl-br),h:Math.round(r.height-bt-bb)},
    aria:modal.getAttribute('aria-label')||'',
    tabs:tabs, pills:pills, tools:tools, cards:cards, cta:cta,
    name:nameEl?{text:txt(nameEl),box:box(nameEl)}:null,
    quick:quick?box(quick):null,
    assets:assets?{box:box(assets),opacity:getComputedStyle(assets).opacity}:null,
    range:range?{aria:range.getAttribute('aria-label'),box:box(range)}:null,
    options:opts};}"""


def click_real_at(page, box):
    """**真实鼠标**点击（产生 pointerdown）⟹ ★ 不是程序化 click。

    ★ 用**读数里的坐标**点，而不是用名字找元素 ⟹
    ★ 「某一枚被改名」不会连带影响点击路径 ⟹ 阴性对照才只翻它自己那一条。
    """
    page.mouse.click(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
    return True


def probe(page):
    page.goto(f"{BASE_URL}/?batch827=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_timeout(1200)

    out = {"viewport": VIEWPORT}

    # ★★ 先证明页面 hydration 了 ⟹ 否则后面所有读数一律作废
    out["hydration"] = page.evaluate(READ_HYDRATION)

    # 打开「角色造型室」（底部工具条第 4 枚，真实鼠标点）
    entry = page.locator('button[aria-label="角色造型室"]').first
    bb = entry.bounding_box()
    if not bb:
        raise RuntimeError("找不到「角色造型室」入口")
    page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    page.wait_for_timeout(900)
    out["面板打开了"] = page.evaluate(
        "()=>!!document.querySelector('[data-character-studio]')")

    out["我的角色库"] = page.evaluate(READ_PANEL)

    # 展开「性别」下拉（真实鼠标点 summary）⟹ 读**展开态**
    gender_summary = page.locator('[data-character-filter-summary="性别"]')
    gb = gender_summary.bounding_box()
    if not gb:
        raise RuntimeError("找不到「性别」胶囊")
    page.mouse.click(gb["x"] + gb["width"] / 2, gb["y"] + gb["height"] / 2)
    page.wait_for_timeout(600)
    out["展开性别"] = page.evaluate(READ_PANEL)
    out["展开性别"]["下拉详情"] = page.evaluate(
        """()=>[...document.querySelectorAll('details[data-character-filter]')].map(d=>{
             const s=d.querySelector('summary'), p=d.querySelector('.cs-panel');
             const b=(e)=>{if(!e)return null;const q=e.getBoundingClientRect();
               return {x:Math.round(q.x),y:Math.round(q.y),
                       w:Math.round(q.width),h:Math.round(q.height)};};
             return {key:d.getAttribute('data-character-filter'),
                     open:d.hasAttribute('open'),
                     summary:b(s), panel:b(p)};})""")
    # 再点一次收起
    page.mouse.click(gb["x"] + gb["width"] / 2, gb["y"] + gb["height"] / 2)
    page.wait_for_timeout(400)
    out["收起性别"] = page.evaluate(READ_PANEL)

    # 切到「官方角色库」（真实鼠标点页签）
    official_tab = page.locator('[data-character-studio-tab="official"]')
    tb = official_tab.bounding_box()
    if not tb:
        raise RuntimeError("找不到「官方角色库」页签")
    page.mouse.click(tb["x"] + tb["width"] / 2, tb["y"] + tb["height"] / 2)
    page.wait_for_timeout(900)
    out["官方角色库"] = page.evaluate(READ_PANEL)

    # ★ 真实点「添加到画布」⟹ 面板应当关闭（这是**真交互**的证据）
    add_btn = page.locator('[data-character-studio-cta="add-to-canvas"]')
    ab = add_btn.bounding_box()
    if ab:
        page.mouse.click(ab["x"] + ab["width"] / 2, ab["y"] + ab["height"] / 2)
        page.wait_for_timeout(800)
    out["点添加到画布后面板关着"] = page.evaluate(
        "()=>!document.querySelector('[data-character-studio]')")
    return out


# ── ★ 探针区结束 ────────────────────────────────────────────────────────────────

# ── 判据（纯函数：吃读数吐检查）───────────────────────────────────────────────
def _diffs(xs):
    return [round(xs[i + 1] - xs[i], 1) for i in range(len(xs) - 1)]


def strip_comments(text: str) -> str:
    """去掉块注释与行注释 ⟹ ★ 判「旧词还在不在」必须只看**代码**。

    ★ ★★ 本组件的注释里**故意**写清了旧形态的词（公共角色库 / 应用至画布 /
    合规素材库 / 种族 / 时代 …，那是本批的考古记录）⟹
    ★★ 若不先去注释，判据就会因为「注释里提到了旧词」而恒红 ⟹
    ★★ 那是**判据读错了字段**，不是实现有问题。
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"(?m)^\s*//.*$", " ", text)
    return text


def build_checks(clone, src, src_details, src_dd, src_bundle, src_i18n,
                 src_texts, probe_src):
    C = []

    def ok(cid, cond, detail=None):
        # ★★★ 参数顺序必须与**调用点**一致（cid, cond, detail）。
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    mine = clone["我的角色库"] or {}
    official = clone["官方角色库"] or {}
    expanded = clone["展开性别"] or {}
    s_mine = src["A 我的角色库"]
    s_official = src["B 官方角色库"]

    # ── S1 ★★ 前提：页面 hydration 了 ＋ 面板打开了 ＋ 探针源码零 store 写调用
    i0 = probe_src.find(PROBE_BEGIN)
    j0 = probe_src.find(PROBE_END)
    region = probe_src[i0:j0] if 0 <= i0 < j0 else probe_src
    store_writes = re.findall(r"\.(setState|addNode|removeNode|updateCamera)\s*\(",
                              region)
    hyd = clone.get("hydration") or {}
    ok("S1:★★ **前提**：页面**已 hydration**（DOM 上有 React props）＋ 面板确实打开了"
       "＋ 探针源码**零 store 写调用**",
       hyd.get("hasOnClick") is True
       and clone.get("面板打开了") is True
       and not store_writes,
       {"hydration": hyd, "面板打开了": clone.get("面板打开了"),
        "扫的区间": "探针区（%s … %s）" % (PROBE_BEGIN, PROBE_END),
        "探针里的 store 写调用": store_writes,
        "★为什么": "Next 16 默认拦截来自 127.0.0.1 的 dev 资源 ⟹ 整页不 hydration "
                "⟹ 页面看起来正常但点击全无效 ⟹ 读数会是假的"})

    # ── S2 面板几何（外框 1200×760 @360,160 ＋ 内容框 1198×758 @361,161）
    src_section = [a for a in src_details["A 收起态"]["「男」的祖先链"]
                   if a.get("tag") == "SECTION"][0]["box"]
    ok("S2:★★★ 面板几何：外框 1200×760 @360,160 ＋ 内容框 1198×758 @361,161"
       "（== 源站 raw）",
       mine.get("outer") == {"x": 360, "y": 160, "w": 1200, "h": 760}
       and mine.get("inner") == {"x": 361, "y": 161, "w": 1198, "h": 758}
       and s_mine["面板根"] == {"x": 361, "y": 161, "w": 1198, "h": 758}
       and src_section == {"x": 360, "y": 160, "w": 1200, "h": 760},
       {"clone外框": mine.get("outer"), "clone内容框": mine.get("inner"),
        "源站raw内容框": s_mine["面板根"], "源站raw祖先链里的SECTION": src_section})

    # ── S3 页签：两枚逐字 ＋ 几何 ＋ 未选中 60% 白
    src_tabs = s_mine["头部"][:2]
    ok("S3:★★★ 页签：两枚**逐字**「我的角色库 / 官方角色库」＋ 几何 90×26 @385,183 / @508,183"
       "＋ 未选中是 60% 白",
       [t["text"] for t in mine.get("tabs", [])] == ["我的角色库", "官方角色库"]
       and [t["box"] for t in mine.get("tabs", [])]
       == [{"x": 385, "y": 183, "w": 90, "h": 26},
           {"x": 508, "y": 183, "w": 90, "h": 26}]
       and [t["color"] for t in mine.get("tabs", [])]
       == ["rgb(255, 255, 255)", "rgba(255, 255, 255, 0.6)"]
       and [d["text"] for d in src_tabs] == ["我的角色库", "官方角色库"]
       and [d["box"] for d in src_tabs]
       == [{"x": 385, "y": 183, "w": 90, "h": 26},
           {"x": 508, "y": 183, "w": 90, "h": 26}],
       {"clone": [(t["text"], t["box"], t["color"]) for t in mine.get("tabs", [])],
        "源站raw": [(d["text"], d["box"], d["color"]) for d in src_tabs]})

    # ── S4 三枚筛选胶囊 ＋ 搜索按钮（几何与源站 raw 逐项相同）
    src_pills = src_dd["A 收起态的三个下拉"]
    clone_pill_map = {p["key"]: p for p in mine.get("pills", [])}
    ok("S4:★★★ 筛选胶囊：三枚 66/79/92 宽 @381/453/538,231 ＋ 搜索 32×32 @636,231"
       "（== 源站 raw）",
       [clone_pill_map.get(k, {}).get("summary")
        for k in ("性别", "年龄段", "文化区域")]
       == [{"x": 381, "y": 231, "w": 66, "h": 32},
           {"x": 453, "y": 231, "w": 79, "h": 32},
           {"x": 538, "y": 231, "w": 92, "h": 32}]
       and mine.get("tools", {}).get("搜索角色名称或描述")
       == {"x": 636, "y": 231, "w": 32, "h": 32}
       and [p["summary"] for p in src_pills]
       == [{"x": 381, "y": 231, "w": 66, "h": 32},
           {"x": 453, "y": 231, "w": 79, "h": 32},
           {"x": 538, "y": 231, "w": 92, "h": 32}],
       {"clone": {k: clone_pill_map.get(k, {}).get("summary")
                  for k in ("性别", "年龄段", "文化区域")},
        "clone搜索": mine.get("tools", {}).get("搜索角色名称或描述"),
        "源站raw": [(p["label"], p["summary"]) for p in src_pills]})

    # ── S5 右侧簇：多选 ＋ 视图切换药丸（几何与源站 raw 逐项相同）
    src_tools = {d["aria"]: d["box"] for d in s_mine["头部"] if d["aria"]}
    ok("S5:★★★ 右侧簇：多选 32×32 @1438,231、列表模式 26×26 @1477,234、"
       "宫格模式 26×26 @1510,234（== 源站 raw）",
       mine.get("tools", {}).get("多选") == {"x": 1438, "y": 231, "w": 32, "h": 32}
       and mine.get("tools", {}).get("列表模式") == {"x": 1477, "y": 234, "w": 26, "h": 26}
       and mine.get("tools", {}).get("宫格模式") == {"x": 1510, "y": 234, "w": 26, "h": 26}
       and src_tools.get("多选") == {"x": 1438, "y": 231, "w": 32, "h": 32}
       and src_tools.get("列表模式") == {"x": 1477, "y": 234, "w": 26, "h": 26}
       and src_tools.get("宫格模式") == {"x": 1510, "y": 234, "w": 26, "h": 26},
       {"clone": {k: mine.get("tools", {}).get(k)
                  for k in ("多选", "列表模式", "宫格模式")},
        "源站raw": {k: src_tools.get(k)
                    for k in ("多选", "列表模式", "宫格模式")}})

    # ── S6 下拉：展开态 180 宽 @381,271（top-10）＋ 收起态读数 303（失真）
    #    ＋ 命中测试**精确区分**展开/收起 ⟹ ★ 这条同时是 batch 826 §5.3 的更正
    dd = expanded.get("下拉详情") or []
    dd_map = {d["key"]: d for d in dd}
    src_open = {d["label"]: d for d in src_dd["展开 性别 后的 details"]}
    opts = expanded.get("options", [])
    hit_true = sorted(o["text"] for o in opts if o["hit"])
    hit_false = sorted(o["text"] for o in opts if not o["hit"])
    src_opts = src_dd["展开 性别"]
    ok("S6:★★★ 下拉：展开态面板 180 宽 @381,271（top-10）＋ 收起态读数 303（**失真**）"
       "＋ **命中测试**精确区分「性别可命中 / 其余两组不可命中」",
       dd_map.get("性别", {}).get("open") is True
       and dd_map.get("性别", {}).get("panel") == {"x": 381, "y": 271, "w": 180, "h": 122}
       and dd_map.get("年龄段", {}).get("panel") == {"x": 453, "y": 303, "w": 180, "h": 194}
       and src_open.get("性别", {}).get("panel") == {"x": 381, "y": 271, "w": 180, "h": 122}
       and hit_true == ["中性", "女", "男"]
       and hit_false == sorted(["儿童", "少年", "青年", "中年", "老年",
                                "东亚", "欧美", "中东", "非洲", "其他"])
       and sorted(o["text"] for o in src_opts if o["命中"]) == ["中性", "女", "男"],
       {"clone展开态": dd_map, "clone命中": hit_true,
        "clone不可命中": hit_false,
        "源站raw展开态": {k: v["panel"] for k, v in src_open.items()},
        "源站raw命中": sorted(o["text"] for o in src_opts if o["命中"]),
        "★更正": "batch 826 §5.3 写的「祖先 opacity:0」是错的；真因是原生 <details> "
               "收起时子节点仍在 DOM 且自身 computed style 报 visible ⟹ 只能靠命中测试"})

    # ── S7 选项逐字：我的角色库（其他）vs 官方角色库（奇幻）
    mine_culture = clone_pill_map.get("文化区域", {}).get("options")
    off_culture = {p["key"]: p for p in official.get("pills", [])}.get(
        "文化区域", {}).get("options")
    src_mine_texts = {e["text"] for e in s_mine["可见叶子文本"]}
    src_off_texts = {e["text"] for e in s_official["可见叶子文本"]}
    ok("S7:★★★ 选项逐字：性别 男/女/中性、年龄段 儿童…老年、"
       "文化区域「我的角色库」= 其他 而「官方角色库」= **奇幻**",
       clone_pill_map.get("性别", {}).get("options") == ["男", "女", "中性"]
       and clone_pill_map.get("年龄段", {}).get("options")
       == ["儿童", "少年", "青年", "中年", "老年"]
       and mine_culture == ["东亚", "欧美", "中东", "非洲", "其他"]
       and off_culture == ["东亚", "欧美", "中东", "非洲", "奇幻"]
       and "其他" in src_mine_texts and "奇幻" not in src_mine_texts
       and "奇幻" in src_off_texts and "其他" not in src_off_texts,
       {"clone我的角色库文化区域": mine_culture,
        "clone官方角色库文化区域": off_culture,
        "源站raw（我的角色库页签）": sorted(t for t in src_mine_texts
                                   if t in ("东亚", "欧美", "中东", "非洲", "其他", "奇幻")),
        "源站raw（官方角色库页签）": sorted(t for t in src_off_texts
                                   if t in ("东亚", "欧美", "中东", "非洲", "其他", "奇幻")),
        "★为什么两个页签不一样": "源站 bundle：mine 页签走写死的 lq 映射"
                        "（east_asia/europe/middle_east/africa/other），"
                        "official 页签走服务端下发的筛选配置（第五项是「奇幻」）"})

    # ── S8 卡片：244×434 @y=321 ＋ 相邻 x 差恒 246（== 源站 raw 的等差）
    src_cards = [c for c in s_mine["卡片图"] if c["box"]["w"] == 244]
    src_pitch = _diffs([c["box"]["x"] for c in src_cards])
    clone_cards = mine.get("cards", [])
    clone_pitch = _diffs([c["box"]["x"] for c in clone_cards])
    ok("S8:★★★ 卡片：244×434 @y=321 ＋ 相邻 x 差恒 246（源站 raw 同样是 246 等差）",
       bool(clone_cards)
       and all(c["box"]["w"] == 244 and c["box"]["h"] == 434 and c["box"]["y"] == 321
               for c in clone_cards)
       and all(c["img"]["w"] == 244 and c["img"]["h"] == 434 and c["img"]["y"] == 321
               for c in clone_cards)
       and set(clone_pitch) == {246}
       and set(src_pitch) == {246}
       and len(src_cards) >= 10,
       {"clone卡片数": len(clone_cards),
        "clone相邻差": sorted(set(clone_pitch)),
        "源站raw常规卡片数": len(src_cards),
        "源站raw相邻差": sorted(set(src_pitch)),
        "源站raw首卡": src_cards[0]["box"] if src_cards else None,
        "★源站那条 291 宽的读数": "源站 raw 里每页签的第一张图读数是 291 宽"
                         "（原因未查明，可能是悬停态的覆盖层）⟹ 本批不据此设判据"})

    # ── S9 名字组：我的角色库 =「创建新角色」@925,783 ＋ 官方角色库 =「甜妹/清新少女」@901,783
    #    ＋ 官方页签那枚 26×26 快捷操作 @993,781
    src_mine_name = [e for e in s_mine["可见叶子文本"] if e["text"] == "创建新角色"]
    src_off_name = [e for e in s_official["可见叶子文本"]
                    if e["text"] == "甜妹/清新少女"]
    ok("S9:★★★ 名字组：**居中**一行（名字 ＋ 26×26 快捷操作）"
       "—— 我的角色库「创建新角色」@925,783 ＋ 官方角色库「甜妹/清新少女」@901,783、"
       "快捷 @993,781",
       mine.get("name", {}).get("text") == "创建新角色"
       and mine.get("name", {}).get("box") == {"x": 925, "y": 783, "w": 70, "h": 22}
       and mine.get("quick") is None
       and official.get("name", {}).get("text") == "甜妹/清新少女"
       and official.get("name", {}).get("box") == {"x": 901, "y": 783, "w": 88, "h": 22}
       and official.get("quick") == {"x": 993, "y": 781, "w": 26, "h": 26}
       and src_mine_name and src_mine_name[0]["box"]
       == {"x": 925, "y": 783, "w": 70, "h": 22}
       and src_off_name and src_off_name[0]["box"]
       == {"x": 901, "y": 783, "w": 88, "h": 22},
       {"clone我的角色库": mine.get("name"), "clone我的角色库快捷": mine.get("quick"),
        "clone官方角色库": official.get("name"), "clone官方角色库快捷": official.get("quick"),
        "源站raw": [src_mine_name[0]["box"] if src_mine_name else None,
                    src_off_name[0]["box"] if src_off_name else None],
        "★为什么两个页签的快捷操作不一样": "源站 bundle：快捷操作只挂在**真实角色**上，"
                              "「创建新角色」占位上没有"})

    # ── S10 底部滚动条：input[type=range] aria=角色列表 1158×12 @381,819
    src_range = [i for i in s_mine["input"] if i["type"] == "range"][0]
    ok("S10:★★ 底部滚动条：`<input type=range aria-label=「角色列表」>` 1158×12 @381,819"
       "（== 源站 raw）",
       mine.get("range", {}).get("aria") == "角色列表"
       and mine.get("range", {}).get("box") == {"x": 381, "y": 819, "w": 1158, "h": 12}
       and src_range["aria"] == "角色列表"
       and src_range["box"] == {"x": 381, "y": 819, "w": 1158, "h": 12},
       {"clone": mine.get("range"), "源站raw": src_range})

    # ── S11 底部 CTA（**我的角色库**那一支）：居中单枚白底 116×40 @902,856
    mine_cta = mine.get("cta", [])
    ok("S11:★★★ 底部 CTA（我的角色库页签）：**居中单枚**白底「创建新角色」116×40 @902,856",
       len(mine_cta) == 1
       and mine_cta[0]["kind"] == "create"
       and mine_cta[0]["text"] == "创建新角色"
       and mine_cta[0]["box"] == {"x": 902, "y": 856, "w": 116, "h": 40}
       and mine_cta[0]["bg"] == "rgb(255, 255, 255)"
       and s_mine["底部CTA"][0]["text"] == "创建新角色"
       and s_mine["底部CTA"][0]["box"] == {"x": 902, "y": 856, "w": 116, "h": 40}
       and s_mine["底部CTA"][0]["bg"] == "rgb(255, 255, 255)",
       {"clone": mine_cta, "源站raw": s_mine["底部CTA"]})

    # ── S13 底部 CTA（**官方角色库**那一支）：左侧 ghost ＋ 居中组两枚
    #     ⟹ ★ 与 S11 **刻意分开**（读不同的字段）⟹ 阴性对照才只翻自己那一条
    off_cta = official.get("cta", [])
    src_off_cta = s_official["底部CTA"]
    src_off_by_text = {d["text"]: d for d in src_off_cta if d["text"]}
    ok("S13:★★★ 底部 CTA（官方角色库页签）：左侧「创建新角色」120×40 @385,856（透明）"
       "＋ 居中组 [「添加到画布」120×40 @843,856 ＋「编辑角色」106×40 @971,856（白底）]",
       [c["kind"] for c in off_cta] == ["create", "add-to-canvas", "edit"]
       and off_cta[0]["box"] == {"x": 385, "y": 856, "w": 120, "h": 40}
       and off_cta[0]["bg"] == "rgba(0, 0, 0, 0)"
       and off_cta[1]["text"] == "添加到画布"
       and off_cta[1]["box"] == {"x": 843, "y": 856, "w": 120, "h": 40}
       and off_cta[1]["bg"] == "rgba(255, 255, 255, 0.06)"
       and off_cta[2]["text"] == "编辑角色"
       and off_cta[2]["box"] == {"x": 971, "y": 856, "w": 106, "h": 40}
       and off_cta[2]["bg"] == "rgb(255, 255, 255)"
       and src_off_by_text.get("创建新角色", {}).get("box")
       == {"x": 385, "y": 856, "w": 120, "h": 40}
       and src_off_by_text.get("添加到画布", {}).get("box")
       == {"x": 843, "y": 856, "w": 120, "h": 40}
       and src_off_by_text.get("编辑角色", {}).get("box")
       == {"x": 971, "y": 856, "w": 106, "h": 40},
       {"clone": off_cta,
        "源站raw": src_off_cta,
        "★算式": "居中组 = 120 + 8(gap) + 106 = 234 ⟹ x = 960-117 = 843"})

    # ── S12 静态锚点：src 的**代码**里**没有**旧词、**有**新词
    #    ★ ★★ 必须先去掉注释：本组件的注释里**故意**写清了旧形态的词
    #       （那是本批的考古记录）⟹ 不去注释就判 ⟹ 判据读错了字段。
    panel_src, css_src, next_src = src_texts
    code = strip_comments(panel_src)
    old_words = ["公共角色库", "合规素材库", "应用至画布", "承诺书", "种族", "时代",
                 "华语", "日韩", "东南亚"]
    new_words = ["我的角色库", "官方角色库", "添加到画布", "创建新角色", "编辑角色",
                 "角色造型室", "生成其他年龄版本", "查看角色资产"]
    ok("S12:★★ 静态锚点：面板 src 的**代码**里**零**旧词（2026-09-07 那套）"
       "＋ 八处新词都在 ＋ CSS 里几何走普通 CSS ＋ next.config 放了 allowedDevOrigins",
       not [w for w in old_words if w in code]
       and all(w in code for w in new_words)
       and "allowedDevOrigins" in next_src
       and "127.0.0.1" in next_src
       and "cs-panel" in css_src and "top: 40px" in css_src,
       {"src代码里还在的旧词": [w for w in old_words if w in code],
        "src代码里缺的新词": [w for w in new_words if w not in code],
        "next.config 放了 allowedDevOrigins": "allowedDevOrigins" in next_src,
        "★判据读的是去掉注释后的代码": True})

    # ── S14 「查看角色资产」是**悬停才显形**（源站 bundle: opacity-0 + group-hover）
    #    ★ 「我的角色库」页签的当前项是「创建新角色」占位 ⟹ **没有**这枚浮层 ⟹
    #    ★ 只在「官方角色库」页签（当前项是真实角色）才有。
    bundle_overlay = src_bundle.get("view_assets_overlay", "")
    off_assets = official.get("assets") or {}
    ok("S14:★★ 「查看角色资产」在 clone 与源站**都是默认 opacity:0**（悬停才显形）"
       "＋ 居中于卡片 ＋ 32 高（我的角色库页签没有这枚，因为当前项是占位）",
       (mine.get("assets") is None)
       and off_assets.get("opacity") == "0"
       and off_assets.get("box", {}).get("h") == 32
       and off_assets.get("box", {}).get("x") == 900
       and "opacity-0" in bundle_overlay
       and "group-hover:opacity-100" in bundle_overlay
       and "characterStudioViewAssets" in bundle_overlay,
       {"clone我的角色库": mine.get("assets"),
        "clone官方角色库": official.get("assets"),
        "源站bundle片段": bundle_overlay[:160],
        "★源站raw里读不到它": "源站 raw 的「可见叶子文本」里**没有**「查看角色资产」"
                       "⟹ 因为它 opacity:0 ⟹ 印证「悬停才显形」"})

    # ── S15 真交互：点「添加到画布」⟹ 面板关闭
    ok("S15:★★ **真实鼠标**点「添加到画布」⟹ 面板**关闭**（真交互的证据）",
       clone.get("点添加到画布后面板关着") is True,
       {"点后面板关着": clone.get("点添加到画布后面板关着")})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def _ret(clone, src, src_details, src_dd, src_bundle, src_i18n, src_texts,
         probe_src):
    return (clone, src, src_details, src_dd, src_bundle, src_i18n, src_texts,
            probe_src)


def n1_no_hydration(clone, *rest):
    c = copy.deepcopy(clone)
    c["hydration"]["hasOnClick"] = False
    return (c,) + rest


def n2_probe_writes_store(clone, src, src_details, src_dd, src_bundle, src_i18n,
                           src_texts, probe_src):
    """在**探针区内部**塞一个 store 写调用 ⟹ S1 翻红（前提真被读）。

    ★ ★★ 必须塞进**探针区里面**：S1 只扫探针区 ⟹ 塞在区外它就扫不到
    ⟹ ★★ 顺带说明：判据扫自己所在的文件时，**必须限定范围**，
    否则「对照里写一个假的 store 调用」会把对照自己变成判红的那个 ⟹ 自指陷阱。
    """
    i = probe_src.find(PROBE_END)
    fake = (probe_src[:i] + "\n# fake: store.setState({})\n" + probe_src[i:]
            if i > 0 else probe_src + "\n# fake: store.setState({})\n")
    return (clone, src, src_details, src_dd, src_bundle, src_i18n, src_texts,
            fake)


def n3_panel_size(clone, *rest):
    c = copy.deepcopy(clone)
    c["我的角色库"]["outer"]["w"] = 1280
    return (c,) + rest


def n4_tab_rename(clone, *rest):
    c = copy.deepcopy(clone)
    c["我的角色库"]["tabs"][0]["text"] = "公共角色库"
    return (c,) + rest


def n5_pill_width(clone, *rest):
    c = copy.deepcopy(clone)
    for p in c["我的角色库"]["pills"]:
        if p["key"] == "性别":
            p["summary"]["w"] = 68
    return (c,) + rest


def n6_tool_x(clone, *rest):
    c = copy.deepcopy(clone)
    c["我的角色库"]["tools"]["多选"]["x"] = 1435
    return (c,) + rest


def n7_dropdown_y(clone, *rest):
    c = copy.deepcopy(clone)
    for d in c["展开性别"]["下拉详情"]:
        if d["key"] == "性别":
            d["panel"]["y"] = 300
    return (c,) + rest


def n8_culture_official(clone, *rest):
    c = copy.deepcopy(clone)
    for p in c["官方角色库"]["pills"]:
        if p["key"] == "文化区域":
            p["options"] = ["东亚", "欧美", "中东", "非洲", "其他"]
    return (c,) + rest


def n9_card_pitch(clone, *rest):
    c = copy.deepcopy(clone)
    c["我的角色库"]["cards"][1]["box"]["x"] += 4
    return (c,) + rest


def n10_name_y(clone, *rest):
    c = copy.deepcopy(clone)
    c["官方角色库"]["name"]["box"]["y"] = 780
    return (c,) + rest


def n11_range_width(clone, *rest):
    c = copy.deepcopy(clone)
    c["我的角色库"]["range"]["box"]["w"] = 1150
    return (c,) + rest


def n12_mine_cta_x(clone, *rest):
    c = copy.deepcopy(clone)
    c["我的角色库"]["cta"][0]["box"]["x"] = 900
    return (c,) + rest


def n13_offline_cta_x(clone, *rest):
    c = copy.deepcopy(clone)
    for cta in c["官方角色库"]["cta"]:
        if cta["kind"] == "edit":
            cta["box"]["x"] = 975
    return (c,) + rest


def n14_old_word_back(clone, src, src_details, src_dd, src_bundle, src_i18n,
                      src_texts, probe_src):
    """在**内存副本**里把「公共角色库」放回面板 src ⟹ S12 翻红。"""
    panel, css, nxt = src_texts
    panel2 = panel.replace("我的角色库", "公共角色库")
    return (clone, src, src_details, src_dd, src_bundle, src_i18n,
            (panel2, css, nxt), probe_src)


def n15_assets_opacity(clone, *rest):
    c = copy.deepcopy(clone)
    c["官方角色库"]["assets"]["opacity"] = "1"
    return (c,) + rest


def n16_add_not_close(clone, *rest):
    c = copy.deepcopy(clone)
    c["点添加到画布后面板关着"] = False
    return (c,) + rest


def main():
    src = json.loads(RAW_SRC_STRUCTURE.read_text(encoding="utf-8"))
    src_details = json.loads(RAW_SRC_DETAILS.read_text(encoding="utf-8"))
    src_dd = json.loads(RAW_SRC_DROPDOWNS.read_text(encoding="utf-8"))
    src_bundle = json.loads(RAW_SRC_BUNDLE.read_text(encoding="utf-8"))
    src_i18n = json.loads(RAW_SRC_I18N.read_text(encoding="utf-8"))
    probe_src = (HERE / "verify-liblib-batch827.py").read_text(encoding="utf-8")
    src_texts = (SRC_CHARACTER.read_text(encoding="utf-8"),
                 SRC_CSS.read_text(encoding="utf-8"),
                 SRC_NEXT_CONFIG.read_text(encoding="utf-8"))

    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport=VIEWPORT, locale="zh-CN")
        pg = ctx.new_page()
        pg.set_default_timeout(25000)
        clone = probe(pg)
        br.close()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(clone, ensure_ascii=False, indent=1),
                   encoding="utf-8")

    checks = build_checks(clone, src, src_details, src_dd, src_bundle, src_i18n,
                          src_texts, probe_src)

    neg = []
    for label, expect, builder in [
        ("N1 把 hydration 读数改成 hasOnClick=false ⟹ S1 翻红（前提真被读）",
         "S1", n1_no_hydration),
        ("N2 在探针源码副本里塞一个 store 写调用 ⟹ S1 翻红",
         "S1", n2_probe_writes_store),
        ("N3 把 clone 面板外框宽改成 1280 ⟹ S2 翻红",
         "S2", n3_panel_size),
        ("N4 把 clone 第一个页签改回「公共角色库」⟹ S3 翻红",
         "S3", n4_tab_rename),
        ("N5 把 clone「性别」胶囊宽改成 68 ⟹ S4 翻红",
         "S4", n5_pill_width),
        ("N6 把 clone「多选」的 x 挪 3px ⟹ S5 翻红",
         "S5", n6_tool_x),
        ("N7 把 clone 展开态下拉面板的 y 改成 300 ⟹ S6 翻红",
         "S6", n7_dropdown_y),
        ("N8 把 clone 官方页签文化区域末位改回「其他」⟹ S7 翻红",
         "S7", n8_culture_official),
        ("N9 把 clone 第二张卡的 x 挪 4px ⟹ S8 翻红",
         "S8", n9_card_pitch),
        ("N10 把 clone 官方页签名字的 y 改成 780 ⟹ S9 翻红",
         "S9", n10_name_y),
        ("N11 把 clone 滚动条宽改成 1150 ⟹ S10 翻红",
         "S10", n11_range_width),
        ("N12 把 clone 我的角色库 CTA 的 x 改成 900 ⟹ S11 翻红",
         "S11", n12_mine_cta_x),
        ("N13 把 clone 官方页签「编辑角色」的 x 改成 975 ⟹ S13 翻红",
         "S13", n13_offline_cta_x),
        ("N14 在内存副本里把「公共角色库」放回面板 src ⟹ S12 翻红",
         "S12", n14_old_word_back),
        ("N15 把 clone「查看角色资产」的 opacity 改成 1 ⟹ S14 翻红",
         "S14", n15_assets_opacity),
        ("N16 把「点添加后面板关着」改成 False ⟹ S15 翻红",
         "S15", n16_add_not_close),
    ]:
        args = builder(clone, src, src_details, src_dd, src_bundle, src_i18n,
                       src_texts, probe_src)
        mc = build_checks(*args)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 827,
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                            "total": len(neg)},
              "checks": checks, "阴性": neg}
    (BATCH / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:78])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:66]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())
