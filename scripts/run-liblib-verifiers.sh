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
  changed_files=$(git diff --name-only origin/master...HEAD 2>/dev/null)
  if [ -z "$changed_files" ]; then
    changed_files=$(git diff --name-only HEAD 2>/dev/null)
  fi
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
  # 一次性建「被改动的 src 文件 -> 提及它的门禁」反查表。
  # 早先版本对 306 个门禁逐个 grep, 光扫描就要几分钟。这里改为先把所有门禁的
  # src 引用一次性抓出来排序去重, 再与改动集合求交 —— 306 次进程调用变 1 次。
  all_srcs=$(grep -ohE 'src/[A-Za-z0-9_./-]+\.(tsx|ts|css)' \
               scripts/verify-liblib-*.py 2>/dev/null | sort -u)
  changed_srcs=""
  for s in $all_srcs; do
    printf '%s\n' "$code_files" | grep -qxF "$s" && changed_srcs="$changed_srcs $s"
  done
  direct=""
  indirect=""
  for b in $SELECTED; do
    script="scripts/verify-liblib-batch$b.py"
    [ -f "$script" ] || continue
    if printf '%s\n' "$code_files" | grep -qxF "$script"; then
      direct="$direct $b"; continue
    fi
    # 该门禁 docstring 里提到、且本次被改动的 src 文件
    hit=no
    for s in $changed_srcs; do
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
if [ "$fail" -gt 0 ] && [ "$RETRIES" -gt 0 ]; then
  echo "---- retrying failed:$failed_list"
  for b in $failed_list; do
    if "$PY" "scripts/verify-liblib-batch$b.py" > "$LOG_DIR/$b.retry.log" 2>&1; then
      pass=$((pass + 1)); fail=$((fail - 1))
      echo "RETRY PASS batch$b"
    else
      echo "RETRY FAIL batch$b  (log: $LOG_DIR/$b.retry.log)"
      tail -5 "$LOG_DIR/$b.retry.log"
    fi
  done
fi

echo "----"
echo "liblib verifiers: $pass passed, $fail failed (of $total, after $RETRIES retry)"
if [ "$fail" -ne 0 ]; then
  echo "failed batches:$failed_list"
  echo "logs kept at $LOG_DIR"
  exit 1
fi
rm -rf "$LOG_DIR"
exit 0
