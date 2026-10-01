"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  AlertTriangle,
  Check,
  Download,
  ImageIcon,
  Info,
  PanelLeftOpen,
  Upload,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DirectorExportPanel,
  type DirectorExportStatus,
} from "@/components/director/DirectorExportPanel";
import { DirectorInspector } from "@/components/director/DirectorInspector";
import { DirectorObjectTree } from "@/components/director/DirectorObjectTree";
import { DirectorTimeline } from "@/components/director/DirectorTimeline";
import {
  getDirectorFocusableElements,
  useDirectorFocusContainment,
} from "@/components/director/useDirectorFocusContainment";
import { DirectorViewport } from "@/components/director/DirectorViewport";
import { DirectorScenePromptBar } from "@/components/director/DirectorScenePromptBar";
import { DirectorIconRail } from "@/components/director/DirectorIconRail";
import {
  collectDirectorCanvasMediaInputs,
  type DirectorCanvasMediaInputV1,
  type DirectorPanoramaRuntimeState,
} from "@/lib/directorCanvasMediaIngress";
import type {
  DirectorVideoExportRequest,
  DirectorVideoExportResult,
} from "@/components/director/directorVideoExport";
import {
  createDirectorAsyncIdentity,
  directorAsyncAuthority,
  type DirectorAsyncIngressContextV1,
  type DirectorAsyncOwnerSnapshotV1,
  type DirectorAsyncResultEnvelopeV1,
} from "@/lib/directorAsyncAuthority";
import { directorDocumentFingerprint } from "@/lib/directorCommandKernel";
import { getDirectorCommandFeedback } from "@/lib/directorCommandFeedback";
import { useCanvasStore } from "@/store/canvasStore";
import {
  getDirectorProjectRegistrySnapshot,
  useDirectorStore,
  type DirectorAspectRatio,
  type DirectorCapture,
  type DirectorViewMode,
} from "@/store/directorStore";

type MobilePanel = "tree" | "inspector" | null;
type DirectorProjectTransferStatus = "idle" | "success" | "error";

function formatDirectorShotRange(startTime: number, endTime: number): string {
  return `${startTime.toFixed(1)}-${endTime.toFixed(1)}s`;
}

