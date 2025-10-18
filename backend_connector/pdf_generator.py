# pdf_generator.py

import io
from fpdf import FPDF

# Die Klasse LadeplanPDF bleibt unverändert
class LadeplanPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Ladeplan', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Seite {self.page_no()}', 0, 0, 'C')

def generate_packing_list_pdf(optimized_data):
    """
    Erstellt eine PDF-Ladeliste, die die hierarchische Stapelreihenfolge
    inklusive Produktnamen korrekt abbildet.
    """
    print("Generiere PDF-Ladeplan mit hierarchischer Stapel-Logik und Produktnamen...")

    try:
        pdf = LadeplanPDF()
        pdf.add_page()

        order_id = optimized_data.get("order", {}).get("order_id", "Unbekannt")
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Bestellung: {order_id}', 0, 1)
        pdf.ln(5)

        # Schritt 1: Nachschlage-Wörterbuch für Objektdetails erstellen
        all_objects = optimized_data.get("order", {}).get("objects", [])
        objects_map = {obj.get('id'): obj for obj in all_objects}

        containers = optimized_data.get("order", {}).get("loading_plan", {}).get("containers", [])
        
        for container in containers:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"Container #{container.get('sequence', 'N/A')}: {container.get('instance_id', 'N/A')} ({container.get('type', 'N/A')})", 'B', 1)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, "Hierarchische Ladereihenfolge:", 0, 1)
            
            placed_objects_list = container.get("placed_objects", [])
            
            # Schritt 2: Basis-Elemente und Stapel-Karte erstellen
            base_items = []
            stack_map = {} 

            for obj in placed_objects_list:
                parent_id = obj.get('stack_level')
                # Annahme: null, 0 oder 1 bedeutet Boden. Du kannst dies anpassen.
                if parent_id is None or parent_id in [0, 1]: 
                    base_items.append(obj)
                else:
                    if parent_id not in stack_map:
                        stack_map[parent_id] = []
                    stack_map[parent_id].append(obj)

            if not base_items and not stack_map:
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 8, "  - Kein Inhalt für diesen Container geplant.", 0, 1)
                pdf.ln(10)
                continue

            # Schritt 3: Rekursive Funktion zum Drucken der Stapel
            step_counter = [0] 

            def print_stack_recursively(parent_obj, level):
                step_counter[0] += 1
                
                obj_id = parent_obj.get("id")
                full_obj_details = objects_map.get(obj_id)
                indent = "    " * level 

                if full_obj_details:
                    obj_name = full_obj_details.get('product_name', 'Unbekanntes Produkt')
                    obj_qty = full_obj_details.get('quantity', 'N/A')
                    
                    # --- NEUE LOGIK ZUR FORMATIERUNG ---
                    
                    # Teil 1: Text vor dem Namen (normal)
                    pdf.set_font('Arial', '', 10)
                    part1 = f"{indent}{step_counter[0]}. ID {obj_id}: "
                    pdf.cell(pdf.get_string_width(part1), 8, part1, 0, 0)

                    # Teil 2: Der Produktname (fett)
                    pdf.set_font('Arial', 'B', 10) # 'B' für Bold
                    part2_bold = obj_name
                    pdf.cell(pdf.get_string_width(part2_bold), 8, part2_bold, 0, 0)
                    
                    # Teil 3: Der Rest der Zeile (wieder normal)
                    pdf.set_font('Arial', '', 10)
                    part3 = f" (Anzahl: {obj_qty})"
                    # Der letzte Teil bekommt ln=1, um zur nächsten Zeile zu springen
                    pdf.cell(0, 8, part3, 0, 1)

                if obj_id in stack_map:
                    pdf.set_font('Arial', 'I', 9)
                    pdf.cell(0, 6, f"{indent}    Darauf stapeln:", 0, 1)
                    for child_obj in stack_map[obj_id]:
                        print_stack_recursively(child_obj, level + 1)

            # Schritt 4: Die Rekursion für jedes Basis-Element starten
            for base_item in base_items:
                print_stack_recursively(base_item, 0)
            
            pdf.ln(10)

        print("PDF-Generierung abgeschlossen.")
        return io.BytesIO(pdf.output(dest='S'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None