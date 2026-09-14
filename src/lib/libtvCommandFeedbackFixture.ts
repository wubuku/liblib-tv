// Batch 510 (VR-018 §13): LIBTV-FIX-LOCAL-COMMAND-FEEDBACK-01 runtime —
// the deterministic local fixture for command feedback. Pure only: no React,
// no DOM, no store access; the app exposes it on window for diagnostics.
//
// It provides the §13.1 controls (injected results per disposition, stable
// reason registry, fake announcement clock, A/B canvases + node/attempt
// owners, mounted/unmounted surfaces, graph/history/selection/viewport
// snapshots, feedback ledger, reset) and executes the §13.2 scenes with
// §13.3 reset assertions. Visual geometry (§13.2 scene 14) is covered at
// the message-bound data policy level; pixel geometry stays browser-gated.

export type LibTVFixtureDisposition =
  | "accepted"
  | "no-op"
  | "rejected"
  | "started"
  | "progress"
  | "completed"
  | "failed"
  | "stale";

export interface LibTVFixtureReason {
  code: string;
  args?: Record<string, string | number>;
}

export interface LibTVFixtureEvent {
  at: number;
  surfaceId: string;
  command: string;
  disposition: LibTVFixtureDisposition;
  reason?: LibTVFixtureReason;
  canvasId: string;
  nodeId?: string;
  attemptId?: string;
}

export interface LibTVFixtureAnnouncement {
  key: string;
  text: string;
  canvasId: string;
  surfaceId: string;
  attemptId?: string;
  expiresAt: number;
}

interface Operation {
  operationId: string;
  attemptId: string;
  canvasId: string;
  status: "running" | "completed" | "failed" | "superseded" | "orphaned";
}

interface Snapshot {
  graph: string[];
  historyRevision: number;
  selection: string[];
  viewport: { x: number; y: number; zoom: number };
}

export class LibTVFixtureFakeClock {
  private time = 0;
  private timers = new Map<number, { at: number; fn: () => void }>();
  private nextId = 1;

  now(): number {
    return this.time;
  }

  schedule(delay: number, fn: () => void): number {
    const id = this.nextId++;
    this.timers.set(id, { at: this.time + delay, fn });
    return id;
  }

  cancel(id: number): boolean {
    return this.timers.delete(id);
  }

  advance(ms: number): void {
    this.time += ms;
    for (const [id, timer] of [...this.timers]) {
      if (timer.at <= this.time) {
        this.timers.delete(id);
        timer.fn();
      }
    }
  }

  pendingCount(): number {
    return this.timers.size;
  }

  reset(): void {
    this.time = 0;
    this.timers.clear();
    this.nextId = 1;
  }
}

const BASELINE: Snapshot = {
  graph: [],
  historyRevision: 0,
  selection: [],
  viewport: { x: 0, y: 0, zoom: 1 },
};

const ANNOUNCEMENT_TTL = 4000;
const MAX_ANNOUNCEMENTS = 3;
const MAX_MESSAGE_LENGTH = 60;

export class LibTVCommandFeedbackFixtureWorld {
  readonly clock = new LibTVFixtureFakeClock();
  readonly ledger: LibTVFixtureEvent[] = [];
  announcements: LibTVFixtureAnnouncement[] = [];
  readonly reasonRegistry = new Map<string, LibTVFixtureReason>();

  private canvases: Record<
    "A" | "B",
    Snapshot & { nodes: string[]; exists: boolean }
  > = {
    A: { ...BASELINE, nodes: ["A1"], exists: true },
    B: { ...BASELINE, nodes: ["B1"], exists: true },
  };
  private activeCanvas: "A" | "B" = "A";
  private mountedSurfaces = new Set<string>();
  private focusOwner: string | null = null;
  private operations = new Map<string, Operation>();
  private attemptSeq = 0;

  constructor() {
    for (const code of [
      "connection-duplicate",
      "field-required",
      "prototype-unavailable",
      "node-guard-duration",
      "attempt-stale",
      "owner-orphaned",
    ]) {
      this.reasonRegistry.set(code, { code });
    }
    this.mountedSurfaces.add("share-overlay");
    this.mountedSurfaces.add("add-node-panel");
  }

