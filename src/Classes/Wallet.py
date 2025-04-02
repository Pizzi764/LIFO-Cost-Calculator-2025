from Classes.CostElement import CostElement
import logging
from globalDataAndUtils import remove_special_characters

class Wallet:
    def __init__(self, column, name, symbol):
        self.column = column
        self.name = remove_special_characters(name)
        self.symbol = symbol
        self.balance = 0
        self.total_cost = 0
        self.average_cost = 0
        self.cost_elements = []

    def __str__(self):
        elements_str = ""
        for index, cost_element in enumerate(self.cost_elements):
            elements_str += f"[{index:02}] {cost_element}\n"
        return (f"{self.name}"
                f" Balance: {self.balance:.2f} {self.symbol}, Costo totale: {self.total_cost:.2f} €, "
                f"Costo medio: {self.average_cost:.2f} €\n"
                f"{elements_str}")

    def extract(self, quantity_to_extract, timestamp, atLoss=False):
        extracted_elements = []
        original_elements = []
        remaining_cost_element = None

        while quantity_to_extract > 0 and self.cost_elements:
            original_cost_element = self.cost_elements.pop(0)
            original_elements.append(original_cost_element.copy())

            if quantity_to_extract >= original_cost_element.quantity:
                extracted_elements.append(original_cost_element)
                quantity_to_extract -= original_cost_element.quantity
            else:
                extracted_cost_element = original_cost_element.subtract_quantity(quantity_to_extract, timestamp)
                self.push_cost_element(original_cost_element)
                extracted_elements.append(extracted_cost_element)
                remaining_cost_element = original_cost_element
                quantity_to_extract = 0

        if quantity_to_extract > 0:
            raise ValueError("Terminati gli elementi nel wallet ma c'è ancora quantità da estrarre = " + str(quantity_to_extract))

        total_quantity = sum(element.quantity for element in extracted_elements)
        total_cost = sum(element.cost for element in extracted_elements)
        sum_element = CostElement(timestamp, total_quantity, self.symbol, total_cost, self.column)

        self.update_balance()

        return {
            "original_elements": original_elements,
            "extracted": sum_element,
            "remaining": remaining_cost_element
        }

    def push_cost_element(self, cost_element):
        self.cost_elements.insert(0, cost_element)
        self.update_balance()

    def update_balance(self):
        self.balance = 0
        self.total_cost = 0
        self.average_cost = 0
        for cost_element in self.cost_elements:
            self.balance += cost_element.quantity
            self.total_cost += cost_element.cost
        if self.balance > 0:
            self.average_cost = self.total_cost / self.balance