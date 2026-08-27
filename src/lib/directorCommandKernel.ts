import type {
  DirectorProjectDocumentV1,
} from "@/lib/directorProjectDocument";

export type DirectorCommandDisposition =
  | "COMMITTED"
  | "NOOP"
  | "REJECTED"
  | "STALE"
  | "CONFLICT"
  | "UNKNOWN";

export type DirectorCommandReason =
  | "DIRECTOR_OWNER_STALE"
  | "DIRECTOR_PROJECT_MISSING"
  | "DIRECTOR_TARGET_MISSING"
  | "DIRECTOR_TARGET_LOCKED"
  | "DIRECTOR_INVALID_VALUE"
  | "DIRECTOR_REFERENCE_INVALID"
  | "DIRECTOR_COMMAND_NO_CHANGE"
  | "DIRECTOR_DELETE_BLOCKED"
  | "DIRECTOR_LAST_CAMERA_REQUIRED"
  | "DIRECTOR_RESOURCE_IN_USE"
  | "DIRECTOR_GESTURE_NOT_ACTIVE"
  | "DIRECTOR_HISTORY_EMPTY"
  | "DIRECTOR_HISTORY_CONFLICT"
  | "DIRECTOR_POLICY_UNKNOWN";

export interface DirectorSelectionResult {
  selectedObjectId: string | null;
  selectedObjectIds: string[];
  selectedGroupId: string | null;
}

export interface DirectorResourceEffect {
  kind: "none";
  resourceId: string | null;
}

export interface DirectorGraphEffect {
  kind: "none";
  nodeId: string | null;
}

export interface DirectorCommandResult {
  commandId: string;
  commandKind: string;
  projectId: string;
  generation: number;
  disposition: DirectorCommandDisposition;
  reason: DirectorCommandReason | null;
  projectChanged: boolean;
  historyEntries: 0 | 1;
  selectionResult: DirectorSelectionResult | null;
  resourceEffects: DirectorResourceEffect[];
  graphEffects: DirectorGraphEffect[];
}

export interface DirectorHistoryEntry {
  entryId: string;
  commandId: string;
  commandKind: string;
  projectId: string;
  generation: number;
  before: DirectorProjectDocumentV1;
  after: DirectorProjectDocumentV1;
  committedAt: string;
}

export interface DirectorGestureTransaction {
  gestureId: string;
  projectId: string;
  generation: number;
  commandKind: string;
  targetId: string | null;
  fieldScope: string | null;
  baselineFingerprint: string;
  baseline: DirectorProjectDocumentV1;
  startedAt: string;
}

export interface DirectorHistoryState {
  past: DirectorHistoryEntry[];
  future: DirectorHistoryEntry[];
  activeGesture: DirectorGestureTransaction | null;
  limit: number;
}

let commandSequence = 0;

function nextIdentity(prefix: string): string {
  commandSequence += 1;
  return `${prefix}-${Date.now()}-${commandSequence}`;
}

export function createDirectorHistoryState(
  limit = 50,
): DirectorHistoryState {
  return {
    past: [],
    future: [],
    activeGesture: null,
    limit: Math.max(1, Math.floor(limit)),
  };
}

export function cloneDirectorHistoryState(
  history: DirectorHistoryState,
): DirectorHistoryState {
  return {
    past: history.past.map((entry) => ({
      ...entry,
      before: entry.before,
      after: entry.after,
    })),
    future: history.future.map((entry) => ({
      ...entry,
      before: entry.before,
      after: entry.after,
    })),
    activeGesture: history.activeGesture
      ? { ...history.activeGesture, baseline: history.activeGesture.baseline }
      : null,
    limit: history.limit,
  };
}

export function directorDocumentFingerprint(
  document: DirectorProjectDocumentV1,
): string {
  return JSON.stringify(document);
}

export function createDirectorCommandResult(input: {
  commandKind: string;
  projectId: string | null;
  generation: number | null;
  disposition: DirectorCommandDisposition;
  reason?: DirectorCommandReason | null;
  projectChanged?: boolean;
  historyEntries?: 0 | 1;
  selectionResult?: DirectorSelectionResult | null;
}): DirectorCommandResult {
  return {
    commandId: nextIdentity("director-command"),
    commandKind: input.commandKind,
    projectId: input.projectId ?? "",
    generation: input.generation ?? 0,
    disposition: input.disposition,
    reason: input.reason ?? null,
    projectChanged: input.projectChanged ?? false,
    historyEntries: input.historyEntries ?? 0,
    selectionResult: input.selectionResult ?? null,
    resourceEffects: [],
    graphEffects: [],
  };
}

export function createDirectorGesture(
  input: Omit<DirectorGestureTransaction, "gestureId" | "startedAt"> & {
    startedAt?: string;
  },
): DirectorGestureTransaction {
  return {
    ...input,
    gestureId: nextIdentity("director-gesture"),
    startedAt: input.startedAt ?? new Date().toISOString(),
  };
}

export function createDirectorHistoryEntry(input: {
  commandId: string;
  commandKind: string;
  projectId: string;
  generation: number;
  before: DirectorProjectDocumentV1;
  after: DirectorProjectDocumentV1;
  committedAt?: string;
}): DirectorHistoryEntry {
  return {
    entryId: nextIdentity("director-history"),
    commandId: input.commandId,
    commandKind: input.commandKind,
    projectId: input.projectId,
    generation: input.generation,
    before: input.before,
    after: input.after,
    committedAt: input.committedAt ?? new Date().toISOString(),
  };
}

export function pushDirectorHistory(
  history: DirectorHistoryState,
  entry: DirectorHistoryEntry,
): DirectorHistoryState {
  return {
    ...history,
    past: [...history.past, entry].slice(-history.limit),
    future: [],
    activeGesture: null,
  };
}
