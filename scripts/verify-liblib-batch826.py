#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 826 验收器 —— 画布底部工具条：与源站**当前**构建**逐枚同构**。

## ★ 这一批把「名字差」「多一枚按钮」两个已知差异**归零**

batch 824 记下两个差异（当时只记不改）：
  ★ clone 第 4 枚写「角色库」，源站逐字是「**角色造型室**」
  ★ clone 多一枚「打开工具箱」，源站那一簇里没有

★★ batch 826 的源站取证（2026-10-21，无头 + 登录态）把两件事的**根因**找出来了：
  ① 源站那一簇是 **7 枚**（`data-sidebar-btn` 逐枚枚举）：
     add-node / tool-mode / open-asset / **character-library** / history /
     keyboard / contact ⟹ 第 4 枚的 aria 逐字是「角色造型室」。
  ② 源站的「打开工具箱」在**素材库 popover 内**（第 3 枚，222×52，无 NEW 徽章），
     **不在**底部那一簇里 ⟹ ⟹ clone 把它放错了位置。

⟹ ★★ 归位之后 clone 那一簇的**几何**也对上了：
   7×32 + 6×8(gap) + 9(快捷键的 ml) + 16(p-2) + 2(border) = **299px**
   = 源站实测的容器宽 299px；相邻差 [40,40,40,40,49,40] 与源站逐项相同。

## ★ 判据纪律

- ★ 源站对照**读入库的 raw**（batch 824 的源站读数 + 本批的源站 raw），不是印象
- ★ 判据只认**绝对几何**与**DOM 可见读数**
- ★ **真实鼠标**点击（pointerdown），不用程序化 click 代替
- ★ 阴性对照打在**性质真正读取的字段**上，且**每条只翻它自己那一条**
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
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch826-2026-10-01"
RAW = BATCH / "raw" / "vb826a.json"
RAW_SRC_RAIL = BATCH / "raw" / "source-826-rail.json"
RAW_SRC_ASSET = BATCH / "raw" / "source-826-asset.json"
RAW_SRC_STUDIO = BATCH / "raw" / "source-826-studio.json"
RAW_SRC_I18N = BATCH / "raw" / "source-826-i18n.json"
RAW_SRC_824 = (ROOT / "docs" / "research" / "liblib-canvas-batch824-2026-10-01"
               / "raw" / "source-824-bottombar.json")
SRC_LEFT = ROOT / "src" / "components" / "LeftSidebar.tsx"
SRC_MATERIAL = ROOT / "src" / "components" / "MaterialLibraryPanel.tsx"
SRC_CHARACTER = ROOT / "src" / "components" / "CharacterLibraryPanel.tsx"

PROBE_BEGIN = "# ── ★ 探针区开始"
PROBE_END = "# ── ★ 探针区结束"

