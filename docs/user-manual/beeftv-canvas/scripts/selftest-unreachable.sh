#!/usr/bin/env bash
# 第六道闸（verify-unreachable.py）的反向验证。
#
# 三处修正，都是被自己的失败教会我的：
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
  elif echo "$out" | grep -F "$want" >/dev/null; then
    echo "  ✓ $desc：闸门正确报出 [$want] 失效（退出码 $rc）"; PASS=$((PASS+1))
  else
    echo "  ✗ $desc：报失效但不是 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  fi
  git update-ref -d "$TMPREF" >/dev/null 2>&1
}

run_pass_case() {  # 说明 path 变换脚本 注入特征 期望**仍然成立**的登记id
  # 「不误伤」用例专用：注入一个**看似相关但不该被判失效**的形态，
  # 闸门必须**照旧通过**。少了这一类，放宽判据就会被当成「更好了」而放过。
  # Batch 157 用例 31 就是它：正则从只认 `=` 放宽到认 `[:=]` 之后，
  # 必须证明**比较式 `starterMode === "guided"` 不算写入**。
  local desc="$1" path="$2" tf="$3" feature="$4" want="$5" c out rc
  CASE=$((CASE+1))
  if ! c=$(build_ref "$path" "$tf"); then
    echo "  ✗ $desc：合成 ref 失败，前提不成立，**本次验证作废**"; VOID=$((VOID+1))
    git update-ref -d "$TMPREF" >/dev/null 2>&1; return
  fi
  if ! git show "$TMPREF:$path" 2>/dev/null | grep -F "$feature" >/dev/null; then
    echo "  ✗ $desc：合成 ref 里找不到注入特征 [$feature] → 前提不成立，**本次验证作废**"
    VOID=$((VOID+1)); git update-ref -d "$TMPREF" >/dev/null 2>&1; return
  fi
  echo "  前提成立：合成 ref 的 $path 已含 [$feature]"
  out=$(BEEFTV_REF="$TMPREF" python3 "$GATE" 2>&1); rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "  ✗ $desc：闸门**误伤**了（期望照旧通过，却退出码 $rc）；实际："
    echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  elif echo "$out" | grep -F "$want" >/dev/null; then
    echo "  ✓ $desc：闸门未误伤，[$want] 仍被正确判为成立"; PASS=$((PASS+1))
  else
    echo "  ✗ $desc：虽通过但输出里找不到 [$want]；实际："; echo "$out" | sed 's/^/      /'; FAIL=$((FAIL+1))
  fi
  git update-ref -d "$TMPREF" >/dev/null 2>&1
}

