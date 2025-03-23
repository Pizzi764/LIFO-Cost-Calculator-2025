
import pandas as pd
import logging
import webDataGet
from Classes.TxTable import TxTable
from Classes.Wallet import Wallet
from Classes.CostElement import CostElement

# Configura il logger
logging.basicConfig(level=logging.DEBUG)

# Istanzia la tabella (caricata una sola volta)
print("Caricamento della TxTable in corso...")
table = TxTable()
print("TxTable caricata con successo!")

# Ciclo interattivo
while True:
    command = input("Inserisci un comando (es. 'print', 'cashin', 'eoy', 'exit'): ").strip().lower()
    
    if command == "print":
        table.print_relevant_transactions()
    elif command == "cashin":
        table.sum_and_print_cash_in_transactions()
    elif command == "eoy":
        days = int(input("Inserisci il numero di giorni per EOY (es. 370): "))
        print_current_EOY_non_zero_wallets(days)
    elif command == "exit":
        print("Uscita dal programma.")
        break
    else:
        print("Comando non riconosciuto. Opzioni: 'print', 'cashin', 'eoy', 'exit'")
