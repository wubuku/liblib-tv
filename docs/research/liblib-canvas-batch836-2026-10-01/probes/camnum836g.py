#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针 v7：★ **把「机位1 删不掉」的剩余替代解释全部排掉**。

★ 到 v6 为止，「机位1 在有 3 台时删不掉」已用**无正则口径**坐实（两个口径台数一致）。
⟹ ★ 但仍有**两个替代解释**没排掉：
  ① **「编号最小者不可删」**（即保护的是「排序第一台」而非「默认机位」）；
  ② **「当前激活机位不可删」**（v4 的激活读数是空的 ⟹ 没钉死）。

★ 本探针用**两步**把两者分开：
  **第一步**：删「机位3」（v4 实测删得掉）⟹ 剩「机位1」「机位2」
  ⟹ 此时若再删「机位1」⟹
     - 删得掉 ⟹ 保护**与编号最小无关**（因为「机位2」才是编号最小）⟹ ⟹ 指向「按身份」；
     - 删不掉 ⟹ 保护**只认编号最小者**（解释 ① 成立）。
  **第二步**：把「机位1」**改名**成别的名字（若源站支持改名）⟹ 若改完就能删 ⟹ 保护是**按名字**的。
  ★ 若改名不可行 ⟹ 如实记「这一步做不了」，**不猜**。

★ 纪律：会改源站项目 ⟹ 每步**删完用无正则口径复验** ⟹ **收尾复原** ⟹ 异常时 finally 清理。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836g.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_LEFT = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a'))) {
    if (!vis(el) || el.childElementCount > 0) continue;
    const r=el.getBoundingClientRect();
    if (r.x > 500) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.indexOf('机位')<0) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def back_to_scene(page):
    try:
        nav = page.locator("nav").filter(
            has=page.locator("button[aria-label='场景']")).first
        nav.locator("button[aria-label='场景']").first.click()
        page.wait_for_timeout(1_600)
    except Exception:
        pass


def left_names(page):
    return [d["text"] for d in page.evaluate(DUMP_LEFT)]


def new_camera(page):
    nav = page.locator("nav").filter(
        has=page.locator("button[aria-label='场景']")).first
    nav.locator("button[aria-label='添加机位']").first.click()
    page.wait_for_timeout(2_200)
    grid = page.locator("div.grid.min-h-0.flex-1").first
    cells = grid.locator("button")
    if not cells.count():
        return False
    cells.nth(0).click()
    page.wait_for_timeout(2_400)
    back_to_scene(page)
    return True


def delete_camera(page, name):
    """删掉**指定名字**的那台 ⟹ **无正则口径**复验台数。"""
    back_to_scene(page)
    before = left_names(page)
    if name not in before:
        return {"ok": False, "why": "%s 不在树区（%s）" % (name, before), "before": before}
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(800)
        item.click(button="right")
        page.wait_for_timeout(1_500)
        del_item = page.locator("[role='menuitem']").filter(has_text="删除").first
        if not del_item.count():
            return {"ok": False, "why": "菜单里没有『删除』", "before": before}
        del_item.click()
        page.wait_for_timeout(1_300)
        for label in ("确认删除", "确定", "确认"):
            try:
                b = page.get_by_role("button", name=label, exact=True)
                if b.count() and b.first.is_visible():
                    b.first.click()
                    page.wait_for_timeout(1_000)
                    break
            except Exception:
                pass
        page.wait_for_timeout(1_300)
    except Exception as exc:
        return {"ok": False, "why": repr(exc), "before": before}
    after = left_names(page)
    return {"ok": len(after) == len(before) - 1, "before": before, "after": after}


def rename_camera(page, name, new_name, log):
    """尝试在源站上给机位改名 ⟹ 用来判别保护是「按名字」还是「按身份」。"""
    back_to_scene(page)
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(700)
        item.click(button="right")
        page.wait_for_timeout(1_200)
        items = page.locator("[role='menuitem']")
        texts = [items.nth(i).inner_text().strip() for i in range(items.count())]
        log.append("右键菜单项：%r" % (texts,))
        ren = page.locator("[role='menuitem']").filter(has_text="重命名").first
        if not ren.count():
            return {"ok": False, "why": "菜单里没有『重命名』（菜单项=%r）" % (texts,)}
        ren.click()
        page.wait_for_timeout(1_000)
        box = page.locator("input[type='text']").first
        if not box.count():
            return {"ok": False, "why": "改名后没找到文本输入框"}
        box.fill(new_name)
        page.wait_for_timeout(300)
        box.press("Enter")
        page.wait_for_timeout(1_300)
        after = left_names(page)
        return {"ok": new_name in after, "after": after}
    except Exception as exc:
        return {"ok": False, "why": repr(exc)}


