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

# 评级一致性校验：任务深度（旗舰/完整/简明）在账本 ↔ 索引分组 ↔ 首页表格三处必须一致。
# 2026-10-01 M58 对账实测：task-inventory.yml 里 use-prompt-library 记为 full，
# 却被 10-tasks/README.md 索引与 README.md 表格都列为「简明」——账本是权威、评级
# 又驱动 audit_manual.py 的门禁强度（core/flagship 需有截图），三处一旦漂移，
# 读者看到的深度与实际门禁强度就对不上。audit_manual.py 只校验 coverage 取值合法性，
# 不校验语义一致，于是一路绿灯放行。这是一道「谁都不会报错」的账实不符，
# 故此处 fail 而非 warn。
RATING_OUT="$(python3 scripts/check-ratings.py . 2>&1)" || fail "评级一致性校验未通过（任务深度在三处记法不一致）：
$RATING_OUT"
echo "$RATING_OUT" | sed 's/^/  /'

# 账本新鲜度：账本 screenshot_count 必须等于 manifest 实数。
# 2026-10-01 M59 对账实测：review_note 里「截图 N 张」的数字长期无人回写，
# 3 条写着数字的与实数不符（create-nodes 2→5、manage-assets 10→13、
# use-agent 4→8）。散文里的数字抓不准（订正文字同时含历史值与正确值），
# 故把数字固化成 screenshot_count 字段、由本脚本从 manifest 实测回填比对。
INVFRESH_OUT="$(python3 scripts/check-inventory-freshness.py . 2>&1)" || fail "账本新鲜度校验未通过（账本截图数与 manifest 实数不符）：
$INVFRESH_OUT"
echo "$INVFRESH_OUT" | sed 's/^/  /'

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

# 账本锁定：`SOURCE_OBSERVATIONS.md` 开头用「版本锁定：提交 <40 位 sha>」把整本
# 账本的证据锚死在一个提交上，而**这句话此前没有任何机制守着它**——应用仓被别的
# 开发者一推进，账本仍以「版本锁定」的口吻陈述旧观察，全部源码层门禁都不会报错。
# 2026-10-02 M105 加；本机没有应用仓副本时**跳过而不是失败**，否则门禁在别人
# clone 下来的机器上必然红。
LEDGERPIN_OUT="$(python3 scripts/check-ledger-pin.py . 2>&1)" || fail "账本锁定校验未通过（账本声明的锁定提交与应用仓 HEAD 不一致）：
$LEDGERPIN_OUT"
echo "$LEDGERPIN_OUT" | sed 's/^/  /'

# 发布文档一致性：PUBLISH.md 的「构建时的门禁」那张表是维护者排查的唯一索引，
# 而它与脚本之间原本没有任何机制相连——2026-10-02 M106 实测该表已漂移
# （把一个构建从不执行的共享脚本列成了构建门禁）。这道门禁把两者钉在一起。
# 账本 YAML 可解析性（第十五道门禁，M123 新增）：此前十四道门禁**无一 import yaml**，
# 全是按行正则读账本，所以「门禁全绿」与「账本是合法 YAML」一直是两件事。实测真出事过：
# 账本第 143 行第 340 列的 note 里嵌了 `{a === "b" ? x : null}` 这类带半角「冒号 + 空格」
# 的源码片段，整个文件用 yaml.safe_load 直接崩。任何将来想用标准 YAML 工具消费这份
# 账本的人都会当场失败——而那正是账本存在的意义（给人读、给工具读）。
INVYAML_OUT="$(python3 scripts/check-inventory-yaml.py . 2>&1)" || fail "账本 YAML 校验未通过（task-inventory.yml 不是合法 YAML、任务 id 重复、或证据 type 非法）：
$INVYAML_OUT"
echo "$INVYAML_OUT" | sed 's/^/  /'

PUBLISHSYNC_OUT="$(python3 scripts/check-publish-sync.py . 2>&1)" || fail "发布文档一致性校验未通过（PUBLISH.md 的门禁表与 build-site.sh 实际调用对不上）：
$PUBLISHSYNC_OUT"
echo "$PUBLISHSYNC_OUT" | sed 's/^/  /'

# 编码完整性：文件里出现 U+FFFD 替换字符，说明某处多字节中文被截断。
# 2026-10-02 M131 新增。此前十五道门禁**没有一道扫它**，而手册里已潜伏 8 处
# （来自 M71 / M108 / M113 三个老提交），产物侧照渲染，读者看到的是「上传的<坏>片节点」。
# 根因是写入路径（bash heredoc 传中文）而非内容，故判据只是"有没有 U+FFFD"这一个信号。
ENCODING_OUT="$(python3 scripts/check-encoding.py . 2>&1)" || fail "编码校验未通过（文件里出现了 U+FFFD 替换字符 = 多字节中文被截断）：
$ENCODING_OUT"
echo "$ENCODING_OUT" | sed 's/^/  /'

# 账本证据一致性（第十七道门禁，M133 新增）：账本每条结论记两处——受校验的
# `evidence`（带 type）与不受校验的 `review_note`（自由文本）。M133 查出
# organize-canvas 与 shortcuts-help 四个批次的运行时取证**只写在 review_note 里**，
# evidence 始终只有一条 static——受校验的字段说「只有源码证据」，不受校验的字段说
# 「实测过好几轮」，**账本自己跟自己打架**，而构建与门禁输出里完全看不出来。
INVEVID_OUT="$(python3 scripts/check-inventory-evidence.py . 2>&1)" || fail "账本证据一致性校验未通过（review_note 声称实测/运行时，但 evidence 里一条 runtime 或 boundary 都没有）：
$INVEVID_OUT"
echo "$INVEVID_OUT" | sed 's/^/  /'

