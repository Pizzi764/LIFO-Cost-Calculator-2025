from globalDataAndUtils import get_wallet_name_by_column
from datetime import datetime

class CostElement:
    def __init__(self, timestamp, quantity, symbol, cost, column):
        self.cost = cost # E' sempre il costo totale della bag
        self.symbol = symbol
        self.quantity = quantity
        self.column = column
        self.timestamp = timestamp

    def total_cost(self):
        return self.cost * self.quantity

    # ridefiniamo la stampa di un CostElement
    def __str__(self):
        walletName = get_wallet_name_by_column(self.column)
        formatted_cost = "{:.2f}".format(self.cost)
        formatted_qty = "{:.8f}".format(self.quantity)
        # Formatta il timestamp come richiesto
        formatted_timestamp = self.timestamp.strftime("%d-%m-%y %H:%M")

        return f"({formatted_timestamp}) Q:{formatted_qty}{self.symbol} C:{formatted_cost}€, {walletName}"

    def copy(self):
        # Crea una nuova istanza di CostElement con gli stessi attributi dell'istanza corrente
        return CostElement(timestamp=self.timestamp,
                           quantity=self.quantity,
                           symbol=self.symbol,
                           cost=self.cost,
                           column=self.column)

    def subtract_quantity(self, quantity_to_subtract, timestamp, atLoss=False):
        # toglie la quantità dall'elemento sorgente e ritorna un nuovo elemento con la quantità sottratta dal primo
        # ricalcola i costi del sorgente in maniera proporzionale ovvero
        # Esempio:
        # - sorgente (self) Quantità 10, Costo 10 (costo unitario 1)
        # - quantity_to_subtract = 2
        # - timestamp 1/1/1970
        # Risultati saranno:
        # self.quantity = 8
        # self.cost = 8
        # self.timestamp deve restare invariato
        # destination_cost_element.quantity = 2
        # destination_cost_element.cost = 2
        # destination_cost_element.timestamp = timestamp
        # symbol e column uguali a quelli di self

        if quantity_to_subtract == 0:
            raise ValueError("Quantità da sottrarre non può esser zero")

        if quantity_to_subtract > self.quantity:
            raise ValueError("Quantità da sottrarre maggiore della quantità disponibile")



        # calcolo del costo unitario
        ratio = self.cost / self.quantity

        # Arrotondamento del costo a 8 cifre decimali
        ratio = round(ratio, 8)

        # Calcolo della nuova quantità e costo del sorgente
        self.quantity -= quantity_to_subtract
        self.cost = self.quantity * ratio

        destination_quantity = quantity_to_subtract
        destination_cost = destination_quantity * ratio

        # Creazione di un nuovo oggetto CostElement con la quantità sottratta
        destination_cost_element = CostElement(timestamp=timestamp,
                                               quantity=destination_quantity,
                                               symbol=self.symbol,
                                               cost=destination_cost,
                                               column=self.column)

        return destination_cost_element