// Batch 450 (VR-021 Slice A): pure media-ingress descriptors, entry-profile
// registry, family classifier and ordered validation with the contract's
// stable reason family (§5, §8). Pure only — no UI/store integration; the
// lease ledger and materializer are Slice B.

export type LibTVMediaIngressEntryProfile =
  | "ADD_RESOURCE_MULTI"
  | "CANVAS_DROP_MULTI"
  | "NODE_MEDIA_REPLACE"
  | "SHOT_SOURCE_UPLOAD"
  | "GENERATED_HISTORY_ATTACH"
  | "REGISTERED_ASSET_ATTACH"
  | "CANVAS_MEDIA_REFERENCE"
  | "LOCAL_EDIT_EXPORT"
  | "DIRECTOR_BROWSER_EXPORT"
  | "DIRECTOR_LOCAL_MODEL_IMPORT";

export interface LibTVMediaIngressProfile {
  profileId: LibTVMediaIngressEntryProfile;
  cardinalityMin: number;
  /** null = unbounded */
  cardinalityMax: number | null;
  target: string;
  projectionPolicy: string;
}

export const LIBTV_MEDIA_INGRESS_PROFILES: Record<
  LibTVMediaIngressEntryProfile,
  LibTVMediaIngressProfile
> = {
  ADD_RESOURCE_MULTI: {
    profileId: "ADD_RESOURCE_MULTI",
    cardinalityMin: 1,
    cardinalityMax: null,
    target: "new-nodes",
    projectionPolicy: "runtime-placeholders-atomic-cohort",
  },
  CANVAS_DROP_MULTI: {
    profileId: "CANVAS_DROP_MULTI",
    cardinalityMin: 1,
    cardinalityMax: null,
    target: "new-nodes-at-flow-points",
    projectionPolicy: "runtime-placeholders-atomic-cohort",
  },
  NODE_MEDIA_REPLACE: {
    profileId: "NODE_MEDIA_REPLACE",
    cardinalityMin: 1,
    cardinalityMax: 1,
    target: "existing-node",
    projectionPolicy: "last-known-good-replace",
  },
  SHOT_SOURCE_UPLOAD: {
    profileId: "SHOT_SOURCE_UPLOAD",
    cardinalityMin: 1,
    cardinalityMax: 1,
    target: "process-source",
    projectionPolicy: "local-preview-until-session-owner",
  },
  GENERATED_HISTORY_ATTACH: {
    profileId: "GENERATED_HISTORY_ATTACH",
    cardinalityMin: 1,
    cardinalityMax: 10,
    target: "new-nodes-or-declared-target",
    projectionPolicy: "immediate-atomic-stable-reference",
  },
  REGISTERED_ASSET_ATTACH: {
    profileId: "REGISTERED_ASSET_ATTACH",
    cardinalityMin: 1,
    cardinalityMax: null,
    target: "new-nodes-or-declared-target",
    projectionPolicy: "immediate-atomic-alias-reference",
  },
  CANVAS_MEDIA_REFERENCE: {
    profileId: "CANVAS_MEDIA_REFERENCE",
    cardinalityMin: 1,
    cardinalityMax: 1,
    target: "process-input-node",
    projectionPolicy: "graph-reference-no-byte-transfer",
  },
  LOCAL_EDIT_EXPORT: {
    profileId: "LOCAL_EDIT_EXPORT",
    cardinalityMin: 1,
    cardinalityMax: 1,
    target: "existing-or-result-node",
    projectionPolicy: "async-materialize-one-semantic-commit",
  },
  DIRECTOR_BROWSER_EXPORT: {
    profileId: "DIRECTOR_BROWSER_EXPORT",
    cardinalityMin: 1,
    cardinalityMax: null,
    target: "ordinary-result-nodes",
    projectionPolicy: "generic-async-convergence",
  },
  DIRECTOR_LOCAL_MODEL_IMPORT: {
    profileId: "DIRECTOR_LOCAL_MODEL_IMPORT",
    cardinalityMin: 1,
    cardinalityMax: null,
    target: "director-library",
    projectionPolicy: "separate-subsystem-byte-budget",
  },
};

export interface LibTVLocalFileDescriptor {
  kind: "LOCAL_FILE";
  name: string;
  declaredMimeType: string;
  sizeBytes: number;
  lastModified: number;
}

export type LibTVMediaFamily =
  | "image"
  | "video"
  | "audio"
  | "text"
  | "director-model"
  | "data-url"
  | "blob-url"
  | "unknown";

