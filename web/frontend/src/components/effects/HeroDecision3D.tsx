import { Suspense, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Sparkles, Stars } from "@react-three/drei";
import * as THREE from "three";

function DecisionCore() {
  const core = useRef<THREE.Mesh>(null);
  const ringA = useRef<THREE.Mesh>(null);
  const ringB = useRef<THREE.Mesh>(null);
  const ringC = useRef<THREE.Mesh>(null);
  const nodes = useRef<THREE.Group>(null);

  const nodePositions = useMemo(() => {
    const pts: [number, number, number][] = [];
    for (let i = 0; i < 18; i++) {
      const phi = Math.acos(-1 + (2 * i) / 18);
      const theta = Math.PI * (1 + Math.sqrt(5)) * i;
      const r = 1.85;
      pts.push([
        r * Math.cos(theta) * Math.sin(phi),
        r * Math.sin(theta) * Math.sin(phi),
        r * Math.cos(phi),
      ]);
    }
    return pts;
  }, []);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const { x, y } = state.pointer;

    if (core.current) {
      core.current.rotation.y = t * 0.35 + x * 0.4;
      core.current.rotation.x = Math.sin(t * 0.4) * 0.15 + y * 0.25;
    }
    if (ringA.current) {
      ringA.current.rotation.z = t * 0.55;
      ringA.current.rotation.x = Math.PI / 2.4 + y * 0.2;
    }
    if (ringB.current) {
      ringB.current.rotation.z = -t * 0.4;
      ringB.current.rotation.y = t * 0.2 + x * 0.3;
    }
    if (ringC.current) {
      ringC.current.rotation.x = t * 0.3;
      ringC.current.rotation.y = t * 0.25;
    }
    if (nodes.current) {
      nodes.current.rotation.y = t * 0.15 + x * 0.15;
      nodes.current.rotation.x = y * 0.12;
    }
  });

  return (
    <group>
      <Float speed={1.6} rotationIntensity={0.35} floatIntensity={0.55}>
        <mesh ref={core}>
          <icosahedronGeometry args={[1.05, 1]} />
          <meshStandardMaterial
            color="#00dcff"
            emissive="#0891b2"
            emissiveIntensity={1.4}
            metalness={0.85}
            roughness={0.18}
            wireframe
          />
        </mesh>
        <mesh scale={0.72}>
          <icosahedronGeometry args={[1, 0]} />
          <meshStandardMaterial
            color="#a78bfa"
            emissive="#7c3aed"
            emissiveIntensity={0.9}
            metalness={0.7}
            roughness={0.25}
            transparent
            opacity={0.55}
          />
        </mesh>
      </Float>

      <mesh ref={ringA} scale={1.55}>
        <torusGeometry args={[1, 0.02, 16, 100]} />
        <meshStandardMaterial
          color="#00dcff"
          emissive="#00dcff"
          emissiveIntensity={2}
          metalness={1}
          roughness={0.1}
        />
      </mesh>

      <mesh ref={ringB} scale={1.85} rotation={[Math.PI / 3, 0.4, 0]}>
        <torusGeometry args={[1, 0.015, 16, 120]} />
        <meshStandardMaterial
          color="#f472b6"
          emissive="#db2777"
          emissiveIntensity={1.6}
          metalness={1}
          roughness={0.15}
        />
      </mesh>

      <mesh ref={ringC} scale={2.15} rotation={[0.6, 0.8, 0.2]}>
        <torusGeometry args={[1, 0.012, 12, 140]} />
        <meshStandardMaterial
          color="#34d399"
          emissive="#059669"
          emissiveIntensity={1.4}
          metalness={1}
          roughness={0.2}
        />
      </mesh>

      <group ref={nodes}>
        {nodePositions.map((pos, i) => (
          <mesh key={i} position={pos}>
            <sphereGeometry args={[0.055 + (i % 3) * 0.015, 12, 12]} />
            <meshStandardMaterial
              color={i % 3 === 0 ? "#00dcff" : i % 3 === 1 ? "#a78bfa" : "#34d399"}
              emissive={i % 3 === 0 ? "#00dcff" : i % 3 === 1 ? "#a78bfa" : "#34d399"}
              emissiveIntensity={2.2}
            />
          </mesh>
        ))}
      </group>

      <Sparkles
        count={80}
        scale={5.5}
        size={2.5}
        speed={0.45}
        opacity={0.7}
        color="#67e8f9"
      />
      <Sparkles
        count={40}
        scale={4.2}
        size={3}
        speed={0.3}
        opacity={0.55}
        color="#c4b5fd"
      />
    </group>
  );
}

function SceneLights() {
  return (
    <>
      <ambientLight intensity={0.35} />
      <pointLight position={[4, 3, 4]} intensity={2.2} color="#00dcff" />
      <pointLight position={[-4, -2, 2]} intensity={1.6} color="#a78bfa" />
      <pointLight position={[0, 4, -2]} intensity={1.2} color="#34d399" />
      <spotLight
        position={[0, 6, 4]}
        angle={0.45}
        penumbra={0.6}
        intensity={1.8}
        color="#e0f2fe"
      />
    </>
  );
}

type Props = {
  className?: string;
};

/** Interactive Three.js decision core for the NARNA hero. */
export default function HeroDecision3D({ className = "" }: Props) {
  return (
    <div className={`fx-r3f ${className}`.trim()} aria-hidden>
      <Canvas
        dpr={[1, 1.75]}
        camera={{ position: [0, 0.2, 5.2], fov: 42 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        style={{ width: "100%", height: "100%", background: "transparent" }}
      >
        <Suspense fallback={null}>
          <SceneLights />
          <Stars radius={40} depth={30} count={1200} factor={2.4} saturation={0.6} fade speed={0.8} />
          <DecisionCore />
        </Suspense>
      </Canvas>
      <div className="fx-r3f-label">
        <span className="fx-r3f-dot" />
        NARNA CORE · THREE.JS
      </div>
    </div>
  );
}
