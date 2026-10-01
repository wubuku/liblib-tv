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


# ── 「无法核对」专用分支（Batch 160） ─────────────────────────────────
# 闸门约定：**退出码 0 = 核对过且一致；1 = 核对过且不一致；2 = 根本没能核对**。
#
# **为什么必须有 2**：Batch 160 普查发现 **6 个闸共 11 处**在「数据不可用」
# （上游源码缺失、dist 未构建等）时打印 `[skip]` 然后 `return 0`——
# 而所有闸的调用点**只看退出码**。于是**上游目录一改名/一缺失，
# 9 道闸里有 5 道什么都没查却全绿**，手册账本里「已逐条核实」的声明
# 被无声地跳过。**这与 Batch 157 修的「工具失败被当成零命中」是同一个病：
# 「查不了」与「查过了没问题」返回了同一个码。**
#
# 这里**故意不复用通用的 if/else**：退出码 2 不是「查出问题」，
# 报成「不一致」会让人去手册里找根本不存在的问题。
run_gate() {  # $1=脚本 $2=名称；成功 0 / 不一致 1 / 无法核对 2
  local script="$1" name="$2" out rc
  out="$(python3 "scripts/$script" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    ok "$out"; return 0
  fi
  if [ "$rc" -eq 2 ]; then
    printf '%s\n' "$out" | while IFS= read -r line; do
      [ -n "$line" ] && warn "$name 无法核对：$line"
    done
    if [ "${ALLOW_UNVERIFIED:-0}" = "1" ]; then
      warn "$name **未能核对**（已设 ALLOW_UNVERIFIED=1，本次放行）——手册中与该闸相关的断言本次未经复查"
      return 0
    fi
    fail "$name **未能核对**（不是「核对通过」）——手册里与该闸相关的断言本次未经复查。请修复上方 skip 原因；确需在无上游的环境构建，显式设 ALLOW_UNVERIFIED=1"
  fi
  printf '%s\n' "$out" | while IFS= read -r line; do
    [ -n "$line" ] && warn "$name $line"
  done
  fail "$name 核对不一致——详见上方"
}

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

# 站内死链检查（Batch 168 从本文件内联的 heredoc 抽出为 scripts/verify-deadlinks.py）。
# 抽出的理由有二，第二个更要紧：
#  ① 内联在 shell 里的判据**无法被反向验证**——它曾是十道闸里唯一一道没有反验的；
#  ② 内联写法 `python3 … 2>/dev/null || true` 会把**工具失败当成「没有问题」**：
#     Python 一挂，计数取到 0，于是输出「站内链接全部可达」——与 Batch 157 同型。
# 现在走 run_gate，三段退出码（0 无死链 / 1 有死链 / 2 未能核对）由它统一处理。
run_gate verify-deadlinks.py 站内死链

# 截图对账闸：源目录 screenshots/ ↔ manifest.yml ↔ 已发布页面引用 ↔ dist 产物，四侧必须一致。
# 背景（Batch 94）：17-light-mode.png 库里有、manifest 登记着、账本也引用着，唯独发布页
# 不再引用它——重写该页时图片被「替换」而非「补入」。单看任一侧都发现不了，只有四方
# 摊平比对才能揪出「证据在库但读者看不到」。详见 scripts/verify-screenshots.py。
run_gate verify-screenshots.py 截图

# 端点核对闸：20-reference.md 声明的 REST 端点 vs 上游生产路由注册。
# 背景（Batch 96）：手册曾把 6 条 /agent/* 当现存接口教读者排查，而上游根本没注册
# ——教用户去调不存在的接口，比漏写更糟，会把排障方向整体带偏。
# 找不到 BeefTV 源码时脚本静默跳过，手册构建不依赖同级仓库。
run_gate verify-endpoints.py 端点

# 快捷键前缀闸：手册里指向「必须带 Ctrl/Cmd 的键」的写法是否都带了前缀。
# 背景（Batch 110）：同一缺陷在两处出现过（Batch 97 导演台页、Batch 107 画布页
# 都把重做写成 Shift+Z，漏了 Ctrl/Cmd）。表格看着完整、语义也说得通，只有拿每行
# 去和源码绑定条件比对才暴露，故闸门化。
run_gate verify-shortcuts.py 快捷键前缀

