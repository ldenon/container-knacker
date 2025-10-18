import json
import math
import os

# --- Konstanten für die Geometrie ---
GEOM_RECT = 0
GEOM_CIRCLE = 1

class OrderParser:
    """
    Diese Klasse lädt eine JSON-Datei mit Container- und Objektdefinitionen
    im neuen Format und extrahiert die relevanten Daten für den Pack-Algorithmus.
    """

    def __init__(self, json_filepath: str):
        """
        Initialisiert den Parser und lädt die JSON-Daten.
        """
        self.raw_data = self._load_json_data(json_filepath)
        if not self.raw_data:
            raise ValueError("JSON-Datei konnte nicht geladen werden oder hat falsches Format (erwarte 'container' und 'objects').")

        # Container-Daten extrahieren (wird von get_container_dimensions verwendet)
        self.container_data = self.raw_data.get("container")
        if not self.container_data:
            raise ValueError("Schlüssel 'container' fehlt in der JSON-Datei.")

        # Diese Liste wird vom Packer benötigt
        self.object_definitions = self._create_object_definitions()

    def _load_json_data(self, json_filepath: str) -> dict | None:
        """Lädt die JSON-Datei sicher (erwartet Root-Dictionary)."""
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Prüfe, ob die erwarteten Hauptschlüssel vorhanden sind
            if "container" in data and "objects" in data:
                return data
            else:
                print("FEHLER: JSON-Datei fehlt 'container' oder 'objects' Schlüssel auf Root-Ebene.")
                return None
        except FileNotFoundError:
            print(f"FEHLER: JSON-Datei nicht gefunden unter: {json_filepath}")
            return None
        except json.JSONDecodeError:
            print(f"FEHLER: JSON-Datei ist ungültig: {json_filepath}")
            return None

    def get_container_dimensions(self) -> tuple[float, float, float | None] | None:
        """
        Gibt die Abmessungen (Breite, Länge) UND das Maximalgewicht des Containers zurück.
        """
        if not self.container_data: # Sollte durch __init__ abgefangen werden, aber sicher ist sicher
             return None

        try:
            # Beachte: JSON 'width' -> AREA_W, JSON 'length' -> AREA_H
            area_w = float(self.container_data["width"])
            area_h = float(self.container_data["length"])
            max_weight = self.container_data.get("max_weight") # Neuer Name
            max_weight_float = float(max_weight) if max_weight is not None else None

            print(f"Verwende Container: (B: {area_w}, L: {area_h}, MaxGew: {max_weight_float if max_weight_float else 'Unbegrenzt'})")
            return (area_w, area_h, max_weight_float)

        except (KeyError, TypeError, ValueError) as e:
            print(f"FEHLER: 'container'-Daten (width, length, max_weight) sind ungültig oder fehlen. {e}")
            return None

    def _create_object_definitions(self) -> list[dict]:
        """
        Interne Funktion: Erstellt die Liste der Definitionen für die PackerEngine.
        Jedes Objekt in der JSON entspricht genau einem Packstück (quantity=1).
        """
        json_objects = self.raw_data.get("objects", [])
        definitions_list = []
        if not json_objects:
            print("WARNUNG: Keine 'objects' in der JSON gefunden.")
            return []

        sequential_id_counter = 0
        for i, obj in enumerate(json_objects): # Nutze enumerate für eindeutige ID falls name fehlt
            try:
                # Verwende 'name' als primären Identifier, fallback auf Index
                original_id = obj.get("name", f"Item_{i}")
                name = original_id # Verwende den Namen auch als Namen

                # Menge ist immer 1 in diesem Format
                anzahl = 1

                weight_val = obj.get("gewicht_kg")
                weight = float(weight_val) if weight_val is not None else 0.0

                form = obj.get("form", "").lower() # Z.B. "quader", "zylinder"
                abmessungen = obj.get("abmessungen", {})

                item_data = {
                    "original_json_id": original_id, # Verwende den Namen als ID
                    "sequential_type_id": sequential_id_counter,
                    "name": name,
                    "anzahl": anzahl,
                    "weight": weight
                }

                if form == "quader" or form == "rectangle": # Akzeptiere beides
                    w_val = abmessungen.get("breite")
                    h_val = abmessungen.get("laenge") # JSON 'laenge' ist unsere Höhe im 2D-Packen

                    if w_val is None or h_val is None:
                         print(f"WARNUNG: Objekt '{name}' (Index {i}) hat 'null' für Maße. Ignoriert.")
                         continue

                    w = float(w_val); h = float(h_val)
                    item_data.update({"geom_type": GEOM_RECT, "w_bb": w, "h_bb": h, "radius": 0.0, "area": w * h})

                elif form == "zylinder" or form == "cylinder": # Akzeptiere beides
                    r_val = abmessungen.get("radius")
                    if r_val is None:
                         print(f"WARNUNG: Objekt '{name}' (Index {i}) hat 'null' für Radius. Ignoriert.")
                         continue
                    r = float(r_val)
                    item_data.update({"geom_type": GEOM_CIRCLE, "w_bb": r * 2, "h_bb": r * 2, "radius": r, "area": math.pi * r**2})
                else:
                    print(f"WARNUNG: Objekt '{name}' (Index {i}) hat unbekannten Form-Typ '{form}'. Ignoriert.")
                    continue

                definitions_list.append(item_data)
                sequential_id_counter += 1

            except (KeyError, TypeError, ValueError) as e:
                print(f"FEHLER: Objekt an Index {i} ('{obj.get('name')}') hat ungültige Daten. Ignoriert. Fehler: {e}")

        return definitions_list

    # --- GETTER-Funktionen ---
    def get_object_definitions(self) -> list[dict]:
        """Gibt die bereinigte Liste der Objekt-Definitionen zurück."""
        return self.object_definitions

    def get_raw_data(self) -> dict:
        """Gibt die *vollständigen*, ursprünglichen JSON-Daten zurück."""
        # Renamed from get_original_order_data for clarity with new format
        return self.raw_data

    def get_type_description_map(self) -> dict:
        """ Gibt eine Map {sequential_id: {"name": ..., "geom_type": ...}} zurück. """
        type_map = {}
        for d in self.object_definitions:
             type_map[d["sequential_type_id"]] = {
                 "name": d["name"],
                 "geom_type": d["geom_type"]
             }
        return type_map