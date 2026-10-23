#!/usr/bin/env bash
# ⭐⭐⭐⭐⭐ 批 1032-②l：**全门禁清单进仓**
#
#   ⇒ ⇒⇒ ⇒ 以前这份清单只活在 `/tmp` 里 ⇒ ⇒⇒ ⇒ 于是「28/28 全绿」这句话
#   ⇒ ⇒⇒ ⇒ ⇒ **谁也复现不了**（清单本身不在仓里）⇒ ⇒⇒ ⇒ ⇒
#   ⇒ ⇒⇒ ⇒ ⇒ ⇒ 把它提交进来，它就是一份**可核对的承诺**
#
#   ⭐⭐⭐⭐⭐ **顺序是有讲究的：1014 必须放在最后**
#     ⇒ ⇒⇒⇒ ⇒ 门禁清单里有一半探针会**重写自己的产物**
#     ⇒ ⇒⇒⇒ ⇒ ⇒ 而 1014 的指纹表记着**别的产物的字节**
#     ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 若 1014 排在中间 ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ ⇒
#     ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **它后面那些探针一跑，这张表就过期了**
#     ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 下一轮清单的头一道门就会红
#     ⇒ ⇒⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而那不是「谁弄坏了」，是**顺序错了**
#
#   ⇒ ⇒⇒⇒ ⇒ 用法：`bash scripts/jimeng_run_all_gates.sh`
#   ⇒ ⇒⇒⇒ ⇒ 日志默认写 `/tmp/jimeng_gates.log`（`GATE_LOG=…` 可改）
set -u
cd "$(git rev-parse --show-toplevel)"
PY=~/.venvs/jimeng-py312/bin/python
HARNESS=~/.venvs/liblib-harness/bin/python
LOG=${GATE_LOG:-/tmp/jimeng_gates.log}
: > "$LOG"
N_OK=0
N_FAIL=0
FAILED=""
run() {
  local name="$1"; shift
  local t0=$(date +%s)
  local rc=0
  "$@" >> "$LOG" 2>&1 || rc=$?
  local t1=$(date +%s)
  printf '%-34s rc=%-3s %ss\n' "$name" "$rc" "$((t1-t0))" | tee -a "$LOG"
  if [ "$rc" -eq 0 ]; then
    N_OK=$((N_OK + 1))
  else
    N_FAIL=$((N_FAIL + 1))
    FAILED="$FAILED $name"
  fi
}

echo "=== jimeng 全门禁 $(date '+%F %T') ===" | tee -a "$LOG"

# ── 第 0 位：**指纹表核对门** ─────────────────────────────────────────────
#   ⇒ 它比的是「**上一次落盘的那张表**」与「盘上的字节」
#   ⇒ ⇒⇒ ⇒ 所以它必须**第一个跑**（先报出真相）⇒ ⇒⇒ ⇒
#   ⇒ ⇒⇒ ⇒ 而 1014 在**最后**跑（跑完树才重新自洽）⇒ ⇒⇒ ⇒
run "1032l-fingerprint-gate"    $PY scripts/jimeng_probe1032l_fingerprint_gate.py
run "1032l-fingerprint-selftest" $PY scripts/jimeng_probe1032l_fingerprint_gate.py --selftest

# ── 第 0 位之二：**提交态新鲜度门** ─────────────────────────────────────
#   ⇒ 它答的是「**提交的那本 == 探针现在会写的那本**」⇒ ⇒⇒ ⇒
#   ⇒ ⇒⇒ ⇒ 而 1015 答的是「跑两遍会不会变」⇒ ⇒⇒ ⇒ ⇒ **两个口径不许合并** ⇒ ⇒⇒ ⇒
#   ⇒ ⇒⇒ ⇒ 而它必须排在 **verifier 之前** ⇒ ⇒⇒ ⇒ ⇒
#   ⇒ ⇒⇒ ⇒ ⇒ ⇒ **因为 verifier 的 DD993AJ.1 要在真树上跑它一遍** ⇒ ⇒⇒ ⇒ ⇒ ⇒
#   ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而「门自己能不能被证伪」是另一件事 ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒
#   ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 它自带五发注入式反证 ⇒ ⇒⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 不用另开一道门
run "1032n-committed-fresh" $PY scripts/jimeng_probe1032n_committed_freshness_gate.py

run "verifier-841"          $PY scripts/verify-jimeng-batch841-unclickable.py
run "anchor-gate"           $PY scripts/jimeng_check_verifier_anchors.py
run "1018-assertion"        $PY scripts/jimeng_probe1018_assertion_vs_behavior.py
run "1019-harness"          $PY scripts/jimeng_probe1019_behavior_harness.py
run "1027-freshness"        $PY scripts/jimeng_probe1027_freshness_gate.py
run "1027-selftest"         $PY scripts/jimeng_probe1027_freshness_gate.py --selftest
run "1021-anchor-cov"       $PY scripts/jimeng_probe1021_anchor_gate_coverage.py
run "1032a-connect"         $PY scripts/jimeng_probe1032a_connect_contract.py
run "1032b2-gen"            $PY scripts/jimeng_probe1032b2_gen_contract.py
run "1032b3-mention"        $PY scripts/jimeng_probe1032b3_mention_contract.py
run "1032b3-crash-self"     $PY scripts/jimeng_probe1032b3_crash_selftest.py
run "1032b4-expanded"       $PY scripts/jimeng_probe1032b4_expanded_contract.py
run "1032c-noop"            $PY scripts/jimeng_probe1032c_noop_contract.py
run "1032-mjs-wiring"       node scripts/jimeng_probe1032_interaction_wiring.mjs
run "1032-build-allowlist"  $PY scripts/jimeng_probe1032_build_allowlist.py
run "1032-allowlist-self"   $PY scripts/jimeng_probe1032_build_allowlist.py --self-test
run "812-harness"           $HARNESS scripts/verify-jimeng-batch812.py
run "1005-census"           $PY scripts/jimeng_probe1005_zero_coupling_census.py
run "1007-disparate"        $PY scripts/jimeng_probe1007_disparate_copies.py
run "1008-golden"           $PY scripts/jimeng_probe1008_golden_freshness.py
run "1009-edit-vis"         $PY scripts/jimeng_probe1009_edit_visibility.py
run "1010-real-history"     $PY scripts/jimeng_probe1010_real_history_detection.py
run "1011-change-local"     $PY scripts/jimeng_probe1011_change_locality.py
run "1012-global"           $PY scripts/jimeng_probe1012_global_detection.py
run "1013-occurrence"       $PY scripts/jimeng_probe1013_occurrence_ledger.py
run "tsc"                   npx tsc --noEmit
run "eslint-jimeng"         npx eslint src/components/jimeng

# ── **最后**才跑 1014：它刷新指纹表 ⇒ 跑完这一轮，树重新自洽 ────────────
run "1014-empty-ambig"      $PY scripts/jimeng_probe1014_empty_ambiguity.py

echo "=== 完成 $(date '+%F %T') —— $N_OK 项绿 / $N_FAIL 项红 ===" | tee -a "$LOG"
if [ "$N_FAIL" -ne 0 ]; then
  echo "红的门：$FAILED" | tee -a "$LOG"
  exit 1
fi
exit 0
