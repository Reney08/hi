from flask import Blueprint, render_template, request, jsonify, Response, send_from_directory
import sqlite3
import os
from typing import Tuple, Any

import esp_client
from database import get_db_connection, get_setting

# Blueprint erstellen
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def admin_index() -> Tuple[str, int]:
    return render_template('index.html'), 200

@admin_bp.route('/database_content')
def database_content() -> Tuple[str, int]:
    conn: sqlite3.Connection = get_db_connection()
    try:
        cocktails_list = conn.execute('SELECT * FROM Cocktail').fetchall()
        zutaten_list = conn.execute('''
            SELECT z.ZutatID, z.Name, z.Verfuegbar, zs.SchienenPos, zs.Pumpe, zs.PumpenNR 
            FROM Zutat z
            LEFT JOIN Zapfstelle zs ON z.Zapfstelle = zs.ZapfstelleID
        ''').fetchall()
        zapfstellen_list = conn.execute('SELECT * FROM Zapfstelle').fetchall()
    except sqlite3.OperationalError as e:
        conn.close()
        return f"<h3>Datenbank-Fehler: {e}</h3>", 500
    
    conn.close()
    return render_template('database.html', cocktails=cocktails_list, zutaten=zutaten_list, zapfstellen=zapfstellen_list), 200

@admin_bp.route('/admin/cocktails')
def admin_cocktails() -> Tuple[str, int]:
    conn: sqlite3.Connection = get_db_connection()
    cocktails_list = conn.execute('SELECT * FROM Cocktail').fetchall()
    conn.close()
    return render_template('admin_cocktails.html', cocktails=cocktails_list), 200

@admin_bp.route('/admin/zutaten')
def admin_zutaten() -> Tuple[str, int]:
    conn: sqlite3.Connection = get_db_connection()
    zutaten_list = conn.execute('''
        SELECT z.ZutatID, z.Name, z.Alkohol, z.Verfuegbar, zs.SchienenPos, zs.Pumpe, zs.PumpenNR 
        FROM Zutat z
        LEFT JOIN Zapfstelle zs ON z.Zapfstelle = zs.ZapfstelleID
    ''').fetchall()
    conn.close()
    return render_template('admin_zutaten.html', zutaten=zutaten_list), 200

@admin_bp.route('/admin/zapfstellen')
def admin_zapfstellen() -> Tuple[str, int]:
    conn: sqlite3.Connection = get_db_connection()
    zapfstellen_list = conn.execute('SELECT * FROM Zapfstelle').fetchall()
    conn.close()
    return render_template('admin_zapfstellen.html', zapfstellen=zapfstellen_list), 200

@admin_bp.route('/admin/rezepte')
def admin_rezepte() -> Tuple[str, int]:
    try:
        conn = get_db_connection()
        query = """
            SELECT r.RezeptID, r.CocktailID, r.ZutatID, r.Menge, r.RezeptPos,
                   c.Name AS CocktailName, z.Name AS ZutatName
            FROM Rezept r
            JOIN Cocktail c ON r.CocktailID = c.CocktailID
            JOIN Zutat z ON r.ZutatID = z.ZutatID
            ORDER BY c.Name ASC, r.RezeptPos ASC
        """
        rezepte = conn.execute(query).fetchall()
        conn.close()
        return render_template('admin_rezepte.html', rezepte=rezepte), 200
    except Exception as e:
        return f"<div style='color:red; padding:20px;'>Fehler: {str(e)}</div>", 500

@admin_bp.route('/admin/reinigung')
def admin_reinigung() -> Tuple[str, int]:
    conn: sqlite3.Connection = get_db_connection()
    query = """
        SELECT zs.ZapfstelleID, zs.PumpenNR, zs.SchienenPos, z.Name AS ZutatName
        FROM Zapfstelle zs
        LEFT JOIN Zutat z ON zs.ZapfstelleID = z.Zapfstelle
        WHERE zs.Pumpe = 1
        ORDER BY zs.PumpenNR ASC
    """
    pumpen_list = conn.execute(query).fetchall()
    conn.close()
    return render_template('admin_reinigung.html', pumpen=pumpen_list), 200

@admin_bp.route('/api/toggle_availability', methods=['POST'])
def toggle_availability() -> Tuple[Response, int]:
    data: Any = request.get_json()
    if not data or 'type' not in data or 'id' not in data:
        return jsonify({"status": "error", "message": "Parameter fehlen."}), 400
    item_type, item_id = data['type'], data['id']
    conn = get_db_connection()
    if item_type == 'cocktail':
        conn.execute('UPDATE Cocktail SET Verfuegbar = Verfuegbar ^ 1 WHERE CocktailID = ?', (item_id,))
    elif item_type == 'zutat':
        conn.execute('UPDATE Zutat SET Verfuegbar = Verfuegbar ^ 1 WHERE ZutatID = ?', (item_id,))
    else:
        conn.close()
        return jsonify({"status": "error", "message": "Ungueltiger Typ."}), 400
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200

