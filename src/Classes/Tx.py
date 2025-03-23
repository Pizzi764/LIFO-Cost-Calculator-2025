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

class Tx:
    def __init__(self, row_number, row_data):
        self.row_number = row_number
        self.timestamp = row_data[TIMESTAMP_COLUMN]  # Attributo timestamp dalla riga
        self.tx_type = row_data[TX_TYPE_COLUMN]  # Attributo tx_type dalla riga
        self.cost_element_in: CostElement = None  # la quantità e il costo della coin in ingresso alla tx
        self.cost_element_out: CostElement = None  # la quantità e il costo della coin in uscita dalla tx
        self.EURvalue = 0 # questo è il valore in € della TX alla data di realizzo (se è fiscalmente rilevante con questi calcoliamo plusvalenza)
        self.cost = 0  # questo è il costo che la TX ha in €
        self.comment = ""
        self.fiscal_relevance = False
        # self.reference_id = row_data[REF_ID_COLUMN]  # Attributo reference_id dalla riga

    def __str__(self):
        # Formattazione del timestamp come data e ora
        formatted_timestamp = datetime.strftime(self.timestamp, "%d-%m-%y %H:%M")
        # Formattazione del costo con due cifre decimali
        formatted_cost = "{:.2f}".format(self.cost)
        formatted_EURvalue = "{:.2f}".format(self.EURvalue)

        # Controlla se self.comment è NaN
        if isinstance(self.comment, float) and math.isnan(self.comment):
            comment_str = ""
        else:
            comment_str = self.comment

        # Controlla se formatted_value è zero
        if self.EURvalue == 0:
            value_str = ""
        else:
            value_str = f"EURvalue={formatted_EURvalue}€ "

        formatted_value = "{:.2f}".format(self.EURvalue)

        return f"Tx:{self.row_number}, {formatted_timestamp}, {self.tx_type}, " \
               f"[{self.cost_element_out}] --> [{self.cost_element_in}], " \
               f"cost={formatted_cost}€ {value_str} {comment_str}"