# excluded 解禁条件闸：账本里「这页还差什么才能补」的判断，是否与上游现状一致。
# 背景（Batch 111）：这类条件最危险的失效方式是悄悄过期——上游可能已解禁（或已
# 彻底移除），而账本仍写旧理由，于是「什么时候能补这一页」的判断从此失准。
run_gate verify-exclusions.py 解禁条件

# 第五道闸：标签漂移核对（Batch 121）
# 背景：同一轮审计连续四次撞上「同一个设置有多个叫法」（Batch 116/117/119/120）。
# 产品里多个文件各持一份同义枚举表，改一处忘另一处就会漂移。本闸维护一份
# 「已知分歧登记表」，出现未登记的新分歧、或登记的分歧已收敛，都以退出码 1 报出。
# 判据与边界写在脚本 docstring 里，务必连着一读。
run_gate verify-label-drift.py 标签漂移

# 第六道闸：不可达声明核对。手册里最难悄悄过期的一类断言是**否定式断言**
# ——「画布库没有导入入口」「审美批改建不出节点」。上游哪天把那个 click 补上，
# 手册会继续言之凿凿地说「找不到」。本闸对 7 条已登记断言逐条跑专属判据，
# 并反向全量扫描 setter 零调用，要求与登记表双向一致。
# 判据与「不检查什么」写在脚本 docstring 里，务必连着一读。
# 截图取证文案闸（Batch 162 新增，第十道）：manifest 里录下的界面文案是否还在上游。
# 它**部分**关掉了覆盖度表 C 类里「截图内容是否仍对得上界面」——
# 核的是**登记的文案**，不是 PNG 像素；后者仍取决于重拍。
run_gate verify-screenshots-literals.py 截图取证文案
run_gate verify-unreachable.py 不可达断言

# 第十一道闸（Batch 171 新增）：上游源码行数快照。
# 手册里那几句「第二大门户」「源码量第三大的界面页」是**用代码行数**论证页面重要性的，
# 而**行数是最容易过期的数字**——上游每改一次文件它就变，没有任何机制会提醒。
# 实测已栽过：create-workspace.md 写「源码 2023 行」，v1.6.16 上游实为 2790 行（差 767），
# 同一句里的排名「仅次于画布工作区」也已被 projects 超过。**错的是没人看着它。**
# 本闸要求「声明的行数 == 上游实修行数」，**上游一改就会红**——
# 那时要更新快照表或删掉那句话里的论据，**不要放宽判据**。
run_gate verify-line-counts.py 上游行数

# 第十二道闸（Batch 172 新增）：随部署模式而变的策略常量。
# 服务端有两套策略——DefaultRuntimePolicy()（默认部署）与 selfUseRuntimePolicy()（**本地部署**），
# 切换判据是 `RuntimePolicy()` 里 `if s.localMode { … }`，而 NewLocal() 正是以 localMode=true 构造的。
# **也就是说本手册的读者绝大多数走的是第二套**，而手册曾把
# 「同时排队或运行的任务最多 5 个」「素材归档 30 天自动清除」当成固定事实写了 5 处。
# 本闸要求**同一个常量的两套取值都与上游相符**——只核一半等于放过了本地模式那一半。
run_gate verify-runtime-policy.py 部署模式策略

# 第十三道闸（Batch 173 新增）：特性开关的默认值。
# 手册多处写「这一整块由 xxxEnabled 开关控制，关掉时会怎样」，**却从不说默认是哪一边**——
# 实测 7 个开关里 6 个默认开，唯一默认关的只有 frontendModels，
# 所以「需开启 pluginCenterEnabled 特性」这种措辞会让人去找一个**根本不存在**的开关
# （服务端只注册了 GET /features，写入方法在 handler/cmd 层零调用，闸 7 已守着这一点）。
run_gate verify-feature-flags.py 特性开关默认值

