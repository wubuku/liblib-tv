#!/usr/bin/env bash
# ============================================================
# LibTV 画布用户手册 —— 站点一键构建脚本
#
# 用法:
#   ./build-site.sh            # 构建静态站点到 .vitepress/dist/
#   ./build-site.sh --preview  # 构建完成后启动本地预览(:4173)
#
# 产物: .vitepress/dist/  —— 纯静态，整体拷贝到任意 Web 服务器即可发布
#
# 说明：任一步失败立即退出。构建过程完全透明，每步都打印统计。
# 与同仓 tdcanvas-canvas 的 build-site.sh 的差别：那份已经长到 12 道 Python
# 门禁（锚点、结构闭环、评级一致性、强断言、订正回归…），是 100+ 批次逐步长出来的，
# 依赖 scripts/ 下十几个自建脚本。本手册还没有那些脚本，硬抄过来只会得到一个
# 「第一步就找不到脚本」的构建。所以这里只放**本目录真能跑**的四道校验：
#   1. 页面/截图数量下限
#   2. 侧边栏覆盖率（每篇正文都得能在导航里找到）
#   3. 产物无残留 .md 链接
#   4. 产物无死链（href 指向的 .html 真实存在）
# 后续如果需要更强的门禁，照着 tdcanvas 的路子逐步加，别一次抄完。
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TS="$(date +%H:%M:%S)"
log()  { printf '\033[1;34m[build %s]\033[0m %s\n' "$TS" "$*"; }
ok()   { printf '\033[1;32m[  ok  %s]\033[0m %s\n' "$TS" "$*"; }
warn() { printf '\033[1;33m[ warn %s]\033[0m %s\n' "$TS" "$*"; }
fail() { printf '\033[1;31m[ FAIL %s]\033[0m %s\n' "$TS" "$*" >&2; exit 1; }

log "══════ LibTV 画布用户手册 · 站点构建开始 ══════"
log "工作目录: $SCRIPT_DIR"

# ---------- 步骤 1/6 环境检查 ----------
log "步骤 1/6 环境检查"
command -v node >/dev/null 2>&1 || fail "未找到 node，请先安装 Node.js 18+（https://nodejs.org）"
command -v npm  >/dev/null 2>&1 || fail "未找到 npm，请确认 Node.js 安装完整"
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAJOR" -ge 18 ] || fail "Node 版本过低: $(node -v)，需要 18+"
ok "node $(node -v) / npm $(npm -v)"
[ -f ".vitepress/config.mjs" ] || fail "缺少 .vitepress/config.mjs（站点配置文件）"
[ -f "README.md" ] || fail "缺少 README.md（站点首页内容）"
ok "站点配置与首页内容齐备"

# ---------- 步骤 2/6 依赖安装 ----------
if [ ! -d node_modules/vitepress ]; then
  log "步骤 2/6 安装构建依赖 vitepress（首次较慢，来自 npm registry）"
  npm install --no-audit --no-fund
  ok "依赖安装完成"
else
  log "步骤 2/6 构建依赖已就绪（node_modules/vitepress 已存在，跳过安装）"
fi
ok "vitepress 版本: $(node -p "require('vitepress/package.json').version")"

# ---------- 步骤 3/6 内容清单 ----------
log "步骤 3/6 统计手册内容"
MD_COUNT="$(find . -maxdepth 2 -name '*.md' \
  ! -path './node_modules/*' ! -path './.vitepress/*' \
  ! -name 'AUDIT.md' ! -name 'PROGRESS.md' ! -name 'PUBLISH.md' | wc -l | tr -d ' ')"
PNG_COUNT="$(find screenshots -name '*.png' 2>/dev/null | wc -l | tr -d ' ')"
[ "$MD_COUNT" -ge 15 ] || fail "Markdown 页面数异常（$MD_COUNT < 15），内容可能缺失"
[ "$PNG_COUNT" -ge 20 ] || fail "screenshots/ 下截图过少（$PNG_COUNT < 20）"
ok "将发布 $MD_COUNT 个页面、$PNG_COUNT 张截图（工作账本已排除）"

