import pandas as pd
import scripts.position_pnl as pp
from scripts.state import balances as bal
from scripts.utils import load_contract


def main():
    start_block = 15949364
    # Load OVL contract
    ovl = load_contract('0xdc77acc82cce1cc095cba197474cc06824ade6f7')

    # Get positions wise PnLs
    btc_pnl = pp.main('0x70cb456202e9ad25d3fdf1d0ac5d6b299a42dc99',
                      start_block)
    eth_pnl = pp.main('0x7f72986e190bbd1d02dac52b8dda82eea363d313',
                      start_block)

    # Get user wise PnLs
    btc_pnl = btc_pnl.loc[:, ['user', 'amount_in', 'realised_value']]\
        .groupby('user').sum().reset_index()
    eth_pnl = eth_pnl.loc[:, ['user', 'amount_in', 'realised_value']]\
        .groupby('user').sum().reset_index()
    total_pnl = eth_pnl.merge(btc_pnl, how='outer',
                              on='user', suffixes=('_eth', '_btc'))
    total_pnl.fillna(0, inplace=True)
    # total_pnl['total_value'] = \
    #     total_pnl[['amount_in_eth', 'amount_in_btc',
    #                'realised_value_eth', 'realised_value_btc']].sum(axis=1)

    # Get list of all position builders
    user_list = list(set(list(btc_pnl.user) + list(eth_pnl.user)))

    # Get initial and final OVL balances
    curr_bals = bal.get_current_balances(user_list, ovl)
    curr_bals = pd.DataFrame({'user': user_list, 'curr_balance': curr_bals})
    old_bals = bal.get_past_balances(user_list, ovl, start_block)
    old_bals = pd.DataFrame({'user': user_list, 'old_balance': old_bals})
    bals = curr_bals.merge(old_bals, on='user', how='inner')

    # Merge balances and PnLs for obtaining litterbox PnL
    lb_pnl = total_pnl.merge(bals, how='inner', on='user')

    # Get airdropped users
    air = pd.read_csv('csv_inputs/airdropped_users.csv')
    air_lb_pnl = lb_pnl.merge(air, on='user', how='inner')
    
    # Save lb pnls to csv
    air_lb_pnl.to_csv('csv/lb_pnls.csv')
