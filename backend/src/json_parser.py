
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
from typing import Dict, Any
import os


# Load the Objekt class directly from backend/transport_objects/3dimensional.py
import importlib.util
import sys
import os
# import the Objekt class from the 3dimensional.py file
from three_dimensional import Objekt

@dataclass
class ContainerDim:
    length: float
    width: float
    height: float
    max_weight: float


class JSONParser:
    """JSON parser that returns ContainerDim and a list of Objekt instances.

    parse_order(file_path) -> (ContainerDim, List[Objekt])
    """
    def read_json(self,file_path: str) -> None:
        with open(file_path, "r", encoding="utf-8") as f:
            self.json_data =  json.load(f)
        return
    
    def get_container_dimensions(self) -> ContainerDim:
        order = self.json_data.get("order")
        containers = order.get("container_definitions", [])
        print("Number of containers:", len(containers))

        # currently we can only handle one container
        container = containers[0]
        container_height = container["inner_dimensions"]["height"]
        container_length = container["inner_dimensions"]["length"]
        container_width = container["inner_dimensions"]["width"]
        container_weight = container["max_weight_kg"]

        container_dim = ContainerDim(
            length=container_length,
            width=container_width, 
            height=container_height,
            max_weight=container_weight
            )
        return container_dim
    
    def get_objects(self) -> List[Objekt]:
        order = self.json_data.get("order")
        objects_data = order.get("objects", [])
        print("Number of objects in JSON:", len(objects_data))
        all_objects = []
        for obj in objects_data:
            quantity = obj.get("quantity", 1)
            form = obj.get("form", {})
            for i in range(quantity):
                obj_height = form.get("height", 0)
                obj_name = obj.get("product_name", "Unnamed")
                obj_name = f"{obj_name}_{i+1}"
                obj_type = form.get("type", "rectangle")
                obj_weight = obj.get("weight_kg", 0)
                objekt = None
                if str.__eq__(str(obj_type), "rectangle"):
                    # make list of params
                    params = [form.get("length", 0), form.get("width", 0)]
                    objekt = Objekt(
                    name=obj_name,
                    form="Quader",
                    params=params,
                    hoehe=obj_height,
                    gewicht_kg=obj_weight,
                    )
                    all_objects.append(objekt)
                elif str.__eq__(str(obj_type), "cylinder"):
                    radius = form.get("radius", 0)
                    params = [radius]
                    objekt = Objekt(
                    name=obj_name,
                    form="Zylinder",
                    params=params,
                    hoehe=obj_height,
                    gewicht_kg=obj_weight,
                )
                    all_objects.append(objekt)
                else:
                    raise ValueError(f"Unknown object type: Check JSON input for object", obj_type)

        return all_objects

    def object_to_dir(self, object:Objekt):
        """Convert Objekt instance to dictionary for JSON serialization."""
        obj_dir = {
            "name": object.name,
            "form": object.form,
            "hoehe": object.hoehe,
            "gewicht_kg": object.gewicht_kg,
            "grundflaeche": object.grundflaeche,
            "abmessungen": object.abmessungen,
        }
        return obj_dir
    
    def dictionary_to_json_file(self,data_dict: Dict[Any, Any], filename: str, indent: int = 4) -> None:
        """
        Schreibt ein Python Dictionary in eine JSON-Datei.

        Args:
            data_dict: Das zu speichernde Dictionary.
            filename: Der Pfad und Name der Zieldatei (z.B. "output.json").
            indent: Optionale Einrückung für eine bessere Lesbarkeit (Standard: 4 Leerzeichen).
        """
        try:
            # Öffnet die Datei im Schreibmodus ('w'). 'utf-8' Encoding ist Best Practice.
            with open(filename, 'w', encoding='utf-8') as file:
                # json.dump() schreibt das Dictionary direkt in das File-Objekt
                json.dump(data_dict, file, indent=indent, ensure_ascii=False)
            print(f"Dictionary erfolgreich in '{os.path.abspath(filename)}' gespeichert.")
        except IOError as e:
            print(f"Fehler beim Speichern der Datei: {e}")
        except TypeError as e:
            print(f"Fehler bei der JSON-Serialisierung (enthält nicht-serialisierbare Objekte): {e}")

    def create_object_list_from_stacks(self, list_of_object):
        """Create json of the following form
        {container: {width: xx, height:xx},
        objects: [
        
        ]
        }
        """
        container_dim = self.get_container_dimensions()
        container_dir = {"height": container_dim.height, "width": container_dim.width, "length": container_dim.length, "max_weight": container_dim.max_weight}
        objects_list = []
        for obj in list_of_object:
            obj_dir = self.object_to_dir(obj)
            objects_list.append(obj_dir)

        dir_gesamt = {"container": container_dir, "objects": objects_list}
        # convert to json and write to file
        path = os.path.dirname(__file__)
        output_file_path = os.path.join(path, "meine_Bestellung.json")
        self.dictionary_to_json_file(dir_gesamt, output_file_path)


    def get_stack_position(self,path)->dict:
        """
        Read json file and extract the postion of each stack.
        Args:
            path (_type_): {"stack_name": {"x": xx, "y": yy, "z": zz}, ...}
        """
        return {}


    def _get_rotated_dimensions(self, obj: Objekt|None, rotation_z_axis: int) -> dict[str, float]:
        """Gibt die dimensions (l, w, h) des Objekts nach Rotation um die Z-Achse zurück."""
        
        # Für Zylinder gibt es keine Änderung der Grundfläche bei Z-Rotation
        if obj.form == "Zylinder":
            durchmesser = 2 * obj.abmessungen['radius']
            return {"length": durchmesser, "width": durchmesser, "height": obj.hoehe}
        
        # Quader-Logik
        laenge = obj.abmessungen['laenge']
        breite = obj.abmessungen['breite']
        hoehe = obj.hoehe
        
        if rotation_z_axis == 90:
            # Bei 90 Grad Rotation um Z werden Länge und Breite vertauscht
            # (Annahme, die Höhe bleibt die Z-Dimension, L/B sind die X/Y-Dimensionen)
            return {"length": breite, "width": laenge, "height": hoehe}
        
        # Für 0 Grad Rotation (oder andere, die ignoriert werden)
        return {"length": laenge, "width": breite, "height": hoehe}

    
    def create_stack_result_json(self, stacks_list, aggregated_stack_positions) -> None:
        """
        Erstellt die finale JSON-Ausgabe mit der Position jedes Einzelobjekts im Stack.

        Args:
            stacks_list: Die Liste der Stapel (Liste von Listen der Objekt-Instanzen).
            aggregated_stack_positions: Die Platzierungen der aggregierten Stapel.
                                        Erwartetes Format: [{'name': 'Stapel_1', 'placement': {...}, ...}, ...]
        """
        container_dim = self.get_container_dimensions()
        
        container_dir = {
            "height": container_dim.height, 
            "width": container_dim.width, 
            "length": container_dim.length, 
            "max_weight": container_dim.max_weight
        }
        
        stacks_output = {}
        
        # Erstelle ein Mapping von Stapelnamen zu ihren Platzierungsinformationen
        placement_map = {d['name']: d['placement'] for d in aggregated_stack_positions}
        
        for i, stack in enumerate(stacks_list):
            stack_name = f"Stapel_{i+1}"
            stack_placement_info = placement_map.get(stack_name)
            
            if not stack_placement_info:
                print(f"⚠️ Platzierungsinformationen für {stack_name} fehlen. Überspringe diesen Stapel.")
                continue

            # Basisposition (Basiskonstanten)
            base_position_x = stack_placement_info['position']['x']
            base_position_y = stack_placement_info['position']['y']
            base_position_z = stack_placement_info['position']['z']
            
            # Rotation (wird nur für die Z-Achse berücksichtigt)
            rotation_z = stack_placement_info['rotation'].get('z_axis', 0)
            
            stack_objects = []
            current_z_offset = base_position_z # Z-Koordinate des aktuellen Objekts im Stack
            
            # ID des Objekts direkt darunter (für stack_level)
            id_unten = None 
            

    def read_placed_json_data(self, file_path: str) -> List[Dict]:
        """
        Liest die Platzierungsergebnisse der aggregierten Stapel aus einer JSON-Datei
        (z.B. 'placed.json') und gibt die Liste der Objekte zurück. 
        
        Dieses Format kann direkt an create_stack_result_json als 
        'aggregated_stack_positions' übergeben werden.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Fehler beim Einlesen der Datei {file_path}: {e}")
            return []

        # Die aggregierten Stapel (inkl. Placement) sind unter dem Schlüssel 'objects' gespeichert.
        aggregated_stacks_with_placement = data.get("objects", [])
        
        return aggregated_stacks_with_placement



if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(path, "beispiel.json")
    myParser = JSONParser()
    # myParser.read_json(json_file_path)
    # myParser.get_container_dimensions()
    # objects = myParser.get_objects()
    # print(f"Total objects parsed: {len(objects)}")
    # print first objects for verification
    # for obj in objects[:5]:
        # print(f"Object: {obj.name}, Form: {obj.form}, Hoehe: {obj.hoehe}, Gewicht: {obj.gewicht_kg}kg")
    placed_file_path = os.path.join(path, "placed.json")
    placed_data = myParser.read_placed_json_data(placed_file_path)
    print(f"Total placed stacks parsed: {len(placed_data)}")
    print("First placed stack data:", placed_data[:1])
    for d in placed_data[:1]:
        print(d["name"], d["placement"])

