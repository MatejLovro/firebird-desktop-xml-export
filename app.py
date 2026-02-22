import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import fdb
import os
import sys
import xml.etree.ElementTree as ET
import configparser
from ftplib import FTP

# ═══════════════════════════════════════════════════════════
# GLOBALNE VARIJABLE
# ═══════════════════════════════════════════════════════════

# Globalna varijabla za naziv XML datoteke
current_xml_file = None

# Globalna konekcija na bazu
global_connection = None

# Konfiguracija iz INI datoteke
CONFIG = None
DB_CONFIG = None
FTP_CONFIG = None

# ═══════════════════════════════════════════════════════════
# KONFIGURACIJA IZ INI DATOTEKE
# ═══════════════════════════════════════════════════════════

def load_config():
    """
    Učitava konfiguraciju iz REPORT.INI datoteke.
    Vraća: dictionary s konfiguracijskim podacima ili None
    """
    config_file = 'REPORT.INI'
    
    # Ako se pokreće kao .exe, traži INI u istom folderu kao .exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    config_path = os.path.join(application_path, config_file)
    
    if not os.path.exists(config_path):
        messagebox.showerror(
            "Greška", 
            f"Konfiguracijska datoteka nije pronađena:\n{config_path}\n\n"
            f"Molimo kreirajte REPORT.INI datoteku u folderu aplikacije."
        )
        return None
    
    try:
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        # Učitaj DATABASE sekciju
        db_config = {
            'database': config.get('DATABASE', 'database'),
            'host': config.get('DATABASE', 'host'),
            'user': config.get('DATABASE', 'user'),
            'password': config.get('DATABASE', 'password'),
            'charset': 'UTF8'
        }
        
        # Učitaj FTP sekciju
        ftp_config = {
            'host': config.get('FTP', 'host'),
            'user': config.get('FTP', 'user'),
            'password': config.get('FTP', 'password')
        }
        
        return {
            'database': db_config,
            'ftp': ftp_config
        }
        
    except Exception as e:
        messagebox.showerror(
            "Greška", 
            f"Greška pri učitavanju REPORT.INI:\n{e}"
        )
        return None


# Učitaj konfiguraciju pri pokretanju
CONFIG = load_config()

if CONFIG is None:
    sys.exit(1)

# Ažuriraj DB_CONFIG i FTP_CONFIG
DB_CONFIG = CONFIG['database']
FTP_CONFIG = CONFIG['ftp']

# ═══════════════════════════════════════════════════════════
# DATABASE CONNECTION MANAGEMENT
# ═══════════════════════════════════════════════════════════

def connect_to_database():
    """
    Otvara globalnu konekciju na bazu podataka.
    Vraća: fdb.Connection objekt ili None
    """
    global global_connection
    try:
        if global_connection is None:
            global_connection = fdb.connect(**DB_CONFIG)
        return global_connection
    except Exception as e:
        messagebox.showerror("Greška", f"Ne mogu se spojiti na bazu:\n{e}")
        return None


def close_database_connection():
    """Zatvara globalnu konekciju na bazu."""
    global global_connection
    if global_connection:
        try:
            global_connection.close()
            global_connection = None
        except Exception as e:
            pass


# ═══════════════════════════════════════════════════════════
# HELPER FUNKCIJE
# ═══════════════════════════════════════════════════════════

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
    
    replacements = {
        'Č': '&#x010C;',
        'č': '&#x010D;',
        'Ć': '&#x0106;',
        'ć': '&#x0107;',
        'Š': '&#x0160;',
        'š': '&#x0161;',
        'Ž': '&#x017D;',
        'ž': '&#x017E;',
        'Đ': '&#x0110;',
        'đ': '&#x0111;',
    }
    
    for char, code in replacements.items():
        text = text.replace(char, code)
    
    return text


# ═══════════════════════════════════════════════════════════
# FIREBIRD FUNKCIJE
# ═══════════════════════════════════════════════════════════

