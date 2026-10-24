#!/usr/bin/env bash
# ★ batch 862 提交脚本：**私有索引**（不碰他人 WIP ＋ 不卷入门禁产物噪声）。
#
# ## 为什么要私有索引
# 工作树里有**他人未提交 WIP**（`docs/research/jimeng-canvas/*`、
# `docs/user-manual/**`、`scripts/jimeng*` …）⟹ ⟹ **绝不能用 `git add -A`**、
# **绝不用 stash**。
#
# ## 流程
# ① 用当前 HEAD 重建一个**临时索引**（HEAD 已被他人推进 ⟹ ⟹ 每次提交前重建）；
# ② 只 `git add` 本批的文件；
# ③ 用 `git diff --cached --name-only` **核对**暂存清单；
# ④ 扫一遍新增行里有没有**裸数字表格首格**（pre-commit 钩子会把它当成手册批次行）；
# ⑤ 扫一遍提交消息里的 U+FFFD；
# ⑥ `git commit -F`（走钩子）；
# ⑦ ★ **必须** `unset GIT_INDEX_FILE` ＋ `git reset --mixed HEAD`
#    （否则后续 `git add` 会写到那个临时索引里、真实索引会失同步）；
# ⑧ 临时索引用 `mavis-trash` 回收。
set -euo pipefail

ROOT=/Users/yangjiefeng/Documents/wubuku/liblib-tv
cd "$ROOT"

MSG_FILE=/tmp/b862-commit-msg.txt
cat > "$MSG_FILE" <<'EOF'
feat(liblib-canvas): batch 862 — 取景框上的「构图参考线」开关（源站逐字归位）

★ 靶子：batch 860 把「画幅比例」接到机位取景框上之后，clone 的框**只有那条线、
没有开关**（开关在 clone 自己的视口底部胶囊里）；而源站逐字那枚开关**长在取景框
的右上角**，而且**只在选了具体比例时存在**。

★ 源站逐字（chunk 0fmehki05gkzw.js.js 的 mP 组件 ＋ 调用点）：按钮
title:s("canvas:directorAspectFrameOverlay")、类名 nodrag nopan nowheel
pointer-events-auto absolute z-20 flex h-8 w-8 items-center justify-center
rounded-lg transition-colors ＋ 关闭态 text-white/50 hover:bg-white/10
hover:text-white/80、开启态 bg-(--btn-secondary-bg) text-btn-primary、
★ 位置公式 style:{left:u.left+u.width-40, top:u.top+8}；调用点
onToggleCompositionGrid:null!==tr?()=>{…}:void 0
⟹ ⟹ ★ 只在选了具体比例时存在（与「取景框不在场」同一条件）
＋ 切换时写进机位 n4(cameraId,"reference_line",…)。

★ 源站运行时实测（raw/source-862-frame-thirds.json 等 3 份）：16:9 的框
@(329,185) 1262×710 ⟹ ⟹ 框上开关 @(1551,193) 32×32、title="构图参考线"
（★ 位置公式实测命中：329＋1262−40 ＝ 1551／185＋8 ＝ 193）⟹ ⟹ 点开关后出现
4 条分线 ⟹ ⟹「自适应」时框与开关都不在场 ⟹ ⟹ 归一化后：框描边 1px／白 18%／
内缩 1px／圆角 12px、分线白 50%、开关开启态前景 rgb(9,202,245) ＋ 背景
rgba(255,255,255,0.1)。

★ clone 整改（2 个源文件）：
- src/components/director/DirectorViewport.tsx：新增 DirectorFrameThirdsToggle
  （逐字类名 ＋ 逐字位置公式 ＋ 逐字源站 svg path（16×16 单 path）＋ 开启态用
  源站实测色）＋ 框的描边从 border 改成源站逐字的 outline（1px／白 18%／
  内缩 1px／圆角 12px）＋ 分线颜色从白 35% 改成源站逐字的白 50%
- src/components/director/DirectorAspectPanel.tsx：只改注释（补上「那行 disabled
  绑定在运行时永远不生效」的诚实标注：clone 的删除规划器有
  DIRECTOR_LAST_CAMERA_REQUIRED 守卫 ⟹ ⟹ 永远至少有一个机位）
  ＋ 立下「注释里不许抄 clone 自己的 JSX 字面量」的纪律

★ 验收：
- 门禁 scripts/verify-liblib-batch862.py 57/57（源站期望值只从入库 raw 读）
- 阴性 probes/neg862.py 7/7 ＋ probes/neg862_migration35.py 2/2（行数中性 ＋
  字节级还原）
- 回归 probes/regress862.py 107 条（比上批多 9 条：新增本批，并把 35／645／
  722／629／815／816／817 拉进来）⟹ ⟹ 新看见 4 条红 ⟹ ⟹ 定点归因（HEAD 态
  vs WORK 态）⟹ ⟹ 红条逐条相同 ⟹ ⟹ 全是旧账、本批引入 0 条
