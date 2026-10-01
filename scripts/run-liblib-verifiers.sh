#!/usr/bin/env bash
# liblib 克隆验证器统一入口 (Batch 361)
#
# 背景: liblib 线有 300+ 个验证器, 此前只能逐个手动定向跑, 每批回归 20~40 分钟,
#       长期是耗时大头。本脚本给这条线一个带并发的统一入口。
#
# 用法:
#   bash scripts/run-liblib-verifiers.sh                 # 跑全部 (默认并发 4)
#   bash scripts/run-liblib-verifiers.sh -j 8            # 指定并发度
#   bash scripts/run-liblib-verifiers.sh 358 359 360     # 只跑指定批次
#   bash scripts/run-liblib-verifiers.sh --changed        # 只跑受本分支改动影响的批次
#   bash scripts/run-liblib-verifiers.sh --list           # 列出全部批次, 不执行
#
# 前置: dev server 已运行在 $LIBLIB_BASE_URL (默认 http://localhost:4317)
#       python 用 $LIBLIB_PYTHON (默认 ~/.venvs/liblib-harness/bin/python)

set -u

PY="${LIBLIB_PYTHON:-$HOME/.venvs/liblib-harness/bin/python}"
[ -x "$PY" ] || PY="python3"
BASE_URL="${LIBLIB_BASE_URL:-http://localhost:4317}"
export LIBLIB_BASE_URL="$BASE_URL"

# **node 必须在 PATH 里**: 有 10 个 liblib 门禁(batch10/51/52/53/54/60/62/69/172/
# 173/185)会 subprocess 调 `node` 跑配套的 .mjs 静态门禁。裸 bash 里 node 不在
# PATH, batch69 会报 `FileNotFoundError: 'node'` —— 而它**不是**回归, 是 runner
# 自己没准备环境。踩到才发现, 属「元缺陷」: 一批验证器悄悄依赖同一个外部运行时。
#
# **必须挑最新的, 不能取 glob 的第一个**: 门禁用 `--experimental-strip-types`,
# 老 node(v12/v14)不支持, 会以 exit 9 失败。第一版直接 `for cand in .../*/bin;
# break`, 在这台机器上选到 v12.18.4 —— 症状从「找不到 node」变成「node 存在但
# 跑不动」, 反而更难查。**兜底代码自己也可能挑错版本。**
if ! command -v node >/dev/null 2>&1; then
  if [ -n "${LIBLIB_NODE_DIR:-}" ] && [ -x "$LIBLIB_NODE_DIR/node" ]; then
    export PATH="$LIBLIB_NODE_DIR:$PATH"
  fi
fi
if ! command -v node >/dev/null 2>&1; then
  newest=""
  for cand in "$HOME/.nvm/versions/node"/*/bin; do
    [ -x "$cand/node" ] || continue
    # 版本号按字典序比(v24 > v9), 够用且不引外部依赖
    if [ -z "$newest" ] || [[ "$(basename "$(dirname "$cand")")" > \
                           "$(basename "$(dirname "$newest")")" ]]; then
      newest="$cand"
    fi
  done
  [ -n "$newest" ] && export PATH="$newest:$PATH"
fi
command -v node >/dev/null 2>&1 || {
  echo "FATAL: node not found in PATH; 10 verifiers shell out to it."
  echo "       set LIBLIB_NODE_DIR=/path/to/node/bin, or put node on PATH."
  exit 2
}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

JOBS=""
RETRIES="${LIBLIB_RETRIES:-1}"
LIST_ONLY=0
CHANGED_ONLY=0
BATCHES=""

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    -j|--jobs) JOBS="$2"; shift 2 ;;
    -r|--retries) RETRIES="$2"; shift 2 ;;
    --list) LIST_ONLY=1; shift ;;
    --changed) CHANGED_ONLY=1; shift ;;
    -h|--help) usage ;;
    *) BATCHES="$BATCHES $1"; shift ;;
  esac
done

[ -n "$JOBS" ] || JOBS="${LIBLIB_JOBS:-4}"

# 全量清单: 动态发现 scripts/verify-liblib-batch*.py
# 注意含字母后缀的批次号(如 146b) —— 按纯数字切会把它截断。
if [ -n "$BATCHES" ]; then
  SELECTED="$BATCHES"
else
  SELECTED=$(ls "$ROOT"/scripts/verify-liblib-batch*.py 2>/dev/null \
    | sed -E 's|.*/verify-liblib-batch||; s|\.py$||' | sort -t. -k1,1V -k2,2 | tr '\n' ' ')