run_case "1) setSort 补上调用" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-1-setsort.py" "void setSort" "canvas-library-no-sort-filter"
run_case "2) 画布库导入补上入口点击" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-2-import-entry.py" "inputRef.current?.click()" "canvas-library-no-import-entry"
run_case "3a) 动态插件入口被从菜单合并里摘掉" web/src/lib/canvas/tool-registry/tool-registry.ts "$HERE/selftest-fix-3a-artcritique-dynamic-chain.py" "反验注入：摘掉动态插件入口" "art-critique-dynamic-entry"
run_pass_case "3b) 审美批改进「添加节点」写死清单（不该判失效）" web/src/lib/canvas/tool-registry/definitions/add-node-menu-tools.tsx "$HERE/selftest-fix-3b-artcritique-hardcoded.py" "ai-art-critique" "art-critique-dynamic-entry"
run_case "4) isLocalWorkspaceMode 改为可配置" web/src/services/workspace-mode.ts "$HERE/selftest-fix-4-workspace-mode.py" "__hosted" "canvas-library-no-join-project"
run_case "5) 审美批改 setter 补上调用" web/src/pages/canvas/project.tsx "$HERE/selftest-fix-5-artcritique-autostart.py" "void setArtCritiqueStartRequest" "art-critique-no-autostart"
run_case "6) 只读模式接上界面入口" web/src/pages/canvas/canvas-project-top-bar.tsx "$HERE/selftest-fix-6-readonly-entry.py" "canvasSelftestReadonlyLink" "canvas-readonly-no-ui-entry"
run_case "7) 复制副本补上后端同步" web/src/pages/canvas/project.tsx "$HERE/selftest-fix-7-copy-sync.py" "await syncLocalCanvasProjectToBackend(id);" "canvas-copy-never-uploaded"
run_case "8) stay=1 被提升为正式功能" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-8-stay-comment.py" "便于用户先确认再建" "canvas-stay-acceptance-only"
run_case "9) 方向三：新增一个未归类的零写出参数" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-9-unmapped-param.py" "canvasSelftestUnmapped" "既不在豁免名单也不在缺陷登记里"
run_case "10) 两处改名统一到同一字段" web/src/components/canvas/canvas-folder-card.tsx "$HERE/selftest-fix-10-two-names-merged.py" "updateProject(project.id, { canvasTitle: editingTitle })" "canvas-two-names"
run_case "11) 顶栏改名补上后端同步" web/src/pages/canvas/project.tsx "$HERE/selftest-fix-11-rename-sync.py" "await syncLocalCanvasProjectToBackend(canvasId);" "canvas-rename-never-uploaded"
run_case "12) 自动保存开始盯 title/canvasTitle" web/src/pages/canvas/use-canvas-project-lifecycle.ts "$HERE/selftest-fix-12-autosave-watches-title.py" "title: currentProject?.title" "canvas-autosave-watches-content-only"
run_case "13) 画布文件夹接上服务端" web/src/pages/canvas/index.tsx "$HERE/selftest-fix-13-folders-synced.py" "createAssetFolder" "canvas-folders-local-only"
run_case "14) 画布封面挪进画布内容" web/src/components/canvas/canvas-folder-card.tsx "$HERE/selftest-fix-14-cover-synced.py" "coverDataUrl" "canvas-cover-localstorage-only"
run_case "15) 导演台场景补上同步" web/src/pages/canvas/use-canvas-director.ts "$HERE/selftest-fix-15-director-sync.py" "scheduleLocalCanvasBackendSync(projectId)" "director-scenes-not-synced"
run_case "16) 远端同步会话判定不再写死 false" web/src/services/local-workspace-sync.ts "$HERE/selftest-fix-16-asset-sync-gate.py" "beef-remote-sync-session" "asset-sync-gated-off"
run_case "17) 前端真的调用服务端素材列表接口" web/src/services/api/workspace-data.ts "$HERE/selftest-fix-17-asset-list-called.py" 'http.get<{ assets: unknown[] }>("/assets")' "asset-list-endpoint-uncalled"
run_case "18) 语音录制测试页补上侧栏入口" web/src/components/layout/workspace-sidebar-nav.tsx "$HERE/selftest-fix-18-voice-test-entry.py" '/test-voice-recording"' "test-voice-page-no-ui-entry"
run_case "19) 任务中心重新开放" web/src/router.tsx "$HERE/selftest-fix-19-tasks-reopened.py" 'element: deferred(<TasksPage />)' "retired-task-skill-pages"
run_case "20) 某档位打开声调开关" web/src/lib/audio-generation.ts "$HERE/selftest-fix-20-audio-pitch-on.py" "showPitch: true" "audio-panel-no-pitch-volume"
run_case "21) more 分组接上渲染" web/src/components/canvas/canvas-node-toolbar.tsx "$HERE/selftest-fix-21-more-group-rendered.py" 'inGroup("more")' "image-toolbar-omits-tools"
run_case "22) 画布库文件夹加上嵌套字段" web/src/stores/canvas/use-canvas-store.ts "$HERE/selftest-fix-22-folder-nested.py" "parentId?: string;" "canvas-folders-not-nested"
run_case "23) 功能开放配置补上写入路由" backend/internal/handler/feature_availability.go "$HERE/selftest-fix-23-feature-write.py" 'r.PATCH("/features"' "feature-availability-readonly"

