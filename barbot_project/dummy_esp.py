from flask import Flask, request, jsonify, Response
from typing import Tuple, Any
import time

app: Flask = Flask(__name__)

@app.route('/fahre', methods=['POST'])
def fahre_eingang() -> Tuple[Response, int]:
    """
    Simuliert das Ansteuern der Linearachse sowie das optionale Öffnen eines Ventils.

    :return: JSON-Statusmeldung und HTTP-Status 200.
    :rtype: Tuple[flask.Response, int]
    """
    data: Any = request.get_json() or {}
    pos: int = data.get('schienen_pos', 0)  # Korrigiert von 'position' zu 'schienen_pos'
    menge: int = data.get('menge', 0)

    print("\n" + "="*50)
    print(f"[ESP HARDWARE] Befehl erhalten: LINEARACHSE ANSTEUERN")
    print(f"[ESP HARDWARE] Fahre Schlitten auf Position: {pos}")
    if menge > 0:
        print(f"[ESP HARDWARE] Oeffne Servo-Ventil fuer: {menge}ml")
    else:
        print(f"[ESP HARDWARE] Reine Leerfahrt / Heimfahrt ohne Dosierung.")
    
    time.sleep(2)  
    
    print("[ESP HARDWARE] Position erreicht und dosiert. Sende 200 OK.")
    print("="*50)
    return jsonify({"status": "done"}), 200

@app.route('/pumpe', methods=['POST'])
def pumpe_eingang() -> Tuple[Response, int]:
    """
    Simuliert das Schalten eines Last-Relais für eine spezifische Pumpe.

    :return: JSON-Statusmeldung und HTTP-Status 200.
    :rtype: Tuple[flask.Response, int]
    """
    data: Any = request.get_json() or {}
    p_nr: int = data.get('pumpen_nr', 0)
    menge: int = data.get('menge', 0)

    print("\n" + "="*50)
    print(f"[ESP HARDWARE] Befehl erhalten: RELAIS-PUMPE SCHALTEN")
    print(f"[ESP HARDWARE] Schalte Relais von Pumpe Nr.: {p_nr} EIN")
    print(f"[ESP HARDWARE] Lasse Pumpe laufen fuer: {menge}ml")
    
    time.sleep(3)  
    
    print("[ESP HARDWARE] Pumpvorgang beendet. Sende 200 OK.")
    print("="*50)
    return jsonify({"status": "done"}), 200

@app.route('/reinigen', methods=['POST'])
def reinigen_eingang() -> Tuple[Response, int]:
    """
    Simuliert das zeitgesteuerte Spülen/Reinigen mehrerer Relais-Pumpen parallel.

    **JSON-Payload-Struktur:**
    
    .. code-block:: json

        {
            "pumpen": [0, 2],
            "dauer_sekunden": 20
        }

    :return: JSON-Statusmeldung über das Ende der Reinigung und HTTP-Status 200.
    :rtype: Tuple[flask.Response, int]
    """
    data: Any = request.get_json() or {}
    pumpen: list = data.get('pumpen', [])
    dauer: int = data.get('dauer_sekunden', 20)

    print("\n" + "🧼"*15)
    print(f"[ESP HARDWARE] Reinigungsmodus aktiviert!")
    print(f"[ESP HARDWARE] Aktiviere Relais für Pumpen: {pumpen}")
    print(f"[ESP HARDWARE] Vorgang läuft blockierend für: {dauer} Sekunden...")
    
    # Simuliere die physische Dauer des Spülens
    time.sleep(dauer)
    
    print(f"[ESP HARDWARE] 📑 {len(pumpen)} Pumpe(n) erfolgreich durchgespült.")
    print("🧼"*15)
    return jsonify({"status": "cleaning_done"}), 200

@app.route('/led', methods=['POST'])
def led_eingang() -> Tuple[Response, int]:
    """
    Simuliert den Empfang von LED-Steuerbefehlen.
    """
    data: Any = request.get_json() or {}
    modus: str = data.get('modus', 'unbekannt')

    print("\n" + "💡"*15)
    print(f"[ESP HARDWARE] LED-Befehl erhalten!")
    print(f"[ESP HARDWARE] Modus: {modus}")
    
    if modus == 'einheitlich':
        r = data.get('r', 0)
        g = data.get('g', 0)
        b = data.get('b', 0)
        print(f"[ESP HARDWARE] Farbe gesetzt auf RGB: ({r}, {g}, {b})")
        
    elif modus == 'position':
        leds_top = data.get('leds_top', [])
        leds_bottom = data.get('leds_bottom', [])
        print(f"[ESP HARDWARE] Beleuchte obere LEDs: {leds_top}")
        print(f"[ESP HARDWARE] Beleuchte untere LEDs: {leds_bottom}")
        
    print("💡"*15)
    return jsonify({"status": "done"}), 200

if __name__ == '__main__':
    app.run(port=8080, debug=True)