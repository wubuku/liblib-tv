import type {
  DirectorProjectDocumentV1,
  DirectorTimelineTrackDocumentV1,
} from "@/lib/directorProjectDocument";
import type { DirectorCommandReason } from "@/lib/directorCommandKernel";

export type DirectorGroupDeletePolicy = "UNGROUP" | "CASCADE";
export type DirectorResourceDeletePolicy = "BLOCK" | "CASCADE";

export type DirectorDeleteCommand =
  | { kind: "DELETE_OBJECT"; objectId: string }
  | { kind: "DELETE_OBJECTS"; objectIds: string[] }
  | {
      kind: "DELETE_GROUP";
      groupId: string;
      memberPolicy: DirectorGroupDeletePolicy;
    }
  | { kind: "DELETE_TRACK"; trackId: string }
  | { kind: "DELETE_MOTION_PATH"; pathId: string }
  | { kind: "DELETE_CAPTURE"; captureId: string }
  | { kind: "DELETE_CAPTURES"; captureIds: string[] }
  | {
      kind: "DELETE_RESOURCE";
      resourceId: string;
      instancePolicy: DirectorResourceDeletePolicy;
    };

export type DirectorDeletePlanDisposition = "READY" | "NOOP" | "REJECTED";

export interface DirectorDeleteClosure {
  deletedObjectIds: string[];
  deletedGroupIds: string[];
  deletedTrackIds: string[];
  deletedPathIds: string[];
  deletedShotIds: string[];
  deletedCaptureIds: string[];
  deletedResourceIds: string[];
  repairedCameraIds: string[];
}

export interface DirectorDeletePlan {
  disposition: DirectorDeletePlanDisposition;
  reason: DirectorCommandReason | null;
  commandKind: string;
  document: DirectorProjectDocumentV1;
  closure: DirectorDeleteClosure;
}

type DirectorDocumentNormalizer = (
  document: DirectorProjectDocumentV1,
) => DirectorProjectDocumentV1;

interface DirectorDeleteWorkingState {
  document: DirectorProjectDocumentV1;
  deletedObjectIds: Set<string>;
  deletedGroupIds: Set<string>;
  deletedTrackIds: Set<string>;
  deletedPathIds: Set<string>;
  deletedShotIds: Set<string>;
  deletedCaptureIds: Set<string>;
  deletedResourceIds: Set<string>;
  repairedCameraIds: Set<string>;
  candidateResourceIds: Set<string>;
}

function emptyClosure(): DirectorDeleteClosure {
  return {
    deletedObjectIds: [],
    deletedGroupIds: [],
    deletedTrackIds: [],
    deletedPathIds: [],
    deletedShotIds: [],
    deletedCaptureIds: [],
    deletedResourceIds: [],
    repairedCameraIds: [],
  };
}

function stableValues(values: Set<string>): string[] {
  return [...values].sort();
}

function closureFromWorking(
  working: DirectorDeleteWorkingState,
): DirectorDeleteClosure {
  return {
    deletedObjectIds: stableValues(working.deletedObjectIds),
    deletedGroupIds: stableValues(working.deletedGroupIds),
    deletedTrackIds: stableValues(working.deletedTrackIds),
    deletedPathIds: stableValues(working.deletedPathIds),
    deletedShotIds: stableValues(working.deletedShotIds),
    deletedCaptureIds: stableValues(working.deletedCaptureIds),
    deletedResourceIds: stableValues(working.deletedResourceIds),
    repairedCameraIds: stableValues(working.repairedCameraIds),
  };
}

function commandKind(command: DirectorDeleteCommand): string {
  return command.kind;
}

function rejectedPlan(
  document: DirectorProjectDocumentV1,
  command: DirectorDeleteCommand,
  reason: DirectorCommandReason,
): DirectorDeletePlan {
  return {
    disposition: "REJECTED",
    reason,
    commandKind: commandKind(command),
    document,
    closure: emptyClosure(),
  };
}

function noopPlan(
  document: DirectorProjectDocumentV1,
  command: DirectorDeleteCommand,
): DirectorDeletePlan {
  return {
    disposition: "NOOP",
    reason: "DIRECTOR_COMMAND_NO_CHANGE",
    commandKind: commandKind(command),
    document,
    closure: emptyClosure(),
  };
}

