def get_historic_prices(market, state, blk):
    prices = state.prices(market, block_identifier=blk)
    return [p/1e18 for p in prices]


def get_historic_bids(market, state, blk):
    return get_historic_prices(market, state, blk)[0]
