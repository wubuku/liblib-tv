#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针 1032-③ —— **克隆页可达性门**：每一个「已完成的克隆成果」都必须从站点根目录走得到。

⭐⭐⭐⭐⭐⭐ **这道门为什么存在**：站点根路由 `/` 是 **LibTV 画布本身** ⇒ 而
**即梦画布、FrameOS 画布、全部项目**同样是「已完成的克隆成果」⇒ ⇒⇒⇒ ⇒
**⇒⇒⇒ ⇒⇒⇒ 它们曾经只能靠手敲 URL 才走得到 ⇒⇒⇒ ⇒⇒⇒ 而全仓没有任何一道门问过这件事**
⇒⇒⇒ ⇒⇒⇒ ⇒⇒⇒ ⇒⇒⇒ 「做完了」与「走得到」在账上长得一模一样 ⇒⇒⇒ ⇒⇒⇒ ⇒⇒⇒ ⇒⇒⇒

⭐⭐⭐⭐⭐ **三个量各记各的**：
  ① **真实路由**（实测 `src/app/**/page.tsx`，不许手列）
  ② **源码可达集合**（从 `/` 出发做 BFS，爬每个页面的 import 闭包里的站内链接）
  ③ **真源登记**（`src/lib/clonePages.ts` —— 应用页、README 路由表、文档三处唯一的出处）
⇒ ⇒ ⇒⇒ ⇒ ⇒ 三者必须逐条对得上 ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒

⭐⭐⭐⭐⭐ **口径（必须写清楚，否则「可达」会被读成比实际更强的东西）**：
  · 「源码可达」是**过近似**：import 闭包里出现过的站内链接都算 ⇒ ⇒ ⇒⇒
    ⇒ ⇒ ⇒⇒ 它抓的是「**忘了挂入口**」这类真实缺口（链接是字面量写的、忘了就是真的没有）
    ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而它**不**保证「那个链接在运行时真的被点得到」
  · ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以另有一条**不过近似**的判据（P5）：
    ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **站点导航组件必须以字面量 href 指向每一个克隆成果页**
  · **别名路由**（纯 `redirect()` 页）不是独立的页面 ⇒ ⇒ ⇒⇒ 它们解析到目标页再判

⭐⭐⭐⭐⭐ **纯离线**（只读仓里的文件）⇒ ⇒ 不依赖浏览器、不依赖 dev server
⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒**
⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
APP = SRC / "app"
GDIR = ROOT / "docs/research/jimeng-canvas"
GOLDEN = GDIR / "clone-reachability-1033.json"
SELF = Path(__file__).name
# ⭐⭐⭐⭐⭐ **真源**：应用页、README 路由表、文档三处唯一的出处
TRUTH_REL = "src/lib/clonePages.ts"
TRUTH = ROOT / TRUTH_REL
# ⭐⭐⭐⭐⭐ **站点导航**：根目录挂的那一组站内链接（判据 P5 钉它）
NAV_REL = "src/components/CloneSiteNav.tsx"
NAV = ROOT / NAV_REL
# ⭐⭐⭐⭐⭐ **索引页**：把真源渲染成页面
INDEX_REL = "src/app/clones/page.tsx"
INDEX = ROOT / INDEX_REL
# ⭐⭐⭐⭐⭐ **文档**：说明「怎么到达」与「怎么交互测试」
DOC_REL = "docs/CLONE_PAGES_INDEX.md"
DOC = ROOT / DOC_REL

# ── kind 三档（本门七条全是 `failure`）────────────────────────────────────────
KINDS_1033 = ("failure", "conclusion", "precondition")
CRITERION_KINDS = {
    "P1_the_route_universe_is_measured_from_the_filesystem_1033": "failure",
    "P2_every_finished_clone_page_is_reachable_from_the_site_root_1033": "failure",
    "P3_every_alias_route_resolves_to_a_reachable_page_1033": "failure",
    "P4_the_registry_lists_every_real_page_and_nothing_else_1033": "failure",
    "P5_the_site_nav_links_to_every_clone_page_by_a_literal_href_1033": "failure",
    "P6_the_docs_say_how_to_reach_and_how_to_interact_test_each_page_1033": "failure",
    "P7_this_gate_can_actually_go_red_1033": "failure",
}