function createWorkingState(
  document: DirectorProjectDocumentV1,
): DirectorDeleteWorkingState {
  return {
    document,
    deletedObjectIds: new Set<string>(),
    deletedGroupIds: new Set<string>(),
    deletedTrackIds: new Set<string>(),
    deletedPathIds: new Set<string>(),
    deletedShotIds: new Set<string>(),
    deletedCaptureIds: new Set<string>(),
    deletedResourceIds: new Set<string>(),
    repairedCameraIds: new Set<string>(),
    candidateResourceIds: new Set<string>(),
  };
}

function collectTrackAndPathClosure(
  working: DirectorDeleteWorkingState,
  shouldDeleteTrack: (track: DirectorTimelineTrackDocumentV1) => boolean,
): void {
  working.document.timeline.tracks.forEach((track) => {
    if (!shouldDeleteTrack(track)) return;
    working.deletedTrackIds.add(track.id);
    if (track.motionPathId) working.deletedPathIds.add(track.motionPathId);
  });
}

function applyTrackAndPathClosure(
  working: DirectorDeleteWorkingState,
): void {
  const tracks = working.document.timeline.tracks
    .filter((track) => !working.deletedTrackIds.has(track.id))
    .map((track): DirectorTimelineTrackDocumentV1 => {
      if (
        track.motionPathId &&
        working.deletedPathIds.has(track.motionPathId)
      ) {
        return { ...track, motionPathId: null };
      }
      if (track.kind !== "group") return track;
      const group = working.document.groups.find(
        (candidate) => candidate.id === track.groupId,
      );
      if (!group) return track;
      const memberOffsets = Object.fromEntries(
        group.characterIds
          .filter((memberId) => track.memberOffsets[memberId])
          .map((memberId) => [
            memberId,
            [...track.memberOffsets[memberId]] as [number, number, number],
          ]),
      );
      return { ...track, memberOffsets };
    });
  const motionPaths = working.document.timeline.motionPaths.filter(
    (path) => !working.deletedPathIds.has(path.id),
  );
  working.document = {
    ...working.document,
    timeline: {
      ...working.document.timeline,
      tracks,
      motionPaths,
    },
  };
}

function referencedResourceIds(
  document: DirectorProjectDocumentV1,
): Set<string> {
  const referenced = new Set<string>();
  document.objects.forEach((object) => {
    if (object.assetRefId) referenced.add(object.assetRefId);
  });
  document.captureDescriptors.forEach((capture) => {
    if (capture.resourceRefId) referenced.add(capture.resourceRefId);
  });
  return referenced;
}

function removeUnreferencedCandidateResources(
  working: DirectorDeleteWorkingState,
): void {
  const referenced = referencedResourceIds(working.document);
  working.candidateResourceIds.forEach((resourceId) => {
    if (!referenced.has(resourceId)) {
      working.deletedResourceIds.add(resourceId);
    }
  });
  if (working.deletedResourceIds.size === 0) return;
  working.document = {
    ...working.document,
    resourceRefs: working.document.resourceRefs.filter(
      (resource) => !working.deletedResourceIds.has(resource.id),
    ),
  };
}

