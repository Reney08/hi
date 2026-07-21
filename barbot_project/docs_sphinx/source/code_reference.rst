BarBot Entwickler-Referenz
==========================

Dieses Kapitel ist in drei Bereiche unterteilt, je nachdem, ob du am Kern-System, 
der Hardware-Kommunikation oder der Web-Oberfläche arbeitest.

1. Interne Core-Logik & Datenbank
---------------------------------
Hier werden alle internen Python-Funktionen dokumentiert, die für Datenbankabfragen, 
Berechnungen und die Verwaltung zuständig sind.

.. automodule:: app
   :members: get_db_connection, run_user_app, run_admin_app

2. ESP Hardware-Schnittstelle (API zum ESP)
-------------------------------------------
Hier sind alle internen Funktionen gebündelt, die für die Kommunikation mit dem Mikrocontroller verantwortlich sind. Das Frontend ruft diese Funktionen indirekt über die REST-API auf.

.. automodule:: esp_client
   :members:
   :undoc-members:
   :show-inheritance:

3. Web REST-API (Für Frontend & Erweiterungen)
----------------------------------------------
Hier findest du alle verfügbaren URLs, erwartete JSON-Payloads und Statuscodes für die Web-Interfaces.

**Admin-Schnittstelle (Port 1337)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoflask:: app:app_admin
   :undoc-endpoints:

**Gäste-Schnittstelle (Port 5000)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoflask:: app:app_user
   :undoc-endpoints: