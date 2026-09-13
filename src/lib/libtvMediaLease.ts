// Batch 451 (VR-021 Slice B): instance-scoped lease ledger and a fake
// materializer per LIBTV_MEDIA_INGRESS_RESOURCE_LIFECYCLE_CONTRACT §6.4,
// §9 and Slice B ("observable probe/preview/session leases; deterministic
// delay/fail/stale/duplicate outcomes; no provider/storage/network").
// Pure/instance-scoped only — no React, store, timer or network usage.

export type LibTVMediaLeaseClass =
  | "LOCAL_BYTES"
  | "METADATA_PROBE_URL"
  | "PREVIEW_URL"
  | "SESSION_RESULT_URL"
  | "STABLE_ASSET_REFERENCE";

export type LibTVMediaLeaseOwnerKind =
  | "INGRESS_OPERATION"
  | "PREVIEW_SURFACE"
  | "GRAPH_REFERENCE_REGISTRY"
  | "DIRECTOR_WORKSPACE"
  | "ASSET_REGISTRY";

export interface LibTVMediaLease {
  leaseId: string;
  resourceId: string;
  resourceClass: LibTVMediaLeaseClass;
  ownerKind: LibTVMediaLeaseOwnerKind;
  ownerId: string;
  acquiredAt: number;
  transferredAt: number | null;
  releasedAt: number | null;
  releaseCount: number;
}

export type LibTVMediaLeaseReleaseStatus =
  | "released"
  | "already-released"
  | "unknown";

export class LibTVMediaLeaseLedger {
  private leases = new Map<string, LibTVMediaLease>();
  private counter = 0;

  acquire(input: {
    resourceId: string;
    resourceClass: LibTVMediaLeaseClass;
    ownerKind: LibTVMediaLeaseOwnerKind;
    ownerId: string;
    at?: number;
  }): LibTVMediaLease {
    this.counter += 1;
    const lease: LibTVMediaLease = {
      leaseId: `lease-${this.counter}`,
      resourceId: input.resourceId,
      resourceClass: input.resourceClass,
      ownerKind: input.ownerKind,
      ownerId: input.ownerId,
      acquiredAt: input.at ?? 0,
      transferredAt: null,
      releasedAt: null,
      releaseCount: 0,
    };
    this.leases.set(lease.leaseId, lease);
    return lease;
  }

  /** Exactly-once semantics: releasedAt is set on the first release only;
   * repeat calls bump releaseCount but never resurrect or re-stamp. */
  release(leaseId: string, at = 0): LibTVMediaLeaseReleaseStatus {
    const lease = this.leases.get(leaseId);
    if (!lease) return "unknown";
    lease.releaseCount += 1;
    if (lease.releasedAt !== null) return "already-released";
    lease.releasedAt = at;
    return "released";
  }

  transfer(
    leaseId: string,
    to: { ownerKind: LibTVMediaLeaseOwnerKind; ownerId: string },
    at = 0,
  ): boolean {
    const lease = this.leases.get(leaseId);
    if (!lease || lease.releasedAt !== null || lease.transferredAt !== null) {
      return false;
    }
    lease.transferredAt = at;
    lease.ownerKind = to.ownerKind;
    lease.ownerId = to.ownerId;
    return true;
  }

  get(leaseId: string): LibTVMediaLease | null {
    return this.leases.get(leaseId) ?? null;
  }

  list(): readonly LibTVMediaLease[] {
    return Array.from(this.leases.values());
  }
}

export interface LibTVFakeLocator {
  locatorClass: "SESSION_RESULT_URL";
  renderUrl: string;
  contentFingerprint: string;
}

export type LibTVFakeMaterializeOutcome =
  | { status: "materialized"; locator: LibTVFakeLocator; leaseId: string }
  | { status: "duplicate"; locator: LibTVFakeLocator }
  | { status: "failed"; reason: "MEDIA_MATERIALIZATION_FAILED" }
  | { status: "superseded"; reason: "MEDIA_ATTEMPT_SUPERSEDED" };

export interface LibTVFakeMaterializerPlan {
  outcome: "ok" | "fail" | "stale";
  isOwnerCurrent?: () => boolean;
}

// Deterministic fake materializer: settle() is invoked manually by the
// caller (fixture/tests) — no timers, no provider, no storage. Duplicate
// content fingerprints resolve to the first locator instead of a second
// materialization.
export class LibTVFakeMaterializer {
  private byFingerprint = new Map<string, LibTVFakeLocator>();
  private counter = 0;

  constructor(private ledger: LibTVMediaLeaseLedger) {}

  materialize(input: {
    canvasId: string;
    nodeId: string;
    contentFingerprint: string;
  }): (plan: LibTVFakeMaterializerPlan) => LibTVFakeMaterializeOutcome {
    const existing = this.byFingerprint.get(input.contentFingerprint);
    if (existing) {
      return () => ({ status: "duplicate", locator: existing });
    }
    return (plan: LibTVFakeMaterializerPlan) => {
      if (plan.outcome === "stale") {
        return { status: "superseded", reason: "MEDIA_ATTEMPT_SUPERSEDED" };
      }
      if (plan.outcome === "fail") {
        return {
          status: "failed",
          reason: "MEDIA_MATERIALIZATION_FAILED",
        };
      }
      if (plan.isOwnerCurrent && !plan.isOwnerCurrent()) {
        return { status: "superseded", reason: "MEDIA_ATTEMPT_SUPERSEDED" };
      }
      this.counter += 1;
      const locator: LibTVFakeLocator = {
        locatorClass: "SESSION_RESULT_URL",
        renderUrl: `blob:fixture-${this.counter}`,
        contentFingerprint: input.contentFingerprint,
      };
      this.byFingerprint.set(input.contentFingerprint, locator);
      const lease = this.ledger.acquire({
        resourceId: input.contentFingerprint,
        resourceClass: "SESSION_RESULT_URL",
        ownerKind: "INGRESS_OPERATION",
        ownerId: `${input.canvasId}/${input.nodeId}`,
      });
      return { status: "materialized", locator, leaseId: lease.leaseId };
    };
  }
}
