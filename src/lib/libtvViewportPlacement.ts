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

export interface LibTVHostCenterPlacement {
  clientCenter: LibTVPoint;
  flowCenter: LibTVPoint;
  nodePosition: LibTVPoint;
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
  }
}

if (typeof window !== "undefined") {
  window.__libtv_plan_host_center_placement = planLibTVHostCenterPlacement;
}
