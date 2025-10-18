import { useRef, useEffect, useState } from "react";
import { useFrame } from "@react-three/fiber";

export default function Box({
  width = 1,
  length = 1,
  height = 1,
  color,
  position = [0, 0],
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
      <boxGeometry ref={geometry} args={[length, height, width]}></boxGeometry>
      <meshStandardMaterial color={color}></meshStandardMaterial>
    </mesh>
  );
}
