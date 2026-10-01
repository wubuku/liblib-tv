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
    # 批 821: 上面这份清单**漏登记**了本轮新扫到的 4 个浮层容器与 3 个非交互
    # 文本/输入节点。此前它们只是被 real_dead 的 `tag in (button,a)` 兜住没
    # 进缺陷结论，但仍会以 DEAD 打印出来 —— 于是"容器"和"死按钮"两种结论
    # 在同一份输出里混着，读的人得自己再判一次。清单既然声称显式列出，就补齐。
    "topbar-share-panel": "分享面板容器（role=dialog），点它自己的留白不反应是对的",
    "topbar-more-menu": "更多菜单容器，真正的两项是里面的 button",
    "jimeng-search-overlay": "搜索浮层容器，点留白不反应是对的",
    "jimeng-search-input": "搜索输入框本身，点击不改变状态（输入才有）",
    "search-empty": "空态文案 <p>，不是控件",
    "topbar-saved-status": "「已保存」状态文本 <span>，不是控件",
    "tool-rail-separator": "工具栏分隔线 div",
    "node-title-text": "节点标题文本 span，点它只是选中节点，判定要看 .selected",
    # 批 827：批 826 补上了 `data-testid="canvas-user-menu"`，于是它**第一次**
    # 有资格被登记。批 826 的 README 里写过一句"没有 testid，它连被正确归档的
    # 资格都没有" —— 现在有了，就登记上去，别让良性容器继续混在 DEAD 输出里。
    "canvas-user-menu": "账号菜单容器，真正的六项是里面的 [role=menuitem]",
    # 批 835：这三枚一直落在「容器/代理命中」桶里，靠读者自己再判一次。
    # 批 821 立的规矩是「清单既然声称显式列出，就补齐」——补上，桶就空了。
    "topbar-history-menu": "生成历史浮层容器（role 菜单），真正的筛选项是里面的 chip",
    "share-link-pill": "分享面板里的链接展示块，点它不改变状态是对的（复制是另一条路径）",
    "canvas-share-scope-action": "分享面板里的「创建团队」说明块容器，按钮在里面",
}

