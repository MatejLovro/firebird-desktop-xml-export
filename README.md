# Firebird Desktop XML Export

Desktop aplikacija za export blagajničkih transakcija iz Firebird baze podataka u XML format i automatski FTP upload.

![Python](https://img.shields.io/badge/python-3.x-blue.svg)
![Firebird](https://img.shields.io/badge/firebird-1.5.6-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 📋 Sadržaj

- [Pregled](#pregled)
- [Funkcionalnosti](#funkcionalnosti)
- [Tehnologije](#tehnologije)
- [Instalacija](#instalacija)
- [Konfiguracija](#konfiguracija)
- [Korištenje](#korištenje)
- [XML Struktura](#xml-struktura)
- [Troubleshooting](#troubleshooting)
- [Autor](#autor)

---

## 🎯 Pregled

Aplikacija omogućava:
- Dohvaćanje blagajničkih transakcija iz Firebird 1.5.6 baze
- Generiranje XML datoteka prema specificiranoj strukturi
- Automatski FTP upload na server
- Iteraciju po datumima s nested XML strukturom

---

## ✨ Funkcionalnosti

### Glavne funkcionalnosti:
- ✅ **Grafičko sučelje (Tkinter)** - jednostavno za korištenje
- ✅ **Odabir datumskog perioda** - kalendar widgeti
- ✅ **Validacija unosa** - provjera datumskih raspona
- ✅ **Globalna konekcija na bazu** - brzo izvršavanje bez smrzavanja
- ✅ **Iteracija po datumima** - svaki datum generira par valto_tetelek + kozonseges_tetelek
- ✅ **Dinamički izračuni** - automatski izračun kupovnih tečajeva i iznosa
- ✅ **FTP upload** - automatsko slanje na server
- ✅ **INI konfiguracija** - lako upravljanje postavkama

### Napredne funkcionalnosti:
- 🔹 Optimizacija SQL upita (bulk dohvat tečajeva)
- 🔹 Post-processing XML-a (self-closing tag konverzija)
- 🔹 Zamjena hrvatskih dijakritičkih znakova
- 🔹 Logika za vevo_orszag (BIH provjera)
- 🔹 Smart enable/disable kontrola dugmadi

---

## 🛠 Tehnologije

### Python biblioteke:
```
fdb                 # Firebird database driver
tkcalendar          # Calendar widget for Tkinter
tkinter             # GUI framework (built-in)
ftplib              # FTP upload (built-in)
configparser        # INI file parsing (built-in)
xml.etree.ElementTree  # XML generation (built-in)
```

### Baza podataka:
- **Firebird 1.5.6** - `EXCHANGE-2026ISM.FDB`
- **7 tablica**: FIRME, BLAGAJNA, BLAGAJNA_STANJE, VALUTE, TECAJEVI, BLAGAJNICKE_TRANSAKCIJE, KORISNICI

### Platforma:
- **Python 3.x (32-bit)** - kompatibilnost s Firebird 1.5.6
- **Windows** - primary target OS

---

## 📦 Instalacija

### 1. Klonirajte repozitorij:
```bash
git clone https://github.com/YOUR_USERNAME/firebird-desktop-xml-export.git
cd firebird-desktop-xml-export
```

### 2. Instalirajte potrebne pakete:
```bash
pip install fdb tkcalendar
```

**VAŽNO:** Koristite **32-bit Python** ako je vaš Firebird 32-bit!

### 3. Kreirajte konfiguracijsku datoteku:
Kopirajte `REPORT.INI.example` u `REPORT.INI` i uredite postavke:

```ini
[DATABASE]
database=C:/EXCHBIH/EXCHANGE-2026ISM.FDB
host=localhost
user=SYSDBA
password=masterkey

[FTP]
host=ftp.ekonto.hr
user=your_username@example.com
password=your_password
```

### 4. Pokrenite aplikaciju:
```bash
python app.py
```

---

## ⚙️ Konfiguracija

### REPORT.INI struktura:

#### [DATABASE] sekcija:
| Parametar | Opis | Primjer |
|-----------|------|---------|
| `database` | Puna putanja do Firebird baze | `C:/EXCHBIH/EXCHANGE-2026ISM.FDB` |
| `host` | Database host | `localhost` |
| `user` | Database korisnik | `SYSDBA` |
| `password` | Database lozinka | `masterkey` |

#### [FTP] sekcija:
| Parametar | Opis | Primjer |
|-----------|------|---------|
| `host` | FTP server adresa | `ftp.ekonto.hr` |
| `user` | FTP korisničko ime | `user@example.com` |
| `password` | FTP lozinka | `your_password` |

### Lokacija XML datoteka:
- **Output folder:** `C:\XML\`
- **Format naziva:** `{valto_nbr}_rpt_{YYYYMMDD_HHMMSS}.XML`
- **Primjer:** `009_rpt_20260221_143022.XML`

---

## 🚀 Korištenje

### Korak po korak:

1. **Pokrenite aplikaciju:**
   ```bash
   python app.py
   ```

2. **Odaberite datumski period:**
   - Početni datum (default: danas)
   - Završni datum (default: danas)
   - **Validacija:** Završni datum mora biti ≥ početnom datumu

3. **Generirajte XML:**
   - Kliknite dugme **"Generiraj XML"**
   - Aplikacija će:
     - Spojiti se na bazu
     - Dohvatiti UNIQUEID (valto_nbr)
     - Iterirati po datumima
     - Generirati XML datoteku
     - Spremiti u `C:\XML\`

4. **Pošaljite na server:**
   - Kliknite dugme **"Pošalji XML na server"**
   - Aplikacija će uploadati datoteku na FTP server
   - Prikaže potvrdu uspješnog slanja

5. **Ponovite proces:**
   - Nakon uspješnog slanja, dugmad se resetiraju
   - Možete generirati novi XML

---

## 📊 XML Struktura

### Nested struktura po datumima:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<tomeges_adatok>
  
  <!-- DATUM 1 -->
  <valto_tetelek>
    <valto_tetel>
      <valto_datum>2026-02-04</valto_datum>
      <valto_nbr>009</valto_nbr>
      <valto_valuta>036</valto_valuta>
      <valto_nyito>100.00</valto_nyito>
      <valto_nyito_km>112.72</valto_nyito_km>
      <valto_exc_percent>90.00</valto_exc_percent>
      <valto_bank_percent>10.00</valto_bank_percent>
    </valto_tetel>
    <!-- više valuta... -->
  </valto_tetelek>
  
  <kozonseges_tetelek>
    <kozonseges_tetel>
      <nbr>1</nbr>
      <datum>2026-02-04 10:30:00</datum>
      <valto>009</valto>
      <felhasznalo>Ime Prezime</felhasznalo>
      <tranzakcio>1234567890</tranzakcio>
      <dokumentumszam>DOC-001</dokumentumszam>
      <valuta>036</valuta>
      <fiz_mod>CASH</fiz_mod>
      <ertek>100.00</ertek>
      <akt_arf>1.1272</akt_arf>
      <alap_arf>1.1272</alap_arf>
      <bank_arf>10.00</bank_arf>
      <honnan_hova></honnan_hova>
      <vevo_kod>Kupac d.o.o.</vevo_kod>
      <vevo_cim></vevo_cim>
      <vevo_utlevel_id>HR12345</vevo_utlevel_id>
      <vevo_orszag>N</vevo_orszag>
    </kozonseges_tetel>
    <!-- više transakcija... -->
  </kozonseges_tetelek>
  
  <!-- DATUM 2 -->
  <valto_tetelek>
    <!-- ... -->
  </valto_tetelek>
  
  <kozonseges_tetelek>
    <!-- ... -->
  </kozonseges_tetelek>
  
</tomeges_adatok>
```

### Mapiranje podataka:

#### valto_tetel (agregacija po valutama):
| XML Tag | Izvor | Opis |
|---------|-------|------|
| `valto_datum` | Datum iteracije | YYYY-MM-DD format |
| `valto_nbr` | FIRME.UNIQUEID | Poslovnica ID |
| `valto_valuta` | BLAGAJNA_STANJE.VALUTA_BROJCANO | Šifra valute |
| `valto_nyito` | BLAGAJNA_STANJE.IZNOS | Iznos u valuti |
| `valto_nyito_km` | IZNOS * KUPOVNI_TECAJ | Iznos u kunama |
| `valto_exc_percent` | 100 - PROV_ZA_BANKU | Mjenjački postotak |
| `valto_bank_percent` | VALUTE.PROV_ZA_BANKU | Bankarski postotak |

#### kozonseges_tetel (pojedinačne transakcije):
| XML Tag | Izvor | Opis |
|---------|-------|------|
| `nbr` | Brojač (resetuje se svaki datum) | Redni broj transakcije |
| `datum` | DATUM_I_VRIJEME_TRANSAKCIJE | YYYY-MM-DD HH:MM:SS |
| `valto` | FIRME.UNIQUEID | Poslovnica ID |
| `felhasznalo` | KORISNICI.IME | Ime korisnika |
| `tranzakcio` | SERIJSKI_BROJ | Serijski broj |
| `dokumentumszam` | BR_KARTICE | Broj dokumenta |
| `valuta` | TEC_VALUTA_BROJCANO | Šifra valute |
| `fiz_mod` | OZNAKA_PLATNOG_INSTRUMENTA_U_K | Način plaćanja |
| `ertek` | IZNOS_U_VALUTI | Iznos |
| `akt_arf` | PRIMJENJENI_TECAJ | Primijenjeni tečaj |
| `alap_arf` | TECAJEVI.KUPOVNI_TECAJ | Kupovni tečaj |
| `bank_arf` | PROVBANKE | Provizija |
| `vevo_kod` | PRODAOIME | Kupac |
| `vevo_utlevel_id` | PRODAODOK | Dokument kupca |
| `vevo_orszag` | Logika: "N" ako PRODAODOK ne sadrži "BIH" | Država |

---

## 🔧 Troubleshooting

### Problem: "Cannot connect to database"
**Rješenje:**
- Provjerite da li je Firebird server pokrenut
- Provjerite putanju u `REPORT.INI`
- Provjerite korisničko ime i lozinku
- Koristite 32-bit Python ako je Firebird 32-bit

### Problem: "FTP upload failed"
**Rješenje:**
- Provjerite internet konekciju
- Provjerite FTP credentials u `REPORT.INI`
- Provjerite da li je FTP server dostupan
- Provjerite firewall postavke

### Problem: "Završni datum ne može biti manji od početnog"
**Rješenje:**
- Odaberite završni datum koji je jednak ili veći od početnog datuma

### Problem: "Nema transakcija u periodu"
**Rješenje:**
- Provjerite da li postoje transakcije za odabrani period
- Provjerite filter `VTR_VRSTA_TRANSAKCIJE = 'FG'`
- Provjerite da li postoji IDBLAG za datum u tablici BLAGAJNA

---

## 📝 Licenca

MIT License - slobodno koristite i modificirajte.

---

## 👤 Autor

**Firebird Desktop XML Export**

Za pitanja i podršku, otvorite issue na GitHubu.

---

## 🙏 Zahvale

- Python `fdb` library za Firebird podršku
- `tkcalendar` za kalendar widget
- Firebird zajednici za odličnu dokumentaciju
