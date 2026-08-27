import type {
  DirectorAspectRatio,
} from "@/store/directorStore";
import type {
  DirectorAsyncOperationDescriptorV1,
} from "@/lib/directorAsyncAuthority";
import type {
  DirectorFrameRect,
} from "@/components/director/directorViewportMath";

export interface DirectorVideoExportRequest {
  id: number;
  durationSeconds: number;
  aspectRatio: DirectorAspectRatio;
  authority: DirectorAsyncOperationDescriptorV1;
}

export interface DirectorVideoExportResult {
  exportId: string;
  authority: DirectorAsyncOperationDescriptorV1;
  videoUrl: string;
  posterDataUrl: string;
  aspectRatio: DirectorAspectRatio;
  width: number;
  height: number;
  durationSeconds: number;
  mimeType: string;
  sizeBytes: number;
  createdAt: string;
}

export type DirectorVideoExportErrorCode =
  | "browser-unsupported"
  | "canvas-record-unsupported"
  | "empty-frame"
  | "recording-failed"
  | "empty-video";

const exportErrorMessages: Record<DirectorVideoExportErrorCode, string> = {
  "browser-unsupported": "当前浏览器不支持导出动画视频",
  "canvas-record-unsupported": "当前浏览器无法录制画布视频",
  "empty-frame": "导出视频画面为空",
  "recording-failed": "动画视频录制失败",
  "empty-video": "导出视频为空",
};

export class DirectorVideoExportError extends Error {
  readonly code: DirectorVideoExportErrorCode;
  readonly userMessage: string;

  constructor(code: DirectorVideoExportErrorCode, cause?: unknown) {
    super(exportErrorMessages[code], { cause });
    this.name = "DirectorVideoExportError";
    this.code = code;
    this.userMessage = exportErrorMessages[code];
  }
}

const outputDimensions: Record<
  DirectorAspectRatio,
  { width: number; height: number }
> = {
  "16:9": { width: 960, height: 540 },
  "9:16": { width: 540, height: 960 },
  "1:1": { width: 720, height: 720 },
};

const mimeCandidates = [
  "video/webm;codecs=vp9",
  "video/webm;codecs=vp8",
  "video/webm",
] as const;

function nextAnimationFrame(): Promise<void> {
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => resolve());
  });
}

function getSupportedMimeType(): string | null {
  if (typeof MediaRecorder === "undefined") return null;
  return (
    mimeCandidates.find((candidate) =>
      MediaRecorder.isTypeSupported(candidate),
    ) ?? null
  );
}

function drawCroppedFrame(
  source: HTMLCanvasElement,
  output: HTMLCanvasElement,
  context: CanvasRenderingContext2D,
  frameRect: DirectorFrameRect,
) {
  const cssWidth = Math.max(source.clientWidth, 1);
  const cssHeight = Math.max(source.clientHeight, 1);
  const scaleX = source.width / cssWidth;
  const scaleY = source.height / cssHeight;
  const sourceX = Math.max(0, Math.round(frameRect.left * scaleX));
  const sourceY = Math.max(0, Math.round(frameRect.top * scaleY));
  const sourceWidth = Math.max(
    1,
    Math.min(
      source.width - sourceX,
      Math.round(frameRect.width * scaleX),
    ),
  );
  const sourceHeight = Math.max(
    1,
    Math.min(
      source.height - sourceY,
      Math.round(frameRect.height * scaleY),
    ),
  );

  context.drawImage(
    source,
    sourceX,
    sourceY,
    sourceWidth,
    sourceHeight,
    0,
    0,
    output.width,
    output.height,
  );
}

function hasVisiblePixels(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
): boolean {
  const pixels = context.getImageData(0, 0, width, height).data;
  for (let index = 0; index < pixels.length; index += 64) {
    if (
      pixels[index + 3] > 0 &&
      pixels[index] + pixels[index + 1] + pixels[index + 2] > 0
    ) {
      return true;
    }
  }
  return false;
}

