// Batch 441 (VR-023 Slice A): typed dimension-authority classification per
// LIBTV_MEDIA_RENDITION_GEOMETRY_CONTRACT §3 + GI-102 — intrinsic, request,
// node-frame, measured and export-frame are distinct authorities. Diagnostics
// only: nothing here mutates graph state or changes rendering.

export type LibTVDimensionAuthority =
  | "intrinsic"
  | "request"
  | "node-frame"
  | "measured"
  | "export-frame"
  | "unknown";

export type LibTVDimensionFieldKind =
  | "dimensions"
  | "display-string"
  | "scalar"
  | "unknown";

export interface LibTVDimensionFieldClassification {
  field: string;
  authority: LibTVDimensionAuthority;
  kind: LibTVDimensionFieldKind;
}

export interface LibTVDimensionConflict {
  nodeId: string;
  kind:
    | "intrinsic-display-string-only"
    | "request-display-string-only"
    | "derived-frame-generic-default";
  detail: string;
}

interface FieldRule {
  authority: LibTVDimensionAuthority;
  kind: LibTVDimensionFieldKind;
}

// Field-name classification for the current clone data model. `width`/
// `height` on image data are a DECLARED intrinsic claim (the preview trusts
// them without a decode check — static audit 2026-08-27); `resolution` and
// `generationSettings` are opaque display projections, never canonical
// geometry (contract §3.4).
const FIELD_TABLE: Record<string, FieldRule> = {
  width: { authority: "intrinsic", kind: "dimensions" },
  height: { authority: "intrinsic", kind: "dimensions" },
  resolution: { authority: "intrinsic", kind: "display-string" },
  generationSettings: { authority: "request", kind: "display-string" },
  aspectRatio: { authority: "request", kind: "display-string" },
  exportFrameWidth: { authority: "export-frame", kind: "dimensions" },
  exportFrameHeight: { authority: "export-frame", kind: "dimensions" },
  measuredWidth: { authority: "measured", kind: "dimensions" },
  measuredHeight: { authority: "measured", kind: "dimensions" },
  editorHeight: { authority: "unknown", kind: "scalar" },
};

export function classifyLibTVDimensionField(
  field: string,
): LibTVDimensionFieldClassification {
  const rule = FIELD_TABLE[field];
  if (!rule) {
    return { field, authority: "unknown", kind: "unknown" };
  }
  return { field, authority: rule.authority, kind: rule.kind };
}

export function parseLibTVDisplayDimensions(
  value: unknown,
): { width: number; height: number } | null {
  if (typeof value !== "string") return null;
  const match = value.match(/(\d+(?:\.\d+)?)\s*[×x*]\s*(\d+(?:\.\d+)?)/);
  if (!match) return null;
  const width = Number(match[1]);
  const height = Number(match[2]);
  if (!Number.isFinite(width) || !Number.isFinite(height)) return null;
  return { width, height };
}

interface DimensionBearingNode {
  id: string;
  type?: string;
  width?: number;
  height?: number;
  style?: { width?: number | string; height?: number | string };
  data?: Record<string, unknown>;
}

// The generic derived image/video frame (getDefaultNodeDimensions) — a
// derived node still carrying it while its source declares a different
// intrinsic ratio is the static audit's "hidden 16:9 reframing" finding,
// made observable here.
export const LIBTV_GENERIC_DERIVED_IMAGE_FRAME = { width: 512, height: 288 };

function isGenericDerivedFrame(width: number, height: number): boolean {
  return (
    Math.abs(width - LIBTV_GENERIC_DERIVED_IMAGE_FRAME.width) < 0.5 &&
    Math.abs(height - LIBTV_GENERIC_DERIVED_IMAGE_FRAME.height) < 0.5
  );
}

function intrinsicRatioOf(node: DimensionBearingNode): number | null {
  const data = node.data ?? {};
  const width = typeof data.width === "number" ? data.width : null;
  const height = typeof data.height === "number" ? data.height : null;
  if (width && height) return width / height;
  const parsed = parseLibTVDisplayDimensions(data.resolution);
  if (parsed) return parsed.width / parsed.height;
  return null;
}

export function detectLibTVDimensionAuthorityConflicts(
  node: DimensionBearingNode,
  source?: DimensionBearingNode,
): LibTVDimensionConflict[] {
  const conflicts: LibTVDimensionConflict[] = [];
  const data = node.data ?? {};

  if (
    node.type === "video" &&
    typeof data.resolution === "string" &&
    !(typeof data.width === "number" && typeof data.height === "number")
  ) {
    conflicts.push({
      nodeId: node.id,
      kind: "intrinsic-display-string-only",
      detail:
        "intrinsic authority is only a display projection (resolution string); no typed dimensions",
    });
  }

  if (
    node.type === "image" &&
    typeof data.generationSettings === "string" &&
    typeof data.aspectRatio !== "string"
  ) {
    conflicts.push({
      nodeId: node.id,
      kind: "request-display-string-only",
      detail:
        "request authority is only an opaque generationSettings display string (§3.4)",
    });
  }

  const frameWidth = node.width ?? Number(node.style?.width);
  const frameHeight = node.height ?? Number(node.style?.height);
  if (
    source &&
    typeof frameWidth === "number" &&
    typeof frameHeight === "number" &&
    isGenericDerivedFrame(frameWidth, frameHeight)
  ) {
    const sourceRatio = intrinsicRatioOf(source);
    if (sourceRatio) {
      const frameRatio = frameWidth / frameHeight;
      if (Math.abs(frameRatio - sourceRatio) / sourceRatio > 0.02) {
        conflicts.push({
          nodeId: node.id,
          kind: "derived-frame-generic-default",
          detail:
            "derived node still carries the generic 512×288 frame while its " +
            `source intrinsic ratio is ${sourceRatio.toFixed(3)}`,
        });
      }
    }
  }

  return conflicts;
}
