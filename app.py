import json

from backend_connector.pdf_generator import generate_packing_list_pdf
from flask import Flask, request, jsonify, send_file, redirect, url_for, render_template
from flask_cors import CORS

######### from my_optimizer import optimize_loading

# --- FLASK SERVER SETUP ---

# Initialisiere die Flask-App
app = Flask(__name__)

CORS(app)

# Definiere die API-Endpunkte (Routen)

@app.route('/')
def index():
    return render_template('./Frontend_Eingabe/index.html')

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
    #optimized_data = run_optimization_algorithm(initial_data)
    optimized_data = initial_data

    
    print()
    if optimized_data is None:
        return jsonify({"error": "Bei der Optimierung ist ein Fehler aufgetreten"}), 500
        
        # JSON-Datei lokal speichern
    with open('optimized_output.json', 'w', encoding='utf-8') as f:
        json.dump(optimized_data, f, ensure_ascii=False, indent=4)

    # Optional: nur Bestätigung zurücksenden
    return {"status": "gespeichert"}, 200

@app.route('/api/ladebalken')
def routeToLadebalken():
    
    # Gibt ladebalken.html aus dem templates-Ordner zurück
    return send_file('./backend_connector/ladebalken.html')

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf_route():
    if not request.is_json:
        return jsonify({"error": "Anfrage muss JSON-Daten enthalten"}), 400
        
    optimized_data = request.get_json()
    
    pdf_buffer = generate_packing_list_pdf(optimized_data)
    
    if pdf_buffer is None:
        return jsonify({"error": "PDF konnte nicht erstellt werden"}), 500
    
    order_id = optimized_data.get("order", {}).get("order_id", "plan")
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f'ladeplan_{order_id}.pdf',
        mimetype='application/pdf'
    )

# Endpunkt, der die Umleitung durchführt
# Z. B. /api/3d-view?order_id=ORD-123&container_id=C1-40HC-01.
@app.route('/api/3d-view')
def routeTo3d():
    order_id_param = request.args.get('order_id')
    full_redirect_url = f"http://localhost:3000/{order_id_param}"
    
    if not order_id_param:
        return jsonify({"error": "Fehlende Parameter 'order_id' oder 'container_id'"}), 400
    
    return redirect(url_for(full_redirect_url))

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
    
