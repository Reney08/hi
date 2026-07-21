import os
import sqlite3

# Bestimme den exakten Ordner, in dem diese db_init.py Datei liegt
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "barbot.db")
SCHEMA_PATH = os.path.join(SCRIPT_DIR, "barbot_schema.sql")

def init_database():
    print("=" * 60)
    print("[DB-INIT] Zurueck zu SQLite: Starte BarBot Reset...")
    print("=" * 60)

    # 1. Pruefen ob die alte Datenbank existiert und diese loeschen
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"[DB-INIT] -> Alte Datei '{DB_PATH}' wurde geloescht.")
        except PermissionError:
            print(f"[DB-INIT] X FEHLER: '{DB_PATH}' blockiert!")
            print("          Bitte beende zuerst deine Flask-App (app.py).")
            print("=" * 60)
            return
        except Exception as e:
            print(f"[DB-INIT] X FEHLER beim Loeschen: {e}")
            print("=" * 60)
            return
    else:
        print("[DB-INIT] -> Keine alte Datenbank-Datei gefunden.")

    # 2. Pruefen ob das SQL-Schema existiert
    if not os.path.exists(SCHEMA_PATH):
        print(f"[DB-INIT] X FEHLER: Die Datei '{SCHEMA_PATH}' wurde nicht gefunden.")
        print("=" * 60)
        return

    # 3. Schema einlesen und in die neue DB schreiben
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Foreign Keys fuer SQLite aktivieren
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Alle SQL-Befehle ausfuehren
        cursor.executescript(schema_sql)
        
        conn.commit()
        conn.close()

        print("[DB-INIT] -> Tabellen wurden erfolgreich generiert.")
        print("[DB-INIT] -> Testdaten wurden fehlerfrei importiert.")
        print("=" * 60)
        print("[DB-INIT] ERFOLG: SQLite 'barbot.db' ist wieder einsatzbereit! ✨")
        print("=" * 60)

    except sqlite3.Error as sqlite_error:
        print(f"[DB-INIT] X SQLITE-FEHLER: {sqlite_error}")
        print("=" * 60)

if __name__ == "__main__":
    init_database()