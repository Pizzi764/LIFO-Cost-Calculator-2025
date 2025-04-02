import math
from enum import Enum
from datetime import datetime
from Classes import CostElement
from globalDataAndUtils import *

class TxType(Enum):
    TRANSFER = 'TRANSFER'
    EXCHANGE = 'EXCHANGE'
    NFT = 'NFT'
    POOL = 'POOL'
    FIAT = 'FIAT'
    FEES = 'FEES'
    SPEND = 'SPEND'
    PNL = 'PNL'
    AIRDROP = 'AIRDROP'
    INTEREST = 'INTEREST'
    CASH_OUT = 'CASH_OUT'
    CASH_IN = 'CASH_IN'
    COST = 'COST'

class Tx:
    def __init__(self, row_number, row_data):
        self.row_number = row_number
        self.timestamp = row_data[TIMESTAMP_COLUMN]
        self.tx_type = row_data[TX_TYPE_COLUMN]
        self.cost_element_in = None
        self.cost_element_out = None
        self.original_cost_elements = []
        self.remaining_cost_element = None
        self.EURvalue = 0
        self.cost = 0
        self.comment = ""
        self.fiscal_relevance = False
        self.exchange_rate = None

    def __str__(self):
        formatted_timestamp = self.timestamp.strftime("%d-%m-%y %H:%M")
        output = f"Tx:{self.row_number} [{self.tx_type}] @ {formatted_timestamp}\n"
        
        if self.cost_element_out and self.original_cost_elements:
            output += f"  Costo Estratto (LIFO) da {get_wallet_name_by_column(self.cost_element_out.column)}:\n"
            for orig in self.original_cost_elements:
                output += f"    - Origine: Q:{orig.quantity:.8f} {orig.symbol}, Costo: {orig.cost:.8f}€ @ {orig.timestamp.strftime('%d-%m-%y %H:%M')}\n"
            output += "    - Splittato:\n"
            output += f"      * Estratto: Q:{self.cost_element_out.quantity:.8f} {self.cost_element_out.symbol}, Costo: {self.cost_element_out.cost:.8f}€\n"
            if self.remaining_cost_element:
                output += f"      * Rimanente: Q:{self.remaining_cost_element.quantity:.8f} {self.remaining_cost_element.symbol}, Costo: {self.remaining_cost_element.cost:.8f}€\n"
        
        if self.cost_element_in:
            output += f"  Destinazione su {get_wallet_name_by_column(self.cost_element_in.column)}:\n"
            output += f"    - Aggiunto: Q:{self.cost_element_in.quantity:.8f} {self.cost_element_in.symbol}, Costo Base: {self.cost_element_in.cost:.8f}€\n"
        
        if self.cost_element_out and self.cost_element_in:
            output += f"  Riepilogo: Q:{self.cost_element_out.quantity:.8f} {self.cost_element_out.symbol} -> Q:{self.cost_element_in.quantity:.8f} {self.cost_element_in.symbol}, Costo: {self.cost_element_out.cost:.8f}€"
        
        return output