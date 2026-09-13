// Batch 449 (VR-022 Slice E): deterministic request handoff — a fake
// operation acceptor replacing raw component timer identity. Every delayed
// task carries a frozen descriptor {operationId, kind, canvasId, nodeId};
// at completion the acceptor re-validates ownership before running the
// task, so a deleted/moved owner yields a stable stale disposition instead
// of a misplaced commit (contract §5.7, §11 async submission descriptor).

export interface LibTVOperationDescriptor {
  operationId: string;
  kind: string;
  canvasId: string;
  nodeId: string;
  acceptedAt: number;
}

export interface LibTVOperationOutcome {
  operationId: string;
  status: "completed" | "cancelled" | "stale-owner";
}

export interface LibTVOperationHandle {
  descriptor: LibTVOperationDescriptor;
  cancel: () => void;
}

export interface LibTVOperationLogEntry {
  operationId: string;
  kind: string;
  canvasId: string;
  nodeId: string;
  status: LibTVOperationOutcome["status"];
}

export type LibTVOperationLog = LibTVOperationLogEntry[];

let operationCounter = 0;

export function acceptLibTVOperation(input: {
  kind: string;
  canvasId: string;
  nodeId: string;
  delayMs: number;
  isOwnerCurrent: () => boolean;
  task: () => void;
  onSettled?: (outcome: LibTVOperationOutcome) => void;
}): LibTVOperationHandle {
  operationCounter += 1;
  const descriptor: LibTVOperationDescriptor = {
    operationId: `op-${input.kind}-${operationCounter}`,
    kind: input.kind,
    canvasId: input.canvasId,
    nodeId: input.nodeId,
    acceptedAt: Date.now(),
  };
  let cancelled = false;
  const timer = setTimeout(() => {
    if (cancelled) return;
    const outcome: LibTVOperationOutcome = input.isOwnerCurrent()
      ? (() => {
          input.task();
          return {
            operationId: descriptor.operationId,
            status: "completed" as const,
          };
        })()
      : {
          operationId: descriptor.operationId,
          status: "stale-owner" as const,
        };
    input.onSettled?.(outcome);
  }, input.delayMs);
  return {
    descriptor,
    cancel: () => {
      if (cancelled) return;
      cancelled = true;
      clearTimeout(timer);
      input.onSettled?.({
        operationId: descriptor.operationId,
        status: "cancelled",
      });
    },
  };
}
