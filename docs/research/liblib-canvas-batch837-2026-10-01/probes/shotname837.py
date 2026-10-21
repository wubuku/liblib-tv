#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 837 源站探针：查清「**镜头名**」的命名规则。

★ 为什么要查这个：clone 现在用 `${camera.name} · 镜头` 派生镜头名
  （`src/store/directorStore.ts:911`），而 batch 836 实测到：
    - 源站的**机位**叫「机位1」；
    - 源站的**镜头**叫「机位01 · 对峙中景 · 镜头」。
  ⟹ ★★ **源站的镜头名里那个「机位01 · 对峙中景」不是机位名** ⟹
  ⟹ ★★ **源站的镜头名不是从机位名派生的** ⟹ clone 的派生模式本身可能是照着旧读数建的。
  ⟹ 而源站**没有改名功能**（batch 836 v7 实测：右键菜单里没有「重命名」）
  ⟹ ⟹ ★ **这个规则必须从源站读，不能靠推断**。

★ 本探针要读到的：
  ① 源站场景里**所有**镜头名（无正则，原样读）；
  ② 每个镜头名对应的**机位名**（镜头条上每枚 chip 的「机位N」标签）；
  ③ 新建一台机位后，**它的镜头叫什么**（这是「派生规则」的直接证据）⟹ ★ 关键；
  ④ 再建一台 ⟹ 看命名是否随编号变。

★ 纪律：会改源站项目 ⟹ 新建的机位**必须删掉** ⟹ 每步**无正则口径复验** ⟹ 收尾复原到只剩「机位1」。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_shotname837.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 场景树区（左侧）所有含「镜头」的可见文本，原样读
DUMP_SHOTS = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a'))) {
    if (!vis(el) || el.childElementCount > 0) continue;
    const r=el.getBoundingClientRect();
    if (r.x > 500) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.indexOf('镜头')<0) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 场景树区所有含「机位」的可见文本
DUMP_CAMS = """()=>{
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

# ★ 右栏第一个输入框 = 选中机位的名字
DUMP_NEWNAME = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const cols=Array.from(document.querySelectorAll('div')).filter(e=>{
    const r=e.getBoundingClientRect();
    return vis(e)&&r.x>=1600&&r.width>=240&&r.width<=300&&r.height>=900;});
  const col=cols[cols.length-1];
  if(!col) return null;
  const ins=Array.from(col.querySelectorAll('input')).filter(vis);
  return ins.length?ins[0].value:null;
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


def texts(page, fn):
    return [d["text"] for d in page.evaluate(fn)]


def new_camera(page):
    nav = page.locator("nav").filter(
        has=page.locator("button[aria-label='场景']")).first
    nav.locator("button[aria-label='添加机位']").first.click()
    page.wait_for_timeout(2_200)
    grid = page.locator("div.grid.min-h-0.flex-1").first
    cells = grid.locator("button")
    if not cells.count():
        return None
    cells.nth(0).click()
    page.wait_for_timeout(2_600)
    return page.evaluate(DUMP_NEWNAME)


def try_delete(page, name):
    back_to_scene(page)
    before = texts(page, DUMP_CAMS)
    if name not in before:
        return False
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(800)
        item.click(button="right")
        page.wait_for_timeout(1_400)
        d = page.locator("[role='menuitem']").filter(has_text="删除").first
        if not d.count():
            return False
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
    except Exception:
        return False
    after = texts(page, DUMP_CAMS)
    return len(after) == len(before) - 1


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
            base_cams = texts(page, DUMP_CAMS)
            out["①基线_机位"] = base_cams
            out["①基线_镜头"] = texts(page, DUMP_SHOTS)
            log.append("基线机位 %r；镜头 %r"
                       % (out["①基线_机位"], out["①基线_镜头"]))

            # ② 新建一台 ⟹ 它的镜头叫什么（★ 关键证据）
            n1 = new_camera(page)
            back_to_scene(page)
            out["②新建后_机位"] = texts(page, DUMP_CAMS)
            out["②新建后_镜头"] = texts(page, DUMP_SHOTS)
            out["②新机位名"] = n1
            log.append("新建 %r 后：机位 %r；镜头 %r"
                       % (n1, out["②新建后_机位"], out["②新建后_镜头"]))

            # ③ 再建一台 ⟹ 命名是否随编号变
            n2 = new_camera(page)
            back_to_scene(page)
            out["③再建后_机位"] = texts(page, DUMP_CAMS)
            out["③再建后_镜头"] = texts(page, DUMP_SHOTS)
            out["③新机位名"] = n2
            log.append("再建 %r 后：机位 %r；镜头 %r"
                       % (n2, out["③再建后_机位"], out["③再建后_镜头"]))

            # ④ 判定：镜头名与机位名的对应关系
            out["④判定"] = {
                "基线机位": out["①基线_机位"],
                "基线镜头": out["①基线_镜头"],
                "★镜头名里是否含机位名": {
                    cam: [s for s in out["③再建后_镜头"] if cam in s]
                    for cam in out["③再建后_机位"]},
                "★镜头名是否 == 机位名 + 「 · 镜头」": all(
                    (cam + " · 镜头") in out["③再建后_镜头"]
                    for cam in out["③再建后_机位"]),
            }
            log.append("判定：%s" % json.dumps(out["④判定"], ensure_ascii=False))
        finally:
            try:
                back_to_scene(page)
                base = out.get("①基线_机位") or []
                for _ in range(6):
                    cur = texts(page, DUMP_CAMS)
                    extra = sorted(set(cur) - set(base))
                    if not extra:
                        break
                    nums = sorted(int(n.replace("机位", "")) for n in extra
                                  if n.replace("机位", "").isdigit())
                    victim = ("机位%d" % nums[-1]) if nums else extra[0]
                    ok = try_delete(page, victim)
                    log.append("收尾：删 %s ⟹ %s" % (victim, ok))
                    if not ok:
                        others = [n for n in extra if n != victim]
                        if not others:
                            break
                        try_delete(page, others[0])
                out["收尾_机位"] = texts(page, DUMP_CAMS)
                out["收尾_镜头"] = texts(page, DUMP_SHOTS)
                out["收尾正确"] = out["收尾_机位"] == base
                log.append("收尾机位 %r（正确=%s）"
                           % (out["收尾_机位"], out["收尾正确"]))
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
        for k in ("①基线_机位", "①基线_镜头", "②新机位名", "②新建后_机位",
                  "②新建后_镜头", "③新机位名", "③再建后_机位", "③再建后_镜头",
                  "④判定", "收尾_机位", "收尾_镜头", "收尾正确"):
            if k in out:
                print("%-16s %s" % (k, json.dumps(out[k], ensure_ascii=False)[:400]))
        print("日志：")
        for line in out.get("日志") or []:
            print("  ", line)
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
