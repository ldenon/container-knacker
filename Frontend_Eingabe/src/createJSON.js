export function generateOrderJSON({
  selectedCountry,
  selectedRegion,
  articles,
  c20,
  c40,
  c40hc,
  c40hw
}) {
  const regionData = selectedRegion.value;

  const allContainerOptions = [
    {
      type: "20-fuß",
      inner_dimensions: { length: 5867, width: 2330, height: 2350 },
      door_dimensions: { width: 2286, height: 2261 },
      ref: c20,
      maxWeightFromRegion: regionData.twentyFoot ?? null
    },
    {
      type: "40-fuß",
      inner_dimensions: { length: 11998, width: 2330, height: 2350 },
      door_dimensions: { width: 2286, height: 2261 },
      ref: c40,
      maxWeightFromRegion: regionData.fourtyFoot ?? null
    },
    {
      type: "40-fuß-hc",
      inner_dimensions: { length: 11998, width: 2330, height: 2655 },
      door_dimensions: { width: 2286, height: 2566 },
      ref: c40hc,
      maxWeightFromRegion: regionData.fourtyFoot ?? null
    },
    {
      type: "40-fuß-hw",
      inner_dimensions: { length: 11998, width: 2330, height: 2350 },
      door_dimensions: { width: 2286, height: 2261 },
      ref: c40hw,
      maxWeightFromRegion: regionData.fourtyFoot ?? null
    }
  ];

  const container_definitions = allContainerOptions
    .filter(c => c.ref.value)
    .map(c => ({
      type: c.type,
      inner_dimensions: c.inner_dimensions,
      door_dimensions: c.door_dimensions,
      max_weight_kg: c.maxWeightFromRegion * 1000,
      tare_weight_kg: null,
      volume_m3: null,
      use: true,
      numbers: null
    }));

  const objects = articles.value.flatMap((article, idx) => {
  const quantity = article.amount || 1;
  return Array.from({ length: quantity }, (_, i) => {
    const base = {
      id: idx*1000 + 1000 + i ,
      product_name: article.name,
      category: "",
      quantity: 1,
      weight_kg: article.weight,
      constraints: {
        allow_rotation: false,
        is_stackable: true,
        max_stack_weight_kg: null,
        loading_priority: null,
        temperature_range: { min: null, max: null }
      },
      placement: {
        container_type: null,
        container_id: "",
        position: { x: null, y: null, z: null },
        rotation: { x_axis: null, y_axis: null, z_axis: null }
      }
    };

    // Neue Bedingung:
    if (article.shape === "Zylinder" && article.usesPallet) {
      // Rechteck-Form mit Palettenmaßen und kombinierten Höhe
      base.form = {
        type: "rectangle",
        length: article.palletLength,
        width: article.palletWidth,
        height: (article.height || 0) + (article.palletHeight || 0)
      };
    } else if (article.shape === "Rechteck") {
      base.form = {
        type: "rectangle",
        length: article.length,
        width: article.width,
        height: article.height
      };
    } else if (article.shape === "Zylinder") {
      base.form = {
        type: "cylinder",
        height: article.height,
        radius: article.diameter ? article.diameter / 2 : null
      };
    }

    return base;
  });
});

  const now = new Date().toISOString();

  const jsonData = {
    order: {
      order_id: "",
      delivery_country: selectedCountry.value,
      delivery_region: regionData.Region || "",
      created_at: now,
      updated_at: now,
      container_definitions,
      objects,
      loading_plan: {
        containers: [
          {
            sequence: 1,
            instance_id: "",
            container_id: "",
            type: "",
            total_weight_kg: null,
            efficiency_percent: null,
            placed_objects: [
              {
                id: null,
                stack_level: null,
                position: { x: null, y: null, z: null },
                rotation: { x_axis: null, y_axis: null, z_axis: null }
              }
            ]
          }
        ]
      }
    }
  };

  return jsonData;
}

// Neue Funktion: erzeugt JSON und startet Download
//export function exportOrderJSONToFile(params) {
//  const jsonData = generateOrderJSON(params);
//  const jsonString = JSON.stringify(jsonData, null, 2);

 // const blob = new Blob([jsonString], { type: "application/json" });
 // const url = URL.createObjectURL(blob);

  //const a = document.createElement("a");
  //a.href = url;
  //a.download = "order.json";
  //a.click();

 // URL.revokeObjectURL(url);
//}

/**
 * Erzeugt die Bestell-JSON, sendet sie per POST an einen Server und leitet bei Erfolg weiter.
 */
export async function exportOrderJSONToFile(params) {
  try {
    // 1. JSON-Daten erzeugen (wie in deinem Originalcode)
    const jsonData = generateOrderJSON(params);
    const jsonString = JSON.stringify(jsonData, null, 2);

    // 2. Daten per POST an den Server senden
    const response = await fetch('localhost:5000/api/optimize', {
      method: 'POST', // Die HTTP-Methode ist POST
      headers: {
        'Content-Type': 'application/json', // Dem Server sagen, dass wir JSON senden
      },
      body: jsonString, // Der JSON-String ist der "Körper" der Anfrage
    });

    // 3. Antwort des Servers prüfen
    if (response.ok) {
      // Wenn die Antwort erfolgreich war (z.B. Status 200 OK)
      console.log('Bestellung erfolgreich an den Server gesendet.');
      
      // 4. Weiterleitung zur Erfolgsseite
      window.location.href = 'localhost:5000/api/ladebalken';

    } else {
      // Wenn der Server einen Fehler meldet (z.B. Status 400 oder 500)
      console.error('Fehler vom Server:', response.status, response.statusText);
      // Optional: Zeige dem Benutzer eine Fehlermeldung
      alert('Es ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.');
    }
  } catch (error) {
    // Falls ein Netzwerkfehler auftritt (z.B. keine Verbindung)
    console.error('Netzwerkfehler oder anderer Fehler:', error);
    alert('Die Verbindung zum Server konnte nicht hergestellt werden.');
  }
}