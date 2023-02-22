def get_prices(market, blk, state):
    prices = state.prices(market, block_identifier=blk)
    return prices
