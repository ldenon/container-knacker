import json
import math
import os

# --- Konstanten für die Geometrie ---
GEOM_RECT = 0
GEOM_CIRCLE = 1

class OrderParser:
    """
    Lädt eine komplexe JSON-Bestelldatei, validiert die Eingabedaten
    und stellt sie dem Pack-Algorithmus zur Verfügung.
    """

    def __init__(self, json_filepath: str):
        self.raw_order_data = self._load_json_data(json_filepath)
        if not self.raw_order_data:
            raise ValueError("JSON-Datei konnte nicht geladen werden oder 'order'-Schlüssel fehlt.")

        # Diese Liste wird vom Packer benötigt
        self.object_definitions = self._create_object_definitions()

    def _load_json_data(self, json_filepath: str) -> dict | None:
        """Lädt die JSON-Datei sicher."""
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("order")
        except FileNotFoundError:
            print(f"FEHLER: JSON-Datei nicht gefunden unter: {json_filepath}")
            return None
        except json.JSONDecodeError:
            print(f"FEHLER: JSON-Datei ist ungültig: {json_filepath}")
            return None

    # In order_parser.py, inside the OrderParser class

    def get_container_dimensions(self, container_type_name: str = None) -> tuple[float, float, float | None] | None:
        """
        Gibt die Abmessungen (Breite, Länge) UND das Maximalgewicht des
        zu verwendenden Containers zurück.

        Logik: Wählt kleinsten 'use: true' Container, wenn kein Name angegeben.
        Gibt jetzt (AREA_W, AREA_H, MAX_WEIGHT) zurück.
        """
        definitions = self.raw_order_data.get("container_definitions", [])
        if not definitions:
            print("FEHLER: Keine 'container_definitions' in der JSON gefunden.")
            return None

        target_def = None

        # 1. Explizite Anforderung
        if container_type_name:
            for container in definitions:
                if container.get("type") == container_type_name:
                    target_def = container
                    break
            if not target_def:
                print(f"WARNUNG: Angegebener Container-Typ '{container_type_name}' nicht gefunden. Starte automatische Auswahl.")

        # 2. Automatische Auswahl (Standardfall)
        if not target_def:
            usable_containers = []
            for container in definitions:
                if container.get("use", False):
                    try:
                        dims = container["inner_dimensions"]
                        w = float(dims["width"])
                        l = float(dims["length"])
                        area = w * l
                        # Speichere Container, Fläche und Gewicht
                        max_w = container.get("max_weight_kg") # Kann None sein
                        usable_containers.append((area, max_w, container))
                    except (KeyError, TypeError, ValueError):
                         print(f"WARNUNG: Container '{container.get('type')}' hat 'use: true', aber ungültige Maße. Wird ignoriert.")

            if not usable_containers:
                # 3. Fallback: Erster Container
                print("WARNUNG: Kein Container hat 'use: true'. Verwende den *ersten* Container als Fallback.")
                if not definitions: return None
                target_def = definitions[0]
            else:
                # 4. Finde den kleinsten Container
                print(f"Automatische Auswahl: {len(usable_containers)} Container mit 'use: true' gefunden. Wähle kleinsten...")
                usable_containers.sort(key=lambda x: x[0]) # Sortiere nach Fläche
                min_area, selected_max_weight, smallest_container = usable_containers[0]
                target_def = smallest_container
                print(f"Kleinster 'use: true'-Container ausgewählt: '{target_def.get('type')}' (Fläche: {min_area})")

        # 5. Extrahiere Maße UND Gewicht
        try:
            dims = target_def["inner_dimensions"]
            area_w = float(dims["width"])
            area_h = float(dims["length"])
            # Hole max_weight_kg, konvertiere zu float falls nicht None
            max_weight = target_def.get("max_weight_kg")
            max_weight_float = float(max_weight) if max_weight is not None else None

            print(f"Verwende Container-Typ: '{target_def.get('type')}' (B: {area_w}, L: {area_h}, MaxGew: {max_weight_float if max_weight_float else 'Unbegrenzt'})")
            # --- WICHTIGE ÄNDERUNG HIER: Gibt 3 Werte zurück ---
            return (area_w, area_h, max_weight_float) # <<<<< MUST RETURN 3 VALUES

        except (KeyError, TypeError, ValueError) as e:
            print(f"FEHLER: 'inner_dimensions'/'max_weight_kg' im final ausgewählten Container '{target_def.get('type')}' sind ungültig. {e}")
            return None

    def _create_object_definitions(self) -> list[dict]:
        """Interne Funktion: Erstellt die Liste der Definitionen inkl. Gewicht."""
        json_objects = self.raw_order_data.get("objects", [])
        definitions_list = []
        if not json_objects:
            print("WARNUNG: Keine 'objects' in der JSON-Bestellung gefunden.")
            return []

        sequential_id_counter = 0
        for obj in json_objects:
            try:
                original_id = int(obj.get("id", -1))
                name = obj.get("product_name", f"Item {original_id}")
                anzahl = int(obj.get("quantity", 0))
                weight_val = obj.get("weight_kg")
                weight = float(weight_val) if weight_val is not None else 0.0

                if anzahl <= 0: continue

                form = obj.get("form", {})
                form_type = form.get("type")

                item_data = {
                    "original_json_id": original_id,
                    "sequential_type_id": sequential_id_counter,
                    "name": name,
                    "anzahl": anzahl,
                    "weight": weight
                }

                if form_type == "rectangle":
                    w_val = form.get("width"); h_val = form.get("length")
                    if w_val is None or h_val is None:
                         print(f"WARNUNG: Objekt '{name}' (ID {original_id}) hat 'null' für Maße. Ignoriert.")
                         continue
                    w = float(w_val); h = float(h_val)
                    item_data.update({"geom_type": GEOM_RECT, "w_bb": w, "h_bb": h, "radius": 0.0, "area": w * h})
                elif form_type == "cylinder":
                    r_val = form.get("radius")
                    if r_val is None:
                         print(f"WARNUNG: Objekt '{name}' (ID {original_id}) hat 'null' für Radius. Ignoriert.")
                         continue
                    r = float(r_val)
                    item_data.update({"geom_type": GEOM_CIRCLE, "w_bb": r * 2, "h_bb": r * 2, "radius": r, "area": math.pi * r**2})
                else:
                    print(f"WARNUNG: Objekt '{name}' (ID {original_id}) hat unbekannten Form-Typ '{form_type}'. Ignoriert.")
                    continue

                definitions_list.append(item_data)
                sequential_id_counter += 1

            except (KeyError, TypeError, ValueError) as e:
                print(f"FEHLER: Objekt-ID {obj.get('id')} hat ungültige Daten. Ignoriert. Fehler: {e}")

        return definitions_list

    # --- GETTER-Funktionen ---
    def get_object_definitions(self) -> list[dict]:
        """Gibt die bereinigte Liste der Objekt-Definitionen zurück."""
        return self.object_definitions

    def get_original_order_data(self) -> dict:
        """Gibt die *vollständigen*, ursprünglichen JSON-Daten zurück."""
        return self.raw_order_data

    def get_type_description_map(self) -> dict:
        """ Gibt eine Map {sequential_id: {"name": ..., "geom_type": ...}} zurück. """
        type_map = {}
        for d in self.object_definitions:
             type_map[d["sequential_type_id"]] = {
                 "name": d["name"],
                 "geom_type": d["geom_type"]
             }
        return type_map