# 手册的机械完整性交给方法论自带的审计脚本，那道闸才认得 task-inventory 的 schema。
# 站点脚本不重复实现它 —— 两边各查一半、谁都不全，不如只留一处权威。
SKILL_AUDIT="../../../.agents/skills/web-studio-user-manual/scripts/audit_manual.py"
if [ -f "$SKILL_AUDIT" ] && command -v python3 >/dev/null 2>&1; then
  if python3 "$SKILL_AUDIT" . --phase gate-a >/dev/null 2>&1; then
    ok "手册 Gate A 机械审计通过（18 任务 / 页面 / 截图三方一致）"
  else
    fail "手册 Gate A 审计未通过，先修手册再构建：
$(python3 "$SKILL_AUDIT" . --phase gate-a 2>&1 | grep -iE '^(ERROR|FAIL)' | head -20)"
  fi
else
  warn "找不到 audit_manual.py 或 python3，跳过 Gate A 校验"
fi

# ---------- 步骤 4/6 清理旧产物 ----------
log "步骤 4/6 清理旧构建产物"
rm -rf .vitepress/dist .vitepress/cache
ok "已清理 .vitepress/dist 与 .vitepress/cache"

# ---------- 步骤 5/6 构建 ----------
log "步骤 5/6 执行 vitepress build（client + server 双端打包、页面渲染）"
npx vitepress build
[ -f ".vitepress/dist/index.html" ] || fail "构建未生成 dist/index.html"
ok "构建完成"

# ---------- 步骤 6/6 产物校验 ----------
log "步骤 6/6 产物校验"
DIST_HTML="$(find .vitepress/dist -name '*.html' | wc -l | tr -d ' ')"
DIST_PNG="$(find .vitepress/dist -name '*.png' | wc -l | tr -d ' ')"
DIST_SIZE="$(du -sh .vitepress/dist | cut -f1 | tr -d '[:space:]')"
ok "dist 页面数: ${DIST_HTML}（含 index 与 404）"
ok "dist 截图数: $DIST_PNG"
ok "dist 总体积: $DIST_SIZE"

# 校验 1：不该有指向 .md 的原始链接（VitePress 会把 md 链接改写成 .html）
RAW_MD_LINKS="$(grep -RhoE 'href="[^"]*\.md"' .vitepress/dist --include='*.html' | wc -l | tr -d ' ' || true)"
if [ "$RAW_MD_LINKS" -ne 0 ]; then
  fail "产物里有 $RAW_MD_LINKS 处指向 .md 的原始链接（没被改写成 .html）"
fi
ok "无残留 .md 原始链接"

# 校验 2：侧边栏覆盖率。
# 漏收的页面读者只能靠页内链接抵达，导航形同虚设 —— 而 build 本身不会报错。
MISSING_SIDEBAR=""
for f in $(find . -name '*.md' -not -path './node_modules/*' -not -path './.vitepress/*' \
  -not -name 'README.md' -not -name 'PUBLISH.md' \
  -not -name 'AUDIT.md' -not -name 'PROGRESS.md'); do
  slug="${f#./}"; slug="${slug%.md}"
  grep -q "'/$slug'" .vitepress/config.mjs || MISSING_SIDEBAR="$MISSING_SIDEBAR $slug"
done
if [ -n "$MISSING_SIDEBAR" ]; then
  fail "以下页面未收录进 config.mjs 侧边栏，读者无法从导航抵达:$MISSING_SIDEBAR"
fi
ok "所有已发布页面均已收录进侧边栏"

# 校验 3：产物死链。
# 「链接被正确改写成 .html」不等于「它指向的东西存在」——前者查格式，后者查事实。
# srcExclude 排除掉的页面仍会被改写成 .html，于是产物里会躺着指向 PUBLISH.html 的死链。
DEAD_LINKS="$(python3 - <<'PY'
import os, re, sys
dist = '.vitepress/dist'
dead = []
for root, _, files in os.walk(dist):
    for fn in files:
        if not fn.endswith('.html'):
            continue
        p = os.path.join(root, fn)
        html = open(p, encoding='utf-8', errors='ignore').read()
        for href in re.findall(r'href="([^"#?]+\.html)(?:[#?][^"]*)?"', html):
            if href.startswith(('http://', 'https://', '//', 'mailto:')):
                continue
            # href 以 / 开头是 **base 相对**（config 里 base:'/'），必须从 dist 根解析；
            # 直接 join(root, href) 会被 os.path.join 丢掉 root，结果去文件系统根找，
            # 每一个站内链接都会误报成死链 —— 这条校验第一版就是这么错的。
            if href.startswith('/'):
                target = os.path.normpath(os.path.join(dist, href.lstrip('/')))
            else:
                target = os.path.normpath(os.path.join(root, href))
            if not os.path.exists(target):
                dead.append(f'{p} → {href}')
print('\n'.join(dead[:20]))
sys.exit(1 if dead else 0)
PY
)" && { ok "产物无死链"; } || { fail "产物中存在死链：
$DEAD_LINKS"; }

