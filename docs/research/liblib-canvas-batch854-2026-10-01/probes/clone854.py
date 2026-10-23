#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 854 clone 探针：导演台**组模型的成员语义**。

## ★ 靶子（源站逐字依据见 raw/source-854-contract.json）

- **D1**：组可以含**任意场景成员**（不只是角色）
  ⟹ 源站逐字 `function sg(e){return"character"===e||"prop"===e||"emptyObject"===e||"camera"===e}`
  ⟹ 源站 reducer 逐字 `case"CREATE_CHARACTER_GROUP":{let r=lB(t.members&&t.members.length>0?t.members:lB(e.selectedSceneMembers,…`
- **D3**：树里 **⇧／⌘／Ctrl** 都能加选
  ⟹ 源站逐字 `let r=t.shiftKey||t.metaKey||t.ctrlKey;`
- **D4**：组成员**默认展开**、且在树里是**缩进子行**
  ⟹ 源站逐字 `expanded:!!F||!j.has(e.id)` ＋ `(F||!j.has(e.id))&&r.map(…{row:e,indent:!0…})`

## ★ 期望值从哪来

★ **不是手打的** ⟹ ⟹ 直接读 `raw/source-854-groupmembers.json`（源站实测落盘）
★ 里那几组读数：组含 camera＋character、成员相对组行 **+16px**、组标签 `分组1`。
★ ⟹ 三层证据链：**源站 chunk 原文 → 提取器 → 源站实测 → 本探针的 clone 实测**。

## ★ 走**真实 UI**（不调 store）

- 点机位行 → 选 1 个
- **⌘+点**角色行 → 加选（这一格与源站实测同路径）
- 点「打组」按钮 ⟹ 组出现
- 点「解组」按钮 ⟹ 复原
- 另一轮用 **⇧+点**验第二个修饰键

## ★ 读数

- 类别分区的对象行：`[data-director-object-id]`（带 `data-director-object-kind`）
- 组行：`[data-director-group-id]`；组成员行：`[data-director-group-member-id]`
  （带 `data-director-group-member-kind` ⟹ ⟹ **组的成员类别能直接从 DOM 读到**）
- 几何：全部用 `getBoundingClientRect()` 的**绝对 x**（不手算缩进）

## 输出

  raw/clone-854-groupmembers.json
  images/854clone_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch854-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
SOURCE_RAW = RAW / "source-854-groupmembers.json"
BASE = "http://localhost:4317"

TREE_CLIP = {"x": 0, "y": 0, "width": 320, "height": 900}

SHOT_NAMES = {
    "①基线": "01-baseline",
    "②点机位后": "02-pick-camera",
    "③cmd加选角色后": "03-cmd-add-character",
    "④打组后": "04-group",
    "⑤解组后": "05-ungroup",
    "⑥shift加选道具后": "06-shift-add-prop",
    "⑦道具组后": "07-prop-group",
    "⑧结束": "08-final",
}

READ_ALL = r"""()=>{
  const q=(s)=>Array.from(document.querySelectorAll(s));
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x*100)/100, y:Math.round(r.y*100)/100,
            w:Math.round(r.width*100)/100, h:Math.round(r.height*100)/100};};
  // ★ 组行 / 成员行的标签：跳过**图标 span**（无文字）与**计数 span**（tabular-nums）
  const labelSpan=(row)=>{
    const spans=Array.from(row.querySelectorAll('span'));
    const cand=spans.filter(sp=>sp.textContent.trim()
      && !String(sp.className||'').includes('tabular-nums'));
    return cand.length? cand[cand.length-1] : null;
  };
  const labelOf=(row)=>{
    const sp=labelSpan(row);
    return sp? sp.textContent.trim() : null;
  };
  // ★★ **同口径**的两层几何：
  // ★   `x` ＝ **行元素**的 x（源站探针也补了这一层，见 source854 的 rowX）
  // ★   `文本x` ＝ **标签 span** 的 x（源站探针原本量的就是这一层）
  // ★ ⟹ ⟹ 两边各比各的，绝不混口径。
  const withBox=(row, extra)=>{
    const sp=labelSpan(row);
    const lb=sp? box(sp) : null;
    return Object.assign({label:labelOf(row), ...box(row),
      文本x: lb? lb.x : null}, extra||{});
  };
  const objRows=q('[data-director-object-id]').map(e=>withBox(e,{
    id:e.getAttribute('data-director-object-id'),
    kind:e.getAttribute('data-director-object-kind'),
    selected:e.getAttribute('data-director-object-selected'),
  }));
  const groupRows=q('[data-director-group-id]').map(e=>{
    const row=e.querySelector('div[role="treeitem"]')||e;
    return withBox(row,{
      id:e.getAttribute('data-director-group-id'),
      selected:e.getAttribute('data-director-group-selected'),
    });
  });
  const memberRows=q('[data-director-group-member-id]').map(e=>withBox(e,{
    id:e.getAttribute('data-director-group-member-id'),
    kind:e.getAttribute('data-director-group-member-kind'),
  }));
  const gBtn=document.querySelector('[data-director-group-action="group"]');
  const uBtn=document.querySelector('[data-director-group-action="ungroup"]');
  const bar=document.querySelector('[data-director-selection-toolbar]');
  const cnt=document.querySelector('[data-director-selection-count]');
  const s=window.__director_store? window.__director_store.getState() : null;
  return {
    DOM组数: groupRows.length,
    DOM组: groupRows,
    DOM组员数: memberRows.length,
    DOM组员: memberRows,
    DOM对象行数: objRows.length,
    DOM对象行: objRows,
    展开容器数: q('[data-director-group-expanded="true"]').length,
    打组按钮禁用: gBtn? gBtn.disabled : null,
    解组按钮禁用: uBtn? uBtn.disabled : null,
    选择工具栏在: Boolean(bar),
    选择类别: bar? bar.getAttribute('data-director-selection-kind') : null,
    选中文本: cnt? cnt.textContent.trim() : null,
    store组数: s? (s.groups||[]).length : null,
    store选中组: s? s.selectedGroupId : null,
    store选中对象: s? (s.selectedObjectIds||[]).slice() : null,
    store组员: s? ((s.groups&&s.groups[0])? (s.groups[0].members||null) : null) : null,
    store组角色id: s? ((s.groups&&s.groups[0])? (s.groups[0].characterIds||[]).slice() : null) : null,
  };
}"""


