import scripts.position_pnl as pp


def main():
    btc_pnl = pp.main('0x70cb456202e9ad25d3fdf1d0ac5d6b299a42dc99', 16002247)
    eth_pnl = pp.main('0x7f72986e190bbd1d02dac52b8dda82eea363d313', 16002247)

    # Get list of all position builders
    user_list = list(set(list(btc_pnl.user) + list(eth_pnl.user)))

    # Get initial and final OVL balances