# 探针**无法验证**（不是"没反应"，是判据伸不到那里）。单列出来，
# 别混进 dead 结论 —— 混进去等于谎报覆盖率。
UNVERIFIABLE = {
    "上传": "点了会打开系统文件选择器，无头环境无法完成选择，没有可观测后果",
    # 以下两条都**人工复核过是活的**，记在这里是为了让工具不反复报它们，
    # 每条都附了复核方法，不是"猜它应该是活的"。
    # 批 837：删掉「选择工具」这条豁免 —— 它的理由是**探针够不着**，不是产品行为。
    #   命中测试实测：dock 最左那枚钮 @[16,778,28,28]，center(30,792) 的命中元素
    #   是 NEXTJS-PORTAL（Next dev 指示器，自身 rect 0×0，但 shadow 内容盖住那个点）。
    #   本文件按坐标 `page.mouse.click` 点，于是事件投给了指示器，指纹当然不变
    #   —— 于是被判 DEAD，再被写成「点它正确地什么都不该变」。**那句话描述的是
    #   探针的失败，不是产品。**
    #   两处一起修才算修完：
    #     ① 产品（批 837）：那枚钮的 onClick 此前是 `setToolActive("select")`
    #        —— 强制置位，已经是 select 时点它真的什么都不发生。改成 toggle，
    #        并与 V 快捷键共用 store 里那一条 `toggleToolActive`。
    #     ② 量具：每项点击前摘掉 dev portal（`clear_dev_portal`）。
    #   重跑：265 扫 / 无响应 15 / **真死按钮 0**，「选择工具」**不再**出现在
    #   不可验证清单里（只剩 上传 / 全部 两条，都有复核方法）。
    #   留着它会有同一个坏处：将来这枚钮真的坏了，会被静默归进「无法验证」。
    # 批 827：把"外链 = 探针无法验证"这条**撤回**（批 820 的「使用手册」「即梦CLI」，
    # 以及批 826 照着同一措辞补的「新功能许愿」，三条一并移除）。
    #
    # 批 820 当时的理由是"真实后果是开新标签页，指纹只看当前页看不见"。
    # **这条理由是错的。** 复现普查的点击与指纹（2026-10-04）实测：
    #     使用手册    指纹变化=True 差异字段=[layers,btn,tids,text] 菜单已关=True
    #     即梦CLI     指纹变化=True 差异字段=[layers,btn,tids,text] 菜单已关=True
    #     新功能许愿  指纹变化=True 差异字段=[layers,btn,tids,text] 菜单已关=True
    # 它们点完都会**关掉菜单**，菜单一关 tids / text / layers 三处同时变 ——
    # 普查**看得见**。所以它们既不需要豁免，也从来不是死按钮。
    # 外链的 URL 另有 verify-jimeng-batch820/826.py 用打桩 window.open 断言。
    #
    # 教训比结论重要：**照抄上一批的结论不构成证据。** 批 826 是照抄批 820 的
    # 措辞写的，而批 820 那句话当时也没验过。豁免清单是判据里最容易腐烂的
    # 部分 —— 一条写错理由的豁免，会让真正的死按钮永远查不出来，且无人察觉。
    # verify-jimeng-batch827.py A.4 现在反过来**正面断言**这三枚会被检出。
    #
    # 批 835：删掉「与 AI 对话」这条豁免 —— 它是**过期**的，而且过期的理由最贵。
    #   当初的理由（"前一轮自己把 AI 抽屉打开了，抽屉正好盖住按钮"）诊断对了
    #   现象，却把原因归给了产品。其实那是**普查自己的状态污染**：复位没关抽屉
    #   （批 381 早记过 Escape 对这个面板无效），于是后面每一项的点击都打在
    #   抽屉上。修的是复位（显式点「收起」），不是产品。
    #   修完重跑：265 扫 / 17 无响应 / **真死按钮 0**，「与 AI 对话」**不再**
    #   出现在「探针无法验证」里 —— 它被正确认成**活的**（点开抽屉 ⇒ 指纹变化）。
    #   留着这条豁免会有两个坏处：① 理由已经不准；② 将来这枚钮**真的**坏了，
    #   它会被静默归进「无法验证」，而清单声称穷尽 —— 又一次无人察觉。
    #   顺带更正本轮我自己的前提：我一度以为「面板开着时点它是死交互」，
    #   源站四刀实测 + 截图证明不是（复刻在面板打开时**卸载**这枚钮）。
    # 批 821: 一组切换项里**永远有一个已经是激活态**，点它正确地什么都不该变 ——
    # 和上面的「选择工具」是同一类，不是指纹不够宽。生成历史进态时默认停在
    # 「全部」，所以四枚 chip 里恰好它被判 DEAD，另外三枚（图片/视频/音频）
    # 因为切得动、被新加的 btn class 指纹正确认成活的。
    # 换句话说：这一条不是"漏网"，是**切换组的固有性质**。
    "全部": "生成历史进态时默认选中「全部」，点它正确地不改变任何状态；"
            "复核：verify-jimeng-batch821.py E.1/E.3 先切到「图片」再点回「全部」，"
            "断言选中 class 真的转移（两向都验过）",
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
    // 批 821: 连线数与小地图是否在场。此前两者都不在指纹里，于是
    // 「小地图」「显示连线」这两个**确实接了**的开关被判 DEAD ——
    // 「我没检测到」不等于「事实如此」。
    edges: Array.from(document.querySelectorAll('.react-flow__edge')).length,
    minimap: document.querySelectorAll('.react-flow__minimap').length,
    // 批 821: 控件**自身**的选中态。有一类按钮点了只改自己的 class / 下划线
    // （生成历史的全部/图片/视频/音频 chip、底dock 的工具切换…），
    // 页面别处毫无变化，指纹就看不出。把每个 button 的 label→class 收进来，
    // 这类"toggle 只改自己"就变成可观测的。
    btn: Array.from(document.querySelectorAll('button'))
      .map(b => ((b.getAttribute('aria-label') || b.innerText || '').trim().slice(0, 16))
                + ':' + (b.className || '').slice(0, 70)).join('|'),
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
    # 批 821: 顶栏其余浮层。账号菜单那 4 个真死按钮被抓出来之后（批 820），
    # 同一类问题必须问一遍：还有哪些顶栏浮层从来没进过普查。
    # 实测几何：更多 200×84 / 搜索 242×95 / 生成历史 380×199 / 分享 400×251。
    ("more-menu",
     'page.locator(\'[aria-label="更多"]\').first.click(); page.wait_for_timeout(600)',
     {"canvas-more-trigger"}),
    ("search",
     'page.locator(\'[aria-label="搜索"]\').first.click(); page.wait_for_timeout(600)',
     {"canvas-panel-launcher"}),
    ("history",
     'page.locator(\'[aria-label="生成历史"]\').first.click(); page.wait_for_timeout(700)',
     {"canvas-history-launcher"}),
    ("share",
     'page.locator(\'[aria-label="分享"]\').first.click(); page.wait_for_timeout(700)',
     {"canvas-share-trigger"}),
]


