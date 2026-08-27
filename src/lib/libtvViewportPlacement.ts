export interface LibTVPoint {
  x: number;
  y: number;
}

export interface LibTVDimensions {
  width: number;
  height: number;
}

export interface LibTVHostRect extends LibTVDimensions {
  left: number;
  top: number;
}

export interface LibTVViewport extends LibTVPoint {
  zoom: number;
}

export interface LibTVHostCenterPlacement {
  clientCenter: LibTVPoint;
  flowCenter: LibTVPoint;
  nodePosition: LibTVPoint;
}

export interface LibTVHostResizeCenterPlan {
  oldClientCenter: LibTVPoint;
  newClientCenter: LibTVPoint;
  flowAnchor: LibTVPoint;
  targetViewport: LibTVViewport;
}

function isFinitePoint(point: LibTVPoint): boolean {
  return Number.isFinite(point.x) && Number.isFinite(point.y);
}

function isValidDimensions(dimensions: LibTVDimensions): boolean {
  return (
    Number.isFinite(dimensions.width) &&
    Number.isFinite(dimensions.height) &&
    dimensions.width > 0 &&
    dimensions.height > 0
  );
}

export function getLibTVHostCenterClientPoint(
  hostRect: LibTVHostRect,
): LibTVPoint | null {
  if (
    !Number.isFinite(hostRect.left) ||
    !Number.isFinite(hostRect.top) ||
    !isValidDimensions(hostRect)
  ) {
    return null;
  }

  return {
    x: hostRect.left + hostRect.width / 2,
    y: hostRect.top + hostRect.height / 2,
  };
}

export function getLibTVNodePositionForFlowCenter(
  flowCenter: LibTVPoint,
  dimensions: LibTVDimensions,
): LibTVPoint | null {
  if (!isFinitePoint(flowCenter) || !isValidDimensions(dimensions)) return null;

  return {
    x: flowCenter.x - dimensions.width / 2,
    y: flowCenter.y - dimensions.height / 2,
  };
}

export function getLibTVViewportForFlowAtHostCenter(
  flowAnchor: LibTVPoint,
  hostRect: LibTVHostRect,
  zoom: number,
): LibTVViewport | null {
  const clientCenter = getLibTVHostCenterClientPoint(hostRect);
  if (!clientCenter || !isFinitePoint(flowAnchor) || !Number.isFinite(zoom) || zoom <= 0) {
    return null;
  }

  return {
    x: hostRect.width / 2 - flowAnchor.x * zoom,
    y: hostRect.height / 2 - flowAnchor.y * zoom,
    zoom,
  };
}

export function planLibTVHostResizeCenterPreservation(
  oldHostRect: LibTVHostRect,
  oldViewport: LibTVViewport,
  newHostRect: LibTVHostRect,
): LibTVHostResizeCenterPlan | null {
  const oldClientCenter = getLibTVHostCenterClientPoint(oldHostRect);
  const newClientCenter = getLibTVHostCenterClientPoint(newHostRect);
  if (
    !oldClientCenter ||
    !newClientCenter ||
    !isFinitePoint(oldViewport) ||
    !Number.isFinite(oldViewport.zoom) ||
    oldViewport.zoom <= 0
  ) {
    return null;
  }

  const flowAnchor = {
    x: (oldHostRect.width / 2 - oldViewport.x) / oldViewport.zoom,
    y: (oldHostRect.height / 2 - oldViewport.y) / oldViewport.zoom,
  };
  const targetViewport = getLibTVViewportForFlowAtHostCenter(
    flowAnchor,
    newHostRect,
    oldViewport.zoom,
  );
  if (!targetViewport) return null;

  return {
    oldClientCenter,
    newClientCenter,
    flowAnchor,
    targetViewport,
  };
}

export function planLibTVHostCenterPlacement(
  hostRect: LibTVHostRect,
  flowCenter: LibTVPoint,
  dimensions: LibTVDimensions,
): LibTVHostCenterPlacement | null {
  const clientCenter = getLibTVHostCenterClientPoint(hostRect);
  const nodePosition = getLibTVNodePositionForFlowCenter(
    flowCenter,
    dimensions,
  );
  if (!clientCenter || !nodePosition) return null;

  return {
    clientCenter,
    flowCenter: { ...flowCenter },
    nodePosition,
  };
}

declare global {
  interface Window {
    __libtv_plan_host_center_placement: typeof planLibTVHostCenterPlacement;
    __libtv_plan_host_resize_center_preservation: typeof planLibTVHostResizeCenterPreservation;
  }
}

if (typeof window !== "undefined") {
  window.__libtv_plan_host_center_placement = planLibTVHostCenterPlacement;
  window.__libtv_plan_host_resize_center_preservation =
    planLibTVHostResizeCenterPreservation;
}
