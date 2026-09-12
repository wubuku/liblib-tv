// Batch 445 (VR-022 Slice A): pure editor profile/session/history model per
// LIBTV_EDITOR_SESSION_COMMIT_HISTORY_CONTRACT §5-§10. Pure only — no React,
// store or runtime changes; the graph commit adapter is Slice B.

export type LibTVEditorProfileId =
  | "INLINE_SCALAR"
  | "INLINE_MULTILINE"
  | "RICH_TEXT"
  | "MODAL_CONFIG"
  | "RECORD_EDITOR"
  | "BITMAP_EDITOR"
  | "RANGE_SELECTOR"
  | "REQUEST_DRAFT"
  | "LIVE_COALESCED_INSPECTOR"
  | "EMPTY_EVIDENCE_GATED";

export type LibTVEditorCommitTrigger =
  | "enter"
  | "blur"
  | "explicit-submit"
  | "apply"
  | "confirm"
  | "submit-async"
  | "gesture-end";

export type LibTVEditorHistoryOwner =
  | "native"
  | "custom"
  | "none"
  | "coalesced-graph";

export interface LibTVEditorProfile {
  profileId: LibTVEditorProfileId;
  version: 1;
  commitTriggers: readonly LibTVEditorCommitTrigger[];
  escapePolicy: "cancel" | "layered";
  historyOwner: LibTVEditorHistoryOwner;
  acceptance: "sync" | "async-descriptor" | "none";
  evidenceGated: boolean;
  normalization:
    | "trim-title"
    | "preserve-whitespace"
    | "sanitize-html"
    | "records"
    | "config"
    | "range"
    | "none";
}

const PROFILE = (
  profile: Omit<LibTVEditorProfile, "version">,
): LibTVEditorProfile => ({ ...profile, version: 1 });

export const LIBTV_EDITOR_PROFILES: Record<
  LibTVEditorProfileId,
  LibTVEditorProfile
> = {
  INLINE_SCALAR: PROFILE({
    profileId: "INLINE_SCALAR",
    commitTriggers: ["enter", "blur"],
    escapePolicy: "cancel",
    historyOwner: "native",
    acceptance: "sync",
    evidenceGated: false,
    normalization: "trim-title",
  }),
  INLINE_MULTILINE: PROFILE({
    profileId: "INLINE_MULTILINE",
    commitTriggers: ["explicit-submit", "blur"],
    escapePolicy: "cancel",
    historyOwner: "native",
    acceptance: "sync",
    evidenceGated: false,
    normalization: "preserve-whitespace",
  }),
  RICH_TEXT: PROFILE({
    profileId: "RICH_TEXT",
    commitTriggers: ["explicit-submit", "apply", "blur"],
    escapePolicy: "cancel",
    historyOwner: "custom",
    acceptance: "sync",
    evidenceGated: false,
    normalization: "sanitize-html",
  }),
  MODAL_CONFIG: PROFILE({
    profileId: "MODAL_CONFIG",
    commitTriggers: ["apply"],
    escapePolicy: "cancel",
    historyOwner: "custom",
    acceptance: "sync",
    evidenceGated: false,
    normalization: "config",
  }),
  RECORD_EDITOR: PROFILE({
    profileId: "RECORD_EDITOR",
    commitTriggers: ["explicit-submit"],
    escapePolicy: "cancel",
    historyOwner: "custom",
    acceptance: "sync",
    evidenceGated: false,
    normalization: "records",
  }),
  BITMAP_EDITOR: PROFILE({
    profileId: "BITMAP_EDITOR",
    commitTriggers: ["explicit-submit"],
    escapePolicy: "cancel",
    historyOwner: "custom",
    acceptance: "sync",
    evidenceGated: false,
    normalization: "records",
  }),
  RANGE_SELECTOR: PROFILE({
    profileId: "RANGE_SELECTOR",
    commitTriggers: ["confirm"],
    escapePolicy: "cancel",
    historyOwner: "none",
    acceptance: "sync",
    evidenceGated: false,
    normalization: "range",
  }),
  REQUEST_DRAFT: PROFILE({
    profileId: "REQUEST_DRAFT",
    commitTriggers: ["submit-async"],
    escapePolicy: "cancel",
    historyOwner: "native",
    acceptance: "async-descriptor",
    evidenceGated: false,
    normalization: "preserve-whitespace",
  }),
  LIVE_COALESCED_INSPECTOR: PROFILE({
    profileId: "LIVE_COALESCED_INSPECTOR",
    commitTriggers: ["gesture-end", "blur"],
    escapePolicy: "layered",
    historyOwner: "coalesced-graph",
    acceptance: "sync",
    evidenceGated: false,
    normalization: "none",
  }),
  EMPTY_EVIDENCE_GATED: PROFILE({
    profileId: "EMPTY_EVIDENCE_GATED",
    commitTriggers: [],
    escapePolicy: "cancel",
    historyOwner: "none",
    acceptance: "none",
    evidenceGated: true,
    normalization: "none",
  }),
};

