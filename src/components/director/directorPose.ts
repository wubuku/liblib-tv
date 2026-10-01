export const DIRECTOR_POSE_PRESET_IDS = [
  "stand",
  "t-pose",
  "walk",
  "run",
  "sit",
  "crouch",
  "kneel-one",
  "kneel-two",
  "hands-on-hips",
  "lean",
  "bow",
  "think",
  "fight",
  "kick",
  "throw",
  "push",
  "wave",
  "reach",
  "cross-arms",
  "phone",
] as const;

export type DirectorPosePresetId =
  (typeof DIRECTOR_POSE_PRESET_IDS)[number];

export type DirectorPoseControls = Record<string, number>;

export interface DirectorCharacterRig {
  posePresetId: DirectorPosePresetId | null;
  controls: DirectorPoseControls;
}

export interface DirectorPoseKeyframeValue {
  posePresetId: DirectorPosePresetId | null;
  controls: DirectorPoseControls;
}

export interface DirectorPosePresetDefinition {
  id: DirectorPosePresetId;
  label: string;
  controls: DirectorPoseControls;
}

export interface DirectorPoseControlDefinition {
  key: string;
  label: string;
  min: number;
  max: number;
  step: number;
  unit: "degree" | "meter";
}

// Batch 584（源站 2026-10-01 实测，角色A 姿势页）：姿势调节按**解剖部位**
// 分组，四肢组内再分「左 / 右」子行；源站七组为 身体 / 躯干 / 头部 /
// 手臂 — 肩 / 肘部 / 腿部 — 髋 / 膝部。side 仅用于渲染子行标题。
export interface DirectorPoseControlRow {
  side?: "left" | "right";
  label?: string;
  controls: DirectorPoseControlDefinition[];
}

export interface DirectorPoseControlGroup {
  id:
    | "body"
    | "torso"
    | "head"
    | "arm-shoulder"
    | "elbow"
    | "leg-hip"
    | "knee";
  label: string;
  bones: string[];
  rows: DirectorPoseControlRow[];
}

const angle = (
  key: string,
  label: string,
  min = -135,
  max = 135,
): DirectorPoseControlDefinition => ({
  key,
  label,
  min,
  max,
  step: 1,
  unit: "degree",
});

