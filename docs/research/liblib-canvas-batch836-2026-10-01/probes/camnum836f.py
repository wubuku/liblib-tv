#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针 v6：★ **决定性的一趟** —— 用**无正则计数**复验删除。

★★★ 起因：v5 实测基线时左侧树区**只有 1 条**含「机位」的文本（「机位1」）
  ⟹ 正则在**基线**下没漏读。
  ⟹ ★ 但 v1／v3／v4 的删除复验判据都是 `len(after) == len(cams) - 1`，
  而 `cams` 是**正则过滤后**的集合 ⟹ ★★ **若场景里真有一台不匹配的机位，
  计数就会一直少一台 ⟹ 「删掉了」也会被判成「未减少」**。
  ⟹ ⟹ **「机位1 删不掉」这个结论，本身可能就是我的计数口径造的。**

★ 所以本探针做**决定性**的一趟：
  ① 造出 3 台（每台建完都**用无正则读法**记一次台数）；
  ② **无正则**读出所有含「机位」的树区文本 ⟹ 得到**真实台数**；
  ③ 删「机位1」⟹ **无正则**再读 ⟹ 台数真的少了吗？
     - 少了 ⟹ 「机位1 删不掉」是**我的口径问题**，★ **推翻前面的结论**；
     - 没少 ⟹ 结论成立（源站确实删不掉默认机位）。
  ④ 再用**正则口径**对照 ⟹ 量化两个口径差了多少。

★ ★ 纪律：会改源站项目 ⟹ 每步**删完复验** ⟹ **收尾复原到只剩「机位1」** ⟹ 异常时 finally 也清理。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836f.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

CAM_RE = re.compile(r"^机位\s*(\d+)$")

# ★ 无正则：所有含「机位」的叶子文本
DUMP_ALL = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a'))) {
    if (!vis(el) || el.childElementCount > 0) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.indexOf('机位')<0) continue;
    const r=el.getBoundingClientRect();
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 树区（左侧）专用的无正则读法
DUMP_LEFT = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a'))) {
    if (!vis(el) || el.childElementCount > 0) continue;
    const r=el.getBoundingClientRect();
    if (r.x > 500) continue;                 // ★ 只要左侧树区
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


def left_all(page):
    """★ 无正则的树区读数 ⟹ 真实台数。"""
    return page.evaluate(DUMP_LEFT)


def left_regex(page):
    """★ 正则口径的读数 ⟹ 用来量化两个口径的差。"""
    return [d["text"] for d in left_all(page) if CAM_RE.match(d["text"])]


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
    back_to_scene(page)
    before_all = left_all(page)
    if not any(d["text"] == name for d in before_all):
        return {"ok": False, "why": "%s 不在树区（%s）" % (name, [d["text"] for d in before_all])}
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(800)
        item.click(button="right")
        page.wait_for_timeout(1_500)
        del_item = page.locator("[role='menuitem']").filter(has_text="删除").first
        if not del_item.count():
            return {"ok": False, "why": "菜单里没有『删除』"}
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
        return {"ok": False, "why": repr(exc)}
    after_all = left_all(page)
    return {"ok": len(after_all) == len(before_all) - 1,
            "before_all": [d["text"] for d in before_all],
            "after_all": [d["text"] for d in after_all],
            "before_regex": left_regex(page)}


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
            base_all = [d["text"] for d in left_all(page)]
            out["①基线_无正则"] = base_all
            out["①基线_正则口径"] = left_regex(page)
            log.append("基线（无正则）%r；正则口径 %r" % (base_all, out["①基线_正则口径"]))

            # 造到 3 台
            guard = 0
            while len(left_all(page)) < 3 and guard < 6:
                guard += 1
                new_camera(page)
            out["②三台_无正则"] = [d["text"] for d in left_all(page)]
            out["②三台_正则口径"] = left_regex(page)
            log.append("三台（无正则）%r；正则口径 %r"
                       % (out["②三台_无正则"], out["②三台_正则口径"]))

            # ★ 决定性：删「机位1」，用无正则计数复验
            res = delete_camera(page, "机位1")
            out["③删机位1_无正则复验"] = res
            log.append("删机位1（无正则复验）：%s" % json.dumps(res, ensure_ascii=False))
            back_to_scene(page)
            out["③删后_无正则"] = [d["text"] for d in left_all(page)]
            out["③删后_正则口径"] = left_regex(page)

            out["④结论"] = (
                "★ 「机位1」**确实删不掉**（无正则口径下台数也没少）⟹ 结论成立"
                if (res.get("before_all") is not None
                    and res.get("after_all") is not None
                    and len(res["after_all"]) == len(res["before_all"]))
                else "★★ 「机位1」**其实删得掉**（无正则口径下台数少了 1）⟹ "
                     "**前面的『删不掉』是我的正则计数口径造的** ⟹ ★ 那个结论被推翻")
            log.append(out["④结论"])
        finally:
            try:
                back_to_scene(page)
                base = out.get("①基线_无正则") or []
                for nm in sorted({d["text"] for d in left_all(page)} - set(base)):
                    delete_camera(page, nm)
                out["收尾_无正则"] = [d["text"] for d in left_all(page)]
                out["收尾正确"] = out["收尾_无正则"] == base
                log.append("收尾：%r（正确=%s）" % (out["收尾_无正则"], out["收尾正确"]))
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
        for k in ("①基线_无正则", "①基线_正则口径", "②三台_无正则", "②三台_正则口径",
                  "③删机位1_无正则复验", "③删后_无正则", "③删后_正则口径",
                  "④结论", "收尾_无正则", "收尾正确"):
            if k in out:
                print("%-20s %s" % (k, json.dumps(out[k], ensure_ascii=False)[:400]))
        print("日志：")
        for line in out.get("日志") or []:
            print("  ", line)
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
