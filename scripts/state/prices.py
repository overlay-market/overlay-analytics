def get_historic_prices(market, state, blk):
    prices = state.prices(market, block_identifier=blk)
    return prices