run_case "24) 审美批改两层统一成都取第一张" web/src/components/canvas/art-critique/ai-art-critique-modal.tsx "$HERE/selftest-fix-24-art-critique-unified.py" "return images[0];" "art-critique-two-layers"
run_case "25) 画风执行策略取消严格分支" web/src/lib/canvas/style-profile.ts "$HERE/selftest-fix-25-style-policy-fixed.py" 'executionPolicy?: "compatible-fallback";' "style-execution-policy-two-branches"
run_case "26) local 标记不再写死 true" web/src/services/workspace-mode.ts "$HERE/selftest-fix-26-channel-title-merged.py" 'local: capabilitySnapshot?.profile === "remote"' "channel-page-three-names"

run_case "27) /dev 调试台接上侧栏入口" web/src/components/layout/workspace-sidebar-nav.tsx "$HERE/selftest-fix-27-dev-lab-entry.py" 'to: "/dev/folders"' "dev-lab-routes-no-entry"

run_case "28) 出厂配置预置了默认模型" web/src/stores/use-config-store.ts "$HERE/selftest-fix-28-default-model.py" 'channels: [{ id: "beefapi-default"' "default-config-no-models"

run_case "29) 补上进入短剧引导的写入点" web/src/stores/canvas/use-canvas-store.ts "$HERE/selftest-fix-29-short-drama-entry.py" 'starterMode: "guided"' "short-drama-empty-state-unreachable"
run_case "30) 空画布四个快捷入口被放出（改条件式）" web/src/components/canvas/canvas-short-drama-entry.tsx "$HERE/selftest-fix-30-empty-canvas-quickstarts.py" 'import.meta.env.DEV;' "empty-canvas-quickstarts-off"
run_pass_case "31) 不误伤：只加比较式 starterMode === \"guided\"（不是写入）" web/src/lib/canvas/canvas-starter.ts "$HERE/selftest-fix-31-guided-comparison-only.py" 'isGuidedStarter' "short-drama-empty-state-unreachable"

# 33/34 是 Batch 170「写出点只看代码、不看注释」这一改动的**一对**反验。
# 缺了 34，这次改动就只有一个方向被验过，而**这类改动的失败模式是静默变弱**：
# 哪天有人图省事不剥注释了、或者把整份源码当注释丢掉，闸门只会少报、不会报错。
# 34 正是把「注释不是界面入口」钉成用例——**它比 33 更该在**。
run_case "33) 代码里补一个真的 ?fixture= 写出点（必须报：该参数已脱零写）" web/src/pages/assets/index.tsx "$HERE/selftest-unreachable-fix-33-fixture-writer.py" '__fixtureEntry' "已被扫到写出点"
run_pass_case "34) 不误伤：只在注释里写 ?fixture=（注释不是界面入口）" web/src/pages/assets/index.tsx "$HERE/selftest-unreachable-fix-34-fixture-in-comment.py" '仅注释，不是界面入口' "9 个参数零写出"

# 关于「工具失败必须与干净的否定结果可区分」：用例 32 **不放这里**。
# 本脚本的框架是往 **BeefTV 源码**注入再重建临时 ref，而那条用例要改的是
# **闸门脚本自己**（verify-unreachable.py）——它根本不在 BeefTV 仓里，
# 用这个框架注入会直接锚点失配。它归 selftest-meta.sh（那边已把
# scripts/verify-unreachable.py 纳入快照范围）。

echo "=== 基线：真实 origin/main 应当通过 ==="
if python3 "$GATE" >/dev/null 2>&1; then echo "  ✓ origin/main 通过"; else echo "  ✗ origin/main 未通过"; FAIL=$((FAIL+1)); fi

git update-ref -d "$TMPREF" >/dev/null 2>&1
echo "=== 结果：通过 $PASS / 作废 $VOID / 失败 $FAIL ==="
echo "=== 清理后状态 ==="
echo "  残留临时 ref: $(git for-each-ref refs/manual-gate-selftest | wc -l | tr -d ' ') （应为 0）"
echo "  BeefTV 工作树改动: $(git status --porcelain | wc -l | tr -d ' ') （应为 0）"
echo "  BeefTV HEAD: $(git rev-parse --short HEAD) （应仍为 852961a）"
[ "$FAIL" -eq 0 ] || exit 1
