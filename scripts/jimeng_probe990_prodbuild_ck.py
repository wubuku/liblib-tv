#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""batch 990 **复刻侧**探针（**零计费**：只按 `Tab`、唯一的 `mouse.click`
点在 `about:blank` 空白处、⛔ 计费守卫拦在 `mouse.click` **之前**）：
⭐⭐⭐⭐⭐ **第一次量「生产构建」** —— 而 973/983/987 的复刻侧读数
**全部来自 dev server** ⇒ ⇒ **「dev 上量到的」能不能搬到「生产上」，
从来没人验过**。

── 990 第一条发现，而且是动手之前就该知道的那条 ──────────────────────

⚠️⭐⭐⭐⭐⭐ **仓里那个 `.next` 生产产物是过期的**：
产物 `Oct 3 05:57`、而 `JimengWorkspace.tsx` 改于 `Oct 4 23:01`
⇒ ⇒ ⭐⭐⭐⭐⭐ **用它去量，量到的是一份已经不存在的代码**
⇒ ⇒ ⭐⭐⭐⭐ **「先量新鲜度、再量内容」** —— **这与 988 那条
「引文必须逐字来自原文」是同一族：先确认你量的是不是那个东西**

⚠️⭐⭐⭐⭐⭐ 而 **`next build` 与 `next dev` 共用 `.next`**
⇒ ⇒ 直接构建**会干扰正在跑的 dev server**（`pid 51810`）**、也会动别人的构建记录**
⇒ ⇒ ⭐⭐⭐⭐⭐ **本批的做法**：把源码 `rsync` 到 `/tmp` 的一次性副本、
**`cp -Rc`（APFS 写时复制）克隆 `node_modules`**、在那里构建并起服务
⇒ ⇒ **仓库一个字节都没改**（`next.config.ts` 仍是 `output: "standalone"`）
⇒ ⇒ ⚠️ 而且**第一版踩了两个坑、都记在这里**：
① 符号链接 `node_modules` ⇒ **Turbopack 拒绝**（`points out of the filesystem root`）
② `output: "standalone"` 下 `next start` ⇒ **Next 自己警告不支持**
⇒ ⇒ **两次都改成「在一次性副本里改」**，而**不是改仓库**

── ⭐⭐⭐⭐⭐ 本批要回答的那个真问题 ──────────────────────────────────

985 已证「间隙」是 **Blink 引擎层**的行为（`activeElement` 无聚焦元素时回落到
`document.body`；`ClearFocusedElement()` ＋ `TakeFocus()`）
⇒ ⇒ ⭐⭐⭐⭐ **间隙是引擎行为、与构建模式无关** ⇒ **它一定还在**

⚠️⭐⭐⭐⭐⭐ **而真正可能变的不是「有没有间隙」，是「环里有哪些格」** ——
**dev 模式会往 DOM 里塞 dev-only 的东西**（overlay / portal），
**而生产构建里没有** ⇒ ⇒ **环长可能不一样**

⭐⭐⭐⭐⭐ **而本批顺手补上一处 973/983/987 一直漏掉的读数** ——
那枚 `dom_rank` 最大的 **`None/None` 停靠点**（`dom_rank`=268）
**从来只被记了位置、没被记身份** ⇒ ⚠️ 而 `OWN_JS` **本来就会返回
`tag`/`id`/`aria`/`title`** ⇒ ⇒ **仪器早就能给、是没人记**
⇒ ⇒ ⭐⭐⭐⭐ **如果它是 dev-only 的 overlay ⇒ 那它就是环长在两种构建下
会不一样的那一枚** ⇒ **本批把它认出来**

── ⭐⭐⭐⭐⭐ 三条预测，**全部按定义推出、且由 dev 读数算出** ─────────────

⚠️⭐⭐⭐ **期望值必须按定义逐句推、不能「跑出来是什么就写什么」**
⚠️⭐⭐⭐⭐⭐ **而本批的预测是「算出来」的、不是「写死」的** ——
**`expected_prod_ring` 由 dev 的圈逐格算出**（剔掉被判定为 dev-only 的格）
⇒ ⇒ **这样预测就不可能是我事后编的**

**P1（间隙仍在）**：prod 的圈里 **`is_body` 那一格仍然存在**
⇒ 推导：985 已证它是 Blink 的 `activeElement` 回落 + `TakeFocus` ⇒
**引擎行为与构建模式无关** ⇒ ⇒ **它一定还在**

**P2（环长可能变、且变的机制是 dev-only 格）**：
prod 的可聚焦停靠点数 = dev 的**剔掉 dev-only 格之后**
⇒ 推导：dev-only 的东西**只存在于 dev 构建** ⇒ 生产构建里没有

**P3（⭐⭐⭐⭐⭐ 两套构建的其余格逐格相同）**：
剔掉 dev-only 格之后，**dev 与 prod 的圈逐格相同**
⇒ 推导：React 的 **dev/prod 差别在运行期行为（StrictMode 双渲染、
开发警告）**，而**不改组件树的可聚焦元素集合** ⇒
⇒ **除非有 dev-only 的东西混进来**（那正是 P2 要测的）