def get_uniqueid():
    """
    Dohvaća UNIQUEID iz tablice FIRME.
    Vraća: string (UNIQUEID) ili None
    """
    try:
        con = connect_to_database()
        if not con:
            return None
            
        cur = con.cursor()
        sql = 'SELECT FIRST 1 UNIQUEID FROM FIRME ORDER BY IDFIRME DESC'
        cur.execute(sql)
        row = cur.fetchone()
        
        if row:
            return row[0]
        return None
            
    except Exception as e:
        messagebox.showerror("Greška", f"Greška pri dohvaćanju UNIQUEID:\n{e}")
        return None


def get_idblag_for_date(date_str):
    """
    Dohvaća IDBLAG iz tablice BLAGAJNA za zadani datum.
    
    Parametri:
        date_str: string u formatu 'YYYY-MM-DD'
    
    Vraća:
        int (IDBLAG) ili None
    """
    try:
        con = connect_to_database()
        if not con:
            return None
            
        cur = con.cursor()
        sql = f"SELECT IDBLAG FROM BLAGAJNA WHERE TL_DATUM_TECAJNE_LISTE = CAST('{date_str}' AS DATE)"
        cur.execute(sql)
        row = cur.fetchone()
        
        if row:
            return row[0]
        return None
        
    except Exception as e:
        return None


def get_blagajna_stanje(id_blag):
    """
    Dohvaća sve slogove iz BLAGAJNA_STANJE za zadani IDBLAG.
    
    Parametri:
        id_blag: int
    
    Vraća:
        lista dictionary objekata ili []
    """
    try:
        con = connect_to_database()
        if not con:
            return []
            
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
        
        results = []
        for row in rows:
            results.append({
                'valuta': row[0],
                'iznos': row[1],
                'prov_za_banku': row[2] if row[2] else 0
            })
        
        return results
        
    except Exception as e:
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
        con = connect_to_database()
        if not con:
            return 1.0
            
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
        
        if row and row[0]:
            return float(row[0])
        return 1.0
        
    except Exception as e:
        return 1.0


def get_all_kupovni_tecajevi_for_date(date_str):
    """
    Dohvaća SVE kupovne tečajeve za zadani datum.
    
    Parametri:
        date_str: string u formatu 'YYYY-MM-DD'
    
    Vraća:
        dictionary {valuta: kupovni_tecaj}
    """
    try:
        con = connect_to_database()
        if not con:
            return {}
            
        cur = con.cursor()
        
        sql = f'''
            SELECT 
                VALUTA_BROJCANO,
                KUPOVNI_TECAJ
            FROM TECAJEVI 
            WHERE TL_DATUM_TECAJNE_LISTE = CAST('{date_str}' AS DATE)
              AND VMT_VRSTA_TECAJA = 'RED'
        '''
        
        cur.execute(sql)
        rows = cur.fetchall()
        
        tecajevi = {}
        for row in rows:
            valuta = row[0]
            tecaj = float(row[1]) if row[1] else 1.0
            tecajevi[valuta] = tecaj
        
        return tecajevi
        
    except Exception as e:
        return {}


def get_transactions_for_idblag(id_blag):
    """
    Dohvaća transakcije iz BLAGAJNICKE_TRANSAKCIJE za zadani IDBLAG.
    
    Parametri:
        id_blag: int
    
    Vraća:
        lista dictionary objekata ili []
    """
    try:
        con = connect_to_database()
        if not con:
            return []
            
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
        return []


# ═══════════════════════════════════════════════════════════
# XML GENERIRANJE
# ═══════════════════════════════════════════════════════════

