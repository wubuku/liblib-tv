"""jimeng 画布**死按钮普查** —— 找出「点了什么都不发生」的可点元素。

背景 (batch 805)：batch 794~803 逐个控件把顶栏接成了真交互，但没有系统性
手段证明「没有漏网的死按钮」。本脚本把这件事变成可重复的体检。

判据不是「元素存不存在」，而是**点击前后页面可观测状态是否变化**：
选中节点、视口 transform、浮层/输入框集合、body 文案、媒体播放态。

用法:
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_dead_button_audit.py
    SNAP_URL=... SNAP_OUT=/tmp/x.json 换页面/输出路径

## 已知的良性命中（不是缺陷，别去"修"）

第一版 fingerprint 太窄，产出过 4 类假阳性，人工复核后确认如下：

| 元素 | 为什么会漏判 |
|---|---|
| 视频卡的 播放/底部播放/取消静音/全屏 | 改的是播放进度与 aria-label，第一版只比 body 文案前 N 字，时间码在很后面 |
| `header[canvas-top-bar]` 等**容器** | 容器本身没有交互语义，点空白处本就不该有反应 |
| `div[rf__node-*]` 节点外框 | 点在节点内部控件的坐标上，事件被子元素吃掉 |

第二版 fingerprint 已覆盖前两类（媒体态 + 自身 aria-label + 全文长度），
容器类命中用 `KNOWN_BENIGN` 显式列出，不再混进缺陷结论。
"""

import json
import os
import sys

from playwright.sync_api import Error, sync_playwright

URL = os.environ.get("SNAP_URL", "http://localhost:4317/jimeng/canvas/demo")
OUT = os.environ.get("SNAP_OUT", "/tmp/jimeng-dead-buttons.json")
VIEWPORT = {"width": 1680, "height": 826}

# 纯容器 / 语义上就不该有反应的命中
KNOWN_BENIGN = {
    "canvas-top-bar": "顶栏容器本身，点空白不反应是对的",
    "topbar-left": "左簇容器",
    "topbar-right": "右簇容器",
    "canvas-fixed-toolbar": "工具栏容器",
}

# 探针**无法验证**（不是"没反应"，是判据伸不到那里）。单列出来，
# 别混进 dead 结论 —— 混进去等于谎报覆盖率。
UNVERIFIABLE = {
    "上传": "点了会打开系统文件选择器，无头环境无法完成选择，没有可观测后果",
    # 以下两条都**人工复核过是活的**，记在这里是为了让工具不反复报它们，
    # 每条都附了复核方法，不是"猜它应该是活的"。
    "选择工具": "已是当前激活工具（点前 class 就带 bg-white/10），点它正确地什么都不该变；"
                "复核：点别的工具把它切走后再点它，class 会变",
    # 批 820：账号菜单里的两项**外链**。点击的真实后果是开新标签页，
    # 本普查的指纹只看**当前页**，看不见新页 → 判据伸不到那里，不是"没反应"。
    # 这两项另有 verify-jimeng-batch820.py 用打桩 window.open 断言 URL 逐字一致。
    "使用手册": "外链，真实后果是开新标签页；见 verify-jimeng-batch820.py 2.1",
    "即梦CLI": "外链，真实后果是开新标签页；见 verify-jimeng-batch820.py 4.1",
    "与 AI 对话": "活的。单独跑 wait=300ms 时 data-testid 集合发生变化；"
                  "审计循环里报它是因为前一轮自己把 AI 抽屉打开了，"
                  "抽屉(x1268-1668)正好盖住按钮(x1549-1667)，后续点击打在抽屉上",
}

LIST_JS = """() => {
  const sel = 'button,[role=button],[role=menuitem],[role=tab],[data-testid]';
  const out = [];
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    if (el.closest('[aria-hidden="true"]')) continue;
    // 祖先里有别的可点元素时，点它大概率被子元素接管
    if (el.parentElement && el.parentElement.closest('button,[role=button]')) continue;
    // Batch 808: 正确禁用的按钮不是死按钮。源站的「新建会话」就带
    // aria-disabled=true（还没有会话可新建），复刻的「粘贴/重做/撤销」
    // 在无可撤销操作时也是 disabled —— 点了没反应是**对的**。
    // 不过滤就会把「设计如此」报成「没接交互」。
    const disabled = el.disabled === true
      || el.getAttribute('aria-disabled') === 'true'
      || el.getAttribute('data-disabled') === 'true';
    if (disabled) continue;
    out.push({
      tag: el.tagName.toLowerCase(),
      // 批 820: 采集 href —— 锚点的后果是整页导航，判"死"之前要先分清
      // "点了没反应" 与 "点了在导航但指纹窗口内还没换"。
      href: el.getAttribute('href') || '',
      tid: el.getAttribute('data-testid') || '',
      al: (el.getAttribute('aria-label') || '').slice(0, 30),
      text: (el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 20),
      x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      w: Math.round(r.width), h: Math.round(r.height),
    });
  }
  return out;
}"""