- 受控对照 probes/attrib862.py（四态 ＋ MIX 半回退态）：稳定 ✔ 有牙 ✔ 复原 ✔
  ⟹ ⟹ HEAD 态 38 条具名红、零 CRASH；WORK 态 0 红；MIX 态运行时 22 红 ＋
  静态 8 红，而面板那条静态判据保持绿 ⟹ ⟹ 隔离干净

★ 顺手整改一条老门禁的旧前提：verify-liblib-batch35.py 原本直接读取景框，隐含
「框默认在场」——batch 860 按源站实测把初始比例改成「自适应＝无框」之后该前提
就不成立（必然 30s 超时）⟹ ⟹ 迁移成「先选比例再读框」的结构性判据，并配阴性
2/2（M1 还原旧前提必须超时／M2 改错比例期望必须断言失败）。

★ 本批自己踩了四个坑（都已写成纪律）：
① 同名在别处出现 ⟹ 静态判据假绿 ⟹ 负控打空（注释里抄了同一个字面量 ⟹ ⟹
   替换命中注释 ⟹ ⟹ 代码没变）⟹ ⟹ 已改成锚点带缩进定位代码行 ＋ 注释纪律；
② 两条 raw 必须同口径（clone 的 CSS rgba alpha 0..1 vs 源站 canvas 像素
   0..255）⟹ ⟹ 判据里 int() 把 0.5 截成 0 ⟹ ⟹ 三条颜色判据假红 ⟹ ⟹ 两侧都走
   canvas 归一化；
③ 绝对像素不可比 ⟹ ⟹ 比「相对偏移」这个不变量（框宽−40, 8）；
④ HEAD 态翻红要翻成具名红条、不是 CRASH ⟹ ⟹ 点之前先计数。

★ 登记差异：D16 源站七格的 disabled:!hasCameras（两侧运行时都不可达 ⟹ ⟹
只能按源码判据）／D17 源站把比例与参考线写进机位对象（clone 未做）／
D18 取景框像素几何不同（源站全屏 1080 ＋ 逐字公式 vs clone 810 高 padding）／
D19 底部胶囊那枚「九宫格辅助线」是 clone 扩展（保留并共享 showThirds）／
D20 源站框外遮罩有 backdrop-blur-md（clone 是 9999px shadow，无模糊）。

★ 用户可达：根 http://localhost:4317/ ⟹ ⟹ hover 导演台卡片 ⟹ ⟹「打开导演台 →」
⟹ ⟹ rail 点「选择画幅比例」⟹ ⟹ 点「16:9」⟹ ⟹ 取景框右上角多了一枚 32×32 的
「构图参考线」按钮 ⟹ ⟹ 点它 ⟹ ⟹ 框内出现 4 条分线（按钮变青）⟹ ⟹ 再点消失
⟹ ⟹ 点「自适应」⟹ ⟹ 框与按钮一起消失。
选择器：[data-director-aspect-frame]／[data-director-frame-thirds-toggle]／
[data-director-thirds]

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF

# ★ ① 重建临时索引（HEAD 可能已被他人推进）
HEAD_SHA=$(git rev-parse HEAD)
IDX=/tmp/b862-index-$$
rm -f "$IDX"
export GIT_INDEX_FILE="$IDX"
git read-tree "$HEAD_SHA"

# ★ ② 只加本批文件
git add \
  src/components/director/DirectorViewport.tsx \
  src/components/director/DirectorAspectPanel.tsx \
  scripts/verify-liblib-batch862.py \
  scripts/verify-liblib-batch35.py \
  docs/research/liblib-canvas-batch862-2026-10-01/ \
  docs/research/LIBTV_CLONE_REACHABILITY.md \
  docs/research/VERIFICATION_LEDGER.md \
  AGENTS.md

# ★ ③ 核对暂存清单
echo "=== 暂存清单 ==="
git diff --cached --name-only

# ★ ③' ★ 断言：**没有**别人的 WIP 被卷进来
echo "=== 他人 WIP 误入扫描（必须 0 命中）==="
if git diff --cached --name-only | grep -E '^(docs/research/jimeng-canvas/|docs/user-manual/|scripts/jimeng|scripts/verify-jimeng-|src/components/jimeng/|src/store/jimengStore\.ts|src/app/page\.tsx|src/app/clones/|src/lib/clonePages\.ts|src/components/CloneSiteNav\.tsx|docs/CLONE_PAGES_INDEX\.md)'; then
  echo "★ 命中 ⟹ 他人 WIP 被卷进来了 ⟹ 先修"
  exit 1
else
  echo "0 命中 ✓"
fi

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
git status --porcelain -- src/components/director/ scripts/verify-liblib-batch862.py \
  scripts/verify-liblib-batch35.py docs/research/liblib-canvas-batch862-2026-10-01/ \
  docs/research/VERIFICATION_LEDGER.md docs/research/LIBTV_CLONE_REACHABILITY.md AGENTS.md
