import {
  buildDirectorMotionPathPoints,
  buildDirectorMotionPathWorldAnchors,
} from "@/components/director/directorMotionMath";
import type {
  DirectorCharacterGroup,
  DirectorMotionPath,
  DirectorObject,
  DirectorTimelineState,
  DirectorTimelineTrack,
  DirectorTransform,
  DirectorTuple3,
} from "@/store/directorStore";
import type {
  DirectorCharacterRigDocumentV1,
  DirectorProjectDocumentV1,
  DirectorResourceReferenceV1,
  DirectorShotRecordV1,
  DirectorTimelineTrackDocumentV1,
  DirectorTransformDocumentV1,
} from "@/lib/directorProjectDocument";

export interface DirectorProjectRuntimeSnapshotV1 {
  scene: DirectorProjectDocumentV1["scene"];
  objects: DirectorObject[];
  groups: DirectorCharacterGroup[];
  shots: DirectorShotRecordV1[];
  activeCameraId: string;
  aspectRatio: DirectorProjectDocumentV1["outputPreferences"]["aspectRatio"];
  timeline: DirectorTimelineState;
}

function cloneTuple3(value: DirectorTuple3): DirectorTuple3 {
  return [...value];
}

function restoreTransform(
  transform: DirectorTransformDocumentV1,
): DirectorTransform {
  return {
    position: cloneTuple3(transform.position),
    rotation: cloneTuple3(transform.rotation),
    scale: cloneTuple3(transform.scale),
  };
}

function restoreRig(
  rig: DirectorCharacterRigDocumentV1,
): DirectorCharacterRigDocumentV1 {
  return {
    posePresetId: rig.posePresetId,
    controls: { ...rig.controls },
  };
}

function restoreObject(
  object: DirectorProjectDocumentV1["objects"][number],
  resources: Map<string, DirectorResourceReferenceV1>,
): DirectorObject {
  const resource = object.assetRefId
    ? resources.get(object.assetRefId)
    : undefined;
  return {
    id: object.id,
    name: object.name,
    kind: object.kind,
    primitive: object.primitive,
    color: object.color,
    visible: object.visible,
    locked: object.locked,
    transform: restoreTransform(object.transform),
    ...(object.assetRefId ? { libraryAssetId: object.assetRefId } : {}),
    ...(object.libraryCategoryId
      ? { libraryCategoryId: object.libraryCategoryId }
      : {}),
    ...(object.libraryVisual ? { libraryVisual: object.libraryVisual } : {}),
    ...(resource
      ? {
          librarySource:
            resource.source === "local" ? ("local" as const) : ("catalog" as const),
          libraryFileName: resource.label,
        }
      : {}),
    ...(object.characterRig
      ? { characterRig: restoreRig(object.characterRig) }
      : {}),
    ...(object.camera
      ? {
          camera: {
            fov: object.camera.fov,
            target: cloneTuple3(object.camera.target),
            lookAtMode: object.camera.lookAtMode,
            lookAtObjectId: object.camera.lookAtObjectId,
            followTargetId: object.camera.followTargetId,
            followOffset: cloneTuple3(object.camera.followOffset),
            followView: object.camera.followView,
          },
        }
      : {}),
  };
}

function restoreTrack(
  track: DirectorTimelineTrackDocumentV1,
): DirectorTimelineTrack {
  const base = {
    id: track.id,
    objectId: track.objectId,
    label: track.label,
    ...(track.motionPathId ? { motionPathId: track.motionPathId } : {}),
    speedCurve: {
      preset: track.speedCurve.preset,
      control1: [...track.speedCurve.control1] as [number, number],
      control2: [...track.speedCurve.control2] as [number, number],
    },
  };
  if (track.kind === "group") {
    return {
      ...base,
      kind: "group",
      groupId: track.groupId,
      memberOffsets: Object.fromEntries(
        Object.entries(track.memberOffsets).map(([id, value]) => [
          id,
          cloneTuple3(value),
        ]),
      ),
      keyframes: track.keyframes.map((keyframe) => ({
        id: keyframe.id,
        time: keyframe.time,
        value: restoreTransform(keyframe.value),
      })),
    };
  }
  if (track.kind === "camera") {
    return {
      ...base,
      kind: "camera",
      keyframes: track.keyframes.map((keyframe) => ({
        id: keyframe.id,
        time: keyframe.time,
        value: {
          transform: restoreTransform(keyframe.value.transform),
          target: cloneTuple3(keyframe.value.target),
          fov: keyframe.value.fov,
        },
      })),
    };
  }
  if (track.kind === "pose") {
    return {
      ...base,
      kind: "pose",
      keyframes: track.keyframes.map((keyframe) => ({
        id: keyframe.id,
        time: keyframe.time,
        value: restoreRig(keyframe.value),
      })),
    };
  }
  return {
    ...base,
    kind: "transform",
    keyframes: track.keyframes.map((keyframe) => ({
      id: keyframe.id,
      time: keyframe.time,
      value: restoreTransform(keyframe.value),
    })),
  };
}

