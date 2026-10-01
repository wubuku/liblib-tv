#!/usr/bin/env bash
# FrameOS 克隆验证器统一入口 (Batch 184)
# 用法:
#   bash scripts/run-frameos-verifiers.sh            # 跑全部
#   bash scripts/run-frameos-verifiers.sh 171 172    # 只跑指定批次
# 前置: dev server 已运行在 $LIBLIB_BASE_URL (默认 http://localhost:4317),
#       python 需有 playwright (~/.pyenv/versions/3.10.6/bin/python 已验证可用)。

set -u

PY="${FRAMEOS_PYTHON:-$HOME/.pyenv/versions/3.10.6/bin/python}"
[ -x "$PY" ] || PY="python3"
BASE_URL="${LIBLIB_BASE_URL:-http://localhost:4317}"
export LIBLIB_BASE_URL="$BASE_URL"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 全量清单: 动态发现 scripts/verify-frameos-batch*.py (Batch 194 起自维护);
# batch168 已随源站新版本退役, 如残留脚本则跳过
RETIRED="168"
if [ "$#" -gt 0 ]; then
  BATCHES="$*"
else
  BATCHES=$(ls "$ROOT"/scripts/verify-frameos-batch*.py 2>/dev/null \
    | sed -E 's/.*batch([0-9]+)\.py/\1/' | sort -n | tr '\n' ' ')
fi

pass=0
fail=0
failed_list=""

# ---- 前置: dev server 活着吗 ----
# Batch 371: 原来**没有**这道探活。dev server 挂掉时, 200 多个验证器会集体报
# 连接错误 —— 刷屏且零信息量, 而「服务器没起」和「代码坏了」在输出里长得一样。
# liblib runner 早就有了这道(batch 361), 这次对齐。
if ! curl -fsS -o /dev/null --max-time 10 "$BASE_URL/" 2>/dev/null; then
  echo "FATAL: dev server not reachable at $BASE_URL"
  echo "       start it first (npm run dev), or set LIBLIB_BASE_URL"
  exit 2
fi

# ---- 记下自身指纹: 收尾核对 ----
# Batch 371: 原来没有。若脚本在运行期间被改动, 统计/重试/汇总跑的是**另一个版本**,
# 报出来的数字没有意义。宁可退出码非零让人重跑, 也不给一份看似正常的错账。
# liblib runner 早已有这道(batch 361), 这次对齐。
SELF_DIGEST="$(shasum "$ROOT/scripts/run-frameos-verifiers.sh" 2>/dev/null | awk '{print $1}')"

# ---- 运行中: dev server 健康监测 ----
# dev server 是**共享可变资源**: Next dev 在源码变化后重新编译, 编译窗口里请求
# 会挂; 并行 session 改文件、或同时跑另一套验证器, 效果一样。而这些失败与
# 「代码真的坏了」在汇总里**长得一模一样**。
# 所以起一个便宜的后台探针(2s 一次, 3s 超时), 收尾时如实交代抖没抖过。
# 证据: liblib batch 370 用假服务器做过双向自检(先返 200 再返 503)。
HEALTH_FILE="$(mktemp "${TMPDIR:-/tmp}/frameos-health.XXXXXX")"
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
# 收尾时无论如何都要收掉, 否则会变成一直 curl 下去��游离后台进程。
cleanup_health() { kill "$HEALTH_PID" 2>/dev/null || true; }
trap cleanup_health EXIT INT TERM

for b in $BATCHES; do
  script="scripts/verify-frameos-batch$b.py"
  if [ ! -f "$script" ]; then
    echo "skip batch$b (no verifier)"
    continue
  fi
  for r in $RETIRED; do
    if [ "$b" = "$r" ]; then
      echo "skip batch$b (retired)"
      continue 2
    fi
  done
  if out=$("$PY" "$script" 2>&1); then
    pass=$((pass + 1))
    echo "PASS batch$b"
  else
    fail=$((fail + 1))
    failed_list="$failed_list $b"
    echo "FAIL batch$b"
    echo "$out" | tail -5
  fi
done

# Batch 215: 失败批次自动重试一次 (偶发失败隔离)
#
# Batch 371 修: **重试通过时必须同时把它从 failed_list 里剔除**。
# 原来只重算 `fail` 计数, `failed_list` 一直留着首轮的原始失败 ——
# 于是收尾输出**汇总与清单不同源**。实测(两个临时探针: 一个必败, 一个首败次过):
#
#   frameos verifiers: 1 passed, 1 failed (after retry)
#   failed batches: 9001 9002          ← 刚打印过 RETRY PASS batch9002
#
# 名义 1 个失败, 清单列了 2 个。同样的 bug 在 liblib runner 上早已修过
# (那里写着「汇总与清单必须同源」), 这边一直漏着。清单只放重试后仍红的。
if [ "$fail" -gt 0 ]; then
  echo "---- retrying failed batches:$failed_list"
  still_failed=""
  for b in $failed_list; do
    if out=$("$PY" "scripts/verify-frameos-batch$b.py" 2>&1); then
      # 重试通过: 从失败计数里**去掉**(它首轮已被 +1), 并计入通过
      pass=$((pass + 1)); fail=$((fail - 1))
      echo "RETRY PASS batch$b"
    else
      # 重试仍败: 计数**不变**(首轮那 +1 就是它), 只进清单。
      # 这里千万别再 fail-- —— 我第一版改写时在两个分支都写了 `fail--`,
      # 结果 fail 恒为 0, 汇总会说「0 failed」而清单非空, 又造出一个
      # 新的「汇总与清单不同源」。计数规则只有一条:
      #   **首轮 +1; 重试通过 -1; 重试仍败不动。**
      echo "RETRY FAIL batch$b"
      echo "$out" | tail -5
      still_failed="$still_failed $b"
    fi
  done
  failed_list="$still_failed"
fi

echo "----"

# ---- 这一轮的结果可信吗 ----
SELF_DIGEST_NOW="$(shasum "$ROOT/scripts/run-frameos-verifiers.sh" 2>/dev/null | awk '{print $1}')"
if [ -n "$SELF_DIGEST" ] && [ "$SELF_DIGEST" != "$SELF_DIGEST_NOW" ]; then
  cleanup_health
  echo "FATAL: this script changed WHILE RUNNING."
  echo "       The tally below was produced by a different version of the"
  echo "       script than the one that started this run, so it cannot be"
  echo "       trusted. Re-run without editing the runner concurrently."
  exit 3
fi

echo "frameos verifiers: $pass passed, $fail failed (after retry)"

# 汇总数字和「这份数字能不能当代码判决」是两件事。dev server 抖过 => 失败里混着
# 基础设施噪声, 这时只报一个干净数字就是误导。
cleanup_health
health_bad=0
if [ -f "$HEALTH_FILE" ]; then
  # 不用 `grep -c ... || echo 0`: `grep -c` **无匹配时打印 0 且返回 1**,
  # `|| echo 0` 会把结果拼成 "0\n0", 后面整数比较直接报错。
  # (这个坑在 liblib runner 上踩过一次, 别再踩。) `grep | wc -l` 只吐一个数。
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

[ "$fail" -eq 0 ] || { echo "failed batches:$failed_list"; exit 1; }
