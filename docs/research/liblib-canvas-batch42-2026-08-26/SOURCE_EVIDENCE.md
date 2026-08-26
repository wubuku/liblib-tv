# Batch 42 Source Evidence

## 1. Provenance

Observation date: 2026-08-26.

Authenticated target associated with the extracted current canvas assets:

```text
https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd
```

Current decoded locale chunk:

```text
/tmp/libtv-director-2026-08-26.js
size: 343745 bytes
sha256: 58ea14cd8358885f35147986fdafe6a2c7391b6111fd1e6e02283668d1bae277
```

The temporary source file is not committed. This document is the durable,
filtered extraction record. Values were extracted only from keys matching
pose, SAM or timeline contracts so an unrelated invalid JavaScript escape
could not corrupt the result.

## 2. Pose Authoring Vocabulary

```text
directorTabPose: 姿势
directorPosePresets: 姿势预设
directorPoseAdjust: 姿势调节
directorPoseStandLabel: 站立
```

These strings prove a dedicated pose tab with preset and continuous-adjustment
regions. They do not prove tab placement, panel width, grid columns, slider
widgets or control ranges.

## 3. Exact 20 Preset Names

```text
directorPose_stand: 站立
directorPose_tpose: T型
directorPose_walk: 行走
directorPose_run: 跑步
directorPose_sit: 坐姿
directorPose_crouch: 蹲下
directorPose_one_knee: 单膝跪
directorPose_two_knees: 双膝跪
directorPose_hands_hips: 叉腰
directorPose_lean: 倚靠
directorPose_bow: 鞠躬
directorPose_think: 思考
directorPose_fight: 格斗
directorPose_kick: 踢球
directorPose_throw: 投掷
directorPose_push: 推进
directorPose_wave: 招手
directorPose_stretch: 伸手
directorPose_arms_crossed: 抱臂
directorPose_phone: 看手机
```

The names and count are direct source facts. Preset joint values are not
present in the locale chunk.

## 4. SAM Bone Vocabulary

### Surface and groups

```text
directorSamBonePose: SAM 骨骼姿势
directorSamBoneGroupBody: 身体
directorSamBoneGroupHeadNeck: 头颈
directorSamBoneGroupLeftArm: 左臂
directorSamBoneGroupRightArm: 右臂
directorSamBoneGroupLeftLeg: 左腿
directorSamBoneGroupRightLeg: 右腿
```

### Bones

```text
directorSamBoneRoot: 根骨骼
directorSamBoneWaist: 腰部
directorSamBoneSpine1: 脊柱 1
directorSamBoneSpine2: 脊柱 2
directorSamBoneChest: 胸腔
directorSamBoneNeck: 颈部
directorSamBoneHead: 头部
directorSamBoneClavicle: 锁骨
directorSamBoneUpperArm: 上臂
directorSamBoneForearm: 前臂
directorSamBoneWrist: 手腕
directorSamBoneThigh: 大腿
directorSamBoneLowerLeg: 小腿
directorSamBoneFoot: 脚掌
```

This proves the visible grouping and naming taxonomy. It does not prove that
every named bone has three Euler sliders, the internal skeleton hierarchy or
the number of editable channels.

## 5. Timeline Semantics

```text
directorTimelineTransformKeyframe: 变换关键帧
directorTimelinePoseKeyframe: 姿态关键帧
directorTimelinePose: 姿态
directorTimelineAutoKeyframe: 自动帧
directorTimelineCreateTrack: 新建轨道
directorTimelineRemoveTrack: 移除轨道
directorTimelineCharacterFallback: 角色
```

`姿态关键帧` is distinct from `变换关键帧`, so a single character must be able
to retain pose animation without replacing its object transform animation.
The strings do not prove the exact serialized value shape or interpolation
algorithm.

## 6. Missing Runtime Evidence

No authenticated pose state was opened and captured during this extraction.
The following remain unknown and must be labeled clone calibration:

- Inspector tab/header geometry and responsive behavior;
- preset tile dimensions, iconography and active styling;
- exact SAM hierarchy presentation and expanded groups;
- control channels, limits, steps and numeric formatting;
- procedural character geometry and materials;
- pose keyframe marker color, icon or row nesting;
- whether source interpolation is Euler, quaternion, stepped or curve-driven.
