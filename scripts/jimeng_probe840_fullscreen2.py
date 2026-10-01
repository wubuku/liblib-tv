#!/usr/bin/env python3
"""batch 840 源站探针（第二轮）：点「全屏编辑」之后**到底有没有**浮层。

第一轮只按 absolute/fixed/sticky + 面积筛，可能整层漏掉；这一轮改成
"点击是否真的命中" + "body 直接子节点" + "任何高 z / 不透明底"三路对照。
只观察，不点任何付费购买流程。
"""

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(9000)


def snap(tag):
    d = page.evaluate("""() => {
      const out = [];
      for (const e of document.querySelectorAll('body *')) {
        const s = getComputedStyle(e);
        const r = e.getBoundingClientRect();
        if (r.width < 200 || r.height < 100) continue;
        const opaque = s.backgroundColor !== 'rgba(0, 0, 0, 0)'
                       && !s.backgroundColor.startsWith('rgba(0, 0, 0, 0)');
        const z = parseInt(s.zIndex || '0', 10);
        if (!opaque && z < 100) continue;
        out.push({tag: e.tagName, tid: e.getAttribute('data-testid') || '',
                  role: e.getAttribute('role') || '',
                  al: e.getAttribute('aria-label') || '',
                  pos: s.position, z: s.zIndex, bg: s.backgroundColor,
                  w: Math.round(r.width), h: Math.round(r.height),
                  cls: (e.className||'').toString().replace(/\\s+/g,' ').slice(0,60)});
      }
      return out;
    }""")
    print(f"\n== {tag}：body 下「不透明底 或 z≥100」且 ≥200×100 的元素 "
          f"= {len(d)} 个 ==")
    for x in d:
        print("  ", x)


snap("点击前")

btn = page.evaluate("""() => {
  const b = [...document.querySelectorAll('button,[role=menuitem]')]
    .find(x => (x.getAttribute('aria-label')||'').includes('全屏编辑'));
  if (!b) return null;
  const r = b.getBoundingClientRect();
  const cx = r.x + r.width/2, cy = r.y + r.height/2;
  const top = document.elementFromPoint(cx, cy);
  return {al: b.getAttribute('aria-label'), tid: b.getAttribute('data-testid')||'',
          r: {x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height)},
          cx: Math.round(cx), cy: Math.round(cy),
          hit: top ? (top.tagName + '/' + (top.getAttribute('aria-label')||'')
                      + '/' + (top.className||'').toString().slice(0,40)) : null,
          hitIsBtnOrChild: !!(top && (top === b || b.contains(top)))};
}""")
print("\n== 全屏编辑按钮 ==", btn)
if not btn:
    raise SystemExit("!! 源站没找到「全屏编辑」")

if btn["hitIsBtnOrChild"]:
    page.mouse.click(btn["cx"], btn["cy"])
else:
    print("!! 点击点被", btn["hit"], "拦住了，elementFromPoint 不在按钮上 —— "
          "这本身就是一条事实：按钮此刻不可点")
page.wait_for_timeout(3000)
snap("点击后")

print("\n== 点击后是否出现 dialog / modal ==")
print(page.evaluate("""() => ({
    dialog: document.querySelectorAll('[role=dialog]').length,
    modal: document.querySelectorAll('[role=modal]').length,
    ariaModal: document.querySelectorAll('[aria-modal=true]').length,
    bodyKids: [...document.body.children].map(e => e.tagName + '#'
        + (e.id||'-') + '.' + (e.className||'').toString().slice(0,36)),
    scrollLocked: getComputedStyle(document.body).overflow,
})"""))
page.screenshot(path="/tmp/b840-source-after-click.png", full_page=False)
print("\n截图 /tmp/b840-source-after-click.png")