def load_source_expect():
    """★ 从**源站实测落盘**里取期望值（不是手打）。

    ★★ **同口径**：源站探针量的 `x` ＝ **标签 span** 的 x ⟹ ⟹ 这里取出来的
    ★ 「成员缩进」是**文本层**的缩进；clone 探针也量了 `文本x` ⟹ ⟹ 两边可比。
    ★ 同时把**行元素层**（源站 `rowX`）也带上 ⟹ ⟹ 两种粒度都能比。
    """
    data = json.loads(SOURCE_RAW.read_text(encoding="utf-8"))
    labels = data["⑤⌘G后标签"]
    kinds = data["⑤⌘G后类别"]
    xs = data["⑤⌘G后x"]
    rows = data.get("⑤⌘G后行") or []
    group_idx = labels.index("分组1")
    member_idx = [i for i in range(len(labels)) if xs[i] == xs[group_idx] + 16]
    out = {
        "源文件": str(SOURCE_RAW.relative_to(ROOT)),
        "期望组标签": labels[group_idx],
        "期望成员类别集合": sorted({kinds[i] for i in member_idx}),
        "期望文本缩进px": 16,
        "期望未入组行仍平铺": sorted(
            {kinds[i] for i in range(len(labels)) if xs[i] == xs[group_idx]}
        ),
    }
    # ★ 行元素层的缩进（源站 `rowX`）—— 若这一层存在就一并给出
    if rows and rows[group_idx].get("rowX") is not None:
        rowxs = [r.get("rowX") for r in rows]
        out["期望行元素缩进px"] = sorted(
            {round(rowxs[i] - rowxs[group_idx], 2) for i in member_idx}
        )
        out["源站组行首子宽"] = rows[group_idx].get("firstW")
        out["源站成员行首子宽"] = [rows[i].get("firstW") for i in member_idx]
    return out


def open_desk(pg):
    """★ **从根地址无参进入**（同时覆盖「根目录可达」这条新目标）。"""
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    pg.wait_for_timeout(1200)
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:
        pass
    pg.locator("[data-open-director]").first.click(timeout=15000)
    pg.wait_for_timeout(6000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def read(pg):
    return pg.evaluate(READ_ALL)


def shot(pg, key):
    p = SHOTS / ("854clone_%s.png" % SHOT_NAMES[key])
    p.parent.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(p), clip=TREE_CLIP)
    return p.name


def click_row(pg, kind, label, modifiers=None):
    """★ 真点那一行（kind ＋ label 双重定位，避免「定位元素别用 first」）。"""
    sel = '[data-director-object-kind="%s"]' % kind
    loc = pg.locator(sel)
    n = loc.count()
    target = None
    for i in range(n):
        el = loc.nth(i)
        if (el.text_content() or "").strip() == label:
            target = el
            break
    if target is None:
        raise SystemExit("★ 找不到 %s／%s 这一行（共 %d 行）" % (kind, label, n))
    try:
        target.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(200)
    kwargs = {"timeout": 15000}
    if modifiers:
        kwargs["modifiers"] = modifiers
    target.click(**kwargs)
    pg.wait_for_timeout(600)


def click_action(pg, action):
    btn = pg.locator('[data-director-group-action="%s"]' % action).first
    btn.scroll_into_view_if_needed(timeout=8000)
    pg.wait_for_timeout(200)
    btn.click(timeout=15000)
    pg.wait_for_timeout(900)