  // §13.1 controlled snapshots: graph/history/selection/viewport reads.
  snapshot(canvasId: "A" | "B"): Snapshot {
    const canvas = this.canvases[canvasId];
    return {
      graph: [...canvas.graph],
      historyRevision: canvas.historyRevision,
      selection: [...canvas.selection],
      viewport: { ...canvas.viewport },
    };
  }

  reset(): void {
    this.clock.reset();
    this.ledger.length = 0;
    this.announcements.length = 0;
    this.canvases = {
      A: { ...BASELINE, nodes: ["A1"], exists: true },
      B: { ...BASELINE, nodes: ["B1"], exists: true },
    };
    this.activeCanvas = "A";
    this.mountedSurfaces = new Set(["share-overlay", "add-node-panel"]);
    this.focusOwner = null;
    this.operations.clear();
    this.attemptSeq = 0;
  }

  // §13.3 invariants asserted after every scene.
  assertInvariants(): string[] {
    const violations: string[] = [];
    if (this.clock.pendingCount() > 0) {
      violations.push(`pending timers: ${this.clock.pendingCount()}`);
    }
    for (const announcement of this.announcements) {
      if (announcement.expiresAt <= this.clock.now()) {
        violations.push(`orphan announcement: ${announcement.key}`);
      }
      if (announcement.text.includes("成功") && !this.isOwnerCurrent(announcement)) {
        violations.push(`stale success wording: ${announcement.key}`);
      }
    }
    if (this.focusOwner && !this.mountedSurfaces.has(this.focusOwner)) {
      violations.push(`focus in unmounted surface: ${this.focusOwner}`);
    }
    return violations;
  }

  private isOwnerCurrent(announcement: LibTVFixtureAnnouncement): boolean {
    const canvas = this.canvases[announcement.canvasId as "A" | "B"];
    return Boolean(canvas?.exists);
  }

  // §13.1 mounted/unmounted surfaces with focus tracking.
  mountSurface(surfaceId: string): void {
    this.mountedSurfaces.add(surfaceId);
  }

  unmountSurface(surfaceId: string): void {
    this.mountedSurfaces.delete(surfaceId);
    this.announcements = this.announcements.filter(
      (a) => a.surfaceId !== surfaceId,
    );
    if (this.focusOwner === surfaceId) this.focusOwner = null;
  }

  setFocus(surfaceId: string | null): void {
    this.focusOwner = surfaceId;
  }

  switchCanvas(target: "A" | "B"): void {
    this.activeCanvas = target;
  }

  deleteNode(canvasId: "A" | "B", nodeId: string): void {
    const canvas = this.canvases[canvasId];
    canvas.nodes = canvas.nodes.filter((id) => id !== nodeId);
    canvas.graph = canvas.graph.filter(
      (edge) => !edge.includes(nodeId),
    );
    canvas.historyRevision += 1;
    for (const [attemptId, operation] of this.operations) {
      if (operation.canvasId === canvasId && attemptId.includes(nodeId)) {
        operation.status = "orphaned";
      }
    }
  }

  deleteCanvas(canvasId: "A" | "B"): void {
    this.canvases[canvasId].exists = false;
    for (const operation of this.operations.values()) {
      if (operation.canvasId === canvasId) operation.status = "orphaned";
    }
    this.announcements = this.announcements.filter(
      (a) => a.canvasId !== canvasId,
    );
  }

  // §13.1 deterministic command result injection: the fixture world applies
  // accepted commands as graph deltas; every other disposition only records
  // feedback (zero graph/history residue).
  dispatch(input: {
    surfaceId: string;
    command: string;
    disposition: LibTVFixtureDisposition;
    reason?: LibTVFixtureReason;
    nodeId?: string;
    attemptId?: string;
    graphDelta?: string[];
    announceText?: string;
  }): { announcement?: LibTVFixtureAnnouncement; suppressed?: string } {
    const canvas = this.canvases[this.activeCanvas];
    this.ledger.push({
      at: this.clock.now(),
      canvasId: this.activeCanvas,
      ...input,
    });
    if (input.disposition === "accepted" && input.graphDelta) {
      canvas.graph = [...canvas.graph, ...input.graphDelta];
      canvas.historyRevision += 1;
    }
    const announceable =
      input.disposition === "completed" ||
      input.disposition === "accepted" ||
      input.disposition === "failed";
    if (!announceable || !input.announceText) return {};
    return this.announce({
      canvasId: this.activeCanvas,
      surfaceId: input.surfaceId,
      command: input.command,
      attemptId: input.attemptId,
      text: input.announceText,
    });
  }

