import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import fdb
import os
import xml.etree.ElementTree as ET

# ═══════════════════════════════════════════════════════════
# KONFIGURACIJA
# ═══════════════════════════════════════════════════════════

DB_CONFIG = {
    'host': 'localhost',
    'database': 'C:/EXCHBIH/NOVAC-2026.FDB',
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
        
        # SQL upit - koristimo direktno stringove umjesto parametara
        sql = f'''
            SELECT 
                bt.TEC_TL_DATUM_TECAJNE_LISTE,
                bt.TEC_VALUTA_BROJCANO,
                bt.IZNOS_U_VALUTI,
                bt.IZNOS_U_KUNAMA,
                v.PROVBANKE
            FROM BLAGAJNICKE_TRANSAKCIJE bt
            LEFT JOIN VALUTE v ON bt.TEC_VALUTA_BROJCANO = v.VALUTA_BROJCANO
            WHERE bt.TEC_TL_DATUM_TECAJNE_LISTE >= CAST('{start_str}' AS DATE)
              AND bt.TEC_TL_DATUM_TECAJNE_LISTE <= CAST('{end_str}' AS DATE)
            ORDER BY bt.ID_BT
        '''
        
        print(f"Izvršavam SQL za transakcije...")
        print(f"SQL: {sql[:200]}...")  # Prikaži prvih 200 znakova
        
        # Izvršavanje upita BEZ parametara
        cur.execute(sql)
        rows = cur.fetchall()
        
        con.close()
        
        # Pretvaranje rezultata u listu dictionary objekata
        transactions = []
        for row in rows:
            transactions.append({
                'datum': row[0],
                'valuta': row[1],
                'iznos_valuta': row[2],
                'iznos_kune': row[3],
                'provbanke': row[4] if row[4] else 0
            })
        
        print(f"✓ Dohvaćeno {len(transactions)} transakcija")
        return transactions
        
    except Exception as e:
        print(f"❌ Greška pri dohvaćanju transakcija: {e}")
        messagebox.showerror("Greška", f"Greška pri dohvaćanju transakcija:\n{e}")
        return None


def generate_xml(valto_nbr, transactions):
    """
    Generira XML datoteku iz transakcija.
    
    Parametri:
        valto_nbr: string (UNIQUEID iz FIRME)
        transactions: lista dictionary objekata
    
    Vraća:
        string (naziv datoteke) ili None
    """
    try:
        print(f"Generiram XML za {len(transactions)} transakcija...")
        
        # Kreiranje root elementa
        root = ET.Element('tomeges_adatok')
        valto_tetelek = ET.SubElement(root, 'valto_tetelek')
        
        # Dodavanje transakcija
        for t in transactions:
            valto_tetel = ET.SubElement(valto_tetelek, 'valto_tetel')
            
            # valto_datum - formatiranje u YYYY-MM-DD
            datum_elem = ET.SubElement(valto_tetel, 'valto_datum')
            if isinstance(t['datum'], datetime):
                datum_elem.text = t['datum'].strftime('%Y-%m-%d')
            else:
                datum_elem.text = str(t['datum'])[:10]  # Uzmi prvih 10 znakova
            
            # valto_nbr
            nbr_elem = ET.SubElement(valto_tetel, 'valto_nbr')
            nbr_elem.text = str(valto_nbr)
            
            # valto_valuta
            valuta_elem = ET.SubElement(valto_tetel, 'valto_valuta')
            valuta_elem.text = str(t['valuta']) if t['valuta'] else ''
            
            # valto_nyito - 2 decimale
            nyito_elem = ET.SubElement(valto_tetel, 'valto_nyito')
            nyito_elem.text = f"{float(t['iznos_valuta']):.2f}"
            
            # valto_nyito_km - 2 decimale
            nyito_km_elem = ET.SubElement(valto_tetel, 'valto_nyito_km')
            nyito_km_elem.text = f"{float(t['iznos_kune']):.2f}"
            
            # valto_bank_percent - 2 decimale
            bank_percent = float(t['provbanke'])
            bank_elem = ET.SubElement(valto_tetel, 'valto_bank_percent')
            bank_elem.text = f"{bank_percent:.2f}"
            
            # valto_exc_percent - 2 decimale
            exc_percent = 100 - bank_percent
            exc_elem = ET.SubElement(valto_tetel, 'valto_exc_percent')
            exc_elem.text = f"{exc_percent:.2f}"
        
        # Generiranje naziva datoteke: valto_nbr_YYYYMMDD_HHMMSS.XML
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        filename = f"{valto_nbr}_{timestamp}.XML"
        
        # Putanja do datoteke
        xml_folder = 'C:/XML'
        
        # Kreiranje foldera ako ne postoji
        if not os.path.exists(xml_folder):
            os.makedirs(xml_folder)
            print(f"✓ Kreiran folder: {xml_folder}")
        
        filepath = os.path.join(xml_folder, filename)
        
        # Kreiranje XML tree i spremanje
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")  # Formatiranje (Python 3.9+)
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
    
    # 2. Dohvat transakcija
    start = start_date.get_date()
    end = end_date.get_date()
    
    print(f"Odabrani period: {start} - {end}")
    
    transactions = get_transactions(start, end)
    
    if transactions is None:
        status_label.config(text="❌ Greška pri dohvaćanju transakcija", fg="red")
        return
    
    if len(transactions) == 0:
        status_label.config(text="⚠ Nema transakcija u odabranom periodu", fg="orange")
        messagebox.showwarning("Upozorenje", "Nema transakcija u odabranom periodu.")
        return
    
    # 3. Generiranje XML-a
    status_label.config(text="Generiram XML...", fg="blue")
    root.update()
    
    filename = generate_xml(valto_nbr, transactions)
    
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
        f"Transakcija: {len(transactions)}\n"
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