fi

if [ "$LIST_ONLY" -eq 1 ]; then
  for b in $SELECTED; do echo "batch$b"; done
  exit 0
fi

# --changed: 挑出「改动可能影响到的」门禁。
#
# 两种命中, 分开报, 因为可信度不同:
#   直接  —— 本批次脚本自身被改, 或它 docstring 里点名的 src/ 文件被改;
#   旁及  —— 同一 src/ 文件被**别的**门禁也点名过(跨线共享组件, 如 director/jimeng)。
#
# 这两类都是**超集**: 门禁 docstring 常在解释原因时提到无关路径(如「跳过导演台,
# 那条线有并行 session 在改」), 于是提到 ≠ 覆盖。宁可多跑不可漏跑, 但使用者
# 必须能看出哪些是「我改的地方」, 哪些是「只是共用了同一个文件」。
if [ "$CHANGED_ONLY" -eq 1 ]; then
  # **两份都要**: 未推送的提交 + 工作区未提交改动。
  # 第一版写成「`origin/master...HEAD` 为空才去看工作区」, 于是**已经 push 过的
  # 提交 + 之后的新改动**这个最常见的组合会被整个漏掉 —— 那正是我实际的工作方式
  # (推完一批, 改点东西, 问「该跑哪些门禁」)。
  # 条件分支在这里是错的: 两个来源都要, 取并集。
  changed_files=$( { git diff --name-only origin/master...HEAD 2>/dev/null; \
                     git diff --name-only HEAD 2>/dev/null; } | sort -u )
  if [ -z "$changed_files" ]; then
    echo "no local changes found; nothing to run"
    exit 0
  fi
  # 只看代码改动。docs/ 下的截图与 md 不会驱动任何门禁, 计入只会白跑。
  code_files=$(printf '%s\n' "$changed_files" | grep -E '^(src|scripts)/' || true)
  if [ -z "$code_files" ]; then
    echo "local changes touch no code (src/ or scripts/); nothing to run"
    exit 0
  fi
  # 匹配判据(三种引用形式全要覆盖, 实测门禁真的三种都在用):
  #   ① 完整路径 `src/components/nodes/AudioNode.tsx`
  #   ② 裸文件名   `AudioNode.tsx`
  #   ③ **反引号组件名** `` `AudioNode` `` —— batch360/358/359 这批的 docstring
  #      全部用这种, **不带扩展名**。
  # 只认 ① 的第一版, 改 `AudioNode.tsx` 会报「无影响」—— 判据过窄的假零,
  # 比假绿更危险: 它让你以为该跑的已经跑过。逐层加判据时, 每次都实测一遍,
  # 发现一层不够再加一层, 不要一次猜到底。
  all_tokens=$(
    { grep -ohE 'src/[A-Za-z0-9_./-]+\.(tsx|ts|css)' scripts/verify-liblib-*.py 2>/dev/null
      grep -ohE '[A-Za-z0-9_/.-]+\.(tsx|ts|css)' scripts/verify-liblib-*.py 2>/dev/null | sed -E 's|.*/||'
      grep -ohE '`[A-Z][A-Za-z0-9_]+`' scripts/verify-liblib-*.py 2>/dev/null | tr -d '`'
    } | sort -u
  )
  changed_names=""
  for f in $(printf '%s\n' "$code_files" | grep -E '\.(tsx|ts|css)$'); do
    base=$(basename "$f")
    stem=${base%.*}
    printf '%s\n' "$all_tokens" | grep -qxF "$base" && changed_names="$changed_names $base"
    printf '%s\n' "$all_tokens" | grep -qxF "$stem" && changed_names="$changed_names $stem"
  done
  changed_names=$(printf '%s\n' $changed_names | sort -u | tr '\n' ' ')
  direct=""
  indirect=""
  for b in $SELECTED; do
    script="scripts/verify-liblib-batch$b.py"
    [ -f "$script" ] || continue
    if printf '%s\n' "$code_files" | grep -qxF "$script"; then
      direct="$direct $b"; continue
    fi
    # 该门禁提到、且本次被改动过的源文件名
    hit=no
    for s in $changed_names; do
      grep -qF "$s" "$script" && hit=yes
    done
    [ "$hit" = yes ] && indirect="$indirect $b"
  done
  SELECTED="$direct$indirect"
  if [ -z "$SELECTED" ]; then
    echo "no verifier appears affected by local changes"
    exit 0
  fi
  echo "direct (code I changed):$(printf ' %s' $direct)"
  [ -n "$indirect" ] && echo "collateral (shared files, incl. others' WIP):$(printf ' %s' $indirect)"
  echo "----"
