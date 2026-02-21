import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import fdb
import os
import xml.etree.ElementTree as ET

# ═══════════════════════════════════════════════════════════
# KONFIGURACIJA
# ═══════════════════════════════════════════════════════════

DB_CONFIG = {
    'host': 'localhost',
    'database': 'C:/EXCHBIH/EXCHANGE-2026ISM.FDB',
    'user': 'SYSDBA',
    'password': 'masterkey'
}

# Globalna varijabla za naziv XML datoteke
current_xml_file = None  
# ═══════════════════════════════════════════════════════════
# FIREBIRD FUNKCIJE (ne ovise o GUI-u)
# ═══════════════════════════════════════════════════════════

def get_uniqueid():
    """
    Dohvaća UNIQUEID iz tablice FIRME (slog s najvećim IDFIRME).
    Vraća: string (UNIQUEID) ili None
    """
    try:
        print("Spajam se na Firebird bazu...")
        con = fdb.connect(**DB_CONFIG)
        cur = con.cursor()
        
        sql = 'SELECT FIRST 1 UNIQUEID FROM FIRME ORDER BY IDFIRME DESC'
        print(f"Izvršavam SQL: {sql}")
        
        cur.execute(sql)
        row = cur.fetchone()
        
        con.close()
        
        if row:
            valto_nbr = row[0]
            print(f"✓ Dohvaćen UNIQUEID: {valto_nbr}")
            return valto_nbr
        else:
            print("❌ Nema podataka u tablici FIRME")
            return None
            
    except Exception as e:
        print(f"❌ Greška pri dohvaćanju UNIQUEID: {e}")
        messagebox.showerror("Greška", f"Greška pri dohvaćanju UNIQUEID:\n{e}")
        return None
    

def replace_croatian_chars(text):
    """
    Zamjenjuje hrvatske dijakritičke znakove s hexadecimalnim kodovima.
    
    Parametri:
        text: string za zamjenu
    
    Vraća:
        string s zamijenjenim znakovima
    """
    if not text:
        return ''
    
    text = str(text)
    
    # Mapa: hrvatski znak -> hex kod
    replacements = {
        'Č': '&#x010C;',  # Č veliko
        'č': '&#x010D;',  # č malo
        'Ć': '&#x0106;',  # Ć veliko
        'ć': '&#x0107;',  # ć malo
        'Š': '&#x0160;',  # Š veliko
        'š': '&#x0161;',  # š malo
        'Ž': '&#x017D;',  # Ž veliko
        'ž': '&#x017E;',  # ž malo
        'Đ': '&#x0110;',  # Đ veliko
        'đ': '&#x0111;',  # đ malo
    }
    
    for char, code in replacements.items():
        text = text.replace(char, code)
    
    return text


def get_idblag_for_date(date_str):
    """
    Dohvaća IDBLAG iz tablice BLAGAJNA za zadani datum.
    
    Parametri:
        date_str: string u formatu 'YYYY-MM-DD'
    
    Vraća:
        int (IDBLAG) ili None
    """
    try:
        con = fdb.connect(**DB_CONFIG)
        cur = con.cursor()
        
        sql = f"SELECT IDBLAG FROM BLAGAJNA WHERE TL_DATUM_TECAJNE_LISTE = CAST('{date_str}' AS DATE)"
        
        cur.execute(sql)
        row = cur.fetchone()
        
        con.close()
        
        if row:
            return row[0]
        return None
        
    except Exception as e:
        print(f"❌ Greška pri dohvaćanju IDBLAG za datum {date_str}: {e}")
        return None


def get_blagajna_stanje(id_blag):
    """
    Dohvaća sve slogove iz BLAGAJNA_STANJE za zadani IDBLAG (JOIN s VALUTE).
    
    Parametri:
        id_blag: int
    
    Vraća:
        lista dictionary objekata ili []
    """
    try:
        con = fdb.connect(**DB_CONFIG)
        cur = con.cursor()
        
        sql = f'''
            SELECT 
                bs.VALUTA_BROJCANO,
                bs.IZNOS,
                v.PROV_ZA_BANKU
            FROM BLAGAJNA_STANJE bs
            LEFT JOIN VALUTE v ON bs.VALUTA_BROJCANO = v.VALUTA_BROJCANO
            WHERE bs.IDBLAG = {id_blag}
            ORDER BY bs.VALUTA_BROJCANO
        '''
        
        cur.execute(sql)
        rows = cur.fetchall()
        
        con.close()
        
        results = []
        for row in rows:
            results.append({
                'valuta': row[0],
                'iznos': row[1],
                'prov_za_banku': row[2] if row[2] else 0
            })
        
        return results
        
    except Exception as e:
        print(f"❌ Greška pri dohvaćanju BLAGAJNA_STANJE: {e}")
        return []