# 第十四道闸（Batch 175 新增）：取证基线自洽——**前面十三道闸读的是哪个版本**。
# 背景：此前 8 道读上游源码的闸门各自把 ref 写死成**浮动的 `origin/main`**，
# 而手册正文声明「适用 v1.6.16」。上游从 v1.6.16 走到 v1.6.22（27 提交 / 223 文件差异）后
# 两边静悄悄地分家：实测 2 道闸结论不一致（canvas 行数 17009→17122、「选择镜头模板」
# 文案在上游已被删除），而**这两条在 v1.6.16 上都是绿的**——手册没写错，是上游走了。
# 危险在于红灯只有一种修法（改正文），于是人会把照 v1.6.16 写的内容改成 v1.6.22 的样子，
# 手册从此不对应任何真实版本。「该升版」被伪装成了「该改字」。
# 本闸把基线声明收敛到 20-reference.md 的「取证基线」小节（唯一真值），
# 并**禁止任何闸门再写死浮动 ref**——声明对了但脚本没读它，等于没声明。
run_gate verify-baseline.py 取证基线

# 第十五道闸（Batch 176 新增）：失败时读者会看到的文案。
# 背景：排障页那几张表抄的是上游 web/src/lib/generation-error.ts 的 CATEGORY_COPY。
# v1.6.16 → v1.6.22 之间该表**新增 2 类**（local_storage「尚未提交生成」、
# delivery_failed「已生成但暂时无法取回」）、**改 1 类**（quota_user 多了「可用」二字）、
# **删 0 类**。前两类都会直接改变读者行为：一类让人别去改参数，一类让人别重新付费。
# 本闸**双向**核：手册写了而上游没有的不管（那是内容准确性，不是漏写），
# 上游有而手册没写的必须报；豁免表逐条复核其理由在上游是否还成立。
run_gate verify-error-copy.py 失败文案

# 第七道闸：markdown 表格结构核对。前面六道查的都是**内容对不对**，
# 这一道查**结构坏没坏**——单元格里的裸竖线（最常见就是代码里的 `||` 和带竖线的 URL）
# 会多切出一列、把整行内容错位，而**构建照样成功**，只有读的人才看得见。
# Batch 142 在 PROGRESS.md 里撞见 5 行这样的历史损坏，20-reference.md 里也有 1 行
# （一个含 `|` 的端点 URL 把行切断了）。判据只拦「多于表头」：
# 少于一列会被 GFM 补空单元格，渲染正常（PROGRESS 里大量「状态」列留空即属此类）。
if TB_OUT="$(python3 scripts/verify-tables.py 2>&1)"; then
  ok "$TB_OUT"
else
  printf '%s\n' "$TB_OUT" | while IFS= read -r line; do
    [ -n "$line" ] && warn "表格结构 $line"
  done
  fail "表格被未转义的竖线截断——单元格内的 | 要写成 \| （代码段里的 || 写成 \|\|）"
fi

# 第八道闸：手册元数据自洽。前面七道查的都是**关于产品**的断言
# （端点怎么注册、功能有没有入口、界面文字漂没漂），这一道查
# **关于本手册自己**的计数——「本手册有多少篇任务指南 / 多少项任务 /
# 多少张截图 / 多少个内容页」。
#
# 它的真值**不来自上游源码**，而来自本仓库自己的目录与 yml，
# 所以前七道闸按定义就照不到它。Batch 145 撞见一批全批过期的此类数字：
# README 写「25 篇 / 32 项」而实际已是 29 篇 / 35 项、FINAL-REPORT 写 33 页
# 而实际 35 个内容页、AUDIT-RULES 的「现有六道闸」漏登记 Batch 143 自己加的第七道。
#
# 与 Batch 143 立的「六道闸全绿不等于发布物正确」同源：
# **七道闸全绿也不等于账本自洽。**
if MT_OUT="$(python3 scripts/verify-meta.py 2>&1)"; then
  printf '%s\n' "$MT_OUT" | while IFS= read -r line; do
    [ -n "$line" ] && ok "元数据 $line"
  done
else
  printf '%s\n' "$MT_OUT" | while IFS= read -r line; do
    [ -n "$line" ] && warn "元数据 $line"
  done
  fail "手册自报的计数与现场重数不一致（或有未登记的计数表述）——重数后更新对应页面"
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
