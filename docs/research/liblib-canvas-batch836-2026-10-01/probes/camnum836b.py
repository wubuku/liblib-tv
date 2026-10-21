#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 836 源站探针 v2：**先把判定的前提钉死**，再测「机位N」的编号规则。

★★★ v1 的两处真缺陷（本版修掉）：
  ① **判定在「没有编号空洞」时照样给出「max+1」** ——
     v1 的「⑥判定」只问「新建后是否与已有编号重名」，
     而**连续编号下「不重名」是必然的** ⟹ 于是它在**根本没做出空洞**的实验上
     给出了「max+1（不重名）」这个**看起来很确定的错误结论**。
     ⟹ ★ 这就是「判据没测到要测的那件事」：**不问前提，就问结论**。
     ⟹ **本版把「空洞存在」变成判定的硬前提**：删完后编号集合**必须不连续**，
        否则直接判「实验无效」并停下（不产出结论）。
  ② **删「机位1」没生效** —— v1 删最小编号那台，日志是「3 → 3 台 ✘ 未减少」。
     ⟹ 「机位1」很可能是**默认机位、不可删**（这是一个**新产品事实**，要单独记）。
     ⟹ ★ 但**不改实验设计去迁就实现**：本版**两个都做**：
        - 先单独测「机位1 能不能删」（独立事实）；
        - 主实验改删**编号第二小**的那台（留下「机位1」＋「机位3」⟹ 空洞在 2）。

★ 纪律（红线，与 batch 833/836v1 同款）：
  - 本探针**会改源站项目**（新建/删除机位）⟹ 每步**删完必须复验**；
  - ⟹ **收尾必须复原**（回到只剩基线那几台）；
  - ⟹ 若中途出错，**也要在 finally 里跑一次清理**。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_camnum836b.json")
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


def delete_camera(page, log, name, verbose=False):
    """删掉**指定名字**的那台 ⟹ 删完**复验**少了一台才算成功。"""
    back_to_scene(page)
    cams = tree_cameras(page)
    if name not in cams:
        log.append("★ %s 不在场景树里（%s）⟹ 无需删" % (name, cams))
        return True
    diag = {"name": name, "before": cams}
    try:
        item = page.get_by_text(name, exact=True).first
        item.click()
        page.wait_for_timeout(700)
        item.click(button="right")
        page.wait_for_timeout(1_500)
        # ★ 把右键菜单里**可见的菜单项全部**列出来（诊断用）
        items = page.locator("[role='menuitem']")
        diag["menuItems"] = [items.nth(i).inner_text().strip() for i in range(items.count())]
        diag["menuItemsVisible"] = [items.nth(i).is_visible() for i in range(items.count())]
        del_item = page.locator("[role='menuitem']").filter(has_text="删除").first
        if not del_item.count():
            log.append("右键菜单里没有 menuitem『删除』；菜单项=%r" % diag["menuItems"])
            diag["ok"] = False
            return False
        del_item.click()
        page.wait_for_timeout(1_500)
        # ★ 确认弹窗：有就点，没有就当**没有确认框**（并如实记）
        diag["confirmClicked"] = None
        for label in ("确认删除", "确定", "确认"):
            try:
                b = page.get_by_role("button", name=label, exact=True)
                if b.count() and b.first.is_visible():
                    b.first.click()
                    page.wait_for_timeout(1_000)
                    diag["confirmClicked"] = label
                    break
            except Exception:
                pass
        page.wait_for_timeout(1_000)
    except Exception as exc:
        diag["exception"] = repr(exc)
        log.append("删 %s 时异常：%r" % (name, exc))
    after = tree_cameras(page)
    ok = len(after) == len(cams) - 1
    diag["after"] = after
    diag["ok"] = ok
    if verbose:
        log.append("删除诊断：%s" % json.dumps(diag, ensure_ascii=False))
    log.append("删 %s：%d → %d 台 %s" % (name, len(cams), len(after),
                                        "✔" if ok else "✘ 未减少"))
    return ok


