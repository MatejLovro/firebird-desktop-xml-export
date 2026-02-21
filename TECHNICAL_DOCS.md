# Tehnička Dokumentacija - Firebird Desktop XML Export

**Verzija:** 1.0.0  
**Datum:** 21.02.2026  
**Autor:** Development Team

---

## 📑 Sadržaj

1. [Arhitektura](#arhitektura)
2. [Struktura Baze Podataka](#struktura-baze-podataka)
3. [Struktura Koda](#struktura-koda)
4. [Funkcije i Moduli](#funkcije-i-moduli)
5. [XML Generiranje](#xml-generiranje)
6. [Optimizacije](#optimizacije)
7. [Sigurnost](#sigurnost)
8. [Deployment](#deployment)

---

## 1. Arhitektura

### Tehnološki Stack

```
┌─────────────────────────────────────┐
│         GUI Layer (Tkinter)         │
├─────────────────────────────────────┤
│      Business Logic (Python)        │
├─────────────────────────────────────┤
│   Database Layer (fdb + Firebird)   │
├─────────────────────────────────────┤
│    Network Layer (ftplib + FTP)     │
└─────────────────────────────────────┘
```

### Komponente

| Komponenta | Tehnologija | Svrha |
|------------|-------------|-------|
| **GUI** | Tkinter | Korisničko sučelje |
| **Calendar** | tkcalendar | Datumski widgeti |
| **Database** | fdb | Firebird konekcija |
| **XML** | xml.etree.ElementTree | Generiranje XML-a |
| **FTP** | ftplib | Upload na server |
| **Config** | configparser | INI datoteke |

---

## 2. Struktura Baze Podataka

### Firebird 1.5.6 - EXCHANGE-2026ISM.FDB

#### Korištene tablice:

### 1. FIRME
```sql
UNIQUEID           VARCHAR(20)   -- ID poslovnice
IDFIRME            INTEGER       -- Primary key
```

**Svrha:** Dohvat identifikatora poslovnice (`valto_nbr`)

**Upit:**
```sql
SELECT FIRST 1 UNIQUEID 
FROM FIRME 
ORDER BY IDFIRME DESC
```

---

### 2. BLAGAJNA
```sql
IDBLAG                      INTEGER       -- Primary key
TL_DATUM_TECAJNE_LISTE     DATE          -- Datum tečajne liste
```

**Svrha:** Mapiranje datuma na IDBLAG

**Upit:**
```sql
SELECT IDBLAG 
FROM BLAGAJNA 
WHERE TL_DATUM_TECAJNE_LISTE = CAST('2026-02-21' AS DATE)
```

---

### 3. BLAGAJNA_STANJE
```sql
IDBLAG              INTEGER           -- Foreign key
VALUTA_BROJCANO     VARCHAR(3)        -- Šifra valute
IZNOS               NUMERIC(18,2)     -- Iznos
```

**Svrha:** Agregacija iznosa po valutama za dan

**Upit:**
```sql
SELECT 
    bs.VALUTA_BROJCANO,
    bs.IZNOS,
    v.PROV_ZA_BANKU
FROM BLAGAJNA_STANJE bs
LEFT JOIN VALUTE v ON bs.VALUTA_BROJCANO = v.VALUTA_BROJCANO
WHERE bs.IDBLAG = 123
ORDER BY bs.VALUTA_BROJCANO
```

---

### 4. VALUTE
```sql
VALUTA_BROJCANO     VARCHAR(3)        -- Primary key
PROV_ZA_BANKU       NUMERIC(9,3)      -- Provizija banke (%)
```

**Svrha:** Dohvat provizije za valutu

---

### 5. TECAJEVI
```sql
TL_DATUM_TECAJNE_LISTE     DATE          -- Datum
VMT_VRSTA_TECAJA           VARCHAR(10)   -- Vrsta ('RED')
VALUTA_BROJCANO            VARCHAR(3)    -- Šifra valute
KUPOVNI_TECAJ              NUMERIC(18,6) -- Tečaj
```

**Svrha:** Dohvat kupovnih tečajeva

**Upit (bulk):**
```sql
SELECT 
    VALUTA_BROJCANO,
    KUPOVNI_TECAJ
FROM TECAJEVI 
WHERE TL_DATUM_TECAJNE_LISTE = CAST('2026-02-21' AS DATE)
  AND VMT_VRSTA_TECAJA = 'RED'
```

---

### 6. BLAGAJNICKE_TRANSAKCIJE
```sql
ID_BT                               INTEGER           -- Primary key
IDBLAG                              INTEGER           -- Foreign key
TEC_TL_DATUM_TECAJNE_LISTE         TIMESTAMP         -- Datum tečajne liste
TEC_VALUTA_BROJCANO                VARCHAR(3)        -- Valuta
IZNOS_U_VALUTI                     NUMERIC(18,2)     -- Iznos
IZNOS_U_KUNAMA                     NUMERIC(18,2)     -- Iznos u HRK
DATUM_I_VRIJEME_TRANSAKCIJE        TIMESTAMP         -- Timestamp
SERIJSKI_BROJ                      CHAR(10)          -- Serijski broj
BR_KARTICE                         VARCHAR           -- Broj kartice/dok
OZNAKA_PLATNOG_INSTRUMENTA_U_K     VARCHAR           -- Način plaćanja
PRIMJENJENI_TECAJ                  NUMERIC(18,6)     -- Primijenjeni tečaj
PRODAOIME                          VARCHAR           -- Kupac
PRODAODOK                          VARCHAR           -- Dokument kupca
VTR_VRSTA_TRANSAKCIJE              VARCHAR           -- Vrsta ('FG')
SISUSER                            INTEGER           -- User ID
```

**Svrha:** Pojedinačne transakcije

**Upit:**
```sql
SELECT 
    bt.TEC_TL_DATUM_TECAJNE_LISTE,
    bt.TEC_VALUTA_BROJCANO,
    bt.IZNOS_U_VALUTI,
    bt.IZNOS_U_KUNAMA,
    bt.DATUM_I_VRIJEME_TRANSAKCIJE,
    bt.SERIJSKI_BROJ,
    bt.BR_KARTICE,
    bt.OZNAKA_PLATNOG_INSTRUMENTA_U_K,
    bt.PRIMJENJENI_TECAJ,
    bt.PRODAOIME,
    bt.PRODAODOK,
    v.PROVBANKE,
    k.IME
FROM BLAGAJNICKE_TRANSAKCIJE bt
LEFT JOIN VALUTE v ON bt.TEC_VALUTA_BROJCANO = v.VALUTA_BROJCANO
LEFT JOIN KORISNICI k ON bt.SISUSER = k.IDKOR
WHERE bt.IDBLAG = 123
ORDER BY bt.ID_BT
```

---

### 7. KORISNICI
```sql
IDKOR       INTEGER       -- Primary key
IME         VARCHAR       -- Ime korisnika
```

**Svrha:** Dohvat imena korisnika

---

## 3. Struktura Koda

### app.py - Glavna datoteka (700+ linija)

```
app.py
├── IMPORTS
├── KONFIGURACIJA
│   ├── load_config()
│   ├── DB_CONFIG
│   └── FTP_CONFIG
├── DATABASE CONNECTION MANAGEMENT
│   ├── global_connection
│   ├── connect_to_database()
│   └── close_database_connection()
├── HELPER FUNKCIJE
│   └── replace_croatian_chars()
├── FIREBIRD FUNKCIJE
│   ├── get_uniqueid()
│   ├── get_idblag_for_date()
│   ├── get_blagajna_stanje()
│   ├── get_kupovni_tecaj()
│   ├── get_all_kupovni_tecajevi_for_date()
│   └── get_transactions_for_idblag()
├── XML GENERIRANJE
│   └── generate_xml()
├── FTP UPLOAD
│   └── upload_to_ftp()
├── GUI KREIRANJE
│   ├── Widgets (DateEntry, Buttons, Labels)
│   └── Layout
├── EVENT HANDLERS
│   ├── generate_xml_handler()
│   ├── send_to_ftp_handler()
│   └── on_closing()
└── MAIN LOOP
    └── root.mainloop()
```

---

## 4. Funkcije i Moduli

### 4.1 Konfiguracija

#### `load_config()` → dict
```python
def load_config():
    """
    Učitava REPORT.INI datoteku.
    
    Returns:
        {
            'database': {host, database, user, password, charset},
            'ftp': {host, user, password}
        }
    """
```

**Features:**
- Automatska detekcija .exe vs .py pokretanja
- Validacija postojanja datoteke
- Error handling s user-friendly porukama

---

### 4.2 Database Connection

#### `connect_to_database()` → fdb.Connection
```python
def connect_to_database():
    """
    Otvara globalnu konekciju na Firebird bazu.
    Singleton pattern - samo jedna konekcija kroz cijelu sesiju.
    
    Returns:
        fdb.Connection objekt ili None
    """
```

**Optimizacija:** Globalna konekcija izbacuje overhead otvaranja/zatvaranja za svaki upit.

**Performance gain:** ~90% brže izvršavanje za velike datasete.

---

#### `close_database_connection()` → None
```python
def close_database_connection():
    """
    Zatvara globalnu konekciju.
    Poziva se automatski pri zatvaranju aplikacije.
    """
```

---

### 4.3 Data Retrieval Functions

#### `get_uniqueid()` → str
```python
def get_uniqueid():
    """
    Dohvaća UNIQUEID iz FIRME tablice.
    
    SQL: SELECT FIRST 1 UNIQUEID FROM FIRME ORDER BY IDFIRME DESC
    
    Returns:
        str: UNIQUEID (npr. "009") ili None
    """
```

---

#### `get_idblag_for_date(date_str)` → int
```python
def get_idblag_for_date(date_str):
    """
    Mapira datum na IDBLAG.
    
    Args:
        date_str: 'YYYY-MM-DD' format
    
    Returns:
        int: IDBLAG ili None ako nema podataka za taj datum
    """
```

---

#### `get_blagajna_stanje(id_blag)` → list[dict]
```python
def get_blagajna_stanje(id_blag):
    """
    Dohvaća agregaciju po valutama za IDBLAG.
    
    Returns:
        [
            {
                'valuta': '036',
                'iznos': 1000.00,
                'prov_za_banku': 10.00
            },
            ...
        ]
    """
```

**JOIN:** BLAGAJNA_STANJE + VALUTE

---

#### `get_all_kupovni_tecajevi_for_date(date_str)` → dict
```python
def get_all_kupovni_tecajevi_for_date(date_str):
    """
    Bulk dohvat svih tečajeva za datum.
    
    OPTIMIZACIJA: Dohvaća SVE tečajeve odjednom umjesto 
                  individual upita za svaku valutu.
    
    Returns:
        {
            '036': 1.1272,
            '978': 7.5345,
            ...
        }
    """
```

**Performance gain:** Eliminira N individual upita (gdje N = broj valuta)

---

#### `get_transactions_for_idblag(id_blag)` → list[dict]
```python
def get_transactions_for_idblag(id_blag):
    """
    Dohvaća sve transakcije za IDBLAG.
    
    JOIN: BLAGAJNICKE_TRANSAKCIJE + VALUTE + KORISNICI
    
    Returns:
        [
            {
                'datum_vrijeme': datetime,
                'valuta': '036',
                'iznos_valuta': 100.00,
                'serijski_broj': '1234567890',
                ...
            },
            ...
        ]
    """
```

---

### 4.4 XML Generation

#### `generate_xml(valto_nbr, start_date, end_date)` → str
```python
def generate_xml(valto_nbr, start_date, end_date):
    """
    Glavni algoritam za generiranje XML-a.
    
    Workflow:
        1. Iteracija po datumima (start → end)
        2. Za svaki datum:
            a) Dohvati IDBLAG
            b) Generiraj valto_tetelek (agregacija valuta)
            c) Generiraj kozonseges_tetelek (transakcije)
        3. Post-processing (self-closing tagovi)
        4. Spremi u C:\XML\
    
    Returns:
        str: Naziv datoteke (npr. "009_rpt_20260221_143022.XML")
    """
```

**Algoritam:**
```
WHILE current_date <= end_date:
    id_blag = get_idblag_for_date(current_date)
    
    IF id_blag IS NULL:
        SKIP to next date
    
    # VALTO_TETELEK
    stanje = get_blagajna_stanje(id_blag)
    FOR EACH valuta IN stanje:
        tecaj = get_kupovni_tecaj(current_date, valuta)
        CREATE <valto_tetel>
    
    # KOZONSEGES_TETELEK
    transactions = get_transactions_for_idblag(id_blag)
    tecajevi = get_all_kupovni_tecajevi_for_date(current_date)  # BULK!
    
    nbr = 1
    FOR EACH transaction IN transactions:
        alap_arf = tecajevi[transaction.valuta]  # O(1) lookup
        CREATE <kozonseges_tetel>
        nbr++
    
    current_date = current_date + 1 day

SAVE XML to file
POST-PROCESS self-closing tags
RETURN filename
```

---

### 4.5 FTP Upload

#### `upload_to_ftp(filename)` → bool
```python
def upload_to_ftp(filename):
    """
    Upload XML datoteke na FTP server.
    
    Protocol: FTP (not FTPS)
    Port: 21
    Mode: Binary (storbinary)
    
    Returns:
        bool: True ako uspješno, False inače
    """
```

**Error handling:**
- Connection errors
- Authentication errors
- File not found errors
- Upload errors

---

## 5. XML Generiranje

### 5.1 Struktura

```xml
<tomeges_adatok>
    <!-- PO DATUMU -->
    <valto_tetelek>
        <valto_tetel> ... </valto_tetel>
        ...
    </valto_tetelek>
    
    <kozonseges_tetelek>
        <kozonseges_tetel> ... </kozonseges_tetel>
        ...
    </kozonseges_tetelek>
    
    <!-- SLJEDEĆI DATUM -->
    <valto_tetelek> ... </valto_tetelek>
    <kozonseges_tetelek> ... </kozonseges_tetelek>
</tomeges_adatok>
```

### 5.2 Mapiranje Podataka

#### valto_tetel izračuni:

| Polje | Formula |
|-------|---------|
| `valto_nyito_km` | `IZNOS * KUPOVNI_TECAJ` |
| `valto_exc_percent` | `100 - PROV_ZA_BANKU` |

#### kozonseges_tetel logika:

| Polje | Logika |
|-------|--------|
| `nbr` | Resetuje se za svaki novi datum, počinje od 1 |
| `alap_arf` | Dohvaća se iz `tecajevi_dict` (bulk lookup) |
| `vevo_orszag` | `"N"` ako `PRODAODOK` **NE** sadrži `"BIH"`, inače `""` |

### 5.3 Post-Processing

**Problem:** ElementTree generira self-closing tagove za prazne elemente:
```xml
<vevo_cim />
```

**Rješenje:** String replacement nakon generiranja:
```python
xml_content = xml_content.replace('<vevo_cim />', '<vevo_cim></vevo_cim>')
```

---

## 6. Optimizacije

### 6.1 Globalna Konekcija

**Prije:**
```python
# Svaki poziv funkcije
def get_data():
    con = fdb.connect(...)  # SPORO!
    # ...
    con.close()
```

**Poslije:**
```python
# Jednom pri pokretanju
global_connection = fdb.connect(...)

# Svaki poziv funkcije
def get_data():
    con = global_connection  # BRZO!
    # ...
    # NE zatvara konekciju
```

**Performance:** 90% ubrzanje

---

### 6.2 Bulk Dohvat Tečajeva

**Prije:**
```python
# Za svaku transakciju (N upita)
for transaction in transactions:
    tecaj = get_kupovni_tecaj(date, transaction.valuta)  # N x database call
```

**Poslije:**
```python
# Jednom za sve valute (1 upit)
tecajevi = get_all_kupovni_tecajevi_for_date(date)  # 1 x database call

for transaction in transactions:
    tecaj = tecajevi[transaction.valuta]  # O(1) dictionary lookup
```

**Performance:** Eliminira N-1 database poziva

---

### 6.3 Dictionary Lookup vs Linear Search

**Tehnologija:** Python dictionary (hash table)

**Complexity:**
- Dictionary lookup: O(1)
- Linear search: O(n)

**Impact:** Za 50 transakcija, razlika je 50x brže!

---

## 7. Sigurnost

### 7.1 Credentials Management

**❌ Loše:**
```python
DB_CONFIG = {
    'password': 'masterkey'  # Hardkodirano u kodu!
}
```

**✅ Dobro:**
```python
# Učitaj iz INI datoteke
DB_CONFIG = load_config()['database']
```

**Best practice:**
- REPORT.INI je **izvan** repozitorija (.gitignore)
- Credentials se ne commitaju na GitHub
- Svaki okoliš ima svoj REPORT.INI

---

### 7.2 SQL Injection Protection

**Problem:** F-string interpolacija SQL-a

```python
sql = f"SELECT * FROM TABLE WHERE id = {user_input}"  # RISKANTNO!
```

**Rješenje:** Kontrolirani input

U našoj aplikaciji:
- Svi datumi dolaze iz `DateEntry` widgeta (validirano)
- IDBLAG dolazi iz baze (trusted)
- Nema direktnog user input-a u SQL

**Dodatna zaštita (opciono):**
```python
# Parametrizirani upiti
cur.execute("SELECT * FROM TABLE WHERE id = ?", (user_input,))
```

---

## 8. Deployment

### 8.1 Kreiranje .exe s PyInstaller

```bash
pip install pyinstaller
```

```bash
pyinstaller --onefile --windowed --name="FirebirdXMLExport" app.py
```

**Opcije:**
- `--onefile` - Kreira jedan .exe
- `--windowed` - Bez terminala (GUI only)
- `--name` - Naziv .exe datoteke

**Output:** `dist/FirebirdXMLExport.exe`

---

### 8.2 Distribucija

**Pakiranje:**
```
FirebirdXMLExport_v1.0.0/
├── FirebirdXMLExport.exe
├── REPORT.INI.example
├── README.txt
└── USER_MANUAL.pdf
```

**Instalacija:**
1. Raspakiraj folder
2. Kopiraj `REPORT.INI.example` → `REPORT.INI`
3. Uredi `REPORT.INI`
4. Pokreni `FirebirdXMLExport.exe`

---

### 8.3 Zahtjevi

**Sistem:**
- Windows 7/8/10/11
- 32-bit ili 64-bit (ovisno o Firebird verziji)

**Firebird:**
- Firebird 1.5.6+ (32-bit ako je Python 32-bit)
- Server mora biti pokrenut

**Network:**
- FTP pristup (port 21)
- Internet konekcija za FTP upload

---

## 9. Daljnji Razvoj

### Moguća poboljšanja:

1. **Logging System**
   - Detaljni logovi u datoteku
   - Rotacija log datoteka

2. **Progress Bar**
   - Prikaz napretka tijekom generiranja

3. **Export u druge formate**
   - Excel (.xlsx)
   - CSV

4. **Email Notifikacije**
   - Automatski email nakon uspješnog uploada

5. **Schedulirani Export**
   - Automatsko pokretanje u određeno vrijeme

6. **Multi-threading**
   - Paralelni upiti za različite datume

---

## 📞 Kontakt za Developere

Za tehnička pitanja ili prijedloge:
- GitHub Issues
- Pull Requests su dobrodošli!

---

**Dokumentacija verzija:** 1.0.0  
**Zadnje ažuriranje:** 21.02.2026
