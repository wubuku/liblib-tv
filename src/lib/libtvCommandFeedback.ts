// Batch 467 (VR-018 Slice A): command outcome → feedback projection per
// LIBTV_COMMAND_OUTCOME_FEEDBACK_CONTRACT — inventory of the ordinary LibTV
// command surfaces and the stable disposition mapping. Pure only: no UI
// rendering, no store access; presentation stays with the owning surfaces.

export type LibTVCommandDisposition =
  | "success"
  | "error"
  | "pending"
  | "inert";

export interface LibTVCommandSurface {
  surfaceId: string;
  component: string;
  feedbackKind: "status-line" | "toast" | "node-state" | "none";
  commands: readonly string[];
  profile: string;
}

// Batch 467 inventory: every ordinary LibTV command surface that presents
// command outcomes, with its feedback channel. Director/Agent surfaces are
// separate islands (async contract owns them).
export const LIBTV_COMMAND_FEEDBACK_CATALOG: readonly LibTVCommandSurface[] = [
  {
    surfaceId: "add-node-panel",
    component: "AddNodePanel",
    feedbackKind: "status-line",
    commands: ["create-node", "material-open", "script-open"],
    profile: "INLINE_SCALAR",
  },
  {
    surfaceId: "add-resource-upload",
    component: "AddNodePanel",
    feedbackKind: "status-line",
    commands: ["add-resource-cohort"],
    profile: "ADD_RESOURCE_MULTI",
  },
  {
    surfaceId: "video-clip-panel",
    component: "VideoClipEditPanel",
    feedbackKind: "status-line",
    commands: ["clip-submit"],
    profile: "REQUEST_DRAFT",
  },
  {
    surfaceId: "subtitle-erase-panel",
    component: "SubtitleErasePanel",
    feedbackKind: "node-state",
    commands: ["subtitle-erase-submit"],
    profile: "RECORD_EDITOR",
  },
  {
    surfaceId: "smart-matting-panel",
    component: "VideoNode",
    feedbackKind: "node-state",
    commands: ["smart-matting-submit"],
    profile: "RECORD_EDITOR",
  },
  {
    surfaceId: "shot-breakdown-card",
    component: "ShotBreakdownNode",
    feedbackKind: "node-state",
    commands: ["shot-breakdown-run"],
    profile: "RECORD_EDITOR",
  },
  {
    surfaceId: "editor-session-commit",
    component: "canvasStore.submitLibTVEditorSessionCommit",
    feedbackKind: "none",
    commands: ["editor-session-commit"],
    profile: "INLINE_SCALAR",
  },
  {
    surfaceId: "asset-reference-attach",
    component: "canvasStore.attachAssetReferences",
    feedbackKind: "none",
    commands: ["asset-reference-attach"],
    profile: "GENERATED_HISTORY_ATTACH",
  },
  {
    surfaceId: "annotate-toolbar",
    component: "ImageAnnotateToolbar",
    feedbackKind: "none",
    commands: ["annotate-save (evidence-gated disabled)"],
    profile: "BITMAP_EDITOR",
  },
  // Batch 501 (VR-018 Slice B remaining): the Share overlay and the Agent
  // drawer's local status line join the inventory. Agent async run/progress
  // stays under the async-contract island; only the local status line is
  // catalogued here.
  {
    surfaceId: "share-overlay",
    component: "TopNavBar.SharePanel",
    feedbackKind: "status-line",
    commands: ["share-publish", "share-link"],
    profile: "INLINE_SCALAR",
  },
  {
    surfaceId: "agent-drawer-status",
    component: "AgentDrawer",
    feedbackKind: "status-line",
    commands: ["agent-submit", "attachment-open", "skill-open"],
    profile: "REQUEST_DRAFT",
  },
];

// §9.2: a no-op must never be presented as success — inert is its own
// disposition. Error-class outcomes surface diagnostics, not success copy.
export type LibTVCommandOutcomeStatus =
  | "accepted"
  | "no-op"
  | "rejected"
  | "stale"
  | "invalid-target"
  | "conflict";

export interface LibTVCommandFeedbackProjection {
  disposition: LibTVCommandDisposition;
  announce: boolean;
}

export function projectLibTVCommandFeedback(
  status: LibTVCommandOutcomeStatus,
): LibTVCommandFeedbackProjection {
  switch (status) {
    case "accepted":
      return { disposition: "success", announce: true };
    case "no-op":
      return { disposition: "inert", announce: false };
    case "rejected":
    case "invalid-target":
      return { disposition: "error", announce: true };
    case "stale":
    case "conflict":
      return { disposition: "error", announce: true };
    default:
      return { disposition: "pending", announce: false };
  }
}

// Batch 468 (VR-018 Slice B): explicit disposition formatting for status
// lines — the copy stays with the owning surface; the tone is the stable
// projection of the outcome.
export type LibTVCommandStatusTone =
  | "neutral"
  | "positive"
  | "diagnostic";

export function formatLibTVCommandStatus(
  projection: LibTVCommandFeedbackProjection,
  copy: string,
): { text: string; tone: LibTVCommandStatusTone } {
  switch (projection.disposition) {
    case "success":
      return { text: copy, tone: "positive" };
    case "error":
      return { text: copy, tone: "diagnostic" };
    default:
      return { text: copy, tone: "neutral" };
  }
}
