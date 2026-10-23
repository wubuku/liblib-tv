#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 857 源站探针（**有副作用**·会真的加一组群众阵列，最后撤销复原）：
导演台「群众阵列（crowd）」的**对话框逐字参数** ＋ **舍入行为** ＋
**加出来的是什么** ＋ **有没有第二个入口**。

## ★ 这批要取证的五件事

① **对话框的逐字参数**（aria／位置尺寸／文案／三个输入的 label·min·max·step·初值）
   ⟹ ⟹ 用来判 clone 的「量程／步长／默认值」是否与源站一致。
② ★ **舍入行为**：把「间距」填成 **1.55** ⟹ ⟹ 读回来看源站是不是**保留 1 位小数**
   ⟹ ⟹ （源站逐字 `Math.min(10,Math.max(.1,Math.round(10*t)/10))`）
   ⟹ ⟹ ★ 这是**行为证据**，比「读代码」更硬。
③ **点「添加」之后源站的场景树里新增了什么**
   ⟹ ⟹ clone 加的是「N 个角色 ＋ **一个组**」⟹ ⟹ 源站到底加不加工组？
④ ★ **有没有第二个「添加群众阵列」入口**
   ⟹ ⟹ clone 有**两个**（rail 对话框 ＋ 视口工具栏按钮）⟹ ⟹ 源站有几个？
   ⟹ ⟹ ★ 判据用**自指**：记下对话框自己的 `aria-label`，
   ⟹ ⟹ 再全页扫「aria-label 等于它」的元素 ⟹ ⟹ **不手打任何中文**。
⑤ **撤销能否复原**（收尾自检）。

## ★ 定位策略（★ 全程按结构，不手打中文标签）

- 场景树行：沿用 batch 856 的同口径（`span` 的 class 含 `truncate pl-1`）。
- crowd 入口：源站 chunk 逐字 `"aria-haspopup":"dialog","aria-expanded":"crowd"===L`
  ⟹ ⟹ 它是「添加角色」浮层里**唯一**那枚 `button[aria-haspopup="dialog"]`
  ⟹ ⟹ 于是：逐个点左侧 rail 的按钮 ⟹ ⟹ **找新出现的**那枚
  ⟹ ⟹ ⟹ **不靠文案**（源站文案是「群众 (3x3)」，但判据不依赖它）。
- 对话框：页面上可能同时有多个 `role="dialog"`（例如画布的 AI 抽屉）
  ⟹ ⟹ 必须**遍历全部**、挑**含 ≥2 个 number 输入**的那个。

## ★ ★ 三个踩过的坑（都写进注释，免得以后重踩）

① **练习浮层**（`[data-director-practice-escape]`）会**拦截所有点击**（`inset-0`）
   ⟹ ⟹ 而且它的「✕」会**关掉整个导演台** ⟹ ⟹ 所以只能用 **Escape** 关它，
   ⟹ ⟹ 且每一步都要读回树 ⟹ ⟹ 自检「导演台还开着吗」。
② **raw click 会落空**：`page.mouse.click` 打在浮层上 ⟹ ⟹ 什么也没发生
   ⟹ ⟹ 所以「点 rail 之前先确认浮层没了」。
③ **多个 `role="dialog"`**：`document.querySelector('[role="dialog"]')`
   会命中画布的 AI 抽屉 ⟹ ⟹ 必须遍历并按「含几个 number 输入」挑。

## ★ 副作用与复原

★ 加群众阵列会**往用户工程里加角色** ⟹ ⟹ 最后必须撤销复原；
★ 兜底：连按 ⌘Z ＋ 读回树，确认回到基线。

## 输出
  raw/source-857-crowd.json
  images/857src_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch857-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 读树行（沿用 856 的同口径）
