#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针 v3：补上 v2 **没有验证的前提**。

★★★ v2 的 raw 里写了一句**没被验证**的结论：
  「★新事实_机位1不可删 ⟹ 默认机位受保护」
  ⟹ ★★ **但那次是在「只有 1 台」时测的** ⟹ 那只证明了「**最后一台**不可删」
     （clone 也是这样 ⟹ `DIRECTOR_LAST_CAMERA_REQUIRED`）⟹ ★ **区分不了**
        「默认机位受保护」与「最后一台不可删」这两条不同的规则！
  ⟹ ★ 而且这已经是本批的**第二个「前提没验证就下结论」**：
     v1 是「没做出空洞却给出 count/max 判定」⟹ v2 是「没排除『最后一台』却断言『受保护』」。
     ⟹ **同一种错误在同一批里犯了两次** ⟹ 修法：**每个否定性结论都要问「有没有别的解释」**。

★ 本探针要回答的三个问题（每个都**先钉死前提**）：
  ① 在**有 3 台**的状态下，删「机位1」（默认机位）⟹ 删得掉吗？
     - 删得掉 ⟹ 源站**没有**「默认机位受保护」这条规则 ⟹ 与 clone 一致（只有「最后一台」保护）；
     - 删不掉 ⟹ 源站**有**「默认机位受保护」⟹ ★ 与 clone 是**实质差异**（clone 在有 2 台时能删默认机位）。
  ② 顺手复验 count+1（空洞态新建 ⟹ 是否重名）⟹ 与 v2 交叉核对。
  ③ 收尾复原到只剩「机位1」。

★ 纪律：会改源站项目 ⟹ 每步**删完复验** ⟹ **收尾必须复原** ⟹ 异常时 finally 也清理。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836c.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

CAM_RE = re.compile(r"^机位\s*(\d+)$")

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

DUMP_TREE = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  return [...new Set(Array.from(document.querySelectorAll('span')).filter(vis)
    .map(s=>(s.textContent||'').trim())
    .filter(t=>/^机位\\s*\\d+$/.test(t)))];
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
    """删掉**指定名字**的那台 ⟹ 删完**复验**少了一台才算成功。

    ★ ★ 注意「重名」的坑：场景里若有两个同名机位（空洞态新建造出来的），
      `get_by_text(name, exact=True).first` 命中的**未必是想要的那一个** ⟹
      所以本函数**删完必须复验台数**；若台数没减 ⟹ **如实记「未减少」**（不重试到成功为止）。
    """
    back_to_scene(page)
    cams = tree_cameras(page)
    if name not in cams:
        log.append("★ %s 不在场景树里（%s）⟹ 无需删" % (name, cams))
        return True
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(700)
        item.click(button="right")
        page.wait_for_timeout(1_500)
        del_item = page.locator("[role='menuitem']").filter(has_text="删除").first
        if not del_item.count():
            log.append("右键菜单里没有 menuitem『删除』")
            return False
        del_item.click()
        page.wait_for_timeout(1_500)
        for label in ("确认删除", "确定", "确认"):
            try:
                b = page.get_by_role("button", name=label, exact=True)
                if b.count() and b.first.is_visible():
                    b.first.click()
                    page.wait_for_timeout(1_000)
                    break
            except Exception:
                pass
        page.wait_for_timeout(1_000)
    except Exception as exc:
        log.append("删 %s 时异常：%r" % (name, exc))
    after = tree_cameras(page)
    ok = len(after) == len(cams) - 1
    log.append("删 %s：%d → %d 台 %s（场景树 %s）"
               % (name, len(cams), len(after), "✔" if ok else "✘ 未减少", after))
    return ok


def new_camera_via_preset(page, log):
    nav = page.locator("nav").filter(
        has=page.locator("button[aria-label='场景']")).first
    nav.locator("button[aria-label='添加机位']").first.click()
    page.wait_for_timeout(2_200)
    grid = page.locator("div.grid.min-h-0.flex-1").first
    cells = grid.locator("button")
    n = cells.count()
    if not n:
        log.append("★ 机位预设面板里没有格子")
        return None
    cells.nth(0).click()
    page.wait_for_timeout(2_400)
    name = page.evaluate(DUMP_NEWNAME)
    log.append("点第一枚预设后右栏读到的新机位名：%r" % (name,))
    return name


def nums_of(names):
    out = []
    for n in names:
        m = CAM_RE.match(n)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


