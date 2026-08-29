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
  ArrowLeft,
  Check,
  Download,
  FileVideo2,
  ImageIcon,
  Info,
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
import { DirectorViewport } from "@/components/director/DirectorViewport";
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
  const selectNode = useCanvasStore((state) => state.selectNode);
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
  const projectImportInputRef = useRef<HTMLInputElement>(null);
  const exportRequestId = useRef(0);
  const exporting = exportStatus === "exporting";
  const phoneVcamRecording = phoneVcamStatus === "recording";
  const workspaceBusy = exporting || phoneVcamRecording;
  const activeMobilePanel = viewportPanelsCollapsed ? null : mobilePanel;
  const activeCapture = useMemo(
    () => captures.find((capture) => capture.id === activeCaptureId) ?? null,
    [activeCaptureId, captures],
  );
  const projectOwner = useMemo(
    () => ({ route: "libtv" as const, canvasId, sourceNodeId }),
    [canvasId, sourceNodeId],
  );
  const commandFeedback = useMemo(
    () => getDirectorCommandFeedback(lastCommandResult),
    [lastCommandResult],
  );

  useEffect(() => {
    openSession(projectOwner);
  }, [openSession, projectOwner]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      workspaceRef.current?.focus({ preventScroll: true });
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const openMobilePanel = useCallback(
    (panel: Exclude<MobilePanel, null>) => {
      setViewportPanelsCollapsed(false);
      setMobilePanel(panel);
    },
    [setViewportPanelsCollapsed],
  );

  const closeWorkspace = useCallback(() => {
    if (workspaceBusy) return;
    if (useDirectorStore.getState().history.activeGesture) {
      cancelDirectorGesture();
    }
    closeSession(projectOwner);
    selectNode(exportedNodeId ?? sourceNodeId);
    onClose();
  }, [
    closeSession,
    cancelDirectorGesture,
    exportedNodeId,
    onClose,
    projectOwner,
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
      if (event.isComposing || isEditable) return;

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
      if (activeMobilePanel) {
        setMobilePanel(null);
        return;
      }
      if (exportPanelOpen) {
        setExportPanelOpen(false);
        return;
      }
      closeWorkspace();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    activeMobilePanel,
    cancelDirectorGesture,
    closeWorkspace,
    copyDirectorSelection,
    deleteDirectorEntity,
    exportPanelOpen,
    pasteDirectorClipboard,
    redoDirector,
    undoDirector,
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
      data-director-history-past={history.past.length}
      data-director-history-future={history.future.length}
      data-director-active-gesture={history.activeGesture?.gestureId ?? ""}
      data-director-last-command={lastCommandResult?.commandKind ?? ""}
      data-director-last-disposition={lastCommandResult?.disposition ?? ""}
      data-director-last-reason={lastCommandResult?.reason ?? ""}
      data-director-project-io-status={projectTransferStatus}
      data-director-project-io-message={projectTransferMessage ?? ""}
      data-director-panels-collapsed={viewportPanelsCollapsed}
      role="dialog"
      aria-modal="true"
      aria-label="3D导演台工作区"
      tabIndex={-1}
      className="fixed inset-0 z-[100] flex h-dvh w-screen flex-col overflow-hidden bg-[#151515] text-[#ededed]"
    >
      <header
        data-director-header
        className="relative z-40 grid h-12 shrink-0 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center border-b border-white/[0.07] bg-[#181818] px-2"
      >
        <div className="flex min-w-0 items-center">
          <button
            type="button"
            data-close-director
            aria-label="返回画布"
            title="返回画布"
            disabled={workspaceBusy}
            onClick={closeWorkspace}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded text-[#a3a3a3] hover:bg-white/[0.06] hover:text-white disabled:text-[#555]"
          >
            <ArrowLeft size={17} />
          </button>
          <span className="mx-2 h-4 w-px shrink-0 bg-white/10" />
          <div className="min-w-0">
            <h1 className="truncate text-xs font-medium text-[#eeeeee]">3D导演台</h1>
            <p className="truncate text-[10px] text-[#666] max-[520px]:hidden">{scene.name}</p>
          </div>
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
              "ml-3 flex min-w-0 max-w-[220px] items-center gap-1 truncate border-l border-white/10 pl-3 text-[10px]",
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

        <div
          role="group"
          aria-label="导演台视角"
          className="flex h-8 items-center rounded bg-[#242424] p-0.5"
        >
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
                "h-7 rounded px-3 text-[11px] text-[#858585] max-[430px]:px-2",
                viewMode === mode && "bg-[#3a3a3a] text-white",
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex min-w-0 items-center justify-end">
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
          <div className="relative">
            <button
              type="button"
              data-director-export-trigger
              aria-expanded={exportPanelOpen}
              disabled={workspaceBusy}
              onClick={toggleExportPanel}
              className={cn(
                "flex h-8 items-center gap-1.5 rounded px-2 text-[11px] text-[#b5b5b5] hover:bg-white/[0.06] hover:text-white disabled:text-[#555]",
                exportPanelOpen && "bg-white/[0.07] text-white",
              )}
            >
              <FileVideo2 size={14} />
              <span className="max-[640px]:hidden">导出视频到画布</span>
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
          <button
            type="button"
            aria-label="关闭导演台"
            title="关闭"
            disabled={workspaceBusy}
            onClick={closeWorkspace}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded text-[#8d8d8d] hover:bg-white/[0.06] hover:text-white disabled:text-[#555]"
          >
            <X size={16} />
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col">
        <div className="relative min-h-0 flex-1">
          {activeMobilePanel ? (
            <button
              type="button"
              aria-label="关闭移动端面板"
              onClick={() => setMobilePanel(null)}
              className="absolute inset-0 z-20 hidden bg-black/45 max-[899px]:block"
            />
          ) : null}

          <aside
            aria-label="场景对象"
            aria-hidden={viewportPanelsCollapsed ? "true" : undefined}
            data-director-mobile-panel-state={activeMobilePanel === "tree" ? "open" : "closed"}
            className={cn(
              "absolute inset-y-0 left-0 z-30 w-[220px] border-r border-white/[0.07] transition-transform duration-200",
              viewportPanelsCollapsed && "min-[900px]:hidden",
              activeMobilePanel === "tree"
                ? "max-[899px]:translate-x-0"
                : "max-[899px]:-translate-x-full",
            )}
          >
            <DirectorObjectTree />
          </aside>

          <main
            className={cn(
              "absolute inset-y-0 min-w-0 max-[899px]:inset-x-0",
              viewportPanelsCollapsed
                ? "inset-x-0"
                : "left-[220px] right-[288px]",
            )}
          >
            <DirectorViewport
              onOpenTree={() => openMobilePanel("tree")}
              onOpenInspector={() => openMobilePanel("inspector")}
              videoExportRequest={videoExportRequest}
              onVideoExportProgress={setExportProgress}
              onVideoExportCompleted={completeVideoExport}
              onVideoExportFailed={failVideoExport}
            />
          </main>

          <aside
            aria-label="属性"
            aria-hidden={viewportPanelsCollapsed ? "true" : undefined}
            data-director-mobile-panel-state={activeMobilePanel === "inspector" ? "open" : "closed"}
            className={cn(
              "absolute inset-y-0 right-0 z-30 w-72 border-l border-white/[0.07] transition-transform duration-200",
              viewportPanelsCollapsed && "min-[900px]:hidden",
              activeMobilePanel === "inspector"
                ? "max-[899px]:translate-x-0"
                : "max-[899px]:translate-x-full",
            )}
          >
          <DirectorInspector
            activeCapture={activeCapture}
            onSendCapture={sendCapture}
            onSendAllCaptures={sendAllCaptures}
          />
          </aside>
        </div>

        <DirectorTimeline />
      </div>
    </div>
  );
}