fi

# ---- 前置: dev server 活着吗 ----
# 306 个验证器在服务器挂了时会全部报连接错误, 刷屏且零信息量。先探活。
if ! curl -fsS -o /dev/null --max-time 10 "$BASE_URL/" 2>/dev/null; then
  echo "FATAL: dev server not reachable at $BASE_URL"
  echo "       start it first (npm run dev), or set LIBLIB_BASE_URL"
  exit 2
fi

total=0
for b in $SELECTED; do
  [ -f "scripts/verify-liblib-batch$b.py" ] || continue
  total=$((total + 1))
done
if [ "$total" -eq 0 ]; then
  echo "no matching verifiers"
  exit 0
fi

LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/liblib-verifiers.XXXXXX")"
echo "running $total verifier(s) with $JOBS job(s); logs -> $LOG_DIR"
echo "----"

# 记下自身指纹: 跑完之后核对。
# 起因: 我在一次全量**运行期间**改了这个脚本, 重试阶段 bash 读到半改完的
# 版本, 直接报 `line 189: syntax error near unexpected token ';'` 并留下一堆
# 半成品结果。那是我不该在运行中改它 —— 但工具对此毫无提示, 报出来的错误
# 也完全指不到真因(「我明明刚 bash -n 过」)。
# 所以: 开工前记指纹, 收尾时核对, 被改过就**明确说这一轮结果不可信**。
SELF_DIGEST="$(shasum "$ROOT/scripts/run-liblib-verifiers.sh" 2>/dev/null | awk '{print $1}')"

# ---- 运行中: dev server 健康监测 (Batch 370) ----
# 起因是两次实测, 都不是猜的:
#
# 1. batch 367 做变异测试时, 我改了源文件立刻跑门禁, 门禁崩在
#    `Page.goto: net::ERR_CONNECTION_REFUSED` 上 —— exit 1, 但**一条断言都没跑到**。
#    我当时判它「结果不作数」, 可整轮里其它门禁的失败也同样被归到了「代码问题上」,
#    而我没有任何机制能看出区别。
# 2. batch 370 我在运行中 `touch` 了一个源文件(只改 mtime, 不改内容)触发
#    Next dev 重编译, 同一批 24 个门禁立刻大面积 `Page.wait_for_function` 超时。
#
# 关键点: **dev server 是共享可变资源**。Next dev 在源码变化后会重新编译,
# 编译窗口里的请求会挂; 并行 session 同时改文件、或同时在跑另一套验证器,
# 效果一样。而这些失败与「代码真的坏了」在汇总里长得**一模一样** —— 都是 FAIL。
#
# 所以这里起一个后台探针, 把运行期间的健康状况**记下来**, 收尾时如实交代:
# 跑歪了就不是一份干净的代码判决。
#
# 探针必须极其便宜(2s 一次 curl, 3s 超时), 且**绝不影响退出码**:
# 它的职责只是把「基础设施抖过」这件事从隐式变成显式。
HEALTH_FILE="$LOG_DIR/dev-server-health.log"
: > "$HEALTH_FILE"
(
  while :; do
    if ! curl -fsS -o /dev/null --max-time 3 "$BASE_URL/" 2>/dev/null; then
      echo "$(date +%H:%M:%S) unreachable" >> "$HEALTH_FILE"
    fi
    sleep 2
  done
) &
HEALTH_PID=$!
# 收尾时无论如何都要收掉它, 否则会变成游离后台进程一直 curl 下去。
cleanup_health() { kill "$HEALTH_PID" 2>/dev/null || true; }
trap cleanup_health EXIT INT TERM

