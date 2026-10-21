#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v11：★ **单趟闭环** —— 新建角色 → 读默认名 → 删除 → 复验。

★★ 为什么必须**单趟**：v9 在一趟里读到了「角色B」，v10 另一趟进站时它已经不在了
   ⟹ ★ 跨趟的**状态与读数无法对齐** ⟹ 「角色B」这条读数**可能是**面板的临时名，
   也可能是真新建的角色名 ⟹ ★ **必须单趟闭环自证**：
   新建 → 读名（此时树区应**多一行**）→ 删除 → 复验（树区行数回到新建前）。

★ 本趟的判据（全部**同趟**读，**不跨趟**）：
  A. 新建**前**：树区行名与行数（**与名字形态无关**的口径）；
  B. 点体型预设 ⟹ **树区行数 +1** ⟹ ★ 这是「真的多了一个角色」的硬前提
     （v8 那次只看到面板行 ⟹ 不是真新增）；
  C. 右栏「名称」输入框的值 ⟹ 新角色的默认名；
  D. 删除 ⟹ 树区行数回到 A 的值 ⟹ ★ **复原**。

★ ★ 若 B 不成立（行数没 +1）⟹ 判「实验无效」⟹ **不下结论**（不拿面板的临时名当结论）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_charname838e.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 场景树**对象行**：靠几何定位树区（x∈[40,300]，y∈[130,460]），**不看名字**
DUMP_TREE_ROWS = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  const seen=new Set();
  for (const el of Array.from(document.querySelectorAll('[role="treeitem"],button,li'))) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 40 || r.x > 300) continue;
    if (r.y < 130 || r.y > 460) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    const key=Math.round(r.y)+'|'+t;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              tag:el.tagName, role:el.getAttribute('role')||'',
              aria:el.getAttribute('aria-label')||'',
              dataKeys:Object.keys(el.dataset||{})});
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
    out.push({value:el.value||'', placeholder:el.getAttribute('placeholder')||'',
              x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out;
}"""

# ★ 标签页标题（右栏最上面那个大标题）⟹ 「角色」/「机位」
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


def rows(page):
    r = page.evaluate(DUMP_TREE_ROWS)
    names, seen = [], set()
    for x in r:
        if x["text"] not in seen:
            seen.add(x["text"])
            names.append(x["text"])
    return names, r


def run(out, cookies):
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        clean(page)

        # A. 新建前
        a_names, a_rows = rows(page)
        out["A_新建前_行名"] = a_names
        out["A_新建前_行数"] = len(a_rows)
        out["A_新建前_详情"] = a_rows

        # B. 点「添加角色」→ 选体型
        page.locator("[aria-label='添加角色']").first.click()
        page.wait_for_timeout(1_500)
        clean(page)
        out["B_面板打开后_行名"] = (rows(page))[0]
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

        # B′ ★ 硬前提：树区行数必须 +1
        b_names, b_rows = rows(page)
        out["B_新建后_行名"] = b_names
        out["B_新建后_行数"] = len(b_rows)
        out["B_★行数增量"] = len(b_rows) - len(a_rows)
        out["B_★★前提_真新增了一行"] = len(b_rows) == len(a_rows) + 1
        new_rows = [r for r in b_rows if r["text"] not in a_names]
        out["B_★新增的行"] = new_rows

        # C. 右栏名称输入框
        out["C_右栏标题"] = page.evaluate(DUMP_PANEL_TITLE)
        out["C_右栏输入框"] = page.evaluate(DUMP_NAME_INPUT)
        out["C_★读到的名称值"] = (page.evaluate(DUMP_NAME_INPUT) or [{}])[0].get("value")
        out["C_★★实验是否有效"] = out["B_★★前提_真新增了一行"] and bool(out["C_★读到的名称值"])

        try:
            page.screenshot(path="/tmp/liblib_source_charname838e.png")
        except Exception:
            pass

        # D. 删除本批新建的那一行
        deleted = False
        if new_rows:
            row = new_rows[0]
            page.mouse.click(row["x"] + 20, row["y"] + row["h"] / 2, button="right")
            page.wait_for_timeout(1_200)
            clean(page)
            try:
                page.get_by_text("删除", exact=True).first.click()
                deleted = True
            except Exception as exc:
                out["D_点删除_异常"] = str(exc)
            page.wait_for_timeout(1_500)
            clean(page)
            try:
                c = page.get_by_text("确定", exact=True).first
                if c.is_visible():
                    out["D_★有二次确认"] = True
                    c.click()
                    page.wait_for_timeout(1_500)
                    clean(page)
            except Exception:
                out["D_★有二次确认"] = False
        out["D_★是否点了删除"] = deleted

        d_names, d_rows = rows(page)
        out["D_删除后_行名"] = d_names
        out["D_删除后_行数"] = len(d_rows)
        out["D_★★是否复原"] = len(d_rows) == len(a_rows)
        try:
            page.screenshot(path="/tmp/liblib_source_charname838e_after.png")
        except Exception:
            pass
        br.close()


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
        for k in ("A_新建前_行名", "B_新建后_行名", "D_删除后_行名"):
            print("%-18s %s" % (k, out.get(k)))
        for k in ("A_新建前_行数", "B_新建后_行数", "B_★行数增量", "B_★★前提_真新增了一行",
                  "C_★读到的名称值", "C_★★实验是否有效", "D_★是否点了删除",
                  "D_删除后_行数", "D_★★是否复原"):
            print("%-24s %r" % (k, out.get(k)))
        print("  新增行 =", out.get("B_★新增的行"))
        print("  右栏标题 =", out.get("C_右栏标题"))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
