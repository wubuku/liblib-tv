# Batch 181 — 老化验证器修复立项（batch72/74 复活 + batch49 自愈确认）

## 背景

12 个老化验证器（Batch 6/9/40/41/44/46/48/49/51/72/74/75）逐一复跑，
失败形态分三类：

1. **工具/fixture 可修（本批修复）**：batch72、batch74。
2. **已自愈**：batch49（director viewport gizmo）直接通过——后续批次
   间接修复了其合同，老化名单实际剩 11。
3. **仍为历史合同**（保持 AGED_GATE，未动）：batch6（marquee，已被
   Batch 77 导航语义取代）、batch9/51（同款几何断言 (1092.5, 900.5)
   超出 900 视口）、batch40/41/44/46/48（早期画布合同）、batch75
   （wait_for_function 30s 超时，需单独立项诊断）。

## batch72 修复（fixture 未随合同更新）

- 失败：`DANGLING_REFERENCE at $.shots[1].cameraId`。
- 归因：Batch 96（3f897b2）引入 shot→camera 存在性校验（多机位 shot
  工作流），晚于 batch72 fixture（2026-08-28）；`deriveDefaultShots`
  为每个相机派生 shot，batch72 的 `oneCameraDocument` 手工过滤了
  camera-b 的对象与轨道但没删其派生 shot。
- 修复：fixture 补 `shots` 过滤（`shot.cameraId !== "camera-b"`），
  镜像 DELETE_OBJECT 的级联语义；`--experimental-strip-types` 对 .mjs
  是冗余 flag（保留不影响）。
- 结果：pure + browser 双 PASS（8 场景全绿）。

## batch74 修复（应用级真回归）

- 失败：`authority.load` 返回 REJECTED（期望 RESTORED）。
- 归因：`documentForPersistence` 剥离非持久 captureDescriptors 时没剪枝
  `shots[].captureIds`——Batch 96 给 shot 增加 captureIds 并收紧
  shot→capture 存在性校验后，任何含未物化 capture 的工程在 load 重校验
  必 REJECTED。这是**真持久化回归**（保存的东西自己读不回来）。
- 修复：`src/lib/directorProjectPersistence.ts` 的 `documentForPersistence`
  剥离 capture 的同时按 stableCaptureIds 剪枝各 shot 的 captureIds。
- 结果：PASS。

## 验收

- batch72 / batch74 全 PASS；batch49 确认自愈。
- Director 系列回归绿：89 / 90 / 91 / 92 / 93 / 94 / 95 / 96。
- 画布全量回归绿：21 / 22 / 26 / 33 / 128 / 149 / 155 / 160 / 165 / 166 /
  169 / 172-180。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：batch75 超时根因（另行立项）；其余历史合同与当前源站的逐条
  差距（继续 AGED_GATE）。
- 源站测试残留清理：0 残留（本批无源站采样，纯 clone/验证器修复）。