# ---- 并发执行 ----
# 每个验证器一个独立 python 进程。xargs -P 按 JOBS 并行, 输出按顺序落文件。
# 用 `|| true` 吞掉退出码: 真实成败由后面读文件统计, 这样 xargs 不会因任一
# 非零退出而提前中断整批。
printf '%s\n' $SELECTED \
  | xargs -P "$JOBS" -I{} sh -c '
      b="$1"; root="$2"; py="$3"; logdir="$4"
      if [ -f "$root/scripts/verify-liblib-batch$b.py" ]; then
        if "$py" "$root/scripts/verify-liblib-batch$b.py" > "$logdir/$b.log" 2>&1; then
          echo "PASS $b" >> "$logdir/results"
        else
          echo "FAIL $b" >> "$logdir/results"
        fi
      fi
    ' _ {} "$ROOT" "$PY" "$LOG_DIR"

pass=0
fail=0
failed_list=""
missing_list=""
for b in $SELECTED; do
  [ -f "scripts/verify-liblib-batch$b.py" ] || continue
  if [ ! -f "$LOG_DIR/$b.log" ]; then
    # 进程在 python 启动前就被杀(xargs 被中断 / OOM), 连重定向都没建。
    # **必须算失败**: 第一版这里 `continue` 掉了, 门禁会从统计里彻底消失。
    missing_list="$missing_list $b"
    continue
  fi
  if [ ! -s "$LOG_DIR/$b.log" ]; then
    # 重定向已建但**零字节** —— 进程在产出任何输出前就被 SIGKILL 了。
    # 走普通 FAIL 会只留一行 shell 的 "Killed: 9", 看不出是被杀还是断言红。
    missing_list="$missing_list $b"
    echo "KILLED (empty output): batch$b"
    continue
  fi
  if grep -qxF "PASS $b" "$LOG_DIR/results" 2>/dev/null; then
    pass=$((pass + 1))
    echo "PASS batch$b"
  else
    fail=$((fail + 1))
    failed_list="$failed_list $b"
    echo "FAIL batch$b  (log: $LOG_DIR/$b.log)"
  fi
done
if [ -n "$missing_list" ]; then
  # 无输出者不并入重试(重试会重新拉起进程, 与「被外部杀掉」是两回事), 但要显式报出。
  fail=$((fail + 1))
  echo "MISSING (never produced output, e.g. killed):$missing_list"
  failed_list="$failed_list$missing_list"
fi

# ---- 失败自动重试 (与 frameos runner 同策) ----
# 并发负载下的偶发失败隔离; 隔离后仍红才算真回归。
#
# 重试通过时**必须同时把它从 failed_list 里剔除**。第一版只减了 fail 计数,
# 于是收尾打印的「failed batches:」里混着 13 个已经 RETRY PASS 的批次 ——
# 汇总说 19 failed, 清单却列了 33 个, **两个数字对不上**。
# 汇总与清单必须同源: 清单只放重试后仍红的。
if [ "$fail" -gt 0 ] && [ "$RETRIES" -gt 0 ]; then
  echo "---- retrying failed:$failed_list"
  still_failed=""
  for b in $failed_list; do
    if "$PY" "scripts/verify-liblib-batch$b.py" > "$LOG_DIR/$b.retry.log" 2>&1; then
      pass=$((pass + 1)); fail=$((fail - 1))
      echo "RETRY PASS batch$b"
    else
      echo "RETRY FAIL batch$b  (log: $LOG_DIR/$b.retry.log)"
      tail -5 "$LOG_DIR/$b.retry.log"
      still_failed="$still_failed $b"
    fi
  done
  failed_list="$still_failed"