# 校验 4：加粗有没有在产物里失效。
#
# 2026-10-02 实测：源文件写着 `…的**「角色造型室」等图标会被压住**。`，
# 收尾的 `**` 紧跟中文句号，CommonMark 的右闭合判定不成立 → 整段加粗失效，
# 产物里留下**字面量 `**`**。**源文件完全正常，前四道校验全部报 ok**，
# 只有把产物打开、把标签剥掉看纯文本才看得见。
#
# 这里刻意**不去静态扫源文件**：试过，规则「`**` 紧邻标点」会误报 500+ 处，
# 绝大多数其实是好的。用产物说话才是准的。
LITERAL_BOLD="$(python3 - <<'PY2'
import html, os, re, sys
dist = '.vitepress/dist'
hits = []
for root, _, files in os.walk(dist):
    for fn in files:
        if not fn.endswith('.html'):
            continue
        p = os.path.join(root, fn)
        doc = open(p, encoding='utf-8', errors='ignore').read()
        # 只看正文区域：<main> 之外还有侧边栏/页脚，加噪
        m = re.search(r'<main[^>]*>(.*?)</main>', doc, re.S)
        body = m.group(1) if m else doc
        text = html.unescape(re.sub(r'<[^>]+>', ' ', body))
        for mm in re.finditer(r'\*\*', text):
            hits.append(f'{p}: {text[max(0, mm.start()-40):mm.start()+40].strip()}')
            break
print('\n'.join(hits[:10]))
sys.exit(1 if hits else 0)
PY2
)" && { ok "产物中无失效加粗（无字面量 **）"; } || { fail "产物里出现字面量 ** —— 有加粗在渲染后失效了，通常是 ** 紧邻中文标点：
$LITERAL_BOLD"; }

# 校验 5：截图是否真的进了产物。
# 少一张通常意味着某页 Markdown 引用了不存在的图 —— 正文里就是一块裂图。
[ "$DIST_PNG" -eq "$PNG_COUNT" ] || fail "产物截图数 $DIST_PNG 与源目录 $PNG_COUNT 不一致，有图没被打包"
ok "全部 $DIST_PNG 张截图均已打包进产物"

# ---------- 完成 ----------
log "════════════════════════════════════════════"
ok "构建成功！发布产物: $SCRIPT_DIR/.vitepress/dist"
ok "发布方式: 把上述 dist 目录整体拷贝到任意静态 Web 服务器（详见 PUBLISH.md）"
if [ "${1:-}" = "--preview" ]; then
  log "启动本地预览 http://localhost:4173 （Ctrl+C 结束）"
  exec npx vitepress preview --port 4173
fi
ok "本地预览: ./build-site.sh --preview"
