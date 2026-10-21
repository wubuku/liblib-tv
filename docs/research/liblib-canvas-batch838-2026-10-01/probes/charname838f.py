#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v15：★★ **单趟闭环** 复现「角色默认名 = 角色 + 字母序号」。

★★★ 为什么必须单趟闭环（v9–v14 的教训）：
  v9 在一趟里读到了「角色B」（右栏名称输入框），v10 另一趟进站时它已经不在了，
  v11 的读数器口径又坏了（把**体型预设面板的行**当成新增的角色行）⟹
  ★★ 跨趟的**状态与读数无法对齐** ⟹ 「角色B」这条读数**缺少自证**。
  ⟹ 本趟把整条链**放在一趟里**：
     新建 → 读名 → **读树区（收窄口径，证明真多了一行）** → 删除 → 等自动保存 → 跨刷新复验。

★ ★★ 读数器口径（照抄 v14 **实测有效**的那套）：
  - 场景树对象行：**x∈[80,240] 且 y∈[140,300]**（实测：机位1@154／机位2@186／角色A@218／
    角色B@250，**全部 x=96**）⟹ ★ 关键：**x 的窄区间**把浮层面板（x=56）排除了；
  - ★ **必须与 v11 区分**：v11 用的是 `x∈[40,300] 且 y∈[130,460]` ⟹ **把面板行读了进来**。

★ ★★ 自动保存的机制（v14 实测）：
  删除后**约 30 秒**才发 `POST /api/canvas/nodes/batch`（保存导演台节点 `n-gYB1c2Peq9` 的
  compositionData）⟹ ★ 所以「跨刷新复验」必须**等够时间**，否则会误判「没删掉」。
  ⟹ 本趟：删后**等 45 秒**，再**用新 context 跨刷新**复验。

★ ★★ 铁律：
  - **只删本批新建的那一个**（用新建前后的**行数差 + 文本**定位，不按名字猜）；
  - 若删除没落盘 ⟹ 如实报告「未复原」，**不谎称复原**；
  - 收尾**必须**跨刷新复验（内存里消失 ≠ 存盘了）。
"""
import json
import pathlib
import time
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_charname838f.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 场景树对象行（★ 收窄口径：x∈[80,240] ⟹ 排除浮层面板 x=56）
DUMP_TREE_OBJ = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[]; const seen=new Set();
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 80 || r.x > 240) continue;
    if (r.y < 140 || r.y > 300) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    const key=Math.round(r.y)+'|'+t;
    if (seen.has(key)) continue; seen.add(key);
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 右栏「名称」输入框（第一个 input）
DUMP_NAME_INPUT = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('input'))) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300) continue;
    out.push({value:el.value||'', x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out;
}"""

# ★ 右栏顶部标题（「角色」/「机位」）⟹ 证明选中的是**角色**面板
DUMP_PANEL_TITLE = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,h1,h2,h3'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300 || r.y > 40) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>20) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out;
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def clean(page):
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


def tree_obj(page):
    rows = page.evaluate(DUMP_TREE_OBJ)
    names = []
    for r in rows:
        if r["text"] not in names:
            names.append(r["text"])
    return names, rows


def add_cookies(ctx, cookies):
    ctx.add_cookies([{"name": c["name"], "value": c["value"],
                      "domain": c["domain"], "path": c.get("path", "/"),
                      "expires": c.get("expires", -1),
                      "httpOnly": c.get("httpOnly", False),
                      "secure": c.get("secure", False),
                      "sameSite": c.get("sameSite", "Lax")} for c in cookies])


