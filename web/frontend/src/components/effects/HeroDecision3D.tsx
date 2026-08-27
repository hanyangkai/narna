import { Suspense, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { ContactShadows, Environment, Float } from "@react-three/drei";
import * as THREE from "three";

/** Refined decision core — glass + metal, single accent, subtle motion. */
function DecisionCore() {
  const group = useRef<THREE.Group>(null);
  const wire = useRef<THREE.Mesh>(null);
  const ring = useRef<THREE.Mesh>(null);
  const orbit = useRef<THREE.Group>(null);

  const satellites = useMemo(() => {
    return Array.from({ length: 8 }, (_, i) => {
      const a = (i / 8) * Math.PI * 2;
      return {
        pos: [Math.cos(a) * 1.65, Math.sin(a * 0.35) * 0.25, Math.sin(a) * 1.65] as [
          number,
          number,
          number,
        ],
      };
    });
  }, []);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const px = state.pointer.x * 0.35;
    const py = state.pointer.y * 0.2;

    if (group.current) {
      group.current.rotation.y = THREE.MathUtils.lerp(group.current.rotation.y, px * 0.6, 0.04);
      group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, -py * 0.4, 0.04);
    }
    if (wire.current) {
      wire.current.rotation.y = t * 0.12;
    }
    if (ring.current) {
      ring.current.rotation.z = t * 0.18;
      ring.current.rotation.x = Math.PI / 2.15;
    }
    if (orbit.current) {
      orbit.current.rotation.y = t * 0.08;
    }
  });

  return (
    <group ref={group} position={[0, 0.15, 0]}>
      <Float speed={1.1} rotationIntensity={0.12} floatIntensity={0.25}>
        {/* Inner solid glass */}
        <mesh>
          <icosahedronGeometry args={[0.85, 1]} />
          <meshPhysicalMaterial
            color="#0e4a5c"
            metalness={0.15}
            roughness={0.12}
            transmission={0.55}
            thickness={1.2}
            transparent
            opacity={0.92}
            envMapIntensity={1.4}
            clearcoat={1}
            clearcoatRoughness={0.08}
          />
        </mesh>

        {/* Outer wire lattice */}
        <mesh ref={wire} scale={1.08}>
          <icosahedronGeometry args={[0.95, 1]} />
          <meshStandardMaterial
            color="#7dd3e8"
            emissive="#0e4a5c"
            emissiveIntensity={0.35}
            metalness={0.9}
            roughness={0.25}
            wireframe
            transparent
            opacity={0.55}
          />
        </mesh>
      </Float>

      {/* Single equatorial ring */}
      <mesh ref={ring} scale={1.45}>
        <torusGeometry args={[1, 0.008, 12, 128]} />
        <meshStandardMaterial
          color="#94a3b8"
          emissive="#00c2d7"
          emissiveIntensity={0.45}
          metalness={1}
          roughness={0.2}
        />
      </mesh>

      {/* Soft satellites */}
      <group ref={orbit}>
        {satellites.map((s, i) => (
          <mesh key={i} position={s.pos}>
            <sphereGeometry args={[0.035, 16, 16]} />
            <meshStandardMaterial
              color="#cbd5e1"
              emissive="#00c2d7"
              emissiveIntensity={0.6}
              metalness={0.8}
              roughness={0.3}
            />
          </mesh>
        ))}
      </group>
    </group>
  );
}

function Scene() {
  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[4, 6, 3]} intensity={1.1} color="#f8fafc" />
      <pointLight position={[-3, 1, 2]} intensity={0.55} color="#00c2d7" />
      <pointLight position={[2, -2, -2]} intensity={0.25} color="#64748b" />
      <Environment preset="city" />
      <DecisionCore />
      <ContactShadows
        position={[0, -1.55, 0]}
        opacity={0.35}
        scale={8}
        blur={2.4}
        far={4}
        color="#041018"
      />
    </>
  );
}

type Props = { className?: string };

export default function HeroDecision3D({ className = "" }: Props) {
  return (
    <div className={`fx-r3f ${className}`.trim()} aria-hidden>
      <Canvas
        dpr={[1, 1.5]}
        camera={{ position: [0, 0.35, 4.6], fov: 38 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        style={{ width: "100%", height: "100%", background: "transparent" }}
      >
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
    </div>
  );
}