def get_kupovni_tecaj(date_str, valuta):
    """
    Dohvaća KUPOVNI_TECAJ iz tablice TECAJEVI za zadani datum i valutu.
    
    Parametri:
        date_str: string u formatu 'YYYY-MM-DD'
        valuta: string (VALUTA_BROJCANO)
    
    Vraća:
        float (KUPOVNI_TECAJ) ili 1.0
    """
    try:
        con = fdb.connect(**DB_CONFIG)
        cur = con.cursor()
        
        sql = f'''
            SELECT KUPOVNI_TECAJ 
            FROM TECAJEVI 
            WHERE TL_DATUM_TECAJNE_LISTE = CAST('{date_str}' AS DATE)
              AND VMT_VRSTA_TECAJA = 'RED'
              AND VALUTA_BROJCANO = '{valuta}'
        '''
        
        cur.execute(sql)
        row = cur.fetchone()
        
        con.close()
        
        if row and row[0]:
            return float(row[0])
        return 1.0  # Default ako nema tečaja
        
    except Exception as e:
        print(f"❌ Greška pri dohvaćanju KUPOVNI_TECAJ: {e}")
        return 1.0


def get_transactions_for_idblag(id_blag):
    """
    Dohvaća transakcije iz BLAGAJNICKE_TRANSAKCIJE za zadani IDBLAG.
    
    Parametri:
        id_blag: int
    
    Vraća:
        lista dictionary objekata ili []
    """
    try:
        con = fdb.connect(**DB_CONFIG)
        cur = con.cursor()
        
        sql = f'''
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
            WHERE bt.IDBLAG = {id_blag}
            ORDER BY bt.ID_BT
        '''
        
        cur.execute(sql)
        rows = cur.fetchall()
        
        con.close()
        
        transactions = []
        for row in rows:
            transactions.append({
                'datum_tecajne_liste': row[0],
                'valuta': row[1],
                'iznos_valuta': row[2],
                'iznos_kune': row[3],
                'datum_vrijeme': row[4],
                'serijski_broj': row[5],
                'br_kartice': row[6],
                'oznaka_platnog': row[7],
                'primjenjeni_tecaj': row[8],
                'prodaoime': row[9],
                'prodaodok': row[10],
                'provbanke': row[11] if row[11] else 0,
                'korisnik_ime': row[12]
            })
        
        return transactions
        
    except Exception as e:
        print(f"❌ Greška pri dohvaćanju transakcija za IDBLAG {id_blag}: {e}")
        return []



def get_transactions(start_date, end_date):
    """
    Dohvaća transakcije iz BLAGAJNICKE_TRANSAKCIJE za zadani period.
    
    Parametri:
        start_date: datetime objekt (početni datum)
        end_date: datetime objekt (završni datum)
    
    Vraća: 
        lista dictionary objekata ili None
    """
    try:
        print(f"Dohvaćam transakcije od {start_date} do {end_date}...")
        
        con = fdb.connect(**DB_CONFIG)
        cur = con.cursor()
        
        # Formatiranje datuma za Firebird (YYYY-MM-DD)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        print(f"Formirani datumi: {start_str} - {end_str}")
        
        # NOVI SQL upit s dodatnim poljima i JOIN-om s KORISNICI
        sql = f'''
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
            WHERE bt.TEC_TL_DATUM_TECAJNE_LISTE >= CAST('{start_str}' AS DATE)
              AND bt.TEC_TL_DATUM_TECAJNE_LISTE <= CAST('{end_str}' AS DATE)
              AND bt.VTR_VRSTA_TRANSAKCIJE = 'FG'
            ORDER BY bt.ID_BT
        '''
        
        print(f"Izvršavam SQL za transakcije...")
        
        cur.execute(sql)
        rows = cur.fetchall()
        
        con.close()
        
        # Pretvaranje rezultata u listu dictionary objekata
        transactions = []
        for row in rows:
            transactions.append({
                # Polja za valto_tetelek (stara struktura)
                'datum_tecajne_liste': row[0],
                'valuta': row[1],
                'iznos_valuta': row[2],
                'iznos_kune': row[3],
                'provbanke': row[11] if row[11] else 0,
                
                # Nova polja za kozonseges_tetelek
                'datum_vrijeme': row[4],      # DATUM_I_VRIJEME_TRANSAKCIJE
                'serijski_broj': row[5],      # SERIJSKI_BROJ
                'br_kartice': row[6],         # BR_KARTICE
                'oznaka_platnog': row[7],     # OZNAKA_PLATNOG_INSTRUMENTA_U_K
                'primjenjeni_tecaj': row[8],  # PRIMJENJENI_TECAJ
                'prodaoime': row[9],          # PRODAOIME
                'prodaodok': row[10],         # PRODAODOK
                'korisnik_ime': row[12]       # k.IME
            })
        
        print(f"✓ Dohvaćeno {len(transactions)} transakcija")
        return transactions
        
    except Exception as e:
        print(f"❌ Greška pri dohvaćanju transakcija: {e}")
        messagebox.showerror("Greška", f"Greška pri dohvaćanju transakcija:\n{e}")
        return None

        
