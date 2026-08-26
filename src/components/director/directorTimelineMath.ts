import type {
  DirectorCameraKeyframeValue,
  DirectorTimelineTrack,
  DirectorTransform,
  DirectorTuple3,
} from "@/store/directorStore";
import { remapDirectorTrackTime } from "@/components/director/directorMotionMath";

export type DirectorTimelineSample =
  | {
      kind: "transform";
      transform: DirectorTransform;
    }
  | {
      kind: "camera";
      transform: DirectorTransform;
      target: DirectorTuple3;
      fov: number;
    };

function interpolateNumber(from: number, to: number, progress: number): number {
  return from + (to - from) * progress;
}

function interpolateTuple(
  from: DirectorTuple3,
  to: DirectorTuple3,
  progress: number,
): DirectorTuple3 {
  return [
    interpolateNumber(from[0], to[0], progress),
    interpolateNumber(from[1], to[1], progress),
    interpolateNumber(from[2], to[2], progress),
  ];
}

function interpolateTransform(
  from: DirectorTransform,
  to: DirectorTransform,
  progress: number,
): DirectorTransform {
  return {
    position: interpolateTuple(from.position, to.position, progress),
    rotation: interpolateTuple(from.rotation, to.rotation, progress),
    scale: interpolateTuple(from.scale, to.scale, progress),
  };
}

function interpolateCamera(
  from: DirectorCameraKeyframeValue,
  to: DirectorCameraKeyframeValue,
  progress: number,
): DirectorCameraKeyframeValue {
  return {
    transform: interpolateTransform(from.transform, to.transform, progress),
    target: interpolateTuple(from.target, to.target, progress),
    fov: interpolateNumber(from.fov, to.fov, progress),
  };
}

export function clampDirectorTimelineTime(
  time: number,
  duration: number,
): number {
  if (!Number.isFinite(time)) return 0;
  return Math.min(Math.max(time, 0), Math.max(duration, 0));
}

export function sampleDirectorTimelineTrack(
  track: DirectorTimelineTrack,
  time: number,
): DirectorTimelineSample | null {
  const sampledTime = remapDirectorTrackTime(track, time);
  if (track.kind === "camera") {
    const keyframes = track.keyframes;
    if (keyframes.length === 0) return null;
    const first = keyframes[0];
    const last = keyframes[keyframes.length - 1];
    if (sampledTime <= first.time) {
      return {
        kind: "camera",
        transform: first.value.transform,
        target: first.value.target,
        fov: first.value.fov,
      };
    }
    if (sampledTime >= last.time) {
      return {
        kind: "camera",
        transform: last.value.transform,
        target: last.value.target,
        fov: last.value.fov,
      };
    }
    const nextIndex = keyframes.findIndex(
      (keyframe) => keyframe.time >= sampledTime,
    );
    const previous = keyframes[Math.max(0, nextIndex - 1)];
    const next = keyframes[nextIndex];
    const span = Math.max(next.time - previous.time, Number.EPSILON);
    const progress = (sampledTime - previous.time) / span;
    const value = interpolateCamera(previous.value, next.value, progress);
    return {
      kind: "camera",
      transform: value.transform,
      target: value.target,
      fov: value.fov,
    };
  }

  const keyframes = track.keyframes;
  if (keyframes.length === 0) return null;
  const first = keyframes[0];
  const last = keyframes[keyframes.length - 1];
  if (sampledTime <= first.time) {
    return { kind: "transform", transform: first.value };
  }
  if (sampledTime >= last.time) {
    return { kind: "transform", transform: last.value };
  }
  const nextIndex = keyframes.findIndex(
    (keyframe) => keyframe.time >= sampledTime,
  );
  const previous = keyframes[Math.max(0, nextIndex - 1)];
  const next = keyframes[nextIndex];
  const span = Math.max(next.time - previous.time, Number.EPSILON);
  const progress = (sampledTime - previous.time) / span;
  return {
    kind: "transform",
    transform: interpolateTransform(previous.value, next.value, progress),
  };
}
