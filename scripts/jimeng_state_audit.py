"""jimeng 交互态死按钮普查 —— 每个元素**重新进入该状态**再点。

batch 807/808 两轮普查的教训都落在这个脚本的设计上：

1. **disabled 不是死按钮**（batch 808）。源站「新建会话」aria-disabled=true，
   复刻粘贴/重做/撤销在无可撤销内容时 disabled —— 点了没反应是对的。
   枚举时直接跳过 disabled/aria-disabled/data-disabled。

2. **状态是被点击销毁的**（batch 809 v1 的教训）。右键菜单一点就关、
   AI 抽屉一点就开。"枚举一次然后逐个点"会让后面那些点击全打在画布上，
   产出一片假死按钮（v1 误报 保存到主体库/下载/删除，实测都是活的）。
   所以每个元素前都重新载入并重新进入该状态。

3. 只审**该状态自己引入的元素**（菜单项、抽屉内控件），不审全页 ——
   全页元素是基线，普查它们是 batch 807 的活。

用法: ~/.venvs/liblib-harness/bin/python scripts/jimeng_state_audit.py
"""
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
READY = '[data-testid="canvas-top-bar"]'

FP = """()=>JSON.stringify({
 vp:document.querySelector('.react-flow__viewport')?.style.transform||'',
 sel:Array.from(document.querySelectorAll('.react-flow__node.selected')).map(n=>n.getAttribute('data-id')).join(','),
 nodes:Array.from(document.querySelectorAll('.react-flow__node')).map(n=>n.className.replace(/\\s+/g,' ')).join('|'),
 tids:Array.from(document.querySelectorAll('[data-testid]')).map(e=>e.getAttribute('data-testid')).sort().join(','),
 aria:Array.from(document.querySelectorAll('[aria-label]')).map(e=>e.getAttribute('aria-label')+'='+e.className).sort().join('~'),
 layers:Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=status],input,textarea'))
   .map(d=>(d.getAttribute('data-testid')||d.getAttribute('aria-label')||d.tagName)+':'+(d.innerText||d.value||'').slice(0,30)).join('~'),
 text:document.body.innerText.replace(/\\s+/g,' ')})"""

# 只取该态容器内的可点元素；跳过 disabled
LIST_IN = """(scopeSel) => {
  const scope = document.querySelector(scopeSel) || document.body;
  return Array.from(scope.querySelectorAll('button,[role=button],[role=menuitem]')).map(el => {
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return null;
    if (el.disabled === true || el.getAttribute('aria-disabled') === 'true'
        || el.getAttribute('data-disabled') === 'true') return null;
    return {key:(el.getAttribute('aria-label')||el.innerText||'').trim().replace(/\\s+/g,' ').slice(0,24),
            x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)};
  }).filter(Boolean);
}"""


def ready(page, tries=6):
    """dev server 会被并行会话反复重启，导航失败就重试。"""
    for i in range(tries):
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector(READY, timeout=25000)
            page.wait_for_timeout(400)
            return True
        except Exception:
            page.wait_for_timeout(2500)
    return False


# 只列**尚未审过**的态。审过并修完的删掉，避免每次重跑都撞 dev server 重启。
# 全部审完后这里会是空的 —— 那本身就是"交互态已普查完"的标志。
# Batch 813 补的一整类：**插入后才出现**的节点内部控件。
# 807 加了时间线/主体/导演台三个节点类型，但普查从没进过"插入之后"这个态 ——
# 于是那三个节点里的死按钮（下载/全屏编辑/静音/编辑主体）一个都没被发现。
# 「默认视图 + 既有交互态」覆盖不到"运行时才长出来的界面"。
def _enter_rail(rail: str, tid: str):
    def go(pg):
        pg.reload(wait_until="domcontentloaded")
        pg.wait_for_selector(READY, timeout=25000)
        pg.wait_for_timeout(400)
        pg.locator(f'[aria-label="{rail}"]').first.click()
        pg.wait_for_selector(f'[data-testid="{tid}"]', timeout=15000)
        pg.wait_for_timeout(400)
    return go


def _node_inner(pg, tid: str) -> str:
    return tid


STATES = {
    "节点右键菜单": ("[role=menu]", lambda pg: pg.mouse.click(640, 323, button="right"), "[role=menu]"),
    "时间线节点内部": ('[data-testid="timeline-node"]',
                _enter_rail("时间线", "timeline-node"), '[data-testid="timeline-node"]'),
    "主体节点内部": ('[data-testid="subject-node"]',
               _enter_rail("主体", "subject-node"), "[data-testid=\"subject-node\"]"),
    "导演台节点内部": ('[data-testid="director-node"]',
                _enter_rail("导演台", "director-node"), "[data-testid=\"director-node\"]"),
}


def main() -> int:
    total_dead = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, (scope, enter, inner) in STATES.items():
            ctx = browser.new_context(viewport={"width": 1680, "height": 826}, locale="zh-CN")
            page = ctx.new_page()
            if not ready(page):
                print(f"== {name}: dev server 不可达，跳过")
                ctx.close()
                continue
            enter(page)
            page.wait_for_selector(scope, timeout=15000)
            page.wait_for_timeout(300)
            items = page.evaluate(LIST_IN, scope)
            dead = []
            for it in items:
                if not ready(page):
                    print(f"== {name}: 中途 dev server 断开，剩余项未审")
                    break
                enter(page)
                page.wait_for_selector(inner, timeout=15000)
                page.wait_for_timeout(300)
                before = page.evaluate(FP)
                try:
                    page.mouse.click(it["x"], it["y"])
                    page.wait_for_timeout(500)
                    after = page.evaluate(FP)
                except Exception:
                    continue
                if before == after:
                    dead.append(it["key"])
            total_dead += len(dead)
            print(f"== {name}: {len(items)} 项, 判为死 {len(dead)}")
            for d in dead:
                print(f"     DEAD {d!r}")
            ctx.close()
        browser.close()
    print(f"\n交互态真死按钮合计: {total_dead}")
    return 1 if total_dead else 0


if __name__ == "__main__":
    sys.exit(main())