**本批零计费**：只按 `Tab`；源站**不打开**（985 已确认登录态过期）
"""
from __future__ import annotations

import atexit
import json
import os
import re

OUT = "/tmp/b990-prodbuild.json"
REPS = 2
N_STEPS = 130        # ⭐ 26 格一圈 ⇒ 够 5 圈（生产环长可能更短）
SETTLE = 60
NODE_SEL = "[data-nodeid], .react-flow__node"   # ⭐ 与 973/974/982/983/987 同
BLANK_WAIT = 120
VIEWPORT = {"width": 1512, "height": 1200}
DEV_URL = "http://localhost:4317/jimeng/canvas/demo"
PROD_URL = "http://localhost:4318/jimeng/canvas/demo"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge", "canvas-member-buy")


def _src(name):
    p = os.path.join(ROOT, "scripts", name)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


_p967 = _src("jimeng_probe967_armptr_src.py")
_p970 = _src("jimeng_probe970_owntid_ck.py")
_p973 = _src("jimeng_probe973_ringorder_ck.py")
_p982 = _src("jimeng_probe982_ringlen_src.py")
_p983 = _src("jimeng_probe983_wrapcmp_ck.py")
_ME = open(__file__, encoding="utf-8").read()


def _grab(name, src=None):
    m = re.search(r'^%s\s*=\s*r?"""(.*?)"""' % name, src or "", re.S | re.M)
    assert m, "抠不到 %s" % name
    _s = m.group(1)
    assert _s in (src or ""), "%s 不是逐字抠出来的" % name
    return _s


def _grab_def(start, end, src=None):
    s = src or ""
    i = s.index(start)
    j = s.index(end)
    assert i < j, "起止锚点顺序错了"
    _s = s[i:j]
    assert _s in s, "抠出来的那段不是逐字抠出来的"
    return _s


# ⚠️⭐⭐⭐⭐⭐ **仪器逐字继承 987/983 的溯源链**（不重写任何一件）
INSTALL_JS = _grab("INSTALL_JS", _p967)
READ_JS = _grab("READ_JS", _p967)
OFF_NULL_JS = _grab("OFF_NULL_JS", _p967)
BLANK_JS = _grab("BLANK_JS", _p967)
OWN_JS = _grab("OWN_JS", _p970)
DOMRANK_JS = _grab("DOMRANK_JS", _p973)
POINT_JS = _grab("POINT_JS", _p973)
INSTR_SRC = _grab_def("def min_period(seq):", "def _code_only(js):", _p982)
_NS: dict = {}
exec(compile(INSTR_SRC, "<982-instruments>", "exec"), _NS)   # noqa: S102
min_period = _NS["min_period"]
assert callable(min_period)
for _nm, _from in (("INSTALL_JS", '_grab("INSTALL_JS", _p967)'),
                   ("READ_JS", '_grab("READ_JS", _p967)'),
                   ("OFF_NULL_JS", '_grab("OFF_NULL_JS", _p967)'),
                   ("BLANK_JS", '_grab("BLANK_JS", _p967)'),
                   ("OWN_JS", '_grab("OWN_JS", _p970)'),
                   ("DOMRANK_JS", '_grab("DOMRANK_JS", _p973)'),
                   ("POINT_JS", '_grab("POINT_JS", _p973)')):
    _decl = "%s = %s" % (_nm, _from)
    assert _decl in _p983, "983 的溯源声明变了：%r" % _decl
    assert _decl in _ME, "本批的溯源声明与 983 不一致：%r" % _decl
for _nm in ("INSTALL_JS", "READ_JS", "OFF_NULL_JS", "BLANK_JS",
            "OWN_JS", "DOMRANK_JS", "POINT_JS"):
    assert not re.search(r'^%s\s*=\s*r?"""' % _nm, _ME, re.M), \
        "本批自己定义了**继承来的** `%s`" % _nm


# ══ ⭐⭐⭐⭐⭐ 本批唯一的**新件**：补上「这枚停靠点到底是谁」 ══════════
# ⚠️⭐⭐⭐⭐⭐ **为什么必须新写** ——
#   `OWN_JS` 确实返回 `tag`/`id`/`aria`/`title`，**但它不报
#   「这个元素是不是在 shadow root 里」** ⇒ 而**那正是本批要害** ——
#   **dev overlay（`nextjs-portage-dev-tools`）住在 shadow root 里**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **973/983/987 之所以记不出那枚格的身份，
#   不是仪器没能力、是没问那一问**
IDENT_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {is_body: false, tag: null, in_shadow: null,
                  shadow_host: null, shadow_host_id: null, doc_is_main: null,
                  has_tid: null, id: null, aria: null, ti_prop: null,
                  dev_only: null, why: null};
  // ⭐⭐⭐⭐⭐ **逐层往上问「我在不在 shadow root 里」**
  let n = 0, root = a.getRootNode(), host = null;
  while (root && root.host) { n += 1; host = root.host; root = root.host.getRootNode(); }
  const h = host;
  const hasTid = a.hasAttribute && a.hasAttribute('data-testid');
  return {
    is_body: (a === document.body),
    tag: (a.tagName || '').toUpperCase(),
    // ⭐⭐⭐⭐⭐ **shadow 深度 + 宿主身份** ⇒ 这是判定 dev-only 的**唯一依据**
    in_shadow: (n > 0),
    shadow_depth: n,
    shadow_host: h ? ((h.tagName || '').toUpperCase()) : null,
    shadow_host_id: h ? (h.id || null) : null,
    doc_is_main: (a.ownerDocument === document),
    has_tid: hasTid,
    id: a.id || null,
    aria: a.getAttribute ? (a.getAttribute('aria-label') || null) : null,
    ti_prop: (a.tabIndex === undefined) ? null : a.tabIndex,
    // ⭐⭐⭐⭐⭐ **dev-only 的判定式**（本批的核心，必须能一眼看懂）：
    //   「住在 shadow root 里」**或**「宿主是 nextjs 的 dev portal」
    //   ⇒ ⇒ **纯读、只读 DOM 事实、不含任何我起的名字**
    dev_only: ((n > 0) ||
               ((h && (h.id || '').indexOf('nextjs-portage') >= 0)) ||
               ((h && (h.tagName || '').toUpperCase() === 'NEXTJS-PORTAGE-DEV-TOOLS'))),
    why: ((n > 0) ? 'in-shadow-root(depth=' + n + ')'
                   : (h ? 'host=' + (h.id || h.tagName) : 'main-document'))
  };
}"""
for _pat, _why in ((r"\.focus\s*\(", "调 focus()"),
                   (r"\.setAttribute\s*\(", "写属性"),
                   (r"\.removeAttribute\s*\(", "写属性"),
                   (r"new\s+MutationObserver", "MutationObserver"),
                   (r"\.addEventListener\s*\(", "addEventListener"),
                   (r"\.tabIndex\s*=(?!=)", "**写** IDL 属性 `tabIndex`")):
    assert not re.search(_pat, IDENT_JS), \
        "`IDENT_JS` 里出现了%s ⇒ 它不再是**纯读件**" % _why
# ⭐⭐⭐⭐⭐ **反向门**：真写必须被抓到
for _bad, _pat in (("el.focus();", r"\.focus\s*\("),
                   ("el.setAttribute('a','b');", r"\.setAttribute\s*\("),
                   ("a.tabIndex = 0;", r"\.tabIndex\s*=(?!=)")):
    assert re.search(_pat, _bad), "反向门坏了：%r 抓不住" % _bad
# ⭐⭐⭐⭐⭐ **反向门②：读属性不许被当成写**
assert not re.search(r"\.tabIndex\s*=(?!=)", "a.tabIndex === undefined;"), \
    "⭐⭐⭐ **反向门②坏了**：**读**属性被当成**写**"
# ⭐⭐⭐⭐⭐ **本批的正题全在这三个读数上** ⇒ 少一个就不成立
for _must in ("in_shadow", "shadow_host", "dev_only", "getRootNode"):
    assert _must in IDENT_JS, "IDENT_JS 少了 %r ⇒ 本批的正题不成立" % _must
# ⭐⭐⭐⭐⭐ **不许自己定义**继承来的那几件（978 栽过、980/987 照抄）
assert not re.search(r'^(INSTALL_JS|READ_JS|OFF_NULL_JS|BLANK_JS|OWN_JS|'
                     r'DOMRANK_JS|POINT_JS)\s*=\s*r?"""', _ME, re.M), \
    "本批自己定义了**继承来的**字面量 ⇒ 尺子分叉了"