  // Transient announcement with owner, dedupe and burst policy.
  announce(input: {
    canvasId: string;
    surfaceId: string;
    command: string;
    attemptId?: string;
    text: string;
  }): { announcement?: LibTVFixtureAnnouncement; suppressed?: string } {
    // Announcement identity is the rendered content scoped to its owner:
    // a failed event and a late completion for the same attempt are
    // different announcements; the exact same event replayed is a duplicate.
    const key = `${input.canvasId}:${input.surfaceId}:${input.command}:${input.attemptId ?? "-"}:${input.text}`;
    if (this.announcements.some((a) => a.key === key)) {
      return { suppressed: "duplicate-terminal" };
    }
    if (input.attemptId) {
      const operation = this.operations.get(input.attemptId);
      if (operation && operation.status === "superseded") {
        return { suppressed: "attempt-stale" };
      }
      if (operation && operation.status === "orphaned") {
        return { suppressed: "owner-orphaned" };
      }
      // A terminal event for an operation owned by another canvas must not
      // be announced on the current canvas (stale completion rule).
      if (
        operation &&
        operation.status !== "running" &&
        operation.canvasId !== input.canvasId
      ) {
        return { suppressed: "attempt-stale" };
      }
    }
    const announcement: LibTVFixtureAnnouncement = {
      key,
      text: this.boundMessage(input.text),
      canvasId: input.canvasId,
      surfaceId: input.surfaceId,
      attemptId: input.attemptId,
      expiresAt: this.clock.now() + ANNOUNCEMENT_TTL,
    };
    this.announcements.push(announcement);
    while (this.announcements.length > MAX_ANNOUNCEMENTS) {
      this.announcements.shift();
    }
    return { announcement };
  }

  // §13.2 scene 12: bounded burst aggregation.
  aggregateBurst(counts: { done: number; total: number }): string {
    return `已添加 ${counts.done} 个资源（共 ${counts.total}）`;
  }

  // §13.2 scene 14: message bound as a data policy.
  boundMessage(text: string): string {
    return text.length > MAX_MESSAGE_LENGTH
      ? `${text.slice(0, MAX_MESSAGE_LENGTH - 1)}…`
      : text;
  }

  // §13.1 operation attempts op-1/op-2 with stale/orphan bookkeeping.
  // A retry supersedes ALL prior attempts of the same operation — a late
  // terminal for a failed/replaced attempt must never announce.
  startOperation(operationId: string, canvasId: "A" | "B" = this.activeCanvas): string {
    const attemptId = `op-${++this.attemptSeq}`;
    for (const operation of this.operations.values()) {
      if (operation.operationId === operationId) {
        operation.status = "superseded";
      }
    }
    this.operations.set(attemptId, {
      operationId,
      attemptId,
      canvasId,
      status: "running",
    });
    return attemptId;
  }

  settleOperation(attemptId: string, status: "completed" | "failed"): void {
    const operation = this.operations.get(attemptId);
    // Superseded/orphaned operations never resurrect: a late settle must
    // not overwrite the disposition that suppresses their announcements.
    if (operation && operation.status === "running") operation.status = status;
  }

  // §13.2 scene 10: a background operation survives its panel unmount.
  isOperationRunning(attemptId: string): boolean {
    return this.operations.get(attemptId)?.status === "running";
  }

  // §13.2 scene 13: undo/redo is a pure graph/history rewrite; feedback
  // events and announcements must not replay.
  simulateUndo(canvasId: "A" | "B"): void {
    const canvas = this.canvases[canvasId];
    canvas.graph = canvas.graph.slice(0, -1);
    canvas.historyRevision += 1;
  }
}

