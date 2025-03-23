
import pandas as pd
import logging
import webDataGet

from Classes.TxTable import *
from Classes.Wallet import Wallet
from Classes.CostElement import CostElement

# Configura il logger
logging.basicConfig(level=logging.DEBUG)

# Istanzia la tabella
table = TxTable()

table.print_relevant_transactions()

print("")

# table.sum_and_print_cash_in_transactions()

print("")

print("")

print("")

print_current_EOY_non_zero_wallets(370)

# print_wallets_not_near_zero_balance()



'''
def test_wallet():
    # Creiamo un wallet di esempio
    wallet = Wallet(1, "Sample Wallet", "BTC")

    # Aggiungiamo alcuni elementi di costo al wallet
    wallet.push_cost_element(CostElement(10, 100))  # Aggiungiamo un elemento di costo con quantità 10 e costo 100
    wallet.push_cost_element(CostElement(20, 200))  # Aggiungiamo un altro elemento di costo con quantità 20 e costo 200

    # Estraiamo una quantità normale dal wallet
    try:
        extracted_normal = wallet.extract(15)  # Estraiamo una quantità di 15
        print("Quantità estratta normalmente:", extracted_normal)
    except ValueError as e:
        print("Errore durante l'estrazione:", e)

    # Estraiamo una quantità in perdita dal wallet
    try:
        extracted_loss = wallet.extract(25, atLoss=True)  # Estraiamo una quantità di 25 in perdita
        print("Quantità estratta in perdita:", extracted_loss)
    except ValueError as e:
        print("Errore durante l'estrazione in perdita:", e)


# Chiamiamo la funzione di test
test_wallet()
'''