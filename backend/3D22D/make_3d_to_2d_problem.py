import networkx as nx
import math
import time

# Konstanten für die Beschränkung
TOP_K_BASEN = 12
TIMEOUT_SEKUNDEN = 180 # 3 Minuten


class Objekt:
    def __init__(self, name, form, params, hoehe):
        self.name = name
        self.form = form  # 'Zylinder' oder 'Quader'
        self.hoehe = hoehe
        self.grundflaeche, self.abmessungen = self._berechne_grundflaeche(params)

    def _berechne_grundflaeche(self, params):
        if self.form == 'Zylinder':
            # params = [radius]
            radius = params[0]
            flaeche = math.pi * radius**2
            # Abmessungen für die Stapelprüfung (Radius)
            return flaeche, {'radius': radius}
        elif self.form == 'Quader':
            # params = [laenge, breite]
            laenge, breite = params
            flaeche = laenge * breite
            # Abmessungen für die Stapelprüfung (Seiten)
            return flaeche, {'laenge': laenge, 'breite': breite}
        return 0, {}
    
    def kann_traeger_sein_fuer(self, objekt_oben):
        """Prüft, ob 'self' als Träger für 'objekt_oben' dienen kann."""
        # 1. Stapelregel: Kleineres Objekt auf Größerem (Grundfläche darf nicht überragen)

        # Vereinfachte Annahme für die Optimierung: Nur Grundflächenvergleich (A_oben <= A_unten)
        # Für eine exakte Prüfung müsste man die Abmessungen (Radius/Länge/Breite) prüfen.
        if objekt_oben.grundflaeche > self.grundflaeche:
            return False

        # Exakte Prüfung (wichtig, da z.B. ein langer Quader nicht auf einem kleineren Zylinder stehen kann)
        # Diese komplexe Logik hängt von der genauen Definition des "Nicht-Überragens" ab
        # und wird hier vereinfacht auf A_oben <= A_unten.

        return True

    def kann_traeger_sein_fuer_no_overlap(self, objekt_oben):
        """Prüft, ob 'self' als Träger für 'objekt_oben' dienen kann."""
        # 1. Stapelregel: Kleineres Objekt auf Größerem (Grundfläche darf nicht überragen)

        # Vereinfachte Annahme für die Optimierung: Nur Grundflächenvergleich (A_oben <= A_unten)
        # Für eine exakte Prüfung müsste man die Abmessungen (Radius/Länge/Breite) prüfen.
        if objekt_oben.grundflaeche > self.grundflaeche:
            return False
        # check if the shape allows stacking -> no overlap when projected downwards
        if self.form == 'Zylinder' and objekt_oben.form == 'Zylinder':
            # Zylinder auf Zylinder
            return objekt_oben.abmessungen['radius'] <= self.abmessungen['radius']
        elif self.form == 'Quader' and objekt_oben.form == 'Quader':
            # Quader auf Quader
            return (objekt_oben.abmessungen['laenge'] <= self.abmessungen['laenge'] and
                    objekt_oben.abmessungen['breite'] <= self.abmessungen['breite'])
        elif self.form == 'Quader' and objekt_oben.form == 'Zylinder':
            # Zylinder auf Quader
            return (2 * objekt_oben.abmessungen['radius'] <= self.abmessungen['laenge'] and
                    2 * objekt_oben.abmessungen['radius'] <= self.abmessungen['breite'])
        elif self.form == 'Zylinder' and objekt_oben.form == 'Quader':
            # Quader auf Zylinder
            return (math.sqrt((objekt_oben.abmessungen['laenge']/2)**2 + (objekt_oben.abmessungen['breite']/2)**2)
                    <= self.abmessungen['radius'])
        # Exakte Prüfung (wichtig, da z.B. ein langer Quader nicht auf einem kleineren Zylinder stehen kann)
        # Diese komplexe Logik hängt von der genauen Definition des "Nicht-Überragens" ab
        # und wird hier vereinfacht auf A_oben <= A_unten.

        return True

    def __repr__(self):
        return f"Objekt('{self.name}', A={self.grundflaeche:.2f}, H={self.hoehe})"


class StapelOptimierer:

    def __init__(self, objekte, max_hoehe):
        self.objekte = objekte
        self.max_hoehe = max_hoehe
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
        print("\n--- Ergebnis ---")
        print(f"Gesamtzeit für Stapelauswahl: {end_zeit - start_zeit:.4f} Sekunden.")
        print("Gefundene Stapel:")
        for i, stapel in enumerate(fertige_stapel):
             # KORREKTUR: Jetzt verwenden wir die Liste von Objekt-Instanzen im Stapel
             print(f" Stapel {i+1}: {[obj.name for obj in stapel]}") 
        print(f"Gesamt genutzte Grundfläche: {gesamt_grundflaeche:.2f}")

        return fertige_stapel, gesamt_grundflaeche            

        
if __name__ == "__main__":
    # Beispielobjekte
    objekte = [
        Objekt("Objekt1", "Quader", [4, 4], 5),
        Objekt("Objekt2", "Zylinder", [2], 3),
        Objekt("Objekt3", "Quader", [3, 3], 4),
        Objekt("Objekt4", "Zylinder", [1.5], 2),
        Objekt("Objekt5", "Quader", [2, 2], 2),
        Objekt("Objekt6", "Zylinder", [1], 1)
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