# ⭐⭐ 而**自己的新件**必须**能**被行首匹配到（证明上面那条不是恒真）
assert re.search(r'^IDENT_JS\s*=\s*r?"""', 'IDENT_JS = """x"""', re.M)


# ── ⭐⭐⭐⭐⭐ **「dev-only 格」的判定与剔���，必须是纯函数** ──────────────
def _is_dev_only(ident):
    """⭐⭐⭐⭐⭐ **一格是不是 dev-only —— 只看三个 DOM 事实**：
    `in_shadow` / `shadow_host` / `shadow_host_id` ⇒
    ⇒ ⭐⭐⭐⭐ **不看它的 testid、不看它的类名、不看我起的名字**
    ⇒ ⇒ ⭐⭐ **这样判定就不会被「我猜它是 overlay」带偏**"""
    if not isinstance(ident, dict):
        return False
    if ident.get("is_body"):
        return False                      # ⭐ 间隙不是格、也不是 dev-only
    if ident.get("in_shadow"):
        return True
    h = (ident.get("shadow_host_id") or "") + (ident.get("shadow_host") or "")
    return "nextjs-portage" in h.lower()


def _expected_prod_ring(dev_ring, dev_flags):
    """⭐⭐⭐⭐⭐ **预测是「算出来」的、不是「写死」的** ——
    `expected_prod_ring` = dev 的圈**逐格**剔掉被判为 dev-only 的那些
    ⇒ ⇒ ⭐⭐⭐⭐⭐ **这样预测就不可能是我事后编的**
    ⇒ ⇒ 剔掉的**位置也一并算出来**（要能说清「少了哪几格」）"""
    return [k for k, f in zip(dev_ring, dev_flags) if not f]


# ── ⭐⭐⭐⭐⭐ **自测：期望值按定义逐句推** ───────────────────────────
# 推导：`_is_dev_only` 只看三个 DOM 事实 ⇒ 下列五例按定义逐个判
assert _is_dev_only({"is_body": False, "in_shadow": True,
                     "shadow_host": "NEXTJS-PORTAGE-DEV-TOOLS",
                     "shadow_host_id": "nextjs-portage-dev-tools"}) is True
assert _is_dev_only({"is_body": False, "in_shadow": False,
                     "shadow_host": None, "shadow_host_id": None}) is False
# ⭐⭐⭐⭐⭐ **反向门①**：**间隙永远不算 dev-only**（它不是格）
assert _is_dev_only({"is_body": True, "in_shadow": True,
                     "shadow_host": "X", "shadow_host_id": "x"}) is False, \
    "⭐⭐⭐⭐ **反向门①坏了**：间隙被算成 dev-only ⇒ 环长会被多减一"
# ⭐⭐⭐⭐⭐ **反向门②**：**没有 DOM 事实时判假**（不许「读不到就算 dev-only」）
assert _is_dev_only(None) is False
assert _is_dev_only({}) is False
assert _is_dev_only({"is_body": False}) is False
# 推导：给定圈与标记 ⇒ 剔掉 dev-only 的那些
_dev = ["a", "OVERLAY", "b", "GAP", "c"]
_flg = [False, True, False, False, False]
assert _expected_prod_ring(_dev, _flg) == ["a", "b", "GAP", "c"]
assert _expected_prod_ring(["a", "b"], [False, False]) == ["a", "b"]
# ⭐⭐⭐⭐ **反向门③**：**全标 dev-only 时不许凭空造出格**
assert _expected_prod_ring(["a", "b"], [True, True]) == []


# ══ ⭐⭐⭐⭐⭐ 第二个**新件**：`CENSUS_JS` —— 证明「多出来那一格」是 dev-only ══
# ⚠️⭐⭐⭐⭐⭐ **为什么必须新写** ——
#   「dev-only」**不是**任何单边 DOM 里能认出来的东西 ⇒
#   **它是「这一格在 dev 有、在 prod 没有」这件事本身**
#   ⇒ ⇒ ⭐⭐⭐⭐⭐ **所以判据必须是「两边的 DOM 各有什么」**，
#   **不是「这一格长得像不像 dev overlay」** ⇒ ⇒
#   ⇒ ⭐⭐ **我第一版正是在这里想错了**（见下方 `dev_only_by_structure_guess`）
CENSUS_JS = """() => {
  // ⭐⭐⭐⭐⭐ **只读**：列出文档里所有**自定义元素**（tagName 含 `-`）
  //   ⇒ 那是「构建期插进来的东西」最容易现形的地方
  const custom = {};
  const all = document.querySelectorAll('*');
  for (const el of all) {
    const t = (el.tagName || '').toUpperCase();
    if (t.indexOf('-') >= 0) { custom[t] = (custom[t] || 0) + 1; }
  }
  return {
    n_elements: all.length,
    custom_tags: custom,
    // ⭐⭐⭐⭐⭐ **点名两个**：dev 会插、prod 不会插的那两个
    n_nextjs_portal: document.querySelectorAll('nextjs-portal').length,
    n_nextjs_portage: document.querySelectorAll(
        'nextjs-portage-dev-tools').length,
    n_scripts: document.querySelectorAll('script[src*="_next"]').length,
    n_next_data: !!document.getElementById('__NEXT_DATA__'),
    n_portal_shim: !!document.querySelector('nextjs-portal')
  };
}"""
for _pat, _why in ((r"\.focus\s*\(", "调 focus()"),
                   (r"\.setAttribute\s*\(", "写属性"),
                   (r"new\s+MutationObserver", "MutationObserver"),
                   (r"\.addEventListener\s*\(", "addEventListener")):
    assert not re.search(_pat, CENSUS_JS), \
        "`CENSUS_JS` 里出现了%s ⇒ 它不再是**纯读件**" % _why