def run(out, cookies):
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
        add_cookies(ctx, cookies)
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        clean(page)

        # A. 基线
        a_names, a_rows = tree_obj(page)
        out["A_进站_场景树对象行"] = a_names
        out["A_★进站_行数"] = len(a_rows)
        out["A_行详情"] = a_rows

        # B. 新建角色
        page.locator("[aria-label='添加角色']").first.click()
        page.wait_for_timeout(1_500)
        clean(page)
        picked = None
        for label in ("标准男性", "标准女性", "健硕"):
            try:
                page.get_by_text(label, exact=True).first.click()
                picked = label
                break
            except Exception:
                continue
        out["B_★选中的体型"] = picked
        page.wait_for_timeout(2_500)
        clean(page)

        # B′ ★ 硬前提：树区行数 +1（**收窄口径** ⟹ 面板行已被排除）
        b_names, b_rows = tree_obj(page)
        out["B_新建后_场景树对象行"] = b_names
        out["B_★新建后_行数"] = len(b_rows)
        out["B_★★行数增量"] = len(b_rows) - len(a_rows)
        out["B_★★前提_真新增了一行"] = len(b_rows) == len(a_rows) + 1
        new_rows = [r for r in b_rows if r["text"] not in a_names]
        out["B_★新增的行"] = new_rows
        out["B_★新增行的文本"] = [r["text"] for r in new_rows]

        # C. 右栏「名称」输入框
        out["C_右栏标题"] = page.evaluate(DUMP_PANEL_TITLE)
        out["C_右栏输入框"] = page.evaluate(DUMP_NAME_INPUT)
        name_val = (out["C_右栏输入框"] or [{}])[0].get("value")
        out["C_★读到的默认名"] = name_val
        out["C_★★实验是否有效"] = bool(
            out["B_★★前提_真新增了一行"] and name_val
            and out["B_★新增行的文本"] and name_val in out["B_★新增行的文本"])

        try:
            page.screenshot(path="/tmp/liblib_source_charname838f.png")
        except Exception:
            pass

        # D. 删除本批新建的那一行
        deleted = False
        if new_rows:
            row = new_rows[0]
            page.mouse.click(row["x"] + 10, row["y"] + row["h"] / 2, button="right")
            page.wait_for_timeout(1_500)
            clean(page)
            for label in ("删除", "删除⌘⌫"):
                try:
                    el = page.get_by_text(label, exact=True).first
                    if el.is_visible():
                        el.click()
                        deleted = True
                        out["D_★点的菜单项"] = label
                        break
                except Exception:
                    continue
            page.wait_for_timeout(1_500)
            clean(page)
            try:
                c = page.get_by_text("确定", exact=True).first
                if c.is_visible():
                    c.click()
                    page.wait_for_timeout(1_500)
                    clean(page)
            except Exception:
                pass
        out["D_★是否点了删除"] = deleted
        d_names, d_rows = tree_obj(page)
        out["D_删除后_场景树对象行"] = d_names
        out["D_★删除后_行数"] = len(d_rows)

        # E. 等自动保存（★ v14 实测约 30 秒延迟 ⟹ 等 45 秒）
        out["E_★等自动保存秒数"] = 45
        page.wait_for_timeout(45_000)
        ctx.close()
        br.close()

        # F. ★ 跨刷新复验（新 context）
        with sync_playwright() as pw2:
            br2 = pw2.chromium.launch(headless=True)
            ctx2 = br2.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
            add_cookies(ctx2, cookies)
            p2 = ctx2.new_page()
            p2.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            p2.wait_for_timeout(12_000)
            open_desk(p2)
            clean(p2)
            f_names, f_rows = tree_obj(p2)
            out["F_★跨刷新后_场景树对象行"] = f_names
            out["F_★跨刷新后_行数"] = len(f_rows)
            out["F_★跨刷新后还剩新建的"] = [t for t in f_names if t not in a_names]
            out["F_★★是否已复原"] = len(f_rows) == len(a_rows)
            try:
                p2.screenshot(path="/tmp/liblib_source_charname838f_after.png")
            except Exception:
                pass
            ctx2.close()
            br2.close()


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("A_进站_场景树对象行", "B_新建后_场景树对象行", "D_删除后_场景树对象行",
                  "F_★跨刷新后_场景树对象行"):
            print("%-26s %s" % (k, out.get(k)))
        for k in ("A_★进站_行数", "B_★新建后_行数", "B_★★行数增量", "B_★★前提_真新增了一行",
                  "B_★新增行的文本", "C_★读到的默认名", "C_★★实验是否有效",
                  "D_★是否点了删除", "D_★删除后_行数", "F_★跨刷新后_行数",
                  "F_★跨刷新后还剩新建的", "F_★★是否已复原"):
            print("%-26s %r" % (k, out.get(k)))
        print("  右栏标题 =", out.get("C_右栏标题"))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
