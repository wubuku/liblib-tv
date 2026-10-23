#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 852 源站探针（**只读**）：导演台**变换类快捷键** V / R / F / X 的实测。

## ★ 靶子与已知结论（来自 `raw/source-852-contract.json`，**机器提取**）

```js
hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])
...
else if("v"===n)iW("translate");
else if("r"===n)iW("rotate");
else if("f"===n)iW("scale");
else if("x"===n)eT(e=>!e);
...
let iW=(0,o.useCallback)(e=>{
  if(t4&&im(),
     "emptyObject"===nf.current.selectedCategory&&"translate"!==e){
    tl("translate"),af.setMode("translate");return}
  tl(e),af.setMode(e)},[im,t4,af]);
...
function p7(e,t){e.translationSnap=t?1:null}
```

★ ⇒ **V/R/F 都切变换模式**（`hY` **含 "f"** ⟹ F 可达）；
★ ⇒ **X 切换网格吸附**（`eT(e=>!e)` ⟹ `snapEnabled` 翻转 ⟹ `translationSnap` 1 / null）；
★ ⇒ **修饰键条件**（`hY` 块的 `&&` 链）：`z`/`g`/`c` 要 ⌘，`d` 要 ⌘⇧，`h` 要**无** ⌘⌥；
   **`v`/`r`/`f`/`x` 没有任何修饰键限制** ⟹ Shift+V 同样生效。

## ★ 三条读数（每条都只用**可见 DOM**，不读内部状态）

1. **变换模式（主读数）**：底部工具栏折叠按钮（`aria-haspopup="menu"`）**点开后的下拉**，
   其中**当前模式那枚**带 `bg-white/8 text-white` ⟹ 读它的**序号**＋**键帽字母**。
   ★ 序号→模式的映射表 **从 `raw/source-852-contract.json` 里解析**
   （源站原文 `R=[{mode:"translate",…,"V"},{mode:"rotate",…,"R"},{mode:"scale",…,"F"}]`），
   ★ **不手打** —— 手打过一次就漏过一个字符，差点把「F 可达」读成「F 是死代码」。
2. **变换模式（副读数）**：折叠按钮里那枚 `<svg>` 的 innerHTML 哈希 ⟹ 同一模式应对应同一段
   ⟹ 用**前后对比**判定「图标有没有变」（自指比较，不依赖手打路径数据）。
3. **网格吸附**：右栏所有 `[role="switch"]` 的 `aria-checked` 列表 ⟹ 按 X 之后
   **哪一枚翻转** ⟹ 那枚**就是**吸附开关（★ 自证式定位，不手打中文标签）。

## ★ 两处「上一版探针踩到的坑」（已修正）

★ 坑 1：`nav button[aria-haspopup="menu"]` 在源站**匹配到的是左栏「帮助」按钮**
  （文档顺序更靠前）⟹ 点开的是**快捷键对话框**（模态）⟹ 右栏被挡住 ⟹ 开关读数变成 0。
  ★ 修法：改用**结构判据**找变换下拉 —— 「恰好 3 枚直接子按钮，且每枚最后一个 span
  是单个大写字母」⟹ 只有变换模式下拉满足。
★ 坑 2：开关读数必须放在**任何点击之前** ⟹ 否则可能被模态/浮层影响。

## ★ 只读保证

★ 只按 **v / r / f / x** 与 **Shift+v** ⟹ ⟹ 全是模式/开关切换，不改画布结构。
★ **绝不按 ⌘V**（源站里 ⌘V 是「粘贴角色」⟹ 会往场景里塞角色 ⟹ 有副作用）。

## 输出

  raw/source-852-transformkeys.json
  images/852src_*.png