FINGERPRINT_JS = """() => {
  const vids = Array.from(document.querySelectorAll('video'))
    .map(v => (v.paused ? 'p' : 'PLAY') + ':' + v.currentTime.toFixed(2) + ':' + v.muted).join(',');
  const view = document.querySelector('.react-flow__viewport');
  return JSON.stringify({
    url: location.pathname,
    vids,
    vp: view ? view.style.transform : '',
    sel: Array.from(document.querySelectorAll('.react-flow__node.selected'))
      .map(n => n.getAttribute('data-id')).join(','),
    // 节点数与节点类型：左栏"插入节点"类按钮的唯一可观测后果
    nodes: Array.from(document.querySelectorAll('.react-flow__node'))
      .map(n => n.className.replace(/\\s+/g, ' ')).join('|'),
    // 浮层/输入框集合
    layers: Array.from(
      document.querySelectorAll('[role=dialog],[role=menu],[role=status],[role=tooltip],input,textarea')
    ).map(d => (d.getAttribute('data-testid') || d.getAttribute('aria-label') || d.tagName)
      + ':' + (d.innerText || d.value || '').slice(0, 24)).join('~'),
    // 挂载了什么：抽屉/小地图/面板都带 data-testid，统计它比逐个 selector 稳
    tids: Array.from(document.querySelectorAll('[data-testid]'))
      .map(e => e.getAttribute('data-testid')).sort().join(','),
    // 自身可访问名/类名：toggle 类按钮只改 class 或 aria-label
    aria: Array.from(document.querySelectorAll('[aria-label]'))
      .map(e => e.getAttribute('aria-label') + '=' + e.className).sort().join('~'),
    // 全文（不截断）：媒体时间码这类变化常出现在很靠后的位置
    text: document.body.innerText.replace(/\\s+/g, ' '),
  });
}"""


# 批 820：**浮层类界面也得进普查**。此前只扫基础态，于是顶栏账号菜单里的
# 4 个真死按钮一个都没被抓到 —— 它们在基础态里根本不存在（要点开用户菜单
# 才渲染）。这与批 813「普查漏了运行时才长出来的界面」是同一个根，只是这次
# 漏的是**顶栏浮层**而不是节点内部。
# 第三项是"进入该态要跳过的元素"：态的**触发器**本身不参与本态扫描。
# 否则点它只会把刚打开的浮层又关掉 —— 判成 DEAD 是必然的假阳性，而它的
# 行为其实已经被"进入该态"这一步验证过了。
STATES: list[tuple[str, object, set[str]]] = [
    ("base", None, set()),
    ("account-menu",
     'page.locator(\'button[aria-label="用户菜单"]\').click(); page.wait_for_timeout(600)',
     {"canvas-user-menu-trigger"}),
]


def enter_state(page, code) -> None:
    if code:
        exec(code, {"page": page})  # noqa: S102 - 普查脚本内部固定字面量，非外部输入