def new_camera_via_preset(page, log):
    """点 rail 的「添加机位」→ 点第一枚预设 ⟹ 真的新建一台 ⟹ 返回新机位的名字。"""
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
    """编号集合**是否有空洞**（不连续）。"""
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
            # ---------- ① 基线 ----------
            back_to_scene(page)
            base = tree_cameras(page)
            out["①基线树"] = base
            out["①基线编号"] = nums_of(base)
            log.append("基线树：%s" % base)

            # ---------- ② 独立事实：「机位1」能不能删？ ----------
            out["②机位1可删"] = delete_camera(page, log, "机位1", verbose=True)
            back_to_scene(page)
            out["②删机位1后树"] = tree_cameras(page)
            if not out["②机位1可删"]:
                log.append("★ 机位1 删不掉（**新事实**：它很可能是默认机位、不可删）")
                # 把它补回来，后面用机位2/3 做实验
                n_back = new_camera_via_preset(page, log)
                back_to_scene(page)
                log.append("补回一台：%r ⟹ 树=%s" % (n_back, tree_cameras(page)))

            # ---------- ③ 造出 3 台（1,2,3）----------
            cur = nums_of(tree_cameras(page))
            while len(cur) < 3:
                new_camera_via_preset(page, log)
                back_to_scene(page)
                cur = nums_of(tree_cameras(page))
            out["③造出三台后树"] = tree_cameras(page)
            out["③编号"] = cur

            # ---------- ④ 删掉**编号第二小**的那台（跳过机位1）⟹ 制造空洞 ----------
            victim = "机位%d" % cur[1] if len(cur) >= 3 else None
            out["④要删的机位"] = victim
            ok_del = delete_camera(page, log, victim, verbose=True)
            out["④删除成功"] = ok_del
            back_to_scene(page)
            t4 = tree_cameras(page)
            nums4 = nums_of(t4)
            out["④删后树"] = t4
            out["④删后编号"] = nums4

            # ★★★ 判定的**硬前提**：必须真的有空洞，否则实验无效
            gap = has_gap(nums4)
            out["④有编号空洞"] = gap
            if not gap:
                out["⑤实验无效"] = ("删后编号 %r **不连续** ⟹ 没有制造出空洞 ⟹ "
                                     "接下来的「新建」无法区分 count+1 与 max+1 "
                                     "⟹ **不下结论**" % (nums4,))
                log.append("★ 实验无效：删后编号 %r 不连续" % (nums4,))
            else:
                # ---------- ⑤ 决定性：空洞态下新建 ----------
                n3 = new_camera_via_preset(page, log)
                back_to_scene(page)
                t5 = tree_cameras(page)
                nums5 = nums_of(t5)
                new_num = int(CAM_RE.match(n3).group(1)) if n3 and CAM_RE.match(n3) else None
                out["⑤空洞态新建后树"] = t5
                out["⑤新机位名"] = n3
                out["⑤新机位编号"] = new_num
                dup = new_num is not None and new_num in nums4
                out["⑥判定"] = {
                    "前提_删后编号不连续": True,
                    "删后已有的编号": nums4,
                    "新机位编号": new_num,
                    "与已有编号重名": dup,
                    "规则": ("count+1（**会与已有编号重名**）" if dup
                             else "max+1（不重名）" if new_num is not None else "读不到"),
                }
                log.append("判定：%s" % out["⑥判定"])

            # ---------- ⑦ 复原 ----------
            back_to_scene(page)
            cur = tree_cameras(page)
            for nm in sorted(set(cur) - set(base),
                             key=lambda x: -nums_of([x])[0] if nums_of([x]) else 0):
                delete_camera(page, log, nm)
            back_to_scene(page)
            out["⑦复原后树"] = tree_cameras(page)
            out["⑦复原正确"] = sorted(tree_cameras(page)) == sorted(base)
            log.append("复原后树：%s（正确=%s）" % (tree_cameras(page), out["⑦复原正确"]))
        finally:
            try:
                back_to_scene(page)
                cur = tree_cameras(page)
                for nm in sorted(set(cur) - set(base)):
                    delete_camera(page, log, nm)
                out["收尾树"] = tree_cameras(page)
            except Exception:
                out["收尾异常"] = traceback.format_exc()
            try:
                page.screenshot(path="/tmp/liblib_source_camnum836b.png")
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
        for k in ("①基线树", "②机位1可删", "②删机位1后树", "③造出三台后树", "③编号",
                  "④要删的机位", "④删除成功", "④删后树", "④删后编号", "④有编号空洞",
                  "⑤实验无效", "⑤空洞态新建后树", "⑤新机位名", "⑥判定",
                  "⑦复原后树", "⑦复原正确"):
            if k in out:
                print("%-18s %s" % (k, json.dumps(out[k], ensure_ascii=False)))
        print("删除日志：")
        for line in out.get("删除日志") or []:
            print("  ", line)
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
