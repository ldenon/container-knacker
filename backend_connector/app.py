import io
from flask import Flask, request, jsonify, send_file, redirect, url_for, render_template
from flask_cors import CORS

######### from my_optimizer import optimize_loading
######### from my_pdf_generator import create_pdf

def run_optimization_algorithm(data):
    """
    Optimierungsalgorithmus.
    Sie nimmt die Input-JSON (als Python-Dict) und reichert sie an.
    """
    print("Starte Optimierungsalgorithmus...")
    
    ### AUFRUF ALGO ###
    
    return None


def generate_packing_list_pdf(optimized_data):
    """
    Sie nimmt die angereicherte JSON und generiert eine PDF-Datei im Speicher.
    """
    print("Generiere PDF-Ladeplan...")
    
    # Hier kommt deine PDF-Logik (z.B. mit ReportLab oder FPDF)
    # Als einfaches Beispiel erstellen wir eine Text-Datei im Speicher
    buffer = io.BytesIO()
    
    order_id = optimized_data.get("order", {}).get("order_id", "Unbekannt")
    buffer.write(f"LADEPLAN FUER BESTELLUNG: {order_id}\n".encode('utf-8'))
    buffer.write(b"===========================================\n\n")

    for container in optimized_data.get("order", {}).get("loading_plan", {}).get("containers", []):
        buffer.write(f"CONTAINER #{container['sequence']}: {container['instance_id']} ({container['type']})\n".encode('utf-8'))
        buffer.write(b"-------------------------------------------\n")
        
        # Finde die Objekte für diesen Container
        placed_ids = [p["id"] for p in container["placed_objects"]]
        for obj in optimized_data.get("order", {}).get("objects", []):
            if obj["id"] in placed_ids:
                 buffer.write(f"  - ID {obj['id']}: {obj['product_name']} (Anzahl: {obj['quantity']})\n".encode('utf-8'))
        buffer.write(b"\n")

    print("PDF-Generierung abgeschlossen.")
    # Wichtig: Den "Cursor" des In-Memory-Files an den Anfang setzen
    buffer.seek(0)
    return buffer

# --- FLASK SERVER SETUP ---

# Initialisiere die Flask-App
app = Flask(__name__, template_folder='../Frontend Eingabe')

CORS(app)

# Definiere die API-Endpunkte (Routen)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/optimize', methods=['POST'])
def optimize_route():
    """
    Dieser Endpunkt nimmt die initialen JSON-Daten vom Frontend entgegen,
    führt den Optimierungsalgorithmus aus und gibt das Ergebnis zurück.
    """
    if not request.is_json:
        return jsonify({"error": "Anfrage muss JSON-Daten enthalten"}), 400

    initial_data = request.get_json()
    
    # Rufe deine Logik auf
    optimized_data = run_optimization_algorithm(initial_data)
    
    if optimized_data is None:
        return jsonify({"error": "Bei der Optimierung ist ein Fehler aufgetreten"}), 500
        
    return jsonify(optimized_data)


@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf_route():
    """
    Dieser Endpunkt nimmt die optimierten JSON-Daten entgegen,
    generiert ein PDF und schickt es als Datei-Download zurück.
    """
    if not request.is_json:
        return jsonify({"error": "Anfrage muss JSON-Daten enthalten"}), 400
        
    optimized_data = request.get_json()
    
    # Rufe deine PDF-Logik auf
    pdf_buffer = generate_packing_list_pdf(optimized_data)
    
    order_id = optimized_data.get("order", {}).get("order_id", "plan")
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'ladeplan_{order_id}.pdf',
        mimetype='application/pdf'
    )

# Endpunkt, der die Umleitung durchführt
#@app.route('/')
#def index():
#    return redirect(url_for('generate_pdf_route'))

if __name__ == '__main__':
    # host='0.0.0.0' macht den Server im lokalen Netzwerk erreichbar
    # debug=True startet den Server im Debug-Modus (automatische Neustarts bei Code-Änderungen)
    app.run(host='127.0.0.1', port=5000, debug=True)