# 探针契约一致性（第十八道门禁，M144 新增）：同一批探针教训被写进四个地方
# （账本 / 两个 .js 文件头 / PUBLISH.md），副本一多必然漂移。M143 已查出一处真实漂移：
# PUBLISH.md 的纪律表只写「白名单四项」却不列出是哪四项，**读者查手册查不到清单**。
# 本门禁把源码里 `DESTRUCTIVE` 集合逐项与文档比对，**只守「文档不能漏项」**——
# 文档可以比源码写得细，但不能漏掉源码里的硬约束。
# 边界如实说清：只校验这一项常量，其余纪律是自然语言、无法机械判定，不碰。
PROBECONTRACT_OUT="$(python3 scripts/check-probe-contracts.py . 2>&1)" || fail "探针契约校验未通过（源码里的不可逆按钮白名单与 PUBLISH.md 纪律表对不上）：
$PROBECONTRACT_OUT"
echo "$PROBECONTRACT_OUT" | sed 's/^/  /'

# 源码引用：手册里每处 `文件.ts:行号` 必须指向应用仓里真实存在的那一行。
# 2026-10-02 M109 新增。账本锁定门禁只在应用仓 HEAD 变化时报错，可一旦有人把
# 账本 sha 一起更新到新提交，那道门禁重新变绿，正文里那几十处行号却可能早已
# 指向别处——读者点着行号跳过去看不到那行，结论就无法复核。
# 路径只按后缀匹配（index.tsx 仓内有 6 个同名）；本机无应用仓时跳过而非失败。
SOURCEREFS_OUT="$(python3 scripts/check-source-refs.py . 2>&1)" || fail "源码引用校验未通过（正文里的 file:line 指向了不存在的文件或越界的行）：
$SOURCEREFS_OUT"
echo "$SOURCEREFS_OUT" | sed 's/^/  /'

# 表格语法：每个 Markdown 表格块都必须自带「表头 + |---| 分隔行」。
# 2026-10-01 M65 实测：shortcuts-help.md 的「弹窗里的十三条」被一段多选提示的
# 引用块从第 8 行和第 9 行之间劈开——前 8 行仍是表格，后 5 行（重做/重做/删除/
# Esc/拖入）没有表头也没有分隔行，产物 HTML 里渲染成一团 | … | 原始管道文本，
# 而且因为引用块在前，这团乱码还被包进了 blockquote。该页正文写着「逐字抄录，
# 一行不落」，读者实际只能看到 8 条表格 + 5 条乱码。**其余九道门禁无一报错**——
# 源文件里每一行都还在，坏掉的只是渲染。AUDIT.md 里另有 61 行同型问题。
TABLES_OUT="$(python3 scripts/check-tables.py . 2>&1)" || fail "表格语法校验未通过（表格被非表格行劈开或缺表头）：
$TABLES_OUT"
echo "$TABLES_OUT" | sed 's/^/  /'

# 强调写法校验：`**` 紧邻标点时 CommonMark 的 flanking 不成立，产物里会留下
# 字面量 `**`，加粗彻底失效。2026-10-01 M90 全站扫产物才发现 7 处（跨 6 页），
# 其余所有门禁当时都报 ok —— 这是继表格未转义竖线之后第二类"源文件没事、
# 产物坏了"的缺陷，且**只能靠这条规则拦住**，产物本身不会有人天天去扫。
EMPHASIS_OUT="$(python3 scripts/check-emphasis.py . 2>&2)" || fail "强调写法校验未通过（** 与标点相邻，产物里会留下字面量 **）：
$EMPHASIS_OUT"
echo "$EMPHASIS_OUT" | sed 's/^/  /'

# 门禁自检：注入 18 类故障，断言每道门禁**以正确的理由**失败。
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

# 产物链接校验。放在构建之后，因为要读 dist。
# M56 实测：build-site.sh 原本只查「有没有残留 .md 链接」，但 VitePress 会把
# **所有** markdown 链接都改写成 .html——包括指向 srcExclude 页面的。于是检查
# 全部通过，站点里却躺着一条指向 ./PUBLISH.html 的死链。
# 「链接被正确改写」不等于「链接指向的东西存在」，前者查格式，后者查事实。
DIST_LINK_OUT="$(python3 scripts/check-dist-links.py . 2>&1)" || fail "产物中存在死链：
$DIST_LINK_OUT"
echo "$DIST_LINK_OUT" | sed 's/^/  /'

# 产物渲染体检：扫**构建后的 HTML**，查表格列数不一致、裸露管道文本、img 异常、
# 页内锚点悬空、正文空标签五类病理。
# 为什么必须在产物侧查：M84（单元格内未转义竖线导致整行内容被丢弃）与 M90
# （`**` 紧邻标点导致加粗失效、留下字面量 `**`）都是**源文件完全正常、
# 八道源码层门禁全部报 ok**，只有把产物打开才看得见。
# 本门禁的每条判据都做过阳性对照（M91 在最小产物里注入对应病理逐一验证）。
RENDER_OUT="$(python3 scripts/check-render.py . 2>&1)" || fail "产物渲染体检未通过（存在渲染后才暴露的病理）：
$RENDER_OUT"
echo "$RENDER_OUT" | sed 's/^/  /'

# ---------- 完成 ----------
log "════════════════════════════════════════════"
ok "构建成功！发布产物: $SCRIPT_DIR/.vitepress/dist"
ok "发布方式: 将上述 dist 目录整体拷贝到任意静态 Web 服务器（详见 PUBLISH.md）"
if [ "${1:-}" = "--preview" ]; then
  log "启动本地预览 http://localhost:4173 （Ctrl+C 结束）"
  exec npx vitepress preview --port 4173
fi
ok "本地预览: ./build-site.sh --preview  或  python3 -m http.server 4173 -d .vitepress/dist"
