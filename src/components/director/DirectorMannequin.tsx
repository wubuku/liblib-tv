import { MathUtils, type MeshStandardMaterialParameters } from "three";
import type { DirectorCharacterRig } from "@/components/director/directorPose";

function rotation(
  controls: Record<string, number>,
  prefix: string,
): [number, number, number] {
  return [
    MathUtils.degToRad(controls[`${prefix}.pitch`] ?? 0),
    MathUtils.degToRad(
      controls[`${prefix}.yaw`] ?? controls[`${prefix}.twist`] ?? 0,
    ),
    MathUtils.degToRad(
      controls[`${prefix}.roll`] ?? controls[`${prefix}.spread`] ?? 0,
    ),
  ];
}

function Material({
  color,
  material,
}: {
  color: string;
  material: MeshStandardMaterialParameters;
}) {
  return (
    <meshStandardMaterial
      color={color}
      roughness={0.72}
      metalness={0.02}
      {...material}
    />
  );
}

function Segment({
  color,
  length,
  material,
  position,
  radius,
}: {
  color: string;
  length: number;
  material: MeshStandardMaterialParameters;
  position: [number, number, number];
  radius: number;
}) {
  return (
    <mesh castShadow position={position}>
      <capsuleGeometry args={[radius, length, 8, 14]} />
      <Material color={color} material={material} />
    </mesh>
  );
}

function Joint({
  color,
  material,
  position,
  radius,
}: {
  color: string;
  material: MeshStandardMaterialParameters;
  position: [number, number, number];
  radius: number;
}) {
  return (
    <mesh castShadow position={position}>
      <sphereGeometry args={[radius, 16, 12]} />
      <Material color={color} material={material} />
    </mesh>
  );
}

function Arm({
  color,
  controls,
  material,
  side,
}: {
  color: string;
  controls: Record<string, number>;
  material: MeshStandardMaterialParameters;
  side: "left" | "right";
}) {
  const sign = side === "left" ? -1 : 1;
  const prefix = side === "left" ? "left" : "right";
  return (
    <group
      position={[sign * 0.43, 0.66, 0]}
      rotation={rotation(controls, `${prefix}Shoulder`)}
    >
      <Joint
        color={color}
        material={material}
        position={[0, 0, 0]}
        radius={0.12}
      />
      <Segment
        color={color}
        length={0.36}
        material={material}
        position={[0, -0.28, 0]}
        radius={0.09}
      />
      <group
        position={[0, -0.58, 0]}
        rotation={[
          MathUtils.degToRad(controls[`${prefix}Elbow.bend`] ?? 0),
          0,
          0,
        ]}
      >
        <Joint
          color={color}
          material={material}
          position={[0, 0, 0]}
          radius={0.095}
        />
        <Segment
          color={color}
          length={0.34}
          material={material}
          position={[0, -0.27, 0]}
          radius={0.075}
        />
        <group
          position={[0, -0.55, 0]}
          rotation={rotation(controls, `${prefix}Hand`)}
        >
          <Joint
            color={color}
            material={material}
            position={[0, 0, 0]}
            radius={0.078}
          />
          <mesh castShadow position={[0, -0.13, 0.025]} scale={[0.85, 1.35, 0.58]}>
            <sphereGeometry args={[0.1, 14, 10]} />
            <Material color="#c9aa94" material={material} />
          </mesh>
        </group>
      </group>
    </group>
  );
}

function Leg({
  controls,
  material,
  side,
}: {
  controls: Record<string, number>;
  material: MeshStandardMaterialParameters;
  side: "left" | "right";
}) {
  const sign = side === "left" ? -1 : 1;
  const prefix = side === "left" ? "left" : "right";
  return (
    <group
      position={[sign * 0.19, 1.15, 0]}
      rotation={rotation(controls, `${prefix}Hip`)}
    >
      <Joint
        color="#25282e"
        material={material}
        position={[0, 0, 0]}
        radius={0.13}
      />
      <Segment
        color="#25282e"
        length={0.42}
        material={material}
        position={[0, -0.31, 0]}
        radius={0.105}
      />
      <group
        position={[0, -0.62, 0]}
        rotation={[
          MathUtils.degToRad(controls[`${prefix}Knee.bend`] ?? 0),
          0,
          0,
        ]}
      >
        <Joint
          color="#25282e"
          material={material}
          position={[0, 0, 0]}
          radius={0.11}
        />
        <Segment
          color="#25282e"
          length={0.4}
          material={material}
          position={[0, -0.3, 0]}
          radius={0.09}
        />
        <group
          position={[0, -0.61, 0.08]}
          rotation={rotation(controls, `${prefix}Foot`)}
        >
          <mesh
            castShadow
            position={[0, 0, 0.12]}
            rotation={[Math.PI / 2, 0, 0]}
            scale={[1, 1.32, 0.75]}
          >
            <capsuleGeometry args={[0.105, 0.24, 8, 14]} />
            <Material color="#17191d" material={material} />
          </mesh>
        </group>
      </group>
    </group>
  );
}

export function DirectorMannequin({
  color,
  material,
  rig,
}: {
  color: string;
  material: MeshStandardMaterialParameters;
  rig: DirectorCharacterRig;
}) {
  const controls = rig.controls;
  return (
    <group
      name="director-articulated-character"
      position={[0, controls["body.offsetY"] ?? 0, 0]}
      rotation={rotation(controls, "body")}
      scale={0.86}
    >
      <Leg
        controls={controls}
        material={material}
        side="left"
      />
      <Leg
        controls={controls}
        material={material}
        side="right"
      />

      <group position={[0, 1.22, 0]} rotation={rotation(controls, "torso")}>
        <mesh castShadow position={[0, 0.02, 0]} scale={[1.25, 0.72, 0.82]}>
          <sphereGeometry args={[0.29, 20, 16]} />
          <Material color={color} material={material} />
        </mesh>
        <mesh castShadow position={[0, 0.35, 0]} scale={[1.08, 1.15, 0.7]}>
          <capsuleGeometry args={[0.29, 0.32, 10, 18]} />
          <Material color={color} material={material} />
        </mesh>

        <Arm
          color={color}
          controls={controls}
          material={material}
          side="left"
        />
        <Arm
          color={color}
          controls={controls}
          material={material}
          side="right"
        />

        <mesh castShadow position={[0, 0.79, 0]}>
          <cylinderGeometry args={[0.1, 0.115, 0.2, 16]} />
          <Material color="#c9aa94" material={material} />
        </mesh>
        <group position={[0, 1.08, 0]} rotation={rotation(controls, "head")}>
          <mesh castShadow scale={[0.9, 1.05, 0.92]}>
            <sphereGeometry args={[0.27, 22, 18]} />
            <Material color="#c9aa94" material={material} />
          </mesh>
          <mesh position={[-0.09, 0.035, 0.245]} scale={[1, 0.6, 0.45]}>
            <sphereGeometry args={[0.027, 10, 8]} />
            <meshStandardMaterial color="#17191d" roughness={0.84} />
          </mesh>
          <mesh position={[0.09, 0.035, 0.245]} scale={[1, 0.6, 0.45]}>
            <sphereGeometry args={[0.027, 10, 8]} />
            <meshStandardMaterial color="#17191d" roughness={0.84} />
          </mesh>
        </group>
      </group>
    </group>
  );
}