function applyObjectClosure(
  working: DirectorDeleteWorkingState,
  requestedObjectIds: Set<string>,
): DirectorCommandReason | null {
  if (requestedObjectIds.size === 0) return null;
  const objectById = new Map(
    working.document.objects.map((object) => [object.id, object]),
  );
  for (const objectId of requestedObjectIds) {
    const object = objectById.get(objectId);
    if (!object) return "DIRECTOR_TARGET_MISSING";
    if (object.locked) return "DIRECTOR_TARGET_LOCKED";
  }

  const survivingObjects = working.document.objects.filter(
    (object) => !requestedObjectIds.has(object.id),
  );
  if (survivingObjects.length === 0) return "DIRECTOR_DELETE_BLOCKED";

  const deletedCameraIds = new Set(
    working.document.objects
      .filter(
        (object) =>
          requestedObjectIds.has(object.id) && object.kind === "camera",
      )
      .map((object) => object.id),
  );
  const survivingCameras = survivingObjects.filter(
    (object) => object.kind === "camera",
  );
  if (deletedCameraIds.size > 0 && survivingCameras.length === 0) {
    return "DIRECTOR_LAST_CAMERA_REQUIRED";
  }

  requestedObjectIds.forEach((objectId) =>
    working.deletedObjectIds.add(objectId),
  );
  working.document.objects.forEach((object) => {
    if (
      requestedObjectIds.has(object.id) &&
      object.assetRefId
    ) {
      working.candidateResourceIds.add(object.assetRefId);
    }
  });

  const groups = working.document.groups.flatMap((group) => {
    const characterIds = group.characterIds.filter(
      (characterId) => !requestedObjectIds.has(characterId),
    );
    if (characterIds.length === 0) {
      working.deletedGroupIds.add(group.id);
      return [];
    }
    return characterIds.length === group.characterIds.length
      ? [group]
      : [{ ...group, characterIds }];
  });
  working.document = {
    ...working.document,
    objects: survivingObjects.map((object) => {
      if (!object.camera) return object;
      const lookAtDeleted =
        object.camera.lookAtObjectId !== null &&
        requestedObjectIds.has(object.camera.lookAtObjectId);
      const followDeleted =
        object.camera.followTargetId !== null &&
        requestedObjectIds.has(object.camera.followTargetId);
      if (!lookAtDeleted && !followDeleted) return object;
      working.repairedCameraIds.add(object.id);
      return {
        ...object,
        camera: {
          ...object.camera,
          lookAtMode: lookAtDeleted ? "coordinate" : object.camera.lookAtMode,
          lookAtObjectId: lookAtDeleted
            ? null
            : object.camera.lookAtObjectId,
          followTargetId: followDeleted
            ? null
            : object.camera.followTargetId,
        },
      };
    }),
    groups,
    shots: working.document.shots.filter((shot) => {
      if (!deletedCameraIds.has(shot.cameraId)) return true;
      working.deletedShotIds.add(shot.id);
      return false;
    }),
    activeCameraId: deletedCameraIds.has(working.document.activeCameraId)
      ? survivingCameras[0].id
      : working.document.activeCameraId,
    captureDescriptors: working.document.captureDescriptors.map((capture) =>
      capture.cameraId && deletedCameraIds.has(capture.cameraId)
        ? { ...capture, cameraId: null, shotId: null }
        : working.deletedShotIds.has(capture.shotId ?? "")
          ? { ...capture, shotId: null }
        : capture,
    ),
  };

  collectTrackAndPathClosure(
    working,
    (track) =>
      working.deletedGroupIds.has(
        track.kind === "group" ? track.groupId : "",
      ) ||
      (track.kind !== "group" && requestedObjectIds.has(track.objectId)),
  );
  working.document.timeline.motionPaths.forEach((path) => {
    if (
      requestedObjectIds.has(path.objectId) ||
      working.deletedGroupIds.has(path.objectId)
    ) {
      working.deletedPathIds.add(path.id);
    }
  });
  applyTrackAndPathClosure(working);
  return null;
}

function applyGroupClosure(
  working: DirectorDeleteWorkingState,
  groupId: string,
  memberPolicy: DirectorGroupDeletePolicy,
): DirectorCommandReason | null {
  const group = working.document.groups.find(
    (candidate) => candidate.id === groupId,
  );
  if (!group) return "DIRECTOR_TARGET_MISSING";
  if (memberPolicy === "CASCADE") {
    return applyObjectClosure(working, new Set(group.characterIds));
  }

  working.deletedGroupIds.add(group.id);
  working.document = {
    ...working.document,
    groups: working.document.groups.filter(
      (candidate) => candidate.id !== group.id,
    ),
  };
  collectTrackAndPathClosure(
    working,
    (track) => track.kind === "group" && track.groupId === group.id,
  );
  applyTrackAndPathClosure(working);
  return null;
}

function applyTrackClosure(
  working: DirectorDeleteWorkingState,
  trackId: string,
): DirectorCommandReason | null {
  const track = working.document.timeline.tracks.find(
    (candidate) => candidate.id === trackId,
  );
  if (!track) return "DIRECTOR_TARGET_MISSING";
  working.deletedTrackIds.add(track.id);
  if (track.motionPathId) working.deletedPathIds.add(track.motionPathId);
  applyTrackAndPathClosure(working);
  return null;
}

function applyPathClosure(
  working: DirectorDeleteWorkingState,
  pathId: string,
): DirectorCommandReason | null {
  if (
    !working.document.timeline.motionPaths.some(
      (candidate) => candidate.id === pathId,
    )
  ) {
    return "DIRECTOR_TARGET_MISSING";
  }
  working.deletedPathIds.add(pathId);
  applyTrackAndPathClosure(working);
  return null;
}