# ── 口径用的正则（全部逐条列出来 ⇒ 「抓到什么」是可读的）────────────────────
_RE_ROUTE_SEG = re.compile(r"^\[([^\]]+)\]$")
_RE_FROM = re.compile(r"""(?:^|\n)\s*(?:import|export)[^\n;]*?from\s*["']([^"']+)["']""")
_RE_BARE_IMPORT = re.compile(r"""(?:^|\n)\s*import\s*["']([^"']+)["']""")
_RE_HREF = re.compile(r"""\bhref\s*=\s*["']([^"']*)["']""")
_RE_ROUTER = re.compile(
    r"""\b(?:router\.(?:push|replace)|redirect)\s*\(\s*["']([^"']*)["']""")
_RE_REDIRECT = re.compile(r"""\bredirect\s*\(\s*["']([^"']*)["']""")
_RE_TRUTH_ROUTE = re.compile(r"""\broute:\s*["']([^"']+)["']""")
_RE_TRUTH_ID = re.compile(r"""\bid:\s*["']([^"']+)["']""")


# ── 读文件层（可被注入式反证覆盖 ⇒ 「改坏盘上的东西」不必真的改盘）────────
#   ⇒ ⇒ ⇒⇒ **⇒ 覆盖表按【绝对路径】索引** ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒⇒
#   ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒⇒ **⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而键必须用 resolve() 后的路径** ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒⇒
#   ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒⇒ ⇒ **⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 否则 macOS 的 /tmp ⇒ /private/tmp 会让覆盖失效**
_OVERRIDES = {}


def _read(path):
    try:
        key = Path(path).resolve()
    except OSError:
        key = path
    if key in _OVERRIDES:
        return _OVERRIDES[key]
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return None


def _is_internal(target):
    """站内链接：以单个 `/` 开头（`//` 是协议相对 URL ⇒ 不算）。"""
    return bool(target) and target.startswith("/") and not target.startswith("//")


def _normalize(route):
    """把 `/frameos/canvas/[id]` 变成 `/frameos/canvas/demo`（动态段取 demo）。"""
    out = []
    for seg in route.strip("/").split("/"):
        if not seg:
            continue
        m = _RE_ROUTE_SEG.match(seg)
        out.append("demo" if m else seg)
    return "/" + "/".join(out)


# ── ① 真实路由（实测，不许手列）──────────────────────────────────────────────
def _routes():
    """扫 `src/app/**/page.tsx` ⇒ 真实路由集合（含动态段的实例化）。"""
    found = {}
    if not APP.is_dir():
        return found
    for page in sorted(APP.rglob("page.tsx")):
        rel = page.relative_to(APP)
        segs = list(rel.parts[:-1])          # 去掉 "page.tsx"
        route = "/" + "/".join(segs) if segs else "/"
        found[_normalize(route)] = page
    return found


def _aliases(routes):
    """纯 `redirect()` 的页是**别名** ⇒ 解析到它的目标。"""
    out = {}
    for route, page in routes.items():
        text = _read(page)
        if not text:
            continue
        m = _RE_REDIRECT.search(text)
        if m and _is_internal(m.group(1)):
            out[route] = _normalize(m.group(1))
    return out


# ── ② 源码链接闭包 ─────────────────────────────────────────────────────────
def _import_specs(text):
    specs = []
    for rx in (_RE_FROM, _RE_BARE_IMPORT):
        for m in rx.finditer(text):
            specs.append(m.group(1))
    return specs


def _resolve(spec, from_file):
    """把 import 说明解析成仓内的真实文件（取不到就 None ⇒ 不猜）。"""
    if spec.startswith("@/"):
        base = SRC / spec[2:]
    elif spec.startswith("."):
        base = (from_file.parent / spec).resolve()
    else:
        return None
    cands = [base, base.with_suffix(".tsx"), base.with_suffix(".ts"),
             base / "index.tsx", base / "index.ts"]
    for cand in cands:
        try:
            if cand.is_file() and cand.suffix in (".tsx", ".ts"):
                return cand
        except OSError:
            continue
    return None


