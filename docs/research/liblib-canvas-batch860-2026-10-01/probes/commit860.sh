#!/usr/bin/env bash
# ★ batch 860 提交脚本：**私有索引**（不碰他人 WIP ＋ 不卷入门禁产物噪声）。
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

MSG_FILE=/tmp/b860-commit-msg.txt
cat > "$MSG_FILE" <<'EOF'
feat(liblib-canvas): batch 860 — 画幅比例真的驱动机位取景框（推翻 D11）

★ D11 被本批实测推翻：源站选画幅比例**不改画布**，改的是**机位取景框**。
源站实测七档逐档的框（自适应不在场／21:9 1262x541／16:9 1262x710／
4:3 1141x856／1:1 856x856／3:4 642x856／9:16 482x856）全部命中期望比例，
而画布容器三态恒为 1920x1080。

clone 改之前的差距：取景框只支持三档 ＋ 左侧面板那七格根本没接到 store
⟹ ⟹ 点哪一档取景框都不动。

clone 整改（4 个源文件）：
- src/store/directorStore.ts：新增取景比例状态 frameAspectRatio（六档 ＋
  null＝自适应）＋ setFrameAspectRatio ＋ 数值表；★ 导出比例 aspectRatio
  （三值，截图/导出用）刻意不动
- src/components/director/directorViewportMath.ts：getDirectorFrameRect
  改成吃任意数值比例；null ⟹ ⟹ 不画框
- src/components/director/DirectorAspectPanel.tsx：★ 七格接到 store
- src/components/director/DirectorViewport.tsx：AspectFrame 改读取景比例；
  底部那三枚（clone 自己的扩展）也接同一状态

验收：
- 门禁 scripts/verify-liblib-batch860.py 59/59
- 阴性 probes/neg860.py 9/9（行数中性变异 ＋ 字节级复原）
- 回归 probes/regress860.py：97 条、红 14 条，红集合与 batch 859 逐条相同
  ⟹ 零新红（626 仍只剩 D7 那 1 条 ⟹ 858/859 的整改没退化）
- 受控对照 probes/attrib860.py 四态：HEAD 两态各 19 条红（两遍一致 ⟹ 稳定）、
  WORK 两态 0 条红 ⟹ 有牙；WORK 独有红条 0 条；源码 SHA-256 复原 True
- 受控对照 probes/attrib860_mix.py（MIX 半回退态）：只回退
  DirectorAspectPanel.tsx ⟹ 13 条红（静态 1 条 + 运行时 12 条），
  store 与 math 的静态判据全绿 ⟹ 隔离干净

★ 判据三次假红都是判据错不是产品错（react-flow 视口 ≠ 导演台视口／
上下 padding 不对称／反推可用区的公式把 padding 算进去了）⟹ ⟹ 最终判据是
「所有档的框共享同一个中心」（源站也成立）。

★ 负控 N9 原改的是 TS 接口字段名 ⟹ 类型不参与运行时 ⟹ 负控打空
⟹ ⟹ 改成改运行时初始值才有效。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF

# ★ ① 重建临时索引（HEAD 可能已被他人推进）
HEAD_SHA=$(git rev-parse HEAD)
IDX=/tmp/b860-index-$$
rm -f "$IDX"
export GIT_INDEX_FILE="$IDX"
git read-tree "$HEAD_SHA"

# ★ ② 只加本批文件
git add \
  src/store/directorStore.ts \
  src/components/director/directorViewportMath.ts \
  src/components/director/DirectorAspectPanel.tsx \
  src/components/director/DirectorViewport.tsx \
  scripts/verify-liblib-batch860.py \
  docs/research/liblib-canvas-batch860-2026-10-01/ \
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
