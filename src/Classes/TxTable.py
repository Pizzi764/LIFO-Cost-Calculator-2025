import logging
import math
import sys
import json
from typing import List

import numpy as np
import pandas as pd

import globalDataAndUtils
from datetime import datetime
from Classes.CostElement import CostElement
from Classes.Wallet import Wallet
from Classes.Tx import TxType
from webDataGet import get_historical_price_EUR, get_EURUSD_exchange_rate

sys.path.append('../')  # Aggiunge il percorso della directory genitore al percorso di ricerca dei moduli

from globalDataAndUtils import *
from Classes.Tx import Tx


class TxTable:
    def __init__(self):
        self.df = pd.read_excel(EXCEL_FILE_PATH, SHEET_NAME, header=None)
        self.wallets = self.__init_wallets()  # Wallets
        self.transactions: List[Tx] = self.__init_load_transactions()  # crea le transazioni con dentro gli oggetti di costo

    # Inizializza i Wallets leggendo le intestazioni delle colonne della tabella
    def __init_wallets(self):

        # Inizializza una lista locale per memorizzare i wallets
        result_wallets = []

        # leggiamo le righe di nome, simbolo e valori iniziali
        names = self.df.iloc[WALLET_HEADERS_ROW - 1]
        symbols = self.df.iloc[CURRENCY_SYMBOL_ROW - 1]

        for col, (name, symbol) in enumerate(
                zip(names[FIRST_TX_DATA_COLUMN:LAST_TX_DATA_COLUMN + 1],
                    symbols[FIRST_TX_DATA_COLUMN:LAST_TX_DATA_COLUMN + 1])):

            # Inizializza il wallet con nome... se c'è anche il simbolo della currency mettilo altrimenti ""
            if isinstance(symbol, float) and math.isnan(symbol):
                symbol = ""
            table_column = FIRST_TX_DATA_COLUMN+col
            wallet = Wallet(table_column, name, symbol)

            #qui ora dobbiamo inserire il codice che va a leggere da un file json rappresentante 
            #le bag di costo del precedente anno per i calcoli LIFO
            pushInitDataIfAny(wallet)

            result_wallets.append(wallet)

        # Inizializzo il wallet speciale per gli Euro spesi di colonna -1
        specialEURwallet = Wallet(-1, "SpentEUR", "EUR")
        result_wallets.append(specialEURwallet)

        globalDataAndUtils.global_wallets = result_wallets
        return result_wallets

    # Carica le transazioni tipizzandole ed elaborandone i costi
    def __init_load_transactions(self):
        transactions: list[Tx] = []

        # Itera sul DataFrame dalle righe FIRST_DATA_ROW alla riga LAST_DATA_ROW
        for index, raw_row_data in self.df.iloc[FIRST_DATA_ROW - 1:LAST_DATA_ROW].iterrows():
            print(f"Processing row index: {index}")  # Aggiungi questo per debug
            # comincio a costruire la riga
            transaction = Tx(index + 1, raw_row_data)

            # ora prendo i dati grezzi dalle colonne e li vado a valutare in base al tipo di TX modificando gli elementi di transaction
            self.__parse_data_to_cost_elements(raw_row_data, transaction)

            # riporto il costo nel file excel
            self.df.at[index, COST_COLUMN] = transaction.cost
            # Save the updated DataFrame back to the Excel file
            self.df.to_excel(EXCEL_FILE_PATH, SHEET_NAME, index=False, header=False)

            transactions.append(transaction)
        return transactions

    # va a definire l'instradamento dei costi a seconda del tipo di TX
    def __parse_data_to_cost_elements(self, raw_row_data, transaction):
        # Prende i dati dal range di valori e li restituisce in un array ordinato in base al valore in ordine crescente
        # Così sappiamo che l'output è sempre il primo
        transferred_values = []
        for col in range(FIRST_TX_DATA_COLUMN, LAST_TX_DATA_COLUMN + 1):
            value = raw_row_data[col]
            if isinstance(value, (int, float)) and not np.isnan(value):
                transferred_values.append((value, col))
        transferred_values.sort()

        # Verifica se ci sono meno di 0 o più di 2 elementi nell'array
        if len(transferred_values) == 0:
            raise ValueError("No transferred values found")
        elif len(transferred_values) > 2:
            raise ValueError("More than 2 transferred values are not allowed")


        logging.debug("***************** TX BEGIN ******************")

        # Partenza del parsing in base ai tipi di TX
        if TxType(transaction.tx_type) == TxType.TRANSFER:
            self.__parse_value_transfer(transferred_values, transaction)


        elif TxType(transaction.tx_type) == TxType.EXCHANGE:
            self.__parse_value_transfer(transferred_values, transaction)


        elif TxType(transaction.tx_type) == TxType.PNL:
            self.__parse_PNL(transferred_values, transaction)

        elif TxType(transaction.tx_type) == TxType.COST:
            self.__parse_PNL(transferred_values, transaction)

        elif transaction.tx_type in [TxType.AIRDROP.name, TxType.INTEREST.name]:
            self.__parse_single_positive(transferred_values, 0, transaction, False)


        elif TxType(transaction.tx_type) == TxType.CASH_IN:
            # Questo è un transfer dalla banca al mondo cripto che si porta dietro un costo/quantità 1
            self.__parse_single_positive(transferred_values, transferred_values[0][0], transaction, False)


        elif transaction.tx_type in [TxType.FEES.name, TxType.CASH_OUT.name]:
            self.__parse_single_negative(transferred_values, transaction,False)


        elif transaction.tx_type in [TxType.SPEND.name]:
            self.__parse_single_negative(transferred_values, transaction,True)


        else:
            raise ValueError("Unknown transaction type: {}".format(transaction.tx_type))

        # calcoli finali
        if transaction.fiscal_relevance == True :
            # andiamo a vedere se l'elemento di input è USD o euro e lo mettiamo in euro in transaction.value
            if find_wallet_by_column(transaction.cost_element_in.column).symbol == "USD" :
                transaction.EURvalue = transaction.cost_element_in.quantity / get_EURUSD_exchange_rate(transaction.timestamp)
            else: # qui son per forza € (si potrebbe fare un controllo e generare una eccezione se non teli
                transaction.EURvalue = transaction.cost_element_in.quantity
        # aggiunta del commento dalla riga apposita
        # transaction.comment = raw_row_data[TX_COMMENT_COLUMN]

        logging.debug(transaction)
        logging.debug("*****************  TX END  ******************")
        logging.debug("")




    # Implementa il parsing per un solo valore in riga di tipo positivo (Interessi, airdrop etc)
    def __parse_single_positive(self, values, cost, transaction, fiscal_relevance=False):
        # Preparo wallet sorgente in base alle colonne da cui ho letto il dato in tabella
        wallet = find_wallet_by_column(values[0][1])

        if values[0][0] > 0:
            # Quando abbiamo valore positivo lo porto dentro al wallet col suo costo
            new_cost_element = CostElement(transaction.timestamp, values[0][0], wallet.symbol, cost, wallet.column)
            wallet.push_cost_element(new_cost_element)
            transaction.cost_element_in = new_cost_element.copy()
        else:
            raise ValueError("Value cannot be zero or negative in this case: {}".format(transaction.tx_type))

        transaction.fiscal_relevance = fiscal_relevance

    # Implementa il parsing per un solo valore in riga di tipo negativo (spend, nft-, fees etc)
    def __parse_single_negative(self, values, transaction, fiscal_relevance=False):
        # Preparo wallet sorgente in base alle colonne da cui ho letto il dato in tabella
        wallet = find_wallet_by_column(values[0][1])

        if values[0][0] >= 0:
            raise ValueError("Value cannot be zero or positive in this case: {}".format(transaction.tx_type))
        else:
            # Estraiaimo valore dal wallet
            new_cost_element = wallet.extract(-values[0][0], transaction.timestamp)
            transaction.cost_element_out = new_cost_element

        transaction.fiscal_relevance = fiscal_relevance
        # ma cosa succede se c'è rilevanza fiscale?
        # l'asset lo buttiamo fuori come se fosse stato convertito in EUR. Creaimo un cost element nuovo col val convertito.
        if fiscal_relevance:
            val_EUR_converted = get_historical_price_EUR(wallet.symbol, transaction.timestamp) * transaction.cost_element_out.quantity
            transaction.cost_element_in = CostElement(transaction.timestamp, val_EUR_converted, wallet.symbol,
                                                      transaction.cost_element_out.cost, -1) # -1 è lo special wallet degli euro spesi
            transaction.EURvalue = val_EUR_converted
            transaction.cost = transaction.cost_element_out.cost



    # Implementa il parsing per il tipo di transazione TRANSFER
    def __parse_PNL(self, values, transaction):
        # Preparo wallet sorgente in base alle colonne da cui ho letto il dato in tabella
        pnl_wallet = find_wallet_by_column(values[0][1])

        if values[0][0] > 0:
            # Quando abbiamo un PNL positivo sono soldi gratis che portiamo dentro al wallet a costo zero
            new_cost_element = CostElement(transaction.timestamp, values[0][0], pnl_wallet.symbol, 0, pnl_wallet.column)
            pnl_wallet.push_cost_element(new_cost_element)
            transaction.cost_element_in = new_cost_element
        else:
            # Quando abbiamo un PNL negativo sono perdite che portiamo dentro al wallet
            new_cost_element = pnl_wallet.extract(-values[0][0], transaction.timestamp, True)
            transaction.cost_element_out = new_cost_element

        transaction.fiscal_relevance = False


        # Implementa il parsing per il tipo di transazione TRANSFER

    def __parse_value_transfer(self, values, transaction):
        # Questa funzione viene usata tipicamente per Exchange o Transfer di valore


        # Preparo wallet sorgente e destinazione in base alle colonne da cui ho letto il dato in tabella
        source_wallet = find_wallet_by_column(values[0][1])
        destination_wallet = find_wallet_by_column(values[1][1])

        # estraggo la quantità dal wallet sorgente ottenendo l'elemento di costo (qui la extract ci dà già un valore nuovo)
        transaction.cost_element_out = source_wallet.extract(-values[0][0], transaction.timestamp)  #il primo elemento valore di values[0] è la q da estrarre

        # creo il nuovo elemento di costo da registrare nella TX come input e da mettere nel wallet di destinazione
        new_input_cost_element = CostElement(transaction.timestamp, values[1][0], destination_wallet.symbol, transaction.cost_element_out.cost,
                                             destination_wallet.column)
        transaction.cost_element_in = new_input_cost_element

        # qui dobbiamo creare un cost element per copia altrimenti andiamo a mettere un oggetto nel wallet che sta anche per riferimento nella Tx
        destination_wallet.push_cost_element(new_input_cost_element.copy())

        transaction.cost = new_input_cost_element.cost

        # La rilevanza fiscale dei transfer è gestita qui
        # se la transazione è di tipo EXCHANGE, la valuta di destinazione è "USD" o "EUR"
        # e la valuta di destinazione è diversa dalla valuta di origine
        if (transaction.tx_type == TxType.EXCHANGE.name and
                destination_wallet.symbol in ["USD", "EUR"] and
                destination_wallet.symbol != source_wallet.symbol):
            transaction.fiscal_relevance = True

    def print_relevant_transactions(self):
        total_profit = 0
        print("Transazioni rilevanti:")
        for index, transaction in enumerate(self.transactions, start=1):
            if transaction.fiscal_relevance:
                profit = transaction.EURvalue - transaction.cost
                formatted_profit = "{:.2f}".format(abs(profit))  # Formattazione a due cifre decimali
                if profit >= 0:
                    print(f"Plusv {formatted_profit}€ : {transaction}")
                else:
                    print(f"Minus {formatted_profit}€ : {transaction}")
                total_profit += profit

        formatted_total_profit = "{:.2f}".format(abs(total_profit))  # Formattazione a due cifre decimali
        print(f"\nSomma totale delle plusvalenze/minusvalenze: {formatted_total_profit} euro")

        # Calcolo dell'imposta sulle plusvalenze
        tax = total_profit * 0.26
        formatted_tax = "{:.2f}".format(abs(tax))  # Formattazione a due cifre decimali
        print(f"Tassa sulle plusvalenze (26%): {formatted_tax} euro")

    def sum_and_print_cash_in_transactions(self):
        total_cash_in_quantity = 0
        print("Transazioni di tipo CASH_IN:")
        for transaction in self.transactions:
            if transaction.tx_type == TxType.CASH_IN.name :
                total_cash_in_quantity += transaction.cost_element_in.quantity
                print(transaction)
        print(f"Somma delle quantità per le transazioni CASH_IN: {total_cash_in_quantity}")
        return total_cash_in_quantity
    