function DirectorShotBar() {
  const shots = useDirectorStore((state) => state.shots);
  const activeShotId = useDirectorStore((state) => state.activeShotId);
  const selectShot = useDirectorStore((state) => state.selectShot);

  return (
    <nav
      data-director-shot-bar
      data-director-active-shot-id={activeShotId ?? ""}
      aria-label="导演台镜头"
      // Batch 613：这条 nav 是 **clone 独有**功能（源站导演台没有任何整幅
      // 页签行 —— 2026-10-01 全 DOM 搜索只命中三枚 nav：画布 navbar
      // `[0,8,1920,32]`、资源栏 `[0,52,48,1098]`、视口底部浮动药丸
      // `[780,968,128,48]`），按既定原则保留。
      //
      // Batch 617 修正了 613 给它的让位量。613 把资源栏与场景树按源站归位到
      // 52..1150（左列 0..281 整条），却只把镜头条右移了 48px（`ml-12`），
      // 结果镜头条的内容（`镜头` 标签 + `机位N` chip，自 x=48 起）**整条落在
      // 场景树底下** —— 树 z-30、镜头条 z-auto，chip 点不动。613 的验收只断言
      // 了标签的 x ≥ 48，没断言它在上层，漏了过去（见 probe617 的命中普查：
      // 导演台 120 枚可交互控件里 chip 是唯一被自家树盖住的一枚）。
      //
      // 正确让位量是**整条左列 281px**（48 资源栏 + 233 场景树）：镜头条自
      // x=281 起，与源站左列的结构一致 —— 源站在 y 52..88 这条带里 x<281 的
      // 部分同样是左列。窄屏 rail 隐藏、场景树是抽屉，故不加边距。
      className="flex h-9 shrink-0 items-center gap-2 overflow-x-auto border-b border-white/[0.07] bg-[#171717] px-3 min-[900px]:ml-[281px]"
    >
      <span className="shrink-0 text-[10px] uppercase tracking-[0.08em] text-[#666]">
        镜头
      </span>
      <div className="flex min-w-0 items-center gap-1">
        {shots.map((shot) => {
          const active = shot.id === activeShotId;
          return (
            <button
              key={shot.id}
              type="button"
              data-director-shot-option={shot.id}
              aria-pressed={active}
              onClick={() => selectShot(shot.id)}
              className={cn(
                "flex h-7 shrink-0 items-center gap-2 rounded border px-2 text-left text-[10px] text-[#858585] hover:text-white",
                active
                  ? "border-[#09caf5]/40 bg-[#09caf5]/10 text-[#dffaff]"
                  : "border-white/[0.07] bg-[#222]",
              )}
            >
              <span className="max-w-[150px] truncate">{shot.name}</span>
              <span className="tabular-nums text-[#626262]">
                {formatDirectorShotRange(shot.startTime, shot.endTime)}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function getCurrentDirectorAsyncContext(): DirectorAsyncIngressContextV1 | null {
  const state = useDirectorStore.getState();
  if (
    !state.projectOwner ||
    !state.projectId ||
    !state.sessionId ||
    state.generation === null
  ) {
    return null;
  }
  const registry = getDirectorProjectRegistrySnapshot();
  const activeSession = registry.activeSession;
  if (
    !activeSession ||
    activeSession.projectId !== state.projectId ||
    activeSession.sessionId !== state.sessionId ||
    activeSession.generation !== state.generation ||
    activeSession.owner.canvasId !== state.projectOwner.canvasId ||
    activeSession.owner.sourceNodeId !== state.projectOwner.sourceNodeId
  ) {
    return null;
  }
  const record = registry.records.find(
    (candidate) => candidate.identity.projectId === state.projectId,
  );
  if (!record) return null;
  const owner: DirectorAsyncOwnerSnapshotV1 = {
    owner: { ...state.projectOwner },
    projectId: state.projectId,
    sessionId: state.sessionId,
    generation: state.generation,
  };
  return {
    owner,
    sourceFingerprint: directorDocumentFingerprint(record.document),
  };
}

function releaseUnacceptedVideoResource(
  result: DirectorVideoExportResult,
): void {
  const claim = directorAsyncAuthority.claimResource(
    result.videoUrl,
    result.authority.operationId,
  );
  if (
    claim.resource?.status === "transferred" ||
    claim.resource?.status === "released"
  ) {
    return;
  }
  const release = directorAsyncAuthority.releaseResource(
    result.videoUrl,
    result.authority.operationId,
  );
  if (release.disposition === "released") {
    URL.revokeObjectURL(result.videoUrl);
  }
}

export default function DirectorDesk({
  canvasId,
  sourceNodeId,
  onClose,
}: {
  canvasId: string;
  sourceNodeId: string;
  onClose: () => void;
}) {
  const scene = useDirectorStore((state) => state.scene);
  const viewMode = useDirectorStore((state) => state.viewMode);
  const captures = useDirectorStore((state) => state.captures);
  const activeCaptureId = useDirectorStore((state) => state.activeCaptureId);
  const isCapturing = useDirectorStore((state) => state.isCapturing);
  const phoneVcamStatus = useDirectorStore(
    (state) => state.phoneVcam.status,
  );
  const aspectRatio = useDirectorStore((state) => state.aspectRatio);
  const timelineDuration = useDirectorStore(
    (state) => state.timeline.duration,
  );
  const viewportPanelsCollapsed = useDirectorStore(
    (state) => state.viewportPanelsCollapsed,
  );
  const openSession = useDirectorStore((state) => state.openSession);
  const exportDirectorProject = useDirectorStore(
    (state) => state.exportDirectorProject,
  );
  const importDirectorProject = useDirectorStore(
    (state) => state.importDirectorProject,
  );
  const closeSession = useDirectorStore((state) => state.closeSession);
  const projectId = useDirectorStore((state) => state.projectId);
  const sessionId = useDirectorStore((state) => state.sessionId);
  const generation = useDirectorStore((state) => state.generation);
  const projectLifecycle = useDirectorStore(
    (state) => state.projectLifecycle,
  );
  const sessionOutcome = useDirectorStore((state) => state.sessionOutcome);
  const history = useDirectorStore((state) => state.history);
  const lastCommandResult = useDirectorStore(
    (state) => state.lastCommandResult,
  );
  const undoDirector = useDirectorStore((state) => state.undoDirector);
  const redoDirector = useDirectorStore((state) => state.redoDirector);
  const copyDirectorSelection = useDirectorStore(
    (state) => state.copyDirectorSelection,
  );
  const pasteDirectorClipboard = useDirectorStore(
    (state) => state.pasteDirectorClipboard,
  );
  const cancelDirectorGesture = useDirectorStore(
    (state) => state.cancelDirectorGesture,
  );
  const deleteDirectorEntity = useDirectorStore(
    (state) => state.deleteDirectorEntity,
  );
  const setViewMode = useDirectorStore((state) => state.setViewMode);
  // Batch 605：源站在机位跟随时于视口顶部正中挂一条「正在跟随」浮层。跟随
  // 判据取活动机位的 `camera.followTargetId` 非空——与 DirectorInspector 的
  // 「跟随目标」选择器、DirectorTimeline/PhoneVcam 的「请先关闭机位跟随」
  // 前置条件用的是同一个字段（store:6308 `camera.camera?.followTargetId`）。
  const activeCameraId = useDirectorStore((state) => state.activeCameraId);
  // Batch 606：源站右头那 280px 定宽列里只放一行选中对象名
  // （`text-[15px] font-medium text-neutral-50`）。clone 此前右头只有
  // 状态文案与项目导入导出，没有对象名。
  const headerObjectName = useDirectorStore((state) => {
    const id =
      state.selectedObjectIds.length > 0
        ? state.selectedObjectIds[0]
        : state.selectedObjectId;
    if (!id) return null;
    return state.objects.find((object) => object.id === id)?.name ?? null;
  });
  const followTargetId = useDirectorStore((state) => {
    const camera = state.objects.find((object) => object.id === state.activeCameraId);
    return camera?.camera?.followTargetId ?? null;
  });
  const updateCamera = useDirectorStore((state) => state.updateCamera);
  const setAspectRatio = useDirectorStore((state) => state.setAspectRatio);
  const setViewportPanelsCollapsed = useDirectorStore(
    (state) => state.setViewportPanelsCollapsed,
  );
  const markCaptureSent = useDirectorStore((state) => state.markCaptureSent);
  const createDirectorCapture = useCanvasStore(
    (state) => state.createDirectorCapture,
  );
  const createDirectorAnimationExport = useCanvasStore(
    (state) => state.createDirectorAnimationExport,
  );
  const canvases = useCanvasStore((state) => state.canvases);
  const selectNode = useCanvasStore((state) => state.selectNode);
  const activeCanvas = useMemo(
    () => canvases.find((canvas) => canvas.id === canvasId),
    [canvasId, canvases],
  );
  const canvasMediaInputs = useMemo(
    () => collectDirectorCanvasMediaInputs(activeCanvas, sourceNodeId),
    [activeCanvas, sourceNodeId],
  );
  const [panoramaSourceId, setPanoramaSourceId] = useState<
    string | null | undefined
  >(undefined);
  const [panoramaRuntimeState, setPanoramaRuntimeState] =
    useState<DirectorPanoramaRuntimeState>("empty");
  const [mobilePanel, setMobilePanel] = useState<MobilePanel>(null);
  const [exportPanelOpen, setExportPanelOpen] = useState(false);
  const [exportDuration, setExportDuration] = useState(timelineDuration);
  const [exportAspectRatio, setExportAspectRatio] =
    useState<DirectorAspectRatio>(aspectRatio);
  const [exportStatus, setExportStatus] =
    useState<DirectorExportStatus>("idle");
  const [exportProgress, setExportProgress] = useState(0);
  const [exportError, setExportError] = useState<string | null>(null);
  const [videoExportRequest, setVideoExportRequest] =
    useState<DirectorVideoExportRequest | null>(null);
  const [exportedNodeId, setExportedNodeId] = useState<string | null>(null);
  const [projectTransferStatus, setProjectTransferStatus] =
    useState<DirectorProjectTransferStatus>("idle");
  const [projectTransferMessage, setProjectTransferMessage] = useState<
    string | null
  >(null);
  const workspaceRef = useRef<HTMLDivElement>(null);
  const treePanelRef = useRef<HTMLElement>(null);
  const inspectorPanelRef = useRef<HTMLElement>(null);
  const mobilePanelReturnRef = useRef<HTMLElement | null>(null);
  const projectImportInputRef = useRef<HTMLInputElement>(null);
  const exportRequestId = useRef(0);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const exporting = exportStatus === "exporting";
  const phoneVcamRecording = phoneVcamStatus === "recording";
  const workspaceBusy = exporting || phoneVcamRecording;
  const activeMobilePanel = viewportPanelsCollapsed ? null : mobilePanel;
  const activeCapture = useMemo(
    () => captures.find((capture) => capture.id === activeCaptureId) ?? null,
    [activeCaptureId, captures],
  );
  const resolvedPanoramaSourceId = useMemo(
    () =>
      panoramaSourceId === undefined
        ? canvasMediaInputs[0]?.sourceNodeId ?? null
        : canvasMediaInputs.some(
              (input) => input.sourceNodeId === panoramaSourceId,
            )
          ? panoramaSourceId
          : null,
    [canvasMediaInputs, panoramaSourceId],
  );
  const selectedPanoramaInput = useMemo<DirectorCanvasMediaInputV1 | null>(
    () =>
      canvasMediaInputs.find(
        (input) => input.sourceNodeId === resolvedPanoramaSourceId,
      ) ?? null,
    [canvasMediaInputs, resolvedPanoramaSourceId],
  );
  const projectOwner = useMemo(
    () => ({ route: "libtv" as const, canvasId, sourceNodeId }),
    [canvasId, sourceNodeId],
  );
  const commandFeedback = useMemo(
    () => getDirectorCommandFeedback(lastCommandResult),
    [lastCommandResult],
  );
  const activeMobileFocusScope =
    isMobileViewport && activeMobilePanel ? activeMobilePanel : null;
  const {
    restoreFocus,
    returnDisposition,
  } = useDirectorFocusContainment({
    rootRef: workspaceRef,
    initialFocus: "root",
    returnFocus: true,
  });
  useDirectorFocusContainment({
    rootRef: treePanelRef,
    enabled: activeMobileFocusScope === "tree",
    initialFocus: "first",
    stopPropagation: true,
  });
  useDirectorFocusContainment({
    rootRef: inspectorPanelRef,
    enabled: activeMobileFocusScope === "inspector",
    initialFocus: "first",
    stopPropagation: true,
  });

  useEffect(() => {
    openSession(projectOwner);
  }, [openSession, projectOwner]);

  useEffect(() => {
    // Batch 622 修：阈值必须与 CSS 的**实际**落点一致。
    // Tailwind v4 把 `max-[899px]` 编译成 `@media (width < 899px)`，即
    // 「宽度 ≤ 898」才走窄屏（见 621 README 的逐像素读数）。而这里原来写的是
    // `matchMedia("(max-width: 899px)")`，语义是「≤ 899」—— 两边**差一个
    // 像素**，于是 vw=899 这一档 JS 判移动端、CSS 判桌面：
    // 场景树与属性列被按桌面布局**可见地**渲染在 [0,88] 与 [618,52]，
    // 却又被 `treeMobileInactive` / `inspectorMobileInactive` 整棵加上
    // `inert` → 两列全部控件**可见但点不动**（普查在 899 报出 22 枚
    // covered，正是它们）。≤898 时 JS/CSS 一致（抽屉收在屏外、inert 正确），
    // ≥900 时也一致（桌面、正常）。对齐到 898 即抹平这唯一一档错位。
    // 选「改 JS 对齐 CSS」而不是反过来改 CSS：全代码库每一条 `max-[899px]`
    // 的落点都在 898/899（621 已记录为不改的既有约定），改 CSS 会一次性
    // 移动所有同类规则。
    const media = window.matchMedia("(max-width: 898px)");
    const update = () => setIsMobileViewport(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      workspaceRef.current?.focus({ preventScroll: true });
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const openMobilePanel = useCallback(
    (panel: Exclude<MobilePanel, null>) => {
      const activeElement = document.activeElement;
      if (activeElement instanceof HTMLElement) {
        mobilePanelReturnRef.current = activeElement;
      }
      setViewportPanelsCollapsed(false);
      setMobilePanel(panel);
    },
    [setViewportPanelsCollapsed],
  );

  const closeMobilePanel = useCallback(() => {
    setMobilePanel(null);
    const target = mobilePanelReturnRef.current;
    window.requestAnimationFrame(() => {
      if (target?.isConnected && !target.hasAttribute("disabled")) {
        target.focus({ preventScroll: true });
      } else {
        workspaceRef.current?.focus({ preventScroll: true });
      }
    });
  }, []);

  useEffect(() => {
    if (!activeMobileFocusScope) return;
    const panel =
      activeMobileFocusScope === "tree"
        ? treePanelRef.current
        : inspectorPanelRef.current;
    if (!panel) return;
    const frame = window.requestAnimationFrame(() => {
      const first = getDirectorFocusableElements(panel)[0];
      first?.focus({ preventScroll: true });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [activeMobileFocusScope]);

  const treeMobileInactive =
    isMobileViewport &&
    (activeMobilePanel !== "tree" || viewportPanelsCollapsed);
  const inspectorMobileInactive =
    isMobileViewport &&
    (activeMobilePanel !== "inspector" || viewportPanelsCollapsed);

  const closeWorkspace = useCallback(() => {
    if (workspaceBusy) return;
    if (useDirectorStore.getState().history.activeGesture) {
      cancelDirectorGesture();
    }
    closeSession(projectOwner);
    selectNode(exportedNodeId ?? sourceNodeId);
    restoreFocus();
    onClose();
  }, [
    closeSession,
    cancelDirectorGesture,
    exportedNodeId,
    onClose,
    projectOwner,
    restoreFocus,
    selectNode,
    sourceNodeId,
    workspaceBusy,
  ]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target;
      const isEditable =
        target instanceof HTMLElement &&
        (target.isContentEditable ||
          target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT");
      if (event.isComposing) return;
      if (event.key === "Escape" && activeMobilePanel) {
        event.preventDefault();
        closeMobilePanel();
        return;
      }
      if (isEditable) return;

      const modifier = event.metaKey || event.ctrlKey;
      if (modifier && event.key.toLowerCase() === "c") {
        event.preventDefault();
        copyDirectorSelection();
        return;
      }
      if (modifier && event.key.toLowerCase() === "v") {
        if (
          workspaceBusy ||
          document.querySelector("[data-director-capture-viewer]")
        ) {
          return;
        }
        event.preventDefault();
        pasteDirectorClipboard();
        return;
      }
      if (modifier && event.key.toLowerCase() === "z") {
        event.preventDefault();
        if (event.shiftKey) redoDirector();
        else undoDirector();
        return;
      }
      if (modifier && event.key.toLowerCase() === "y") {
        event.preventDefault();
        redoDirector();
        return;
      }
      if (event.key === "Delete" || event.key === "Backspace") {
        if (
          workspaceBusy ||
          document.querySelector("[data-director-capture-viewer]")
        ) {
          return;
        }
        const directorState = useDirectorStore.getState();
        if (directorState.selectedGroupId) {
          event.preventDefault();
          deleteDirectorEntity({
            kind: "DELETE_GROUP",
            groupId: directorState.selectedGroupId,
            memberPolicy: "UNGROUP",
          });
          return;
        }
        const objectIds =
          directorState.selectedObjectIds.length > 0
            ? directorState.selectedObjectIds
            : directorState.selectedObjectId
              ? [directorState.selectedObjectId]
              : [];
        if (objectIds.length > 0) {
          event.preventDefault();
          deleteDirectorEntity({
            kind: "DELETE_OBJECTS",
            objectIds,
          });
        }
        return;
      }
      if (event.key !== "Escape") return;
      event.preventDefault();
      if (document.querySelector("[data-director-capture-viewer]")) return;
      if (workspaceBusy) return;
      if (useDirectorStore.getState().history.activeGesture) {
        cancelDirectorGesture();
        return;
      }
      if (exportPanelOpen) {
        setExportPanelOpen(false);
        return;
      }
      // Batch 605（源站实测）：跟随浮层的提示气泡逐字是「按 ESC 退出」——
      // ESC 在机位跟随时**先退出跟随**，而不是直接关掉整个导演台。这一档
      // 必须排在 closeWorkspace() 之前。
      if (followTargetId) {
        if (activeCameraId) updateCamera(activeCameraId, { followTargetId: null });
        return;
      }
      closeWorkspace();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    activeCameraId,
    activeMobilePanel,
    cancelDirectorGesture,
    closeMobilePanel,
    closeWorkspace,
    copyDirectorSelection,
    deleteDirectorEntity,
    exportPanelOpen,
    followTargetId,
    pasteDirectorClipboard,
    redoDirector,
    undoDirector,
    updateCamera,
    workspaceBusy,
  ]);

  const sendCapture = (capture: DirectorCapture) => {
    if (capture.sentNodeId) return;
    const nodeId = createDirectorCapture(sourceNodeId, {
      captureId: capture.id,
      cameraId: capture.cameraId,
      cameraName: capture.cameraName,
      aspectRatio: capture.aspectRatio,
      width: capture.width,
      height: capture.height,
      createdAt: capture.createdAt,
      dataUrl: capture.dataUrl,
    });
    if (nodeId) markCaptureSent(capture.id, nodeId);
  };

  const sendAllCaptures = () => {
    captures
      .filter((capture) => !capture.sentNodeId)
      .forEach((capture) => {
        const nodeId = createDirectorCapture(sourceNodeId, {
          captureId: capture.id,
          cameraId: capture.cameraId,
          cameraName: capture.cameraName,
          aspectRatio: capture.aspectRatio,
          width: capture.width,
          height: capture.height,
          createdAt: capture.createdAt,
          dataUrl: capture.dataUrl,
        });
        if (nodeId) markCaptureSent(capture.id, nodeId);
      });
  };

  const toggleExportPanel = () => {
    if (workspaceBusy) return;
    setExportPanelOpen((open) => {
      const nextOpen = !open;
      if (nextOpen) {
        setExportDuration((duration) =>
          Math.min(Math.max(duration, 1), timelineDuration),
        );
        setExportAspectRatio(aspectRatio);
      }
      return nextOpen;
    });
  };

  const changeExportDuration = (duration: number) => {
    const nextDuration = Number.isFinite(duration)
      ? Math.min(Math.max(duration, 1), timelineDuration)
      : 1;
    setExportDuration(nextDuration);
  };

  const changeExportAspectRatio = (ratio: DirectorAspectRatio) => {
    setExportAspectRatio(ratio);
    setAspectRatio(ratio);
  };

  const beginVideoExport = () => {
    if (workspaceBusy) return;
    const durationSeconds = Math.min(
      Math.max(exportDuration, 1),
      timelineDuration,
    );
    exportRequestId.current += 1;
    setExportDuration(durationSeconds);
    setExportError(null);
    setExportProgress(0);
    setExportStatus("exporting");
    setExportedNodeId(null);
    const context = getCurrentDirectorAsyncContext();
    if (!context || context.owner.owner.sourceNodeId !== sourceNodeId) {
      setExportError("导演台会话已失效，请重新打开后导出");
      setExportStatus("error");
      return;
    }
    const operationId = createDirectorAsyncIdentity("director-video-export");
    const descriptor = {
      operationId,
      kind: "video-export" as const,
      owner: context.owner,
      attemptId: createDirectorAsyncIdentity("director-video-export-attempt"),
      sourceFingerprint: context.sourceFingerprint,
      requestFingerprint: JSON.stringify({
        durationSeconds,
        aspectRatio: exportAspectRatio,
      }),
      acceptedAt: new Date().toISOString(),
      selectionPolicy: "select-result" as const,
    };
    const begin = directorAsyncAuthority.begin(descriptor);
    if (begin.disposition !== "accepted") {
      setExportError("导出请求未被接受，请重试");
      setExportStatus("error");
      return;
    }
    setVideoExportRequest({
      id: exportRequestId.current,
      durationSeconds,
      aspectRatio: exportAspectRatio,
      authority: descriptor,
    });
  };

  const completeVideoExport = useCallback(
    (result: DirectorVideoExportResult) => {
      const context = getCurrentDirectorAsyncContext();
      const envelope: DirectorAsyncResultEnvelopeV1<DirectorVideoExportResult> =
        {
          operationId: result.authority.operationId,
          kind: result.authority.kind,
          owner: result.authority.owner,
          attemptId: result.authority.attemptId,
          sourceFingerprint: result.authority.sourceFingerprint,
          resultId: result.exportId,
          resultVersionId: result.exportId,
          phase: "succeeded",
          payload: result,
        };
      const ingress = context
        ? directorAsyncAuthority.reconcile(envelope, context)
        : {
            disposition: "reject-stale" as const,
            reason: "DIRECTOR_ASYNC_OWNER_STALE" as const,
          };
      if (ingress.disposition !== "apply-current") {
        releaseUnacceptedVideoResource(result);
        setExportError("导出结果已失效，请重新导出");
        setExportStatus("error");
        return;
      }
      const claim = directorAsyncAuthority.claimResource(
        result.videoUrl,
        result.authority.operationId,
      );
      if (
        claim.disposition === "reject-invalid" ||
        !claim.resource ||
        claim.resource.status === "transferred" ||
        claim.resource.status === "released"
      ) {
        releaseUnacceptedVideoResource(result);
        setExportError("导出资源状态无效，请重新导出");
        setExportStatus("error");
        return;
      }
      const directorState = useDirectorStore.getState();
      const activeCamera = directorState.objects.find(
        (object) => object.id === directorState.activeCameraId,
      );
      const nodeId = createDirectorAnimationExport(sourceNodeId, {
        exportId: result.exportId,
        sceneName: directorState.scene.name,
        cameraId: activeCamera?.id ?? null,
        cameraName: activeCamera?.name ?? "导演视角",
        aspectRatio: result.aspectRatio,
        width: result.width,
        height: result.height,
        durationSeconds: result.durationSeconds,
        mimeType: result.mimeType,
        sizeBytes: result.sizeBytes,
        createdAt: result.createdAt,
        videoUrl: result.videoUrl,
        posterDataUrl: result.posterDataUrl,
      });
      if (!nodeId) {
        const release = directorAsyncAuthority.releaseResource(
          result.videoUrl,
          result.authority.operationId,
        );
        if (release.disposition === "released") {
          URL.revokeObjectURL(result.videoUrl);
        }
        setExportError("视频已生成，但画布节点创建失败");
        setExportStatus("error");
        return;
      }
      directorAsyncAuthority.transferResource(
        result.videoUrl,
        result.authority.operationId,
        result.exportId,
      );
      setExportProgress(1);
      setExportError(null);
      setExportedNodeId(nodeId);
      setExportStatus("success");
    },
    [createDirectorAnimationExport, sourceNodeId],
  );

  const failVideoExport = useCallback(
    (message: string) => {
      const request = videoExportRequest;
      const context = getCurrentDirectorAsyncContext();
      if (request && context) {
        const envelope: DirectorAsyncResultEnvelopeV1<{ message: string }> = {
          operationId: request.authority.operationId,
          kind: request.authority.kind,
          owner: request.authority.owner,
          attemptId: request.authority.attemptId,
          sourceFingerprint: request.authority.sourceFingerprint,
          resultId: `${request.authority.operationId}-failure`,
          resultVersionId: `${request.authority.operationId}-failure`,
          phase: "failed",
          payload: { message },
        };
        directorAsyncAuthority.reconcile(envelope, context);
      }
      setExportError(message);
      setExportStatus("error");
    },
    [videoExportRequest],
  );

  const exportProjectFile = useCallback(() => {
    const payload = exportDirectorProject();
    if (!payload) {
      setProjectTransferStatus("error");
      setProjectTransferMessage("当前导演台会话不可导出");
      return;
    }
    const sceneName = scene.name
      .trim()
      .replace(/[^\p{L}\p{N}_-]+/gu, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 48);
    const fileName = `director-project-${sceneName || "project"}.json`;
    const url = URL.createObjectURL(
      new Blob([payload], { type: "application/json" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
    setProjectTransferStatus("success");
    setProjectTransferMessage("项目已导出");
  }, [exportDirectorProject, scene.name]);

  const importProjectFile = useCallback(
    async (file: File) => {
      try {
        const result = importDirectorProject(await file.text());
        if (result.disposition === "COMMITTED") {
          setProjectTransferStatus("success");
          setProjectTransferMessage("项目已导入");
          return;
        }
        if (result.disposition === "NOOP") {
          setProjectTransferStatus("success");
          setProjectTransferMessage("项目内容未变化");
          return;
        }
        setProjectTransferStatus("error");
        setProjectTransferMessage(
          result.reason === "DIRECTOR_IMPORT_BUSY"
            ? "当前操作进行中，请稍后重试"
            : result.reason === "DIRECTOR_PROJECT_MISSING"
              ? "导演台会话已失效，请重新打开"
              : "项目文件无效，未修改当前项目",
        );
      } catch {
        setProjectTransferStatus("error");
        setProjectTransferMessage("项目文件读取失败，未修改当前项目");
      }
    },
    [importDirectorProject],
  );

  const handleProjectImportChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.currentTarget.files?.[0] ?? null;
      event.currentTarget.value = "";
      if (!file || workspaceBusy) return;
      void importProjectFile(file);
    },
    [importProjectFile, workspaceBusy],
  );

  return (
    <div
      ref={workspaceRef}
      data-director-workspace
      data-director-workspace-focus-owner
      data-director-canvas-id={canvasId}
      data-director-source-node-id={sourceNodeId}
      data-director-project-id={projectId ?? ""}
      data-director-session-id={sessionId ?? ""}
      data-director-generation={generation ?? ""}
      data-director-project-lifecycle={projectLifecycle ?? ""}
      data-director-session-disposition={sessionOutcome?.disposition ?? ""}
      data-director-session-reason={sessionOutcome?.reason ?? ""}
      data-director-session-previous-owner={
        sessionOutcome?.previousOwnerKey ?? ""
      }
      data-director-history-past={history.past.length}
      data-director-history-future={history.future.length}
      data-director-active-gesture={history.activeGesture?.gestureId ?? ""}
      data-director-last-command={lastCommandResult?.commandKind ?? ""}
      data-director-last-disposition={lastCommandResult?.disposition ?? ""}
      data-director-last-reason={lastCommandResult?.reason ?? ""}
      data-director-project-io-status={projectTransferStatus}
      data-director-project-io-message={projectTransferMessage ?? ""}
      data-director-panels-collapsed={viewportPanelsCollapsed}
      data-director-focus-scope="workspace"
      data-director-focus-return={returnDisposition}
      data-director-focus-state={
        activeMobileFocusScope ? `mobile-${activeMobileFocusScope}` : "workspace"
      }
      role="dialog"
      aria-modal="true"
      aria-label="3D导演台工作区"
      tabIndex={-1}
      className="fixed inset-0 z-[100] flex h-dvh w-screen flex-col overflow-hidden bg-[#151515] text-[#ededed]"
    >
      <header
        data-director-header
        // Batch 606（源站 2026-10-01 实测）：顶栏高 52px；左右各一条**定宽
        // 280px** 的列（源站 `header.border-white/8.flex.h-[52px].items-center
        // .border-b` 与 `div.flex.shrink-0.items-center.justify-between.h-12
        // .px-3`），中间是 52px 悬浮带里的视角对（batch 605）。clone 此前是
        // 横跨全宽的三列 grid + h-12，这里把两侧改成 ≥900px 时的 280px 定宽列，
        // 窄屏（<900px，与 clone 既有的 max-[899px] 面板折叠断点一致）仍流式。
        className="relative z-40 grid h-[52px] shrink-0 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center border-b border-white/[0.08] bg-[#181818]"
      >
        {/* 左头 280px：关闭(40) + 标题(flex-1) + 收起(40)，三者间隙全为 0
            （40 + 200 + 40 = 280）。两枚图标按钮都是 40x40 的
            `text-white/72 … hover:text-white`，图标 16px。clone 原先是
            32x32 `rounded text-[#a3a3a3]`，且把「返回画布」和「关闭导演台」
            做成两个都调 closeWorkspace 的冗余按钮——源站左头只有一个关闭。

            Batch 615：`max-w-[calc(50vw-85px)]` 是窄屏下的碰撞解药。视角
            切换器是 `absolute left-1/2 -translate-x-1/2` 的 **170px 定宽**，
            它无视 grid 直接骑在正中，390px 视口下占 110..280；而左列是
            `minmax(0,1fr)`，分到 147.5，收起按钮落在 99.5..139.5 —— 右半
            被切换器整个压住，点 56 次都命中不了它（batch 94 移动腿红，
            基线对照确认与 613/614 无关）。把左列压到切换器左缘
            `50vw − 85`（85 = 170/2）即可让开：390 时左列 110、收起
            62..102，与 110 相接不重叠；≥900 时 `50vw−85 ≥ 395 > 280`，
            该上限永不生效，源站的 280 定宽与几何一字未动。 */}
        <div className="flex h-full min-w-0 max-w-[calc(50vw-85px)] items-center max-[899px]:px-2 min-[900px]:max-w-none min-[900px]:w-[280px] min-[900px]:shrink-0">
          <button
            type="button"
            data-close-director
            aria-label="关闭"
            title="关闭"
            disabled={workspaceBusy}
            onClick={closeWorkspace}
            className="flex size-10 shrink-0 items-center justify-center text-white/72 transition-colors hover:text-white disabled:opacity-35"
          >
            <X size={16} aria-hidden="true" />
          </button>
          {/* 源站标题槽是单行 `min-w-0 flex-1 truncate text-[14px]
              leading-[22px] text-white/90`。clone 保留 batch 587 钉住的
              h1「3D导演台」，并把场景名作为 clone-only 的第二行小字。 */}
          <div className="min-w-0 flex-1 truncate px-2 text-[14px] leading-[22px] text-white/90">
            <h1 className="truncate">
              3D导演台
            </h1>
            <p className="truncate text-[10px] text-[#666] max-[520px]:hidden">
              {scene.name}
            </p>
          </div>
          {/* Batch 587（源站 2026-10-01 实测）：顶栏唯一的折叠入口是
              「收起」，位于标题右侧。它只收掉左侧场景面板——图标栏、
              3D 视口、右侧属性面板、视角切换、gizmo、重置视角全部保留
              （源站收起后实测 header 与左面板从 DOM 移除，其余坐标不变）。
              恢复入口不是第二个按钮，而是图标栏的「场景」条目。原先挂在
              视口底栏的「全屏 / 恢复侧栏」是 clone 独有的全幅折叠，与源站
              不符，本批移除。Batch 606：尺寸/配色改源站的 40x40
              `text-white/72`，图标 17px -> 16px。 */}
          {!viewportPanelsCollapsed ? (
            <button
              type="button"
              data-director-panels-toggle
              aria-label="收起"
              title="收起"
              aria-pressed={false}
              onClick={() => setViewportPanelsCollapsed(true)}
              className="flex size-10 shrink-0 items-center justify-center text-white/72 transition-colors hover:text-white"
            >
              <PanelLeftOpen size={16} aria-hidden="true" />
            </button>
          ) : null}
        </div>

        {/* 命令反馈移到中间格：左头定宽 280px 之后塞不下它（max-w-[220px]
            + ml-3 + pl-3）。仍在 header 内，batch 83 的包含性断言不受影响。 */}
        <div className="flex min-w-0 items-center justify-center px-2">
          <div
            data-director-command-feedback
            data-director-command-feedback-disposition={
              commandFeedback?.disposition ?? "hidden"
            }
            data-director-command-feedback-reason={
              commandFeedback?.reason ?? ""
            }
            role="status"
            aria-live="polite"
            aria-atomic="true"
            className={cn(
              "flex min-w-0 max-w-[220px] items-center gap-1 truncate border-l border-white/10 pl-3 text-[10px]",
              commandFeedback?.tone === "error"
                ? "text-[#ef9292]"
                : commandFeedback?.tone === "warning"
                  ? "text-[#e5c58b]"
                  : "text-[#a7b9c5]",
              !commandFeedback && "invisible",
            )}
          >
            {commandFeedback?.tone === "error" ? (
              <AlertTriangle size={12} className="shrink-0" aria-hidden="true" />
            ) : (
              <Info size={12} className="shrink-0" aria-hidden="true" />
            )}
            <span className="truncate">
              {commandFeedback?.message ?? "无命令反馈"}
            </span>
          </div>
        </div>

        {/* Batch 605（源站 2026-10-01 实测 1920x1150）：这一对**不是**顶栏
            grid 的一格，而是浮在视口上方正中：
              div.pointer-events-auto.absolute.left-1/2.top-2.-translate-x-1/2
                  div.border-white/8.flex.h-9.items-center.justify-center
                      .gap-0.5.overflow-hidden.rounded-xl.border
                      .bg-[#212121].p-0.5.w-[170px]          170x36 @(875,8)
                ├ button h-8.rounded-[10px].text-[13px].leading-5
                │        .transition-colors.min-w-0.flex-1.px-2
                │        .bg-white/10.text-neutral-50           81x32 @(878,10)
                └ button …text-neutral-50.hover:bg-white/10      81x32 @(961,10)
            两者间隙 2px（容器 gap-0.5）；两枚按钮的**文字色相同**
            （都是 text-neutral-50），只有底色区分选中态。
            源站这两枚按钮**没有 aria-label**，可及名来自可见文字；clone
            保留 aria-label（可及名等价，且便于定位）。 */}
        <div
          role="group"
          aria-label="导演台视角"
          className="pointer-events-auto absolute left-1/2 top-2 z-10 -translate-x-1/2"
        >
          <div className="flex h-9 w-[170px] items-center justify-center gap-0.5 overflow-hidden rounded-xl border border-white/[0.08] bg-[#212121] p-0.5">
            {(
              [
                ["director", "导演视角"],
                ["camera", "机位视角"],
              ] as Array<[DirectorViewMode, string]>
            ).map(([mode, label]) => (
              <button
                key={mode}
                type="button"
                data-director-view-mode={mode}
                aria-pressed={viewMode === mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  "flex h-8 min-w-0 flex-1 items-center justify-center rounded-[10px] px-2 text-[13px] leading-5 text-neutral-50 transition-colors hover:bg-white/10 max-[430px]:px-1",
                  viewMode === mode && "bg-white/10",
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* 右头 280px（Batch 606，源站实测 `flex shrink-0 items-center
            justify-between h-12 px-3`）：源站这列里只有一行选中对象名
            `text-[15px] font-medium text-neutral-50`；clone 保留自己的
            状态文案与项目导入导出（源站导演台顶栏无对应物，clone-only）。 */}
        <div className="flex h-full min-w-0 items-center justify-end gap-2 max-[899px]:px-2 min-[900px]:w-[280px] min-[900px]:shrink-0 min-[900px]:justify-between min-[900px]:px-3 min-[900px]:justify-self-end">
          <span
            data-director-header-object-name
            className="min-w-0 truncate text-[15px] font-medium text-neutral-50"
          >
            {headerObjectName ?? "—"}
          </span>
          <div
            data-director-capture-status={
              exporting
                ? "exporting"
                : phoneVcamRecording
                  ? "phone-recording"
                : isCapturing
                  ? "capturing"
                  : activeCapture
                    ? "ready"
                    : "empty"
            }
            className="mr-1 flex min-w-0 items-center gap-1.5 px-2 text-[10px] text-[#777] max-[620px]:hidden"
          >
            {exporting ? (
              <>
                <span className="h-2 w-2 animate-pulse rounded-full bg-[#09caf5]" />
                导出中 {Math.round(exportProgress * 100)}%
              </>
            ) : phoneVcamRecording ? (
              <>
                <span className="h-2 w-2 animate-pulse rounded-full bg-[#e25c60]" />
                手机运镜录制中
              </>
            ) : isCapturing ? (
              <>
                <span className="h-2 w-2 animate-pulse rounded-full bg-[#09caf5]" />
                正在截图
              </>
            ) : activeCapture ? (
              <>
                {activeCapture.sentNodeId ? <Check size={12} /> : <ImageIcon size={12} />}
                {activeCapture.sentNodeId ? "已回到画布" : `${captures.length} 张构图`}
              </>
            ) : (
              "尚无构图"
            )}
          </div>
          <div className="relative">
            <input
              ref={projectImportInputRef}
              type="file"
              accept=".json,application/json"
              data-director-project-import-input
              className="hidden"
              onChange={handleProjectImportChange}
            />
            <button
              type="button"
              data-director-project-export
              aria-label="导出导演台项目"
              title="导出项目 JSON"
              disabled={workspaceBusy}
              onClick={exportProjectFile}
              className="flex h-8 w-8 items-center justify-center rounded text-[#9d9d9d] hover:bg-white/[0.06] hover:text-white disabled:text-[#555]"
            >
              <Download size={14} />
            </button>
          </div>
          <button
            type="button"
            data-director-project-import
            aria-label="导入导演台项目"
            title="导入项目 JSON"
            disabled={workspaceBusy}
            onClick={() => projectImportInputRef.current?.click()}
            className="flex h-8 w-8 items-center justify-center rounded text-[#9d9d9d] hover:bg-white/[0.06] hover:text-white disabled:text-[#555]"
          >
            <Upload size={14} />
          </button>
          <div
            data-director-project-io-feedback
            aria-live="polite"
            className={cn(
              "max-w-[120px] truncate px-1 text-[10px]",
              projectTransferStatus === "error"
                ? "text-[#ef9292]"
                : projectTransferStatus === "success"
                  ? "text-[#9ddbb9]"
                  : "text-transparent",
            )}
          >
            {projectTransferMessage ?? ""}
          </div>
          {/* Batch 606：原先右头这枚「关闭导演台」已移到左头（与源站一致，
              源站的关闭在左头最左端），此处移除——它与新左头的「关闭」是
              同一个 closeWorkspace，留着就是同一动作的第二枚按钮。 */}
        </div>
      </header>

      <DirectorShotBar />

      {/* Batch 613（源站 2026-10-01 实测，/tmp/src593/probe613d + 613i + 613f）：
          源站左列是**一块** `aside.absolute.inset-y-0.left-0.z-30
          .overflow-hidden.border-r.border-white/10.bg-[#171717]`，281 宽、
          纵贯视口（0..1150），里面自上而下是
            header [0,0,280,52]  `flex h-[52px] items-center border-b`
            div   [0,52,280,1098] `flex h-[calc(100%-52px)]`
              nav [0,52,48,1098]   ← 资源栏
              div [48,52,232,1098] ← 场景树
          也就是说**资源栏与场景树都从 52（顶栏下沿）起、直到视口底**，
          时间线是浮在中间列上的独立覆盖层，会盖住 rail 的下段。
          clone 原先把两者 `absolute inset-y-0` 挂在中间 flex 子节点里，
          于是整体被 36px 高的镜头条（clone 独有）顶到 88、下沿又停在
          时间线上沿 968 —— 资源栏每一枚都比源站低 36px，「帮助」差 182px，
          场景树则是 46/220 而非 48/232。
          现按源站把它们提到工作区根（`fixed`，本身即包含块）并定位
          `top-[52px] bottom-0`。窄屏（<900px）下 rail 仍隐藏、场景树仍
          是 `left-0` 抽屉，故这两处覆写留在 min-[900px] 断点里。 */}
      <aside
        ref={treePanelRef}
        aria-label="场景对象"
        aria-hidden={
          viewportPanelsCollapsed || treeMobileInactive ? "true" : undefined
        }
        inert={treeMobileInactive || viewportPanelsCollapsed}
        data-director-focus-scope={
          activeMobileFocusScope === "tree" ? "tree" : undefined
        }
        data-director-mobile-panel-state={activeMobilePanel === "tree" ? "open" : "closed"}
        className={cn(
          // 233 = 源站树的 232 内容 + 源站 aside 那 1px `border-r`
          // （源站 aside 281 宽、树 48..280、边框落在 280..281）。
          "absolute bottom-0 left-0 top-[88px] z-30 w-[220px] border-r border-white/10 transition-transform duration-200 min-[900px]:left-12 min-[900px]:top-[52px] min-[900px]:w-[233px]",
          viewportPanelsCollapsed && "min-[900px]:hidden",
          activeMobilePanel === "tree"
            ? "max-[899px]:translate-x-0"
            : "max-[899px]:-translate-x-full",
        )}
      >
        <DirectorObjectTree />
      </aside>

      <DirectorIconRail onPanoramaSourceChange={setPanoramaSourceId} />

      <div className="flex min-h-0 flex-1 flex-col">
        <div className="relative min-h-0 flex-1">
          {activeMobilePanel ? (
            <button
              type="button"
              aria-label="关闭移动端面板"
              onClick={closeMobilePanel}
              className="absolute inset-0 z-20 hidden bg-black/45 max-[899px]:block"
            />
          ) : null}

          <main
            className={cn(
              "absolute inset-y-0 min-w-0 max-[899px]:inset-x-0",
              /* Batch 613/614：这两个内缩值必须与左列、右列的**实际**几何
                 对齐，否则视口框和两列之间会露出一条缝。
                 613 之后左列是 rail 0..48 + 场景树 48..281（233 宽，含那
                 1px 边框），右列 614 之后是 281 宽 —— 源站整列实测
                 `aside [0,0,281,1150]`（含 1px border-r）与
                 `div [1639,0,281,1020]`（含 1px border-l），两列合起来
                 正好把 0..281 与 1639..1920 占满。
                 此前这里是 46 / 266 / 288，是 613 之前的 46+220 与自造的
                 288，与 613/614 改完的列宽都不一致了。 */
              viewportPanelsCollapsed
                ? "left-[48px] right-[281px]"
                : "left-[281px] right-[281px]",
            )}
          >
            <DirectorViewport
              onOpenTree={() => openMobilePanel("tree")}
              onOpenInspector={() => openMobilePanel("inspector")}
              panoramaInput={selectedPanoramaInput}
              onPanoramaStatusChange={setPanoramaRuntimeState}
              videoExportRequest={videoExportRequest}
              onVideoExportProgress={setExportProgress}
              onVideoExportCompleted={completeVideoExport}
              onVideoExportFailed={failVideoExport}
              // Batch 604（源站实测）：prompt 胶囊与工具胶囊并排在视口底部
              // 同一行（`flex items-center gap-2` 居中）。此前两者各自绝对
              // 定位（工具条 z-10 @(651,904) / prompt 条 z-20 @(266,908)），
              // 几乎完全重叠且后者吞掉前者点击；现由 DirectorViewport 的
              // `data-director-bottom-bar` 统一承载。
              bottomBarExtra={<DirectorScenePromptBar />}
            />
          </main>

          {/* Batch 614（源站 2026-10-01 实测，/tmp/src593/probe614 +
              614b/614c/614d）：源站属性列的整棵子树是
              `div.absolute.right-0.top-0.z-20.flex.w-[281px].flex-col
               .overflow-hidden` → `[1639,0,281,1020]`，里面
              `div.flex.min-h-0.flex-1.flex-col.overflow-hidden.border.w-[281px]
               .border-y-0.border-l.border-r-0`（底色实测 rgb(33,33,33)
               = #212121，四条边里只有 `border-left: 1px
               rgba(255,255,255,0.08)`），再里面是 48px 标题条 + 滚动区。
              clone 此前整列比源站低 36px（88 起而非 52 起）、窄 1px、无左边框、
              底色浅两阶、标题条自造了 border-b 且是两段小字。

              **顶边**：源站是 `top-0`，因为它的顶栏只有左头 280px（就在左列
              那块 aside 里），右列上方是空的。clone 的顶栏是**通栏** grid
              （batch 606 建的），右组 280px 占着 `[1640,0,280,51]`，放到
              top-0 会把本列的标题条整个盖住 —— 等于新造一个看不见的控件。
              故上沿取 52。中间 flex 子节点从 88 起（52 顶栏 + 36 镜头条），
              故用 `-top-9`（-36px）把它提到 52。

              **底沿**：源站列高 1020 是**内容驱动**（实测 scrollHeight ==
              clientHeight == 972，根本不滚动，computed 的 `bottom:130px`
              只是派生值不是声明）。但 clone 的相机属性面板内容实测 1185，
              比源站的 907 高 278（多出 可见/未锁定、当前镜头、镜头名称 等行，
              属另一个靶心）—— 照抄内容驱动会让列冲出视口 140px；反过来若把
              列拉满到视口底，clone 比源站高 52px 的时间线（182 vs 130）会盖住
              面板下段，实测 `data-director-panorama-clear` 就此点不到
              （batch 95 回归抓到）。所以底沿交给中间区：**止于时间线上沿**，
              这正是源站那 1020 与时间线 1021 的关系。

              z 保留 30 而非源站的 20：窄屏下属性列是抽屉，必须压过 `z-20` 的
              移动端遮罩；桌面上两者无重叠区域，不影响观感。 */}
          <aside
            ref={inspectorPanelRef}
            aria-label="属性"
            aria-hidden={inspectorMobileInactive ? "true" : undefined}
            inert={inspectorMobileInactive}
            data-director-focus-scope={
              activeMobileFocusScope === "inspector" ? "inspector" : undefined
            }
            data-director-mobile-panel-state={
              activeMobilePanel === "inspector" ? "open" : "closed"
            }
            className={cn(
              /* Batch 610 此前把列宽从自造的 `w-72 border-l`（288）收到 280，
                 并说「源站该列没有左边框」—— 那句只对了一半：源站没有的是
                 **整列**的边框，列**内部**的面板有一条 1px `border-l`
                 （实测落在 1639..1640）。所以列取 281（border-box，含那
                 1px），内容仍是 280 @1640，与源站逐字对上。 */
              "absolute -top-9 bottom-0 right-0 z-30 w-[281px] overflow-hidden transition-transform duration-200",
              /* Batch 618：窄屏下 `-top-9` 必须让位。
                 `-top-9`（-36px）是桌面的取法——本 aside 的包含块是中间那格
                 `relative.min-h-0.flex-1`（y 88..668），往上提 36 让列顶边落到
                 52，与源站属性列同高。但窄屏下这 36px 正是**镜头条**那一行
                 （y 52..88），于是抽屉一打开就把 clone 自己的镜头条盖掉：
                 唯一那枚「机位01」chip 宽 177.1 @41.6，中心 130 落在抽屉
                 （x 109..390）内，点不动。
                 同一屏里另外两样东西都说明镜头条那一行**不该**被抽屉吃掉：
                 (1) 关闭抽屉的遮罩是 `absolute inset-0`，即 88..668，起点
                 正好在镜头条之下——遮罩的取景已经声明了「这一行保持可用」；
                 (2) 场景树抽屉用的是 `top-[88px] min-[900px]:top-[52px]`
                 （见上方 tree aside），窄屏同样从 88 起，只有属性抽屉没有这层
                 覆写。两个抽屉行为不一致，属遗漏而非设计。
                 故窄屏把 `-top-9` 抵掉：包含块本身就起于 88，`top-0` 即 88，
                 抽屉与遮罩、与树抽屉三者对齐；桌面 `-top-9` 原样保留，614 的
                 列几何（顶 52 / 宽 281 / 下沿止于时间线）一字未动。 */
              "max-[899px]:top-0",
              activeMobilePanel === "inspector"
                ? "max-[899px]:translate-x-0"
                : "max-[899px]:translate-x-full",
            )}
          >
            <DirectorInspector
              activeCapture={activeCapture}
              onSendCapture={sendCapture}
              onSendAllCaptures={sendAllCaptures}
              panoramaInputs={canvasMediaInputs}
              selectedPanoramaSourceId={resolvedPanoramaSourceId}
              panoramaRuntimeState={panoramaRuntimeState}
              onPanoramaSourceChange={setPanoramaSourceId}
            />
          </aside>

        </div>

        <DirectorTimeline
          trailing={
            // Batch 596（源站实测）：「导出视频到画布」在源站是时间轴工具条
            // 右端的**浅色主按钮** `(1804,1025) 108x28`，`bg-[#f7f7f7]` /
            // `text-[#141414]` / 12px medium / `rounded-lg`，**纯文字没有图标**。
            // clone 原来在顶栏，深色幽灵按钮 + FileVideo2 图标。
            <div className="relative">
              <button
                type="button"
                data-director-export-trigger
                aria-expanded={exportPanelOpen}
                disabled={workspaceBusy}
                onClick={toggleExportPanel}
                className={cn(
                  "relative flex h-7 shrink-0 items-center gap-2 rounded-lg bg-[#f7f7f7] px-3 text-[12px] font-medium leading-none text-[#141414] transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-60",
                  exportPanelOpen && "bg-white",
                )}
              >
                <span>导出视频到画布</span>
              </button>
              <DirectorExportPanel
                open={exportPanelOpen}
                status={exportStatus}
                durationSeconds={exportDuration}
                maxDurationSeconds={timelineDuration}
                aspectRatio={exportAspectRatio}
                progress={exportProgress}
                error={exportError}
                onDurationChange={changeExportDuration}
                onAspectRatioChange={changeExportAspectRatio}
                onSubmit={beginVideoExport}
              />
            </div>
          }
        />

        {/* Batch 605（源站 2026-10-01 实测 173.7x34 @(873.1,0)）：机位跟随
            时挂在视口顶部正中的橙色浮层。逐字结构：
              div.pointer-events-none.fixed.left-1/2.top-0.z-[305]
                  .-translate-x-1/2.motion-safe:transition-opacity
                  .motion-safe:duration-200
                └ div.flex.items-center.gap-2.rounded-b-xl.border.px-3.py-1.5
                    .text-white.shadow-md.pointer-events-none
                    底色与描边都是 rgb(228,101,37) = #E46525
                  ├ span.inline-block.size-2.shrink-0.rounded-full.bg-white
                  ├ span.text-sm 「正在跟随」  14px
                  └ span.relative.ml-1.inline-flex
                      ├ button[aria-label=退出跟随]
                      │   .peer.rounded-full.bg-white.px-2.py-0.5.text-xs
                      │   .font-medium.leading-none.text-gray-900
                      │   .transition-colors.hover:bg-white/90  「取消ESC」
                      └ span.pointer-events-none.absolute.left-1/2.top-full
                          .z-10.mt-2.-translate-x-1/2.whitespace-nowrap
                          .rounded-md.bg-black/90.px-2.py-1.text-xs
                          .font-normal.text-white.opacity-0.shadow-md
                          .transition-opacity.peer-hover:opacity-100
                        「按 ESC 退出」  ← hover 胶囊才显形的提示

            源站那个 8px 白点是**静态**的（animation-name: none），照抄不做
            呼吸动画。取消按钮清空 `followTargetId`，ESC 同效（见上方
            键盘处理）。 */}
        {followTargetId ? (
          <div
            data-director-follow-banner
            className="pointer-events-none fixed left-1/2 top-0 z-[305] -translate-x-1/2 motion-safe:transition-opacity motion-safe:duration-200"
          >
            <div className="pointer-events-none flex items-center gap-2 rounded-b-xl border border-[#e46525] bg-[#e46525] px-3 py-1.5 text-white shadow-md">
              <span className="inline-block size-2 shrink-0 rounded-full bg-white" />
              <span className="text-sm">正在跟随</span>
              <span className="relative ml-1 inline-flex">
                <button
                  type="button"
                  data-director-follow-cancel
                  aria-label="退出跟随"
                  onClick={() => {
                    if (activeCameraId) {
                      updateCamera(activeCameraId, { followTargetId: null });
                    }
                  }}
                  // 有意偏离源站一处：源站这枚按钮从浮层继承到
                  // `pointer-events: none`（浮层与面板都写了
                  // pointer-events-none，按钮自身没写 auto），实测
                  // elementFromPoint 落在按钮中心命中的是它**底下**的
                  // 「机位视角」，也就是说源站这枚「取消」根本点不动，
                  // 那句 peer-hover 的「按 ESC 退出」也因此永远显不出来。
                  // 几何、配色、文案全部照抄，只把命中打开——一个死按钮
                  // 不算可复刻的体验。ESC 键退出在源站是真实语义，已接上。
                  className="pointer-events-auto peer rounded-full bg-white px-2 py-0.5 text-xs font-medium leading-none text-gray-900 transition-colors hover:bg-white/90"
                >
                  {/* Batch 612 复测：源站这枚胶囊是**单文本节点**
                      `取消ESC`（own='取消ESC'，无子元素，整枚 12px/12px/500）；
                      此前 clone 拆成「取消 + 10px 的 ESC」，宽度与字重都对不上。 */}
                  取消ESC
                </button>
                <span className="pointer-events-none absolute left-1/2 top-full z-10 mt-2 -translate-x-1/2 whitespace-nowrap rounded-md bg-black/90 px-2 py-1 text-xs font-normal text-white opacity-0 shadow-md transition-opacity peer-hover:opacity-100 peer-focus-visible:opacity-100">
                  按 ESC 退出
                </span>
              </span>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
