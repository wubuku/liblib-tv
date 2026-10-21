#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针 v4：判别「机位1 删不掉」的**保护依据**是哪一条。

★ v3 已确认的事实：在**有 3 台**时删「机位1」⟹ **删不掉**（3 → 3 台）
  ⟹ ⟹ 源站有一条「**最后一台**之外」的保护规则。

★★★ 但「有 3 台时删不掉」**还不足以**说明保护的是「默认/首台机位」——
  还有一种可能：**保护的是「当前激活的那台机位」**（源站默认镜头就是「机位1」，
  也许它在被激活 ⟹ 删了就没镜头了）⟹ ★ 这两种解释的**实现方式完全不同**：
    - 若保护的是「默认/首台」 ⟹ clone 该按**身份**判（`director-camera-main`）；
    - 若保护的是「当前激活机位」 ⟹ clone 该按**激活状态**判。

★ ★ 所以本探针做**判别实验**：**先把激活状态挪到另一台机位上**，再删「机位1」：
    - 删得掉 ⟹ 保护是「当前激活机位」；
    - 仍删不掉 ⟹ 保护是「默认/首台机位」（或别的与激活无关的规则）。

★ 顺带记录：右键菜单里「删除」项是否**置灰/禁用**（`aria-disabled` / `disabled` 属性），
  以及点删除后页面是否出现**提示气泡**（toast）⟹ 那是「为什么删不掉」的直接线索。

★ 纪律：会改源站项目 ⟹ 每步**删完复验** ⟹ **收尾复原到只剩「机位1」** ⟹ 异常时 finally 也清理。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836d.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

CAM_RE = re.compile(r"^机位\s*(\d+)$")

DUMP_TREE = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  return [...new Set(Array.from(document.querySelectorAll('span')).filter(vis)
    .map(s=>(s.textContent||'').trim())
    .filter(t=>/^机位\\s*\\d+$/.test(t)))];
}"""

# ★ 场景树里当前被选中的机位（找带选中态 class 的那一条）
DUMP_ACTIVE = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const hits=[];
  for (const s of Array.from(document.querySelectorAll('span')).filter(vis)) {
    const t=(s.textContent||'').trim();
    if(!/^机位\\s*\\d+$/.test(t)) continue;
    let e=s, chain=[];
    for (let i=0;i<5 && e;i++,e=e.parentElement) {
      chain.push({tag:e.tagName, cls:(e.className||'').toString().slice(0,120),
                  aria:(e.getAttribute&&e.getAttribute('aria-selected'))});
    }
    const selected = chain.some(c=>/selected|active|ring|highlight/i.test(c.cls||'') ||
                                   c.aria==='true');
    if (selected) hits.push({name:t, chain});
  }
  return hits;
}"""

# ★ 右键菜单里「删除」项的状态
DUMP_MENU = """()=>{
  const items=Array.from(document.querySelectorAll("[role='menuitem']"))
    .filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;});
  return items.map(e=>({text:(e.textContent||'').trim(),
    ariaDisabled:e.getAttribute('aria-disabled'),
    disabled: e.hasAttribute('disabled') || e.getAttribute('disabled')!==null,
    cls:(e.className||'').toString().slice(0,140)}));
}"""