// Batch 584：滑杆量程逐项取自源站实测（range 的 min/max/step 全为 step=1）。
// 注意滑杆量程 ≠ 钳制量程：源站 T型 预设的肩外展为 -70，落在源站滑杆下限
// -10 之外，因此 DIRECTOR_POSE_CONTROL_REGISTRY 保留原有宽量程用于
// normalizeDirectorPoseControls 钳制，滑杆仅按源站区间呈现（越界时
// 滑块贴边，与源站行为一致）。
export const DIRECTOR_POSE_CONTROL_GROUPS: DirectorPoseControlGroup[] = [
  {
    id: "body",
    label: "身体",
    bones: ["根骨骼", "腰部", "脊柱 1", "脊柱 2", "胸腔"],
    rows: [
      {
        controls: [
          angle("body.pitch", "前倾", -90, 90),
          angle("body.yaw", "转身", -90, 90),
          angle("body.roll", "侧倾", -45, 45),
        ],
      },
    ],
  },
  {
    id: "torso",
    label: "躯干",
    bones: ["腰部", "脊柱 1", "脊柱 2", "胸腔"],
    rows: [
      {
        controls: [
          angle("torso.pitch", "前倾", -45, 45),
          angle("torso.yaw", "扭转", -45, 45),
          angle("torso.roll", "侧倾", -30, 30),
        ],
      },
    ],
  },
  {
    id: "head",
    label: "头部",
    bones: ["颈部", "头部"],
    rows: [
      {
        controls: [
          angle("head.pitch", "点头", -60, 60),
          angle("head.yaw", "转头", -90, 90),
          angle("head.roll", "歪头", -30, 30),
        ],
      },
    ],
  },
  {
    id: "arm-shoulder",
    label: "手臂 — 肩",
    bones: ["锁骨", "上臂"],
    rows: [
      {
        side: "left",
        label: "左",
        controls: [
          angle("leftShoulder.pitch", "前举", -90, 180),
          angle("leftShoulder.spread", "外展", -10, 90),
          angle("leftShoulder.twist", "扭转", -90, 90),
        ],
      },
      {
        side: "right",
        label: "右",
        controls: [
          angle("rightShoulder.pitch", "前举", -90, 180),
          angle("rightShoulder.spread", "外展", -10, 90),
          angle("rightShoulder.twist", "扭转", -90, 90),
        ],
      },
    ],
  },
  {
    id: "elbow",
    label: "肘部",
    bones: ["前臂"],
    rows: [
      {
        side: "left",
        label: "左",
        controls: [angle("leftElbow.bend", "弯曲", 0, 150)],
      },
      {
        side: "right",
        label: "右",
        controls: [angle("rightElbow.bend", "弯曲", 0, 150)],
      },
    ],
  },
  {
    id: "leg-hip",
    label: "腿部 — 髋",
    bones: ["大腿"],
    rows: [
      {
        side: "left",
        label: "左",
        controls: [
          angle("leftHip.pitch", "前抬", -90, 90),
          angle("leftHip.spread", "外展", -30, 60),
          angle("leftHip.twist", "扭转", -45, 45),
        ],
      },
      {
        side: "right",
        label: "右",
        controls: [
          angle("rightHip.pitch", "前抬", -90, 90),
          angle("rightHip.spread", "外展", -30, 60),
          angle("rightHip.twist", "扭转", -45, 45),
        ],
      },
    ],
  },
  {
    id: "knee",
    label: "膝部",
    bones: ["小腿"],
    rows: [
      {
        side: "left",
        label: "左",
        controls: [angle("leftKnee.bend", "弯曲", 0, 150)],
      },
      {
        side: "right",
        label: "右",
        controls: [angle("rightKnee.bend", "弯曲", 0, 150)],
      },
    ],
  },
];

// Batch 584: 源站姿势页没有「根骨骼 · 高度」「手腕」「脚掌」滑杆，但 clone
// 的 20 个源站对齐预设（蹲下 / 坐姿 / 抱臂 / 招手…）依赖这些关节取值，
// 因此它们只从 UI 隐去，仍登记在内部量程表里参与钳制与预设应用。
const INTERNAL_POSE_CONTROLS: DirectorPoseControlDefinition[] = [
  {
    key: "body.offsetY",
    label: "根骨骼 · 高度",
    min: -0.6,
    max: 0.35,
    step: 0.01,
    unit: "meter",
  },
  angle("leftHand.pitch", "手腕 · 俯仰", -90, 90),
  angle("leftHand.roll", "手腕 · 侧倾", -90, 90),
  angle("leftHand.twist", "手腕 · 扭转", -90, 90),
  angle("rightHand.pitch", "手腕 · 俯仰", -90, 90),
  angle("rightHand.roll", "手腕 · 侧倾", -90, 90),
  angle("rightHand.twist", "手腕 · 扭转", -90, 90),
  angle("leftFoot.pitch", "脚掌 · 俯仰", -90, 90),
  angle("leftFoot.roll", "脚掌 · 侧倾", -90, 90),
  angle("rightFoot.pitch", "脚掌 · 俯仰", -90, 90),
  angle("rightFoot.roll", "脚掌 · 侧倾", -90, 90),
];

