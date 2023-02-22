def pos_value_historic(market, blk, state):
    prices = state.prices(market, block_identifier=blk)
    return prices
