#!/usr/bin/env bash
# ============================================================
# 即梦画布用户手册 —— 站点一键构建脚本
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

log "══════ 即梦画布用户手册站点 · 一键构建开始 ══════"
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
  ! -name 'TEST_MEDIA_ASSETS.md' ! -name 'SOURCE_OBSERVATIONS.md' \
  ! -name 'PUBLISH.md' | wc -l | tr -d ' ')"
PNG_COUNT="$(find screenshots -name '*.png' 2>/dev/null | wc -l | tr -d ' ')"
[ "$MD_COUNT" -ge 15 ] || fail "Markdown 页面数异常（$MD_COUNT < 15），内容可能缺失"
[ "$PNG_COUNT" -ge 20 ] || fail "screenshots/ 下没有截图"
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
  ok "无 .md 残留链接"
fi
if [ "$DIST_PNG" -ne "$PNG_COUNT" ]; then
  warn "dist 截图数不一致: dist=$DIST_PNG, 源=$PNG_COUNT —— 未被 md 引用的截图会被构建静默丢弃，请核对 manifest 引用"
else
  ok "截图数与源一致: $PNG_COUNT"
fi

# SVG 示意图校验：Vite 会把被引用的 SVG 内联为 data URI（不落到 dist/assets），
# 未被引用的则直接消失。两者都体现在 dist 的 .svg 文件数上，因此「数文件」无法发现
# 丢失——必须逐个确认每个示意图确实出现在了构建产物里。
# 内联后文件名不可见，改用 alt 文本作为稳定锚点：每个示意图在正文都有唯一 alt。
SVG_COUNT="$(find screenshots -name '*.svg' 2>/dev/null | wc -l | tr -d ' ')"
if [ "$SVG_COUNT" -gt 0 ]; then
  SVG_MISSING=0
  while IFS= read -r alt; do
    [ -z "$alt" ] && continue
    if ! grep -rqF "$alt" .vitepress/dist --include='*.html'; then
      warn "示意图未出现在构建产物中（可能被静默丢弃）：$alt"
      SVG_MISSING=$((SVG_MISSING + 1))
    fi
  done < <(awk '/^  - file: screenshots\/diagrams\/.*\.svg$/{insvg=1;next} insvg&&/^    alt: /{sub(/^    alt: /,"");print;insvg=0}' screenshots/manifest.yml)
  if [ "$SVG_MISSING" -eq 0 ]; then
    ok "示意图均已进入构建产物: $SVG_COUNT"
  else
    warn "有 $SVG_MISSING 个示意图未进入产物，请核对其 md 引用路径"
  fi

  # manifest 的 alt 必须与正文引用处的 alt 逐字一致：上面的示意图校验正是以 alt
  # 为锚点，两者不一致会把「已正确引用」误判为「丢失」。此处提前对齐。
  ALT_MISMATCH=0
  while IFS= read -r a; do
    [ -z "$a" ] && continue
    if ! grep -rqF "![$a](" --include='*.md' . 2>/dev/null; then
      ALT_MISMATCH=$((ALT_MISMATCH + 1))
    fi
  done < <(awk '/^  - file: screenshots\/diagrams\/.*\.svg$/{f=1;next} f&&/^    alt: /{sub(/^    alt: /,"");print;f=0}' screenshots/manifest.yml)
  if [ "$ALT_MISMATCH" -eq 0 ]; then
    ok "示意图 alt 与正文引用逐字一致"
  else
    warn "有 $ALT_MISMATCH 个示意图的 manifest alt 与正文 alt 不一致，请同步 screenshots/manifest.yml"
  fi
fi

log "══════ 构建结束 ══════"
log "产物目录: $SCRIPT_DIR/.vitepress/dist（整体拷贝即可发布，详见 PUBLISH.md）"

if [ "${1:-}" = "--preview" ]; then
  log "启动本地预览: http://localhost:4173 （Ctrl+C 结束）"
  log "提示: vite preview 启动时缓存文件清单，重新构建后必须重启预览进程"
  npx vitepress preview
fi
