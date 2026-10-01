#!/usr/bin/env bash
# ============================================================
# BeefTV 用户手册 —— 站点一键构建脚本
#
# 用法:
#   ./build-site.sh            # 构建静态站点到 .vitepress/dist/
#   ./build-site.sh --preview  # 构建完成后自动启动本地预览(:4173)
#
# 产物: .vitepress/dist/（纯静态，整体拷贝到任意 Web 服务器即可发布）
# 说明: 每一步都打印进度与统计，构建过程完全透明；任一步失败立即退出。
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TS="$(date +%H:%M:%S)"
log()  { printf '\033[1;34m[build %s]\033[0m %s\n' "$TS" "$*"; }
ok()   { printf '\033[1;32m[  ok  %s]\033[0m %s\n' "$TS" "$*"; }
warn() { printf '\033[1;33m[ warn %s]\033[0m %s\n' "$TS" "$*"; }
fail() { printf '\033[1;31m[ FAIL %s]\033[0m %s\n' "$TS" "$*" >&2; exit 1; }

log "══════ BeefTV 用户手册站点 · 一键构建开始 ══════"
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
  log "步骤 2/6 依赖已就绪（node_modules/vitepress 已存在，跳过安装）"
fi
VP_VERSION="$(node -p "require('vitepress/package.json').version")"
ok "vitepress 版本: $VP_VERSION"

# ---------- 步骤 3/6 内容清单 ----------
log "步骤 3/6 统计手册内容"
MD_COUNT="$(find . -maxdepth 2 -name '*.md' \
  ! -path './node_modules/*' ! -path './.vitepress/*' \
  ! -name 'AUDIT.md' ! -name 'PROGRESS.md' \
  ! -name 'TEST_MEDIA_ASSETS.md' ! -name 'SOURCE_OBSERVATIONS.md' | wc -l | tr -d ' ')"
PNG_COUNT="$(find screenshots -name '*.png' 2>/dev/null | wc -l | tr -d ' ')"
[ "$MD_COUNT" -ge 20 ] || fail "Markdown 页面数异常（$MD_COUNT < 15），内容可能缺失"
[ "$PNG_COUNT" -ge 10 ] || fail "screenshots/ 下没有截图"
ok "将发布 $MD_COUNT 个页面、$PNG_COUNT 张截图（内部资料已排除）"

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
DIST_SIZE="$(du -sh .vitepress/dist | cut -f1)"
ok "dist 页面数: ${DIST_HTML} (含 index 与 404)"
ok "dist 截图数: $DIST_PNG"
ok "dist 总体积: $DIST_SIZE"
RAW_MD_LINKS="$(grep -RhoE 'href="[^"]*\.md"' .vitepress/dist --include='*.html' | wc -l | tr -d ' ' || true)"
if [ "$RAW_MD_LINKS" -ne 0 ]; then
  warn "发现 $RAW_MD_LINKS 处指向 .md 的原始链接（未被改写为 .html），请检查对应页面"
else
  ok "无残留 .md 原始链接"
fi

# 站内死链检查：VitePress 的 ignoreDeadLinks 会放过指向 srcExclude 文件的链接
# （如被排除的 PUBLISH.md / task-inventory.yml），发布后就是 404。逐个解析 href 兜底。
DEAD_REPORT="$(python3 - <<'PYEOF' 2>/dev/null || true
import os, re
from urllib.parse import urldefrag
DIST = ".vitepress/dist"
exists = set()
for root, _, files in os.walk(DIST):
    for f in files:
        exists.add(os.path.relpath(os.path.join(root, f), DIST))
dead = set()
for root, _, files in os.walk(DIST):
    for f in files:
        if not f.endswith(".html"):
            continue
        page = os.path.relpath(os.path.join(root, f), DIST)
        base = os.path.dirname(page)
        with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
            html = fh.read()
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http", "mailto:", "data:")) or href.startswith("#"):
                continue
            target = urldefrag(href)[0]
            if not target:
                continue
            target = target.lstrip("/") if target.startswith("/") else os.path.normpath(os.path.join(base, target))
            target = target.replace("\\", "/")
            # "/" 与 "./" 都解析到站点根 index.html
            if target in ("", ".", ".."):
                target = "index.html"
            if target.endswith("/"):
                target += "index.html"
            if target not in exists:
                dead.add(f"{page} -> {href}")
print(len(dead))
for d in sorted(dead):
    print(d)
PYEOF
)"
DEAD_COUNT="$(printf '%s\n' "$DEAD_REPORT" | head -1 | tr -dc '0-9')"
DEAD_COUNT="${DEAD_COUNT:-0}"
if [ "$DEAD_COUNT" -ne 0 ]; then
  printf '%s\n' "$DEAD_REPORT" | tail -n +2 | while IFS= read -r line; do
    [ -n "$line" ] && warn "死链 $line"
  done
  fail "站内死链 $DEAD_COUNT 处——指向被 srcExclude 排除的文件最常见"
