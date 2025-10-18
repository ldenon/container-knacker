import { useRef } from "react";

export default function Container({
  length = 5.89,
  width = 2.35,
  height = 2.3,
  thickness = 0.3,
  color = "#4a90e2",
  position,
  children,
}) {
  const geometry = useRef();
  const material = useRef();
  const containerMesh = useRef();

  return (
    <group position={position}>
      {/* Floor */}
      <mesh
        ref={containerMesh}
        position={[length / 2, thickness / 2, width / 2]}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial
          ref={material}
          color={color}
          metalness={0.8}
          roughness={0.2}
        />
        <boxGeometry ref={geometry} args={[length, thickness, width]} />
      </mesh>
      {/* Back wall */}
      <mesh
        position={[length / 2, height / 2, width + thickness / 2]}
        castShadow
      >
        <meshStandardMaterial
          ref={material}
          color={color}
          metalness={0.8}
          roughness={0.2}
        />

        <boxGeometry
          ref={geometry}
          args={[length + thickness * 2, height, thickness]}
        ></boxGeometry>
      </mesh>
      {/* Left wall */}
      <mesh position={[-(thickness / 2), height / 2, width / 2]} castShadow>
        <meshStandardMaterial
          ref={material}
          color={color}
          metalness={0.8}
          roughness={0.2}
        />

        <boxGeometry
          ref={geometry}
          args={[thickness, height, width]}
        ></boxGeometry>
      </mesh>

      {/* Right wall */}
      <mesh
        position={[length + thickness / 2, height / 2, width / 2]}
        castShadow
      >
        <meshStandardMaterial
          ref={material}
          color={color}
          metalness={0.8}
          roughness={0.2}
        />

        <boxGeometry
          ref={geometry}
          args={[thickness, height, width]}
        ></boxGeometry>
      </mesh>
      <group>{children}</group>
    </group>
  );
}
