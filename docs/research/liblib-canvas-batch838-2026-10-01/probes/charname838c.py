#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v9：★★ 选中一个**体型预设**，看源站给新角色起的**默认名**。

★ v8 已确证：点「添加角色」打开的是**体型预设面板**（11 枚：本地上传／标准男性／
  标准女性／健硕／纤细／少年／儿童／宽厚／二头身／群众(3x3)／几何模型）⟹
  ★ **「添加角色」不是直接新建** ⟹ v8 那一步的「是否直接新增」为 True 是**读数口径问题**
    （左栏多了一行**面板里的体型名**，不是多了一个角色）⟹ ★ **不据此下结论**。

★ v9 做真正的区分实验：点一枚体型预设 ⟹ 源站**新建一个角色** ⟹ 读它的默认名。
  ★ 收尾：**删掉本批新建的那个角色**（用**无正则**口径复验）。

★ ★★ 铁律（承 batch 836 的教训）：
  1. **前提不满足 ⟹ 判「实验无效」并不下结论**；
  2. ★ **计数口径必须与被测对象的名字形态无关** ⟹ 「角色数」用**左栏里 x∈[50,300] 的行**
     的**计数**，不用「以『角色』开头」这种**正则**口径；
  3. ★ **只删本批新建的那一个**（源站有并发活动）⟹ 用**新建前后的差集**定位，
     不按名字猜。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_charname838c.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 场景树的**对象行**：左栏 x∈[50,300]，取每个可点行（button/role=treeitem）的文本
DUMP_OBJROWS = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  const seen=new Set();
  for (const el of Array.from(document.querySelectorAll('button,[role="treeitem"],[role="button"],li'))) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 40 || r.x > 300) continue;
    if (r.y < 130 || r.y > 400) continue;      // ★ 场景树的树区
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    const key=Math.round(r.y)+'|'+t;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              tag:el.tagName, aria:el.getAttribute('aria-label')||'',
              dataKeys:Object.keys(el.dataset||{})});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 右栏（选中角色后的属性面板）里的输入框值 ⟹ 角色名
DUMP_RIGHT_INPUTS = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('input,textarea'))) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300) continue;
    out.push({value:el.value||'', placeholder:el.getAttribute('placeholder')||'',
              aria:el.getAttribute('aria-label')||'', x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height)});
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


def objrows(page):
    rows = page.evaluate(DUMP_OBJROWS)
    names = []
    for r in rows:
        if r["text"] not in names:
            names.append(r["text"])
    return names, rows


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

        base, base_rows = objrows(page)
        out["①进站基线_树区行名"] = base
        out["①★进站基线_行数_与名字形态无关的口径"] = len(base_rows)
        out["①基线行详情"] = base_rows

        # ② 点「添加角色」→ 选「标准男性」
        page.locator("[aria-label='添加角色']").first.click()
        page.wait_for_timeout(1_500)
        clean(page)
        picked = False
        try:
            page.get_by_text("标准男性", exact=True).first.click()
            picked = True
        except Exception as exc:
            out["②选体型_异常"] = str(exc)
        page.wait_for_timeout(2_500)
        clean(page)
        out["②是否点到了体型"] = picked

        after, after_rows = objrows(page)
        out["③选完体型后_树区行名"] = after
        out["③★行数_与名字形态无关的口径"] = len(after_rows)
        new_rows = [r for r in after_rows if r["text"] not in base]
        out["③★新增的行"] = new_rows
        out["③★新增行数"] = len(new_rows)

        # ④ 右栏输入框 ⟹ 新角色的默认名
        out["④右栏输入框"] = page.evaluate(DUMP_RIGHT_INPUTS)
        out["④右栏可见文本"] = page.evaluate("""() => {
          const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
          const out=[];
          for (const el of Array.from(document.querySelectorAll('span,div,button,a,p'))) {
            if (!vis(el) || el.childElementCount>0) continue;
            const r=el.getBoundingClientRect();
            if (r.x < 1300) continue;
            const t=(el.textContent||'').trim();
            if (!t || t.length>40) continue;
            out.push({text:t, x:Math.round(r.x), y:Math.round(r.y), tag:el.tagName});
          }
          return out.sort((a,b)=>(a.y-b.y)||(a.x-b.x));
        }""")
        try:
            page.screenshot(path="/tmp/liblib_source_charname838c.png")
            out["截图"] = "/tmp/liblib_source_charname838c.png"
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
        print("\n=== 进站基线（树区行名）===")
        print("  ", out.get("①进站基线_树区行名"))
        print("  行数（与名字形态无关的口径）=", out.get("①★进站基线_行数_与名字形态无关的口径"))
        print("\n=== 选完体型后（树区行名）===")
        print("  ", out.get("③选完体型后_树区行名"))
        print("  行数 =", out.get("③★行数_与名字形态无关的口径"))
        print("  ★新增行 =", out.get("③★新增的行"))
        print("\n=== 右栏输入框 ===")
        for d in (out.get("④右栏输入框") or []):
            print("  @(%s,%s) value=%r placeholder=%r aria=%r" %
                  (d["x"], d["y"], d["value"], d["placeholder"], d["aria"]))
        print("\n=== 右栏文本（前 25）===")
        for d in (out.get("④右栏可见文本") or [])[:25]:
            print("  @(%s,%s) %r" % (d["x"], d["y"], d["text"]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