// §8.3 stable reasons (client-pure subset, in validation order).
export type LibTVMediaIngressReason =
  | "MEDIA_ENTRY_PROFILE_INVALID"
  | "MEDIA_CARDINALITY_EXCEEDED"
  | "MEDIA_EMPTY"
  | "MEDIA_TARGET_MISSING"
  | "MEDIA_CANVAS_STALE"
  | "MEDIA_SOURCE_DESCRIPTOR_INVALID"
  | "MEDIA_TYPE_AMBIGUOUS"
  | "MEDIA_TYPE_UNSUPPORTED"
  | "MEDIA_SIZE_EXCEEDED";

// Clone-only fixture budgets, explicitly NOT source limits (§8.2).
const FAMILY_BUDGET_BYTES: Partial<Record<LibTVMediaFamily, number>> = {
  image: 20 * 1024 * 1024,
  video: 200 * 1024 * 1024,
  audio: 50 * 1024 * 1024,
  text: 2 * 1024 * 1024,
};

export function classifyLibTVMediaFamily(
  descriptor: LibTVLocalFileDescriptor,
): LibTVMediaFamily {
  if (descriptor.kind !== "LOCAL_FILE") return "unknown";
  const mime = descriptor.declaredMimeType.toLowerCase();
  const name = descriptor.name.toLowerCase();
  const ext = name.includes(".") ? name.slice(name.lastIndexOf(".") + 1) : "";
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("video/")) return "video";
  if (mime.startsWith("audio/")) return "audio";
  if (mime === "application/json" || mime.startsWith("text/")) return "text";
  if (mime === "application/octet-stream" || mime === "") {
    if (["blend", "glb", "fbx", "obj"].includes(ext)) return "director-model";
    if (["png", "jpg", "jpeg", "webp", "gif"].includes(ext)) return "image";
    if (["mp4", "mov", "webm"].includes(ext)) return "video";
    if (["mp3", "wav", "m4a"].includes(ext)) return "audio";
    if (["md", "txt", "json"].includes(ext)) return "text";
    return "unknown";
  }
  return "unknown";
}

export interface LibTVMediaIngressIntentInput {
  profileId: string;
  descriptors: readonly LibTVLocalFileDescriptor[];
  canvasExists: boolean;
  canvasGeneration: number;
  expectedCanvasGeneration: number;
}

export interface LibTVMediaIngressValidationResult {
  status: "accepted" | "rejected";
  reasons: LibTVMediaIngressReason[];
  family: LibTVMediaFamily | null;
}

// §8.1 ordered client validation (steps 1-6; probe/materializer steps 7-11
// belong to Slice B). All applicable reasons are reported in order.
export function validateLibTVMediaIngressIntent(
  input: LibTVMediaIngressIntentInput,
): LibTVMediaIngressValidationResult {
  const reasons: LibTVMediaIngressReason[] = [];
  const profile =
    LIBTV_MEDIA_INGRESS_PROFILES[
      input.profileId as LibTVMediaIngressEntryProfile
    ];
  if (!profile) {
    return {
      status: "rejected",
      reasons: ["MEDIA_ENTRY_PROFILE_INVALID"],
      family: null,
    };
  }

  if (input.descriptors.length < profile.cardinalityMin) {
    reasons.push("MEDIA_EMPTY");
  } else if (
    profile.cardinalityMax !== null &&
    input.descriptors.length > profile.cardinalityMax
  ) {
    reasons.push("MEDIA_CARDINALITY_EXCEEDED");
  }

  if (!input.canvasExists) {
    reasons.push("MEDIA_TARGET_MISSING");
  } else if (input.canvasGeneration !== input.expectedCanvasGeneration) {
    reasons.push("MEDIA_CANVAS_STALE");
  }

  for (const descriptor of input.descriptors) {
    if (
      typeof descriptor.name !== "string" ||
      descriptor.name.length === 0 ||
      !Number.isFinite(descriptor.sizeBytes) ||
      descriptor.sizeBytes < 0 ||
      typeof descriptor.declaredMimeType !== "string"
    ) {
      reasons.push("MEDIA_SOURCE_DESCRIPTOR_INVALID");
      continue;
    }
    if (descriptor.sizeBytes === 0) {
      reasons.push("MEDIA_EMPTY");
      continue;
    }
    const family = classifyLibTVMediaFamily(descriptor);
    if (family === "unknown") {
      reasons.push("MEDIA_TYPE_AMBIGUOUS");
      continue;
    }
    const budget = FAMILY_BUDGET_BYTES[family];
    if (budget === undefined) {
      reasons.push("MEDIA_TYPE_UNSUPPORTED");
      continue;
    }
    if (descriptor.sizeBytes > budget) {
      reasons.push("MEDIA_SIZE_EXCEEDED");
    }
  }

  const unique = Array.from(new Set(reasons));
  return {
    status: unique.length === 0 ? "accepted" : "rejected",
    reasons: unique,
    family:
      input.descriptors.length > 0
        ? classifyLibTVMediaFamily(input.descriptors[0])
        : null,
  };
}