fi

# ---- AGED_GATE 单独归类(必须在重试之后) ----
# 带 `AGED_GATE / HISTORICAL_CONTRACT` 标记的门禁(本线 12 个)是自己声明的
# **历史遗留**: 在基线 86673b6 上同样失败, 已被 LIBTV_VERIFIER_REPLACEMENT_MAP
# 里的现行门禁取代。它们的红不是回归, 混进「failed batches」会让人每次全量
# 都以为欠了一批债, 而其中两个根本不该再修。
# 判据 = 门禁自己写的标记, **不按批次号开名单** —— 名单会在重构中悄悄失效。
aged_list=""
live_list=""
for b in $failed_list; do
  if grep -q "AGED_GATE" "scripts/verify-liblib-batch$b.py" 2>/dev/null; then
    aged_list="$aged_list $b"
  else
    live_list="$live_list $b"
  fi
done
if [ -n "$aged_list" ]; then
  aged_n=$(printf '%s\n' $aged_list | wc -l | tr -d ' ')
  echo "note: $aged_n of those are AGED_GATE (declared historical, not regressions):$aged_list"
fi

echo "----"

# ---- 自我保护: 这一轮的结果可信吗 ----
# 脚本在运行期间被改动过, 则后半段(统计/重试/汇总)跑的是**另一个版本**,
# 报出来的数字没有意义。宁可退出码非零让人重跑, 也不给一份看似正常的错账。
SELF_DIGEST_NOW="$(shasum "$ROOT/scripts/run-liblib-verifiers.sh" 2>/dev/null | awk '{print $1}')"
SELF_CHANGED=0
if [ -n "$SELF_DIGEST" ] && [ "$SELF_DIGEST" != "$SELF_DIGEST_NOW" ]; then
  SELF_CHANGED=1
fi

if [ "$SELF_CHANGED" -eq 1 ]; then
  echo "FATAL: this script changed WHILE RUNNING."
  echo "       The tally below was produced by a different version of the"
  echo "       script than the one that started this run, so it cannot be"
  echo "       trusted. Re-run without editing the runner concurrently."
  echo "       logs kept at $LOG_DIR"
  exit 3
fi

echo "liblib verifiers: $pass passed, $fail failed (of $total, after $RETRIES retry)"

# ---- 这一轮的基础设施状况(必须**在**报数旁边说, 不能只在心里知道) ----
# 汇总数字和「这份数字能不能当代码判决」是两件事。
# dev server 抖过 => 失败里混着基础设施噪声, 这时只报一个干净数字就是误导。
cleanup_health
health_bad=0
if [ -f "$HEALTH_FILE" ]; then
  # 不用 `grep -c ... || echo 0`: `grep -c` **无匹配时会打印 0 并且返回 1**,
  # 于是 `|| echo 0` 会把结果拼成 "0\n0", 后面 `[ "$x" -gt 0 ]` 直接报
  # `integer expression expected` —— 这是自检跑出来的第一处 bug。
  # `grep | wc -l` 永远只吐一个数, 不会双吐。
  health_bad=$(grep "unreachable" "$HEALTH_FILE" 2>/dev/null | wc -l | tr -d ' ')
fi
if [ "${health_bad:-0}" -gt 0 ] 2>/dev/null; then
  echo "WARNING: dev server was UNREACHABLE $health_bad time(s) during this run."
  echo "         Failures above may be infrastructure noise, not code regressions:"
  echo "         Next dev recompiles on any source change (yours OR a parallel"
  echo "         session's), and requests fail while it rebuilds."
  echo "         Re-run the failed batches before treating them as regressions."
  echo "         probe log: $HEALTH_FILE"
fi
if [ -n "$aged_list" ]; then
  echo "(AGED_GATE historical contracts above are declared, not regressions)"
fi
if [ "$fail" -ne 0 ]; then
  echo "failed batches:$failed_list"
  echo "logs kept at $LOG_DIR"
  exit 1
fi
rm -rf "$LOG_DIR"
exit 0

