import type { DirectorProjectOwnerV1 } from "./directorProjectDocument.ts";
import {
  createDirectorProjectOwnerKey,
  type DirectorProjectRegistrySnapshot,
} from "./directorProjectRegistry.ts";

export interface DirectorOwnerReachabilityCanvas {
  id: string;
  nodes: readonly { id: string }[];
}

export interface DirectorOwnerReachabilityPlan {
  liveOwnerKeys: string[];
  preservedOwnerKeys: string[];
  tombstoneOwners: DirectorProjectOwnerV1[];
  tombstoneOwnerKeys: string[];
  alreadyTombstonedOwnerKeys: string[];
  activeOwnerKey: string | null;
  activeOwnerInvalidated: boolean;
  invalidLiveOwnerCount: number;
}

export interface PlanDirectorOwnerReachabilityInput {
  liveOwners: readonly DirectorProjectOwnerV1[];
  registry: DirectorProjectRegistrySnapshot;
}

function cloneOwner(owner: DirectorProjectOwnerV1): DirectorProjectOwnerV1 {
  return {
    route: "libtv",
    canvasId: owner.canvasId,
    sourceNodeId: owner.sourceNodeId,
  };
}

function isValidOwner(owner: DirectorProjectOwnerV1): boolean {
  return (
    owner.route === "libtv" &&
    owner.canvasId.length > 0 &&
    owner.canvasId.trim() === owner.canvasId &&
    owner.sourceNodeId.length > 0 &&
    owner.sourceNodeId.trim() === owner.sourceNodeId
  );
}

function normalizeLiveOwnerKeys(
  owners: readonly DirectorProjectOwnerV1[],
): {
  keys: string[];
  invalidCount: number;
} {
  const keys = new Set<string>();
  let invalidCount = 0;
  for (const owner of owners) {
    if (!isValidOwner(owner)) {
      invalidCount += 1;
      continue;
    }
    keys.add(createDirectorProjectOwnerKey(owner));
  }
  return {
    keys: [...keys].sort(),
    invalidCount,
  };
}

export function collectLiveDirectorProjectOwners(
  canvases: readonly DirectorOwnerReachabilityCanvas[],
): DirectorProjectOwnerV1[] {
  return canvases.flatMap((canvas) =>
    canvas.nodes.map((node) => ({
      route: "libtv" as const,
      canvasId: canvas.id,
      sourceNodeId: node.id,
    })),
  );
}

export function createDirectorOwnerReachabilitySignature(
  canvases: readonly DirectorOwnerReachabilityCanvas[],
): string {
  return normalizeLiveOwnerKeys(
    collectLiveDirectorProjectOwners(canvases),
  ).keys.join("\n");
}

export function planDirectorOwnerReachability(
  input: PlanDirectorOwnerReachabilityInput,
): DirectorOwnerReachabilityPlan {
  const normalizedLive = normalizeLiveOwnerKeys(input.liveOwners);
  const liveOwnerKeys = new Set(normalizedLive.keys);
  const preservedOwnerKeys: string[] = [];
  const tombstoneOwners: DirectorProjectOwnerV1[] = [];
  const alreadyTombstonedOwnerKeys: string[] = [];

  const records = [...input.registry.records].sort((left, right) =>
    createDirectorProjectOwnerKey(left.identity.owner).localeCompare(
      createDirectorProjectOwnerKey(right.identity.owner),
    ),
  );
  for (const record of records) {
    const ownerKey = createDirectorProjectOwnerKey(record.identity.owner);
    if (record.lifecycle === "TOMBSTONED") {
      alreadyTombstonedOwnerKeys.push(ownerKey);
    } else if (liveOwnerKeys.has(ownerKey)) {
      preservedOwnerKeys.push(ownerKey);
    } else {
      tombstoneOwners.push(cloneOwner(record.identity.owner));
    }
  }

  const tombstoneOwnerKeys = tombstoneOwners.map(
    createDirectorProjectOwnerKey,
  );
  const activeOwnerKey = input.registry.activeSession
    ? createDirectorProjectOwnerKey(input.registry.activeSession.owner)
    : null;

  return {
    liveOwnerKeys: normalizedLive.keys,
    preservedOwnerKeys,
    tombstoneOwners,
    tombstoneOwnerKeys,
    alreadyTombstonedOwnerKeys,
    activeOwnerKey,
    activeOwnerInvalidated:
      activeOwnerKey !== null && tombstoneOwnerKeys.includes(activeOwnerKey),
    invalidLiveOwnerCount: normalizedLive.invalidCount,
  };
}
