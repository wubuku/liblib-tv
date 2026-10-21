#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针 v8：★ **用右栏读激活态**，排除最后那个解释。

★ 到 v7 为止已排除的解释：
  ✗ 「最后一台」   ⟹ v3：有 3 台时仍删不掉
  ✗ 「编号最小者」 ⟹ v7：删掉「机位3」后（剩 1、2）仍删不掉
  ✗ 「计数口径错」 ⟹ v6：无正则口径下台数确实没少

★ **还没排除的**：「**当前激活机位**不可删」。
  ⟹ v4 做过「点机位3 再删机位1」⟹ 但**激活态读数是空的**（我的 DUMP_ACTIVE 找不到选中态 class）
  ⟹ ⟹ ★ **那次实验的前提没钉死** ⟹ 结论不算数。

★ 本探针用**右栏第一个输入框**读激活态（★ batch 833 已验证：它 = 选中机位的名字）：
  ① 基线时读右栏 ⟹ 激活的是谁？
  ② 点「机位3」⟹ **读回右栏** ⟹ 确认激活态**真的挪到机位3**了（这一步是硬前提）
  ③ 删「机位1」⟹ 记录
  ⟹ 若②读回确实是「机位3」且③仍删不掉 ⟹ ★ **保护与激活态无关** ⟹ 是「主机位」
  ⟹ 若②读回**不是**「机位3」⟹ ★ **前提不成立** ⟹ 这次实验**不算数** ⟹ 不下结论

★ 纪律：会改源站项目 ⟹ 每步**用无正则口径复验** ⟹ **收尾复原到只剩「机位1」**（带重试）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836h.json")
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

# ★ 右栏第一个输入框 = 选中机位的名字（batch 833 实测口径）
DUMP_ACTIVE_NAME = """()=>{
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


def names(page):
    return [d["text"] for d in page.evaluate(DUMP_LEFT)]


def active_name(page):
    return page.evaluate(DUMP_ACTIVE_NAME)


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


def try_delete(page, name):
    back_to_scene(page)
    before = names(page)
    if name not in before:
        return {"ok": False, "why": "不在树里", "before": before}
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(800)
        item.click(button="right")
        page.wait_for_timeout(1_400)
        d = page.locator("[role='menuitem']").filter(has_text="删除").first
        if not d.count():
            return {"ok": False, "why": "菜单里没有删除", "before": before}
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
        return {"ok": False, "why": repr(exc), "before": before}
    after = names(page)
    return {"ok": len(after) == len(before) - 1, "before": before, "after": after}


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
            base = names(page)
            out["①基线树"] = base
            out["①基线激活名"] = active_name(page)
            log.append("基线树 %r；激活名 %r" % (base, out["①基线激活名"]))

            # 造到 3 台
            guard = 0
            while len(names(page)) < 3 and guard < 6:
                guard += 1
                new_camera(page)
            out["②三台"] = names(page)
            log.append("三台 %r" % out["②三台"])

            # ② 激活态：点「机位3」⟹ 读回右栏
            back_to_scene(page)
            try:
                page.get_by_text("机位3", exact=True).first.click()
                page.wait_for_timeout(1_200)
            except Exception as exc:
                log.append("点机位3 异常：%r" % (exc,))
            act = active_name(page)
            out["③点机位3后的激活名"] = act
            log.append("点机位3 后激活名 %r" % (act,))

            # ③ 前提是否成立
            out["③前提_激活态真的挪到机位3"] = (act == "机位3")
            if act != "机位3":
                out["④实验无效"] = ("★ 激活态读回是 %r（不是「机位3」）⟹ "
                               "**前提不成立** ⟹ 本次实验**不算数** ⟹ 不下结论" % (act,))
                log.append(out["④实验无效"])
            else:
                back_to_scene(page)
                r = try_delete(page, "机位1")
                out["④此时删机位1"] = r
                log.append("此时删机位1：%s" % json.dumps(r, ensure_ascii=False))
                out["⑤判定"] = (
                    "★ 激活态**确实**挪到「机位3」，而「机位1」**仍删不掉** ⟹ "
                    "★ **保护与激活态无关** ⟹ 是「**主机位**」这类**按身份**的规则"
                    if (r.get("before") and r.get("after")
                        and len(r["after"]) == len(r["before"]))
                    else "★ 激活态挪到「机位3」后「机位1」**删得掉** ⟹ 保护是「**当前激活机位**」")
                log.append(out["⑤判定"])
        finally:
            try:
                back_to_scene(page)
                base = out.get("①基线树") or []
                for _ in range(6):
                    cur = names(page)
                    extra = sorted(set(cur) - set(base))
                    if not extra:
                        break
                    nums = sorted(int(n.replace("机位", "")) for n in extra
                                  if n.replace("机位", "").isdigit())
                    victim = ("机位%d" % nums[-1]) if nums else extra[0]
                    ok, why = try_delete(page, victim)["ok"], ""
                    log.append("收尾：删 %s ⟹ %s" % (victim, ok))
                    if ok:
                        continue
                    # ★ 删不掉 ⟹ 换一个目标再试（最多 6 轮）
                    others = [n for n in extra if n != victim]
                    if not others:
                        break
                    try_delete(page, others[0])
                out["收尾树"] = names(page)
                out["收尾正确"] = out["收尾树"] == base
                log.append("收尾 %r（正确=%s）" % (out["收尾树"], out["收尾正确"]))
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
        for k in ("①基线树", "①基线激活名", "②三台", "③点机位3后的激活名",
                  "③前提_激活态真的挪到机位3", "④实验无效", "④此时删机位1", "⑤判定",
                  "收尾树", "收尾正确"):
            if k in out:
                print("%-26s %s" % (k, json.dumps(out[k], ensure_ascii=False)[:360]))
        print("日志：")
        for line in out.get("日志") or []:
            print("  ", line)
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
