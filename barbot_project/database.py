import sqlite3
import os

# Absoluter Pfad zur barbot.db im selben Verzeichnis wie diese Datei
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "barbot.db")

def get_db_connection() -> sqlite3.Connection:
    """
    Stellt eine Verbindung zur SQLite-Datenbank des BarBots her.

    :return: Das aktive Datenbank-Verbindungsobjekt.
    :rtype: sqlite3.Connection
    """
    conn: sqlite3.Connection = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_setting(schluessel: str, default: str = 'auto') -> str:
    """
    Liest eine Einstellung sicher aus der Datenbank aus.
    Gibt den 'default' Wert zurück, falls die Einstellung oder Tabelle nicht existiert.
    """
    try:
        conn = get_db_connection()
        row = conn.execute("SELECT Wert FROM Einstellungen WHERE Schluessel = ?", (schluessel,)).fetchone()
        conn.close()
        return row['Wert'] if row else default
    except Exception as e:
        print(f"[DB WARNUNG] Fehler beim Lesen der Einstellung '{schluessel}': {e}")
        return default