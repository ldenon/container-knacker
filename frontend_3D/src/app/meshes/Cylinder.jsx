import { useRef, useEffect, useState } from "react";
import { useFrame } from "@react-three/fiber";

export default function Cylinder({
  radius = 0.5,
  height = 1,
  color,
  position,
  delay = 0,
  animationDuration = 0.5,
  onItemClick,
}) {
  const geometry = useRef();
  const meshRef = useRef();
  const [started, setStarted] = useState(false);
  const [animProgress, setAnimProgress] = useState(0);

  useEffect(() => {
    // Décale la géométrie de moitié de sa taille
    geometry.current.translate(0, 0.5, 0);
  }, []);

  useFrame((state, delta) => {
    if (!started) {
      if (state.clock.elapsedTime > delay) {
        setStarted(true);
      }
    } else if (animProgress < 1) {
      setAnimProgress((prev) => Math.min(prev + delta / animationDuration, 1));
    }
  });

  return (
    <mesh
      ref={meshRef}
      position={[position[0], 0.3, position[1] - 10 * (1 - animProgress)]}
      castShadow
      onPointerDown={(e) => {
        e.stopPropagation();
        onItemClick();
      }}
    >
      <cylinderGeometry
        ref={geometry}
        args={[radius, radius, height]}
      ></cylinderGeometry>
      <meshStandardMaterial color={color}></meshStandardMaterial>
    </mesh>
  );
}