export const DIRECTOR_POSE_PRESETS: DirectorPosePresetDefinition[] = [
  { id: "stand", label: "站立", controls: {} },
  {
    id: "t-pose",
    label: "T型",
    controls: {
      "leftShoulder.spread": -70,
      "rightShoulder.spread": 70,
      "leftShoulder.pitch": 15,
      "rightShoulder.pitch": 15,
      "leftElbow.bend": 10,
      "rightElbow.bend": 10,
    },
  },
  {
    id: "walk",
    label: "行走",
    controls: {
      "leftShoulder.pitch": 20,
      "rightShoulder.pitch": -20,
      "leftHip.pitch": -20,
      "rightHip.pitch": 20,
      "leftKnee.bend": 12,
      "rightKnee.bend": 4,
    },
  },
  {
    id: "run",
    label: "跑步",
    controls: {
      "leftShoulder.pitch": 42,
      "rightShoulder.pitch": -42,
      "leftHip.pitch": -35,
      "rightHip.pitch": 40,
      "leftKnee.bend": 28,
      "rightKnee.bend": 18,
    },
  },
  {
    id: "sit",
    label: "坐姿",
    controls: {
      "torso.pitch": -10,
      "leftHip.pitch": 80,
      "rightHip.pitch": 80,
      "leftKnee.bend": 90,
      "rightKnee.bend": 90,
    },
  },
  {
    id: "crouch",
    label: "蹲下",
    controls: {
      "body.offsetY": -0.43,
      "body.pitch": -26,
      "torso.pitch": -24,
      "head.pitch": 22,
      "leftHip.pitch": 92,
      "rightHip.pitch": 92,
      "leftKnee.bend": 112,
      "rightKnee.bend": 112,
      "leftShoulder.pitch": 52,
      "rightShoulder.pitch": 50,
      "leftShoulder.spread": -10,
      "rightShoulder.spread": 10,
      "leftElbow.bend": 80,
      "rightElbow.bend": 76,
    },
  },
  {
    id: "kneel-one",
    label: "单膝跪",
    controls: {
      "body.offsetY": -0.42,
      "body.pitch": -16,
      "torso.pitch": -10,
      "head.pitch": 12,
      "leftHip.pitch": 68,
      "leftKnee.bend": 86,
      "leftFoot.pitch": 20,
      "rightHip.pitch": -15,
      "rightKnee.bend": 80,
      "rightFoot.pitch": 60,
      "leftShoulder.pitch": 5,
      "leftShoulder.spread": 10,
      "leftShoulder.twist": -10,
      "leftElbow.bend": 30,
      "rightShoulder.pitch": -18,
      "rightShoulder.spread": 10,
      "rightElbow.bend": 18,
    },
  },
  {
    id: "kneel-two",
    label: "双膝跪",
    controls: {
      "body.offsetY": -0.4,
      "body.pitch": 2,
      "torso.pitch": 8,
      "head.pitch": -2,
      "leftShoulder.pitch": -10,
      "rightShoulder.pitch": -10,
      "leftShoulder.spread": -5,
      "rightShoulder.spread": 5,
      "leftElbow.bend": 8,
      "rightElbow.bend": 8,
      "leftHip.pitch": -8,
      "rightHip.pitch": -8,
      "leftKnee.bend": 126,
      "rightKnee.bend": 126,
      "leftFoot.pitch": -20,
      "rightFoot.pitch": -20,
    },
  },
  {
    id: "hands-on-hips",
    label: "叉腰",
    controls: {
      "leftShoulder.pitch": -36,
      "rightShoulder.pitch": -36,
      "leftShoulder.twist": 80,
      "rightShoulder.twist": -80,
      "leftElbow.bend": 86,
      "rightElbow.bend": 86,
      "leftHand.roll": -35,
      "rightHand.roll": 35,
    },
  },
  {
    id: "lean",
    label: "倚靠",
    controls: {
      "body.roll": -10,
      "leftHip.spread": -8,
      "rightHip.spread": 8,
      "head.roll": 6,
    },
  },
  {
    id: "bow",
    label: "鞠躬",
    controls: {
      "body.pitch": -46,
      "torso.pitch": -10,
      "head.pitch": 20,
      "leftHip.pitch": 49,
      "rightHip.pitch": 49,
      "leftShoulder.pitch": 5,
      "rightShoulder.pitch": 5,
      "leftShoulder.spread": 10,
      "rightShoulder.spread": -10,
      "leftElbow.bend": 12,
      "rightElbow.bend": 12,
    },
  },
  {
    id: "think",
    label: "思考",
    controls: {
      "rightShoulder.pitch": 8,
      "rightShoulder.twist": -40,
      "rightElbow.bend": 90,
      "rightHand.roll": -40,
      "rightHand.pitch": 15,
      "rightHand.twist": -10,
      "leftShoulder.pitch": 8,
      "leftShoulder.twist": 40,
      "leftElbow.bend": 90,
    },
  },
  {
    id: "fight",
    label: "格斗",
    controls: {
      "body.yaw": -10,
      "body.pitch": 5,
      "torso.yaw": 8,
      "head.yaw": 8,
      "leftShoulder.pitch": 48,
      "leftShoulder.spread": -16,
      "leftShoulder.twist": 22,
      "rightShoulder.pitch": 30,
      "rightShoulder.twist": -22,
      "leftElbow.bend": 86,
      "rightElbow.bend": 84,
      "leftHip.spread": -18,
      "rightHip.spread": 22,
      "leftHip.pitch": 4,
      "rightHip.pitch": -6,
      "leftKnee.bend": 12,
      "rightKnee.bend": 18,
    },
  },
  {
    id: "kick",
    label: "踢球",
    controls: {
      "leftHip.pitch": -8,
      "rightHip.pitch": 58,
      "rightKnee.bend": 35,
      "leftShoulder.pitch": 18,
      "rightShoulder.pitch": -24,
    },
  },
  {
    id: "throw",
    label: "投掷",
    controls: {
      "body.offsetY": -0.12,
      "body.pitch": 5,
      "body.yaw": 14,
      "torso.yaw": -10,
      "head.yaw": 8,
      "rightShoulder.pitch": 76,
      "rightShoulder.spread": -14,
      "rightShoulder.twist": 28,
      "rightElbow.bend": 86,
      "rightHand.roll": 18,
      "rightHand.pitch": -12,
      "leftShoulder.pitch": 34,
      "leftShoulder.spread": 10,
      "leftShoulder.twist": 8,
      "leftElbow.bend": 54,
      "leftHand.pitch": -10,
      "leftHip.spread": -12,
      "rightHip.spread": 18,
      "leftHip.pitch": 24,
      "rightHip.pitch": -10,
      "leftKnee.bend": 30,
      "rightKnee.bend": 14,
      "leftFoot.pitch": -8,
      "rightFoot.roll": 6,
    },
  },
  {
    id: "push",
    label: "推进",
    controls: {
      "body.offsetY": -0.16,
      "body.pitch": 5,
      "body.yaw": 38,
      "torso.pitch": -4,
      "head.pitch": 6,
      "leftShoulder.pitch": 92,
      "rightShoulder.pitch": 92,
      "leftShoulder.spread": -11,
      "rightShoulder.spread": 11,
      "leftShoulder.twist": 6,
      "rightShoulder.twist": -6,
      "leftElbow.bend": 6,
      "rightElbow.bend": 6,
      "leftHand.pitch": -14,
      "rightHand.pitch": -14,
      "leftHip.spread": -12,
      "rightHip.spread": 14,
      "leftHip.pitch": 38,
      "rightHip.pitch": -20,
      "leftKnee.bend": 42,
      "rightKnee.bend": 20,
      "leftFoot.pitch": -6,
      "rightFoot.roll": 8,
    },
  },
  {
    id: "wave",
    label: "招手",
    controls: {
      "rightShoulder.pitch": 60,
      "rightShoulder.twist": 30,
      "rightElbow.bend": 90,
      "rightHand.roll": -20,
      "rightHand.pitch": 12,
      "rightHand.twist": 10,
      "leftShoulder.pitch": -10,
      "leftShoulder.spread": 8,
      "leftElbow.bend": 18,
      "leftHand.pitch": -8,
    },
  },
  {
    id: "reach",
    label: "伸手",
    controls: {
      "rightShoulder.pitch": 50,
      "rightElbow.bend": 12,
    },
  },
  {
    id: "cross-arms",
    label: "抱臂",
    controls: {
      "leftShoulder.pitch": 50,
      "leftShoulder.spread": -55,
      "leftShoulder.twist": 75,
      "leftElbow.bend": 50,
      "leftHand.pitch": -10,
      "rightShoulder.pitch": 90,
      "rightShoulder.spread": 55,
      "rightShoulder.twist": -45,
      "rightElbow.bend": 50,
      "rightHand.roll": 18,
      "rightHand.pitch": -10,
    },
  },
  {
    id: "phone",
    label: "看手机",
    controls: {
      "head.pitch": 18,
      "rightShoulder.pitch": 20,
      "rightShoulder.spread": -4,
      "rightShoulder.twist": -30,
      "rightElbow.bend": 82,
      "rightHand.roll": -30,
      "rightHand.pitch": 14,
      "rightHand.twist": 60,
      "leftShoulder.pitch": -10,
      "leftShoulder.spread": 8,
      "leftElbow.bend": 16,
      "leftHand.pitch": -8,
    },
  },
];

