import assert from "node:assert/strict";
import {
  createDirectorCommandResult,
} from "../src/lib/directorCommandKernel.ts";
import { getDirectorCommandFeedback } from "../src/lib/directorCommandFeedback.ts";

function result(
  disposition,
  reason,
  commandKind = "TEST_COMMAND",
) {
  return createDirectorCommandResult({
    commandKind,
    projectId: "batch83-project",
    generation: 1,
    disposition,
    reason,
  });
}

assert.equal(getDirectorCommandFeedback(null), null);
assert.equal(getDirectorCommandFeedback(result("COMMITTED", null)), null);

const invalid = getDirectorCommandFeedback(
  result("REJECTED", "DIRECTOR_INVALID_VALUE"),
);
assert.ok(invalid);
assert.equal(invalid.tone, "error");
assert.equal(invalid.message, "输入值无效，未应用修改");

const stale = getDirectorCommandFeedback(
  result("STALE", "DIRECTOR_OWNER_STALE"),
);
assert.ok(stale);
assert.equal(stale.tone, "warning");
assert.equal(stale.message, "导演台会话已失效，未应用结果");

const conflict = getDirectorCommandFeedback(
  result("CONFLICT", "DIRECTOR_HISTORY_CONFLICT"),
);
assert.ok(conflict);
assert.equal(conflict.tone, "warning");
assert.equal(conflict.message, "历史状态已变化，未执行该操作");

const undoEmpty = getDirectorCommandFeedback(
  result("NOOP", "DIRECTOR_HISTORY_EMPTY", "UNDO"),
);
assert.ok(undoEmpty);
assert.equal(undoEmpty.message, "没有可撤销的操作");

const redoEmpty = getDirectorCommandFeedback(
  result("NOOP", "DIRECTOR_HISTORY_EMPTY", "REDO"),
);
assert.ok(redoEmpty);
assert.equal(redoEmpty.message, "没有可重做的操作");

const changeNoop = getDirectorCommandFeedback(
  result("NOOP", "DIRECTOR_COMMAND_NO_CHANGE"),
);
assert.ok(changeNoop);
assert.equal(changeNoop.tone, "neutral");
assert.equal(changeNoop.message, "内容未发生变化");

assert.equal(
  getDirectorCommandFeedback(
    result("NOOP", "DIRECTOR_GESTURE_NOT_ACTIVE", "TEST_COMMAND"),
  )?.message,
  "当前没有进行中的编辑操作",
);

const unknown = getDirectorCommandFeedback(
  result("UNKNOWN", "DIRECTOR_POLICY_UNKNOWN"),
);
assert.ok(unknown);
assert.equal(unknown.tone, "error");
assert.equal(unknown.message, "当前操作无法安全处理");

console.log(
  JSON.stringify({
    batch: 83,
    status: "PASS",
    cases: {
      committedHidden: true,
      rejectedVisibleMapping: true,
      staleWarningMapping: true,
      conflictWarningMapping: true,
      noOpRecoveryMapping: true,
      unknownBoundedFallback: true,
    },
  }),
);