def main() -> int:
    hits: list[dict] = []
    scanned = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, locale="zh-CN")
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        for state_name, enter, skip_tids in STATES:
          if state_name != "base":
            # 批 820: 换态前**重新加载页面**。此前各态共用一个 page，基础态扫描
            # 里点开的 AI 抽屉会带到下一个态，于是 account-menu 态里混进了抽屉
            # 的元素，canvas-agent-mode-action 被判 DEAD —— 假阳性：它接的是
            # addSkill(chip)（批 810 已验 39/39 是活的）。这与 UNVERIFIABLE 里
            # 记的「与 AI 对话」是同一处污染。
            page.goto(URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            enter_state(page, enter)
          items = [i for i in page.evaluate(LIST_JS) if i["tid"] not in skip_tids]
          scanned += len(items)
          for it in items:
            before = page.evaluate(FINGERPRINT_JS)
            try:
                page.mouse.click(it["x"], it["y"])
                # 220ms 不够：AI 抽屉这类带挂载过渡的面层在 220ms 时还没进 DOM，
                # 会被误判成死按钮（实测 400ms 才稳定）。
                page.wait_for_timeout(420)
            except Exception as exc:  # noqa: BLE001
                hits.append({**it, "verdict": "click-error", "detail": str(exc)[:90], "state": state_name})
                continue
            try:
                after = page.evaluate(FINGERPRINT_JS)
            except Error as exc:
                # 点了之后上下文被销毁 = 真的发生了整页导航。导航**就是**状态变化，
                # 不能因为 evaluate 报错就误判成死按钮（返回首页就是这种）。
                if "destroyed" in str(exc) or "navigat" in str(exc).lower():
                    hits.append({**it, "verdict": "NAVIGATED", "state": state_name})
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(800)
                    continue
                hits.append({**it, "verdict": "eval-error", "detail": str(exc)[:90], "state": state_name})
                continue
            if before == after:
                # 批 820: 锚点是**整页导航**。420ms 的指纹窗口内页面往往还没换，
                # 于是被判成"没反应"—— canvas-project-logo（<a href="/jimeng">，
                # 批 807 改的）就是这么被误判的。导航本身就是状态变化，
                # 所以对带 href 的锚点多等一轮再判。
                is_anchor = it.get("tag") == "a" and it.get("href")
                if is_anchor:
                    page.wait_for_timeout(1500)
                    try:
                        after2 = page.evaluate(FINGERPRINT_JS)
                        if after2 != before or page.url != it.get("url_before", page.url):
                            hits.append({**it, "verdict": "NAVIGATED", "state": state_name})
                            page.wait_for_load_state("domcontentloaded")
                            page.wait_for_timeout(800)
                            if state_name != "base":
                                page.goto(URL, wait_until="domcontentloaded")
                                page.wait_for_timeout(2000)
                                enter_state(page, enter)
                            continue
                    except Error as exc2:
                        if "destroyed" in str(exc2) or "navigat" in str(exc2).lower():
                            hits.append({**it, "verdict": "NAVIGATED", "state": state_name})
                            page.wait_for_load_state("domcontentloaded")
                            page.wait_for_timeout(800)
                            if state_name != "base":
                                page.goto(URL, wait_until="domcontentloaded")
                                page.wait_for_timeout(2000)
                                enter_state(page, enter)
                            continue
                hits.append({**it, "verdict": "DEAD", "state": state_name})
            # 复位：关浮层 + 点画布空白收起各类选择态
            page.keyboard.press("Escape")
            page.wait_for_timeout(90)
            page.mouse.click(20, 700)
            page.wait_for_timeout(90)
            # 批 820: 非基础态必须**重新进入**该态 —— 上面的复位把菜单关掉了，
            # 不重进的话后续项拿着旧坐标去点画布空白，全被判成 DEAD。
            if state_name != "base":
                enter_state(page, enter)
        ctx.close()
        browser.close()

    benign, unverifiable, dead = [], [], []
    for h in hits:
        if h["tid"] in KNOWN_BENIGN:
            benign.append(h)
        elif h.get("al") in UNVERIFIABLE or h.get("text") in UNVERIFIABLE:
            unverifiable.append(h)
        else:
            dead.append(h)
    # 容器/祖先类的其余命中：祖先已是可点元素时不单独算缺陷
    real_dead = [h for h in dead if h["tag"] in ("button", "a")]

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"scanned": scanned, "hits": hits}, f, ensure_ascii=False, indent=1)

    print(f"可点元素 {scanned} 个；无响应 {len(hits)} 个"
          f"（良性容器 {len(benign)}，探针无法验证 {len(unverifiable)}，"
          f"真死按钮 {len(real_dead)}）")
    for h in unverifiable:
        print(f"  ?? 探针无法验证 al={h['al']!r} — {UNVERIFIABLE.get(h['al']) or UNVERIFIABLE.get(h['text'])}")
    for h in real_dead:
        print(f"  DEAD  <{h['tag']}> al={h['al']!r} text={h['text']!r} "
              f"tid={h['tid'] or '-'} @{h['x']},{h['y']}")
    for h in dead:
        if h not in real_dead:
            print(f"  (容器/代理命中，不算缺陷) tid={h['tid'] or '-'} text={h['text']!r}")
    print(f"明细已写入 {OUT}")
    return 1 if real_dead else 0


if __name__ == "__main__":
    sys.exit(main())