const controlLimits = new Map(
  [
    ...DIRECTOR_POSE_CONTROL_GROUPS.flatMap((group) =>
      group.rows.flatMap((row) => row.controls),
    ),
    ...INTERNAL_POSE_CONTROLS,
  ].map((control) => [control.key, control] as const),
);

export function normalizeDirectorPoseControls(
  controls: DirectorPoseControls,
): DirectorPoseControls {
  return Object.fromEntries(
    Object.entries(controls).flatMap(([key, value]) => {
      if (!Number.isFinite(value)) return [];
      const limits = controlLimits.get(key);
      const normalized = limits
        ? Math.min(Math.max(value, limits.min), limits.max)
        : value;
      return [[key, normalized]];
    }),
  );
}

export function createDirectorCharacterRig(): DirectorCharacterRig {
  return {
    posePresetId: "stand",
    controls: {},
  };
}

export function cloneDirectorCharacterRig(
  rig: DirectorCharacterRig,
): DirectorCharacterRig {
  return {
    posePresetId: rig.posePresetId,
    controls: { ...rig.controls },
  };
}

export function getDirectorPosePreset(
  presetId: DirectorPosePresetId,
): DirectorPosePresetDefinition {
  return (
    DIRECTOR_POSE_PRESETS.find((preset) => preset.id === presetId) ??
    DIRECTOR_POSE_PRESETS[0]
  );
}