"""
import hashlib
import json
import pathlib
import re
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch852-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
CONTRACT = RAW / "source-852-contract.json"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 裁剪区要**同时框住底部胶囊与向上展开的下拉**
#   （源站下拉是 `bottom-[calc(100%+12px)]` ⟹ 在按钮**上方** ⟹ 只框按钮就看不到 active 项）
TOOLBAR_CLIP = {"x": 735, "y": 880, "width": 300, "height": 180}


def h(text) -> str:
    """★ 稳定哈希（★ 不用内置 hash()：它对 str 每次进程都不同 ⟹ 证据不可复现）"""
    return hashlib.md5((text or "").encode("utf-8")).hexdigest()[:12]


def load_mode_table() -> dict:
    """★ 从**入库的源站原文**里解析「下拉序号 / 键帽字母 → 模式」映射表。

    ★ 不手写映射：手抄终端输出时漏过一个字符，就足以把结论弄反
    （本批真踩过：手抄的 `hY` 少了 `"f"`）。
    """
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    src = data["片段"]["底部工具栏的变换模式表 R"]["原文"]
    items = re.findall(r'mode:"([^"]+)"[^}]*?shortcut:"([^"]+)"', src)
    if not items:
        raise SystemExit("★ 契约里没解析出模式表")
    return {
        "顺序": [m for m, _ in items],
        "模式表": dict(items),                 # mode → 键帽字母
        "字母表": {letter: mode for mode, letter in items},  # 键帽字母 → mode（★ 反查用）
        "原文": src,
    }


# ★ 找「变换模式下拉」：恰好 3 枚**直接子**按钮，且每枚最后一个 span 是单个大写字母
FIND_DROPDOWN = r"""()=>{
  const popups = Array.from(document.querySelectorAll('div')).filter(d=>{
    const bs = Array.from(d.querySelectorAll(':scope > button'));
    if (bs.length !== 3) return false;
    return bs.every(b=>{
      const sp = Array.from(b.querySelectorAll('span')).map(s=>(s.textContent||'').trim());
      return sp.length >= 2 && /^[A-Z]$/.test(sp[sp.length-1]);
    });
  });
  if (!popups.length) return {找到:false};
  const p = popups[popups.length-1];
  const owner = p.closest('nav') ? p.closest('nav') : p.parentElement;
  const btn = owner ? owner.querySelector('button[aria-haspopup="menu"]') : null;
  const svg = btn ? btn.querySelector('svg') : null;
  const br = btn ? btn.getBoundingClientRect() : null;
  return {找到:true,
    折叠按钮:{存在:!!btn, bbox:br?[Math.round(br.x),Math.round(br.y),Math.round(br.width),Math.round(br.height)]:null,
              aria标签:btn?btn.getAttribute('aria-label'):null,
              svg:svg?svg.innerHTML:null},
    下拉项:Array.from(p.querySelectorAll(':scope > button')).map(b=>{
      const sp = Array.from(b.querySelectorAll('span')).map(s=>(s.textContent||'').trim());
      // ★ token 精确匹配：**非** active 那枚的类名里有 `hover:bg-white/8`，
      //   用 `includes('bg-white/8')` 会把三枚全判成 active（上一版真踩到了）。
      //   源站 chunk 原文：active 追加 `bg-white/8 text-white`，非 active 是 `text-white/72 … hover:bg-white/8 …`。
      const tk = String(b.className||'').split(/\s+/);
      return {文字:sp, 类名:b.className,
              active: tk.indexOf('bg-white/8')>=0 && tk.indexOf('text-white')>=0};
    })};
}"""

READ_SWITCHES = r"""()=>{
  const list = Array.from(document.querySelectorAll('[role="switch"]'));
  return list.map(e=>{
    const r=e.getBoundingClientRect();
    return {文本:(e.textContent||'').trim().slice(0,40),
            aria:e.getAttribute('aria-checked'),
            x:Math.round(r.x), y:Math.round(r.y),
            w:Math.round(r.width), h:Math.round(r.height),
            可见:r.width>0&&r.height>0};
  });
}"""

READ_PANEL = r"""()=>{
  const list = Array.from(document.querySelectorAll('[role="switch"]'));
  return {开关数:list.length,
          文本:list.map(e=>(e.textContent||'').trim().slice(0,20))};
}"""



# ★ 冒泡阶段监听器：★ 源站的 keydown 处理器在 **window 捕获阶段**就调了
#   `stopPropagation()+stopImmediatePropagation()`（chunk 里的 `h4`）⟹
#   事件**根本到不了 document 的冒泡阶段** ⟹ 下面这个监听器**应当一个键都收不到**。
#   这不是 bug，这是**源站行为的读数**（导演台吞掉所有按键）。
LISTEN_BUBBLE = r"""()=>{
  window.__bubble=[];
  document.addEventListener('keydown', e=>{
    window.__bubble.push({key:e.key, phase:'bubble', target:e.target?e.target.tagName:''});
  }, false);
  return 'installed';
}"""
READ_BUBBLE = "()=>window.__bubble"

def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def shot(page, name):
    p = SHOTS / ("852src_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip=TOOLBAR_CLIP)
    return p


def mode_from(table, dd):
    """从下拉读数推出模式（★ 序号与键帽字母两条独立路径必须一致）"""
    if not dd.get("找到"):
        return {"模式": None, "原因": "没找到变换模式下拉"}
    items = dd.get("下拉项") or []
    active = [i for i in items if i.get("active")]
    out = {"模式": None, "下拉项数": len(items), "active数": len(active)}
    if len(active) != 1:
        out["原因"] = "active 项不是恰好 1 个"
        out["active文本"] = [a.get("文字") for a in active]
        return out
    idx = items.index(active[0])
    letters = [t for t in active[0].get("文字", []) if t]
    letter = letters[-1] if letters else None
    order = table["顺序"]
    by_index = order[idx] if 0 <= idx < len(order) else None
    by_letter = table["字母表"].get(letter) if letter else None  # ★ 字母 → 模式
    out["下拉序号"] = idx
    out["下拉项文字"] = letters
    out["按序号"] = by_index
    out["按字母"] = by_letter
    out["两条一致"] = (by_index is not None and by_index == by_letter)
    out["模式"] = by_index if out["两条一致"] else None
    return out


def open_transform_dropdown(pg):
    """★ 打开「变换模式下拉」。

    ★ ★ 上一版踩过的坑：按 `button[aria-haspopup="menu"]` 逐个试 ⟹ 文档顺序里
    **左栏「帮助」按钮排在前** ⟹ 点开的是**快捷键对话框（模态）** ⟹
    ① 变换下拉没找到 ② 之后的按键全被模态吞掉（X 按了没反应）。
    ★ 修法：**只认「nav 内恰好 3 枚按钮」的那枚**（源站 chunk 里底部胶囊就是
    变换/截图/动画时间轴三枚）⟹ 左栏那个 nav 有 7 枚 ⟹ 天然被排除。
    """
    n = pg.evaluate(
        "()=>Array.from(document.querySelectorAll('button[aria-haspopup=\"menu\"]'))"
        ".filter(b=>{const r=b.getBoundingClientRect();"
        "if(!(r.width>0&&r.height>0))return false;"
        "const nv=b.closest('nav');return !!nv&&nv.querySelectorAll('button').length===3;}).length")
    if n != 1:
        return {"找到": False, "★候选数": n}, -1
    try:
        cand = pg.locator(
            'button[aria-haspopup="menu"]:visible').filter(has_text="").nth(0)
    except Exception:
        pass
    # ★ 直接用 JS 点（避免 locator 索引与过滤后顺序不一致）
    pg.evaluate(
        "()=>{const b=Array.from(document.querySelectorAll('button[aria-haspopup=\"menu\"]'))"
        ".find(b=>{const r=b.getBoundingClientRect();"
        "if(!(r.width>0&&r.height>0))return false;"
        "const nv=b.closest('nav');return !!nv&&nv.querySelectorAll('button').length===3;});"
        "if(b)b.click();}")
    pg.wait_for_timeout(400)
    dd = pg.evaluate(FIND_DROPDOWN)
    return dd, 0


def main() -> int:
    out = {}
    try:
        table = load_mode_table()
        out["★模式映射表（源站原文解析）"] = {
            "顺序": table["顺序"], "模式表": table["模式表"],
            "字母表": table["字母表"], "原文": table["原文"],
        }
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)

            open_desk(pg)
            # ★ 装冒泡阶段监听器 ⟹ 用来**读出**「源站吞掉所有按键」这个行为
            out["①冒泡监听器"] = pg.evaluate(LISTEN_BUBBLE)
            # ★ 开关读数**必须在任何点击之前**（★ 上一版被模态挡成 0）
            sw_initial = pg.evaluate(READ_SWITCHES)
            out["①初始开关"] = sw_initial
            out["①初始开关数"] = len(sw_initial)
            shot(pg, "initial")

            # ★★ **不要点视口**：点中 3D 视口会**选中一个对象** ⟹ 右栏从「环境面板」
            #   换成「对象面板」 ⟹ `[role="switch"]` 读数直接归零（上一版真踩到了）。
            #   源站的 `h5(e.target)` 只在目标是 input/textarea/select/contenteditable 时早退；
            #   此时 activeElement 是 DIV ⟹ 不需要点任何东西就能满足。
            out["②右栏开关（点视口前）"] = pg.evaluate(READ_PANEL)

            out["②初始activeElement"] = pg.evaluate(
                "()=>{const a=document.activeElement;return {tag:a?a.tagName:''}}")

            # ── 打开变换模式下拉（结构判据）
            dd, cand_idx = open_transform_dropdown(pg)
            out["③下拉识别"] = {
                "候选序号": cand_idx,
                "折叠按钮": dd.get("折叠按钮"),
                "下拉项数": len(dd.get("下拉项") or []),
            }
            out["③初始模式"] = mode_from(table, dd)
            out["③初始svg哈希"] = h(dd.get("折叠按钮", {}).get("svg"))
            shot(pg, "dropdown")

            # ── 逐键实测：v / r / f
            # ★ 键序 R → F → V：每一步都把模式推到**下一个** ⟹ 三步连成一条可判的链
            #   （若先按 V，则初始态本来就是 translate ⟹ 读数「不变」证明力弱）
            for key, label in [("r", "R"), ("f", "F"), ("v", "V")]:
                rec = {}
                try:
                    before = pg.evaluate(FIND_DROPDOWN)
                    if not before.get("找到"):
                        before, _ = open_transform_dropdown(pg)
                        rec["★按前下拉已重开"] = True
                    rec["按前"] = {"模式": mode_from(table, before),
                                   "svg哈希": h(before.get("折叠按钮", {}).get("svg"))}
                    shot(pg, "%s-before" % key)
                    pg.keyboard.press(key)
                    pg.wait_for_timeout(400)
                    after = pg.evaluate(FIND_DROPDOWN)
                    rec["按后"] = {"模式": mode_from(table, after),
                                   "svg哈希": h(after.get("折叠按钮", {}).get("svg"))}
                    rec["svg变了"] = (rec["按前"]["svg哈希"] != rec["按后"]["svg哈希"])
                    rec["开关数"] = pg.evaluate(READ_PANEL)["开关数"]
                    shot(pg, "%s-after" % key)
                except Exception:
                    rec["★异常"] = traceback.format_exc()[-400:]
                out["④按%s" % label] = rec

            # ── Shift+V：源站对 v **没有**修饰键限制 ⟹ Shift+V 也应切到 translate
            #   ★★ 上一版不可判：按之前模式**已经是 translate** ⟹ 「没变」既可能是
            #   「Shift+V 无效」也可能是「本来就是 translate」⟹ 先按 R 走到 rotate 再测。
            try:
                pg.keyboard.press("r")
                pg.wait_for_timeout(400)
                before = pg.evaluate(FIND_DROPDOWN)
                pg.keyboard.down("Shift")
                pg.keyboard.press("v")
                pg.keyboard.up("Shift")
                pg.wait_for_timeout(400)
                after = pg.evaluate(FIND_DROPDOWN)
                out["⑤Shift+V"] = {
                    "按前模式": mode_from(table, before),
                    "按后模式": mode_from(table, after),
                    "svg变了": h(before.get("折叠按钮", {}).get("svg")) != h(after.get("折叠按钮", {}).get("svg")),
                    "★说明": "按前先按过 R ⟹ 模式是 rotate ⟹ Shift+V 若有效应变成 translate",
                }
            except Exception:
                out["★Shift+V异常"] = traceback.format_exc()[-400:]

            # ── X：网格吸附。★ 自证式定位 —— 按下后**哪一枚开关翻转**
            snap = {}
            try:
                sw0 = pg.evaluate(READ_SWITCHES)
                snap["按前开关"] = sw0
                shot(pg, "x-before")
                pg.keyboard.press("x")
                pg.wait_for_timeout(500)
                sw1 = pg.evaluate(READ_SWITCHES)
                snap["按后开关"] = sw1
                shot(pg, "x-after")
                flips = []
                for a, b in zip(sw0, sw1):
                    if a.get("aria") != b.get("aria"):
                        flips.append({"文本": a.get("文本"), "前": a.get("aria"),
                                      "后": b.get("aria"), "x": a.get("x"),
                                      "y": a.get("y")})
                snap["翻转项"] = flips
                snap["翻转项数"] = len(flips)
                # ★ 再按一次 X ⟹ 应当翻回去（X 是「翻转」不是「置位」）
                pg.keyboard.press("x")
                pg.wait_for_timeout(500)
                sw2 = pg.evaluate(READ_SWITCHES)
                flips2 = []
                for a, b in zip(sw1, sw2):
                    if a.get("aria") != b.get("aria"):
                        flips2.append({"文本": a.get("文本"), "前": a.get("aria"),
                                       "后": b.get("aria")})
                snap["再按翻转项"] = flips2
            except Exception:
                snap["★异常"] = traceback.format_exc()[-400:]
            out["⑥按X"] = snap

            # ★ 冒泡阶段一共收到几个键？（★ 期望 0 个 ⟹ 源站在 window 捕获阶段就掐断了）
            bubble = pg.evaluate(READ_BUBBLE) or []
            out["⑦冒泡阶段收到的键"] = bubble
            out["⑦冒泡阶段收到数"] = len(bubble)

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-852-transformkeys.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-852-transformkeys.json")
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
        print("--- 模式映射表 ---", out.get("★模式映射表（源站原文解析）"))
        print("--- 初始开关数 ---", out.get("①初始开关数"))
        for s in (out.get("①初始开关") or []):
            print("    switch:", s)
        print("--- 下拉识别 ---", out.get("③下拉识别"))
        print("--- 初始模式 ---", out.get("③初始模式"))
        for k in ["④按V", "④按R", "④按F"]:
            v = out.get(k) or {}
            b = (v.get("按前") or {}).get("模式") or {}
            a = (v.get("按后") or {}).get("模式") or {}
            print("  %-6s 前=%-10s 后=%-10s 序号=%s→%s 字母=%s→%s svg变了=%s 开关数=%s"
                  % (k, b.get("模式"), a.get("模式"),
                     b.get("下拉序号"), a.get("下拉序号"),
                     (b.get("下拉项文字") or [None])[-1],
                     (a.get("下拉项文字") or [None])[-1],
                     v.get("svg变了"), v.get("开关数")))
        s5 = out.get("⑤Shift+V") or {}
        print("  Shift+V 前=%s 后=%s" % ((s5.get("按前模式") or {}).get("模式"),
                                        (s5.get("按后模式") or {}).get("模式")))
        s6 = out.get("⑥按X") or {}
        print("  按X 翻转项数=%s 翻转=%s" % (s6.get("翻转项数"), s6.get("翻转项")))
        print("  再按一次 翻转=%s" % (s6.get("再按翻转项"),))
        print("  冒泡阶段收到的键数=%s（源站在 window 捕获阶段掐断 ⟹ 期望 0）"
              % out.get("⑦冒泡阶段收到数"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