def has_gap(nums):
    if len(nums) < 2:
        return False
    s = sorted(nums)
    return any(b - a > 1 for a, b in zip(s, s[1:]))


def run(out, cookies):
    log = out.setdefault("删除日志", [])
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

            # ---------- ② 造出 3 台 ----------
            cur = nums_of(base)
            while len(cur) < 3:
                new_camera_via_preset(page, log)
                back_to_scene(page)
                cur = nums_of(tree_cameras(page))
            out["②造出三台后树"] = tree_cameras(page)
            out["②编号"] = cur
            log.append("三台：%s" % tree_cameras(page))

            # ---------- ③ ★★ 决定性：在**有 3 台**时删「机位1」（默认机位）----------
            out["③前提_删之前有几台"] = len(tree_cameras(page))
            out["③机位1可删"] = delete_camera(page, log, "机位1")
            back_to_scene(page)
            out["③删后树"] = tree_cameras(page)
            out["③判定_默认机位是否受保护"] = (
                "★ **受保护**（在有 %d 台时仍删不掉 ⟹ 源站有一条「最后一台」之外的规则）"
                % len(out["②造出三台后树"]) if out["③机位1可删"] is False else
                "删得掉 ⟹ 源站**没有**「默认机位受保护」规则 ⟹ 与 clone 一致（只有「最后一台」保护）")
            log.append("判定：%s" % out["③判定_默认机位是否受保护"])

            # 若删掉了 ⟹ 补回一台，让后面还有 3 台可用
            if out["③机位1可删"]:
                while len(nums_of(tree_cameras(page))) < 3:
                    new_camera_via_preset(page, log)
                    back_to_scene(page)
                out["③补回后树"] = tree_cameras(page)

            # ---------- ④ 复验 count+1（空洞态） ----------
            cur = nums_of(tree_cameras(page))
            if len(cur) >= 3:
                victim = "机位%d" % cur[1]
                out["④要删的机位"] = victim
                out["④删除成功"] = delete_camera(page, log, victim)
                back_to_scene(page)
                t4 = tree_cameras(page)
                nums4 = nums_of(t4)
                out["④删后树"] = t4
                out["④删后编号"] = nums4
                out["④有编号空洞"] = has_gap(nums4)
                if not has_gap(nums4):
                    out["④实验无效"] = "删后编号 %r 不连续 ⟹ 不下结论" % (nums4,)
                else:
                    new_camera_via_preset(page, log)
                    back_to_scene(page)
                    t5 = tree_cameras(page)
                    out["④空洞态新建后树"] = t5
                    nums5 = nums_of(t5)
                    # 新机位名 = 树里**不在删后集合里**的那一个（按名字多重集算）
                    from collections import Counter
                    c4 = Counter(tree_cameras(page))
                    c5 = Counter(t5)
                    added = list((c5 - c4).elements())
                    out["④新增的名字"] = added
                    new_num = None
                    for nm in added:
                        m = CAM_RE.match(nm)
                        if m:
                            new_num = int(m.group(1))
                    out["④新机位编号"] = new_num
                    dup = new_num is not None and new_num in nums4
                    out["④判定"] = {
                        "前提_删后编号不连续": True,
                        "删后已有的编号": nums4,
                        "新机位编号": new_num,
                        "与已有编号重名": dup,
                        "规则": ("count+1（**会与已有编号重名**）" if dup
                                 else "max+1（不重名）" if new_num is not None else "读不到"),
                    }
                    log.append("空洞态判定：%s" % out["④判定"])

            # ---------- ⑤ 复原 ----------
            back_to_scene(page)
            for nm in sorted(set(tree_cameras(page)) - set(base)):
                delete_camera(page, log, nm)
            back_to_scene(page)
            out["⑤复原后树"] = tree_cameras(page)
            out["⑤复原正确"] = sorted(tree_cameras(page)) == sorted(base)
            log.append("复原后树：%s（正确=%s）" % (tree_cameras(page), out["⑤复原正确"]))
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
        OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("①基线树", "②造出三台后树", "②编号", "③前提_删之前有几台",
                  "③机位1可删", "③删后树", "③判定_默认机位是否受保护",
                  "④删后编号", "④有编号空洞", "④实验无效", "④新增的名字",
                  "④新机位编号", "④判定", "⑤复原后树", "⑤复原正确", "收尾树"):
            if k in out:
                print("%-24s %s" % (k, json.dumps(out[k], ensure_ascii=False)))
        print("删除日志：")
        for line in out.get("删除日志") or []:
            print("  ", line)
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