export function getLibTVEditorProfile(
  profileId: LibTVEditorProfileId,
): LibTVEditorProfile {
  return LIBTV_EDITOR_PROFILES[profileId];
}

// §5.2 invalid profile combinations as pure invariant checks.
export function getLibTVProfileInvariantViolations(
  profile: LibTVEditorProfile,
): string[] {
  const violations: string[] = [];
  if (
    profile.profileId === "EMPTY_EVIDENCE_GATED" &&
    (profile.commitTriggers.length > 0 || profile.acceptance !== "none")
  ) {
    violations.push("evidence-gated profile exposes an acceptance command");
  }
  if (
    profile.profileId === "LIVE_COALESCED_INSPECTOR" &&
    profile.historyOwner !== "coalesced-graph"
  ) {
    violations.push("live inspector must coalesce graph history");
  }
  if (
    profile.profileId === "BITMAP_EDITOR" &&
    profile.normalization !== "records"
  ) {
    violations.push("bitmap editor must compare operation/record fingerprints");
  }
  if (
    profile.profileId === "INLINE_MULTILINE" &&
    profile.commitTriggers.includes("enter")
  ) {
    violations.push(
      "multiline inline editor may not use bare Enter as commit unless the source contract reserves it",
    );
  }
  return violations;
}

// §9.1 semantic normalization for the string-valued profiles.
export function normalizeLibTVEditorValue(
  profile: LibTVEditorProfile,
  value: string,
): string {
  switch (profile.normalization) {
    case "trim-title":
      return value.trim();
    case "preserve-whitespace":
      return value;
    default:
      return value;
  }
}

export function isLibTVEditorNoOp(
  profile: LibTVEditorProfile,
  baseline: string,
  draft: string,
): boolean {
  return (
    normalizeLibTVEditorValue(profile, baseline) ===
    normalizeLibTVEditorValue(profile, draft)
  );
}

// §7 session state machine (reducer subset for the local model).
export type LibTVEditorSessionState =
  | "CLOSED"
  | "OPEN_CLEAN"
  | "OPEN_DIRTY"
  | "COMMITTING_SYNC"
  | "ACCEPTED"
  | "REJECTED_RETRYABLE"
  | "INVALIDATED"
  | "DISPOSING";

export interface LibTVEditorSessionSnapshot {
  state: LibTVEditorSessionState;
  profileId: LibTVEditorProfileId;
  baseline: string;
  draft: string;
  dirty: boolean;
}

export type LibTVEditorSessionEvent =
  | { type: "open"; profileId: LibTVEditorProfileId; baseline: string }
  | { type: "edit"; value: string }
  | { type: "cancel" }
  | { type: "commit-sync" }
  | { type: "commit-accepted" }
  | { type: "commit-rejected" }
  | { type: "invalidate" }
  | { type: "disposed" };

export type LibTVEditorSessionOutcome =
  | "handled"
  | "handled-noop"
  | "rejected-transition"
  | "rejected-invalid-draft";

export interface LibTVEditorSessionResult {
  snapshot: LibTVEditorSessionSnapshot;
  outcome: LibTVEditorSessionOutcome;
  reason?: string;
}