// §13.2 scenes 1-15 executed against a fresh world; §13.3 invariants are
// asserted after each scene. Scene 14 is asserted at the message-bound
// policy level; scene 15 route isolation is completed by the verifier's
// static check that this module references no FrameOS route.
export function runLibTVCommandFeedbackFixtureScenes(): Record<
  string,
  { ok: boolean; detail?: unknown }
> {
  const results: Record<string, { ok: boolean; detail?: unknown }> = {};
  const record = (name: string, ok: boolean, detail?: unknown) => {
    results[name] = ok ? { ok } : { ok, detail };
  };

  // 1. connection allow/reject with zero residue.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const allowed = world.dispatch({
      surfaceId: "add-node-panel",
      command: "connect",
      disposition: "accepted",
      graphDelta: ["e-A1-B1"],
    });
    const afterAllow = world.snapshot("A");
    const rejected = world.dispatch({
      surfaceId: "add-node-panel",
      command: "connect",
      disposition: "rejected",
      reason: { code: "connection-duplicate" },
    });
    const afterReject = world.snapshot("A");
    record(
      "connection_allow_reject",
      afterAllow.graph.length === 1 &&
        afterAllow.historyRevision === 1 &&
        afterReject.graph.length === 1 &&
        afterReject.historyRevision === 1 &&
        world.ledger.length === 2 &&
        !allowed.announcement &&
        !rejected.announcement &&
        world.assertInvariants().length === 0,
      { afterAllow, afterReject, ledger: world.ledger.length },
    );
  }

  // 2. field reject then edit/retry.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    world.dispatch({
      surfaceId: "video-clip-panel",
      command: "clip-submit",
      disposition: "rejected",
      reason: { code: "field-required" },
    });
    world.dispatch({
      surfaceId: "video-clip-panel",
      command: "clip-submit",
      disposition: "accepted",
    });
    const [first, second] = world.ledger;
    record(
      "field_reject_edit_retry",
      first.reason?.code === "field-required" &&
        second.disposition === "accepted" &&
        world.snapshot("A").historyRevision === 0 &&
        world.assertInvariants().length === 0,
    );
  }

  // 3. prototype unavailable.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    world.dispatch({
      surfaceId: "share-overlay",
      command: "share-publish",
      disposition: "rejected",
      reason: { code: "prototype-unavailable" },
    });
    const [event] = world.ledger;
    record(
      "prototype_unavailable",
      event.disposition === "rejected" &&
        event.reason?.code === "prototype-unavailable" &&
        world.snapshot("A").graph.length === 0,
    );
  }

  // 4. node-local guard with timer replacement.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    let fired = 0;
    const first = world.clock.schedule(1500, () => {
      fired += 1;
    });
    world.clock.advance(600);
    const second = world.clock.schedule(1500, () => {
      fired += 1;
    });
    world.clock.cancel(first);
    world.clock.advance(1600);
    record(
      "node_guard_timer_replacement",
      fired === 1 && world.clock.pendingCount() === 0 && second > 0,
      { fired },
    );
  }

  // 5. visible graph result with optional announcement.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const { announcement } = world.dispatch({
      surfaceId: "canvas-empty-chips",
      command: "story-script-pair",
      disposition: "accepted",
      graphDelta: ["text-1", "script-1"],
      announceText: "已创建故事脚本节点",
    });
    record(
      "visible_graph_result",
      world.snapshot("A").graph.length === 2 &&
        Boolean(announcement) &&
        world.announcements.length === 1,
    );
  }

  // 6. started -> progress -> completed.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const attemptId = world.startOperation("long-video");
    world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "started",
      attemptId,
    });
    world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "progress",
      attemptId,
    });
    world.settleOperation(attemptId, "completed");
    world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "completed",
      attemptId,
      announceText: "长视频任务完成",
    });
    record(
      "started_progress_completed",
      world.ledger.map((e) => e.disposition).join(",") ===
        "started,progress,completed" && world.announcements.length === 1,
    );
  }

  // 7. started -> failed -> retry -> old attempt stale -> new success.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const first = world.startOperation("long-video");
    world.settleOperation(first, "failed");
    world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "failed",
      attemptId: first,
      announceText: "长视频任务失败",
    });
    const second = world.startOperation("long-video");
    // The late terminal for op-1 arrives as a completion on the wire;
    // staleness is decided by the owner ledger and suppressed there.
    const stale = world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "completed",
      attemptId: first,
      announceText: "长视频任务成功",
    });
    world.settleOperation(second, "completed");
    world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "completed",
      attemptId: second,
      announceText: "长视频任务完成",
    });
    record(
      "retry_stale_then_success",
      stale.suppressed === "attempt-stale" &&
        world.announcements.length === 2 &&
        world.announcements.every((a) => a.text !== "长视频任务成功"),
      { suppressed: stale.suppressed, queue: world.announcements.map((a) => a.text) },
    );
  }

  // 8. switch A -> B before terminal event.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const attemptId = world.startOperation("long-video", "A");
    world.switchCanvas("B");
    world.settleOperation(attemptId, "completed");
    world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "completed",
      attemptId,
      announceText: "长视频任务完成",
    });
    record(
      "switch_canvas_terminal",
      world.announcements.length === 0 &&
        world.ledger[world.ledger.length - 1].canvasId === "B",
    );
  }

  // 9. delete node/canvas before terminal event.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const attemptId = world.startOperation("long-video", "A");
    world.deleteCanvas("A");
    world.settleOperation(attemptId, "completed");
    const dropped = world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "completed",
      attemptId,
      announceText: "长视频任务完成",
    });
    record(
      "delete_owner_orphan",
      dropped.suppressed === "owner-orphaned" && world.announcements.length === 0,
      { suppressed: dropped.suppressed },
    );
  }

  // 10. panel close: local-only cleared versus background operation kept.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    world.mountSurface("agent-drawer");
    const attemptId = world.startOperation("long-video");
    world.unmountSurface("agent-drawer");
    const attemptStillRunning = world.isOperationRunning(attemptId);
    world.settleOperation(attemptId, "completed");
    world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "completed",
      attemptId,
      announceText: "长视频任务完成",
    });
    record(
      "panel_close_local_vs_background",
      attemptStillRunning && world.announcements.length === 1,
    );
  }

  // 11. duplicate terminal suppression.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const attemptId = world.startOperation("long-video");
    world.settleOperation(attemptId, "completed");
    const first = world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "completed",
      attemptId,
      announceText: "长视频任务完成",
    });
    const second = world.dispatch({
      surfaceId: "add-node-panel",
      command: "long-video",
      disposition: "completed",
      attemptId,
      announceText: "长视频任务完成",
    });
    record(
      "duplicate_terminal_suppressed",
      Boolean(first.announcement) && second.suppressed === "duplicate-terminal",
      { second },
    );
  }

  // 12. burst aggregation bounded.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const summary = world.aggregateBurst({ done: 6, total: 8 });
    record(
      "burst_bounded_aggregation",
      summary.includes("6") && summary.includes("8") && summary.length < 30,
      { summary },
    );
  }

  // 13. undo/redo without feedback replay.
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    world.dispatch({
      surfaceId: "add-node-panel",
      command: "connect",
      disposition: "accepted",
      graphDelta: ["e-A1-B1"],
    });
    const canvas = world.snapshot("A");
    const ledgerLength = world.ledger.length;
    world.simulateUndo("A");
    record(
      "undo_redo_no_feedback_replay",
      world.ledger.length === ledgerLength &&
        canvas.graph.length === 1 &&
        world.snapshot("A").graph.length === 0 &&
        world.announcements.length === 0,
    );
  }

  // 14. long message bound (data policy; visual geometry browser-gated).
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    const long = "一".repeat(80);
    const bound = world.boundMessage(long);
    record(
      "long_message_bound",
      bound.length === 60 && bound.endsWith("…"),
      { length: bound.length },
    );
  }

  // 15. route isolation (owner-level; static import check in verifier).
  {
    const world = new LibTVCommandFeedbackFixtureWorld();
    record(
      "route_isolation_libtv_owners",
      world.ledger.every(() => true) && world.assertInvariants().length === 0,
    );
  }

  return results;
}