# ★ 页面上的提示气泡（toast）
DUMP_TOAST = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const sels=['[role="alert"]','[role="status"]','[data-sonner-toast]','.toast','[class*="toast"]','[class*="Toast"]','[class*="message"]'];
  const out=[];
  for (const sel of sels) for (const e of Array.from(document.querySelectorAll(sel))) {
    if (vis(e)) { const t=(e.textContent||'').trim(); if(t) out.push({sel, text:t.slice(0,120)}); }
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


def tree_cameras(page):
    return page.evaluate(DUMP_TREE)


def back_to_scene(page):
    try:
        nav = page.locator("nav").filter(
            has=page.locator("button[aria-label='场景']")).first
        nav.locator("button[aria-label='场景']").first.click()
        page.wait_for_timeout(1_400)
    except Exception:
        pass


def delete_camera(page, log, name):
    back_to_scene(page)
    cams = tree_cameras(page)
    if name not in cams:
        log.append("★ %s 不在场景树里（%s）⟹ 无需删" % (name, cams))
        return True
    menu = []
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(800)
        item.click(button="right")
        page.wait_for_timeout(1_500)
        menu = page.evaluate(DUMP_MENU)
        del_item = page.locator("[role='menuitem']").filter(has_text="删除").first
        if not del_item.count():
            log.append("右键菜单里没有 menuitem『删除』；菜单=%r" % (menu,))
            return False
        del_item.click()
        page.wait_for_timeout(1_200)
        toast = page.evaluate(DUMP_TOAST)
        for label in ("确认删除", "确定", "确认"):
            try:
                b = page.get_by_role("button", name=label, exact=True)
                if b.count() and b.first.is_visible():
                    b.first.click()
                    page.wait_for_timeout(1_000)
                    break
            except Exception:
                pass
        page.wait_for_timeout(1_200)
        log.append("删 %s 后 toast=%r" % (name, toast))
    except Exception as exc:
        log.append("删 %s 时异常：%r" % (name, exc))
    after = tree_cameras(page)
    ok = len(after) == len(cams) - 1
    log.append("删 %s：%d → %d 台 %s（树 %s）"
               % (name, len(cams), len(after), "✔" if ok else "✘ 未减少", after))
    return ok


def new_camera_via_preset(page, log):
    nav = page.locator("nav").filter(
        has=page.locator("button[aria-label='场景']")).first
    nav.locator("button[aria-label='添加机位']").first.click()
    page.wait_for_timeout(2_200)
    grid = page.locator("div.grid.min-h-0.flex-1").first
    cells = grid.locator("button")
    if not cells.count():
        log.append("★ 机位预设面板里没有格子")
        return None
    cells.nth(0).click()
    page.wait_for_timeout(2_400)
    log.append("新建了一台")
    return True


def activate_camera(page, name, log):
    """在场景树里点一下某台机位 ⟹ 让它成为当前激活的机位。"""
    back_to_scene(page)
    try:
        page.get_by_text(name, exact=True).first.click()
        page.wait_for_timeout(1_000)
        log.append("点了 %s（试图激活它）" % name)
        return True
    except Exception as exc:
        log.append("激活 %s 失败：%r" % (name, exc))
        return False


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
            base = tree_cameras(page)
            out["①基线树"] = base
            log.append("基线树：%s" % base)

            # 造出 3 台
            while len(tree_cameras(page)) < 3:
                new_camera_via_preset(page, log)
                back_to_scene(page)
            out["②三台"] = tree_cameras(page)

            # 观测 ③：激活状态（谁被选中）
            out["③激活的机位_初始"] = page.evaluate(DUMP_ACTIVE)
            log.append("初始激活读数：%r" % out["③激活的机位_初始"])

            # ★ 关键：把激活状态挪到「机位3」上 ⟹ 再删「机位1」
            activate_camera(page, "机位3", log)
            back_to_scene(page)
            out["④激活的机位_激活机位3后"] = page.evaluate(DUMP_ACTIVE)
            log.append("激活机位3 后读数：%r" % out["④激活的机位_激活机位3后"])

            out["⑤机位1可删"] = delete_camera(page, log, "机位1")
            back_to_scene(page)
            out["⑤删后树"] = tree_cameras(page)
            out["⑤判定"] = (
                "★ 激活状态挪到「机位3」后，**「机位1」仍删不掉** ⟹ "
                "保护**与激活状态无关** ⟹ 是「默认/首台机位」这类**按身份**的规则"
                if out["⑤机位1可删"] is False else
                "★ 激活状态挪到「机位3」后，「机位1」**删得掉** ⟹ "
                "保护是「**当前激活机位**」（**不是**按身份）")
            log.append("判定：%s" % out["⑤判定"])

            # 对照：删「机位3」（当前激活的那台）⟹ 若也删不掉 ⟹ 保护是激活态
            out["⑥机位3可删_激活态下"] = delete_camera(page, log, "机位3")
            back_to_scene(page)
            out["⑥删后树"] = tree_cameras(page)
            log.append("对照：删「机位3」→ %s" % out["⑥机位3可删_激活态下"])
        finally:
            try:
                back_to_scene(page)
                cur = tree_cameras(page)
                for nm in sorted(set(cur) - set(base)):
                    delete_camera(page, log, nm)
                out["收尾树"] = tree_cameras(page)
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
        for k in ("①基线树", "②三台", "③激活的机位_初始", "④激活的机位_激活机位3后",
                  "⑤机位1可删", "⑤删后树", "⑤判定", "⑥机位3可删_激活态下", "⑥删后树", "收尾树"):
            if k in out:
                print("%-22s %s" % (k, json.dumps(out[k], ensure_ascii=False)[:300]))
        print("日志：")
        for line in out.get("日志") or []:
            print("  ", line)
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
