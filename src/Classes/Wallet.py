from Classes.CostElement import CostElement
import logging

from globalDataAndUtils import remove_special_characters


class Wallet:
    def __init__(self, column, name, symbol):
        self.column = column
        self.name = remove_special_characters(name)
        self.symbol = symbol
        self.balance = 0  # the total coins in the wallet
        self.total_cost = 0  # the total cost of all the coins in the wallet
        self.average_cost = 0  # the average cost of 1 coin in the wallet
        self.cost_elements = []

    # ridefiniamo come viene stampato il wallet
    def __str__(self):
        elements_str = ""
        for index, cost_element in enumerate(self.cost_elements):
            elements_str += f"[{index:02}] {cost_element}\n"
        return (f"{self.name}"
                f" Balance: {self.balance:.2f} {self.symbol}, Costo totale: {self.total_cost:.2f} €, "
                f"Costo medio: {self.average_cost:.2f} €\n"
                f"{elements_str}")


    # Main interface *******************************************

    # Insert coins on the wallet assigning them a cost basis
    """def insert(self, quantity, cost):
        new_cost_element = CostElement(0, quantity, "changeme", cost, self.column)
        self.cost_elements.insert(0, new_cost_element)  # add at the first position (instead of push)
        self.update_balance()
    """

    # Extracts coins from the wallet, returns a cost element obtained with LIFO method from the previous cost elements
    # Se è in perdita (atLoss) cambia come viene considerato il costo della quantità da estrarre ovvero non viene reso proporzionale
    # LOGICA DI ESTRAZIONE IN PERDITA TODO
    def extract(self, quantity_to_extract, timestamp, atLoss=False):
        logging.debug("wallet.extract " + self.name)
        extracted_elements = []

        # Estrai gli elementi fino a quando non finisci la quantità da estrarre
        while quantity_to_extract > 0 and self.cost_elements:
            original_cost_element = self.cost_elements.pop(0)  # Estrai il primo elemento dal wallet

            if quantity_to_extract >= original_cost_element.quantity:

                # Se l'elemento basta o servono ulteriori elementi per soddifare la quantità da estrarre, lo trasferisco immediatamente e proseguo
                logging.debug("Estrazione di " + str(original_cost_element))
                extracted_elements.append(original_cost_element)
                quantity_to_extract -= original_cost_element.quantity

            else:
                # devo splittare l'elemento originale in 2
                # mi viene in aiuto la subtract_quantity del CostElement che prende l'elemento originale e ne aggiusta i costi
                # restituendo un nuovo elemento con le nuove quantità e i costi aggiustati
                logging.debug("Split elemento (" + str(original_cost_element) + ") in:")

                # tolgo la quantità all'elemento corrente, ottengo new_dest_element
                # e riaggiungo l'elemento modificato all'array del wallet origine (self)
                extracted_cost_element = original_cost_element.subtract_quantity(quantity_to_extract, timestamp)
                logging.debug(original_cost_element)
                self.push_cost_element(original_cost_element)

                # creo il nuovo elemento di costo e lo aggiungo all'array di destinazione
                logging.debug(extracted_cost_element)
                extracted_elements.append(extracted_cost_element)
                quantity_to_extract = 0

        # Ora dobbiamo controllare se la quantità da estrarre è ancora positiva, nel caso generiamo una eccezione
        if quantity_to_extract > 0:
            raise ValueError("Terminati gli elementi nel wallet ma c'è ancora quantità da estrarre = " + str(
                quantity_to_extract))

        logging.debug("Elementi estratti")
        for index, element in enumerate(extracted_elements):
            logging.debug(f"[{index:02}] {element}")

        # ritorno un CostElement somma di quantità e costi
        total_quantity = sum(element.quantity for element in extracted_elements)
        total_cost = sum(element.cost for element in extracted_elements)
        sum_element = CostElement(timestamp, total_quantity, self.symbol, total_cost, self.column)

        self.update_balance()
        return sum_element

    # UTILS *******************************************

    def push_cost_element(self, cost_element):
        logging.debug("wallet.push_cost_element " + self.name)
        self.cost_elements.insert(0, cost_element)  # add at the first position (instead of push)
        self.update_balance()

    def update_balance(self):
        self.balance = 0
        self.total_cost = 0
        self.average_cost = 0

        # Calcola il costo totale e la quantità totale dagli elementi di costo
        for cost_element in self.cost_elements:
            self.balance += cost_element.quantity
            self.total_cost += cost_element.cost

        # Calcola il nuovo costo medio se ci sono elementi di costo
        if self.balance > 0:
            self.average_cost = self.total_cost / self.balance

# utilità
