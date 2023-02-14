from brownie import Contract, multicall
import pandas as pd
import numpy as np
import time


def get_args_df(event_list):
    args = []
    for i in range(len(event_list)):
        args.append(event_list[i].args)
    return pd.DataFrame(args)


def get_event_df(event_list, cols):
    args_df = get_args_df(event_list)
    event_df = pd.DataFrame(event_list, columns=cols)
    return event_df.join(args_df)


def load_contract(address):
    try:
        return Contract(address)
    except ValueError:
        return Contract.from_explorer(address)


def active_pos_value(positions, state):
    multicall(address='0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696')
    with multicall:
        pos_value = [state.value(pos[0], pos[1], pos[2])
                     for pos in positions]
    return pos_value


def main():
    # Load contracts
    market = load_contract('0x7f72986e190BBd1D02daC52b8DdA82eEa363d313')
    state = load_contract('0x477122219aa1F76E190f480a85af97DE0A643320')
    token = load_contract('0xdc77acc82cce1cc095cba197474cc06824ade6f7')
    print('Contracts loaded')
    # Get events and build pandas df
    market_events = market.events.get_sequence(from_block=15691468)
    token_events = token.events.get_sequence(from_block=15691468)
    build_df = get_event_df(
                market_events.Build,
                ['address', 'event', 'logIndex', 'transactionHash']
                )
    unwind_df = get_event_df(
                market_events.Unwind,
                ['address', 'event', 'logIndex', 'transactionHash']
                )
    liq_df = get_event_df(
                market_events.Liquidate,
                ['address', 'event', 'logIndex', 'transactionHash']
                )
    trans_df = get_event_df(
                token_events.Transfer,
                ['address', 'event', 'logIndex', 'transactionHash']
                )
    print('Dataframes built')
    # Add columns for joining with build, unwind and liq dfs
    trans_df.loc[:, 'logIndexMinusOne'] = trans_df.loc[:, 'logIndex'] - 1
    trans_df.loc[:, 'logIndexMinusTwo'] = trans_df.loc[:, 'logIndex'] - 2
    trans_df.loc[:, 'logIndexMinusThr'] = trans_df.loc[:, 'logIndex'] - 3

    # Join build and transfers to get initial collateral from `value`
    build_df = build_df.merge(
            trans_df, how='left',
            left_on=['address', 'transactionHash', 'logIndex', 'sender'],
            right_on=['to', 'transactionHash', 'logIndexMinusOne', 'from'])
    build_df = build_df.loc[:, ['address_x', 'debt', 'isLong', 'oi',
                                'positionId', 'price', 'sender', 'value']]
    build_df.columns = ['market', 'debt', 'isLong', 'oi', 'positionId',
                        'mid_price', 'user', 'amount_in']
    cols_num = ['debt', 'oi', 'amount_in']
    build_df[cols_num] = build_df[cols_num].apply(
                            pd.to_numeric, errors='coerce', axis=1)
    cols_dec = ['debt', 'amount_in']
    build_df[cols_dec] = build_df[cols_dec]/1e18

    # Remove build fees
    # Formula: collateral = (amount_in - debt*trading_fee)/(1 + trading_fee)
    build_df['amount_in'] =\
        (build_df.amount_in - (build_df.debt*0.00075))/(1.00075)
    print('Build data ready')
    # Add leverage info
    build_df['leverage'] = 1 + (build_df.debt/build_df.amount_in)

    # Join unwind and transfers to get value at close of position
    unwind_df = unwind_df.merge(
            trans_df, how='left',
            left_on=['address', 'transactionHash', 'logIndex', 'sender'],
            right_on=['from', 'transactionHash', 'logIndexMinusTwo', 'to'])
    unwind_df = unwind_df.loc[:, ['address_x', 'fraction', 'positionId',
                                  'sender', 'value']]
    unwind_df.columns = ['market', 'fraction', 'positionId',
                         'user', 'realised_value']
    unwind_df['realised_value'] = pd.to_numeric(unwind_df['realised_value'])
    unwind_df['realised_value'] = unwind_df['realised_value'].divide(1e18)
    unwind_df['fraction'] = unwind_df['fraction'].multiply(-1/1e18).add(1)
    # In case of multiple unwinds:
    # Reduce position fraction proportionate to previous fraction
    unwind_df = pd.DataFrame(
        unwind_df.groupby(['market', 'positionId', 'user'])['fraction']
                 .cumprod()
                 .rename('fraction_remain'),
        columns=['fraction_remain']).join(unwind_df)
    unwind_df.drop('fraction', axis=1, inplace=True)
    unwind_df = \
        unwind_df.groupby(['market', 'positionId', 'user'], as_index=False)\
                 .agg({'fraction_remain': 'min', 'realised_value': 'sum'})
    print('Unwind data ready')

    # Merge build and unwind dfs
    df = build_df.merge(unwind_df, how='left',
                        on=['market', 'user', 'positionId'])

    # Merge liquidations df
    liq_df = liq_df.loc[:, ['address', 'owner', 'positionId', 'price']]
    liq_df.columns = ['market', 'user', 'positionId', 'liq_price']
    df = df.merge(liq_df, how='left', on=['market', 'user', 'positionId'])
    df['liquidated'] = 'False'
    df.loc[~df['liq_price'].isna(), 'liquidated'] = 'True'
    df['unrealised_value'] = np.nan
    # For liquidated positions, realised value can be non zero if the position
    # was unwound partially before getting liquidated. But after getting
    # liquidated, unrealised value is set to zero and liquidated flag to True.
    df.loc[~df['liq_price'].isna(), 'unrealised_value'] = 0
    df.loc[(~df['liq_price'].isna())
           & (df['realised_value'].isna()), 'realised_value'] = 0
    df.loc[~df['liq_price'].isna(), 'fraction_remain'] = 0

    # All remaining positions haven't been unwound or liquidated
    df.loc[df['fraction_remain'].isna(), 'fraction_remain'] = 1
    df.loc[df['fraction_remain'] == 1, 'realised_value'] = 0
    print('Liquidations data ready')

    # Get unrealised values
    pos = df.loc[df['fraction_remain'] > 0, ['market', 'user', 'positionId']]
    pos_list = pos.values.tolist()
    pos_values = active_pos_value(pos_list, state)
    pos['active_pos_value'] = pos_values
    pos['active_pos_value'] = pos['active_pos_value']/1e18
    df = df.merge(pos, how='left', on=['market', 'user', 'positionId'])
    df['unrealised_value'] = df.unrealised_value.combine_first(
                                                    df.active_pos_value)
    df.drop('active_pos_value', axis=1, inplace=True)
    df.loc[df['unrealised_value'].isna(), 'unrealised_value'] = 0

    # Get PnLs and PnL percentages
    df['rpnl'] =\
        df.realised_value - ((1-df.fraction_remain) * df.amount_in)
    df['rpnl_perc'] =\
        df['rpnl']/((1-df.fraction_remain) * df.amount_in)
    # If liquidated, then realised value to be compared to entire amount_in
    df.loc[df.liquidated == 'True', 'rpnl'] = df.realised_value - df.amount_in
    df.loc[df.liquidated == 'True', 'rpnl_perc'] = df['rpnl']/df.amount_in
    df['upnl'] = df.unrealised_value - (df.fraction_remain * df.amount_in)
    df['upnl'] = pd.to_numeric(df['upnl'])
    df['upnl_perc'] = df['upnl']/(df.fraction_remain * df.amount_in)
    df['total_pnl'] = (df.realised_value + df.unrealised_value) - df.amount_in
    df['total_pnl_perc'] = df.total_pnl/df.amount_in
    perc_cols = ['rpnl_perc', 'upnl_perc', 'total_pnl_perc']
    df.loc[:, perc_cols] = df.loc[:, perc_cols].fillna(0)
    df.loc[:, perc_cols] = df.loc[:, perc_cols].multiply(100)
    print('PnLs calculated')
    cols = ['market', 'user', 'positionId', 'debt', 'oi', 'mid_price',
            'isLong', 'amount_in', 'leverage', 'fraction_remain', 'liquidated',
            'liq_price', 'realised_value', 'rpnl', 'rpnl_perc',
            'unrealised_value', 'upnl', 'upnl_perc',
            'total_pnl', 'total_pnl_perc']
    df = df[cols]
    df.to_csv('csv/litterbox_pnl_' + time.strftime("%Y%m%d-%H%M%S") + '.csv')
    print('CSV saved!')
