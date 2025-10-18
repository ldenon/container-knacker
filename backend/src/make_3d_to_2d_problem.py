from ast import List
import networkx as nx
import math
import time

from pyparsing import Dict
from three_dimensional import Objekt
# Konstanten für die Beschränkung
TOP_K_BASEN = 12
TIMEOUT_SEKUNDEN = 180 # 3 Minuten


class StapelOptimierer:

    def __init__(self, objekte, max_hoehe, verbose=False):
        self.objekte = objekte
        self.max_hoehe = max_hoehe
        self.verbose = verbose
        self.graph = nx.DiGraph()
        self.erzeuge_graphen()

    def erzeuge_graphen(self):
        """Erstellt den gerichteten Abhängigkeitsgraphen."""
        self.graph.add_nodes_from(self.objekte)

        for i in range(len(self.objekte)):
            for j in range(len(self.objekte)):
                if i == j:
                    continue
                unten = self.objekte[i]
                oben = self.objekte[j]

                # Regel 1: Kann_Träger_sein_fuer muss erfüllt sein (A_oben <= A_unten)
                if unten.kann_traeger_sein_fuer(oben):
                    # Regel 2: Die Kante stellt nur einen möglichen direkten Schritt dar.
                    # Die Höhenprüfung findet im Algorithmus (DP) statt, da sie vom gesamten Pfad abhängt.
                    
                    # Kante (unten -> oben) bedeutet: Objekt 'oben' kann direkt auf 'unten' gestapelt werden
                    self.graph.add_edge(unten, oben, gewicht=oben.hoehe)
        if self.verbose:
            print("Erzeugter Stapelgraph mit Kanten:")
            for u, v, data in self.graph.edges(data=True):
                print(f"  {u.name} -> {v.name} (Gewicht: {data['gewicht']})")

# ... (Klasse Objekt und Klasse StapelOptimierer initialisierung bleibt unverändert) ...

# --------------------------------------------------------------------------------------------------
# Der DP-Schritt (finde_optimale_stapel) bleibt unverändert, da er die Basis-Informationen berechnet
# --------------------------------------------------------------------------------------------------

    def finde_optimale_stapel(self):
        # ... (print-Ausgaben des Graphen) ...
        
        # Sortierung: Absteigend nach Grundfläche (größere Objekte zuerst)
        objekte_sortiert = sorted(self.objekte, key=lambda o: o.grundflaeche, reverse=True)

        # KORREKTUR: Jedes Objekt ist initial ein Stapel der Länge 1 mit seiner eigenen Höhe.
        # DP-Speicher: Speichert (maximale_objekte, hoehe_verbraucht, nachfolger)
        optimale_stapel_info = {obj: (1, obj.hoehe, None) for obj in objekte_sortiert} 

        for i in range(len(objekte_sortiert) - 1, -1, -1):
            unten = objekte_sortiert[i]
            # Der beste Stapel muss mindestens das Objekt selbst sein (Länge 1, eigene Höhe)
            beste_folgestapelung = (1, unten.hoehe, None) 

            # Suche nach dem besten direkten Nachfolger J
            for oben in self.graph.neighbors(unten):
                anzahl_j, hoehe_j, nachfolger_j = optimale_stapel_info[oben]
                
                # Wenn der Folgestapel J die Länge 1 hat (Objekt J selbst), muss die Gesamthöhe geprüft werden.
                # Wenn der Folgestapel länger ist, ist die Höhe J bereits die Höhe des Stapels, 
                # der auf J beginnt.
                
                neue_gesamthoehe = unten.hoehe + (hoehe_j - oben.hoehe) + oben.hoehe # = unten.hoehe + hoehe_j (ist korrekt)
                
                neue_gesamthoehe = unten.hoehe + hoehe_j # (Formel ist logisch richtig, wenn hoehe_j die Höhe des Sub-Stapels ist)

                neue_anzahl = anzahl_j + 1
                
                if neue_gesamthoehe <= self.max_hoehe:
                    # Wähle den Nachfolger, der die meisten Objekte bringt
                    # oder bei gleicher Anzahl den, der flacher ist (optional, aber stabilisiert)
                    if neue_anzahl > beste_folgestapelung[0]:
                        beste_folgestapelung = (neue_anzahl, neue_gesamthoehe, oben)
                    # Optional: Bei gleicher Länge den flacheren wählen (kann die Lösung stabilisieren)
                    # elif neue_anzahl == beste_folgestapelung[0] and neue_gesamthoehe < beste_folgestapelung[1]:
                    #     beste_folgestapelung = (neue_anzahl, neue_gesamthoehe, oben)

            
            # Update des aktuellen Objekts:
            anzahl_gesamter_stapel, hoehe_gesamter_stapel, nachfolger = beste_folgestapelung
            
            optimale_stapel_info[unten] = (
                anzahl_gesamter_stapel, 
                hoehe_gesamter_stapel,
                nachfolger
            )
            # ... (Debug-Ausgaben)
        return optimale_stapel_info
# --------------------------------------------------------------------------------------------------
# ANGEPASSTER loese_problem-Schritt mit TOP-K und TIMEOUT
# --------------------------------------------------------------------------------------------------