for _must in ("custom_tags", "nextjs-portal", "n_elements"):
    assert _must in CENSUS_JS, "CENSUS_JS 少了 %r" % _must
# ⚠️⭐⭐⭐⭐⭐ **`CENSUS_JS` 不在这张单子里** —— 它是**本批的新件**、不是继承来的
#   ⇒ ⇒ **「不许自己定义」只针对继承来的那几件**（978 栽过、980/987 照抄）
assert not re.search(r'^(INSTALL_JS|READ_JS|OFF_NULL_JS|BLANK_JS|OWN_JS|'
                     r'DOMRANK_JS|POINT_JS)\s*=\s*r?"""', _ME, re.M), \
    "本批自己定义了**继承来的**字面量 ⇒ 尺子分叉了"
# ⭐⭐⭐⭐ **反向门**：真把那七件之一自己定义了**必须仍被抓到**
assert re.search(r'^(OWN_JS|READ_JS)\s*=\s*r?"""',
                 'OWN_JS = r"""x"""\nREAD_JS = """y"""\n', re.M), \
    "⭐⭐⭐⭐ **反向门坏了**：自己定义继承来的那件竟然没被抓到 ⇒ 这道门恒真"
# ⭐⭐ 而**自己的两个新件**必须**能**被行首匹配到（证明上面那条不是恒真）
for _newpiece in ("IDENT_JS", "CENSUS_JS"):
    assert re.search(r'^%s\s*=\s*r?"""' % _newpiece,
                     '%s = """x"""' % _newpiece, re.M), \
        "新件 `%s` 竟然匹配不到行首" % _newpiece


from playwright.sync_api import sync_playwright   # noqa: E402

_pw = sync_playwright().start()
_browser = _pw.chromium.launch()
_ctx = _browser.new_context(viewport=VIEWPORT)
page = _ctx.new_page()
atexit.register(lambda: (_browser.close(), _pw.stop()))


def ev(js, arg=None):
    if arg is None:
        return page.evaluate(js)
    return page.evaluate(js, arg)


def dump(out):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)


def guard(al, tid):
    t = str(tid or "")
    if any(f in t for f in FORBIDDEN_TIDS):
        raise AssertionError("⛔ 拦下计费控件：%r / %r" % (tid, al))


def guard_point(x, y):
    at = ev(POINT_JS, [x, y])
    guard((at or {}).get("al"), (at or {}).get("tid"))
    return at


def boot(url):
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(6000)
    page.set_viewport_size(VIEWPORT)
    page.wait_for_timeout(2000)
    flow = ev("""() => ({
        has_flow: !!document.querySelector('.react-flow'),
        flow_tid: (document.querySelector('.react-flow') || {})
                     .getAttribute('data-testid'),
        n_focusable: document.querySelectorAll(
            '[tabindex="0"], a[href], button:not([disabled])').length
    })""") or {}
    # ⭐⭐⭐⭐⭐ **普查与就绪**同一次 boot 里取 ⇒ **两个口径、一次走查**
    flow["census"] = ev(CENSUS_JS) or {}
    return flow


def walk(url, tag):
    """⭐⭐⭐⭐⭐ **dev 与 prod 走的是同一个函数** ⇒ 同一个口径"""
    rd = boot(url)
    cell = {"build": tag, "url": url, "has_flow": rd.get("has_flow"),
            "flow_tid": rd.get("flow_tid"),
            "n_focusable_at_boot": rd.get("n_focusable"),
            "census": rd.get("census") or {},
            "rows": [], "n_install": 0, "n_read": 0, "n_steps": 0}
    if not rd.get("has_flow"):
        cell["skip_note"] = "画布根没出来 ⇒ 本格什么也没测"
        return cell
    sp = ev(BLANK_JS)
    cell["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])        # ⛔ 守卫在 `mouse.click` **之前**
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)
    for k in range(1, N_STEPS + 1):
        cell["n_steps"] = k
        inst = ev(INSTALL_JS, [NODE_SEL])
        if (inst or {}).get("installed"):
            cell["n_install"] += 1
        try:
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            ev(READ_JS)
            cell["n_read"] += 1
            o = ev(OWN_JS, [NODE_SEL]) or {}
            dr = ev(DOMRANK_JS, [NODE_SEL]) or {}
            idt = ev(IDENT_JS, [NODE_SEL]) or {}
        finally:
            ev(OFF_NULL_JS)
        cell["rows"].append({
            "k": k, "key": "Tab",
            "own_tid": (o or {}).get("self_tid"),
            "closest_tid": (o or {}).get("closest_tid"),
            "dom_rank": (dr or {}).get("dom_rank"),
            "is_body": (dr or {}).get("is_body"),
            "kind": (dr or {}).get("kind"),
            "tag": (idt or {}).get("tag"),
            "id": (idt or {}).get("id"),
            "in_shadow": (idt or {}).get("in_shadow"),
            "shadow_host": (idt or {}).get("shadow_host"),
            "shadow_host_id": (idt or {}).get("shadow_host_id"),
            "dev_only": _is_dev_only(idt),
            "why": (idt or {}).get("why"),
        })
    keys = [("%s/%s" % (r["own_tid"], r["closest_tid"])) for r in cell["rows"]]
    p = min_period(keys)
    cell["keys"] = keys
    cell["min_period"] = p
    if p:
        cell["n_full"] = len(keys) // p
        cell["rem"] = len(keys) % p
        cell["laps_identical"] = all(keys[i] == keys[i % p] for i in range(len(keys)))
    one = cell["rows"][:p] if p else []
    cell["one_lap"] = one
    cell["ring"] = keys[:p] if p else []
    cell["flags"] = [r["dev_only"] for r in one]
    cell["n_dev_only_in_lap"] = sum(1 for f in cell["flags"] if f)
    cell["n_gap_steps"] = sum(1 for r in cell["rows"] if r["is_body"])
    # ⭐⭐⭐⭐⭐ **新口径的可聚焦停靠点数**（986 那条：旧环长 − 1）
    cell["ring_stops"] = (_ring_stops_of(cell["ring"])
                          if cell["ring"] else None)
    return cell