def run(out, cookies):
    log = out.setdefault("日志", [])
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
        try:
            back_to_scene(page)
            base = left_names(page)
            out["①基线"] = base
            log.append("基线：%r" % base)

            # 造到 3 台
            guard = 0
            while len(left_names(page)) < 3 and guard < 6:
                guard += 1
                new_camera(page)
            out["②三台"] = left_names(page)
            log.append("三台：%r" % out["②三台"])

            # ---------- 第一步：删「机位3」（v4 实测删得掉）⟹ 剩 1、2 ----------
            r3 = delete_camera(page, "机位3")
            out["③删机位3"] = r3
            log.append("删机位3：%s" % json.dumps(r3, ensure_ascii=False))
            back_to_scene(page)
            out["③剩"] = left_names(page)

            # ---------- 第二步：此时删「机位1」（编号最小的那台） ----------
            r1 = delete_camera(page, "机位1")
            out["④此时删机位1"] = r1
            log.append("此时删机位1：%s" % json.dumps(r1, ensure_ascii=False))
            back_to_scene(page)
            out["④剩"] = left_names(page)

            out["⑤判定_保护是否只认编号最小"] = (
                "★ 删掉「机位3」之后，「机位1」**仍然删不掉** ⟹ "
                "保护**不是**「编号最小者」那条规则 ⟹ 指向**按身份**（默认机位）"
                if (r1.get("before") and r1.get("after")
                    and len(r1["after"]) == len(r1["before"]))
                else "★ 删掉「机位3」之后，「机位1」**删得掉** ⟹ "
                     "保护**就是「编号最小者」**（解释 ① 成立）")

            # ---------- 第三步：改名 ⟹ 判别「按名字」还是「按身份」 ----------
            if len(left_names(page)) >= 2:
                rn = rename_camera(page, "机位1", "机位X", log)
                out["⑥改名机位1为机位X"] = rn
                log.append("改名：%s" % json.dumps(rn, ensure_ascii=False))
                if rn.get("ok"):
                    back_to_scene(page)
                    out["⑥改名后树"] = left_names(page)
                    r2 = delete_camera(page, "机位X")
                    out["⑥改名后删机位X"] = r2
                    log.append("改名后删：%s" % json.dumps(r2, ensure_ascii=False))
                    out["⑦判定_保护是否按名字"] = (
                        "★ 改名成「机位X」后**删得掉** ⟹ 保护是**按名字**的"
                        if r2.get("ok") else
                        "★ 改名成「机位X」后**仍删不掉** ⟹ 保护**与名字无关**（按身份）")
                else:
                    out["⑦判定_保护是否按名字"] = "★ 改名这一步做不了：%s ⟹ **不猜**" % rn.get("why")
            else:
                out["⑦判定_保护是否按名字"] = "★ 场景里机位不够，改名那步没做 ⟹ **不猜**"
        finally:
            try:
                back_to_scene(page)
                base = out.get("①基线") or []
                for nm in sorted(set(left_names(page)) - set(base)):
                    delete_camera(page, nm)
                out["收尾"] = left_names(page)
                out["收尾正确"] = out["收尾"] == base
                log.append("收尾：%r（正确=%s）" % (out["收尾"], out["收尾正确"]))
            except Exception:
                out["收尾异常"] = traceback.format_exc()
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
        for k in ("①基线", "②三台", "③删机位3", "③剩", "④此时删机位1", "④剩",
                  "⑤判定_保护是否只认编号最小", "⑥改名机位1为机位X", "⑥改名后树",
                  "⑥改名后删机位X", "⑦判定_保护是否按名字", "收尾", "收尾正确"):
            if k in out:
                print("%-22s %s" % (k, json.dumps(out[k], ensure_ascii=False)[:400]))
        print("日志：")
        for line in out.get("日志") or []:
            print("  ", line)
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
