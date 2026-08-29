import type {
  DirectorCommandDisposition,
  DirectorCommandReason,
  DirectorCommandResult,
} from "@/lib/directorCommandKernel";

export type DirectorCommandFeedbackTone = "neutral" | "warning" | "error";

export interface DirectorCommandFeedback {
  disposition: Exclude<DirectorCommandDisposition, "COMMITTED">;
  reason: DirectorCommandReason | null;
  tone: DirectorCommandFeedbackTone;
  message: string;
}

const REASON_MESSAGES: Readonly<
  Partial<Record<DirectorCommandReason, string>>
> = {
  DIRECTOR_OWNER_STALE: "导演台会话已失效，未应用结果",
  DIRECTOR_PROJECT_MISSING: "导演台项目不可用，请重新打开",
  DIRECTOR_TARGET_MISSING: "目标对象不存在，未应用修改",
  DIRECTOR_TARGET_LOCKED: "目标对象已锁定，未应用修改",
  DIRECTOR_INVALID_VALUE: "输入值无效，未应用修改",
  DIRECTOR_REFERENCE_INVALID: "对象引用无效，未应用修改",
  DIRECTOR_COMMAND_NO_CHANGE: "内容未发生变化",
  DIRECTOR_DELETE_BLOCKED: "对象仍被引用，无法删除",
  DIRECTOR_LAST_CAMERA_REQUIRED: "至少需要保留一个机位",
  DIRECTOR_RESOURCE_IN_USE: "资源仍在使用中，暂时无法删除",
  DIRECTOR_GESTURE_NOT_ACTIVE: "当前没有进行中的编辑操作",
  DIRECTOR_HISTORY_EMPTY: "没有可撤销或重做的操作",
  DIRECTOR_HISTORY_CONFLICT: "历史状态已变化，未执行该操作",
  DIRECTOR_CLIPBOARD_EMPTY: "当前没有可复制或粘贴的对象",
  DIRECTOR_CLIPBOARD_STALE: "复制内容已失效，请重新复制",
  DIRECTOR_CLIPBOARD_INVALID: "复制内容无效，未执行粘贴",
  DIRECTOR_IMPORT_INVALID: "项目文件无效，未修改当前项目",
  DIRECTOR_IMPORT_BUSY: "当前操作进行中，请稍后重试",
  DIRECTOR_IMPORT_TOMBSTONED: "该导演台项目已删除，无法重新打开",
  DIRECTOR_POLICY_UNKNOWN: "当前操作无法安全处理",
};

function getMessage(result: DirectorCommandResult): string {
  if (
    result.reason === "DIRECTOR_HISTORY_EMPTY" &&
    result.commandKind === "UNDO"
  ) {
    return "没有可撤销的操作";
  }
  if (
    result.reason === "DIRECTOR_HISTORY_EMPTY" &&
    result.commandKind === "REDO"
  ) {
    return "没有可重做的操作";
  }
  return (
    (result.reason ? REASON_MESSAGES[result.reason] : undefined) ??
    "当前操作未完成，未修改项目"
  );
}

function getTone(
  disposition: Exclude<DirectorCommandDisposition, "COMMITTED">,
): DirectorCommandFeedbackTone {
  if (disposition === "NOOP") return "neutral";
  if (disposition === "CONFLICT" || disposition === "STALE") {
    return "warning";
  }
  return "error";
}

export function getDirectorCommandFeedback(
  result: DirectorCommandResult | null,
): DirectorCommandFeedback | null {
  if (!result || result.disposition === "COMMITTED") return null;
  if (
    result.disposition === "NOOP" &&
    result.reason !== "DIRECTOR_COMMAND_NO_CHANGE" &&
    result.reason !== "DIRECTOR_HISTORY_EMPTY" &&
    result.reason !== "DIRECTOR_GESTURE_NOT_ACTIVE" &&
    result.reason !== "DIRECTOR_CLIPBOARD_EMPTY" &&
    result.reason !== "DIRECTOR_CLIPBOARD_STALE"
  ) {
    return null;
  }
  return {
    disposition: result.disposition,
    reason: result.reason,
    tone: getTone(result.disposition),
    message: getMessage(result),
  };
}
