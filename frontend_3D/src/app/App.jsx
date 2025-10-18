import { Canvas } from "@react-three/fiber";
import * as THREE from "three";
import { useState } from "react";
import Scene from "./Scene";
import { Button } from "@/components/ui/button";
import data from "@/data/data.json";

export default function App() {
  const [numItems, setNumItems] = useState(0);
  const [cameraAngle, setCameraAngle] = useState("top");
  const [selectedItem, setSelectedItem] = useState(null);

  const sortedItems = [...data.items].sort((a, b) => b.center_y - a.center_y);
  const nextItem = sortedItems[numItems];

  return (
    <div className=" p-12 h-screen grid grid-cols-3">
      <div className="col-span-1 px-6">
        <h1 className="text-sm  text-gray-500">ORDER</h1>
        <h1 className="text-2xl">ORD-2023-1027-A4B8</h1>
        <div className="mt-6">
          <h2 className="text-lg font-semibold mb-2">Camera Angles</h2>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCameraAngle("top")}
            >
              Top
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCameraAngle("front")}
            >
              Front
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCameraAngle("left")}
            >
              Left
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCameraAngle("right")}
            >
              Right
            </Button>
          </div>
        </div>
        <div className="mt-12">
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-1">
              <span>Items in Container</span>
              <span>
                {numItems} / {data.items.length}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${(numItems / data.items.length) * 100}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {data.items.length - numItems} items remaining to add
            </p>
          </div>
          <div className="flex gap-2 mt-4">
            <Button
              onClick={() =>
                setNumItems((prev) => Math.min(prev + 1, data.items.length))
              }
              disabled={numItems === data.items.length}
            >
              Next Item
            </Button>
            <Button
              onClick={() => setNumItems((prev) => Math.max(prev - 1, 0))}
              disabled={numItems === 0}
            >
              Remove item
            </Button>
            <Button
              onClick={() => setNumItems(data.items.length)}
              disabled={numItems === data.items.length}
            >
              All
            </Button>
          </div>
          {nextItem && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-sm font-medium text-blue-800">
                Next Item:
              </div>
              <div className="text-lg font-semibold text-blue-900">
                {nextItem.type_name}
              </div>
              <div className="text-sm text-blue-700">ID: {nextItem.id}</div>
            </div>
          )}

          {/* {selectedItem && (
            <div className="mt-6">
              <h2 className="text-lg font-semibold mb-2">Selected Item</h2>
              <div className="space-y-1 text-sm">
                <p>
                  <strong>Geometry:</strong> {selectedItem.geometry}
                </p>
                {selectedItem.geometry === "rectangle" && (
                  <>
                    <p>
                      <strong>Width:</strong> {selectedItem.width}
                    </p>
                    <p>
                      <strong>Height:</strong> {selectedItem.height}
                    </p>
                  </>
                )}
                {selectedItem.geometry === "circle" && (
                  <p>
                    <strong>Radius:</strong> {selectedItem.radius}
                  </p>
                )}
                <p>
                  <strong>Center X:</strong> {selectedItem.center_x}
                </p>
                <p>
                  <strong>Center Y:</strong> {selectedItem.center_y}
                </p>
              </div>
            </div>
          )} */}
        </div>
      </div>

      <Canvas
        className="col-span-2 bg-white border-1 rounded-lg"
        shadows
        camera={{ position: [-1, 10, 0], fov: 80 }}
      >
        <Scene
          numItems={numItems}
          cameraAngle={cameraAngle}
          setSelectedItem={setSelectedItem}
        />
      </Canvas>
    </div>
  );
}