# ... (Klasse Objekt, StapelOptimierer.__init__, _erzeuge_graphen und finde_optimale_stapel bleiben unverändert) ...

# --------------------------------------------------------------------------------------------------
# KORRIGIERTER loese_problem-Schritt mit Top-K, Timeout und disjunkter Stapelrekonstruktion
# --------------------------------------------------------------------------------------------------

    def loese_problem(self):
        """Wendet DP an und wählt gierig die Stapel aus (mit Top-K und Timeout-Beschränkung)."""
        
        start_zeit = time.time()
        
        # 1. DP-Vorbereitung
        optimale_stapel_info = self.finde_optimale_stapel()
        
        verbleibende_objekte = set(self.objekte)
        fertige_stapel = [] # Enthält die Liste der Objekt-Instanzen
        gesamt_grundflaeche = 0.0

        # Sortieren der Basis-Kandidaten nach der Effizienz: ANZAHL OBJEKTE / GRUNDFLÄCHE
        basis_kandidaten_sortiert = sorted(
            optimale_stapel_info.keys(),
            key=lambda o: optimale_stapel_info[o][0] / o.grundflaeche, # NEUES KRITERIUM
            reverse=True
        )
        
        # 2. Beschränkung auf die TOP-K=10 Basis-Kandidaten
        basis_kandidaten_begrenzt = basis_kandidaten_sortiert[:TOP_K_BASEN]
        if self.verbose:
            print(f"Beschränke die gierige Auswahl auf die Top-{TOP_K_BASEN} Stapelbasen.")

        for basis in basis_kandidaten_begrenzt:
            # 3. Timeout-Prüfung
            if time.time() - start_zeit > TIMEOUT_SEKUNDEN:
                print(f"⛔️ Timeout nach {TIMEOUT_SEKUNDEN} Sekunden erreicht. Beende gierige Stapelauswahl.")
                break 

            # Prüfe, ob die Basis noch verfügbar ist
            if basis not in verbleibende_objekte:
                continue

            # --- KORRIGIERTE STAPELREKONSTRUKTION (Iterative Verfügbarkeitsprüfung) ---
            
            aktueller_stapel = [basis]
            aktuell_hoehe = basis.hoehe
            
            # Starte die Rekonstruktion mit dem optimalen Nachfolger aus der DP-Tabelle
            _, _, naechster_knoten = optimale_stapel_info[basis]
            
            akt_knoten = naechster_knoten
            
            while akt_knoten:
                # Wichtig: Prüfe, ob das Objekt verfügbar ist UND die Höhe noch passt
                if akt_knoten in verbleibende_objekte and (aktuell_hoehe + akt_knoten.hoehe) <= self.max_hoehe:
                    
                    # Wenn verfügbar und stapelbar: Zum Stapel hinzufügen
                    aktueller_stapel.append(akt_knoten)
                    aktuell_hoehe += akt_knoten.hoehe
                    
                    # Gehe zum nächsten Knoten im optimalen DP-Pfad
                    _, _, akt_knoten = optimale_stapel_info[akt_knoten]
                else:
                    # Der DP-Pfad ist unterbrochen (Objekt verbraucht oder Höhe überschritten)
                    # Dies stellt sicher, dass Objekte nur einmal verwendet werden.
                    break 

            # Füge den Stapel zur Lösung hinzu und aktualisiere die Kosten
            fertige_stapel.append(aktueller_stapel) # Füge die Liste der Objekt-Instanzen hinzu
            gesamt_grundflaeche += basis.grundflaeche
            
            # Entferne ALLE verwendeten Objekte aus der Verfügbarkeitsmenge
            for obj in aktueller_stapel:
                verbleibende_objekte.discard(obj)
                
        # 4. Finalisierung: Verbleibende Objekte als Einzelstapel verpacken
        if verbleibende_objekte:
            print(f"⚠️ {len(verbleibende_objekte)} Objekte konnten nicht in den Top-K Stapeln verwendet werden. Sie werden als Einzelstapel verpackt.")
            for obj in verbleibende_objekte:
                 fertige_stapel.append([obj]) # [Objekt-Instanz]
                 gesamt_grundflaeche += obj.grundflaeche
        
        end_zeit = time.time()
        
        # --- KORRIGIERTE AUSGABE ---
        if self.verbose:
            print("\n--- Ergebnis ---")
            print(f"Gesamtzeit für Stapelauswahl: {end_zeit - start_zeit:.4f} Sekunden.")
            print("Gefundene Stapel:")
            for i, stapel in enumerate(fertige_stapel):
                 # KORREKTUR: Jetzt verwenden wir die Liste von Objekt-Instanzen im Stapel
                 print(f" Stapel {i+1}: {[obj.name for obj in stapel]}") 
            print(f"Gesamt genutzte Grundfläche: {gesamt_grundflaeche:.2f}")

        return fertige_stapel, gesamt_grundflaeche            

    def stapel_zu_objekten_aggregieren(self, fertige_stapel):
        """
        Aggregiert die gefundenen Stapel zu neuen, virtuellen Objekt-Instanzen.
        """
        neue_objekte = []
        
        for i, stapel in enumerate(fertige_stapel):
            # 1. Sammle alle Attribute
            basis_objekt = stapel[0]
            
            # Form- und Attributprüfung
            formen = {obj.form for obj in stapel}
            
            if len(formen) == 1 and 'Quader' in formen:
                neue_form = 'Quader' # Reiner Quader-Stapel
                # Grundfläche/Abmessungen basieren auf der Basis
                neue_flaeche = basis_objekt.grundflaeche
                neue_abmessungen = basis_objekt.abmessungen
                
            elif len(formen) == 1 and 'Zylinder' in formen:
                neue_form = 'Zylinder' # Reiner Zylinder-Stapel
                # Grundfläche/Abmessungen basieren auf der Basis
                neue_flaeche = basis_objekt.grundflaeche
                neue_abmessungen = basis_objekt.abmessungen
                
            else:
                neue_form = 'Quader' # Gemischter Stapel
                
                # Finde maximale Abmessungen (für das kleinste umschließende Rechteck)
                max_laenge = 0
                max_breite = 0

                for obj in stapel:
                    if obj.form == 'Quader':
                        max_laenge = max(max_laenge, obj.abmessungen['laenge'])
                        max_breite = max(max_breite, obj.abmessungen['breite'])
                    elif obj.form == 'Zylinder':
                        durchmesser = 2 * obj.abmessungen['radius']
                        max_laenge = max(max_laenge, durchmesser)
                        max_breite = max(max_breite, durchmesser)
                
                # Neue Grundfläche des umschließenden Rechtecks
                neue_flaeche = max_laenge * max_breite
                neue_abmessungen = {'laenge': max_laenge, 'breite': max_breite}
            
            # Allgemeine Attribute
            neuer_name = f"Stapel_{i+1}"
            neue_hoehe = sum(obj.hoehe for obj in stapel)
            neue_gewicht = sum(obj.gewicht_kg for obj in stapel) # Platzhalter: Summe der Höhen als Gewicht

            # 2. Erstellung des neuen Objekt-Containers (vereinfacht, da wir nicht alle 
            #    Ursprungs-Initialisierungsparameter haben)
            
            # Wir müssen eine Methode schaffen, um das Objekt mit den berechneten Werten zu instanziieren:
            
            # Simuliere die Initialisierung mit den berechneten Werten:
            # Wir verwenden die Basis-Initialisierung (Form/Params), aber überschreiben Flache/Abmessungen.
            
            if neue_form == 'Zylinder':
                neue_objekt_params = [neue_abmessungen['radius']]
            elif neue_form == 'Quader':
                neue_objekt_params = [neue_abmessungen['laenge'], neue_abmessungen['breite']]
            else:
                neue_objekt_params = [] # Fallback
                
            neues_objekt = Objekt(neuer_name, neue_form, neue_objekt_params, neue_hoehe, neue_gewicht)
            
            # Wichtig: Überschreibe die berechnete Grundfläche und Abmessungen,
            # falls die interne _berechne_grundflaeche Logik abweicht (besonders bei gemischten Stapeln).
            neues_objekt.grundflaeche = neue_flaeche
            neues_objekt.abmessungen = neue_abmessungen
            neues_objekt.gewicht_kg = neue_gewicht # Füge Gewicht hinzu
            
            neue_objekte.append(neues_objekt)

        return neue_objekte



