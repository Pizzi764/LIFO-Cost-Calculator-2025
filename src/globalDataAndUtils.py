# Import the logging module to set the log level
import logging
import re
from datetime import datetime

from webDataGet import get_historical_price_EUR


def excel_column_to_index(column_str):
    index = 0
    for char in column_str:
        index = index * 26 + (ord(char.upper()) - ord('A')) + 1
    return index - 1  # Sottrai 1 perché l'indice della colonna in Python inizia da 0


# Log level (set to DEBUG)
LOG_LEVEL = logging.DEBUG

EXCEL_FILE_PATH = 'data/TX2024-corretto.xlsx'
INITAL_DATA_FILE_PATH = 'data/initial-costs-2024.json'
SHEET_NAME = 'Transazioni'

FISCAL_YEAR = 2024
WALLET_HEADERS_ROW = 7
CURRENCY_SYMBOL_ROW = 8

FIRST_DATA_ROW = 9
LAST_DATA_ROW = 376

TIMESTAMP_COLUMN = excel_column_to_index("B")
REF_ID_COLUMN = excel_column_to_index("C")
TX_TYPE_COLUMN = excel_column_to_index("F")

FIRST_TX_DATA_COLUMN = excel_column_to_index("G")
LAST_TX_DATA_COLUMN = excel_column_to_index("BX")
TX_COMMENT_COLUMN = excel_column_to_index("BY")
COST_COLUMN = excel_column_to_index("E")

global global_wallets  # viene linkato dalla TxTable al momento della init


# Funzioni di Utilità

def find_wallet_by_column(column):
    """
    Trova un wallet nella lista in base alla colonna specificata.

    Args:
    wallets (list[Wallet]): La lista di wallet in cui cercare.
    column (int): Il valore della colonna da cercare.

    Returns:
    Wallet: L'oggetto wallet trovato.

    Raises:
    ValueError: Se il wallet non viene trovato.
    """
    for wallet in global_wallets:
        if wallet.column == column:
            return wallet
    raise ValueError(f"Wallet with column {column} not found.")


def get_wallet_name_by_column(column):
    if column == -1:
        return "SPENT"

    wallet = find_wallet_by_column(column)
    # Pulisci il nome del wallet dalle sequenze di escape come \n e \t
    clean_name = wallet.name.replace('\n', ' ').replace('\t', ' ')
    return clean_name.strip()  # Rimuove gli spazi bianchi iniziali e finali

def print_current_EOY_non_zero_wallets(tolerance):
    print("Wallets al a fine anno non near zero:")

    # valore complessivo portafogli
    tot_wallet_value = 0
    for wallet in global_wallets:
        # Ottieni la data 31/12 dell'anno fiscale
        fiscal_year_end_date = datetime(FISCAL_YEAR, 12, 31)

        # Ottieni il prezzo storico utilizzando la funzione 'get_historical_price'
        historical_price = get_historical_price_EUR(wallet.symbol, fiscal_year_end_date)

        # Calcola il valore del portafoglio
        wallet_value = wallet.balance * historical_price
        wallet_value_str = "{:.2f}".format(wallet_value)

        # Stampa il portafoglio se non è vicino allo zero
        if not(-tolerance <= wallet_value <= tolerance):
            print(f"{wallet}Valore al 31-12: {wallet_value_str} €\n\n")
            tot_wallet_value += wallet_value

    print(f"\nTotale di tutti i portafogli: {"{:.2f}".format(tot_wallet_value)}€")
    print(f"Tassa del 2* 1000 = {"{:.2f}".format(tot_wallet_value*0.002)}€")





def remove_special_characters(text):
    # Utilizziamo un'espressione regolare per rimuovere solo i caratteri di fine linea
    cleaned_text = text.replace('\n', '').replace('\r', '')
    return cleaned_text