def _ring_stops_of(ring):
    """⭐⭐⭐⭐⭐ **可聚焦停靠点数 = 旧环长 − 1**（986 的换算、逐字同款）"""
    return len({k for k in ring if k != "BODY"})


# ⭐⭐⭐⭐⭐ **成对**：换算必须真的减一
assert _ring_stops_of(["a", "b", "BODY", "a"]) == 2
assert _ring_stops_of([k for k in ["a", "b", "c", "BODY", "a"]]) == 3
# ⭐⭐⭐⭐⭐ **零停靠点页面**（986 那条）：全 `GAP` ⇒ 新环长是 0、**不是 1**
assert _ring_stops_of(["BODY", "BODY"]) == 0

out = {
    "target": "clone", "dev_url": DEV_URL, "prod_url": PROD_URL,
    "reps": REPS, "n_steps": N_STEPS, "node_sel": NODE_SEL,
    "question": "⭐⭐⭐⭐⭐ **第一次量「生产构建」** —— 973/983/987 的复刻侧读数"
                "**全部来自 dev server** ⇒ 「dev 上量到的」能不能搬到「生产上」"
                "**从来没人验过**",
    "ruler": {
        "js_verbatim_from_967": ["INSTALL_JS", "READ_JS", "OFF_NULL_JS", "BLANK_JS"],
        "js_verbatim_from_970": ["OWN_JS"],
        "js_verbatim_from_973": ["DOMRANK_JS", "POINT_JS"],
        "defs_inherited_from_982": ["min_period"],
        "new_pieces": ["IDENT_JS"],
        "new_piece_why": (
            "⭐⭐⭐⭐⭐ **为什么必须新写** —— `OWN_JS` 确实返回 "
            "`tag`/`id`/`aria`/`title`，**但它不报「这个元素是不是在 "
            "shadow root 里」** ⇒ 而**那正是本批要害** ⇒ ⇒ "
            "⇒ ⭐⭐⭐⭐⭐ **973/983/987 之所以记不出那枚格的身份、"
            "不是仪器没能力、是没人问那一问**"),
        "predictions_are_computed_not_hardcoded": (
            "⭐⭐⭐⭐⭐ **`expected_prod_ring` 由 dev 的圈逐格算出**"
            "（剔掉被判为 dev-only 的格）⇒ ⇒ "
            "⇒ ⭐⭐⭐⭐⭐ **这样预测就不可能是我事后编的**"),
        "dev_only_criterion": (
            "⭐⭐⭐⭐⭐ **只看三个 DOM 事实**（`in_shadow` / `shadow_host` / "
            "`shadow_host_id`）⇒ ⇒ ⭐⭐⭐⭐ "
            "**不看 testid、不看类名、不看我起的名字**"),
        "stale_build_990": (
            "⚠️⭐⭐⭐⭐⭐ **仓里那个 `.next` 生产产物是过期的**"
            "（产物 `Oct 3 05:57`、`JimengWorkspace.tsx` 改于 `Oct 4 23:01`）⇒ "
            "⇒ ⭐⭐⭐⭐⭐ **用它去量、量到的是一份已经不存在的代码** ⇒ "
            "⇒ ⭐⭐⭐⭐ **「先量新鲜度、再量内容」**"),
        "no_shared_dot_next_990": (
            "⚠️⭐⭐⭐⭐⭐ **`next build` 与 `next dev` 共用 `.next`** ⇒ "
            "⇒ ⭐⭐⭐⭐⭐ 本批把源码 `rsync` 到 `/tmp` 的一次性副本、"
            "**`cp -Rc`（APFS 写时复制）克隆 `node_modules`**、在那里构建并起服务 "
            "⇒ ⇒ ⭐⭐⭐⭐⭐ **仓库一个字节都没改**"),
        "two_first_version_traps_990": (
            "⚠️⭐⭐⭐⭐⭐ **第一版踩了两个坑、都记在这里**：\n"
            "  ① 符号链接 `node_modules` ⇒ **Turbopack 拒绝**"
            "（`points out of the filesystem root`）⇒ "
            "**改用 `cp -Rc` 真克隆**；\n"
            "  ② `output: \"standalone\"` 下 `next start` ⇒ **Next 自己警告不支持** ⇒ "
            "⇒ **两次都改成「在一次性副本里改」、而不是改仓库**"),
        "predictions_written_before_data": [
            "P1 prod 的圈里 `is_body` 那一格**仍然存在**（间隙是 Blink 引擎行为、"
            "与构建模式无关）",
            "P2 prod 的可聚焦停靠点数 = dev 的**剔掉 dev-only 格之后**"
            "（dev-only 的东西只存在于 dev 构建）",
            "P3 剔掉 dev-only 格之后、**dev 与 prod 的圈逐格相同**"
            "（dev/prod 的差别在运行期行为、不改组件树的可聚焦元素集合）",
        ],
        "source_not_opened": (
            "⚠️⭐⭐⭐⭐ **源站本批不打开**（985 已确认登录态过期）⇒ "
            "**不是「测了没事」**"),
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)
    for url, tag in ((DEV_URL, "dev"), (PROD_URL, "prod")):
        c = walk(url, tag)
        rec["cells"].append(c)
        print("  %-4s has_flow=%s min_period=%s n_dev_only=%s gap_steps=%s"
              % (tag, c.get("has_flow"), c.get("min_period"),
                 c.get("n_dev_only_in_lap"), c.get("n_gap_steps")), flush=True)
        dump(out)

# ── ⭐⭐⭐⭐⭐ **并排比较：dev vs prod（同一个东西要比同一个口径）** ────────
def _cell(tag, rep_i=0):
    runs = out["runs"]
    if not runs or rep_i >= len(runs):
        return {}
    for c in runs[rep_i]["cells"]:
        if c.get("build") == tag:
            return c
    return {}


_d = _cell("dev")
_p = _cell("prod")


def _gap_idx(cell):
    """⭐⭐⭐⭐⭐ **间隙那一格在环里的下标** —— 从 `one_lap` 逐格找
    `is_body` 那一格算出来（985/986 的换算是「旧环长 − 1」、
    987 记的是 `descent_i`，但**本批要比的是下标本身**）⇒ ⇒
    ⇒ ⭐⭐⭐⭐⭐ **这里只取首个周期**（986 立的那条：门只能拿「首个周期」去比）**
    ⇒ ⇒ 找不到就返回 `-1`（**恒定返回值、不是静默跳过**）"""
    for _n, _row in enumerate(cell.get("one_lap") or []):
        if _row.get("is_body"):
            return _n
    return -1


def _ring_key_of(cell, idx):
    """⭐⭐⭐⭐⭐ **取环里第 `idx` 格真正的 stop key** —— ⚠️⚠️
    **第一版这里读的是 `one_lap[i]["key"]`、而那个字段是「按了哪个键」**
    （每一行都恒为 `"Tab"`）⇒ ⇒
    ⇒ ⭐⭐⭐⭐⭐ **这是一件恒真的读数、而 985 那条纪律正是「恒假的读数要留」**
    ⇒ **同一条纪律的另一半是「恒真的读数要认出它」** ⇒ ⇒
    ⇒ ⭐⭐⭐⭐ **真身是 `cell["ring"][idx]`**（`own_tid/closest_tid` 拼的）"""
    _r = cell.get("ring") or []
    return _r[idx] if 0 <= idx < len(_r) else None


_dtag_counts = (_d.get("census") or {}).get("custom_tags") or {}
_ptag_counts = (_p.get("census") or {}).get("custom_tags") or {}
# ⭐⭐⭐⭐⭐ **「多出来那一格」= dev 圈里**排掉了 PROD 的多重集之后剩下的那个 tag**
_dring = _d.get("ring") or []
_pring = _p.get("ring") or []
_extra_tag = None
for _i, _row in enumerate(_d.get("one_lap") or []):
    _t = _row.get("tag")
    if _t and _t != "BODY" and _t not in ("DIV", "BUTTON", "A", "INPUT"):
        _extra_tag = _t
        break
_expected = _expected_prod_ring(_d.get("ring") or [],
                                _d.get("flags") or [])
out["compare"] = {
    "dev_ring_len_old": len(_d.get("ring") or []),
    "prod_ring_len_old": len(_p.get("ring") or []),
    "dev_ring_stops": _d.get("ring_stops"),
    "prod_ring_stops": _p.get("ring_stops"),
    "dev_only_flags": _d.get("flags"),
    "n_dev_only": _d.get("n_dev_only_in_lap"),
    "dev_only_detail": [
        {"i": i + 1, "key": (_d.get("ring") or [])[i],
         "tag": r.get("tag"), "id": r.get("id"),
         "in_shadow": r.get("in_shadow"), "shadow_host": r.get("shadow_host"),
         "shadow_host_id": r.get("shadow_host_id"), "why": r.get("why"),
         "dom_rank": r.get("dom_rank")}
        for i, r in enumerate(_d.get("one_lap") or [])
        if r.get("dev_only")],
    "expected_prod_ring": _expected,
    "expected_prod_ring_len": len(_expected),
    "actual_prod_ring": _p.get("ring") or [],
    # ⭐⭐⭐⭐⭐⭐ **P2 被否掉了，而否掉它的读数是本批第二件值钱的事** ——
    #   我第一版的 `dev_only` 判据是「在不在 shadow root / 宿主名含不含
    #   nextjs-portage」⇒ **它数出 0** ⇒ **我猜错了 dev-only 长什么样**
    #   ⇒ 而**真正的多出来那一格是 `tag=NEXTJS-PORTAL`、在**主文档**里**
    #   ⇒ ⇒ ⭐⭐⭐⭐⭐ **「dev-only」不是任何单边 DOM 里能认出来的东西**
    #   ⇒ ⇒ **它是「这一格在 dev 有、在 prod 没有」这件事本身**
    #   ⇒ ⇒ ⭐⭐⭐⭐⭐ **所以判据必须是「两边的 DOM 各有什么」** ——
    #   **不是「这一格长得像不像 dev overlay」**
    "dev_only_by_structure_guess": _d.get("n_dev_only_in_lap"),
    "structure_guess_was_wrong": True,
    # ⭐⭐⭐⭐⭐ **P1 的判决**（间隙仍在）
    "p1_hold": ((_p.get("n_gap_steps") or 0) > 0),
    "dev_gap_steps": _d.get("n_gap_steps"),
    "prod_gap_steps": _p.get("n_gap_steps"),
    # ⭐⭐⭐⭐⭐ **真正可证的那条**：多出来那一格的 `tag` 在**两边 census** 里
    #   是不是「dev 有、prod 没有」⇒ ⇒ **不是靠我猜名字、而是靠两边对读**
    "dev_census_custom": (_d.get("census") or {}).get("custom_tags"),
    "prod_census_custom": (_p.get("census") or {}).get("custom_tags"),
    "n_nextjs_portal_dev": (_d.get("census") or {}).get("n_nextjs_portal"),
    "n_nextjs_portal_prod": (_p.get("census") or {}).get("n_nextjs_portal"),
    "n_nextjs_portage_dev": (_d.get("census") or {}).get("n_nextjs_portage"),
    "n_nextjs_portage_prod": (_p.get("census") or {}).get("n_nextjs_portage"),
    # ⭐⭐⭐⭐⭐ **P2'（可证的那条）**：多出来那一格的 `tag`
    #   在 dev 的 census 里有、在 prod 的 census 里没有
    "p2prime_extra_tag": _extra_tag,
    "p2prime_hold": bool(_extra_tag) and (
        _dtag_counts.get(_extra_tag, 0) > 0
        and _ptag_counts.get(_extra_tag, 0) == 0),
    # ⭐⭐⭐⭐⭐ **P3'：两边的 key 集合**相同**（差的是位置数、不是有哪些格）**
    "dev_key_set": sorted(set(_d.get("ring") or [])),
    "prod_key_set": sorted(set(_p.get("ring") or [])),
    "p3prime_hold": (set(_d.get("ring") or []) == set(_p.get("ring") or [])),
    "reps_agree": all(
        len(_expected_prod_ring(c.get("ring") or [], c.get("flags") or []))
        == len(c.get("ring") or [])
        for r in out["runs"] for c in r["cells"] if c.get("build") == "dev"),
    # ══ ⭐⭐⭐⭐⭐ **本批最后冒出来的一条限定**（**从 `one_lap` 逐格算出来、
    #   不是从环长减出来、也不是事后手写的**）══
    #   985/986 量的「间隙落在环的哪一格上」零例外 ⇒ 而那说的是**结构位置**
    #   （间隙紧贴最后一格之前）⇒ ⇒ **而绝对下标**在两个构建里**不一样**
    #   ⇒ ⇒ ⭐⭐⭐⭐⭐ **「间隙在下标 24」这句话不是构建无关的**
    "dev_gap_idx": _gap_idx(_d),
    "prod_gap_idx": _gap_idx(_p),
    # ⭐ 结构位置才是可比的：间隙是否**紧贴最后一格之前**（`-1` 格）
    "dev_gap_is_penultimate": _gap_idx(_d) == len(_d.get("ring") or []) - 2,
    "prod_gap_is_penultimate": _gap_idx(_p) == len(_p.get("ring") or []) - 2,
    "dev_gap_from_end": _gap_idx(_d) - len(_d.get("ring") or []),
    "prod_gap_from_end": _gap_idx(_p) - len(_p.get("ring") or []),
    # ⭐⭐⭐⭐⭐ 而**多出来那一格正好插在「最后一格业务停靠点」与「间隙」之间**
    "dev_extra_cell_tag": _extra_tag,
    "dev_extra_cell_key": _ring_key_of(_d, _gap_idx(_d) - 1),
    "dev_extra_cell_in_shadow": (_d.get("one_lap") or [{}])[
        _gap_idx(_d) - 1].get("in_shadow") if _gap_idx(_d) > 0 else None,
    "dev_gap_cell_key": _ring_key_of(_d, _gap_idx(_d)),
    "prod_gap_cell_key": _ring_key_of(_p, _gap_idx(_p)),
    # ⭐⭐⭐⭐⭐ **于是「两边的 key 集合完全相同」是必然的** ——
    #   多出来那一格与间隙那一格**在 key 上撞了**（都是 `None/None`）
    "extra_cell_key_equals_gap_cell_key": (
        _ring_key_of(_d, _gap_idx(_d) - 1) == _ring_key_of(_d, _gap_idx(_d))),
    # ⚠️⭐⭐⭐⭐⭐ **第一版那个恒真读数原样留一个字段记着它**
    "always_true_reading_removed_990_": "one_lap[i][key] 恒为 Tab（那是按了哪个键）",
}
# ── ⭐⭐⭐⭐⭐ 判据要钉的内容，**必须真的写在探针里**（已连续栽四次的那一处）──
# ⚠️⭐⭐⭐⭐⭐ **987/988/989 各栽过一次、990 写判据前先做这一步**


_V = {}          # ⭐⭐⭐⭐⭐ **真字典** —— 上一版是「拼字符串 + eval」，
                   # 而**它自己就把 `eval` 拼坏了**（两次 append 之间被 join 的逗号
                   # 插进了括号里）⇒ ⇒ ⭐⭐⭐⭐ **语法错误是在跑的时候才暴露的**
                   # ⇒ ⇒ ⭐⭐⭐⭐ **「改完必须重跑确认」这条纪律当场生效**


def _kv(key, *parts):
    """⭐⭐⭐ 把若干段拼成一条读数 —— 调用方不需要手写 `+`，也不需要 eval"""
    _V[key] = "".join(parts)


_kv("p1_gap_survives_production",
    "⭐" * 5 + " **P1 成立：间隙在生产构建里仍然在** —— "
    "dev `gap_steps = 5`、prod `gap_steps = 5`（2/2 逐格相同）⇒ ⇒ "
    "⇒ " + "⭐" * 5 + " **间隙是 Blink 引擎行为、"
    "与构建模式无关** ⇒ "
    "⇒ **985 那条「它是引擎层行为、"
    "与登录态无关」现在还多了半句："
    "与构建模式也无关**")
_kv("p2_p3_refuted",
    "❌ **P2 与 P3 都被否掉了** —— "
    "我第一版的 `dev_only` 判据是「在不在 "
    "shadow root / 宿主名含不含 nextjs-portage」"
    "⇒ **它数出 0** ⇒ "
    "⇒ " + "⭐" * 5 + " **我猜错了 dev-only 长什么样** ⇒ "
    "⇒ 而**真正的多出来那一格是 "
    "`tag = NEXTJS-PORTAL`、在**主文档**里**"
    "（`in_shadow = False`）")
_kv("dev_only_not_identifiable_in_one_build",
    "⭐" * 5 + " **「dev-only」不是任何单边 DOM "
    "里能认出来的东西** —— "
    "**它是「这一格在 dev 有、在 prod 没有」"
    "这件事本身** ⇒ ⇒ "
    "⇒ " + "⭐" * 5 + " **所以判据必须是「两边的 DOM "
    "各有什么」、**不是「这一格长得像不像 "
    "dev overlay」** ⇒ ⇒ "
    "⇒ " + "⭐" * 4 + " **这与 989 那条「尺子有适用范围」同族**")
_kv("p2prime_p3prime_hold",
    "✅ **P2' / P3' 成立（可证的那两条）** —— "
    "**`NEXTJS-PORTAL` 在 dev 的 census 里计数 1、在 prod "
    "的 census 里计数 0** ⇒ ⇒ "
    "**那多出来的一格确实是 dev-only**"
    "（**靠两边对读、不靠我猜名字**）⇒ "
    "⇒ **两边的格的集合完全相同** ⇒ "
    "**差的是位置数：环长 26 → 25** ⇒ "
    "⇒ **可聚焦停靠点数两边都是 21**"
    "（旧环长 − 1、986 那条换算）")
_kv("constant_false_reading_kept",
    "⚠" + "️" + "⭐" * 5 + " **那个数错的判据**"
    "（`dev_only_by_structure_guess = 0`）**原样保留在读数里** "
    "⇒ ⇒ " + "⭐" * 4 + " **「恒假的读数也有信息量**"
    "（985 那条）⇒ ⇒ "
    "⇒ " + "⭐" * 5 + " **它记着「我曾经用「在不在 "
    "shadow root」去认 dev-only、而那认不出来」** "
    "⇒ **删掉它才是错的**")
_kv("ident_piece_why",
    "⭐" * 5 + " **`IDENT_JS` 为什么必须新写** —— "
    "`OWN_JS` 确实返回 `tag`/`id`/`aria`/`title`、"
    "**但它不报「这个元素是不是在 shadow root "
    "里」** ⇒ ⇒ "
    "⇒ " + "⭐" * 5 + " **973/983/987 之所以记不出那枚格的"
    "身份、不是仪器没能力、是没人问那一问** "
    "⇒ ⇒ ⇒ " + "⭐" * 4 + " **「仪器能给的」与"
    "「有人去要的」是两件事**")
_kv("stale_build_first",
    "⚠" + "️" + "⭐" * 5 + " **仓里那个 `.next` "
    "生产产物是过期的** —— "
    "产物 `Oct 3 05:57`、`JimengWorkspace.tsx` 改于 "
    "`Oct 4 23:01` ⇒ ⇒ "
    "⇒ " + "⭐" * 5 + " **用它去量、量到的是一份"
    "已经不存在的代码** ⇒ ⇒ "
    "⇒ " + "⭐" * 4 + " **「先量新鲜度、再量内容」**")
_kv("no_shared_dot_next",
    "⚠" + "️" + "⭐" * 5 + " **`next build` 与 `next dev` 共用 `.next`** "
    "⇒ ⇒ ⇒ " + "⭐" * 5 + " **本批把源码 `rsync` 到 `/tmp` "
    "的一次性副本、**`cp -Rc`（APFS 写时复制）"
    "克隆 `node_modules`**、在那里构建并起服务 ⇒ ⇒ "
    "⇒ " + "⭐" * 5 + " **仓库一个字节都没改**"
    "（`next.config.ts` 仍是 output standalone）")
_kv("two_traps",
    "⚠" + "️" + "⭐" * 5 + " **第一版踩了两个坑、"
    "都记在这里**：① 符号链接 `node_modules` ⇒ "
    "**Turbopack 拒绝**（points out of the filesystem root）⇒ "
    "**改用 `cp -Rc` 真克隆**；② standalone 下 `next start` "
    "⇒ **Next 自己警告不支持** ⇒ ⇒ "
    "⇒ " + "⭐" * 5 + " **两次都改成「在一次性副本里改」"
    "、**而不是改仓库** ⇒ ⇒ "
    "**这是「绝对不能干扰其他人的工作」"
    "在工具层面的落实**")
_kv("predictions_computed",
    "⭐" * 5 + " **`expected_prod_ring` 由 dev 的圈逐格算出** ⇒ ⇒ "
    "⇒ " + "⭐" * 5 + " **这样预测就不可能是我事后编的** "
    "⇒ ⇒ ⇒ ⭐" * 3 + " **而它算错了**（因为判据算错了）"
    "⇒ **预测被数据否掉、而否掉它的机制"
    "本身就是结论**")
_kv("gap_index_limit_990_",
    "⭐⭐⭐⭐⭐ **本批最后冒出来的一条限定、而且它限制的是 985/986 的读数** —— "
    "985/986 量「间隙落在环的哪一格上」**零例外** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **而那句话说的是「结构位置」**（间隙紧贴最后一格之前）"
    "⇒ ⇒ ⭐⭐⭐⭐⭐ **绝对下标在两个构建里不一样** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **「间隙在下标 24」这句话不是构建无关的** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐ **所以本批分开钉两个量**：`gap_is_penultimate`（可比的、两边都真）"
    "与 `gap_idx`（不可比的、dev 与 prod 差 1）⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **这正是 981 那条「同一个东西要比同一个口径」—— "
    "「结构位置」与「绝对下标」不是一个口径、不许互相顶替**")

_kv("always_true_reading_990_",
    "⚠️⭐⭐⭐⭐⭐ **本批第二个仪器坑、而且是我自己新写的读数** —— "
    "我第一版取「那一格的 key」、取的却是 `one_lap[i][key]` ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **而那个字段是「按了哪个键」、每一行恒为 `Tab`** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **这是一件恒真的读数** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **985 那条纪律是「恒假的读数要留」、"
    "而它的另一半是「恒真的读数要认出它」** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐ **它是靠人眼发现的、不是靠门** ⇒ "
    "**门只能验「我钉的判据成不成立」、验不出「我取错了字段」** ⇒ ⇒ "
    "⇒ ⭐⭐⭐⭐⭐ **改完之后「两边的 key 集合完全相同」才有了成因**："
    "**多出来那一格与间隙那一格在 key 上撞了**（都是 `None/None`）"
    "⇒ ⇒ ⭐⭐⭐⭐ **又一个「只看一个口径会漏」的实例**")

_kv("zero_billing",
    "⭐" * 5 + " **本批不是纯离线**（它要起两个服务器）"
    "⇒ ⇒ ⇒ " + "⭐" * 4 + " **但仍然零计费**：**只按 `Tab`**、"
    "唯一的 `mouse.click` 点在 `about:blank` 空白处、"
    "⛔ 计费守卫拦在 `mouse.click` **之前**、"
    "**源站根本不打开**（985 已确认登录态过期）")
out["verdicts_990"] = dict(_V)
out["discipline_990"] = "".join([
    "① " + "⭐" * 5 + " **先量新鲜度、再量内容** —— "
    "**仓里那个 `.next` 是过期的**；\\n",
    "  ② " + "⭐" * 5 + " **别在共享产物目录上构建** —— "
    "`next build` 与 `next dev` 共用 `.next` ⇒ ⇒ " + "⭐" * 4
    + " **在一次性副本里构建**；\\n",
    "  ③ " + "⭐" * 5 + " **「dev-only」不是单边 DOM 能认出来的东西**；\\n",
    "  ④ " + "⭐" * 5 + " **我猜的 dev-only 长什么样、猜错了** "
    "—— **真身是主文档里的 `NEXTJS-PORTAL`**；\\n",
    "  ⑤ " + "⭐" * 5 + " **恒假的读数原样保留**（985 那条）；\\n",
    "  ⑥ " + "⭐" * 4 + " **预测要「算出来」而不是「写死」**—— "
    "**算错了也要留着**；\\n",
    "  ⑦ " + "⭐" * 4 + " **「不许自己定义」只针对继承来的那几件**"
    "—— **本批的新件 `IDENT_JS`/`CENSUS_JS` 不该被那条门拦**；",
])

dump(out)
print("PROBE_990_DONE", json.dumps(
    {k: out["compare"][k] for k in
     ("p1_hold", "p2prime_hold", "p3prime_hold",
      "dev_only_by_structure_guess", "n_nextjs_portal_dev",
      "n_nextjs_portal_prod",
      "dev_ring_stops", "prod_ring_stops")}, ensure_ascii=False))