export async function recordDirectorCanvasVideo({
  sourceCanvas,
  frameRect,
  request,
  timelineDuration,
  onTimelineTime,
  onProgress,
}: {
  sourceCanvas: HTMLCanvasElement;
  frameRect: DirectorFrameRect;
  request: DirectorVideoExportRequest;
  timelineDuration: number;
  onTimelineTime: (time: number) => void;
  onProgress: (progress: number) => void;
}): Promise<DirectorVideoExportResult> {
  if (typeof MediaRecorder === "undefined") {
    throw new DirectorVideoExportError("browser-unsupported");
  }

  const output = document.createElement("canvas");
  if (typeof output.captureStream !== "function") {
    throw new DirectorVideoExportError("canvas-record-unsupported");
  }

  const dimensions = outputDimensions[request.aspectRatio];
  output.width = dimensions.width;
  output.height = dimensions.height;
  const context = output.getContext("2d", {
    alpha: false,
    desynchronized: true,
  });
  if (!context) {
    throw new DirectorVideoExportError("canvas-record-unsupported");
  }

  onTimelineTime(0);
  await nextAnimationFrame();
  await nextAnimationFrame();
  drawCroppedFrame(sourceCanvas, output, context, frameRect);
  if (!hasVisiblePixels(context, output.width, output.height)) {
    throw new DirectorVideoExportError("empty-frame");
  }
  const posterDataUrl = output.toDataURL("image/png");
  const mimeType = getSupportedMimeType();
  if (!mimeType) {
    throw new DirectorVideoExportError("browser-unsupported");
  }

  const stream = output.captureStream(30);
  const chunks: Blob[] = [];
  let recorderError: Error | null = null;
  let resolveStopped: (() => void) | null = null;
  const stopped = new Promise<void>((resolve) => {
    resolveStopped = resolve;
  });
  let recorder: MediaRecorder;

  try {
    recorder = new MediaRecorder(stream, {
      mimeType,
      videoBitsPerSecond: 4_000_000,
    });
  } catch (error) {
    stream.getTracks().forEach((track) => track.stop());
    throw new DirectorVideoExportError("recording-failed", error);
  }

  recorder.addEventListener("dataavailable", (event) => {
    if (event.data.size > 0) chunks.push(event.data);
  });
  recorder.addEventListener("error", () => {
    recorderError = new Error("MediaRecorder emitted an error");
  });
  recorder.addEventListener("stop", () => resolveStopped?.(), { once: true });

  try {
    recorder.start(200);
    const startedAt = performance.now();
    const durationMilliseconds = request.durationSeconds * 1000;

    while (performance.now() - startedAt < durationMilliseconds) {
      if (recorderError) throw recorderError;
      const elapsed = performance.now() - startedAt;
      const progress = Math.min(elapsed / durationMilliseconds, 1);
      onTimelineTime(progress * timelineDuration);
      await nextAnimationFrame();
      drawCroppedFrame(sourceCanvas, output, context, frameRect);
      onProgress(progress);
    }

    onTimelineTime(timelineDuration);
    await nextAnimationFrame();
    await nextAnimationFrame();
    drawCroppedFrame(sourceCanvas, output, context, frameRect);
    onProgress(1);
    recorder.requestData();
    await new Promise((resolve) => window.setTimeout(resolve, 80));
    recorder.stop();
    await stopped;
  } catch (error) {
    if (recorder.state !== "inactive") recorder.stop();
    throw new DirectorVideoExportError("recording-failed", error);
  } finally {
    stream.getTracks().forEach((track) => track.stop());
  }

  if (recorderError) {
    throw new DirectorVideoExportError("recording-failed", recorderError);
  }
  const video = new Blob(chunks, { type: mimeType });
  if (video.size === 0) {
    throw new DirectorVideoExportError("empty-video");
  }

  const createdAt = new Date().toISOString();
  return {
    exportId: `director-animation-export-${Date.now()}`,
    authority: request.authority,
    videoUrl: URL.createObjectURL(video),
    posterDataUrl,
    aspectRatio: request.aspectRatio,
    width: output.width,
    height: output.height,
    durationSeconds: request.durationSeconds,
    mimeType,
    sizeBytes: video.size,
    createdAt,
  };
}
