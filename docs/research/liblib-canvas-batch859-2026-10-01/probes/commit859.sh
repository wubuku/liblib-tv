#!/usr/bin/env bash
# ★ batch 859 提交脚本：**私有索引**（不碰他人 WIP ＋ 不卷入门禁产物噪声）。
#
# ## 为什么要私有索引
# 工作树里有**他人未提交 WIP**（`docs/research/jimeng-canvas/*`、
# `docs/user-manual/**`、`src/components/jimeng/*` …）⟹ ⟹ **绝不能用
# `git add -A`**、**绝不用 stash**。
#
# ## 流程
# ① 用当前 HEAD 重建一个**临时索引**（HEAD 已被他人推进 ⟹ ⟹ 每次提交前重建）；
# ② 只 `git add` 本批的文件；
# ③ 用 `git diff --cached --name-only` **核对**暂存清单；
# ④ 扫一遍新增行里有没有**裸数字表格首格**（pre-commit 钩子会把它当成手册批次行）；
# ⑤ `git commit -F`（走钩子）；
# ⑥ ★ **必须** `unset GIT_INDEX_FILE` ＋ `git reset --mixed HEAD`
#    （否则后续 `git add` 会写到那个临时索引里、真实索引会失同步）；
# ⑦ 临时索引用 `mavis-trash` 回收。
set -euo pipefail

ROOT=/Users/yangjiefeng/Documents/wubuku/liblib-tv
cd "$ROOT"

MSG_FILE=/tmp/b859-commit-msg.txt
cat > "$MSG_FILE" <<'EOF'
feat(liblib-canvas): batch 859 — 导演台「全景图」「选择画幅比例」面板化（D8 结案）

源站逐字：左侧那个 232px 面板是**五模式互斥容器**（scene／character／camera／
panorama／aspect）⟹ 「全景图」「选择画幅比例」是**面板模式**、不是 rail 浮层
（clone 此前做成 portal 浮层 ⟹ ⟹ 与源站逐字不符）。

clone 整改（4 个源文件）：
- 新建 DirectorPanoramaPanel.tsx（标题条 aO ＋ 容器 px-2 ＋ 三枚逐字 eu 行：
  本地上传／历史记录／AI生成；条件渲染 if (!active) return null）
- 新建 DirectorAspectPanel.tsx（grid grid-cols-2 gap-2 px-2 pb-3 ＋ 七枚
  104×72 卡片 ＋ ASPECT_GLYPH 字形表；选中项跨模式保留）
- DirectorIconRail.tsx：删掉两个 portal 浮层；isEntryPressed 五枚全部由
  panelView 派生；两个 open? 回调合并成单一 onSelectLeftPanelView
- DirectorDesk.tsx：引入并渲染两个新面板；aside aria-label 随模式走

★ 修掉一个真 bug：三个面板同写 key={leftPanelView} ⟹ 兄弟节点 key 重复 ⟹
React 错配 ⟹ 改为只有「添加角色」面板保留 key。

验收：
- 门禁 scripts/verify-liblib-batch859.py 48/48
- 阴性 probes/neg859.py 9/9（行数中性变异 ＋ 字节级复原）
- 回归 probes/regress859.py
- 受控对照 probes/attrib859.py（四态）＋ probes/attrib859_mix.py（MIX 半回退态）
- 迁移 8 条老门禁（538/589/613/617/619/624/625/626）⟹ 浮层尺子改结构性断言

★ 门禁三处加固：静态类串判据剥注释后再比（否则注释里的逐字拷贝会造成假绿）／
borderColor 的 alpha 提取认三种形态／源文件缺失时不崩而是逐条报红。

登记 D11（如实登记不修）：clone 的画幅比例选中项不改画布宽高比。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF

# ★ ① 重建临时索引（HEAD 可能已被他人推进）
HEAD_SHA=$(git rev-parse HEAD)
IDX=/tmp/b859-index-$$
rm -f "$IDX"
export GIT_INDEX_FILE="$IDX"
git read-tree "$HEAD_SHA"

# ★ ② 只加本批文件
git add \
  src/components/director/DirectorPanoramaPanel.tsx \
  src/components/director/DirectorAspectPanel.tsx \
  src/components/director/DirectorIconRail.tsx \
  src/components/director/DirectorDesk.tsx \
  scripts/verify-liblib-batch859.py \
  scripts/verify-liblib-batch538.py \
  scripts/verify-liblib-batch589.py \
  scripts/verify-liblib-batch613.py \
  scripts/verify-liblib-batch617.py \
  scripts/verify-liblib-batch619.py \
  scripts/verify-liblib-batch624.py \
  scripts/verify-liblib-batch625.py \
  scripts/verify-liblib-batch626.py \
  docs/research/liblib-canvas-batch859-2026-10-01/ \
  docs/research/LIBTV_CLONE_REACHABILITY.md \
  docs/research/VERIFICATION_LEDGER.md \
  AGENTS.md

# ★ ③ 核对暂存清单
echo "=== 暂存清单 ==="
git diff --cached --name-only

# ★ ④ 扫裸数字表格首格（pre-commit 钩子的误报形状）
echo "=== 裸数字首格扫描（必须 0 命中）==="
git diff --cached -U0 | grep -nE '^\+\| *[0-9]+[a-z]? *\|' && {
  echo "★ 命中 ⟹ pre-commit 钩子会误判成手册批次行 ⟹ 先改首列"
  exit 1
} || echo "0 命中 ✓"

# ★ ⑤ 提交
git commit -F "$MSG_FILE"

# ★ ⑥ 必须还原真实索引
unset GIT_INDEX_FILE
git reset --mixed HEAD

# ★ ⑦ 回收临时索引
"$HOME/.minimax/bin/mavis-trash" -- "$IDX"

echo
echo "=== 提交后状态 ==="
git log --oneline -2
git status --porcelain -- src/components/director/ scripts/ docs/research/liblib-canvas-batch859-2026-10-01/ docs/research/VERIFICATION_LEDGER.md docs/research/LIBTV_CLONE_REACHABILITY.md AGENTS.md