const CLOSED_SNAPSHOT: LibTVEditorSessionSnapshot = {
  state: "CLOSED",
  profileId: "INLINE_SCALAR",
  baseline: "",
  draft: "",
  dirty: false,
};

export function reduceLibTVEditorSession(
  snapshot: LibTVEditorSessionSnapshot,
  event: LibTVEditorSessionEvent,
): LibTVEditorSessionResult {
  const reject = (reason: string): LibTVEditorSessionResult => ({
    snapshot,
    outcome: "rejected-transition",
    reason,
  });
  const profileOf = () => getLibTVEditorProfile(snapshot.profileId);

  switch (event.type) {
    case "open": {
      if (snapshot.state !== "CLOSED") {
        return reject("session already open");
      }
      const profile = getLibTVEditorProfile(event.profileId);
      if (profile.evidenceGated) {
        return reject("evidence-gated profile cannot open a semantic session");
      }
      return {
        snapshot: {
          state: "OPEN_CLEAN",
          profileId: event.profileId,
          baseline: event.baseline,
          draft: event.baseline,
          dirty: false,
        },
        outcome: "handled",
      };
    }
    case "edit": {
      if (
        snapshot.state !== "OPEN_CLEAN" &&
        snapshot.state !== "OPEN_DIRTY"
      ) {
        return reject("no open editable session");
      }
      const dirty = !isLibTVEditorNoOp(
        profileOf(),
        snapshot.baseline,
        event.value,
      );
      return {
        snapshot: {
          ...snapshot,
          state: dirty ? "OPEN_DIRTY" : "OPEN_CLEAN",
          draft: event.value,
          dirty,
        },
        outcome: dirty ? "handled" : "handled-noop",
      };
    }
    case "cancel": {
      if (
        snapshot.state === "CLOSED" ||
        snapshot.state === "DISPOSING" ||
        snapshot.state === "COMMITTING_SYNC"
      ) {
        return reject("cancel not allowed from this state");
      }
      return {
        snapshot: { ...snapshot, state: "DISPOSING" },
        outcome: "handled",
      };
    }
    case "commit-sync": {
      if (snapshot.state !== "OPEN_DIRTY") {
        return reject("commit requires a dirty session");
      }
      return {
        snapshot: { ...snapshot, state: "COMMITTING_SYNC" },
        outcome: "handled",
      };
    }
    case "commit-accepted": {
      if (snapshot.state !== "COMMITTING_SYNC") {
        return reject("no pending sync commit");
      }
      return {
        snapshot: { ...snapshot, state: "ACCEPTED" },
        outcome: "handled",
      };
    }
    case "commit-rejected": {
      if (snapshot.state !== "COMMITTING_SYNC") {
        return reject("no pending sync commit");
      }
      return {
        snapshot: { ...snapshot, state: "REJECTED_RETRYABLE", dirty: true },
        outcome: "handled",
      };
    }
    case "invalidate": {
      if (
        snapshot.state === "CLOSED" ||
        snapshot.state === "DISPOSING" ||
        snapshot.state === "INVALIDATED"
      ) {
        return reject("session already terminal");
      }
      return {
        snapshot: { ...snapshot, state: "INVALIDATED" },
        outcome: "handled",
      };
    }
    case "disposed": {
      if (snapshot.state === "CLOSED") {
        return reject("already closed");
      }
      return {
        snapshot: { ...CLOSED_SNAPSHOT },
        outcome: "handled",
      };
    }
    default:
      return reject("unknown event");
  }
}

// §10.7/§10.2: local-history budget and gesture coalescing helpers.
export interface LibTVLocalHistoryEntry {
  kind: string;
  at: number;
  value: string;
}

export interface LibTVLocalHistoryBudget {
  maxEntries: number;
  coalesceWindowMs: number;
}

export const DEFAULT_LIBTV_LOCAL_HISTORY_BUDGET: LibTVLocalHistoryBudget = {
  maxEntries: 50,
  coalesceWindowMs: 600,
};

