/**
 * ★★★ Batch 864：**源站那条「机位设置变更」埋点**的**本地等价实现**。
 *
 * ## ★ 为什么要做这件事（★ 这正是 batch 862 登记的 **D17** 的真相）
 *
 * ★ ★ Batch 862 把这条记成了「源站把比例与 `reference_line` **写进机位对象**」
 *   ⟹ ⟹ 本批用**源站逐字 ＋ 源站运行时网络取证**把它**推翻**了：
 *
 *   ① **源站逐字**（chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`）：
 *   ```js
 *   // 右侧面板选比例：
 *   o$ = useCallback(e => { tn(e);
 *     let t = e1 || rL.cameras[0]?.id;
 *     t && n4(t, "aspect_ratio", (0,nZ.R)(e), "right_panel"); }, [e1, rL.cameras, n4])
 *
 *   // 框上那枚「构图参考线」开关：
 *   onToggleCompositionGrid: null !== tr ? () => {
 *     let e = !ti, t = e1 || rL.cameras[0]?.id;
 *     t && n4(t, "reference_line", (0,nZ.p)(e), "right_panel"), to(e); } : void 0
 *
 *   // ★ n4 的定义 —— **它只是发一条埋点**：
 *   n4 = useCallback((e,t,r,n) => {
 *     (0,nZ.S)("libtv.canvas.director.camera.update", {
 *       director_session_id: nb.current, camera_uuid: e,
 *       setting_name: t, setting_value: r, operation_source: n })
 *   }, [])
 *   ```
 *   ⟹ ⟹ `n4` **不改任何状态** ⟹ ⟹ 源站**没有**把这两个字段写进机位对象。
 *
 *   ② **源站运行时实测**（`raw/source-864-camera-write.json`）：
 *   点「16:9」与点那枚「构图参考线」，源站发出的都是
 *   ```
 *   POST https://api2.liblib.art/api/www/log/acceptor/f
 *   {"e":"libtv.canvas.director.camera.update",
 *    "var":{"camera_uuid":"director-main-camera",
 *           "setting_name":"aspect_ratio",  "setting_value":"16:9",
 *           "operation_source":"right_panel", …}}
 *   {"e":"libtv.canvas.director.camera.update",
 *    "var":{"camera_uuid":"director-main-camera",
 *           "setting_name":"reference_line", "setting_value":1,
 *           "operation_source":"right_panel", …}}
 *   ```
 *   ⟹ ⟹ 落点是**埋点接收端点**（`/api/www/log/acceptor/f`）
 *   ⟹ ⟹ 而且**没有任何工程状态写入请求**（只有 `project/heartbeat` 心跳）。
 *
 *   ③ ★ **静态反证**：整个 chunk（1,018,130 字符）里
 *   **`reference_line` 只出现 1 次**（就在上面那条埋点里）
 *   ⟹ ⟹ 它**从来不是**机位对象上被读写的字段。
 *
 * ## ★ ★★ 结论（★ D17 被推翻）
 *
 * ★ 源站的模型是：**取景比例与参考线都是「组件级单值状态」**
 *   （`tr` / `ti`）⟹ ⟹ clone 的全局 `frameAspectRatio` ＋ `showThirds`
 *   **与源站同构** ⟹ ⟹ 「clone 缺了机位级写入」这个**差距不存在**。
 *
 * ★ 源站与 clone 在这一处**真正的差别**只有一条：
 *   源站会把这次改动**上报到后端** ⟹ ⟹ clone **不触网**（原型不碰真实接口）
 *   ⟹ ⟹ 本模块提供**本地等价记录**：事件名与属性**逐字同构**，
 *   但**只落在内存里**（`directorStore.telemetryLog`）
 *   ⟹ ⟹ 这样「改了比例 / 切了参考线 ⟹ 记了哪台机位的哪个设置」在原型里**可观察、可测试**。
 */

/** ★ 源站逐字：事件名。 */
export const DIRECTOR_TELEMETRY_EVENT_CAMERA_UPDATE =
  "libtv.canvas.director.camera.update";

/** ★ 源站逐字：本批用到的那两个 `setting_name`。 */
export type DirectorTelemetrySettingName = "aspect_ratio" | "reference_line";

/**
 * ★ 源站逐字的事件形状：`{e, var:{camera_uuid, setting_name, setting_value, operation_source}}`。
 *
 * ★ ★ `var` 里**只有**源站那四个键 ⟹ ⟹ 不许加 clone 自己的字段
 *   （clone 自己的信息另放在 store 的条目里，不混进 `var`）。
 */
export interface DirectorTelemetryCameraUpdateEvent {
  e: typeof DIRECTOR_TELEMETRY_EVENT_CAMERA_UPDATE;
  var: {
    camera_uuid: string;
    setting_name: DirectorTelemetrySettingName;
    setting_value: string | number | null;
    operation_source: "right_panel";
  };
}

/** ★ 源站逐字：`operation_source` 在「右侧面板选比例」与「框上开关」两处**都是** `"right_panel"`。 */
export const DIRECTOR_TELEMETRY_OPERATION_SOURCE = "right_panel" as const;

/** ★ 组一条与源站**逐字同构**的事件。 */
export function buildDirectorCameraUpdateEvent(input: {
  cameraId: string;
  settingName: DirectorTelemetrySettingName;
  settingValue: string | number | null;
}): DirectorTelemetryCameraUpdateEvent {
  return {
    e: DIRECTOR_TELEMETRY_EVENT_CAMERA_UPDATE,
    var: {
      camera_uuid: input.cameraId,
      setting_name: input.settingName,
      setting_value: input.settingValue,
      operation_source: DIRECTOR_TELEMETRY_OPERATION_SOURCE,
    },
  };
}

/**
 * ★ 源站逐字：`let t = e1 || rL.cameras[0]?.id`
 * ⟹ ⟹ **选中机位**优先 ⟹ ⟹ 否则**第一个机位**。
 *
 * ★ clone 侧的对应：`activeCameraId` ＝ 选中的机位；
 *   机位集合 ＝ `objects` 里 `kind === "camera"` 的那些（源站的 `rL.cameras`）。
 */
export function resolveDirectorTelemetryCameraId(
  cameras: readonly { id: string }[],
  activeCameraId: string | null | undefined,
): string | null {
  if (
    activeCameraId &&
    cameras.some((camera) => camera.id === activeCameraId)
  ) {
    return activeCameraId;
  }
  return cameras[0]?.id ?? null;
}

/** ★ 本地事件日志的上限（★ 免得无限增长）。 */
export const DIRECTOR_TELEMETRY_LOG_LIMIT = 50;