def generate_xml(valto_nbr, start_date, end_date):
    """
    Generira XML datoteku iteracijom po datumima.
    Za svaki datum: valto_tetelek + kozonseges_tetelek
    
    Parametri:
        valto_nbr: string (UNIQUEID iz FIRME)
        start_date: datetime.date objekt
        end_date: datetime.date objekt
    
    Vraća:
        string (naziv datoteke) ili None
    """
    try:
        print(f"Generiram XML po datumima od {start_date} do {end_date}...")
        
        # Kreiranje root elementa
        root = ET.Element('tomeges_adatok')
        
        # ═══════════════════════════════════════════════════════════
        # ITERACIJA PO DATUMIMA
        # ═══════════════════════════════════════════════════════════
        
        current_date = start_date
        total_valto = 0
        total_kozonseges = 0
        
        while current_date <= end_date:
            d_datum = current_date.strftime('%Y-%m-%d')
            print(f"\nObrađujem datum: {d_datum}")
            
            # 1. Dohvati IDBLAG za ovaj datum
            id_blag = get_idblag_for_date(d_datum)
            
            if id_blag is None:
                print(f"  ⚠ Nema IDBLAG za datum {d_datum} - preskačem")
                current_date += timedelta(days=1)
                continue
            
            print(f"  ✓ IDBLAG: {id_blag}")
            
            # ═══════════════════════════════════════════════════════════
            # GRUPA 1: valto_tetelek za ovaj datum
            # ═══════════════════════════════════════════════════════════
            
            valto_tetelek = ET.SubElement(root, 'valto_tetelek')
            
            # Dohvati sve valute iz BLAGAJNA_STANJE
            stanje_rows = get_blagajna_stanje(id_blag)
            print(f"  ✓ BLAGAJNA_STANJE: {len(stanje_rows)} valuta")
            
            for stanje in stanje_rows:
                valuta = stanje['valuta']
                iznos = stanje['iznos']
                prov_za_banku = stanje['prov_za_banku']
                
                # Dohvati KUPOVNI_TECAJ za ovu valutu i datum
                kupovni_tecaj = get_kupovni_tecaj(d_datum, valuta)
                
                # Izračunaj valto_nyito_km
                valto_nyito_km = float(iznos) * kupovni_tecaj
                
                # Kreiraj valto_tetel
                valto_tetel = ET.SubElement(valto_tetelek, 'valto_tetel')
                
                ET.SubElement(valto_tetel, 'valto_datum').text = d_datum
                ET.SubElement(valto_tetel, 'valto_nbr').text = str(valto_nbr)
                ET.SubElement(valto_tetel, 'valto_valuta').text = str(valuta) if valuta else ''
                ET.SubElement(valto_tetel, 'valto_nyito').text = f"{float(iznos):.2f}"
                ET.SubElement(valto_tetel, 'valto_nyito_km').text = f"{valto_nyito_km:.2f}"
                ET.SubElement(valto_tetel, 'valto_exc_percent').text = f"{100 - float(prov_za_banku):.2f}"
                ET.SubElement(valto_tetel, 'valto_bank_percent').text = f"{float(prov_za_banku):.2f}"
                
                total_valto += 1
            
            # ═══════════════════════════════════════════════════════════
            # GRUPA 2: kozonseges_tetelek za ovaj datum
            # ═══════════════════════════════════════════════════════════
            
            kozonseges_tetelek = ET.SubElement(root, 'kozonseges_tetelek')
            
            # Dohvati transakcije za ovaj IDBLAG
            transactions = get_transactions_for_idblag(id_blag)
            print(f"  ✓ Transakcije: {len(transactions)}")
            
            # Brojač za nbr (resetira se za svaki datum)
            nbr_counter = 1
            
            for t in transactions:
                kozonseges_tetel = ET.SubElement(kozonseges_tetelek, 'kozonseges_tetel')
                
                ET.SubElement(kozonseges_tetel, 'nbr').text = str(nbr_counter)
                
                # datum - TIMESTAMP format
                datum_elem = ET.SubElement(kozonseges_tetel, 'datum')
                if isinstance(t['datum_vrijeme'], datetime):
                    datum_elem.text = t['datum_vrijeme'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    datum_elem.text = str(t['datum_vrijeme'])
                
                ET.SubElement(kozonseges_tetel, 'valto').text = str(valto_nbr)
                ET.SubElement(kozonseges_tetel, 'felhasznalo').text = str(t['korisnik_ime']) if t['korisnik_ime'] else ''
                ET.SubElement(kozonseges_tetel, 'tranzakcio').text = str(t['serijski_broj']) if t['serijski_broj'] else ''
                ET.SubElement(kozonseges_tetel, 'dokumentumszam').text = str(t['br_kartice']) if t['br_kartice'] else ''
                ET.SubElement(kozonseges_tetel, 'valuta').text = str(t['valuta']) if t['valuta'] else ''
                ET.SubElement(kozonseges_tetel, 'fiz_mod').text = str(t['oznaka_platnog']) if t['oznaka_platnog'] else ''
                ET.SubElement(kozonseges_tetel, 'ertek').text = f"{float(t['iznos_valuta']):.2f}" if t['iznos_valuta'] else '0.00'
                ET.SubElement(kozonseges_tetel, 'akt_arf').text = str(t['primjenjeni_tecaj']) if t['primjenjeni_tecaj'] else ''

                ET.SubElement(kozonseges_tetel, 'alap_arf').text = str(t['primjenjeni_tecaj']) if t['primjenjeni_tecaj'] else ''

                # alap_arf_tecaj = get_kupovni_tecaj(d_datum, t['valuta'])
                # ET.SubElement(kozonseges_tetel, 'alap_arf').text = str(alap_arf_tecaj) if alap_arf_tecaj else ''


                ET.SubElement(kozonseges_tetel, 'bank_arf').text = f"{float(t['provbanke']):.2f}" if t['provbanke'] else '0.00'
                ET.SubElement(kozonseges_tetel, 'honnan_hova').text = ''

                # ET.SubElement(kozonseges_tetel, 'vevo_kod').text = str(t['prodaoime']) if t['prodaoime'] else ''
                ET.SubElement(kozonseges_tetel, 'vevo_kod').text = replace_croatian_chars(t['prodaoime'])

                ET.SubElement(kozonseges_tetel, 'vevo_cim').text = ''
                ET.SubElement(kozonseges_tetel, 'vevo_utlevel_id').text = str(t['prodaodok']) if t['prodaodok'] else ''
                ET.SubElement(kozonseges_tetel, 'vevo_orszag').text = ''
                
                nbr_counter += 1
                total_kozonseges += 1
            
            # Sljedeći datum
            current_date += timedelta(days=1)
        
        # ═══════════════════════════════════════════════════════════
        # SPREMANJE XML-a
        # ═══════════════════════════════════════════════════════════
        
        print(f"\n✓ Ukupno valto_tetel elemenata: {total_valto}")
        print(f"✓ Ukupno kozonseges_tetel elemenata: {total_kozonseges}")
        
        # Generiranje naziva datoteke
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        filename = f"{valto_nbr}_{timestamp}.XML"
        
        xml_folder = 'C:/XML'
        if not os.path.exists(xml_folder):
            os.makedirs(xml_folder)
        
        filepath = os.path.join(xml_folder, filename)
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(filepath, encoding='UTF-8', xml_declaration=True)
        
        print(f"✓ XML datoteka kreirana: {filepath}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Greška pri generiranju XML-a: {e}")
        messagebox.showerror("Greška", f"Greška pri generiranju XML-a:\n{e}")
        return None



# ═══════════════════════════════════════════════════════════
# GUI KREIRANJE
# ═══════════════════════════════════════════════════════════

# Kreiranje glavnog prozora
root = tk.Tk()
root.title("Export Blagajničkih Transakcija")
root.geometry("500x400")
root.resizable(False, False)

# Naslov
title_label = tk.Label(
    root, 
    text="Export Blagajničkih Transakcija", 
    font=("Arial", 16, "bold")
)
title_label.pack(pady=20)

# Frame za datumska polja
date_frame = tk.Frame(root)
date_frame.pack(pady=20)

# Početni datum
start_label = tk.Label(date_frame, text="Početni datum:", font=("Arial", 10))
start_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

start_date = DateEntry(
    date_frame,
    width=15,
    background='darkblue',
    foreground='white',
    borderwidth=2,
    date_pattern='dd.mm.yyyy'
)
start_date.grid(row=0, column=1, padx=10, pady=10)

# Završni datum
end_label = tk.Label(date_frame, text="Završni datum:", font=("Arial", 10))
end_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

end_date = DateEntry(
    date_frame,
    width=15,
    background='darkblue',
    foreground='white',
    borderwidth=2,
    date_pattern='dd.mm.yyyy'
)
end_date.grid(row=1, column=1, padx=10, pady=10)

# Frame za dugmad
button_frame = tk.Frame(root)
button_frame.pack(pady=20)

# Status label (kreiramo PRIJE dugmadi jer ga koriste u command)
status_label = tk.Label(
    root,
    text="Spremno za rad",
    font=("Arial", 9),
    fg="gray"
)
status_label.pack(pady=10)

# ═══════════════════════════════════════════════════════════
# EVENT HANDLER FUNKCIJE (koriste GUI elemente)
# ═══════════════════════════════════════════════════════════

def test_database():
    """
    Generira XML datoteku iz podataka iz baze.
    """
    status_label.config(text="Dohvaćam podatke iz baze...", fg="blue")
    root.update()
    
    # 1. Dohvat UNIQUEID
    valto_nbr = get_uniqueid()
    
    if not valto_nbr:
        status_label.config(text="❌ Greška pri dohvaćanju UNIQUEID", fg="red")
        return
    
    # 2. Datumi
    start = start_date.get_date()
    end = end_date.get_date()
    
    print(f"Odabrani period: {start} - {end}")
    
    # 3. Generiranje XML-a (iteracija po datumima)
    status_label.config(text="Generiram XML...", fg="blue")
    root.update()
    
    filename = generate_xml(valto_nbr, start, end)
    
    if not filename:
        status_label.config(text="❌ Greška pri generiranju XML-a", fg="red")
        return
    
    # 4. Uspjeh!
    status_label.config(text=f"✓ XML kreiran: {filename}", fg="green")
    
    messagebox.showinfo(
        "Uspjeh", 
        f"XML datoteka uspješno kreirana!\n\n"
        f"Naziv: {filename}\n"
        f"Lokacija: C:\\XML\\\n"
        f"UNIQUEID: {valto_nbr}"
    )
    
    # Omogući dugme "Pošalji na server"
    btn_send.config(state="normal")
    
    # Spremi naziv datoteke za FTP upload
    global current_xml_file
    current_xml_file = filename



# ═══════════════════════════════════════════════════════════
# DUGMAD (definirani NAKON event handler funkcija)
# ═══════════════════════════════════════════════════════════

# Dugme "Generiraj XML"
btn_generate = tk.Button(
    button_frame,
    text="Generiraj XML",
    width=15,
    height=2,
    bg="#2196F3",
    fg="white",
    font=("Arial", 10, "bold"),
    cursor="hand2",
    command=test_database
)
btn_generate.grid(row=0, column=0, padx=10)

# Dugme "Pošalji na server"
btn_send = tk.Button(
    button_frame,
    text="Pošalji XML na server",
    width=18,
    height=2,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 10, "bold"),
    cursor="hand2",
    state="disabled"
)
btn_send.grid(row=0, column=1, padx=10)

# ═══════════════════════════════════════════════════════════
# POKRETANJE APLIKACIJE
# ═══════════════════════════════════════════════════════════

root.mainloop()