BASE_URL = os.environ.get("LIBLIB_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1920, "height": 1080}

# ★ 源站那一簇的 7 枚（`data-sidebar-btn` 逐枚枚举，源站 2026-10-21 实测）
SOURCE_CLUSTER = [
    "添加节点", "移动", "素材库", "角色造型室",
    "生成历史", "快捷键", "教程",
]

# ── ★ 探针区开始 ────────────────────────────────────────────────────────────────
# ★ 判据 S1 只扫**这一段**：探针（跑浏览器的部分）里不允许出现 store 写调用。
# ★ 阴性对照区在探针区**之后** ⟹ 它的文本**不在**扫描范围内
# ★ （否则「对照里写一个假的 store 调用」会把自己判成红 —— 自指陷阱）。
READ_RAIL = """()=>{
  const out={pill:null, buttons:[], dot:null, orb:null};
  const add=document.querySelector('button[aria-label="添加节点"]');
  const pill=add?add.parentElement:null;
  if(!pill) return out;
  const pr=pill.getBoundingClientRect();
  out.pill={x:pr.x,y:pr.y,w:pr.width,h:pr.height,
            cls:(pill.getAttribute('class')||'')};
  const all=[...pill.querySelectorAll(':scope > button')];
  for(const b of all){
    if(b.hasAttribute('data-tv-director-trigger')){
      const r=b.getBoundingClientRect();
      out.orb={x:r.x,y:r.y,w:r.width,h:r.height,
               aria:b.getAttribute('aria-label')||''};
      continue;
    }
    const r=b.getBoundingClientRect();
    const svg=b.querySelector('svg');
    const sr=svg?svg.getBoundingClientRect():null;
    out.buttons.push({aria:b.getAttribute('aria-label')||'',
      title:b.getAttribute('title')||'',
      x:r.x,y:r.y,w:r.width,h:r.height,
      svg: sr? [Math.round(sr.width*10)/10,Math.round(sr.height*10)/10]:null});
  }
  const dot=pill.querySelector('[data-studio-new-dot]');
  if(dot){
    const r=dot.getBoundingClientRect();
    const cs=getComputedStyle(dot);
    out.dot={exists:true,x:r.x,y:r.y,w:r.width,h:r.height,
             opacity:cs.opacity,display:cs.display,bg:cs.backgroundColor};
  } else { out.dot={exists:false}; }
  return out;}"""

READ_MATERIAL = """()=>{
  const p=document.querySelector('[data-liblib-overlay="primary:material"]');
  if(!p) return null;
  const r=p.getBoundingClientRect();
  const h2=p.querySelector('h2');
  const entries=[...p.querySelectorAll('[data-material-entry]')].map(b=>{
    const br=b.getBoundingClientRect();
    const t=(b.textContent||'').trim().replace(/\\s+/g,' ');
    const svg=b.querySelector('svg');
    const sr=svg?svg.getBoundingClientRect():null;
    return {label:b.getAttribute('data-material-entry')||'',
      text:t, hasNEW:t.indexOf('NEW')>=0,
      svg: sr? [Math.round(sr.width*10)/10,Math.round(sr.height*10)/10]:null,
      x:br.x,y:br.y,w:br.width,h:br.height};
  });
  return {panel:{x:r.x,y:r.y,w:r.width,h:r.height},
          title:(h2?h2.textContent:'').trim(), entries};}"""

READ_CHARACTER = """()=>{
  const p=document.querySelector('[data-liblib-overlay="primary:character"]');
  if(!p) return null;
  const r=p.getBoundingClientRect();
  return {aria:p.getAttribute('aria-label')||'',
          panel:{x:r.x,y:r.y,w:r.width,h:r.height},
          tabs:[...p.querySelectorAll('[data-clib-tabs] button')]
                 .map(b=>(b.textContent||'').trim())};}"""


def read_toolbox_open(page):
    return page.evaluate("""()=>{
      const p=document.querySelector('[data-liblib-overlay="primary:toolbox"]');
      if(!p) return false;
      const r=p.getBoundingClientRect();
      return r.width>0 && r.height>0;}""")


def click_real(page, locator):
    """**真实鼠标**点击一个 locator（产生 pointerdown）。"""
    locator.scroll_into_view_if_needed(timeout=4000)
    bb = locator.bounding_box()
    if not bb:
        return False
    page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
    return True


def click_real_at(page, box):
    """**真实鼠标**点击（产生 pointerdown）⟹ ★ 不是程序化 click。

    ★ 用**读数里的坐标**点，而不是用名字找元素 ⟹
    ★ 「某一枚被改名」不会连带影响点击路径 ⟹ 阴性对照才只翻它自己那一条。
    """
    page.mouse.click(box["x"] + box["w"] / 2, box["y"] + box["h"] / 2)
    return True


def probe(page):
    page.goto(f"{BASE_URL}/?batch70=1", wait_until="networkidle", timeout=90_000)
    page.wait_for_timeout(900)

    out = {"viewport": VIEWPORT}
    out["簇·初始"] = page.evaluate(READ_RAIL)
    rail = out["簇·初始"]
    if len(rail["buttons"]) < 4:
        raise RuntimeError("读到的簇按钮不足 4 枚：%r" % (rail,))

    # ① 点第 3 枚（素材库）⟹ 读素材库面板
    click_real_at(page, rail["buttons"][2])
    page.wait_for_timeout(600)
    out["素材库面板"] = page.evaluate(READ_MATERIAL)

    # ② 点面板里那枚「打开工具箱」⟹ 工具箱面板应当打开
    entry = page.locator('[data-material-entry="打开工具箱"]')
    out["素材库里有打开工具箱"] = entry.count() == 1
    if out["素材库里有打开工具箱"]:
        click_real(page, entry)
        page.wait_for_timeout(600)
    out["点后工具箱面板开着"] = read_toolbox_open(page)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # ③ 点第 4 枚（角色造型室）⟹ 角色面板 + 蓝点应消失
    click_real_at(page, rail["buttons"][3])
    page.wait_for_timeout(700)
    out["角色面板"] = page.evaluate(READ_CHARACTER)
    out["簇·点完角色入口"] = page.evaluate(READ_RAIL)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # ④ 刷新 ⟹ 蓝点应**仍**消失（localStorage 记忆，源站同款）
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(900)
    out["簇·刷新后"] = page.evaluate(READ_RAIL)
    return out


# ── ★ 探针区结束 ────────────────────────────────────────────────────────────────

# ── 判据（纯函数：吃读数吐检查）───────────────────────────────────────────────
def _diffs(xs):
    return [round(xs[i + 1] - xs[i], 1) for i in range(len(xs) - 1)]


def build_checks(clone, src824, src_asset, src_i18n, src_rail, src_texts,
                 probe_src):
    C = []

    def ok(cid, cond, detail=None):
        # ★★★ 参数顺序必须与**调用点**一致（cid, cond, detail）。
        # ★ 之前这里写成 (cid, name, cond, detail)，而调用点只给了 3 个 ⟹
        # ★ `cond` 收到的是**详情字典** ⟹ `bool(dict)` 恒真 ⟹
        # ★★ 门禁「全绿」却是**空转**的 ⟹ ★★ 这正是「跑通了 ≠ 看到了」。
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    rail = clone["簇·初始"]
    names = [b["aria"] for b in rail["buttons"]]
    xs = [b["x"] for b in rail["buttons"]]
    boxes = [(b["w"], b["h"]) for b in rail["buttons"]]

    src_names = [d["aria"] for d in src824["底部中间"]
                 if d["aria"] != "TV Director"]
    src_xs = [d["矩形"]["x"] for d in src824["底部中间"]
              if d["aria"] != "TV Director"]
    src_diffs = _diffs(src_xs)
    src_span = (src_xs[-1] + 32) - src_xs[0]

    # ── S1 前提：读到了东西，且探针零 store 写调用
    i0 = probe_src.find(PROBE_BEGIN)
    j0 = probe_src.find(PROBE_END)
    region = probe_src[i0:j0] if 0 <= i0 < j0 else probe_src
    store_writes = re.findall(r"\.(setState|addNode|removeNode|updateCamera)\s*\(",
                              region)
    ok("S1:★★ **前提**：簇按钮 7 枚、容器有宽高；探针源码**零 store 写调用**",
       len(rail["buttons"]) == 7
       and rail["pill"]["w"] > 0 and rail["pill"]["h"] > 0
       and not store_writes,
       {"枚数": len(rail["buttons"]), "容器": rail["pill"],
        "扫的区间": "探针区（%s … %s）" % (PROBE_BEGIN, PROBE_END),
        "探针里的 store 写调用": store_writes})

    # ── S2 逐字同名同序（对**入库的源站读数**）
    ok("S2:★★★ **逐字同名同序**：clone 那一簇 7 枚的可及名序列 == 源站 raw",
       names == src_names == SOURCE_CLUSTER,
       {"clone": names, "源站raw": src_names, "本脚本常量": SOURCE_CLUSTER})

    # ── S3 几何：相邻差 + 簇宽 + 药丸容器宽
    src_container = src_asset["素材库popover"].get("容器宽")  # 可能没有
    ok("S3:★★★ **几何**：相邻差序列与簇宽与源站 raw 逐项相同",
       _diffs(xs) == src_diffs
       and abs(((xs[-1] + boxes[-1][0]) - xs[0]) - src_span) <= 0.6,
       {"clone相邻差": _diffs(xs), "源站raw相邻差": src_diffs,
        "clone簇宽": round((xs[-1] + boxes[-1][0]) - xs[0], 1),
        "源站raw簇宽": src_span})

    # ── S3b 药丸容器宽：与**入库的源站 raw**（source-826-rail.json）一致
    src_pill_w = src_rail["A 工具条"]["容器"]["rect"]["w"]
    ok("S3b:★★★ **药丸容器宽** == 源站 raw 的实测值（去掉那枚多余的按钮后正好对上）",
       abs(rail["pill"]["w"] - src_pill_w) <= 1.0,
       {"clone容器宽": round(rail["pill"]["w"], 1),
        "源站raw容器宽": src_pill_w,
        "算式": "7×32 + 6×8 + 9(快捷键ml) + 16(p-2) + 2(border) = 299"})

    # ── S4 源站底部那一行**没有**「打开工具箱」
    # ★ 读**源站 raw 的底部一行按钮数组**（与 S9 读的元素数组是**两份不同的数据**）
    # ⟹ ★ 阴性对照可以只打在这份数据上 ⟹ 每条阴性**只**翻它自己那一条。
    src_bottom_row = [e["aria"] for e in
                      src_rail["A 工具条"]["底部一行按钮（按x排序）"]]
    ok("S4:★★★ 源站底部那一行**没有**「打开工具箱」（它在素材库 popover 里，不在工具条）",
       "打开工具箱" not in src_bottom_row,
       {"源站底部一行可及名": src_bottom_row})

    # ── S5 素材库面板三枚：逐字 + 顺序 + NEW 只在前两枚 + 52 高 + 20px 图标
    mat = clone.get("素材库面板") or {}
    mat_entries = mat.get("entries", [])
    src_entries = src_asset["素材库popover"]["入口"]
    src_labels = [e["leaves"][0] for e in src_entries]
    ok("S5:★★★ 素材库面板里的入口**逐字与顺序**与源站 raw 相同，且 NEW 只在前两枚",
       [e["label"] for e in mat_entries] == src_labels
       and [e["hasNEW"] for e in mat_entries] == [True, True, False]
       and [e["h"] for e in mat_entries] == [52, 52, 52]
       and all(e["svg"] == [20, 20] for e in mat_entries),
       {"clone": [(e["label"], e["hasNEW"], e["h"], e["svg"])
                  for e in mat_entries],
        "源站raw": [(e["leaves"][0], e["hasNEW"], e["rect"]["h"], e["svg"])
                    for e in src_entries]})

    # ── S6 真实鼠标点面板里那枚「打开工具箱」⟹ 工具箱面板打开
    ok("S6:★★★ **真实鼠标**点素材库面板里的「打开工具箱」⟹ 工具箱面板**打开**",
       clone.get("素材库里有打开工具箱") is True
       and clone.get("点后工具箱面板开着") is True,
       {"面板里有那枚": clone.get("素材库里有打开工具箱"),
        "点后工具箱开着": clone.get("点后工具箱面板开着")})

    # ── S7 角色造型室：面板 aria + 页签逐字
    ch = clone.get("角色面板") or {}
    ok("S7:★★ 点「角色造型室」⟹ 面板可及名 == 「角色造型室」、首个页签 == 「官方角色库」",
       ch.get("aria") == "角色造型室"
       and (ch.get("tabs") or [])[:1] == ["官方角色库"]
       and len(ch.get("tabs") or []) == 2,
       {"面板aria": ch.get("aria"), "页签": ch.get("tabs"),
        "源站当前页签": ["我的角色库", "官方角色库"],
        "源站i18n": {k: src_i18n["抽出的键"].get(k)
                     for k in ("characterStudioMyLibrary",
                               "characterStudioOfficialLibrary",
                               "publicCharacterLibrary")}})

    # ── S8 蓝点 new-dot：初始可见 → 点入口后消失 → 刷新后仍消失
    dot0 = clone["簇·初始"]["dot"]
    dot1 = clone["簇·点完角色入口"]["dot"]
    dot2 = clone["簇·刷新后"]["dot"]
    ok("S8:★★ 源站那枚**蓝色 new-dot**：初始可见 → 点入口后消失 → 刷新后**仍**消失（记忆）",
       dot0.get("exists") is True
       and abs(dot0.get("w", 0) - 8) <= 1 and abs(dot0.get("h", 0) - 8) <= 1
       and dot0.get("opacity") == "1"
       and dot1.get("exists") is False
       and dot2.get("exists") is False,
       {"初始": dot0, "点完入口": dot1, "刷新后": dot2})

    # ── S9 源站对照（读**本批自己的入库源站 raw**：source-826-rail.json）
    # ★ 与 S2/S3 读的那份 raw（batch 824 的）**刻意分开**；也与 S4 读的
    #   「底部一行按钮」数组分开 ⟹ ★ 阴性对照可以精确地只打中某一条。
    rail_els = src_rail["A 工具条"]["带sidebar-btn/guide-target的元素"]
    src_keys = [e["key"] for e in rail_els if e.get("key")]
    src_arias = [e["aria"] for e in rail_els if e.get("key")]
    ok("S9:★★★ **源站对照**（读**本批的入库源站 raw**）：源站那一簇 7 枚"
       "（data-sidebar-btn 逐枚）、第 4 枚逐字「角色造型室」、簇里**没有**"
       "「打开工具箱」",
       src_keys == ["add-node", "tool-mode", "open-asset",
                    "character-library", "history", "keyboard", "contact"]
       and src_arias[3] == "角色造型室"
       and "打开工具箱" not in src_arias,
       {"源站簇的 data-sidebar-btn": src_keys,
        "源站簇的可及名": src_arias})

    # ── S10 静态锚点：src 里的三处改动都在
    # ★ src 正文作为**参数**传进来（不在判据里直接读文件）⟹
    # ★ 阴性对照可以只改内存里的副本 ⟹ ★ 不必动磁盘上的文件（更安全）。
    left_src, mat_src, ch_src = src_texts
    ok("S10:★ 静态锚点：rail 段里**没有**「打开工具箱」、**有**「角色造型室」；"
       "素材库面板**有**「打开工具箱」；角色面板可及名 == 「角色造型室」",
       'label="打开工具箱"' not in left_src
       and 'label="角色造型室"' in left_src
       and 'label="角色库"' not in left_src
       and '打开工具箱' in mat_src
       and 'aria-label="角色造型室"' in ch_src
       and '官方角色库' in ch_src,
       {"LeftSidebar 还有 rail 的打开工具箱": 'label="打开工具箱"' in left_src,
        "LeftSidebar 有角色造型室": 'label="角色造型室"' in left_src,
        "MaterialLibraryPanel 有打开工具箱": '打开工具箱' in mat_src,
        "CharacterLibraryPanel 的可及名": 'aria-label="角色造型室"' in ch_src})

    # ── S11 orb 仍在药丸之外（batch 824 的结论不许被本批破坏）
    ok("S11:★★ 药丸**之外**那枚 48×48 的「TV Director」入口**仍在**（batch 824 的结论不被破坏）",
       rail["orb"]["aria"] == "TV Director"
       and abs(rail["orb"]["w"] - 48) <= 0.6 and abs(rail["orb"]["h"] - 48) <= 0.6
       and rail["orb"]["x"] >= rail["buttons"][-1]["x"] + rail["buttons"][-1]["w"],
       {"orb": rail["orb"], "簇末枚右缘":
        rail["buttons"][-1]["x"] + rail["buttons"][-1]["w"]})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def n1_rename(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["簇·初始"]["buttons"][3]["aria"] = "角色库"
    return c, src824, src_asset, src_i18n, src_rail, src_texts, probe_src


def n2_source_raw(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    # ★ 改的是**本批自己的入库源站 raw**（source-826-rail.json）⟹
    # ★ S9（读它）会翻，而 S2/S3（读 batch 824 那份 raw）与 S4（读同一份 raw
    #   的**另一个数组**）**不翻** ⟹ ★ 每条阴性**只**翻它自己那一条。
    s = copy.deepcopy(src_rail)
    for e in s["A 工具条"]["带sidebar-btn/guide-target的元素"]:
        if e.get("key") == "character-library":
            e["aria"] = "角色造型室X"
    return clone, src824, src_asset, src_i18n, s, src_texts, probe_src


def n3_swap_material(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    c = copy.deepcopy(clone)
    e = c["素材库面板"]["entries"]
    e[0], e[1] = e[1], e[0]
    return c, src824, src_asset, src_i18n, src_rail, src_texts, probe_src


def n4_hide_dot(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    c = copy.deepcopy(clone)
    c["簇·初始"]["dot"]["opacity"] = "0"
    return c, src824, src_asset, src_i18n, src_rail, src_texts, probe_src


def n5_shift_x(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    """把 clone 簇里第 3 枚的 x 挪 7px ⟹ 几何判据（S3）翻红。"""
    c = copy.deepcopy(clone)
    c["簇·初始"]["buttons"][2]["x"] += 7
    return c, src824, src_asset, src_i18n, src_rail, src_texts, probe_src


def n6_wide_pill(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    """把 clone 药丸容器宽改成 340 ⟹ 容器宽判据（S3b）翻红。"""
    c = copy.deepcopy(clone)
    c["簇·初始"]["pill"]["w"] = 340
    return c, src824, src_asset, src_i18n, src_rail, src_texts, probe_src


def n7_character_aria(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    """把 clone 角色面板的可及名改回「角色库」⟹ S7 翻红。"""
    c = copy.deepcopy(clone)
    c["角色面板"]["aria"] = "角色库"
    return c, src824, src_asset, src_i18n, src_rail, src_texts, probe_src


def n8_static_anchor(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    """在**内存副本**里把 rail 的「打开工具箱」放回去 ⟹ S10 翻红。"""
    left, mat, ch = src_texts
    left2 = left.replace('label="角色造型室"',
                          'label="打开工具箱"\n          label2="角色造型室"')
    return (clone, src824, src_asset, src_i18n, src_rail, (left2, mat, ch),
            probe_src)


def n9_shrink_orb(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    """把 clone 那枚 orb 改成 40×40 ⟹ S11 翻红。"""
    c = copy.deepcopy(clone)
    c["簇·初始"]["orb"]["w"] = 40
    c["簇·初始"]["orb"]["h"] = 40
    return c, src824, src_asset, src_i18n, src_rail, src_texts, probe_src


def n10_source_bottom_row(clone, src824, src_asset, src_i18n, src_rail, src_texts, probe_src):
    """在源站 raw 的「底部一行」数组里塞进「打开工具箱」⟹ S4 翻红。"""
    s = copy.deepcopy(src_rail)
    s["A 工具条"]["底部一行按钮（按x排序）"].append(
        {"aria": "打开工具箱"})
    return clone, src824, src_asset, src_i18n, s, src_texts, probe_src


def n11_probe_writes_store(clone, src824, src_asset, src_i18n, src_rail,
                           src_texts, probe_src):
    """在**探针区内部**塞一个 store 写调用 ⟹ S1 翻红（前提真被读）。

    ★ ★★ 必须塞进**探针区里面**：S1 只扫探针区 ⟹ 塞在区外它就扫不到
    ⟹ ★★ 顺带说明：判据扫自己所在的文件时，**必须限定范围**，
    否则「对照里写一个假的 store 调用」会把对照自己变成判红的那个 ⟹ 自指陷阱。
    """
    i = probe_src.find(PROBE_END)
    fake = (probe_src[:i] + "\n# fake: store.setState({})\n" + probe_src[i:]
            if i > 0 else probe_src + "\n# fake: store.setState({})\n")
    return (clone, src824, src_asset, src_i18n, src_rail, src_texts, fake)


def n12_toolbox_not_open(clone, src824, src_asset, src_i18n, src_rail,
                          src_texts, probe_src):
    """把「点后面板开着」的读数改成 False ⟹ S6 翻红。"""
    c = copy.deepcopy(clone)
    c["点后工具箱面板开着"] = False
    return (c, src824, src_asset, src_i18n, src_rail,
            src_texts, probe_src)


def main():
    src824 = json.loads(RAW_SRC_824.read_text(encoding="utf-8"))
    src_asset = json.loads(RAW_SRC_ASSET.read_text(encoding="utf-8"))
    src_i18n = json.loads(RAW_SRC_I18N.read_text(encoding="utf-8"))
    src_rail = json.loads(RAW_SRC_RAIL.read_text(encoding="utf-8"))
    probe_src = (HERE / "verify-liblib-batch826.py").read_text(encoding="utf-8")
    src_texts = (SRC_LEFT.read_text(encoding="utf-8"),
                 SRC_MATERIAL.read_text(encoding="utf-8"),
                 SRC_CHARACTER.read_text(encoding="utf-8"))

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

    checks = build_checks(clone, src824, src_asset, src_i18n, src_rail,
                          src_texts, probe_src)

    neg = []
    for label, expect, builder in [
        ("N1 把 clone 簇里第 4 枚改名 ⟹ S2 翻红（逐字同名同序真被读）",
         "S2", n1_rename),
        ("N2 把**本批入库的源站 raw**里第 4 枚改名 ⟹ S9 翻红（源站对照真被读）",
         "S9", n2_source_raw),
        ("N3 把 clone 素材库面板前两枚**对调** ⟹ S5 翻红（顺序真被读）",
         "S5", n3_swap_material),
        ("N4 把蓝点 opacity 改成 0 ⟹ S8 翻红（蓝点真被读）",
         "S8", n4_hide_dot),
        ("N5 把 clone 簇里第 3 枚的 x 挪 7px ⟹ S3 翻红（几何真被读）",
         "S3", n5_shift_x),
        ("N6 把 clone 药丸容器宽改成 340 ⟹ S3b 翻红（容器宽真被读）",
         "S3b", n6_wide_pill),
        ("N7 把 clone 角色面板可及名改回「角色库」⟹ S7 翻红",
         "S7", n7_character_aria),
        ("N8 在内存副本里把 rail 的「打开工具箱」放回去 ⟹ S10 翻红（静态锚点真被读）",
         "S10", n8_static_anchor),
        ("N9 把 clone 那枚 orb 改成 40×40 ⟹ S11 翻红（orb 真被读）",
         "S11", n9_shrink_orb),
        ("N10 在源站 raw 的「底部一行」里塞进「打开工具箱」⟹ S4 翻红",
         "S4", n10_source_bottom_row),
        ("N11 在探针源码副本里塞一个 store 写调用 ⟹ S1 翻红（前提真被读）",
         "S1", n11_probe_writes_store),
        ("N12 把「点后面板开着」的读数改成 False ⟹ S6 翻红",
         "S6", n12_toolbox_not_open),
    ]:
        c2, s2, a2, i2, r2, t2, p2 = builder(clone, src824, src_asset,
                                             src_i18n, src_rail,
                                             src_texts, probe_src)
        mc = build_checks(c2, s2, a2, i2, r2, t2, p2)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 826,
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                            "total": len(neg)},
              "checks": checks, "阴性": neg}
    (BATCH / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:70])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:62]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())