@admin_bp.route('/api/admin/list/<string:item_type>', methods=['GET'])
def api_admin_list(item_type: str):
    if item_type not in ['Cocktail', 'Zutat', 'Zapfstelle', 'Rezept']:
        return jsonify({'status': 'error', 'message': 'Ungültiger Tabellentyp'}), 400
    try:
        conn = get_db_connection()
        rows = conn.execute(f"SELECT * FROM {item_type}").fetchall()
        conn.close()
        return jsonify({'status': 'success', 'data': [dict(r) for r in rows]}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/admin/get/<string:item_type>/<int:item_id>', methods=['GET'])
def api_admin_get(item_type: str, item_id: int):
    if item_type not in ['Cocktail', 'Zutat', 'Zapfstelle', 'Rezept']:
        return jsonify({'status': 'error', 'message': 'Ungültiger Tabellentyp'}), 400
    try:
        conn = get_db_connection()
        row = conn.execute(f"SELECT * FROM {item_type} WHERE {item_type}ID = ?", (item_id,)).fetchone()
        conn.close()
        if row is None:
            return jsonify({'status': 'error', 'message': 'Eintrag nicht gefunden'}), 404
        return jsonify({'status': 'success', 'data': dict(row)}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/admin/save', methods=['POST'])
def api_admin_save():
    data = request.get_json() or {}
    item_type = data.get('type')
    item_id = data.get('id')
    if item_type not in ['Cocktail', 'Zutat', 'Zapfstelle', 'Rezept']:
        return jsonify({'status': 'error', 'message': 'Ungültiger Typ'}), 400
    try:
        conn = get_db_connection()
        if item_type == 'Cocktail':
            name, verfuegbar = data.get('Name'), data.get('Verfuegbar', 1)
            if item_id:
                conn.execute("UPDATE Cocktail SET Name = ?, Verfuegbar = ? WHERE CocktailID = ?", (name, verfuegbar, item_id))
            else:
                conn.execute("INSERT INTO Cocktail (Name, Verfuegbar) VALUES (?, ?)", (name, verfuegbar))
        elif item_type == 'Zutat':
            name, alkohol, verfuegbar, zapfstelle = data.get('Name'), data.get('Alkohol', 0), data.get('Verfuegbar', 1), data.get('Zapfstelle')
            if item_id:
                conn.execute("UPDATE Zutat SET Name = ?, Alkohol = ?, Verfuegbar = ?, Zapfstelle = ? WHERE ZutatID = ?", (name, alkohol, verfuegbar, zapfstelle, item_id))
            else:
                conn.execute("INSERT INTO Zutat (Name, Alkohol, Verfuegbar, Zapfstelle) VALUES (?, ?, ?, ?)", (name, alkohol, verfuegbar, zapfstelle))
        elif item_type == 'Zapfstelle':
            schienen_pos, pumpe, pumpen_nr = data.get('SchienenPos', 0), data.get('Pumpe', 0), data.get('PumpenNR')
            if item_id:
                conn.execute("UPDATE Zapfstelle SET SchienenPos = ?, Pumpe = ?, PumpenNR = ? WHERE ZapfstelleID = ?", (schienen_pos, pumpe, pumpen_nr, item_id))
            else:
                conn.execute("INSERT INTO Zapfstelle (SchienenPos, Pumpe, PumpenNR) VALUES (?, ?, ?)", (schienen_pos, pumpe, pumpen_nr))
        elif item_type == 'Rezept':
            cocktail_id, zutat_id, menge, rezept_pos = data.get('CocktailID'), data.get('ZutatID'), data.get('Menge'), data.get('RezeptPos')
            if item_id:
                conn.execute("UPDATE Rezept SET CocktailID = ?, ZutatID = ?, Menge = ?, RezeptPos = ? WHERE RezeptID = ?", (cocktail_id, zutat_id, menge, rezept_pos, item_id))
            else:
                if not rezept_pos:
                    rezept_pos = conn.execute("SELECT COUNT(*) FROM Rezept WHERE CocktailID = ?", (cocktail_id,)).fetchone()[0] + 1
                conn.execute("INSERT INTO Rezept (CocktailID, ZutatID, Menge, RezeptPos) VALUES (?, ?, ?, ?)", (cocktail_id, zutat_id, menge, rezept_pos))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Gespeichert!'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/admin/delete', methods=['POST'])
def api_admin_delete():
    data = request.get_json() or {}
    item_type, item_id = data.get('type'), data.get('id')
    if item_type not in ['Cocktail', 'Zutat', 'Zapfstelle', 'Rezept'] or not item_id:
        return jsonify({'status': 'error', 'message': 'Fehlerhafte Parameter'}), 400
    try:
        conn = get_db_connection()
        conn.execute(f"DELETE FROM {item_type} WHERE {item_type}ID = ?", (item_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Eintrag gelöscht!'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/api/admin/reinigen', methods=['POST'])
def api_admin_reinigen() -> Tuple[Response, int]:
    data: Any = request.get_json()
    if not data or 'pumpen' not in data:
        return jsonify({"status": "error", "message": "Keine Pumpen ausgewählt."}), 400
        
    selected_pumps = data['pumpen']
    erfolg = esp_client.starte_reinigung(selected_pumps, dauer_sekunden=20)
    
    if not erfolg:
        return jsonify({"status": "error", "message": "Hardware meldet Fehler oder ESP nicht erreichbar."}), 500
        
    return jsonify({"status": "success", "message": "Reinigungszyklus erfolgreich beendet!"}), 200

@admin_bp.route('/docs/')
@admin_bp.route('/docs/<path:filename>')
def docs(filename: str = 'index.html') -> Response:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_path = os.path.join(base_dir, 'docs_sphinx', 'build', 'html')
    return send_from_directory(docs_path, filename)

@admin_bp.route('/admin/led', methods=['GET'])
def admin_led_view():
    """
    Liefert die LED-Steuerungsseite aus.
    Gibt nur das reine HTML-Snippet zurück, damit es nahtlos in die SPA passt.
    """
    # Hole aktuelle Einstellungen für die Vorauswahl im UI
    aktueller_modus = get_setting('led_modus', 'rainbow')
    color_str = get_setting('led_color', '0,0,255')
    
    return render_template('admin_led_snippet.html', modus=aktueller_modus, color=color_str)

@admin_bp.route('/api/admin/led', methods=['POST'])
def api_admin_led() -> Tuple[Response, int]:
    """Schaltet den globalen LED-Modus um."""
    data = request.get_json() or {}
    modus = data.get('modus')
    
    if modus not in ['rainbow', 'auto', 'aus', 'einheitlich']:
        return jsonify({'status': 'error', 'message': 'Ungültiger LED-Modus'}), 400
        
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO Einstellungen (Schluessel, Wert) VALUES ('led_modus', ?)", (modus,))
    
    # Wenn einheitlich gewählt wurde, speichern wir die RGB-Werte zusätzlich ab
    if modus == 'einheitlich':
        r = int(data.get('r', 0))
        g = int(data.get('g', 0))
        b = int(data.get('b', 0))
        
        # Farbe als "R,G,B" String in die DB schreiben
        color_str = f"{r},{g},{b}"
        conn.execute("INSERT OR REPLACE INTO Einstellungen (Schluessel, Wert) VALUES ('led_color', ?)", (color_str,))
        conn.commit()
        conn.close()
        
        erfolg = esp_client.sende_led_modus('einheitlich', r=r, g=g, b=b)
    else:
        conn.commit()
        conn.close()
        
        # Bei Auto oder Rainbow starten wir den Regenbogen, bei Aus schalten wir ab
        if modus == 'auto' or modus == 'rainbow':
            erfolg = esp_client.sende_led_modus('rainbow')
        else:
            erfolg = esp_client.sende_led_modus('aus')
            
    if not erfolg:
        return jsonify({'status': 'error', 'message': 'LED-Modus in DB gespeichert, aber ESP offline.'}), 500
        
    return jsonify({'status': 'success', 'message': f'LED-Modus erfolgreich auf {modus} gesetzt.'}), 200

@admin_bp.route('/led_content', methods=['GET'])
def led_content_snippet():
    """
    Liefert das reine LED-Steuerungs-Snippet für die Hauptseite (SPA) aus.
    Liest alle aktuellen Werte live aus der Datenbank.
    """
    # 1. Aktuellen LED-Modus holen (Fallback: 'rainbow')
    aktueller_modus = get_setting('led_modus', 'rainbow')
    
    # 2. Aktuelle einheitliche Farbe holen (Fallback: Blau '0,0,255')
    aktuelle_farbe = get_setting('led_color', '0,0,255')
    
    # 3. Aktuelle Regenbogen-Geschwindigkeit holen (Fallback: 50)
    # Da get_setting meist Strings liefert, konvertieren wir es hier für den Slider sicherheitshalber in eine Zahl
    try:
        geschwindigkeit = int(get_setting('led_speed', '50'))
    except (ValueError, TypeError):
        geschwindigkeit = 50

    # Rendert das überarbeitete Snippet und übergibt alle Parameter an Jinja2
    return render_template(
        'admin_led_snippet.html', 
        modus=aktueller_modus, 
        color=aktuelle_farbe, 
        geschwindigkeit=geschwindigkeit
    )