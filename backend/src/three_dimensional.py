
import math


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
