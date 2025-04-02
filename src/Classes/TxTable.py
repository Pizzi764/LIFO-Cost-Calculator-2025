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
sys.path.append('../')
from globalDataAndUtils import *
from Classes.Tx import Tx

class TxTable:
    def __init__(self):
        self.df = pd.read_excel(EXCEL_FILE_PATH, SHEET_NAME, header=None)
        self.wallets = self.__init_wallets()
        self.transactions: List[Tx] = self.__init_load_transactions()

    def __init_wallets(self):
        result_wallets = []
        names = self.df.iloc[WALLET_HEADERS_ROW - 1]
        symbols = self.df.iloc[CURRENCY_SYMBOL_ROW - 1]
        for col, (name, symbol) in enumerate(
                zip(names[FIRST_TX_DATA_COLUMN:LAST_TX_DATA_COLUMN + 1],
                    symbols[FIRST_TX_DATA_COLUMN:LAST_TX_DATA_COLUMN + 1])):
            if isinstance(symbol, float) and math.isnan(symbol):
                symbol = ""
            table_column = FIRST_TX_DATA_COLUMN + col
            wallet = Wallet(table_column, name, symbol)
            pushInitDataIfAny(wallet)
            result_wallets.append(wallet)
        specialEURwallet = Wallet(-1, "SpentEUR", "EUR")
        result_wallets.append(specialEURwallet)
        globalDataAndUtils.global_wallets = result_wallets
        return result_wallets

    def __init_load_transactions(self):
        transactions: list[Tx] = []
        for index, raw_row_data in self.df.iloc[FIRST_DATA_ROW - 1:LAST_DATA_ROW].iterrows():
            transaction = Tx(index + 1, raw_row_data)
            self.__parse_data_to_cost_elements(raw_row_data, transaction)
            self.df.at[index, COST_COLUMN] = transaction.cost
            if transaction.fiscal_relevance:
                self.df.at[index, FISCAL_RELEVANCE_COLUMN] = "SI"
            transactions.append(transaction)
        self.df.to_excel(EXCEL_FILE_PATH, SHEET_NAME, index=False, header=False)
        return transactions

    def __parse_value_transfer(self, values, transaction):
        source_wallet = find_wallet_by_column(values[0][1])
        destination_wallet = find_wallet_by_column(values[1][1])
        extract_result = source_wallet.extract(-values[0][0], transaction.timestamp)
        transaction.cost_element_out = extract_result["extracted"]
        transaction.original_cost_elements = extract_result["original_elements"]
        transaction.remaining_cost_element = extract_result["remaining"]
        
        if transaction.tx_type == TxType.EXCHANGE.name and destination_wallet.symbol in ["USD", "EUR", "USDC"]:
            if destination_wallet.symbol == "EUR":
                cost_in_eur = values[1][0]
                transaction.exchange_rate = 1.0
            else:
                rate = get_EURUSD_exchange_rate(transaction.timestamp)
                if rate is None:
                    logging.error(f"Impossibile ottenere il tasso EUR/USD per {transaction.timestamp}, uso costo originale")
                    cost_in_eur = transaction.cost_element_out.cost
                    transaction.exchange_rate = None
                else:
                    cost_in_eur = values[1][0] / rate
                    transaction.exchange_rate = rate
        else:
            cost_in_eur = transaction.cost_element_out.cost
            transaction.exchange_rate = None

        new_input_cost_element = CostElement(transaction.timestamp, values[1][0], destination_wallet.symbol, 
                                             cost_in_eur, destination_wallet.column)
        transaction.cost_element_in = new_input_cost_element
        destination_wallet.push_cost_element(new_input_cost_element.copy())
        transaction.cost = new_input_cost_element.cost
        transaction.EURvalue = cost_in_eur

        if (transaction.tx_type == TxType.EXCHANGE.name and
                destination_wallet.symbol in ["USD", "EUR", "USDC"] and
                destination_wallet.symbol != source_wallet.symbol):
            transaction.fiscal_relevance = True
            logging.debug(f"Costo ricertificato per {destination_wallet.symbol}: {new_input_cost_element.cost} EUR")

    def __parse_data_to_cost_elements(self, raw_row_data, transaction):
        transferred_values = []
        for col in range(FIRST_TX_DATA_COLUMN, LAST_TX_DATA_COLUMN + 1):
            value = raw_row_data[col]
            if isinstance(value, (int, float)) and not np.isnan(value):
                transferred_values.append((value, col))
        transferred_values.sort()
        if len(transferred_values) == 0:
            raise ValueError("No transferred values found")
        elif len(transferred_values) > 2:
            raise ValueError("More than 2 transferred values are not allowed")
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
            self.__parse_single_positive(transferred_values, transferred_values[0][0], transaction, False)
        elif transaction.tx_type in [TxType.FEES.name, TxType.CASH_OUT.name]:
            self.__parse_single_negative(transferred_values, transaction, False)
        elif transaction.tx_type in [TxType.SPEND.name]:
            self.__parse_single_negative(transferred_values, transaction, True)
        else:
            raise ValueError("Unknown transaction type: {}".format(transaction.tx_type))
        output = str(transaction) + "\n\n"
        print(output, end="")
        logging.info(output)

    def __parse_single_positive(self, values, cost, transaction, fiscal_relevance=False):
        wallet = find_wallet_by_column(values[0][1])
        if values[0][0] > 0:
            new_cost_element = CostElement(transaction.timestamp, values[0][0], wallet.symbol, cost, wallet.column)
            wallet.push_cost_element(new_cost_element)
            transaction.cost_element_in = new_cost_element.copy()
        else:
            raise ValueError("Value cannot be zero or negative in this case: {}".format(transaction.tx_type))
        transaction.fiscal_relevance = fiscal_relevance

    def __parse_single_negative(self, values, transaction, fiscal_relevance=False):
        wallet = find_wallet_by_column(values[0][1])
        if values[0][0] >= 0:
            raise ValueError("Value cannot be zero or positive in this case: {}".format(transaction.tx_type))
        else:
            new_cost_element = wallet.extract(-values[0][0], transaction.timestamp)
            transaction.cost_element_out = new_cost_element
        transaction.fiscal_relevance = fiscal_relevance
        if fiscal_relevance:
            val_EUR_converted = get_historical_price_EUR(wallet.symbol, transaction.timestamp) * transaction.cost_element_out.quantity
            transaction.cost_element_in = CostElement(transaction.timestamp, val_EUR_converted, wallet.symbol,
                                                      transaction.cost_element_out.cost, -1)
            transaction.EURvalue = val_EUR_converted
            transaction.cost = transaction.cost_element_out.cost

    def __parse_PNL(self, values, transaction):
        pnl_wallet = find_wallet_by_column(values[0][1])
        if values[0][0] > 0:
            new_cost_element = CostElement(transaction.timestamp, values[0][0], pnl_wallet.symbol, 0, pnl_wallet.column)
            pnl_wallet.push_cost_element(new_cost_element)
            transaction.cost_element_in = new_cost_element
        else:
            new_cost_element = pnl_wallet.extract(-values[0][0], transaction.timestamp, True)
            transaction.cost_element_out = new_cost_element
        transaction.fiscal_relevance = False

    def print_relevant_transactions(self):
        headers = ["N° Tx", "Data", "Asset Venduto", "Asset Acquistato", "Costo (€)", "Ricavo (€)", "Plus/Minus (€)", "Tasso EUR/USD"]
        col_widths = [6, 15, 20, 20, 12, 12, 15, 12]
        
        # Stampa intestazione
        header_row = "".join(f"{header:<{width}}" for header, width in zip(headers, col_widths))
        print(header_row)
        print("-" * len(header_row))
        
        total_profit = 0
        for tx in self.transactions:
            if tx.fiscal_relevance:
                profit = tx.cost - tx.cost_element_out.cost
                total_profit += profit
                
                tx_num = f"{tx.row_number}"
                date = tx.timestamp.strftime("%d-%m-%y %H:%M")
                sold = f"{tx.cost_element_out.quantity:.2f} {tx.cost_element_out.symbol}"
                bought = f"{tx.cost_element_in.quantity:.2f} {tx.cost_element_in.symbol}"
                cost = f"{tx.cost_element_out.cost:.2f}"
                proceeds = f"{tx.cost:.2f}"
                plus_minus = f"{'+' if profit >= 0 else '-'}{abs(profit):.2f}"
                rate = f"{tx.exchange_rate:.4f}" if tx.exchange_rate else "N/A"
                
                row = [
                    tx_num, date, sold, bought, cost, proceeds, plus_minus, rate
                ]
                print("".join(f"{field:<{width}}" for field, width in zip(row, col_widths)))
        
        print("\n")
        formatted_total_profit = "{:.2f}".format(total_profit)
        print(f"Somma totale delle plusvalenze/minusvalenze: {formatted_total_profit} euro")
        tax = max(total_profit, 0) * 0.26
        formatted_tax = "{:.2f}".format(tax)
        print(f"Tassa sulle plusvalenze (26%): {formatted_tax} euro")

def pushInitDataIfAny(wallet):
    try:
        with open(INITAL_DATA_FILE_PATH, 'r') as file:
            data = json.load(file)
        for wallet_data in data:
            if wallet_data["wallet_name"] == wallet.name:
                cost_elements = wallet_data["cost_elements"]
                sorted_elements = sorted(
                    cost_elements,
                    key=lambda x: datetime.strptime(x["timestamp"], "%d-%m-%y %H:%M")
                )
                for element in sorted_elements:
                    timestamp = datetime.strptime(element["timestamp"], "%d-%m-%y %H:%M")
                    quantity = element["quantity"]
                    cost = element["cost"]
                    symbol = element["symbol"]
                    cost_element = CostElement(timestamp, quantity, symbol, cost, wallet.column)
                    wallet.push_cost_element(cost_element)
                break
    except FileNotFoundError:
        print(f"File JSON {INITAL_DATA_FILE_PATH} non trovato. Nessun dato iniziale caricato per {wallet.name}.")
    except json.JSONDecodeError:
        print(f"Errore nel parsing del file JSON {INITAL_DATA_FILE_PATH}.")
    except Exception as e:
        print(f"Errore durante il caricamento dei dati iniziali per {wallet.name}: {str(e)}")