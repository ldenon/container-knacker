
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
        self.dictionary_to_json_file(dir_gesamt, "output_stack.json")


if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(path, "beispiel.json")
    myParser = JSONParser()
    myParser.read_json(json_file_path)
    myParser.get_container_dimensions()
    objects = myParser.get_objects()
    print(f"Total objects parsed: {len(objects)}")
    # print first objects for verification
    for obj in objects[:5]:
        print(f"Object: {obj.name}, Form: {obj.form}, Hoehe: {obj.hoehe}, Gewicht: {obj.gewicht_kg}kg")