READ_ROWS = r"""()=>{
  const out = [];
  document.querySelectorAll('span').forEach(e=>{
    const cls = e.className || '';
    if(typeof cls !== 'string' || cls.indexOf('truncate pl-1') < 0) return;
    const r = e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x > 300) return;
    const t = (e.textContent||'').trim();
    if(!t) return;
    out.push({label:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height)});
  });
  out.sort((a,b)=>a.y-b.y);
  return out;
}"""

# ★ 左侧 rail 的按钮（按位置认：最左侧竖条）
READ_RAIL = r"""()=>{
  const out = [];
  document.querySelectorAll('button').forEach(b=>{
    const r=b.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x>70) return;
    if(r.y<40||r.y>1000) return;
    out.push({x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      aria:b.getAttribute('aria-label')||''});
  });
  out.sort((a,b)=>a.y-b.y);
  return out;
}"""

# ★★ 只认 **button** 形态的 aria-haspopup=dialog（页面里还有 div 形态的）
READ_POPUP_BTN = r"""()=>{
  const out=[];
  document.querySelectorAll('button[aria-haspopup="dialog"]').forEach(e=>{
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    out.push({x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      aria:e.getAttribute('aria-label')||'',
      text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,26)});
  });
  return out;
}"""

# ★★★ 遍历**全部** role=dialog，挑「含 ≥2 个 number 输入」的那个
READ_DIALOG = r"""()=>{
  const all=[...document.querySelectorAll('[role="dialog"]')].map(dlg=>{
    const nums=[...dlg.querySelectorAll('input[type="number"]')];
    const r=dlg.getBoundingClientRect();
    return {aria:dlg.getAttribute('aria-label')||'',
            n:nums.length,
            visible:r.width>0&&r.height>0,
            x:Math.round(r.x), y:Math.round(r.y),
            w:Math.round(r.width), h:Math.round(r.height),
            text:(dlg.textContent||'').replace(/\s+/g,' ').trim().slice(0,140),
            vals:nums.map(i=>({aria:i.getAttribute('aria-label'),min:i.getAttribute('min'),
                                max:i.getAttribute('max'),step:i.getAttribute('step'),v:i.value})),
            btns:[...dlg.querySelectorAll('button')].map(b=>
              (b.textContent||'').replace(/\s+/g,' ').trim().slice(0,20))};
  });
  const crowd=all.find(d=>d.n>=2)||null;
  return {all, crowd};
}"""

# ★★★ **自指**判据：有没有第二个同 aria-label 的入口
READ_SAME_ARIA = r"""(aria)=>{
  const hits = [...document.querySelectorAll('[aria-label]')]
    .filter(e=>e.getAttribute('aria-label')===aria)
    .map(e=>{
      const r=e.getBoundingClientRect();
      return {tag:e.tagName,
              text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,24),
              visible:r.width>0&&r.height>0,
              x:Math.round(r.x), y:Math.round(r.y)};
    });
  return {aria, count:hits.length, hits};
}"""


# ★★ **宽松**读树：不过滤零尺寸 ⟹ ⟹ 能区分「树面板被关掉了」与「真的没有新行」
READ_ROWS_LOOSE = r"""()=>{
  const out = [];
  document.querySelectorAll('span').forEach(e=>{
    const cls = e.className || '';
    if(typeof cls !== 'string' || cls.indexOf('truncate pl-1') < 0) return;
    const r = e.getBoundingClientRect();
    const t = (e.textContent||'').trim();
    if(!t) return;
    out.push({label:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height)});
  });
  out.sort((a,b)=>a.y-b.y);
  return out;
}"""


