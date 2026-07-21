-- BarbotDB: Table Definitions (SQLite kompatibel)

CREATE TABLE IF NOT EXISTS Cocktail (
    CocktailID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR(30),
    Beschreibung VARCHAR(250),
    ExtLink VARCHAR(200),
    Bild BLOB,
    Verfuegbar INTEGER DEFAULT 1 -- 1 = Aktiv, 0 = Gesperrt
);

CREATE TABLE IF NOT EXISTS Zapfstelle (
    ZapfstelleID INTEGER PRIMARY KEY AUTOINCREMENT,
    SchienenPos INT,
    Pumpe TINYINT,
    PumpenNR INT,
    Fuellmenge INT
);

CREATE TABLE IF NOT EXISTS Zutat (
    ZutatID INTEGER PRIMARY KEY AUTOINCREMENT,
    Zapfstelle INT,
    Name VARCHAR(30),
    Alkohol TINYINT,
    Verfuegbar INTEGER DEFAULT 1,
    FOREIGN KEY (Zapfstelle) REFERENCES Zapfstelle(ZapfstelleID)
);

CREATE TABLE IF NOT EXISTS Rezept (
    RezeptID INTEGER PRIMARY KEY AUTOINCREMENT,
    CocktailID INT,
    ZutatID INT,
    RezeptPos INT,
    Menge INT,
    FOREIGN KEY (CocktailID) REFERENCES Cocktail(CocktailID),
    FOREIGN KEY (ZutatID) REFERENCES Zutat(ZutatID)
);

CREATE TABLE IF NOT EXISTS Einstellungen (
    Schluessel TEXT PRIMARY KEY,
    Wert TEXT
);

-- 1. Insert Cocktails
INSERT INTO Cocktail (Name, Beschreibung, ExtLink, Bild, Verfuegbar) VALUES
('Vodka Sunrise', 'Vodka mit Orangensaft', 'https://example.com/vodka-sunrise', NULL, 1),
('Gin Tonic',     'Gin mit Tonic Water',   'https://example.com/gin-tonic', NULL, 1),
('Bacardi Cola',  'Bacardi mit Cola',      'https://example.com/bacardi-cola', NULL, 1),
('Tequila Fanta', 'Tequila mit Fanta',     'https://example.com/tequila-fanta', NULL, 1),
('Korn Sprite',   'Korn mit Sprite',       'https://example.com/korn-sprite', NULL, 1);

-- 2. Insert Zapfstelle
INSERT INTO Zapfstelle (SchienenPos, Pumpe, PumpenNR, Fuellmenge) VALUES
(25,    0, NULL, 1000),   -- 1: Vodka
(525,   0, NULL, 1000),   -- 2: Tequila
(1025,  0, NULL, 1000),   -- 3: Bacardi
(1525,  0, NULL, 1000),   -- 4: Rum
(2025,  0, NULL, 1000),   -- 5: Korn
(2525,  0, NULL, 1000),   -- 6: Gin
(3025,  1, 0,    1000),   -- 7: Cola
(3025,  1, 1,    1000),   -- 8: Orangensaft
(3025,  1, 2,    1000),   -- 9: Bananensaft
(3025,  1, 3,    1000),   -- 10: Ananassaft
(3025,  1, 4,    1000),   -- 11: Tonic Water
(3025,  1, 5,    1000),   -- 12: Fanta
(3025,  1, 6,    1000);   -- 13: Sprite

-- 3. Insert Zutat
INSERT INTO Zutat (Zapfstelle, Name, Alkohol, Verfuegbar) VALUES
(1,  'Vodka',        1, 1),
(2,  'Tequila',      1, 1),
(3,  'Bacardi',      1, 1),
(4,  'Rum',          1, 1),
(5,  'Korn',         1, 1),
(6,  'Gin',          1, 1),
(7,  'Cola',         0, 1),
(8,  'Orangensaft',  0, 1),
(9,  'Bananensaft',  0, 1),
(10, 'Ananassaft',   0, 1),
(11, 'Tonic Water',  0, 1),
(12, 'Fanta',        0, 1),
(13, 'Sprite',       0, 1);

-- 4. Insert Rezept
INSERT INTO Rezept (CocktailID, ZutatID, RezeptPos, Menge) VALUES
(1, 1, 1, 40),   
(1, 8, 2, 100),  
(2, 6, 1, 40),   
(2, 11, 2, 100), 
(3, 3, 1, 40),   
(3, 7, 2, 100),  
(4, 2, 1, 40),   
(4, 12, 2, 100), 
(5, 5, 1, 40),   
(5, 13, 2, 100);

-- 5. Insert default Einstellungen
INSERT OR IGNORE INTO Einstellungen (Schluessel, Wert) VALUES ('led_modus', 'rainbow');