function applyCaptureClosure(
  working: DirectorDeleteWorkingState,
  captureIds: Set<string>,
): DirectorCommandReason | null {
  if (captureIds.size === 0) return null;
  const existingIds = new Set(
    working.document.captureDescriptors.map((capture) => capture.id),
  );
  for (const captureId of captureIds) {
    if (!existingIds.has(captureId)) return "DIRECTOR_TARGET_MISSING";
  }
  working.document.captureDescriptors.forEach((capture) => {
    if (!captureIds.has(capture.id)) return;
    working.deletedCaptureIds.add(capture.id);
    if (capture.resourceRefId) {
      working.candidateResourceIds.add(capture.resourceRefId);
    }
  });
  working.document = {
    ...working.document,
    captureDescriptors: working.document.captureDescriptors.filter(
      (capture) => !captureIds.has(capture.id),
    ),
    shots: working.document.shots.map((shot) => ({
      ...shot,
      captureIds: shot.captureIds.filter(
        (captureId) => !captureIds.has(captureId),
      ),
    })),
  };
  return null;
}

function applyResourceClosure(
  working: DirectorDeleteWorkingState,
  resourceId: string,
  instancePolicy: DirectorResourceDeletePolicy,
): DirectorCommandReason | null {
  if (
    !working.document.resourceRefs.some(
      (resource) => resource.id === resourceId,
    )
  ) {
    return "DIRECTOR_TARGET_MISSING";
  }
  const objectIds = working.document.objects
    .filter((object) => object.assetRefId === resourceId)
    .map((object) => object.id);
  const captureIds = working.document.captureDescriptors
    .filter((capture) => capture.resourceRefId === resourceId)
    .map((capture) => capture.id);
  if (
    instancePolicy === "BLOCK" &&
    (objectIds.length > 0 || captureIds.length > 0)
  ) {
    return "DIRECTOR_RESOURCE_IN_USE";
  }
  if (instancePolicy === "CASCADE") {
    const objectReason = applyObjectClosure(
      working,
      new Set(objectIds),
    );
    if (objectReason) return objectReason;
    const captureReason = applyCaptureClosure(
      working,
      new Set(captureIds),
    );
    if (captureReason) return captureReason;
  }
  working.deletedResourceIds.add(resourceId);
  working.document = {
    ...working.document,
    resourceRefs: working.document.resourceRefs.filter(
      (resource) => resource.id !== resourceId,
    ),
  };
  return null;
}

export function planDirectorDelete(
  document: DirectorProjectDocumentV1,
  command: DirectorDeleteCommand,
  normalizeDocument: DirectorDocumentNormalizer,
): DirectorDeletePlan {
  const working = createWorkingState(document);
  let reason: DirectorCommandReason | null = null;

  switch (command.kind) {
    case "DELETE_OBJECT":
      reason = applyObjectClosure(working, new Set([command.objectId]));
      break;
    case "DELETE_OBJECTS":
      if (command.objectIds.length === 0) return noopPlan(document, command);
      reason = applyObjectClosure(working, new Set(command.objectIds));
      break;
    case "DELETE_GROUP":
      reason = applyGroupClosure(
        working,
        command.groupId,
        command.memberPolicy,
      );
      break;
    case "DELETE_TRACK":
      reason = applyTrackClosure(working, command.trackId);
      break;
    case "DELETE_MOTION_PATH":
      reason = applyPathClosure(working, command.pathId);
      break;
    case "DELETE_CAPTURE":
      reason = applyCaptureClosure(
        working,
        new Set([command.captureId]),
      );
      break;
    case "DELETE_CAPTURES":
      if (command.captureIds.length === 0) return noopPlan(document, command);
      reason = applyCaptureClosure(
        working,
        new Set(command.captureIds),
      );
      break;
    case "DELETE_RESOURCE":
      reason = applyResourceClosure(
        working,
        command.resourceId,
        command.instancePolicy,
      );
      break;
  }

  if (reason) return rejectedPlan(document, command, reason);
  removeUnreferencedCandidateResources(working);

  try {
    const normalized = normalizeDocument(working.document);
    return {
      disposition: "READY",
      reason: null,
      commandKind: commandKind(command),
      document: normalized,
      closure: closureFromWorking(working),
    };
  } catch {
    return rejectedPlan(
      document,
      command,
      "DIRECTOR_REFERENCE_INVALID",
    );
  }
}
