#!/usr/bin/env python3
"""即梦（jimeng.jianying.com）登录态捕获与无头复用的共享工具。

为什么把登录态显式落盘成 storageState，而不是让无头任务直接复用有头浏览器的
profile 目录：

1. Chrome 会**锁定** user-data-dir。有头登录窗口只要还开着，无头任务就无法以
   同一个 profile 再开一个浏览器；"后台无头执行任务"和"用户手动操作"必须能同时成立。
2. storageState（cookie + localStorage + IndexedDB）可以喂给任意一个新的、
   非持久的 browser context，互不干扰，也不用复制 150MB+ 的 profile。
3. 登录态是**凭证**，不能进 git 仓库。因此落盘在 ~/.jimeng-automation/ 而不是
   仓库里的任何目录（仓库 .gitignore 也不覆盖它，双保险）。

引擎选择：有头登录与无头任务都用**真实 Google Chrome**（channel="chrome"），
而不是 Playwright 自带的 Chromium。原因是登录态往往与浏览器版本/指纹相关，
用同一个引擎会话才不会被判定为异地登录而被踢下线。
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

# ---------------------------------------------------------------- 路径与常量

HOME = Path.home() / ".jimeng-automation"
PROFILE = HOME / "profile"          # 有头登录浏览器的 user-data-dir（独占）
STATE = HOME / "state.json"         # 捕获的登录态（凭证，chmod 600）
META = HOME / "state.meta.json"     # 捕获元信息：时间、cookie 名清单等
CDP_PORT = 9555                     # 避开 9222/9444（已被其他 Chrome 占用）

DEFAULT_URL = "https://jimeng.jianying.com/"
JIMENG_HOST = "jimeng.jianying.com"

# 与 scripts/jimeng-explore.mjs 保持一致：这些按钮会**提交按积分计费的任务**，
# 无头任务默认硬拦截；确实需要时由调用方显式 --allow-billed 放行。
BILLED_ACTIONS = [
    "生成", "发送", "局部重拍", "智能超清", "视频编辑", "补帧", "深度动作捕捉",
    "提示词反推", "智能改图", "配音", "音频生成", "立即创作", "确认生成",
]

# 登录后即梦首页应出现的文案（用于人工 sanity check，不作为唯一判据）
LOGGED_IN_TEXT_HINTS = ["AI画布", "我的作品", "创作", "智能画布", "首页"]

# 权威登录判据：字节 passport 账户信息接口。同源 fetch，自带 cookie。
# 未登录时稳定返回 {"data":{"user_id":0,"error_code":13,"description":"会话过期，请重新登录"}}
# 登录后 user_id > 0，可直接拿到昵称/头像。
# 为什么用接口而不是"页面上有没有'请先登录'"：文案判据极脆 —— 登录弹窗可能在 iframe 里、
# 可能文案改版、也可能首屏还没渲染完；而接口是服务端对 cookie 的裁决。
ACCOUNT_INFO_API = "/passport/account/info/v2/?aid=513695&account_sdk_source=web&sdk_version=2.2.6"

LAUNCH_ARGS = [
    f"--remote-debugging-port={CDP_PORT}",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-features=Translate",
]

CONTEXT_OPTIONS = {
    "viewport": {"width": 1512, "height": 950},
    "locale": "zh-CN",
    "timezone_id": "Asia/Shanghai",
}


def ensure_home() -> None:
    """创建凭证目录。700 权限：只有当前用户可读，避免 cookie 泄漏给本机其他账号。"""
    HOME.mkdir(parents=True, exist_ok=True)
    os.chmod(HOME, 0o700)


# ---------------------------------------------------------------- 登录态判据

# 强信号：出现即视为已登录（未登录时这些都不会有）
STRONG_SESSION_COOKIES = {
    "sessionid", "sessionid_ss", "sid_tt", "sid_guard", "passport_auth_status",
}
# 弱信号：未登录也可能被种下（ttwid/msToken/csrf 之类），必须叠加"页面无登录入口"
WEAK_SESSION_COOKIES = {
    "uid_tt", "odin_tt", "ttwid", "msToken", "passport_csrf_token", "s_v_web_id",
}
# 登录墙文案
LOGIN_WALL_TEXT = ["立即登录", "扫码登录", "验证码登录", "抖音登录", "手机号登录", "请先登录"]


def fetch_account_info(page, timeout_ms: int = 15_000) -> dict:
    """调 passport 账户信息接口，返回结构化账户状态。这是登录与否的权威来源。

    必须在**即梦页面内**执行（same-origin），否则 cookie 不会带上，接口永远回未登录。
    """
    try:
        raw = page.evaluate(
            """async ({api, timeout}) => {
              const ctl = new AbortController();
              const t = setTimeout(() => ctl.abort(), timeout);
              try {
                const r = await fetch(api, { credentials: 'include', signal: ctl.signal });
                return await r.text();
              } finally { clearTimeout(t); }
            }""",
            {"api": ACCOUNT_INFO_API, "timeout": timeout_ms},
        )
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200], "user_id": 0}

    try:
        payload = json.loads(raw)
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": "non-json response", "user_id": 0, "raw": str(raw)[:200]}

    d = payload.get("data") or {}
    return {
        "ok": True,
        "user_id": d.get("user_id") or 0,
        "error_code": d.get("error_code"),
        "message": str(d.get("description") or payload.get("message") or "").strip(),
        "name": d.get("name") or "",
        "nickname": d.get("nickname") or d.get("display_name") or "",
        "avatar": ((d.get("avatar") or {}).get("url")) if isinstance(d.get("avatar"), dict) else None,
    }


def account_is_logged_in(info: dict) -> bool:
    """user_id > 0 才算登录。error_code 13/未登录文案都归为未登录。"""
    return bool(info.get("ok")) and int(info.get("user_id") or 0) > 0



def pick_jimeng_page(ctx, prefer_url: str | None = None):
    """从 context 里挑一个最像"即梦主页面"的 tab。

    登录过程常会开新页（扫码、中间跳转），这里按 域名匹配 > 命中登录态 > 有内容
    的顺序打分，避免把用户停留在的空白页当成主页面。
    """
    pages = list(ctx.pages)
    if not pages:
        return None
    if prefer_url:
        for p in pages:
            if p.url == prefer_url:
                return p

    def score(p):
        s = 0
        if JIMENG_HOST in p.url:
            s += 10
        if "/login" not in p.url:
            s += 2
        try:
            s += min(len(p.content()), 200_000) // 20_000  # 粗略衡量"有内容"
        except Exception:  # noqa: BLE001 - 导航中的页面可能取不到
            pass
        return s

    return max(pages, key=score)


def login_probe(ctx, page=None) -> dict:
    """只读探测登录态。返回结构化结果，不抛异常（导航竞态属正常）。

    判据优先级：passport 接口的 user_id > 强 session cookie > DOM 文案。
    **绝不能**用"页面上没看到登录入口"来推断已登录 —— 未登录首屏可能恰好没渲染出
    登录弹窗（实测即梦就是如此，会造成假阳性）。
    """
    page = page or pick_jimeng_page(ctx)
    out = {
        "url": None, "title": None, "logged_in": False,
        "strong_cookies": [], "weak_cookies": [],
        "login_wall": [], "pages": len(ctx.pages),
        "account": {"ok": False, "user_id": 0},
    }
    if page is None:
        return out

    try:
        out["url"] = page.url
        out["title"] = page.title()
    except Exception:  # noqa: BLE001
        pass

    names = {c["name"] for c in ctx.cookies()}
    out["strong_cookies"] = sorted(names & STRONG_SESSION_COOKIES)
    out["weak_cookies"] = sorted(names & WEAK_SESSION_COOKIES)

    # 权威判据：必须在即梦同源页面里发这个请求
    if page.url.startswith("https://" + JIMENG_HOST):
        acct = fetch_account_info(page)
        out["account"] = acct
        if account_is_logged_in(acct):
            out["logged_in"] = True

    try:
        text = page.evaluate("() => document.body ? document.body.innerText : ''")
    except Exception:  # noqa: BLE001
        text = ""
    out["login_wall"] = [w for w in LOGIN_WALL_TEXT if w in text]

    # 兜底：接口不可用（页面还在跳转 / 非同源）时，才退回 cookie 判据。
    # 注意只认强 cookie，弱 cookie（ttwid 等）未登录也会被种下，不能作为依据。
    if not out["account"].get("ok") and out["strong_cookies"]:
        out["logged_in"] = True
    return out



def summarize_state(state: dict) -> str:
    """把 storageState 摘要成可读文本。**只列 cookie 名，绝不打印 cookie 值**。"""
    lines = [f"origins: {len(state.get('origins') or [])}"]
    for o in state.get("origins") or []:
        ls = o.get("localStorage") or []
        idb = o.get("indexedDB") or []
        lines.append(
            f"  - {o.get('origin')}: localStorage={len(ls)} indexedDB={len(idb)}"
        )
    cookies = state.get("cookies") or []
    lines.append(f"cookies: {len(cookies)}")
    for c in cookies:
        bits = [c.get("name", "?")]
        if c.get("domain"):
            bits.append(c["domain"])
        if c.get("expires", -1) and c["expires"] > 0:
            bits.append(time.strftime("%Y-%m-%d %H:%M", time.localtime(c["expires"])))
        else:
            bits.append("session")
        lines.append("  " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------- 捕获与复用

def _harvest_local_storage(ctx) -> list:
    """手动补采各页面的 localStorage。

    为什么需要：Playwright 自开的 persistent context 能直接吐出 origins，但
    **connect_over_cdp 附加**到已在运行的浏览器时，storage_state() 只返回 cookie，
    origins 恒为空。cookie 足够维持登录，但 localStorage 里存着主题/模型偏好/
    引导标记，补上能让无头页面更接近用户真实环境。
    """
    harvested = []
    for page in ctx.pages:
        try:
            if not page.url.startswith(f"https://{JIMENG_HOST}"):
                continue
            origin = page.url.split("?")[0].split("#")[0]
            origin = "/".join(origin.split("/")[:3])  # scheme://host
            items = page.evaluate(
                """() => Object.keys(localStorage).map((k) => ({
                     name: k, value: String(localStorage.getItem(k))
                   }))"""
            )
        except Exception:  # noqa: BLE001
            continue
        if items:
            harvested.append({"origin": origin, "localStorage": items})
    return harvested


def capture_state(ctx, path: Path = STATE, meta_path: Path = META) -> dict:
    """把当前 context 的登录态写盘。含 IndexedDB —— 即梦部分登录标记存在那里。"""
    ensure_home()
    path = Path(path)
    # 注意 kwarg 拼写：Python **同步** API 是 indexed_db（下划线），
    # 异步 _impl 里才是驼峰 indexedDB。拼错会 TypeError 并静默退化成"丢掉 localStorage"。
    try:
        state = ctx.storage_state(path=str(path), indexed_db=True)
        idb_included = True
    except TypeError:
        # 旧版 Playwright 不支持该 kwarg，退化为 cookie+localStorage
        state = ctx.storage_state(path=str(path))
        idb_included = False

    if not (state.get("origins") or []):
        extra = _harvest_local_storage(ctx)
        if extra:
            state["origins"] = extra
            path.write_text(json.dumps(state))
            os.chmod(path, 0o600)

    os.chmod(path, 0o600)
    meta = {
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "indexed_db_included": idb_included,
        "cookie_count": len(state.get("cookies") or []),
        "cookie_names": sorted({c.get("name", "") for c in state.get("cookies") or []}),
        "origins": [o.get("origin") for o in (state.get("origins") or [])],
    }
    meta_path = Path(meta_path)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    os.chmod(meta_path, 0o600)
    return state


def open_headless(playwright, state_path: Path = STATE, headless: bool = True):
    """用捕获的登录态开一个全新的无头 context。返回 (browser, context, page)。

    与有头 profile 完全隔离，不触碰 ~/.jimeng-automation/profile。
    """
    state_path = Path(state_path)
    if not state_path.exists():
        raise FileNotFoundError(
            f"未找到登录态文件 {state_path}；请先运行 scripts/jimeng_login_capture.py 完成登录。"
        )
    browser = playwright.chromium.launch(
        channel="chrome",  # 真实 Chrome：与登录时同引擎，避免风控判定异地登录
        headless=headless,
        args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(storage_state=str(state_path), **CONTEXT_OPTIONS)
    context.set_default_timeout(30_000)
    page = context.new_page()
    return browser, context, page


def verify_login(context, page=None, url: str = DEFAULT_URL) -> dict:
    """无头侧校验登录态是否仍然有效（cookie 过期/被踢下线时会失败）。"""
    page = page or pick_jimeng_page(context)
    if page is None:
        return {"logged_in": False, "reason": "no page", "account": {}}
    if not page.url.startswith(f"https://{JIMENG_HOST}"):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        except Exception as e:  # noqa: BLE001
            return {"logged_in": False, "reason": f"goto failed: {str(e)[:120]}", "account": {}}
    page.wait_for_timeout(2500)
    out = login_probe(context, page)
    if not out["logged_in"]:
        acct = out.get("account") or {}
        out["reason"] = (
            f"passport 未登录（user_id={acct.get('user_id')}, "
            f"error_code={acct.get('error_code')}, msg={acct.get('message') or acct.get('error')!r}）"
        )
    return out



# ---------------------------------------------------------------- 计费护栏

def assert_not_billed_action(text: str, allow_billed: bool = False) -> None:
    """命中计费关键词即拒绝。默认硬拦截，与 jimeng-explore.mjs 的约定一致。"""
    if allow_billed or not text:
        return
    for kw in BILLED_ACTIONS:
        if kw in text:
            raise RuntimeError(
                f"拒绝执行：命中计费关键词「{kw}」（原文：{text.strip()[:80]}）。"
                "即梦的生成类操作按积分计费，确认要花积分再加 --allow-billed。"
            )
