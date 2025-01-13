from abc import ABC, abstractmethod

class TradeDecision(ABC):

    def __init__(self):
        pass
    @abstractmethod
    def get_data(self):
        """ Get data for model
        """ 
        pass

    @abstractmethod
    def decide(self):
        """ Decide wheteher to buy or sell 
        """ 
        pass