else
  ok "站内链接全部可达（逐个 href 解析核对）"
fi

# 截图对账闸：源目录 screenshots/ ↔ manifest.yml ↔ 已发布页面引用 ↔ dist 产物，四侧必须一致。
# 背景（Batch 94）：17-light-mode.png 库里有、manifest 登记着、账本也引用着，唯独发布页
# 不再引用它——重写该页时图片被「替换」而非「补入」。单看任一侧都发现不了，只有四方
# 摊平比对才能揪出「证据在库但读者看不到」。详见 scripts/verify-screenshots.py。
if SHOT_OUT="$(python3 scripts/verify-screenshots.py 2>&1)"; then
  ok "$SHOT_OUT"
else
  printf '%s\n' "$SHOT_OUT" | while IFS= read -r line; do
    [ -n "$line" ] && warn "截图 $line"
  done
  fail "截图对账不一致——孤儿图意味着证据在库但页面不展示，读者看不到"
fi

# 端点核对闸：20-reference.md 声明的 REST 端点 vs 上游生产路由注册。
# 背景（Batch 96）：手册曾把 6 条 /agent/* 当现存接口教读者排查，而上游根本没注册
# ——教用户去调不存在的接口，比漏写更糟，会把排障方向整体带偏。
# 找不到 BeefTV 源码时脚本静默跳过，手册构建不依赖同级仓库。
if EP_OUT="$(python3 scripts/verify-endpoints.py 2>&1)"; then
  ok "$EP_OUT"
else
  printf '%s\n' "$EP_OUT" | while IFS= read -r line; do
    [ -n "$line" ] && warn "端点 $line"
  done
  fail "REST 端点声明与上游生产路由不一致——详见上方"
fi

# 快捷键前缀闸：手册里指向「必须带 Ctrl/Cmd 的键」的写法是否都带了前缀。
# 背景（Batch 110）：同一缺陷在两处出现过（Batch 97 导演台页、Batch 107 画布页
# 都把重做写成 Shift+Z，漏了 Ctrl/Cmd）。表格看着完整、语义也说得通，只有拿每行
# 去和源码绑定条件比对才暴露，故闸门化。
if SC_OUT="$(python3 scripts/verify-shortcuts.py 2>&1)"; then
  ok "$SC_OUT"
else
  printf '%s\n' "$SC_OUT" | while IFS= read -r line; do
    [ -n "$line" ] && warn "快捷键 $line"
  done
  fail "快捷键修饰键前缀缺失——带 Ctrl/Cmd 的键被写成了裸键"
fi

# excluded 解禁条件闸：账本里「这页还差什么才能补」的判断，是否与上游现状一致。
# 背景（Batch 111）：这类条件最危险的失效方式是悄悄过期——上游可能已解禁（或已
# 彻底移除），而账本仍写旧理由，于是「什么时候能补这一页」的判断从此失准。
if EX_OUT="$(python3 scripts/verify-exclusions.py 2>&1)"; then
  ok "$EX_OUT"
else
  printf '%s\n' "$EX_OUT" | while IFS= read -r line; do
    [ -n "$line" ] && warn "解禁条件 $line"
  done
  fail "excluded 任务的解禁条件可能已失效——需回走验证并更新 PROGRESS 条件表"
fi

# 第五道闸：标签漂移核对（Batch 121）
# 背景：同一轮审计连续四次撞上「同一个设置有多个叫法」（Batch 116/117/119/120）。
# 产品里多个文件各持一份同义枚举表，改一处忘另一处就会漂移。本闸维护一份
# 「已知分歧登记表」，出现未登记的新分歧、或登记的分歧已收敛，都以退出码 1 报出。
# 判据与边界写在脚本 docstring 里，务必连着一读。
if LD_OUT="$(python3 scripts/verify-label-drift.py 2>&1)"; then
  ok "$LD_OUT"
else
  printf '%s\n' "$LD_OUT" | while IFS= read -r line; do
    [ -n "$line" ] && warn "标签漂移 $line"
  done
  fail "存在未登记的标签漂移，或已登记的分歧已被上游统一——需更新 verify-label-drift.py 的登记表"
fi

# ---------- 完成 ----------
log "════════════════════════════════════════════"
ok "构建成功！发布产物: $SCRIPT_DIR/.vitepress/dist"
ok "发布方式: 将上述 dist 目录整体拷贝到任意静态 Web 服务器（详见 PUBLISH.md）"
if [ "${1:-}" = "--preview" ]; then
  log "启动本地预览 http://localhost:4173 （Ctrl+C 结束）"
  exec npx vitepress preview --port 4173
fi
ok "本地预览: ./build-site.sh --preview  或  python3 -m http.server 4173 -d .vitepress/dist"