def _closure(path, limit=600):
    """一个页面的 import 闭包（递归）⇒ 文件 → 文本。"""
    seen = set()
    out = {}
    stack = [path]
    while stack and len(out) < limit:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        text = _read(f)
        if text is None:
            continue
        out[f] = text
        for spec in _import_specs(text):
            r = _resolve(spec, f)
            if r is not None and r not in seen:
                stack.append(r)
    return out


def _links(texts):
    """从一批源码里收集站内链接（字面量 href ＋ router.push/replace/redirect）。"""
    out = set()
    for text in texts:
        for m in _RE_HREF.finditer(text):
            if _is_internal(m.group(1)):
                out.add(m.group(1))
        for m in _RE_ROUTER.finditer(text):
            if _is_internal(m.group(1)):
                out.add(_normalize(m.group(1)))
    return out


def _reachable(routes):
    """从站点根目录 `/` 出发做 BFS ⇒ 可达路由集合（源码口径）。"""
    start = "/"
    if start not in routes:
        return set(), {}
    seen = set()
    hops = {}
    queue = [start]
    while queue:
        cur = queue.pop(0)
        if cur in seen:
            continue
        seen.add(cur)
        page = routes.get(cur)
        if page is None:
            continue
        texts = list(_closure(page).values())
        for link in _links(texts):
            nxt = _normalize(link)
            if nxt in routes and nxt not in seen:
                hops.setdefault(nxt, cur)
                queue.append(nxt)
    return seen, hops


# ── ③ 真源登记 ─────────────────────────────────────────────────────────────
def _registry():
    """从 `src/lib/clonePages.ts` 里读出登记（id → route/kind）。"""
    text = _read(TRUTH)
    if not text:
        return []
    entries = []
    ids = _RE_TRUTH_ID.findall(text)
    routes = _RE_TRUTH_ROUTE.findall(text)
    kinds = re.findall(r"""\bkind:\s*["'](clone|site)["']""", text)
    for i, rid in enumerate(ids):
        entries.append({
            "id": rid,
            "route": routes[i] if i < len(routes) else None,
            "kind": kinds[i] if i < len(kinds) else None,
        })
    return entries


# ── ④ 文档 ─────────────────────────────────────────────────────────────────
def _doc_sections():
    """从文档里切出每个 `## <id>` 小节 ⇒ id → 小节正文。"""
    text = _read(DOC)
    if not text:
        return {}
    out = {}
    parts = re.split(r"(?m)^##\s+", text)
    for part in parts[1:]:
        head = part.split("\n", 1)[0].strip()
        sid = head.split(" ", 1)[0].strip().strip("`")
        out[sid] = part
    return out


