from flask import Blueprint, render_template, request, jsonify, Response
import sqlite3
from typing import Tuple, Any, Dict

import esp_client
from database import get_db_connection, get_setting

# Blueprint erstellen
user_bp = Blueprint('user', __name__)

# Globaler Zustand für den aktuellen Mixvorgang
active_order: Dict[str, Any] = {
    "is_mixing": False,
    "steps": [],
    "current_index": 0
}

led_mapping = {
    "Pos1": { "top-row": [78, 79, 80, 81, 82], "bottom-row": [71, 70, 69, 68, 67] },
    "Pos2": { "top-row": [84, 85, 86, 87, 88], "bottom-row": [65, 64, 63, 62, 61] },
    "Pos3": { "top-row": [90, 91, 92, 93, 94], "bottom-row": [59, 58, 57, 56, 55] },
    "Pos4": { "top-row": [96, 97, 98, 99, 100], "bottom-row": [53, 52, 51, 50, 49] },
    "Pos5": { "top-row": [102, 103, 104, 105, 106], "bottom-row": [47, 46, 45, 44, 43] },
    "Pos6": { "top-row": [108, 109, 110, 111, 112], "bottom-row": [41, 40, 39, 38, 37] },
    "Pumps": { "top-row": [111, 112, 113, 114, 115], "bottom-row": [38, 37, 36, 35, 34] }
}

@user_bp.route('/')
def index() -> Tuple[str, int]:
    """Rendert die Haupt-Rahmenseite für Gäste (SPA Shell)."""
    return render_template('index_user.html'), 200

@user_bp.route('/home_content')
def home_content() -> Tuple[str, int]:
    """Rendert die dynamischen Willkommens-Inhalte für die Startseite."""
    return render_template('home.html'), 200

@user_bp.route('/cocktails')
def cocktails() -> Tuple[str, int]:
    """Rendert die Cocktail-Auswahlseite anhand der Datenbank."""
    conn: sqlite3.Connection = get_db_connection()
    query = '''
        SELECT * FROM Cocktail 
        WHERE Verfuegbar = 1 
        AND CocktailID NOT IN (
            SELECT r.CocktailID 
            FROM Rezept r
            JOIN Zutat z ON r.ZutatID = z.ZutatID
            WHERE z.Verfuegbar = 0
        )
    '''
    try:
        cocktails_list = conn.execute(query).fetchall()
    except sqlite3.OperationalError as e:
        conn.close()
        return f"<h3>Datenbank-Fehler: {e}. Bitte db_init.py ausfuehren!</h3>", 500
        
    conn.close()
    return render_template('cocktails.html', cocktails=cocktails_list), 200

@user_bp.route('/finished')
def finished() -> Tuple[str, int]:
    """Rendert die Erfolgsseite nach einem beendeten Mixvorgang."""
    return render_template('finished.html'), 200

@user_bp.route('/api/order', methods=['POST'])
def order_cocktail():
    global active_order
    if active_order["is_mixing"]:
        return jsonify({"status": "error", "message": "Es läuft bereits ein Mixvorgang."}), 400

    data = request.get_json() or {}
    cocktail_id = data.get("cocktail_id")

    conn = get_db_connection()
    schritte = conn.execute("""
        SELECT 
            z.ZutatID, 
            r.Menge, 
            zs.SchienenPos, 
            zs.Pumpe, 
            zs.PumpenNR
        FROM Rezept r
        JOIN Zutat z ON r.ZutatID = z.ZutatID
        JOIN Zapfstelle zs ON z.Zapfstelle = zs.ZapfstelleID
        WHERE r.CocktailID = ?
        ORDER BY zs.Pumpe ASC, zs.SchienenPos ASC
    """, (cocktail_id,)).fetchall()

    if not schritte:
        conn.close()
        return jsonify({"status": "error", "message": "Cocktail hat keine Zutaten oder existiert nicht."}), 404

    # LED-Modus für den Mixvorgang umschalten
    aktueller_modus = get_setting('led_modus', 'rainbow')
    conn.execute("INSERT OR REPLACE INTO Einstellungen (Schluessel, Wert) VALUES ('led_modus_vorher', ?)", (aktueller_modus,))
    conn.execute("INSERT OR REPLACE INTO Einstellungen (Schluessel, Wert) VALUES ('led_modus', 'auto')")
    conn.commit()
    conn.close()

    # Mix-Auftrag im Speicher registrieren
    active_order = {
        "is_mixing": True,
        "current_index": 0,
        "steps": [dict(s) for s in schritte]
    }

    # 💡 NEU: LEDs für den ALLERERSTEN Schritt (Index 0) sofort einschalten!
    erster_schritt = active_order["steps"][0]
    if erster_schritt['Pumpe'] == 1:
        pos_key = "Pumps"
    else:
        pos_key = f"Pos{erster_schritt['SchienenPos']}"
        
    mapping = led_mapping.get(pos_key)
    if mapping:
        try:
            esp_client.sende_led_modus(
                modus='position', 
                leds_top=mapping['top-row'], 
                leds_bottom=mapping['bottom-row']
            )
            print(f"[LED START] Erste Position ({pos_key}) erfolgreich ausgeleuchtet.")
        except Exception as e:
            print(f"[WARNUNG] Erster LED-Befehl schlug fehl: {e}")

    return jsonify({"status": "started"}), 200

