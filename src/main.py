import pandas as pd
import logging
from Classes.TxTable import TxTable
from Classes.Wallet import Wallet
from Classes.CostElement import CostElement
from globalDataAndUtils import print_current_EOY_non_zero_wallets

LOG_FILE = "transaction_log.txt"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s',
    filename=LOG_FILE,
    filemode='w'
)

print("Caricamento della TxTable in corso...")
table = TxTable()
print("TxTable caricata con successo!")

while True:
    command = input("Inserisci un comando (es. 'tx', 'wallets', 'exit'): ").strip().lower()
    
    if command == "tx":
        table.print_relevant_transactions()
    elif command == "wallets":
        print_current_EOY_non_zero_wallets(500)
    elif command == "exit":
        print("Uscita dal programma.")
        break
    else:
        print("Comando non riconosciuto. Opzioni: 'tx', 'wallets', 'exit'")