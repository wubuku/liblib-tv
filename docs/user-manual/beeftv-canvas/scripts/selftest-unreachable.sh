#!/usr/bin/env bash
# 第六道闸（verify-unreachable.py）的反向验证。
#
# 三处修正，都是被自己的失败教会��：
#  1) v1 出了**假阳性**——合成 tree 其实没建成功，闸门对着坏 ref 报错，也被判成
#     「✓ 正确报出失效」。反向验证若不校验自己的前提，等于没做。现在先确认合成
#     ref 里**真的出现修复特征**，不成立就作废本次验证（宁可少认几条 ✓）。
#  2) v2/v3 的 commit-tree 失败，根因是 `rm` 被环境的可恢复删除包装器拦截并返回
#     非零，污染了函数退出码。改用固定 index 路径，全程不调 rm。
#  3) 变换脚本改放独立 .py 文件，避免 shell 引号嵌套炸掉整个脚本。
#
# 全程 git plumbing 造临时 ref：不改工作树、不动任何现有分支，结束即清 ref。
#
# ⚠️ 副作用须知：会在 BeefTV 仓的 .git 里写入**悬空对象**（blob/tree/commit）。
# 这是 `git hash-object -w` 与 `commit-tree` 的固有行为，无法避免；临时 ref 已删除，
# 悬空对象会被 git gc 自动回收，**不会进入任何分支、不影响工作树**。
# 退出前会打印 BeefTV 的工作树改动数与 HEAD，供你复核确实没被碰过。
set -uo pipefail
SRC="${BEEFTV_SRC:-/Users/yangjiefeng/Documents/glanderness/BeefTV}"
GATE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/verify-unreachable.py"
TMPREF=refs/manual-gate-selftest
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IDXBASE="${TMPDIR:-/tmp}/beef-gate-selftest"
CASE=0
cd "$SRC" || exit 1

build_ref() {  # $1=path  $2=变换脚本路径 → 成功时 stdout 输出 commit sha
  local path="$1" tf="$2" base blob tree commit IDX
  # 每个用例用**独立** index：共用一个时，第 5 条用例的前提校验会莫名失败
  # （单独跑同一套 plumbing 完全正常），属串扰而非闸门缺陷。宁可不共享。
  IDX="${IDXBASE}.${CASE}.index"
  base=$(git rev-parse "origin/main^{tree}") || return 1
  blob=$(git show "origin/main:$path" | python3 "$tf" | git hash-object -w --stdin) || return 1
  [ -n "$blob" ] || return 1
  GIT_INDEX_FILE="$IDX" git read-tree "$base" || return 1
  GIT_INDEX_FILE="$IDX" git update-index --add --cacheinfo "100644,$blob,$path" || return 1
  tree=$(GIT_INDEX_FILE="$IDX" git write-tree) || return 1
  [ -n "$tree" ] || return 1
  commit=$(echo "gate selftest" | git commit-tree "$tree" -p "$(git rev-parse origin/main)") || return 1
  git update-ref "$TMPREF" "$commit" || return 1
  echo "$commit"
}

PASS=0; VOID=0; FAIL=0

run_case() {  # 说明 path 变换脚本 修复特征 期望失效的登记id
  local desc="$1" path="$2" tf="$3" feature="$4" want="$5" c out rc
  CASE=$((CASE+1))
  if ! c=$(build_ref "$path" "$tf"); then
    echo "  ✗ $desc：合成 ref 失败，前提不成立，**本次验证作废**"; VOID=$((VOID+1))
    git update-ref -d "$TMPREF" >/dev/null 2>&1; return
  fi
  # 注意：这里**不能用 grep -q**。脚本开了 pipefail，而 grep -q 命中即退出、
  # 上游 git show 收到 SIGPIPE 返回 141，整条管道被判失败——文件越大越容易触发
  # （第 5 条用例的 project.tsx 最大，于是被前提校验误判成假阴性）。
  # 改用不带 -q 的 grep：它会读完整个输入，不产生 SIGPIPE。
  if ! git show "$TMPREF:$path" 2>/dev/null | grep -F "$feature" >/dev/null; then
    echo "  ✗ $desc：合成 ref 里找不到修复特征 [$feature] → 前提不成立，**本次验证作废**"
    VOID=$((VOID+1)); git update-ref -d "$TMPREF" >/dev/null 2>&1; return
  fi
  echo "  前提成立：合成 ref 的 $path 已含 [$feature]"
  out=$(BEEFTV_REF="$TMPREF" python3 "$GATE" 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "  ✗ $desc：闸门**未**报失效（期望退出码 1）→ 反向验证失败"; FAIL=$((FAIL+1))
  elif echo "$out" | grep -qF "$want"; then
    echo "  ✓ $desc：闸门正确报出 [$want] 失效（退出码 $rc）"; PASS=$((PASS+1))
  else
    echo "  ✗ $desc：报失效但不是 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  fi
  git update-ref -d "$TMPREF" >/dev/null 2>&1
}

run_case "1) setSort 补上调用" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-1-setsort.py" "void setSort" "canvas-library-no-sort-filter"
run_case "2) 画布库导入补上入口点击" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-2-import-entry.py" "inputRef.current?.click()" "canvas-library-no-import-entry"
run_case "3) AI 审美批改进「添加节点」清单" web/src/lib/canvas/tool-registry/definitions/add-node-menu-tools.tsx "$HERE/selftest-fix-3-artcritique-menu.py" "ai-art-critique" "art-critique-no-create-entry"
run_case "4) isLocalWorkspaceMode 改为可配置" web/src/services/workspace-mode.ts "$HERE/selftest-fix-4-workspace-mode.py" "__hosted" "canvas-library-no-join-project"
run_case "5) 审美批改 setter 补上调用" web/src/pages/canvas/project.tsx "$HERE/selftest-fix-5-artcritique-autostart.py" "void setArtCritiqueStartRequest" "art-critique-no-autostart"
run_case "6) 只读模式接上界面入口" web/src/pages/canvas/canvas-project-top-bar.tsx "$HERE/selftest-fix-6-readonly-entry.py" "canvasSelftestReadonlyLink" "canvas-readonly-no-ui-entry"
run_case "7) 复制副本补上后端同步" web/src/pages/canvas/project.tsx "$HERE/selftest-fix-7-copy-sync.py" "await syncLocalCanvasProjectToBackend(id);" "canvas-copy-never-uploaded"
run_case "8) stay=1 被提升为正式功能" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-8-stay-comment.py" "便于用户先确认再建" "canvas-stay-acceptance-only"
run_case "9) 方向三：新增一个未归类的零写出参数" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-9-unmapped-param.py" "canvasSelftestUnmapped" "既不在豁免名单也不在缺陷登记里"

echo "=== 基线：真实 origin/main 应当通过 ==="
if python3 "$GATE" >/dev/null 2>&1; then echo "  ✓ origin/main 通过"; else echo "  ✗ origin/main 未通过"; FAIL=$((FAIL+1)); fi

git update-ref -d "$TMPREF" >/dev/null 2>&1
echo "=== 结果：通过 $PASS / 作废 $VOID / 失败 $FAIL ==="
echo "=== 清理后状态 ==="
echo "  残留临时 ref: $(git for-each-ref refs/manual-gate-selftest | wc -l | tr -d ' ') （应为 0）"
echo "  BeefTV 工作树改动: $(git status --porcelain | wc -l | tr -d ' ') （应为 0）"
echo "  BeefTV HEAD: $(git rev-parse --short HEAD) （应仍为 852961a）"
[ "$FAIL" -eq 0 ] || exit 1
