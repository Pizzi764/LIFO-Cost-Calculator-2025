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
        self.timestamp = row_data[TIMESTAMP_COLUMN]  # Attributo timestamp dalla riga
        self.tx_type = row_data[TX_TYPE_COLUMN]  # Attributo tx_type dalla riga
        self.cost_element_in: CostElement = None  # la quantità e il costo della coin in ingresso alla tx
        self.cost_element_out: CostElement = None  # la quantità e il costo della coin in uscita dalla tx
        self.EURvalue = 0  # questo è il valore in € della TX alla data di realizzo (se è fiscalmente rilevante con questi calcoliamo plusvalenza)
        self.cost = 0  # questo è il costo che la TX ha in € (valore di realizzo)
        self.comment = ""
        self.fiscal_relevance = False
        self.exchange_rate = None  # Nuovo campo per il tasso EUR/USD
        # self.reference_id = row_data[REF_ID_COLUMN]  # Attributo reference_id dalla riga

    def __str__(self):
        formatted_timestamp = datetime.strftime(self.timestamp, "%d-%m-%y %H:%M")
        if isinstance(self.comment, float) and math.isnan(self.comment):
            comment_str = ""
        else:
            comment_str = self.comment
        return f"Tx:{self.row_number}, {formatted_timestamp}, {self.tx_type}, " \
               f"[{self.cost_element_out}] --> [{self.cost_element_in}] {comment_str}"