def main() -> int:
    out = {}
    try:
        expect = load_source_expect()
        out["★期望来源"] = expect
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            open_desk(pg)

            base = read(pg)
            out["①基线"] = base
            shot(pg, "①基线")

            # ── D3-⌘：点机位 → ⌘+点角色（与源站实测同一条路径）────────────
            try:
                click_row(pg, "camera", "机位1")
                out["②点机位后"] = read(pg)
                shot(pg, "②点机位后")
                click_row(pg, "character", "角色A", modifiers=["Meta"])
                out["③cmd加选角色后"] = read(pg)
                shot(pg, "③cmd加选角色后")
            except Exception:
                out["★选择段异常"] = traceback.format_exc()[-800:]

            # ── D1：打组（成员含 camera ＋ character）────────────────────
            try:
                click_action(pg, "group")
                g = read(pg)
                out["④打组后"] = g
                shot(pg, "④打组后")
                group_x = g["DOM组"][0]["x"] if g["DOM组"] else None
                group_tx = g["DOM组"][0]["文本x"] if g["DOM组"] else None
                member_kinds = sorted({m["kind"] for m in g["DOM组员"]})
                object_kinds = sorted({r["kind"] for r in g["DOM对象行"]})
                out["④判定"] = {
                    "组数": g["DOM组数"],
                    "组标签": g["DOM组"][0]["label"] if g["DOM组"] else None,
                    "期望组标签": expect["期望组标签"],
                    "组标签一致": bool(g["DOM组"]) and
                    g["DOM组"][0]["label"] == expect["期望组标签"],
                    "成员类别集合": member_kinds,
                    "期望成员类别集合": expect["期望成员类别集合"],
                    "成员类别一致": member_kinds == expect["期望成员类别集合"],
                    "★文本层缩进px": [round(m["文本x"] - group_tx, 2)
                                 for m in g["DOM组员"]]
                    if group_tx is not None else None,
                    "★期望文本层缩进px": expect["期望文本缩进px"],
                    "★行元素层缩进px": [round(m["x"] - group_x, 2)
                                  for m in g["DOM组员"]]
                    if group_x is not None else None,
                    "★期望行元素层缩进px": expect.get("期望行元素缩进px"),
                    "成员默认展开": g["展开容器数"] == 1 and g["DOM组员数"] > 0,
                    "入组后剩余类别分区": object_kinds,
                    "入组后剩余对象行": g["DOM对象行数"],
                    "store组员": g["store组员"],
                    "store组角色id": g["store组角色id"],
                }
            except Exception:
                out["★打组段异常"] = traceback.format_exc()[-800:]

            # ── 解组 ⟹ 回到基线 ────────────────────────────────────────
            try:
                click_action(pg, "ungroup")
                u = read(pg)
                out["⑤解组后"] = u
                shot(pg, "⑤解组后")
                out["⑤判定"] = {
                    "组数": u["DOM组数"],
                    "对象行数": u["DOM对象行数"],
                    "基线对象行数": base["DOM对象行数"],
                    "回到基线": u["DOM组数"] == 0 and
                    u["DOM对象行数"] == base["DOM对象行数"],
                }
            except Exception:
                out["★解组段异常"] = traceback.format_exc()[-800:]

            # ── D3-⇧：道具 × 道具（第二个修饰键）────────────────────────
            try:
                click_row(pg, "prop", "咖啡桌")
                out["⑥a点道具后"] = read(pg)
                click_row(pg, "prop", "冷掉的咖啡", modifiers=["Shift"])
                s = read(pg)
                out["⑥shift加选道具后"] = s
                shot(pg, "⑥shift加选道具后")
                out["⑥判定"] = {
                    "选中对象数": len(s["store选中对象"] or []),
                    "期望选中对象数": 2,
                    "选中类别": sorted(
                        {r["kind"] for r in s["DOM对象行"]
                         if r["selected"] == "true"}),
                }
                click_action(pg, "group")
                g2 = read(pg)
                out["⑦道具组后"] = g2
                shot(pg, "⑦道具组后")
                out["⑦判定"] = {
                    "组数": g2["DOM组数"],
                    "成员类别集合": sorted({m["kind"] for m in g2["DOM组员"]}),
                    "成员数": g2["DOM组员数"],
                    "成员默认展开": g2["展开容器数"] == 1,
                }
                click_action(pg, "ungroup")
                out["⑧结束"] = read(pg)
                shot(pg, "⑧结束")
            except Exception:
                out["★道具段异常"] = traceback.format_exc()[-800:]

            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "clone-854-groupmembers.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "clone-854-groupmembers.json")
        for k in ("④判定", "⑤判定", "⑥判定", "⑦判定"):
            if k in out:
                print("---", k)
                for kk, vv in out[k].items():
                    print("    %-22s %s" % (kk, vv))
        if out.get("异常"):
            print("异常：", out["异常"][-800:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
