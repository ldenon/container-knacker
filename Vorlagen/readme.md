# 📦 JSON-Struktur – Container- und Warenverteilung

## 🧭 Überblick

Diese JSON-Struktur dient als Grundlage für den **Workflow zur optimalen Verteilung von Waren auf Container**.  
Sie beschreibt alle relevanten Informationen zu:

- Auftrag (Order)
- Containertypen und -definitionen
- Warenobjekten (mit Maßen, Gewicht, Eigenschaften)
- Ladeplan (welches Objekt kommt in welchen Container)

Das zugehörige **JSON Schema** ermöglicht eine automatische **Validierung** und **Fehlerprüfung**.

---

## 📁 JSON-Datei – Beispielstruktur

```json
{
  "order": {
    "order_id": "",
    "delivery_country": "",
    "created_at": "",
    "updated_at": "",
    "container_definitions": [
      {
        "type": "20-fuß",
        "inner_dimensions": { "length": 5867, "width": 2330, "height": 2350 },
        "door_dimensions": { "width": 2286, "height": 2261 },
        "max_weight_kg": 28000,
        "tare_weight_kg": null,
        "volume_m3": null,
        "use": false,
        "numbers": null
      }
    ],
    "objects": [
      {
        "id": 1,
        "product_name": "",
        "category": "",
        "quantity": null,
        "weight_kg": null,
        "form": {
          "type": "rectangle",
          "length": 1200,
          "width": 800,
          "height": 1000
        },
        "constraints": {
          "allow_rotation": false,
          "is_stackable": true,
          "max_stack_weight_kg": null,
          "loading_priority": null,
          "temperature_range": { "min": null, "max": null }
        },
        "placement": {
          "container_type": null,
          "container_id": "",
          "position": { "x": null, "y": null, "z": null },
          "rotation": { "x_axis": null, "y_axis": null, "z_axis": null }
        }
      }
    ],
    "loading_plan": {
      "containers": [
        {
          "sequence": 1,
          "instance_id": "",
          "container_id": "",
          "type": "",
          "total_weight_kg": null,
          "efficiency_percent": null
        }
      ]
    }
  }
}
```

---

## ⚙️ Grundprinzipien

| Bereich | Beschreibung |
|----------|---------------|
| **order** | Enthält Metadaten zum Auftrag |
| **container_definitions** | Definition aller verfügbaren Containertypen |
| **objects** | Liste der zu verladenden Waren |
| **loading_plan** | Ergebnisbereich für die Zuordnung von Waren zu Containern |

---

## 🔢 Feldkonventionen

| Wert | Bedeutung |
|------|------------|
| `null` | Wert ist noch nicht bekannt oder nicht relevant |
| `true` / `false` | Boolesche Zustände (z. B. ob stapelbar oder drehbar) |
| numerische Werte | Maßeinheit: Millimeter (mm) bzw. Kilogramm (kg) |

---

## 📐 Container-Definitionen

Jedes Containerelement beschreibt die **Innenmaße**, **Türmaße** und **maximale Nutzlast**.  
Beispiel:

```json
{
  "type": "40-fuß-hc",
  "inner_dimensions": { "length": 11998, "width": 2330, "height": 2655 },
  "door_dimensions": { "width": 2286, "height": 2566 },
  "max_weight_kg": null,
  "tare_weight_kg": null,
  "volume_m3": null,
  "use": false,
  "numbers": null
}
```

---

## 📦 Warenobjekte

Jedes Objekt beschreibt ein Produkt mit Form, Gewicht und möglichen Einschränkungen.

**Formtypen:**
- `"rectangle"` (Standard-Kiste)
- `"cylinder"` (z. B. Rohrleitungen, Fässer)

**Constraints:**
- `allow_rotation`: darf gedreht werden?
- `is_stackable`: darf gestapelt werden?
- `max_stack_weight_kg`: wie viel Gewicht darf oben drauf liegen?
- `temperature_range`: min/max zulässige Temperatur (optional)

---

## 🧩 JSON Schema (Validierungs-Regeln)

Das Schema definiert den „Bauplan“ für die JSON-Datei.  
Speichere es als **`schema.json`** ab.

*(Schema-Inhalt siehe Chat oben – aus Platzgründen nicht dupliziert.)*

---

## 🧪 Validierung

### ✅ In **Visual Studio Code**

1. Lege `schema.json` und `order.json` im selben Ordner an.  
2. Füge in `order.json` oben ein:

   ```json
   { "$schema": "./schema.json", "order": { ... } }
   ```

3. VS Code prüft automatisch:
   - Fehlende Felder
   - Falsche Datentypen
   - Autovervollständigung

---

### ⚙️ In **Node.js**

```bash
npm install ajv
```

**validate.js:**
```js
import Ajv from "ajv";
import fs from "fs";

const ajv = new Ajv({ allErrors: true });
const schema = JSON.parse(fs.readFileSync("./schema.json", "utf8"));
const data = JSON.parse(fs.readFileSync("./order.json", "utf8"));

const validate = ajv.compile(schema);
const valid = validate(data);

if (valid) {
  console.log("✅ JSON ist gültig!");
} else {
  console.error("❌ JSON ist ungültig!");
  console.error(validate.errors);
}
```

**Ausführen:**
```bash
node validate.js
```

---

### 🐍 In **Python**

```python
import json
import jsonschema
from jsonschema import validate

with open("schema.json") as s, open("order.json") as d:
    schema = json.load(s)
    data = json.load(d)
    validate(instance=data, schema=schema)

print("✅ JSON ist gültig!")
```

---

## 📘 Fazit

✅ Einheitliche Struktur für Warenverteilung  
✅ Maschinenlesbar & erweiterbar  
✅ Automatisch validierbar  
✅ Perfekt für API-, KI- oder Optimierungs-Workflows

---

© 2025 – JSON Schema Dokumentation für Warenverteilungs-Workflow