def generate_xml(valto_nbr, start_date, end_date):
    """
    Generira XML datoteku iteracijom po datumima.
    
    Parametri:
        valto_nbr: string (UNIQUEID iz FIRME)
        start_date: datetime.date objekt
        end_date: datetime.date objekt
    
    Vraća:
        string (naziv datoteke) ili None
    """
    try:
        root = ET.Element('tomeges_adatok')
        
        current_date = start_date
        total_valto = 0
        total_kozonseges = 0
        
        while current_date <= end_date:
            d_datum = current_date.strftime('%Y-%m-%d')
            
            id_blag = get_idblag_for_date(d_datum)
            
            if id_blag is None:
                current_date += timedelta(days=1)
                continue
            
            # ═══════════════════════════════════════════════════════════
            # GRUPA 1: valto_tetelek
            # ═══════════════════════════════════════════════════════════
            
            valto_tetelek = ET.SubElement(root, 'valto_tetelek')
            
            stanje_rows = get_blagajna_stanje(id_blag)
            
            for stanje in stanje_rows:
                valuta = stanje['valuta']
                iznos = stanje['iznos']
                prov_za_banku = stanje['prov_za_banku']
                
                kupovni_tecaj = get_kupovni_tecaj(d_datum, valuta)
                valto_nyito_km = float(iznos) * kupovni_tecaj
                
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
            # GRUPA 2: kozonseges_tetelek
            # ═══════════════════════════════════════════════════════════
            
            kozonseges_tetelek = ET.SubElement(root, 'kozonseges_tetelek')
            
            transactions = get_transactions_for_idblag(id_blag)
            tecajevi_dict = get_all_kupovni_tecajevi_for_date(d_datum)
            
            nbr_counter = 1
            
            for t in transactions:
                kozonseges_tetel = ET.SubElement(kozonseges_tetelek, 'kozonseges_tetel')
                
                ET.SubElement(kozonseges_tetel, 'nbr').text = str(nbr_counter)
                
                datum_elem = ET.SubElement(kozonseges_tetel, 'datum')
                if isinstance(t['datum_vrijeme'], datetime):
                    datum_elem.text = t['datum_vrijeme'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    datum_elem.text = str(t['datum_vrijeme'])
                
                valuta = t['valuta']
                alap_arf_tecaj = tecajevi_dict.get(valuta, 1.0)
                
                ET.SubElement(kozonseges_tetel, 'valto').text = str(valto_nbr)
                ET.SubElement(kozonseges_tetel, 'felhasznalo').text = replace_croatian_chars(t['korisnik_ime'])
                ET.SubElement(kozonseges_tetel, 'tranzakcio').text = str(t['serijski_broj']) if t['serijski_broj'] else ''
                ET.SubElement(kozonseges_tetel, 'dokumentumszam').text = replace_croatian_chars(t['br_kartice'])
                ET.SubElement(kozonseges_tetel, 'valuta').text = str(t['valuta']) if t['valuta'] else ''
                ET.SubElement(kozonseges_tetel, 'fiz_mod').text = replace_croatian_chars(t['oznaka_platnog'])
                ET.SubElement(kozonseges_tetel, 'ertek').text = f"{float(t['iznos_valuta']):.2f}" if t['iznos_valuta'] else '0.00'
                ET.SubElement(kozonseges_tetel, 'akt_arf').text = str(t['primjenjeni_tecaj']) if t['primjenjeni_tecaj'] else ''
                ET.SubElement(kozonseges_tetel, 'alap_arf').text = str(alap_arf_tecaj) if alap_arf_tecaj else ''
                ET.SubElement(kozonseges_tetel, 'bank_arf').text = f"{float(t['provbanke']):.2f}" if t['provbanke'] else '0.00'
                ET.SubElement(kozonseges_tetel, 'honnan_hova').text = ''
                ET.SubElement(kozonseges_tetel, 'vevo_kod').text = replace_croatian_chars(t['prodaoime'])
                ET.SubElement(kozonseges_tetel, 'vevo_cim').text = ''
                ET.SubElement(kozonseges_tetel, 'vevo_utlevel_id').text = replace_croatian_chars(t['prodaodok'])
                
                vevo_orszag_value = 'N' if t['prodaodok'] and 'BIH' not in str(t['prodaodok']).upper() else ''
                ET.SubElement(kozonseges_tetel, 'vevo_orszag').text = vevo_orszag_value
                
                nbr_counter += 1
                total_kozonseges += 1
            
            current_date += timedelta(days=1)
        
        # ═══════════════════════════════════════════════════════════
        # SPREMANJE XML-a
        # ═══════════════════════════════════════════════════════════
        
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        filename = f"{valto_nbr}_rpt_{timestamp}.XML"
        
        xml_folder = 'C:/XML'
        if not os.path.exists(xml_folder):
            os.makedirs(xml_folder)
        
        filepath = os.path.join(xml_folder, filename)
        
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(filepath, encoding='UTF-8', xml_declaration=True)
        
        # Post-processing: zamjena self-closing tagova
        with open(filepath, 'r', encoding='UTF-8') as f:
            xml_content = f.read()
        
        tags_to_fix = ['honnan_hova', 'vevo_kod', 'vevo_cim', 'vevo_utlevel_id', 'vevo_orszag']
        
        for tag in tags_to_fix:
            xml_content = xml_content.replace(f'<{tag} />', f'<{tag}></{tag}>')
            xml_content = xml_content.replace(f'<{tag}/>', f'<{tag}></{tag}>')
        
        with open(filepath, 'w', encoding='UTF-8') as f:
            f.write(xml_content)
        
        return filename
        
    except Exception as e:
        messagebox.showerror("Greška", f"Greška pri generiranju XML-a:\n{e}")
        return None


# ═══════════════════════════════════════════════════════════
# FTP UPLOAD
# ═══════════════════════════════════════════════════════════

def upload_to_ftp(filename):
    """
    Šalje XML datoteku na FTP server.
    
    Parametri:
        filename: string - naziv XML datoteke
    
    Vraća:
        bool - True ako uspješno, False ako greška
    """
    try:
        xml_folder = 'C:/XML'
        filepath = os.path.join(xml_folder, filename)
        
        if not os.path.exists(filepath):
            messagebox.showerror("Greška", f"Datoteka nije pronađena:\n{filepath}")
            return False
        
        ftp = FTP()
        ftp.connect(FTP_CONFIG['host'], 21)
        ftp.login(FTP_CONFIG['user'], FTP_CONFIG['password'])
        
        with open(filepath, 'rb') as file:
            ftp.storbinary(f'STOR {filename}', file)
        
        ftp.quit()
        
        return True
        
    except Exception as e:
        messagebox.showerror("Greška pri slanju", f"Greška pri slanju datoteke na FTP server:\n\n{e}")
        return False


# ═══════════════════════════════════════════════════════════
# GUI KREIRANJE
# ═══════════════════════════════════════════════════════════

root = tk.Tk()
root.title("Export Blagajničkih Transakcija")
root.geometry("500x400")
root.resizable(False, False)

title_label = tk.Label(root, text="Export Blagajničkih Transakcija", font=("Arial", 16, "bold"))
title_label.pack(pady=20)

date_frame = tk.Frame(root)
date_frame.pack(pady=20)

start_label = tk.Label(date_frame, text="Početni datum:", font=("Arial", 10))
start_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

start_date = DateEntry(date_frame, width=15, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
start_date.grid(row=0, column=1, padx=10, pady=10)

end_label = tk.Label(date_frame, text="Završni datum:", font=("Arial", 10))
end_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

end_date = DateEntry(date_frame, width=15, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
end_date.grid(row=1, column=1, padx=10, pady=10)

button_frame = tk.Frame(root)
button_frame.pack(pady=20)

status_label = tk.Label(root, text="Spremno za rad", font=("Arial", 9), fg="gray")
status_label.pack(pady=10)


# ═══════════════════════════════════════════════════════════
# EVENT HANDLER FUNKCIJE
# ═══════════════════════════════════════════════════════════

def generate_xml_handler():
    """Generira XML datoteku iz podataka iz baze."""
    status_label.config(text="Spajam se na bazu...", fg="blue")
    root.update()
    
    start = start_date.get_date()
    end = end_date.get_date()
    
    # Validacija datuma
    if end < start:
        status_label.config(text="❌ Neispravan raspon datuma", fg="red")
        messagebox.showwarning(
            "Neispravan unos",
            "Završni datum ne može biti manji od početnog!\n\n"
            f"Početni datum: {start.strftime('%d.%m.%Y')}\n"
            f"Završni datum: {end.strftime('%d.%m.%Y')}"
        )
        status_label.config(text="Spremno za rad", fg="gray")
        return
    
    if not connect_to_database():
        status_label.config(text="❌ Ne mogu se spojiti na bazu", fg="red")
        return
    
    valto_nbr = get_uniqueid()
    
    if not valto_nbr:
        status_label.config(text="❌ Greška pri dohvaćanju UNIQUEID", fg="red")
        return
    
    status_label.config(text="Generiram XML...", fg="blue")
    root.update()
    
    filename = generate_xml(valto_nbr, start, end)
    
    if not filename:
        status_label.config(text="❌ Greška pri generiranju XML-a", fg="red")
        return
    
    status_label.config(text=f"✓ XML kreiran: {filename}", fg="green")
    
    messagebox.showinfo(
        "Uspjeh",
        f"XML datoteka uspješno kreirana!\n\n"
        f"Naziv: {filename}\n"
        f"Lokacija: C:\\XML\\\n"
        f"POSLOVNICA: {valto_nbr}\n\n"
        f"SADA JE POŠALJITE NA SERVER",
    )
    
    btn_generate.config(state="disabled")
    btn_send.config(state="normal")
    
    global current_xml_file
    current_xml_file = filename


def send_to_ftp_handler():
    """Šalje XML datoteku na FTP server."""
    global current_xml_file
    
    if not current_xml_file:
        messagebox.showwarning("Upozorenje", "Nema generirane XML datoteke za slanje!")
        return
    
    status_label.config(text="Šaljem datoteku na server...", fg="blue")
    root.update()
    
    success = upload_to_ftp(current_xml_file)
    
    if success:
        status_label.config(text=f"✓ Datoteka poslana: {current_xml_file}", fg="green")
        messagebox.showinfo(
            "Uspjeh",
            f"XML datoteka uspješno poslana na server!\n\n"
            f"Datoteka: {current_xml_file}\n"
            f"Server: {FTP_CONFIG['host']}"
        )
        
        btn_generate.config(state="normal")
        btn_send.config(state="disabled")
        current_xml_file = None
        
    else:
        status_label.config(text="❌ Greška pri slanju na server", fg="red")


def on_closing():
    """Zatvara aplikaciju i konekciju na bazu."""
    close_database_connection()
    root.destroy()


# ═══════════════════════════════════════════════════════════
# DUGMAD
# ═══════════════════════════════════════════════════════════

btn_generate = tk.Button(
    button_frame,
    text="Generiraj XML",
    width=15,
    height=2,
    bg="#2196F3",
    fg="white",
    font=("Arial", 10, "bold"),
    cursor="hand2",
    command=generate_xml_handler
)
btn_generate.grid(row=0, column=0, padx=10)

btn_send = tk.Button(
    button_frame,
    text="Pošalji XML na server",
    width=18,
    height=2,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 10, "bold"),
    cursor="hand2",
    state="disabled",
    command=send_to_ftp_handler
)
btn_send.grid(row=0, column=1, padx=10)


# ═══════════════════════════════════════════════════════════
# POKRETANJE APLIKACIJE
# ═══════════════════════════════════════════════════════════

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
