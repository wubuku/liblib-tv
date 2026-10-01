// Batch 611（源站 2026-10-01 实测 probe66）：属性面板顶部有一块
// **sticky 预览缩略图** `section.sticky.top-0.z-20`，里面是
// `div.relative.overflow-hidden.rounded-xl.border` 240×135，盒内是一个
// `<canvas>` —— 裁图确认它是**真 3D 渲染**（能看到机位视角下的角色与
// 地平线），不是示意图。左上角 `pointer-events-none absolute left-3 top-3`
// 的 `FOV 50°` 角标，右下角 24×24 的放大钮。
//
// 这里不复刻成 2D 示意图 —— 那样会得到一个「看起来能用、其实在撒谎」的
// 控件。改为在**已有的那个 WebGL 上下文**里做离屏渲染：把同一份 scene 用
// 一台按所选机位摆放的临时 PerspectiveCamera 渲进 WebGLRenderTarget，
// readRenderTargetPixels 回读后 putImageData 到面板里那块 2D canvas。
// 不新增 WebGL context，导出路径用的仍是原来那块主 canvas。

import {
  LinearFilter,
  PerspectiveCamera,
  RGBAFormat,
  SRGBColorSpace,
  WebGLRenderTarget,
  type Scene,
  type WebGLRenderer,
} from "three";

/** 源站实测：预览盒 240×135（16:9），`div [1656,121,240,135]`。 */
export const DIRECTOR_CAMERA_PREVIEW_WIDTH = 240;
export const DIRECTOR_CAMERA_PREVIEW_HEIGHT = 135;

export const DIRECTOR_CAMERA_PREVIEW_ASPECT =
  DIRECTOR_CAMERA_PREVIEW_WIDTH / DIRECTOR_CAMERA_PREVIEW_HEIGHT;

export interface DirectorCameraPreviewPlacement {
  position: readonly [number, number, number];
  fov: number;
  target: readonly [number, number, number];
  useRotation: boolean;
  rotation: readonly [number, number, number];
}

// 面板里那块 2D canvas 通过模块级 sink 交给 Canvas 内的渲染器，
// 免得把 DOM 引用穿过 R3F 的 provider 树。
const sink: { canvas: HTMLCanvasElement | null } = { canvas: null };

export function attachDirectorCameraPreviewCanvas(
  canvas: HTMLCanvasElement | null,
): void {
  sink.canvas = canvas;
}

export function hasDirectorCameraPreviewCanvas(): boolean {
  return sink.canvas !== null;
}

/** 按机位摆放相机；朝向规则与视口 `CameraController` 保持一致。 */
export function composeDirectorCameraPreviewCamera(
  camera: PerspectiveCamera,
  placement: DirectorCameraPreviewPlacement,
): void {
  camera.position.set(
    placement.position[0],
    placement.position[1],
    placement.position[2],
  );
  camera.fov = placement.fov;
  camera.aspect = DIRECTOR_CAMERA_PREVIEW_ASPECT;
  if (placement.useRotation) {
    camera.rotation.set(
      (placement.rotation[0] * Math.PI) / 180,
      (placement.rotation[1] * Math.PI) / 180,
      (placement.rotation[2] * Math.PI) / 180,
    );
  } else {
    camera.lookAt(
      placement.target[0],
      placement.target[1],
      placement.target[2],
    );
  }
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld();
}

let target: WebGLRenderTarget | null = null;
let pixels: Uint8Array | null = null;

function ensureTarget(): WebGLRenderTarget {
  if (target) return target;
  // 1:1 回读，任何缩放/滤波都会糊掉边缘。
  target = new WebGLRenderTarget(
    DIRECTOR_CAMERA_PREVIEW_WIDTH,
    DIRECTOR_CAMERA_PREVIEW_HEIGHT,
    {
      minFilter: LinearFilter,
      magFilter: LinearFilter,
      format: RGBAFormat,
      depthBuffer: true,
      stencilBuffer: false,
    },
  );
  // 主画布输出 sRGB，RT 用同一色彩空间，回读的字节才和主视口一致，
  // 否则缩略图会明显偏亮/偏暗。
  target.texture.colorSpace = SRGBColorSpace;
  target.texture.generateMipmaps = false;
  return target;
}

/**
 * 把 scene 用 previewCamera 渲进离屏 RT 并回读到面板的 2D canvas。
 * 没有挂载 sink 时返回 false，调用方据此整段跳过。
 */
export function renderDirectorCameraPreview(
  gl: WebGLRenderer,
  scene: Scene,
  previewCamera: PerspectiveCamera,
): boolean {
  const canvas = sink.canvas;
  if (!canvas) return false;
  const rt = ensureTarget();
  const size = DIRECTOR_CAMERA_PREVIEW_WIDTH * DIRECTOR_CAMERA_PREVIEW_HEIGHT * 4;
  if (!pixels || pixels.length !== size) {
    pixels = new Uint8Array(size);
  }

  const previousTarget = gl.getRenderTarget();
  gl.setRenderTarget(rt);
  gl.render(scene, previewCamera);
  gl.readRenderTargetPixels(
    rt,
    0,
    0,
    DIRECTOR_CAMERA_PREVIEW_WIDTH,
    DIRECTOR_CAMERA_PREVIEW_HEIGHT,
    pixels,
  );
  gl.setRenderTarget(previousTarget);

  // WebGL 原点在左下、ImageData 在左上，逐行翻转。
  const context = canvas.getContext("2d");
  if (!context) return false;
  const image = context.createImageData(
    DIRECTOR_CAMERA_PREVIEW_WIDTH,
    DIRECTOR_CAMERA_PREVIEW_HEIGHT,
  );
  const rowBytes = DIRECTOR_CAMERA_PREVIEW_WIDTH * 4;
  for (let row = 0; row < DIRECTOR_CAMERA_PREVIEW_HEIGHT; row += 1) {
    const from = (DIRECTOR_CAMERA_PREVIEW_HEIGHT - 1 - row) * rowBytes;
    image.data.set(pixels.subarray(from, from + rowBytes), row * rowBytes);
  }
  context.putImageData(image, 0, 0);
  return true;
}

/** 卸载时释放 RT。 */
export function disposeDirectorCameraPreview(): void {
  target?.dispose();
  target = null;
  pixels = null;
}
