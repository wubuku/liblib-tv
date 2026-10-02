#!/usr/bin/env python3
"""batch 855 源站侦察：顶栏那几个 launcher **各自到底开出什么**。

`topbar-history-menu` 一直记「**前置态没成立**」：847c/847d 想点「生成历史」，
点开第 2 个 `canvas-panel-launcher` 得到的却是**「积分明细」**，0 个新的
fixed 层 ⇒ 于是判「这一版画布取不到样」。

⚠️ 但那个结论里藏着一个**从没验证过的前提**：*「生成历史」就是第 2 个
launcher*。847 记的是「点**第 2 个** `canvas-panel-launcher`」——
**按位置猜的，没按名字对**。859 同款：源站顶栏一排 launcher 里，
第 2 个可能是积分/消息/历史/其它，**位置和功能没有对应关系**。
所以「点第 2 个」是个**没验证的指针**。

这一批就把它验掉：**把顶栏每一个 launcher 都点一遍，逐个记下
「它开出的到底是什么」**（标题 / 角色 / 几何 / 里面有哪些条目），
让「生成历史」自己露出名字，而不是靠位置猜。

⚠️ 计费边界：只点**顶栏 launcher**。**绝不**点生成/发送/购买/充值/兑换
—— 积分页里可能有「充值」按钮，一个都不碰。
"""

import json
import sys

from jimeng_kb_probe_lib import SNAP_JS, UNMARK_JS  # noqa: E402

sys.path.insert(0, __file__.rsplit("/", 1)[0])

BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值", "兑换")


def guard(label):
    t = (label or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED_EXACT or base in BILLED_EXACT or any(t.startswith(b) for b in BILLED_PREFIX):
        print(f"   🛑 拦下付费动作 {t!r}（不点）")
        return True
    return False


def diff_layers(before, after):
    keys = {(b["x"], b["y"], b["w"], b["h"]) for b in before}
    return [a for a in after if (a["x"], a["y"], a["w"], a["h"]) not in keys]


# 打开的层里**有什么**（标题 + 若干条目）—— 「积分明细」和「生成历史」靠这个分
# ⚠️ 第一版这个选择器**没限定在层内**（`document.querySelectorAll` 从整页开始），
#    于是「里面写着」抓回来的是**全页文本**（测试项目/节点20/视频1/时间线1…），
#    跟刚点开的层毫无关系。判据量错对象的老毛病又来了 —— 只是这次量错的是
#    「读的文本」而不是「认的层」。改成**先认层、再只读层内**。
INSIDE_JS = """(rect) => {
  const [x, y, w, h] = rect;
  // 找矩形**包含**这个面板的最小可见容器
  let best = null, bestArea = Infinity;
  for (const e of document.querySelectorAll('div,section,aside,[role=dialog]')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < w - 2 || r.height < h - 2) continue;
    if (r.x > x + 2 || r.y > y + 2) continue;
    const a = r.width * r.height;
    if (a < bestArea) { bestArea = a; best = e; }
  }
  const root = best || document.body;
  const t = [];
  for (const e of root.querySelectorAll('h1,h2,h3,div,span,p,li,button')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    if (r.x < x - 4 || r.y < y - 4) continue;
    const own = [...e.childNodes].filter(n => n.nodeType === 3)
      .map(n => n.textContent.trim()).join(' ').trim();
    if (own && own.length <= 24) t.push(own);
  }
  return [...new Set(t)].slice(0, 30);
}"""

out = {}
page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(2500)
print(f"== URL {page.url[:60]}… ==")

# 顶栏所有 launcher + 具名按钮，一个不漏
BARS = """() => {
  const bar = document.querySelector('header[aria-label="Canvas top bar"]')
    || document.querySelector('header');
  const scope = bar || document.body;
  const out = [];
  for (const b of scope.querySelectorAll('button,[role=button]')) {
    const s = getComputedStyle(b);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = b.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    out.push({al: b.getAttribute('aria-label') || '',
              txt: (b.innerText || '').trim().slice(0, 14),
              launcher: /canvas-panel-launcher|panel-launcher|launcher/
                .test(b.className || ''),
              cls: (b.className || '').toString().replace(/\\s+/g, ' ').slice(0, 50),
              rect: [Math.round(r.x), Math.round(r.y),
                     Math.round(r.width), Math.round(r.height)]});
  }
  out.sort((a, b) => a.rect[0] - b.rect[0]);
  return out;
}"""

bars = page.evaluate(BARS)
print(f"== 顶栏可见按钮 {len(bars)} 个（按 x 排序）==")
for i, b in enumerate(bars):
    print(f"  [{i:>2}] launcher={b['launcher']!s:<5} al={b['al']!r:<16} "
          f"txt={b['txt']!r:<16} rect={b['rect']}")
out["topbar"] = bars

print("\n########## 逐个点开，看它到底是什么 ##########")
probed = []
for i, b in enumerate(bars):
    if guard(b["al"]) or guard(b["txt"]):
        probed.append({**b, "result": "guarded"})
        continue
    # 先按 Esc 关掉上一个
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    before = page.evaluate(SNAP_JS)
    x = b["rect"][0] + b["rect"][2] // 2
    y = b["rect"][1] + b["rect"][3] // 2
    # ⚠️ 点之前先验落点（843 同病：点坐标前必须 elementFromPoint 验落点）
    hit = page.evaluate("""([x, y]) => {
      const t = document.elementFromPoint(x, y);
      return t ? t.tagName + '/' +
        ((t.getAttribute('aria-label') ||
          (t.className || '').toString().slice(0, 30) || '')) : 'null';
    }""", [x, y])
    page.mouse.click(x, y)
    page.wait_for_timeout(1200)
    new = diff_layers(before, page.evaluate(SNAP_JS))
    if not new:
        print(f"  [{i:>2}] al={b['al']!r:<16} ⇒ 没开出新层（{hit}）")
        probed.append({**b, "result": "no_new_layer", "hit": hit})
        continue
    layer = sorted(new, key=lambda z: -(z["w"] * z["h"]))[0]
    inside = page.evaluate(INSIDE_JS,
                            [layer["x"], layer["y"], layer["w"], layer["h"]])
    print(f"  [{i:>2}] al={b['al']!r:<16} ⇒ {layer['w']}×{layer['h']} "
          f"role={layer['role']!r} tid={layer['tid']!r}")
    print(f"       里面写着: {inside[:12]}")
    probed.append({**b, "result": "opened", "hit": hit, "layer": layer,
                   "inside": inside})
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    page.evaluate(UNMARK_JS)

out["probed"] = probed

# 有没有哪个开出的层里写着「历史」/「生成记录」
hits = [p for p in probed if p.get("result") == "opened"
        and any("历史" in s or "记录" in s for s in p.get("inside", []))]
print(f"\n== 开出层里含「历史/记录」的 launcher: {len(hits)} 个 ==")
for h in hits:
    print(f"   al={h['al']!r} rect={h['rect']} "
          f"⇒ {[s for s in h['inside'] if '历史' in s or '记录' in s][:5]}")
out["history_hits"] = [h["al"] for h in hits]

with open("/tmp/b855-topbar-recon.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\n== 已写 /tmp/b855-topbar-recon.json ==")