# ★★ 读 **3D 视口里的名字标签**（drei 的 Html 标签 ⟹ 用 translate3d 定位）
#   ⟹ ⟹ 这是「加出来几个东西」的**可数读数**
#   ⟹ ⟹ ★ 为什么需要它：源站在添加之后会把**场景树面板切走**（DOM 里读不到树），
#   ⟹ ⟹ 于是「树里新增几行」这条读数**拿不到** ⟹ ⟹ 只能换一条读数路径。
READ_VIEWPORT_LABELS = r"""()=>{
  const out = [];
  document.querySelectorAll('div,span').forEach(e=>{
    const st = e.getAttribute('style')||'';
    if(st.indexOf('translate3d') < 0) return;
    const r = e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x < 280) return;                  // ★ 只要 3D 视口那一侧
    const t = (e.textContent||'').replace(/\s+/g,' ').trim();
    if(!t || t.length > 14) return;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
  });
  const seen = new Set();
  const uniq = [];
  for (const o of out) {
    const k = o.text + '@' + Math.round(o.x/12);
    if (seen.has(k)) continue;
    seen.add(k);
    uniq.push(o);
  }
  uniq.sort((a,b)=>a.y-b.y || a.x-b.x);
  return uniq;
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def tree_labels(page):
    return [r["label"] for r in page.evaluate(READ_ROWS)]


def tree_labels_loose(page):
    return [r["label"] for r in page.evaluate(READ_ROWS_LOOSE)]


def director_alive(page):
    """导演台还开着吗 ⟹ ⟹ 靠左侧 rail 是否有按钮来判。"""
    return len(page.evaluate(READ_RAIL)) > 0


def read_tree_with_toggle(page):
    """读树；若读不到，★ 点右上角的面板开关（树面板 toggle）再读一次。

    ★ 实测坑：★ **Escape 会把场景树面板关掉** ⟹ ⟹ 于是「读不到树」是**读数问题**
    ⟹ ⟹ 不是「没有新行」。所以要先分清这两种情况，再读。
    """
    labels = tree_labels(page)
    if labels:
        return labels, "直接读到"
    loose = tree_labels_loose(page)
    # ★ 树可能是「零尺寸」（面板关着）⟹ ⟹ 点一下面板开关（右上角）再读
    try:
        page.mouse.click(260, 25)
        page.wait_for_timeout(900)
        again = tree_labels(page)
        if again:
            return again, "点面板开关后读到"
    except Exception:  # noqa: BLE001
        pass
    return labels, "读不到（宽松读法拿到 %d 条：%s）" % (len(loose), loose[:6])


def shot(page, name, clip=None):
    p = SHOTS / ("857src_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(p), clip=clip)
    return p


def main() -> int:
    out = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(20_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            open_desk(pg)

            # ── ① 基线树 ＋ ①b 基线的视口标签
            base = tree_labels(pg)
            out["①基线树"] = base
            base_labels = pg.evaluate(READ_VIEWPORT_LABELS)
            out["①基线视口标签"] = [x["text"] for x in base_labels]

            # ── ★ 关练习浮层：只能用 Escape（点 ✕ 会关掉整个导演台）
            out["②有练习浮层"] = pg.query_selector(
                "[data-director-practice-escape]") is not None
            if out["②有练习浮层"]:
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(900)
                out["②Esc后树"] = tree_labels(pg)
                out["②导演台还开着"] = bool(out["②Esc后树"])

            # ── ③ 找 crowd 入口：逐个点 rail，找**新出现**的 button[aria-haspopup=dialog]
            base_pop = pg.evaluate(READ_POPUP_BTN)
            out["③基线popup按钮数"] = len(base_pop)
            entry = None
            for item in pg.evaluate(READ_RAIL):
                try:
                    pg.mouse.click(item["x"] + item["w"] / 2, item["y"] + item["h"] / 2)
                    pg.wait_for_timeout(700)
                    now = pg.evaluate(READ_POPUP_BTN)
                    new = [b for b in now if b not in base_pop]
                    if new:
                        out["③触发浮层的rail按钮"] = item
                        out["③新出现的入口"] = new
                        entry = new[0]
                        break
                    pg.keyboard.press("Escape")
                    pg.wait_for_timeout(300)
                except Exception as exc:  # noqa: BLE001
                    out.setdefault("③点rail异常", []).append(str(exc)[:120])
            if entry is None:
                out["★异常"] = "没找到 aria-haspopup=dialog 的 crowd 入口"

            if entry:
                # ── ④ 打开对话框 ＋ 读逐字参数
                pg.mouse.click(entry["x"] + entry["w"] / 2, entry["y"] + entry["h"] / 2)
                pg.wait_for_timeout(900)
                d = pg.evaluate(READ_DIALOG)
                out["④对话框"] = d
                shot(pg, "crowd-dialog")

                crowd = d.get("crowd")
                if not crowd:
                    out["★异常"] = "对话框没打开（找含 ≥2 个 number 输入的那个）"

                if crowd:
                    # ── ⑤ **自指**判据：有没有第二个同 aria-label 的入口
                    out["⑤同aria元素"] = pg.evaluate(READ_SAME_ARIA, crowd["aria"])

                    # ── ⑥ ★ **舍入行为**：把间距填成 1.55 ⟹ ⟹ 读回来看是不是 1 位小数
                    try:
                        sp = pg.locator('[role="dialog"] input[type="number"]').nth(2)
                        sp.fill("1.55")
                        pg.wait_for_timeout(600)
                        out["⑥间距填1.55后"] = sp.input_value()
                        sp2 = pg.locator('[role="dialog"] input[type="number"]').nth(0)
                        out["⑥行数未被动"] = sp2.input_value()
                    except Exception as exc:  # noqa: BLE001
                        out["⑥舍入探测异常"] = str(exc)[:200]

                    # ── ⑦ 点「添加」⟹ 读「加出来几个」＋「有没有组」
                    try:
                        pg.locator('[role="dialog"] button:has-text("添加")').last.click()
                        pg.wait_for_timeout(4_000)
                        # ★★★ 主读数：**3D 视口里的名字标签**（可数）
                        labels = pg.evaluate(READ_VIEWPORT_LABELS)
                        out["⑦添加后视口标签"] = [x["text"] for x in labels]
                        out["⑦新增标签数"] = len(labels) - len(base_labels)
                        out["⑦新增标签"] = [x["text"] for x in labels[len(base_labels):]]
                        out["⑦有没有组标签"] = any(
                            "组" in x["text"] for x in labels)
                        # ★ 副读数：场景树（源站添加后会把树面板切走 ⟹ 可能读不到）
                        after, how = read_tree_with_toggle(pg)
                        out["⑦读树方式"] = how
                        out["⑦添加后树"] = after
                        out["⑦导演台还开着"] = director_alive(pg)
                        shot(pg, "after-add")
                    except Exception as exc:  # noqa: BLE001
                        out["⑦添加异常"] = str(exc)[:300]

                    # ── ⑧ 撤销复原 ＋ 自检
                    for _ in range(3):
                        pg.keyboard.press("Meta+z")
                        pg.wait_for_timeout(700)
                    # ★★ 复原的读数要**重新加载后再读**：
                    #   实测源站在添加之后会把**场景树面板切走**（DOM 里读不到树），
                    #   ⟹ ⟹ 同一会话里读到的空树**不能**当「没复原成功」的证据。
                    #   ⟹ ⟹ 重新加载 ⟹ ⟹ 面板回到默认（打开）⟹ ⟹ 再读 ⟹ ⟹ 才是权威读数。
                    pg.reload(wait_until="domcontentloaded", timeout=90_000)
                    pg.wait_for_timeout(12_000)
                    el2 = pg.query_selector("text=下次再说")
                    if el2:
                        el2.click()
                        pg.wait_for_timeout(900)
                    open_desk(pg)
                    final = tree_labels(pg)
                    out["⑧复原后树(重载后读)"] = final
                    out["⑧树回到基线"] = final == base
                    shot(pg, "restored", {"x": 0, "y": 0, "width": 700, "height": 700})

    except Exception:
        out["★异常"] = traceback.format_exc()[-2500:]
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-857-crowd.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-857-crowd.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