export function applyDirectorPosePreset(
  presetId: DirectorPosePresetId,
): DirectorCharacterRig {
  const preset = getDirectorPosePreset(presetId);
  return {
    posePresetId: preset.id,
    controls: normalizeDirectorPoseControls(preset.controls),
  };
}

export function updateDirectorPoseControl(
  rig: DirectorCharacterRig,
  key: string,
  value: number,
): DirectorCharacterRig {
  return {
    posePresetId: null,
    controls: normalizeDirectorPoseControls({
      ...rig.controls,
      [key]: value,
    }),
  };
}

export function cloneDirectorPoseValue(
  value: DirectorPoseKeyframeValue,
): DirectorPoseKeyframeValue {
  return {
    posePresetId: value.posePresetId,
    controls: { ...value.controls },
  };
}

export function interpolateDirectorPoseValue(
  from: DirectorPoseKeyframeValue,
  to: DirectorPoseKeyframeValue,
  progress: number,
): DirectorPoseKeyframeValue {
  if (progress <= 0) return cloneDirectorPoseValue(from);
  if (progress >= 1) return cloneDirectorPoseValue(to);
  const keys = new Set([
    ...Object.keys(from.controls),
    ...Object.keys(to.controls),
  ]);
  const controls: DirectorPoseControls = {};
  keys.forEach((key) => {
    const fromValue = from.controls[key] ?? 0;
    const toValue = to.controls[key] ?? 0;
    controls[key] = fromValue + (toValue - fromValue) * progress;
  });
  return {
    posePresetId:
      from.posePresetId === to.posePresetId ? from.posePresetId : null,
    controls,
  };
}
