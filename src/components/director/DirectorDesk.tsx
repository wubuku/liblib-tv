"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  ArrowLeft,
  Check,
  FileVideo2,
  ImageIcon,
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
import { useCanvasStore } from "@/store/canvasStore";
import {
  useDirectorStore,
  type DirectorAspectRatio,
  type DirectorCapture,
  type DirectorViewMode,
} from "@/store/directorStore";

type MobilePanel = "tree" | "inspector" | null;

export default function DirectorDesk({
  sourceNodeId,
  onClose,
}: {
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
  const openSession = useDirectorStore((state) => state.openSession);
  const setViewMode = useDirectorStore((state) => state.setViewMode);
  const setAspectRatio = useDirectorStore((state) => state.setAspectRatio);
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
  const exportRequestId = useRef(0);
  const exporting = exportStatus === "exporting";
  const phoneVcamRecording = phoneVcamStatus === "recording";
  const workspaceBusy = exporting || phoneVcamRecording;
  const activeCapture = useMemo(
    () => captures.find((capture) => capture.id === activeCaptureId) ?? null,
    [activeCaptureId, captures],
  );

  useEffect(() => {
    openSession(sourceNodeId);
  }, [openSession, sourceNodeId]);

  const closeWorkspace = useCallback(() => {
    if (workspaceBusy) return;
    selectNode(exportedNodeId ?? sourceNodeId);
    onClose();
  }, [exportedNodeId, onClose, selectNode, sourceNodeId, workspaceBusy]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      if (document.querySelector("[data-director-capture-viewer]")) return;
      if (workspaceBusy) return;
      if (mobilePanel) {
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
  }, [closeWorkspace, exportPanelOpen, mobilePanel, workspaceBusy]);

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
    setVideoExportRequest({
      id: exportRequestId.current,
      durationSeconds,
      aspectRatio: exportAspectRatio,
    });
  };

  const completeVideoExport = useCallback(
    (result: DirectorVideoExportResult) => {
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
        URL.revokeObjectURL(result.videoUrl);
        setExportError("视频已生成，但画布节点创建失败");
        setExportStatus("error");
        return;
      }
      setExportProgress(1);
      setExportError(null);
      setExportedNodeId(nodeId);
      setExportStatus("success");
    },
    [createDirectorAnimationExport, sourceNodeId],
  );

  const failVideoExport = useCallback((message: string) => {
    setExportError(message);
    setExportStatus("error");
  }, []);

  return (
    <div
      data-director-workspace
      data-director-source-node-id={sourceNodeId}
      className="fixed inset-0 z-[100] flex h-dvh w-screen flex-col overflow-hidden bg-[#151515] text-[#ededed]"
    >
      <header className="relative z-40 grid h-12 shrink-0 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center border-b border-white/[0.07] bg-[#181818] px-2">
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
          {mobilePanel ? (
            <button
              type="button"
              aria-label="关闭移动端面板"
              onClick={() => setMobilePanel(null)}
              className="absolute inset-0 z-20 hidden bg-black/45 max-[899px]:block"
            />
          ) : null}

          <aside
            aria-label="场景对象"
            data-director-mobile-panel-state={mobilePanel === "tree" ? "open" : "closed"}
            className={cn(
              "absolute inset-y-0 left-0 z-30 w-[220px] border-r border-white/[0.07] transition-transform duration-200",
              mobilePanel === "tree"
                ? "max-[899px]:translate-x-0"
                : "max-[899px]:-translate-x-full",
            )}
          >
            <DirectorObjectTree />
          </aside>

          <main className="absolute inset-y-0 left-[220px] right-[288px] min-w-0 max-[899px]:inset-x-0">
            <DirectorViewport
              onOpenTree={() => setMobilePanel("tree")}
              onOpenInspector={() => setMobilePanel("inspector")}
              videoExportRequest={videoExportRequest}
              onVideoExportProgress={setExportProgress}
              onVideoExportCompleted={completeVideoExport}
              onVideoExportFailed={failVideoExport}
            />
          </main>

          <aside
            aria-label="属性"
            data-director-mobile-panel-state={mobilePanel === "inspector" ? "open" : "closed"}
            className={cn(
              "absolute inset-y-0 right-0 z-30 w-72 border-l border-white/[0.07] transition-transform duration-200",
              mobilePanel === "inspector"
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
