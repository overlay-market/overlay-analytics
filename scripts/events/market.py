from brownie import Contract


class Market:
    def __init__(self, addr):
        self.addr = addr
        self.market = Contract.from_explorer(addr)
