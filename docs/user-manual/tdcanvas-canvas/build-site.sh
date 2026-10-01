#!/usr/bin/env bash
# ============================================================
# TDCanvas 用户手册 —— 站点一键构建脚本
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

log "══════ TDCanvas 用户手册站点 · 一键构建开始 ══════"
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
[ "$MD_COUNT" -ge 15 ] || fail "Markdown 页面数异常（$MD_COUNT < 15），内容可能缺失"
[ "$PNG_COUNT" -ge 20 ] || fail "screenshots/ 下没有截图"
ok "将发布 $MD_COUNT 个页面、$PNG_COUNT 张截图（内部资料已排除）"

# 内部锚点校验：VitePress 会把标题里的全角括号、逗号、斜杠、引号统统折成 `-`，
# 手写锚点极易对不上（2026-10-01 M31 实测：4 处交叉引用全部落空）。
# 坏锚点是硬缺陷——读者点「见 20-reference.md 某节」会直接扑空，故此处 fail 而非 warn。
command -v python3 >/dev/null 2>&1 || fail "未找到 python3，无法执行内部锚点校验"
ANCHOR_OUT="$(python3 scripts/check-anchors.py . 2>&1)" || fail "内部锚点校验未通过：
$ANCHOR_OUT"
echo "$ANCHOR_OUT" | sed 's/^/  /'

# 结构闭环校验：任务页 ↔ task-inventory.yml ↔ 10-tasks/README.md 索引 ↔ 侧边栏。
# 2026-10-01 M42 负向测试实测：往 10-tasks/ 塞一个没登记的「孤儿页」，
# audit_manual.py 退出码 0、构建也只 warn 一句就通过——孤儿页可以完全不出现在
# 账本与索引里就混进发布产物；从索引删掉一条已有任务页同样无人拦截。
# 这类问题不会让构建失败，但会让手册的任务结构悄悄失真，故此处 fail 而非 warn。
STRUCT_OUT="$(python3 scripts/check-structure.py . 2>&1)" || fail "结构闭环校验未通过：
$STRUCT_OUT"
echo "$STRUCT_OUT" | sed 's/^/  /'

# 强断言校验：正文里出现「逐字 / 完全一致 / 一一对应」这类话的小节，
# 必须在同一节里写明凭什么这么说（实测 / 复核 / 对拍 / 源码 / 抓取 / 逐条 / 回归）。
# 2026-10-01 M44 实测：shortcuts-help 曾写「键位速查（与弹窗逐字一致）」，
# 实际混进了 3 条弹窗没有的条目、还把「剪切板」写成「剪贴板」，而手册自己的
# 截图就证伪了它自己的表格。这类错误靠人眼复核极易放过——写的时候手里有截图，
# 但没人回头把文字和截图逐条对一遍。故此处 fail 而非 warn。
CLAIM_OUT="$(python3 scripts/check-claims.py . 2>&1)" || fail "强断言校验未通过（存在没写明证据的强断言）：
$CLAIM_OUT"
echo "$CLAIM_OUT" | sed 's/^/  /'

# 订正回归：M47 订正「导出 zip 可恢复画布」时只改了审计点名的 3 个文件，
# 漏了 30-concepts 与 undo-persistence 里重复同样错误说法的地方——**改一处
# 事实错误的风险不在于改错，而在于漏改**。这里把每次订正登记成撤回记录，
# 确认那些错误原句没有重新长出来。
RETRACT_OUT="$(python3 scripts/check-retractions.py . 2>&1)" || fail "订正回归校验未通过（已订正的错误说法又出现了）：
$RETRACT_OUT"
echo "$RETRACT_OUT" | sed 's/^/  /'

# 门禁自检：注入 15 类故障，断言每道门禁**以正确的理由**失败。
# 2026-10-01 M41/M42 实测：锚点门禁在 236 个标题里错判 29 个却一直报「全部有效」，
# 孤儿页与索引漏条两类问题两道门禁全都放行——门禁自己坏了不会喊疼。
# 这里断言的是**错误内容**而不只是退出码：只看退出码会被「变异脚本写歪了」
# 和「以错误理由失败」两种假阳性骗过去（探针误删 .vitepress 那次就差点中招）。
# 全量约 3 秒（随机器有波动），成本可忽略，故每次构建都跑。
SELFTEST_OUT="$(python3 scripts/selftest-gates.py . 2>&1)" || fail "门禁自检未通过（存在形同虚设的门禁）：
$SELFTEST_OUT"
echo "$SELFTEST_OUT" | grep -E '^\s*\[ ok \]|^---' | sed 's/^/  /'

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
ok "dist 页面数: ${DIST_HTML} (含 index 与 404)"
ok "dist 截图数: $DIST_PNG"
ok "dist 总体积: $DIST_SIZE"

# 回填 README 的构建统计表。
# 这三个数字是**派生数据**——手工维护必然过期：M47–M53 连加 9 张图，
# README 里的「76 张截图 / 19M」就再没被更新过，长期与实际产物不符。
# 与其指望人记得改，不如让构建直接把实测值写回去。
STATS_OUT="$(python3 scripts/update-build-stats.py --pages "$DIST_HTML" --images "$DIST_PNG" --size "$DIST_SIZE" 2>&1)" \
  || fail "构建统计回填失败：
$STATS_OUT"
echo "$STATS_OUT" | sed 's/^/  /'
RAW_MD_LINKS="$(grep -RhoE 'href="[^"]*\.md"' .vitepress/dist --include='*.html' | wc -l | tr -d ' ' || true)"
if [ "$RAW_MD_LINKS" -ne 0 ]; then
  warn "发现 $RAW_MD_LINKS 处指向 .md 的原始链接（未被改写为 .html），请检查对应页面"
else
  ok "无残留 .md 原始链接"
fi

# 侧边栏完整性：每个已发布页面都应出现在 config.mjs 的侧边栏中，
# 否则读者只能靠页内链接抵达，站点导航形同虚设（2026-09-30 M23 实测缺陷）。
# 仅校验真正发布的页面；内部账本由 config.mjs 的 srcExclude 排除，不在此列。
MISSING_SIDEBAR=""
for f in $(find . -name '*.md' -not -path './node_modules/*' -not -path './.vitepress/*' \
  -not -name 'README.md' -not -name 'PUBLISH.md' \
  -not -name 'AUDIT.md' -not -name 'PROGRESS.md' \
  -not -name 'TEST_MEDIA_ASSETS.md' -not -name 'SOURCE_OBSERVATIONS.md'); do
  slug="${f#./}"; slug="${slug%.md}"
  grep -q "'/$slug'" .vitepress/config.mjs || MISSING_SIDEBAR="$MISSING_SIDEBAR $slug"
done
if [ -n "$MISSING_SIDEBAR" ]; then
  warn "以下页面未收录进 config.mjs 侧边栏:$MISSING_SIDEBAR"
else
  ok "所有已发布页面均已收录进侧边栏"
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
