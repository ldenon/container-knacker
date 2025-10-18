import networkx as nx
import math
import time

# Konstanten für die Beschränkung
TOP_K_BASEN = 3
TIMEOUT_SEKUNDEN = 120 # 2 Minuten


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
        self._erzeuge_graphen()

    def _erzeuge_graphen(self):
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
        """
        Führt den DP-basierten Greedy-Ansatz durch.
        Berechnet für jedes Objekt den längsten Stapel (max. Objekte), der es als Basis nutzt.
        """
        # Sortierung: Absteigend nach Grundfläche (größere Objekte zuerst)
        objekte_sortiert = sorted(self.objekte, key=lambda o: o.grundflaeche, reverse=True)

        # DP-Speicher: Speichert (maximale_objekte, hoehe_verbraucht, nachfolger)
        optimale_stapel_info = {obj: (0, 0, None) for obj in objekte_sortiert}

        for i in range(len(objekte_sortiert) - 1, -1, -1):
            unten = objekte_sortiert[i]
            beste_folgestapelung = (0, 0, None) # (Anzahl, Höhe, Nachfolger)

            # Suche nach dem besten direkten Nachfolger J
            for oben in self.graph.neighbors(unten):
                anzahl_j, hoehe_j, _ = optimale_stapel_info[oben]
                
                neue_gesamthoehe = unten.hoehe + hoehe_j
                neue_anzahl = anzahl_j + 1
                
                if neue_gesamthoehe <= self.max_hoehe:
                    # Wähle den Nachfolger, der die meisten Objekte bringt
                    if neue_anzahl > beste_folgestapelung[0]:
                        beste_folgestapelung = (neue_anzahl, neue_gesamthoehe, oben)
            
            # Update des aktuellen Objekts:
            anzahl_folgestapel, hoehe_folgestapel, nachfolger_folgestapel = beste_folgestapelung
            
            optimale_stapel_info[unten] = (
                1 + anzahl_folgestapel, # +1 für die Basis 'unten'
                unten.hoehe + hoehe_folgestapel,
                nachfolger_folgestapel
            )
            # print(f"Optimale Stapelinfo für {unten.name}: Anzahl={optimale_stapel_info[unten][0]}, Höhe={optimale_stapel_info[unten][1]}, Nachfolger={optimale_stapel_info[unten][2].name if optimale_stapel_info[unten][2] else 'None'}")
            
        return optimale_stapel_info

# --------------------------------------------------------------------------------------------------
# ANGEPASSTER loese_problem-Schritt mit TOP-K und TIMEOUT
# --------------------------------------------------------------------------------------------------

    def loese_problem(self):
        """Wendet DP an und wählt gierig die Stapel aus (mit Top-K und Timeout-Beschränkung)."""
        
        start_zeit = time.time()
        
        # 1. DP-Vorbereitung (die Berechnung selbst wird nicht unterbrochen)
        optimale_stapel_info = self.finde_optimale_stapel()
        
        verbleibende_objekte = set(self.objekte)
        fertige_stapel = []
        gesamt_grundflaeche = 0.0

        # Sortieren Sie die Objekte so, dass die Basen mit dem größten Potenzial (meisten Objekte) zuerst gewählt werden
        basis_kandidaten_sortiert = sorted(
            optimale_stapel_info.keys(),
            key=lambda o: optimale_stapel_info[o][0], # Sortiert nach der maximalen Objektanzahl
            reverse=True
        )
        
        # 2. ANPASSUNG: Beschränkung auf die TOP-K=10 Basis-Kandidaten
        basis_kandidaten_begrenzt = basis_kandidaten_sortiert[:TOP_K_BASEN]
        print(f"Beschränke die gierige Auswahl auf die Top-{TOP_K_BASEN} Stapelbasen.")

        for basis in basis_kandidaten_begrenzt:
            # 3. ANPASSUNG: Timeout-Prüfung
            print(f"Aktuelle Basis: {basis.name}")
            if time.time() - start_zeit > TIMEOUT_SEKUNDEN:
                print(f"⛔️ Timeout nach {TIMEOUT_SEKUNDEN} Sekunden erreicht. Beende gierige Stapelauswahl.")
                break 

            if basis not in verbleibende_objekte:
                continue

            # Baue den Stapel
            aktueller_stapel = [basis]
            # Der Stapelpfad wird direkt aus der DP-Tabelle rekonstruiert
            _, _, naechster_knoten = optimale_stapel_info[basis]
            
            akt_knoten = naechster_knoten
            while akt_knoten:
                aktueller_stapel.append(akt_knoten)
                # Aktualisiere den aktuellen Knoten im Pfad
                _, _, akt_knoten = optimale_stapel_info[akt_knoten]

            # Füge den Stapel zur Lösung hinzu und aktualisiere die Kosten
            print(f"Gefundener Stapel mit Basis {basis.name}: {[obj.name for obj in aktueller_stapel]}")
            fertige_stapel.append(aktueller_stapel)
            gesamt_grundflaeche += basis.grundflaeche
            print(f"Aktuelle Gesamtgrundfläche: {gesamt_grundflaeche:.2f}")
            
            # Entferne alle verwendeten Objekte
            for obj in aktueller_stapel:
                verbleibende_objekte.discard(obj)
                
        # 4. Finalisierung: Verbleibende Objekte als Einzelstapel verpacken
        # Dies gewährleistet eine gültige, wenn auch suboptimale, Gesamtlösung.
        if verbleibende_objekte:
            print(f"⚠️ {len(verbleibende_objekte)} Objekte konnten im Top-K / Timeout-Fenster nicht gestapelt werden. Sie werden als Einzelstapel verpackt.")
            for obj in verbleibende_objekte:
                 fertige_stapel.append([obj])
                 gesamt_grundflaeche += obj.grundflaeche
        
        end_zeit = time.time()
        print(f"Gesamtzeit für Stapelauswahl: {end_zeit - start_zeit:.2f} Sekunden.")

        return fertige_stapel, gesamt_grundflaeche    

if __name__ == "__main__":
    # Beispielobjekte
    objekte = [
        Objekt("Objekt1", "Quader", [4, 4], 5),
        Objekt("Objekt2", "Zylinder", [2], 3),
        Objekt("Objekt3", "Quader", [3, 3], 4),
        # Objekt("Objekt4", "Zylinder", [1.5], 2),
        # Objekt("Objekt5", "Quader", [2, 2], 2),
        # Objekt("Objekt6", "Zylinder", [1], 1)
    ]

    max_hoehe = 10

    optimierer = StapelOptimierer(objekte, max_hoehe)
    optimierer.erzeuge_graphen()
    graph = optimierer.graph
    # stapel_loesung, gesamt_grundflaeche = optimierer.loese_problem()

    # print("Gefundene Stapel:")
    # for i, stapel in enumerate(stapel_loesung):
        # print(f" Stapel {i+1}: {[obj.name for obj in stapel]}")
    # print(f"Gesamt genutzte Grundfläche: {gesamt_grundflaeche:.2f}")