@user_bp.route('/api/next_step', methods=['GET'])
def next_step():
    global active_order
    if not active_order["is_mixing"]:
        return jsonify({"status": "error", "message": "Kein aktiver Mixvorgang."}), 400
    
    try:
        # 1. Fall: Alle Schritte beendet -> Heimfahrt & LED Reset
        if active_order["current_index"] >= len(active_order["steps"]):
            erfolg = esp_client.sende_heimfahrt()
            
            # --- NEU: Alten LED-Modus wiederherstellen ---
            alter_modus = get_setting('led_modus_vorher', 'rainbow')
            conn = get_db_connection()
            conn.execute("INSERT OR REPLACE INTO Einstellungen (Schluessel, Wert) VALUES ('led_modus', ?)", (alter_modus,))
            conn.commit()
            conn.close()
            
            # Sende den alten Modus an den ESP (Fehler werden ignoriert)
            try:
                if alter_modus == 'aus':
                    esp_client.sende_led_modus('aus')
                elif alter_modus == 'einheitlich':
                    color_str = get_setting('led_color', '0,0,255')
                    r, g, b = map(int, color_str.split(','))
                    esp_client.sende_led_modus('einheitlich', r=r, g=g, b=b)
                else:
                    # Regenbogen als Fallback
                    esp_client.sende_led_modus('rainbow')
            except Exception as e:
                print(f"[WARNUNG] LED Wiederherstellung ignoriert: {e}")
                
            if not erfolg:
                active_order["is_mixing"] = False
                return jsonify({"status": "error", "message": "Hardware-Fehler bei Heimfahrt."}), 500

            active_order["is_mixing"] = False
            return jsonify({"status": "finished"}), 200

        # 2. Fall: Normaler Mix-Schritt
        schritt = active_order["steps"][active_order["current_index"]]
        
        # LED-Position sicher senden (Ignoriert Abstürze) ---
        # Wir wissen, dass der Modus jetzt 'auto' ist, da wir ihn in /api/order gesetzt haben.
        if schritt['Pumpe'] == 1:
            pos_key = "Pumps"
        else:
            pos_key = f"Pos{schritt['SchienenPos']}"
            
        mapping = led_mapping.get(pos_key)
        if mapping:
            try:
                esp_client.sende_led_modus(
                    modus='position', 
                    leds_top=mapping['top-row'], 
                    leds_bottom=mapping['bottom-row']
                )
            except Exception as e:
                print(f"[WARNUNG] LED-Senden schlug fehl, mixen geht trotzdem weiter. Grund: {e}")

        # --- Hardware-Befehle ausführen ---
        if schritt['Pumpe'] == 1:
            erfolg = esp_client.steuere_pumpe(schritt['SchienenPos'], schritt['PumpenNR'], schritt['Menge'])
        else:
            erfolg = esp_client.fahre_zu_position(schritt['SchienenPos'], schritt['Menge'])

        if not erfolg:
            active_order["is_mixing"] = False
            return jsonify({"status": "error", "message": "Fehler bei der Hardware-Kommunikation."}), 500

        active_order["current_index"] += 1
        return jsonify({"status": "mixing", "current_step": schritt}), 200

    except Exception as e:
        # 🔥 NOTFALL-ABBRUCH: Greift bei JEDEM Fehler im try-Block!
        print(f"\n🚨 [CRITICAL] Mixvorgang wegen Fehler abgebrochen! Grund: {e}")
        
        # System sofort wieder freigeben und aufräumen
        quit_and_reset_mixvorgang(erfolgreich=False)
        
        return jsonify({
            "status": "error", 
            "message": f"Mixvorgang abgebrochen wegen Systemfehler: {str(e)}"
        }), 500
        
def quit_and_reset_mixvorgang(erfolgreich: bool = True):
    """
    Hilfsfunktion, die das System unter allen Umständen in einen sicheren,
    konsistenten Zustand zurückbringt und für die nächste Bestellung freigibt.
    """
    global active_order
    print(f"[CLEANUP] Setze System zurück. Status: {'Erfolg' if erfolgreich else 'Abbruch'}")
    
    # 1. Alten LED-Modus aus der DB holen und wiederherstellen
    try:
        alter_modus = get_setting('led_modus_vorher', 'rainbow')
        conn = get_db_connection()
        conn.execute("INSERT OR REPLACE INTO Einstellungen (Schluessel, Wert) VALUES ('led_modus', ?)", (alter_modus,))
        conn.commit()
        conn.close()
        
        # Befehl an den ESP senden
        if alter_modus == 'aus':
            esp_client.sende_led_modus('aus')
        elif alter_modus == 'einheitlich':
            color_str = get_setting('led_color', '0,0,255')
            r, g, b = map(int, color_str.split(','))
            esp_client.sende_led_modus('einheitlich', r=r, g=g, b=b)
        else:
            esp_client.sende_led_modus('rainbow' if erfolgreich else 'einheitlich', r=255, g=0, b=0) # Rot bei Fehler!
    except Exception as led_err:
        print(f"[CLEANUP WARNUNG] LED-Reset fehlgeschlagen: {led_err}")

    # 2. Hardware in die Heimatposition schicken
    try:
        esp_client.sende_heimfahrt()
    except Exception as hw_err:
        print(f"[CLEANUP CRITICAL] Heimfahrt konnte nicht gesendet werden: {hw_err}")

    # 3. WICHTIGSTES ELEMENT: Zustand auf jeden Fall zurücksetzen!
    active_order = {
        "is_mixing": False,
        "current_index": 0,
        "steps": []
    }