# ── 判决（纯函数 ⇒ 可被注入式反证直接调用）────────────────────────────────
def _judge(routes=None, aliases=None, registry=None, nav_text=None,
           doc_sections=None):
    if routes is None:
        routes = _routes()
    if aliases is None:
        aliases = _aliases(routes)
    if registry is None:
        registry = _registry()
    if nav_text is None:
        nav_text = _read(NAV)
    if doc_sections is None:
        doc_sections = _doc_sections()

    why = []
    canonical = {r: p for r, p in routes.items() if r not in aliases}
    reachable, hops = _reachable(routes)

    # ① 路由宇宙是实测的
    if not routes:
        why.append("no_route_found_under_src_app")
    if not canonical:
        why.append("no_canonical_page_found")

    # ② 每个规范页都必须从 `/` 可达
    unreachable = sorted(r for r in canonical if r not in reachable)
    if unreachable:
        why.append("pages_not_reachable_from_the_site_root:%d" % len(unreachable))

    # ③ 别名必须解析到一个可达页
    bad_alias = sorted(
        a for a, t in aliases.items()
        if t not in canonical or t not in reachable)
    if bad_alias:
        why.append("alias_routes_not_resolving_to_a_reachable_page:%d"
                   % len(bad_alias))

    # ④ 登记必须与真实页逐条对得上（双向）
    reg_routes = [e["route"] for e in registry if e["route"]]
    missing_in_registry = sorted(r for r in canonical if r not in reg_routes)
    phantom_in_registry = sorted(r for r in reg_routes if r not in canonical)
    if missing_in_registry:
        why.append("pages_missing_from_the_registry:%d" % len(missing_in_registry))
    if phantom_in_registry:
        why.append("registry_lists_pages_that_do_not_exist:%d"
                   % len(phantom_in_registry))
    if not registry:
        why.append("registry_is_empty_or_unreadable")

    # ⑤ 站点导航必须以**字面量 href** 指向每一个克隆成果页
    nav_links = set()
    if nav_text:
        for m in _RE_HREF.finditer(nav_text):
            nav_links.add(_normalize(m.group(1)))
    else:
        why.append("site_nav_component_missing_or_unreadable")
    need_in_nav = sorted(
        e["route"] for e in registry
        if e["kind"] == "clone" and e["route"] and e["route"] != "/")
    missing_in_nav = sorted(r for r in need_in_nav if r not in nav_links)
    if missing_in_nav:
        why.append("site_nav_does_not_link_to:%d" % len(missing_in_nav))

    # ⑥ 文档必须对每个登记条目写明「怎么到达」＋「怎么交互测试」
    doc_missing = []
    for e in registry:
        if not e["id"]:
            continue
        sec = doc_sections.get(e["id"])
        if sec is None:
            doc_missing.append(e["id"])
            continue
        if "怎么到达" not in sec or "怎么交互测试" not in sec:
            doc_missing.append(e["id"])
    if doc_missing:
        why.append("docs_missing_reach_or_interaction_sections:%d"
                   % len(doc_missing))

    return {
        "ok": not why,
        "why": why,
        "n_routes": len(routes),
        "n_canonical": len(canonical),
        "n_aliases": len(aliases),
        "n_reachable": len(reachable),
        "routes": sorted(routes),
        "canonical": sorted(canonical),
        "aliases": aliases,
        "unreachable_pages": unreachable,
        "bad_aliases": bad_alias,
        "missing_in_registry": missing_in_registry,
        "phantom_in_registry": phantom_in_registry,
        "registry": registry,
        "nav_links": sorted(nav_links),
        "missing_in_nav": missing_in_nav,
        "doc_missing": doc_missing,
        "hops": hops,
    }