def enter_state(page, code) -> None:
    if code:
        exec(code, {"page": page})  # noqa: S102 - 普查脚本内部固定字面量，非外部输入


def clear_dev_portal(page) -> None:
    """摘掉 Next.js dev 指示器（**量具**缺陷，不是产品缺陷）。

    批 837 实测：dock 最左那枚「选择工具」@[16,778,28,28]，其中心点的命中元素
    是 NEXTJS-PORTAL（该 portal 自身 rect 是 0×0，但 shadow 里的指示器盖住了
    那个点）。本文件用 `page.mouse.click(x, y)` 按坐标点，于是那一项的点击
    **投给了指示器而不是按钮** —— 指纹当然不变，于是被判 DEAD。
    「选择工具」那条 UNVERIFIABLE 的理由（「点它正确地什么都不该变」）就是这么来的：
    不是产品的行为，是探针够不着。

    `force=True` 救不了（force 只跳过可点性检查，事件仍投给最上层元素）。
    摘掉 portal 才是修量具。生产构建里没有这个 portal。
    """
    try:
        page.evaluate("() => document.querySelector('nextjs-portal')?.remove()")
    except Error:
        pass  # 导航中：下一轮复位会再清一次


def fingerprint(page) -> str:
    """取一次指纹，**导航中重试**。

    批 821: 上一批的普查跑了 20 分钟后整个崩在
        before = page.evaluate(FINGERPRINT_JS)
        Error: Execution context was destroyed, most likely because of a navigation
    根因不是判据，是**防御不对称**：`after` 那次读取包了导航判断（判成
    NAVIGATED 继续跑），`before` 那次没包。前一项的整页导航若还在途中，下一
    项的 before 就正好落在上下文销毁的窗口里 —— 崩掉的是**工具**，不是被测
    页面。一个跑了 20 分钟的体检不该因为一次导航全废，所以 before 也走同一条
    恢复路径：等 load 落定后重取一次。
    """
    for attempt in range(3):
        try:
            return page.evaluate(FINGERPRINT_JS)
        except Error as exc:
            if "destroyed" not in str(exc) and "navigat" not in str(exc).lower():
                raise
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(800 if attempt == 0 else 1500)
    return page.evaluate(FINGERPRINT_JS)


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
            before = fingerprint(page)
            try:
                clear_dev_portal(page)   # 批 837：坐标点击会被 dev 指示器吞掉
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
            # 批 835：复位**漏了 AI 抽屉**，而这是本文件最隐蔽的一处污染。
            # 抽屉 @x1268..1668 正好盖住右下角那枚药丸 @x1549..1667；
            # 批 381 记过 Escape 对这个面板**无效**，所以上面两行永远关不掉它。
            # 于是：某一轮点开抽屉之后的**每一项**，点击都打在抽屉上 ——
            # `canvas-sidecar-launcher` 就是这样被判 DEAD 的，它自己的
            # UNVERIFIABLE 备注写着「前一轮自己把 AI 抽屉打开了」。
            # 一枚**假阳性**混进结论，而清单声称穷尽，读者无从分辨。
            # 修法就一行：点它自己的「收起」钮。复位必须**回到基线态**，
            # 而不是「按了几个键」。
            try:
                if page.locator('[data-testid="canvas-agent-drawer"]').count():
                    page.locator('[data-testid="canvas-agent-session-collapse"]').first.click()
                    page.wait_for_timeout(220)
            except Error as exc4:
                # 复位失败不能吞掉：记一笔，让读者知道这一轮的结论不可信
                hits.append({"tag": "script", "tid": "", "al": "", "text": "",
                             "verdict": "reset-failed", "state": state_name,
                             "detail": f"AI 抽屉没能复位: {str(exc4)[:80]}"})
            # 批 820: 非基础态必须**重新进入**该态 —— 上面的复位把菜单关掉了，
            # 不重进的话后续项拿着旧坐标去点画布空白，全被判成 DEAD。
            # 批 821: 这里也要抗导航。上一项若是整页锚点，导航可能仍在途中，
            # 裸 enter_state 会跟 before 一样崩在同一处。
            if state_name != "base":
                try:
                    enter_state(page, enter)
                except Error as exc3:
                    if "destroyed" not in str(exc3) and "navigat" not in str(exc3).lower():
                        raise
                    page.wait_for_load_state("domcontentloaded")
                    page.goto(URL, wait_until="domcontentloaded")
                    page.wait_for_timeout(2500)
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
    # 批 821: 这里原本**只看 tag 不看 verdict**，于是 verdict=NAVIGATED 的
    # <a> 返回首页也被算进「真死按钮」—— 上一轮输出把两个整页锚点印成
    # `DEAD <a> al='返回首页'`，标题还报「真死按钮 3」。真实死按钮是 0。
    # 一次导航恰恰**就是**状态变化（本文件批 820 注释里就是这么写的），
    # 把它记成缺陷，等于把判据的立论自己扔了。打印那一行同样把 verdict
    # 写死成 "DEAD"，所以光看控制台会被误导 —— 结论与它打印的字不符。
    navigated = [h for h in dead if h.get("verdict") == "NAVIGATED"]
    real_dead = [
        h for h in dead
        if h.get("verdict") == "DEAD" and h["tag"] in ("button", "a")
    ]
    other = [
        h for h in dead
        if h not in real_dead and h not in navigated
    ]

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"scanned": scanned, "hits": hits}, f, ensure_ascii=False, indent=1)

    print(f"可点元素 {scanned} 个；无响应 {len(hits)} 个"
          f"（良性容器 {len(benign)}，探针无法验证 {len(unverifiable)}，"
          f"整页导航 {len(navigated)}，非控件容器 {len(other)}，"
          f"真死按钮 {len(real_dead)}）")
    for h in unverifiable:
        print(f"  ?? 探针无法验证 al={h['al']!r} — {UNVERIFIABLE.get(h['al']) or UNVERIFIABLE.get(h['text'])}")
    for h in real_dead:
        print(f"  DEAD  <{h['tag']}> al={h['al']!r} text={h['text']!r} "
              f"tid={h['tid'] or '-'} @{h['x']},{h['y']} state={h['state']}")
    for h in navigated:
        print(f"  NAV   <{h['tag']}> al={h['al']!r} tid={h['tid'] or '-'} "
              f"@{h['x']},{h['y']} state={h['state']} —— 整页导航，不是死按钮")
    for h in other:
        print(f"  (容器/代理命中，不算缺陷) tid={h['tid'] or '-'} text={h['text']!r} state={h['state']}")
    print(f"明细已写入 {OUT}")
    return 1 if real_dead else 0


if __name__ == "__main__":
    sys.exit(main())
