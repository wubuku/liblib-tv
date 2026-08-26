# Batch 41 Source Evidence

## 1. Provenance

Observation date: 2026-08-26.

Authenticated target associated with the extracted current canvas assets:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

The decoded locale chunk reused from Batch 40:

```text
https://liblibai-web-static.liblib.cloud/liblibtv_online/static/_next/static/chunks/0_o2gxip5splz.js
size: 343745 bytes
sha256: 58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277
```

On 2026-08-26 the public canvas shell exposed 108 current static chunk URLs
totalling 14,439,615 downloaded bytes. A repository-wide search across those
chunks found `directorPhoneVcam`, `手机运镜` or `虚拟相机` only in the locale
chunk above. Therefore this batch has product-state vocabulary but not
component DOM/CSS or implementation code.

The minified source and temporary chunk corpus are not committed. This document
is the durable extraction record.

## 2. Exact Product Contracts

### Entry, startup and pairing

```text
directorPhoneVcamTitle: 虚拟相机
directorPhoneVcamDisabled: 当前不可使用手机运镜
directorPhoneVcamDisableFollowHint: 请先关闭机位跟随，再使用手机运镜
directorPhoneVcamUnsupported: 当前环境不支持手机运镜
directorPhoneVcamPreparing: 正在准备本机环境
directorPhoneVcamStarting: 正在启动本机信令
directorPhoneVcamStartFailed: 手机运镜启动失败
directorPhoneVcamIdle: 点击重试启动手机运镜
directorPhoneVcamWaitingPhone: 请保持手机和电脑在同一 wifi 下，用手机扫码连接
directorPhoneVcamPaired: 手机已连接，可开始录制
directorPhoneVcamSelfSignedHint: 如果手机提示证书风险，请在同一 Wi-Fi 下继续访问并信任本机证书。
directorPhoneVcamRetry: 重试
```

These strings directly prove a stateful local-signaling workflow with
same-network QR pairing and a self-signed certificate trust path. They do not
prove the signaling protocol, QR payload, panel geometry or startup timing.

### Recording and timeline import

```text
directorPhoneVcamStartRecord: 录制
directorPhoneVcamRecording: 录制中
directorPhoneVcamStopRecord: 停止录制
directorPhoneVcamNoRoom: 当前播放头后没有可录制时长
directorPhoneVcamTakeEmpty: 本次手机运镜没有有效录制内容
directorPhoneVcamImported: 手机运镜已导入机位时间轴
directorPhoneVcamCameraName: 手机运镜 {index}
directorPhoneVcamTrackName: 手机运镜 {index}
directorPhoneVcamSceneNotReady: 导演台视口还未准备好
```

This proves:

- recording starts relative to the current playhead;
- there is an explicit no-remaining-time guard;
- empty takes are rejected;
- a successful take imports a named camera and a named camera track.

The source strings do not prove whether samples are reduced, how often they
are sampled or whether an existing camera is duplicated versus created fresh.

### Phone controls

```text
directorPhoneVcamGyro: 陀螺仪
directorPhoneVcamEnableGyro: 启用陀螺仪
directorPhoneVcamGyroReady: 陀螺仪已启用
directorPhoneVcamGyroPermissionHint: 请在 Safari 设置中允许运动与方向访问后重试
directorPhoneVcamStability: 稳定度
directorPhoneVcamSettingsTitle: 陀螺仪设置
directorPhoneVcamStabilityValue: 稳定度：{value}
directorPhoneVcamGyroValue: GYRO：{value}
directorPhoneVcamKeepLevel: 保持水平
directorPhoneVcamHold: 临时锁定机位
directorPhoneVcamUnlockCamera: 解锁机位
directorPhoneVcamReleaseToCalibrate: 松开校准
directorPhoneVcamElevateUp: 上升
directorPhoneVcamElevateDown: 下降
```

This proves orientation input plus smoothing/level/hold/elevation controls.
Exact control widgets, units, value ranges and motion mapping remain unknown.

### Performance diagnostics

The remaining direct keys prove an internal diagnostic surface for:

- connection and pose reception;
- phone and desktop sample gaps;
- camera application and main-thread frame rate;
- video uplink, RTT, available bandwidth and packet loss;
- encoding time, ICE route, quality limits and invalid messages;
- copying or exporting diagnostic JSON.

Diagnostics are backend/network breadth and are out of scope for the bounded
frontend prototype in this batch.

## 3. Existing Replication Boundary

The fixed submodule commit
`8c8bd361790be4d37158a7430365e65546e358fe` contains an unrelated mannequin
pose named `phone`, but repository-wide source search finds no orientation
events, QR pairing, signaling, virtual camera or phone camera-track import.

The upstream project supplies no implementation shortcut or visual evidence
for this feature.

## 4. Clone Calibration Boundary

The following are clone decisions and must not be described as LibTV facts:

- a `Smartphone` entry in the existing viewport toolbar;
- a popover above that toolbar;
- a non-scannable QR-like pairing placeholder;
- an explicit `本机预演` label and local-connect command;
- browser `deviceorientation` input with pointer-pad fallback;
- stability range `0..100`;
- camera orbit sensitivity and elevation increments;
- approximately 10 Hz recording samples;
- creating a new camera object and typed camera track on import;
- mobile width and overflow behavior.