# ── 注入式反证（改原始输入 ⇒ 必须翻红）──────────────────────────────────
def _selftest(base=None):
    """⭐⭐⭐⭐⭐ **反证必须改【原始输入】**（盘上的文件内容），
    ⇒ ⇒ ⇒⇒ 而不许改上游的 ok 标志 ⇒ ⇒ ⇒⇒ 否则那道判决会变成恒真。

    ⇒ ⇒ ⇒⇒ 而「注入」的实现方式是**覆盖读文件层**（`_OVERRIDES`）⇒ ⇒ ⇒⇒
    ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒⇒ ⇒ **⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以反证**不碰盘上的任何一个字节** ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒⇒
    """
    base = base if base is not None else _judge()
    cases = []

    def _case(name, overrides):
        _OVERRIDES.clear()
        _OVERRIDES.update(overrides)
        try:
            r = _judge()
        finally:
            _OVERRIDES.clear()
        went_red = (not r["ok"]) and (r["why"] != base["why"])
        cases.append({"case": name, "went_red": went_red,
                      "why": list(r["why"])})

    nav_text = _read(NAV) or ""
    truth_text = _read(TRUTH) or ""
    doc_text = _read(DOC) or ""
    jimeng_alias = ROOT / "src/app/jimeng/page.tsx"

    # ① 忘了给即梦画布挂入口（站点导航里那个 href 改成不存在的路由）
    if nav_text:
        _case("站点导航里把即梦画布的 href 改坏",
              {NAV.resolve(): nav_text.replace('"/jimeng/canvas/demo"',
                                               '"/no-such-route"')})

    # ② 站点导航整个不可读（文件被清空）
    if nav_text:
        _case("站点导航文件被清空", {NAV.resolve(): ""})

    # ③ 真源里少登记一条（做完了但没登记）
    if truth_text:
        _case("真源里少登记一个克隆页",
              {TRUTH.resolve(): truth_text.replace('route: "/project",',
                                                  'route: "/project-gone",')})

    # ④ 真源里多登记一条不存在的页
    if truth_text:
        _case("真源里多登记一个不存在的页",
              {TRUTH.resolve(): truth_text.replace(
                  'export const CLONE_PAGES: ClonePageEntry[] = [',
                  'export const CLONE_PAGES: ClonePageEntry[] = [\n'
                  '  { id: "phantom", name: "幽灵页", route: "/no-such-page",'
                  ' product: "无", summary: "无", reachableVia: ["无"],'
                  ' trySteps: ["无"], mockBoundary: "无", manual: null,'
                  ' kind: "clone" },')})

    # ⑤ 文档里删掉一整节（⭐ 必须挑一个**登记里有的 id** ⇒
    #    ⇒ ⇒ 删掉「入口在哪」那种非登记小节是**不构成缺陷**的 ⇒ ⇒ 那样的注入证明不了门有牙）
    reg_ids = [e["id"] for e in _registry() if e["id"]]
    if doc_text and reg_ids:
        victim = reg_ids[0]
        parts = doc_text.split("\n## ")
        cut = [parts[0]] + [p for p in parts[1:] if not p.startswith(victim)]
        _case("文档里删掉一整节（%s）" % victim,
              {DOC.resolve(): "\n## ".join(cut)})

    # ⑥ 文档某节里删掉「怎么交互测试」（同 victim ⇒ 必须是**那一节**里的那一句）
    if doc_text and reg_ids:
        victim = reg_ids[0]
        parts = doc_text.split("\n## ")
        cut = [parts[0]] + [
            (p.replace("怎么交互测试", "怎么用") if p.startswith(victim) else p)
            for p in parts[1:]]
        _case("文档某节里删掉「怎么交互测试」（%s）" % victim,
              {DOC.resolve(): "\n## ".join(cut)})

    # ⑦ 别名路由解析坏掉（即梦入口指向一个不存在的页）
    alias_text = _read(jimeng_alias)
    if alias_text:
        _case("别名路由解析到不存在的页",
              {jimeng_alias.resolve(): alias_text.replace(
                  'redirect("/jimeng/canvas/demo")',
                  'redirect("/no-such-page")')})

    ok = bool(cases) and all(c["went_red"] for c in cases)
    return {"n_cases": len(cases), "cases": cases, "ok": ok}


