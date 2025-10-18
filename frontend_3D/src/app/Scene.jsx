import * as THREE from "three";
import { memo, useRef, forwardRef, useEffect, useState, useMemo } from "react";
import Box from "./meshes/Box";
import Container from "./meshes/Container";
import Cylinder from "./meshes/Cylinder";
import { CameraControls } from "@react-three/drei";
import { useThree } from "@react-three/fiber";
import data from "@/data/data.json";
import { log } from "three/tsl";

const { DEG2RAD } = THREE.MathUtils;

function getRandomColor() {
  let letters = "0123456789ABCDEF";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

export default function Scene({ numItems, cameraAngle, setSelectedItem }) {
  const cameraControlsRef = useRef();

  const { camera } = useThree();

  const itemColors = useMemo(() => data.items.map(() => getRandomColor()), []);

  // Configurable animation speed variables
  const animationSpeed = 0.5; // seconds per item delay
  const animationDuration = 0.5; // seconds for slide animation

  useEffect(() => {
    if (cameraControlsRef.current) {
      const containerLength = data.container.width / 100;
      const containerWidth = data.container.height / 100;
      const targetX = containerLength / 2;
      const targetY = 0.15; // thickness / 2
      const targetZ = containerWidth / 2;

      switch (cameraAngle) {
        case "top":
          cameraControlsRef.current.setPosition(targetX, 7, targetZ, true);
          break;
        case "front":
          cameraControlsRef.current.setPosition(targetX, 5, targetZ - 7, true);
          break;
        case "left":
          cameraControlsRef.current.setPosition(targetX - 7, 5, targetZ, true);
          break;
        case "right":
          cameraControlsRef.current.setPosition(targetX + 7, 5, targetZ, true);
          break;
        default:
          cameraControlsRef.current.setPosition(targetX, 7, targetZ, true);
      }
      cameraControlsRef.current.setTarget(targetX, targetY, targetZ, true);
    }
  }, [cameraAngle]);

  const getContainerMeshes = (data) => {
    const sortedItems = data.items.sort((a, b) => b.center_y - a.center_y);
    const items = sortedItems.slice(0, numItems).map((item, index) => {
      if (item.geometry == "rectangle")
        return (
          <Box
            key={index}
            color={itemColors[data.items.indexOf(item)]}
            length={item.width / 100}
            width={item.height / 100}
            position={[item.center_x / 100, item.center_y / 100]}
            delay={index * animationSpeed}
            animationDuration={animationDuration}
            onItemClick={() => {
              setSelectedItem(item);
            }}
          ></Box>
        );
      if (item.geometry == "circle")
        return (
          <Cylinder
            key={index}
            color={itemColors[data.items.indexOf(item)]}
            radius={item.radius / 100}
            position={[item.center_x / 100, item.center_y / 100]}
            delay={index * animationSpeed}
            animationDuration={animationDuration}
            onItemClick={() => {
              setSelectedItem(item);
            }}
          ></Cylinder>
        );
    });

    return (
      <Container
        width={data.container.height / 100}
        length={data.container.width / 100}
      >
        {items}
      </Container>
    );
  };

  return (
    <>
      <color attach="background" args={["#f0f0f0"]} />
      <fog attach="fog" args={["#f0f0f0", 20, 50]} />
      <ambientLight intensity={0.6} />
      <directionalLight
        position={[5, 10, 5]}
        intensity={1.5}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-far={50}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
      />
      <directionalLight position={[-5, 5, -5]} intensity={0.5} />
      <pointLight position={[0, 10, 0]} intensity={0.8} />

      <mesh
        receiveShadow
        position={[0, -0.05, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <planeGeometry args={[50, 50]} />
        <meshStandardMaterial color="#e0e0e0" />
      </mesh>

      {getContainerMeshes(data)}

      <group>
        <CameraControls ref={cameraControlsRef} />
      </group>
    </>
  );
}
