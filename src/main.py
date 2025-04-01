import pandas as pd
import logging
from Classes.TxTable import TxTable  # Modifica qui
from Classes.Wallet import Wallet
from Classes.CostElement import CostElement
from globalDataAndUtils import print_current_EOY_non_zero_wallets

# Configura il logger
LOG_FILE = "transaction_log.txt"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s: %(message)s',
    filename=LOG_FILE,
    filemode='w'
)

# Istanzia la tabella (caricata una sola volta)
print("Caricamento della TxTable in corso...")
table = TxTable()
print("TxTable caricata con successo!")

# Ciclo interattivo
while True:
    command = input("Inserisci un comando (es. 'print', 'wallets', 'exit'): ").strip().lower()
    
    if command == "print":
        table.print_relevant_transactions()
    elif command == "wallets":
        print_current_EOY_non_zero_wallets(500)
    elif command == "exit":
        print_current_EOY_non_zero_wallets()
        print("Uscita dal programma.")
        break
    else:
        print("Comando non riconosciuto. Opzioni: 'print', 'wallets', 'exit'")