def _criteria(verdict, st):
    """⭐⭐⭐⭐⭐ 判据的**唯一一份实现** —— `main()` 与别处（verifier 的运行时那一格）
    都调它 ⇒ ⇒ ⇒ ⇒ ⇒ 而「同一个量只能有一份实现」⇒ ⇒ ⇒ ⇒ ⇒
    ⇒ ⇒ ⇒ ⇒ ⇒ 两处各写一份 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 迟早漂移 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而漂移了看不出来
    """
    return {
        "P1_the_route_universe_is_measured_from_the_filesystem_1033":
            bool(verdict["n_routes"] and verdict["n_canonical"]),
        "P2_every_finished_clone_page_is_reachable_from_the_site_root_1033":
            not verdict["unreachable_pages"],
        "P3_every_alias_route_resolves_to_a_reachable_page_1033":
            not verdict["bad_aliases"],
        "P4_the_registry_lists_every_real_page_and_nothing_else_1033":
            (not verdict["missing_in_registry"]
             and not verdict["phantom_in_registry"]),
        "P5_the_site_nav_links_to_every_clone_page_by_a_literal_href_1033":
            not verdict["missing_in_nav"],
        "P6_the_docs_say_how_to_reach_and_how_to_interact_test_each_page_1033":
            not verdict["doc_missing"],
        "P7_this_gate_can_actually_go_red_1033": bool(st["ok"]),
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true",
                        help="只跑注入式反证（不写产物）")
    # 1015 会带着 `--write-golden` 跑每一本 ⇒ 这个门必须**认**它
    parser.add_argument("--write-golden", action="store_true",
                        help="兼容 1015 的统一调用（本门永远写仓内产物）")
    args = parser.parse_args(argv)

    verdict = _judge()
    st = _selftest(verdict)

    crit = _criteria(verdict, st)

    print("— 1032-③ 克隆页可达性门")
    print("   真实路由 %d 个（规范 %d ＋ 别名 %d）｜可达 %d"
          % (verdict["n_routes"], verdict["n_canonical"], verdict["n_aliases"],
             verdict["n_reachable"]))
    print("   登记 %d 条｜站点导航链接 %d 条"
          % (len(verdict["registry"]), len(verdict["nav_links"])))
    print("   反证：%d 例，%s" % (st["n_cases"], "全过" if st["ok"] else "有漏网的"))
    if verdict["why"]:
        print("   ⭐ 不通过：%s" % "; ".join(verdict["why"]))
        for k in ("unreachable_pages", "missing_in_registry",
                  "phantom_in_registry", "missing_in_nav", "doc_missing"):
            if verdict.get(k):
                print("     %s: %s" % (k, ", ".join(verdict[k])))

    if args.selftest:
        for c in st["cases"]:
            print("     [%s] %s" % ("OK" if c["went_red"] else "FAIL", c["case"]))
        print("PROBE_1033_SELFTEST_OK" if st["ok"] else "PROBE_1033_SELFTEST_FAIL")
        return 0 if st["ok"] else 1

    payload = {
        "generated_by": SELF,
        "what_this_gate_asks": "**每一个已完成的克隆成果都必须从站点根目录 `/` 走得到**",
        "what_it_is_not": "⇒ ⇒ **这不是「页面好不好看」** ⇒ ⇒ 本门只问「有没有入口」"
                          "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而「入口在哪、长什么样」由文档与索引页负责",
        "measurements": {
            "n_routes": verdict["n_routes"],
            "n_canonical_pages": verdict["n_canonical"],
            "n_alias_routes": verdict["n_aliases"],
            "n_reachable": verdict["n_reachable"],
            "routes": verdict["routes"],
            "canonical_pages": verdict["canonical"],
            "alias_routes": verdict["aliases"],
            "unreachable_pages": verdict["unreachable_pages"],
            "bad_aliases": verdict["bad_aliases"],
            "registry": verdict["registry"],
            "missing_in_registry": verdict["missing_in_registry"],
            "phantom_in_registry": verdict["phantom_in_registry"],
            "site_nav_links": verdict["nav_links"],
            "missing_in_nav": verdict["missing_in_nav"],
            "docs_missing_sections": verdict["doc_missing"],
        },
        "selftest": {
            "n_cases": st["n_cases"],
            "cases": st["cases"],
            "ok": st["ok"],
        },
        "criteria_1033": crit,
        "criterion_kinds_1033": CRITERION_KINDS,
        "criterion_kinds_complete_1033": (set(CRITERION_KINDS) == set(crit)),
        "n_criteria_1033": len(crit),
        "rule": "⇒ ⇒ **三个量各记各的**：真实路由（实测）／源码可达集合（从 `/` 做 BFS）"
                "／真源登记（`src/lib/clonePages.ts`）⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 三者必须逐条对得上"
                "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒**",
        "scope_note": "⇒ ⇒ **口径**：「源码可达」是**过近似**"
                      "（import 闭包里出现过的站内链接都算）⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ 它抓的是「**忘了挂入口**」这类真实缺口"
                      "（链接是字面量写的、忘了就是真的没有）⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ 而它**不**保证「那个链接在运行时真的被点得到」"
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
                      "⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
    }
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
    bad = [k for k, v in crit.items() if v is False]
    print("   判据逐条 = %s" % " | ".join("%s=%s" % (k, crit[k]) for k in sorted(crit)))
    if bad:
        print("   P 为假的：%s" % ", ".join(sorted(bad)))
        return 1
    print("   P 为假的： 无 | 共 %d 条 P 判据" % len(crit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