def pushInitDataIfAny(wallet):
    """
    Legge i dati iniziali da un file JSON e li pusha nel wallet in ordine cronologico crescente,
    se esistono.
    
    Args:
        wallet: Oggetto Wallet in cui pushare i CostElement iniziali.
    """
    try:
        # Apertura del file JSON
        with open(INITAL_DATA_FILE_PATH, 'r') as file:
            data = json.load(file)
        
        # Cerca il wallet nel JSON usando il nome
        for wallet_data in data:
            if wallet_data["wallet_name"] == wallet.name:
                # Trovato il wallet, ora processiamo i cost_elements
                cost_elements = wallet_data["cost_elements"]
                
                # Ordina i cost_elements per timestamp in ordine crescente
                sorted_elements = sorted(
                    cost_elements,
                    key=lambda x: datetime.strptime(x["timestamp"], "%d-%m-%y %H:%M")
                )
                
                # Inserisci gli elementi ordinati nel wallet
                for element in sorted_elements:
                    # Converti il timestamp in oggetto datetime
                    timestamp = datetime.strptime(element["timestamp"], "%d-%m-%y %H:%M")
                    quantity = element["quantity"]
                    cost = element["cost"]
                    symbol = element["symbol"]
                    
                    # Crea un nuovo CostElement
                    cost_element = CostElement(timestamp, quantity, symbol, cost, wallet.column)
                    
                    # Pusha il CostElement nel wallet
                    wallet.push_cost_element(cost_element)
                break  # Esci dal ciclo una volta trovato il wallet
                
    except FileNotFoundError:
        print(f"File JSON {INITAL_DATA_FILE_PATH} non trovato. Nessun dato iniziale caricato per {wallet.name}.")
    except json.JSONDecodeError:
        print(f"Errore nel parsing del file JSON {INITAL_DATA_FILE_PATH}.")
    except Exception as e:
        print(f"Errore durante il caricamento dei dati iniziali per {wallet.name}: {str(e)}")