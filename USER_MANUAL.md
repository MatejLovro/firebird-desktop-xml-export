# Korisnički Priručnik - Firebird Desktop XML Export

**Verzija:** 1.0.0  
**Datum:** 21.02.2026

---

## 📑 Sadržaj

1. [Uvod](#uvod)
2. [Pokretanje Aplikacije](#pokretanje-aplikacije)
3. [Korisničko Sučelje](#korisničko-sučelje)
4. [Generiranje XML Datoteke](#generiranje-xml-datoteke)
5. [Slanje na Server](#slanje-na-server)
6. [Česte Greške i Rješenja](#česte-greške-i-rješenja)
7. [Najčešća Pitanja](#najčešća-pitanja)

---

## 1. Uvod

Ova aplikacija omogućava jednostavno exportovanje blagajničkih transakcija iz Firebird baze podataka u XML format i automatsko slanje na FTP server.

### Što aplikacija radi?

1. **Dohvaća podatke** iz Firebird baze za odabrani period
2. **Generira XML datoteku** prema specificiranoj strukturi
3. **Sprema XML** u `C:\XML\` folder
4. **Šalje XML** na FTP server

---

## 2. Pokretanje Aplikacije

### Prije prvog pokretanja:

#### Korak 1: Instalirajte potrebne komponente
- Python 3.x (32-bit) mora biti instaliran
- Firebird server mora biti pokrenut

#### Korak 2: Kreirajte konfiguracijsku datoteku

U folderu gdje se nalazi aplikacija, kreirajte datoteku `REPORT.INI` sa sljedećim sadržajem:

```ini
[DATABASE]
database=C:/EXCHBIH/EXCHANGE-2026ISM.FDB
host=localhost
user=SYSDBA
password=masterkey

[FTP]
host=ftp.ekonto.hr
user=bihup2024@ecgroup.hr
password=your_password_here
```

**VAŽNO:** Zamijenite `your_password_here` s pravom lozinkom!

#### Korak 3: Pokrenite aplikaciju

Dvostruki klik na `app.py` ili u Command Prompt-u:
```
python app.py
```

---

## 3. Korisničko Sučelje

### Izgled aplikacije:

```
┌─────────────────────────────────────────────┐
│   Export Blagajničkih Transakcija           │
├─────────────────────────────────────────────┤
│                                             │
│  Početni datum:   [📅 21.02.2026]          │
│                                             │
│  Završni datum:   [📅 21.02.2026]          │
│                                             │
│  [  Generiraj XML  ] [ Pošalji XML na... ] │
│                                             │
│  Status: Spremno za rad                     │
│                                             │
└─────────────────────────────────────────────┘
```

### Elementi sučelja:

1. **Naslov** - "Export Blagajničkih Transakcija"
2. **Početni datum** - Kalendar widget za odabir početnog datuma
3. **Završni datum** - Kalendar widget za odabir završnog datuma
4. **Dugme "Generiraj XML"** - Pokreće generiranje XML datoteke
5. **Dugme "Pošalji XML na server"** - Šalje generiranu datoteku na FTP
6. **Status label** - Prikazuje trenutni status operacije

---

## 4. Generiranje XML Datoteke

### Korak po korak:

#### 1. Odaberite početni datum
- Kliknite na kalendar pored "Početni datum"
- Odaberite željeni datum
- Zatvorite kalendar

#### 2. Odaberite završni datum
- Kliknite na kalendar pored "Završni datum"
- Odaberite željeni datum
- **VAŽNO:** Završni datum mora biti jednak ili kasniji od početnog datuma!

#### 3. Kliknite "Generiraj XML"

Aplikacija će:
1. Provjeriti jesu li datumi ispravni
2. Spojiti se na bazu podataka
3. Dohvatiti UNIQUEID poslovnice
4. Za svaki datum u periodu:
   - Dohvatiti agregaciju po valutama (BLAGAJNA_STANJE)
   - Dohvatiti sve transakcije (BLAGAJNICKE_TRANSAKCIJE)
   - Generirati XML tagove
5. Spremiti XML datoteku u `C:\XML\`

#### 4. Pričekajte potvrdu

Prikazat će se poruka:
```
XML datoteka uspješno kreirana!

Naziv: 009_rpt_20260221_143022.XML
Lokacija: C:\XML\
POSLOVNICA: 009

SADA JE POŠALJITE NA SERVER
```

#### 5. Što se dešava s dugmadima?

- ❌ **"Generiraj XML"** - postaje **neaktivno** (sivo)
- ✅ **"Pošalji XML na server"** - postaje **aktivno** (zeleno)

---

## 5. Slanje na Server

### Korak po korak:

#### 1. Nakon uspješnog generiranja XML-a

Kliknite dugme **"Pošalji XML na server"**

#### 2. Aplikacija će:

1. Otvoriti FTP konekciju na `ftp.ekonto.hr`
2. Prijaviti se s podacima iz `REPORT.INI`
3. Uploadati XML datoteku
4. Provjeriti da li je datoteka stvarno poslana
5. Zatvoriti FTP konekciju

#### 3. Pratite status

U status labelu vidjet ćete:
- "Šaljem datoteku na server..." (plavo)
- "✓ Datoteka poslana: 009_rpt_20260221_143022.XML" (zeleno)

#### 4. Potvrda uspjeha

Prikazat će se poruka:
```
XML datoteka uspješno poslana na server!

Datoteka: 009_rpt_20260221_143022.XML
Server: ftp.ekonto.hr
```

#### 5. Dugmad se resetiraju

- ✅ **"Generiraj XML"** - postaje **aktivno** (plavo)
- ❌ **"Pošalji XML na server"** - postaje **neaktivno** (sivo)

Sada možete generirati novi XML za drugi period!

---

## 6. Česte Greške i Rješenja

### ❌ "Završni datum ne može biti manji od početnog"

**Uzrok:** Odabrali ste završni datum koji je raniji od početnog.

**Rješenje:**
1. Provjerite odabrane datume
2. Odaberite završni datum koji je jednak ili kasniji od početnog
3. Pokušajte ponovno

**Primjer:**
- ❌ Početni: 25.02.2026, Završni: 20.02.2026 (KRIVO)
- ✅ Početni: 20.02.2026, Završni: 25.02.2026 (TOČNO)
- ✅ Početni: 21.02.2026, Završni: 21.02.2026 (TOČNO - isti dan)

---

### ❌ "Ne mogu se spojiti na bazu"

**Uzrok:** Firebird server nije dostupan ili su podaci u `REPORT.INI` netočni.

**Rješenje:**
1. Provjerite je li Firebird server pokrenut
2. Otvorite `REPORT.INI` i provjerite:
   - `database` putanju
   - `user` korisničko ime
   - `password` lozinku
3. Pokušajte ponovno pokrenuti aplikaciju

---

### ❌ "Greška pri slanju datoteke na FTP server"

**Uzrok:** FTP server nije dostupan ili su credentials netočni.

**Rješenje:**
1. Provjerite internet konekciju
2. Otvorite `REPORT.INI` i provjerite FTP sekciju:
   - `host` - adresa servera
   - `user` - korisničko ime
   - `password` - lozinka
3. Pokušajte ponovno

---

### ⚠ "Nema transakcija u odabranom periodu"

**Uzrok:** U bazi nema transakcija za odabrani period ili nema IDBLAG za te datume.

**Rješenje:**
1. Provjerite da li postoje transakcije u odabranom periodu
2. Odaberite drugačiji period
3. Kontaktirajte administratora baze ako problem perzistira

---

### ❌ "Konfiguracijska datoteka nije pronađena"

**Uzrok:** Nedostaje `REPORT.INI` datoteka.

**Rješenje:**
1. Kreirajte `REPORT.INI` u istom folderu gdje je aplikacija
2. Kopirajte sadržaj iz `REPORT.INI.example`
3. Uredite postavke
4. Pokrenite aplikaciju ponovno

---

## 7. Najčešća Pitanja

### P: Gdje se spremaju XML datoteke?
**O:** Sve XML datoteke se spremaju u `C:\XML\` folder.

### P: Kako se zove generirana datoteka?
**O:** Format je: `{poslovnica}_rpt_{YYYYMMDD_HHMMSS}.XML`  
Primjer: `009_rpt_20260221_143022.XML`

### P: Mogu li generirati XML za više mjeseci odjednom?
**O:** Da! Odaberite početni datum (npr. 01.01.2026) i završni datum (npr. 31.03.2026). Aplikacija će automatski iterirati po svim datumima.

### P: Što ako ne želim poslati XML na server odmah?
**O:** Ne morate! XML datoteka ostaje spremljena u `C:\XML\` i možete je poslati kasnije ili ručno.

### P: Mogu li promijeniti FTP server?
**O:** Da! Uredite `REPORT.INI` datoteku, sekciju `[FTP]`, i promijenite `host`.

### P: Što znači "POSLOVNICA" u poruci?
**O:** To je UNIQUEID iz tablice FIRME - identifikator vaše poslovnice/mjenjačnice.

### P: Aplikacija se smrzava - što da radim?
**O:** 
1. Provjerite koliko transakcija ima u periodu (možda ih ima puno)
2. Pokušajte s manjim periodom (npr. tjedan dana)
3. Pričekajte - aplikacija radi, samo može trajati duže za velike periode

### P: Mogu li vidjeti generirani XML prije slanja?
**O:** Da! Otvorite `C:\XML\` folder i pogledajte datoteku u text editoru ili XML vieweru.

### P: Što ako želim izbrisati stare XML datoteke?
**O:** Možete ručno izbrisati datoteke iz `C:\XML\` foldera. Aplikacija ih ne briše automatski.

---

## 📞 Podrška

Za dodatna pitanja ili probleme:
1. Provjerite ovu dokumentaciju
2. Pregledajte log u terminalu (ako pokrećete iz Command Prompt-a)
3. Kontaktirajte IT podršku

---

**Hvala što koristite Firebird Desktop XML Export!** 🎉
