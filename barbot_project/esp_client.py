import requests
from typing import List

ESP_BASE_URL: str = "http://127.0.0.1:8080"
DEFAULT_TIMEOUT: int = 20

def steuere_pumpe(schienen_pos: int, pumpen_nr: int, menge: int) -> bool:
    """
    Sendet den Befehl an den ESP, zu einer Position zu fahren und eine Pumpe zu aktivieren.

    **Beispiel-Payload (JSON), das an /pumpe gesendet wird:**
    
    .. code-block:: json

        {
            "schienen_pos": 3,
            "pumpen_nr": 2,
            "menge": 5000
        }

    :param int schienen_pos: Die Ziel-Position auf der Schiene.
    :param int pumpen_nr: Die ID des Relais/der Pumpe.
    :param int menge: Die zu pumpende Menge (z. B. in ml oder Millisekunden).
    :return: ``True`` wenn der ESP mit Status 200 antwortet, sonst ``False``.
    :rtype: bool
    """
    payload = {"schienen_pos": schienen_pos, "pumpen_nr": pumpen_nr, "menge": menge}
    try:
        print(f"[ESP CLIENT] Sende Pumpe an {ESP_BASE_URL}/pumpe: {payload}")
        response = requests.post(f"{ESP_BASE_URL}/pumpe", json=payload, timeout=DEFAULT_TIMEOUT)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[ESP CLIENT] Verbindungsfehler: {e}")
        return False, response.status_code == 500

def fahre_zu_position(schienen_pos: int, menge: int) -> bool:
    """
    Sendet den Fahr-Befehl an den ESP (ohne Pumpenaktivierung).
    Kann genutzt werden, um eine Pause an einer bestimmten Position einzulegen.

    **Beispiel-Payload (JSON), das an /fahre gesendet wird:**

    .. code-block:: json

        {
            "schienen_pos": 5,
            "menge": 2000
        }

    :param int schienen_pos: Die Ziel-Position auf der Schiene.
    :param int menge: Menge/Dauer, die an der Position gewartet wird.
    :return: ``True`` bei Erfolg, sonst ``False``.
    :rtype: bool
    """
    payload = {"schienen_pos": schienen_pos, "menge": menge}
    try:
        print(f"[ESP CLIENT] Sende Fahrt an {ESP_BASE_URL}/fahre: {payload}")
        response = requests.post(f"{ESP_BASE_URL}/fahre", json=payload, timeout=DEFAULT_TIMEOUT)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[ESP CLIENT] Verbindungsfehler: {e}")
        return False, response.status_code == 500

def sende_heimfahrt() -> bool:
    """
    Beordert den Schlitten zurück an die Startposition (Position 0).
    Ruft intern ``fahre_zu_position(0, 0)`` auf.

    **Erzeugtes Payload (JSON):**

    .. code-block:: json

        {
            "schienen_pos": 0,
            "menge": 0
        }

    :return: ``True`` bei Erfolg, sonst ``False``.
    :rtype: bool
    """
    return fahre_zu_position(0, 0)

def starte_reinigung(pumpen: List[int], dauer_sekunden: int = 20) -> bool:
    """
    Sendet den Befehl zur Reinigung mehrerer Pumpen gleichzeitig.
    Gibt dem ESP automatisch ein längeres Timeout, da das Spülen Zeit kostet.

    **Beispiel-Payload (JSON), das an /reinigen gesendet wird:**

    .. code-block:: json

        {
            "pumpen": [1, 3, 4],
            "dauer_sekunden": 30
        }

    :param list[int] pumpen: Liste der zu reinigenden Pumpen-IDs.
    :param int dauer_sekunden: Wie lange gespült werden soll (Default: 20s).
    :return: ``True`` bei Erfolg, sonst ``False``.
    :rtype: bool
    """
    payload = {"pumpen": pumpen, "dauer_sekunden": dauer_sekunden}
    try:
        print(f"[ESP CLIENT] Sende Reinigung an {ESP_BASE_URL}/reinigen: {payload}")
        response = requests.post(f"{ESP_BASE_URL}/reinigen", json=payload, timeout=dauer_sekunden + 5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[ESP CLIENT] Verbindungsfehler: {e}")
        return False, response.status_code == 500
    
def sende_led_modus(
    modus: str, 
    position: int = None, 
    r: int = 0, 
    g: int = 0, 
    b: int = 0, 
    leds_top: list = None, 
    leds_bottom: list = None
) -> bool:
    """
    Sendet einen LED-Steuerungsbefehl an den ESP zur visuellen Statusanzeige.
    Unterstützt verschiedene Modi wie einheitliche Farben, vordefinierte Effekte oder exakte LED-Mappings.

    **Beispiel-Payload (JSON) für eine positionsabhängige LED-Steuerung:**

    .. code-block:: json

        {
            "modus": "position",
            "leds_top": [90, 91, 92, 93, 94],
            "leds_bottom": [59, 58, 57, 56, 55]
        }

    :param str modus: Der gewünschte LED-Modus (z. B. 'rainbow', 'einheitlich', 'position', 'aus', 'fertig').
    :param int position: Optional; ID oder Index der physischen Flaschenposition.
    :param int r: Rot-Wert (0-255) für den einheitlichen Farbmodus (Default: 0).
    :param int g: Grün-Wert (0-255) für den einheitlichen Farbmodus (Default: 0).
    :param int b: Blau-Wert (0-255) für den einheitlichen Farbmodus (Default: 0).
    :param list[int] leds_top: Liste der exakten LED-Indizes der oberen Reihe, die leuchten sollen.
    :param list[int] leds_bottom: Liste der exakten LED-Indizes der unteren Reihe, die leuchten sollen.
    :return: ``True`` bei erfolgreicher HTTP-Übermittlung, sonst ``False``.
    :rtype: bool
    """
    payload = {"modus": modus}
    
    if position is not None:
        payload["position"] = position
        
    if modus == 'einheitlich':
        payload["r"] = r
        payload["g"] = g
        payload["b"] = b
        
    # Die exakten LED-Nummern mitsenden
    if leds_top is not None:
        payload["leds_top"] = leds_top
    if leds_bottom is not None:
        payload["leds_bottom"] = leds_bottom
        
    try:
        print(f"[ESP CLIENT] Sende LED-Befehl an {ESP_BASE_URL}/led: {payload}")
        import requests
        response = requests.post(f"{ESP_BASE_URL}/led", json=payload, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[ESP CLIENT] LED-Verbindungsfehler: {e}")
        return False