function restoreMotionPath(
  path: DirectorProjectDocumentV1["timeline"]["motionPaths"][number],
): DirectorMotionPath {
  const initialAnchors = path.initialAnchors.map((anchor) => ({
    id: anchor.id,
    position: cloneTuple3(anchor.position),
    type: anchor.type,
    handleIn: cloneTuple3(anchor.handleIn),
    handleOut: cloneTuple3(anchor.handleOut),
  }));
  const anchors = path.anchors.map((anchor) => ({
    id: anchor.id,
    position: cloneTuple3(anchor.position),
    type: anchor.type,
    handleIn: cloneTuple3(anchor.handleIn),
    handleOut: cloneTuple3(anchor.handleOut),
  }));
  const transform = restoreTransform(path.transform);
  const pivot = cloneTuple3(path.pivot);
  return {
    id: path.id,
    objectId: path.objectId,
    name: path.name,
    preset: path.preset,
    enabled: path.enabled,
    orientToPath: path.orientToPath,
    closed: path.closed,
    pivot,
    transform,
    initialAnchors,
    anchors,
    points: buildDirectorMotionPathPoints(
      buildDirectorMotionPathWorldAnchors(anchors, pivot, transform),
      path.closed,
    ),
  };
}

export function restoreDirectorProjectRuntimeSnapshotV1(
  document: DirectorProjectDocumentV1,
): DirectorProjectRuntimeSnapshotV1 {
  const resources = new Map(
    document.resourceRefs.map((resource) => [resource.id, resource]),
  );
  const tracks = document.timeline.tracks.map(restoreTrack);
  const firstTrack = tracks[0] ?? null;
  return {
    scene: {
      name: document.scene.name,
      backgroundColor: document.scene.backgroundColor,
      groundColor: document.scene.groundColor,
      showGround: document.scene.showGround,
      showGrid: document.scene.showGrid,
    },
    objects: document.objects.map((object) =>
      restoreObject(object, resources),
    ),
    groups: document.groups.map((group) => ({
      id: group.id,
      label: group.label,
      characterIds: [...group.characterIds],
      ...(group.crowd
        ? {
            crowd: {
              rows: group.crowd.rows,
              columns: group.crowd.columns,
              spacing: group.crowd.spacing,
            },
          }
        : {}),
    })),
    shots: document.shots.map((shot) => ({
      id: shot.id,
      name: shot.name,
      cameraId: shot.cameraId,
      startTime: shot.startTime,
      endTime: shot.endTime,
      captureIds: [...shot.captureIds],
    })),
    activeCameraId: document.activeCameraId,
    aspectRatio: document.outputPreferences.aspectRatio,
    timeline: {
      duration: document.timeline.duration,
      currentTime: 0,
      isPlaying: false,
      loop: document.timeline.loop,
      zoom: 1,
      autoKeyframe: document.timeline.autoKeyframe,
      tracks,
      motionPaths: document.timeline.motionPaths.map(restoreMotionPath),
      selectedTrackId: firstTrack?.id ?? null,
      selectedKeyframeId: firstTrack?.keyframes[0]?.id ?? null,
      selectedMotionPathId: firstTrack?.motionPathId ?? null,
      selectedMotionPathAnchorId: null,
      selectedMotionPathHandle: null,
      motionPathDraft: null,
      editorMode: "timeline",
      cameraMotionPreset: {
        application: null,
        error: null,
      },
    },
  };
}