export function pushLibTVLocalHistory(
  history: readonly LibTVLocalHistoryEntry[],
  entry: LibTVLocalHistoryEntry,
  budget: LibTVLocalHistoryBudget = DEFAULT_LIBTV_LOCAL_HISTORY_BUDGET,
): LibTVLocalHistoryEntry[] {
  const last = history.at(-1);
  const merged =
    last &&
    last.kind === entry.kind &&
    entry.at - last.at <= budget.coalesceWindowMs;
  const next = merged
    ? [...history.slice(0, -1), entry]
    : [...history, entry];
  return next.slice(-budget.maxEntries);
}

// Batch 447 (VR-022 Slice C): RECORD_EDITOR one-acceptance path — stable
// record fingerprints so an identical resubmit is a no-op, not a duplicate.
export function fingerprintLibTVEditorRecords(value: unknown): string {
  return JSON.stringify(value, (_key, entry) => {
    if (entry && typeof entry === "object" && !Array.isArray(entry)) {
      return Object.keys(entry as Record<string, unknown>)
        .sort()
        .reduce<Record<string, unknown>>((acc, key) => {
          acc[key] = (entry as Record<string, unknown>)[key];
          return acc;
        }, {});
    }
    return entry;
  });
}

export interface LibTVRecordEditorSubmitResult {
  status: "accepted" | "no-op" | "rejected";
  targetId: string | null;
}

// Batch 446 (VR-022 Slice B): equality-aware graph commit adapter planner —
// owner/generation/fingerprint validation with named outcomes; the caller
// applies graph mutation only on "accepted".

export interface LibTVEditorCommitRequest {
  profileId: LibTVEditorProfileId;
  nodeId: string;
  expectedCanvasId: string;
  expectedCanvasGeneration: number;
  field: string;
  baselineValue: string;
  draftValue: string;
}

export interface LibTVEditorCommitObservation {
  canvasId: string;
  canvasGeneration: number;
  nodeExists: boolean;
  currentFieldValue: string;
}

export type LibTVEditorCommitStatus =
  | "accepted"
  | "no-op"
  | "stale"
  | "invalid-owner"
  | "conflict";

export interface LibTVEditorCommitPlan {
  status: LibTVEditorCommitStatus;
  reason?: string;
  normalizedDraft: string;
  normalizedCurrent: string;
}

export interface LibTVEditorCommitResult {
  status: LibTVEditorCommitStatus;
  reason?: string;
  historyPushed: boolean;
  normalizedDraft: string;
  normalizedCurrent: string;
}

export function planLibTVEditorSessionCommit(
  request: LibTVEditorCommitRequest,
  observation: LibTVEditorCommitObservation,
): LibTVEditorCommitPlan {
  const profile = LIBTV_EDITOR_PROFILES[request.profileId];
  const normalizedDraft = normalizeLibTVEditorValue(
    profile,
    request.draftValue,
  );
  const normalizedCurrent = normalizeLibTVEditorValue(
    profile,
    observation.currentFieldValue,
  );
  if (!observation.nodeExists) {
    return {
      status: "invalid-owner",
      reason: "OWNER_MISSING",
      normalizedDraft,
      normalizedCurrent,
    };
  }
  if (observation.canvasId !== request.expectedCanvasId) {
    return {
      status: "stale",
      reason: "CANVAS_CHANGED",
      normalizedDraft,
      normalizedCurrent,
    };
  }
  if (observation.canvasGeneration !== request.expectedCanvasGeneration) {
    return {
      status: "stale",
      reason: "GENERATION_CHANGED",
      normalizedDraft,
      normalizedCurrent,
    };
  }
  const normalizedBaseline = normalizeLibTVEditorValue(
    profile,
    request.baselineValue,
  );
  if (normalizedDraft === normalizedCurrent) {
    return {
      status: "no-op",
      reason:
        normalizedDraft === normalizedBaseline
          ? "DRAFT_EQUALS_BASELINE"
          : "DRAFT_EQUALS_CURRENT",
      normalizedDraft,
      normalizedCurrent,
    };
  }
  if (normalizedCurrent !== normalizedBaseline) {
    return {
      status: "conflict",
      reason: "SCOPED_FIELD_DRIFTED",
      normalizedDraft,
      normalizedCurrent,
    };
  }
  return { status: "accepted", normalizedDraft, normalizedCurrent };
}
