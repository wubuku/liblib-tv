#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针 v8：**只做一件事** —— 把源站恢复到只剩「机位1」。

★ 为什么要单独一个脚本：v7 的收尾没复原干净（源站剩「机位1」「机位2」）
  ⟹ v7 的 finally 里按 `set(树) - set(基线)` 逐个删 ⟹ 但「机位2」那次删除
  不知为何没生效（**没有复验**）⟹ ★ **清理也必须带复验 + 重试**。

★ 本脚本：循环「删掉**编号最大**的那台（避开受保护的「机位1」）⟹ 复验 ⟹ 直到只剩「机位1」」
  ⟹ 最多 6 轮 ⟹ 每轮都**读回树**确认 ⟹ 最后**打印最终树** ⟹ 不静默结束。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836_restore.json")
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


def names(page):
    return [d["text"] for d in page.evaluate(DUMP_LEFT)]


def try_delete(page, name):
    back_to_scene(page)
    before = names(page)
    if name not in before:
        return False, "不在树里"
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(800)
        item.click(button="right")
        page.wait_for_timeout(1_400)
        d = page.locator("[role='menuitem']").filter(has_text="删除").first
        if not d.count():
            return False, "菜单里没有删除"
        d.click()
        page.wait_for_timeout(1_300)
        for label in ("确认删除", "确定", "确认"):
            try:
                b = page.get_by_role("button", name=label, exact=True)
                if b.count() and b.first.is_visible():
                    b.first.click()
                    page.wait_for_timeout(900)
                    break
            except Exception:
                pass
        page.wait_for_timeout(1_200)
    except Exception as exc:
        return False, repr(exc)
    after = names(page)
    return (len(after) == len(before) - 1), "%r → %r" % (before, after)


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {"轮次": []}
    try:
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
            back_to_scene(page)
            out["起始树"] = names(page)
            print("起始树：", out["起始树"])
            for i in range(6):
                cur = names(page)
                if cur == ["机位1"]:
                    break
                # ★ 删**编号最大**的那台（跳过受保护的「机位1」）
                nums = sorted(int(n.replace("机位", "")) for n in cur if n.replace("机位", "").isdigit())
                if not nums:
                    break
                victim = "机位%d" % nums[-1]
                ok, why = try_delete(page, victim)
                out["轮次"].append({"轮": i, "删": victim, "成功": ok, "详情": why})
                print("  轮 %d：删 %s ⟹ %s %s" % (i, victim, "✔" if ok else "✘", why))
            out["最终树"] = names(page)
            out["★复原正确"] = out["最终树"] == ["机位1"]
            print("最终树：", out["最终树"], "✔" if out["★复原正确"] else "✘ 未复原")
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)


if __name__ == "__main__":
    main()