# Fügen Sie die Hilfsmethode in die JSONParser Klasse im json_parser.py Codeblock ein.

# Und passen Sie die Klasse `JSONParser` mit der neuen Methode an:
# (Die Klasse ist bereits in den Codeblöcken enthalten, hier ist nur die Implementierung)

if __name__ == "__main__":
    # Beispielobjekte
    objekte = [
        Objekt("Objekt1", "Quader", [4, 4], 5, 10),
        Objekt("Objekt2", "Zylinder", [2], 3, 5),
        Objekt("Objekt3", "Quader", [3, 3], 4, 8),
        Objekt("Objekt4", "Zylinder", [1.5], 2, 3),
        Objekt("Objekt5", "Quader", [2, 2], 2, 4),
        Objekt("Objekt6", "Zylinder", [1], 1, 2)
    ]

    max_hoehe = 10

    optimierer = StapelOptimierer(objekte, max_hoehe)
    # optimierer.erzeuge_graphen()
    # graph = optimierer.graph
    stapel_loesung, gesamt_grundflaeche = optimierer.loese_problem()

    print("Gefundene Stapel:")
    for i, stapel in enumerate(stapel_loesung):
        print(f" Stapel {i+1}: {[obj.name for obj in stapel]}")
    print(f"Gesamt genutzte Grundfläche: {gesamt_grundflaeche:.2f}")
    stack_obj = optimierer.stapel_zu_objekten_aggregieren(stapel_loesung)
    print("Länge der aggregierten Objekte:", len(stack_obj))
    print("Aggregierte Objekte aus Stapeln:")
    for obj in stack_obj:
        print(f" Objekt: {obj.name}, Form: {obj.form}, Höhe: {obj.hoehe}, Gewicht: {obj.gewicht_kg}kg")