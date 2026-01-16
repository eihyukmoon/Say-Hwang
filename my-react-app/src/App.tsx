import { Canvas } from "@react-three/fiber"
import { OrbitControls, useGLTF } from "@react-three/drei"
import { Suspense } from "react"

function LionHead() {
  const { scene } = useGLTF("/lion_head_4k.gltf/lion_head_4k.gltf")
  return <primitive object={scene} scale={5} />
}

export default function App() {
  return (
    <div style={{ height: "100vh", position: "relative" }}>
      {/* 3D 씬 */}
      <Canvas camera={{ position: [0, 1, 4] }}>
        <ambientLight intensity={0.8} />
        <directionalLight position={[5, 5, 5]} intensity={1.2} />

        <Suspense fallback={null}>
          <LionHead />
        </Suspense>

        <OrbitControls />
      </Canvas>

      {/* 프론트 UI */}
      <div
        style={{
          position: "absolute",
          top: 20,
          left: 20,
          padding: "12px 16px",
          background: "rgba(0,0,0,0.6)",
          color: "white",
          borderRadius: 8,
          fontSize: 18,
        }}
      >
        안녕하세요
      </div>
    </div>
  )
}

useGLTF.preload("/lion_head_4k.gltf/lion_head_4k.gltf")
