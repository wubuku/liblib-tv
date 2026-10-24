#!/usr/bin/env bash
# ★ batch 861 提交脚本：**私有索引**（不碰他人 WIP ＋ 不卷入门禁产物噪声）。
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

MSG_FILE=/tmp/b861-commit-msg.txt
cat > "$MSG_FILE" <<'EOF'
feat(liblib-canvas): batch 861 — 「全景图」三行不再是死按钮

★ 靶子：batch 859 把「全景图」面板化之后，那三行（本地上传／历史记录／AI生成）
仍然完全没有 onClick ⟹ ⟹ 点了什么也不会发生。

★ 源站逐字（chunk aU 的 panorama 段）：本地上传 onClick:()=>{I?.(),et.current?.click()}、
历史记录 onClick:T、AI生成 onClick:P ＋ disabled:E；三个回调的实现逐字查清：
oY ＝ 纯埋点（真动作是 et.current?.click()）、oB ＝ eu?.((e,t)=>{…r6({panoramaUrl:e})})、
oX ＝ td(!0)（打开对话框）。

★ 源站运行时实测：点「本地上传」弹出了文件选择器（filechooser ＝ True）；
点「历史记录」按钮 86 → 95；点「AI生成」按钮 86 → 98（同一选择器 ＋ 多
「上传图片」「生成」「关闭」）⟹ ⟹ 两行打开的是同一个资产库选择器（全屏）。

★ clone 整改（5 个源文件）：
- src/components/director/DirectorPanoramaPanel.tsx：三行接 onClick（显式三分支）
  ＋ 隐藏 file input（accept="image/*"）＋ 点击即 fileInputRef.current?.click()
  ＋ 底部加一行「当前全景图」
- src/components/director/DirectorPanoramaPicker.tsx（新建）：选择器对话框
  （取消／确认选择；AI 模式多「生成」「上传图片」）
- src/store/directorStore.ts：新增 localPanoramaAsset ＋ setLocalPanoramaAsset
  （换资产时 revoke 旧 blob）
- src/lib/directorCanvasMediaIngress.ts：新增 mergeDirectorLocalPanoramaInput
  ＋ 前缀 local-panorama:
- src/components/director/DirectorDesk.tsx：把本地资产并进 canvasMediaInputs

★ 本地文件没有节点 id ⟹ ⟹ 包成同构的虚拟输入 ⟹ ⟹ 3D 层、检查器、选择器
一条通路照常工作，不必新增渲染分支。

验收：
- 门禁 scripts/verify-liblib-batch861.py 29/29
- 阴性 probes/neg861.py 8/8（★ 含一条底线门禁：选择器源码里不许出现任何
  网络调用 ⟹ ⟹ clone 绝不接真实全景图生成，真实生图会产生费用）
- 回归 probes/regress861.py
- 受控对照 probes/attrib861.py（四态）＋ probes/attrib861_mix.py（MIX 半回退态）

★ 判据的两个真 bug（都是判据错、不是产品错）：① strip_comments() 的 /*…*/
会把 JSX 属性值 image/* 当块注释起点删掉 ⟹ ⟹ 改成先保护引号字符串再剥注释；
② 静态判据用 in 全文匹配 ⟹ ⟹ 同一名字在别处出现（常量表、提示文案、store 的
多处声明）⟹ ⟹ 假绿 ⟹ ⟹ 改成精确定位到声明处 ⟹ ⟹ 这条判据还逼出了源码的
一个真弱点（第三行原本是裸 else ⟹ ⟹ 改成显式三分支）。

★ 登记差异：D12 选择器形态不同／D13 本地上传走 blob 不上传／D14「AI生成」
不接真实生成／D15 面板多一行「当前全景图」／D16 源站 disabled:!hasCameras
未对齐（源站机位删不掉 ⟹ ⟹ 无机位态未能实测 ⟹ ⟹ 只登记不修）。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF

# ★ ① 重建临时索引（HEAD 可能已被他人推进）
HEAD_SHA=$(git rev-parse HEAD)
IDX=/tmp/b861-index-$$
rm -f "$IDX"
export GIT_INDEX_FILE="$IDX"
git read-tree "$HEAD_SHA"

# ★ ② 只加本批文件
git add \
  src/store/directorStore.ts \
  src/lib/directorCanvasMediaIngress.ts \
  src/components/director/DirectorPanoramaPanel.tsx \
  src/components/director/DirectorPanoramaPicker.tsx \
  src/components/director/DirectorDesk.tsx \
  scripts/verify-liblib-batch861.py \
  docs/research/liblib-canvas-batch861-2026-10-01/ \
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

# ★ ④' 扫 U+FFFD（★ 手打的文本可能混进乱码 ⟹ ⟹ 提交前必须扫一遍）
echo "=== U+FFFD 扫描（必须 0 命中）==="
if grep -n $'\ufffd' "$MSG_FILE"; then
  echo "★ 提交消息里有 U+FFFD ⟹ 先修"
  exit 1
else
  echo "0 命中 ✓"
fi

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
git status --porcelain -- src/components/director/ scripts/ docs/research/liblib-canvas-batch860-2026-10-01/ docs/research/VERIFICATION_LEDGER.md docs/research/LIBTV_CLONE_REACHABILITY.md AGENTS.md
