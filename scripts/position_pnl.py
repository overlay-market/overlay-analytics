import pandas as pd
from scripts.events import event_utils as eu
from scripts.events import build, unwind
from scripts.events import liquidations as liq
from scripts.state import positions
from scripts import utils


def main(addr, from_blk):
    # Load contracts
    market = utils.load_contract(addr)
    state = utils.load_contract('0x477122219aa1F76E190f480a85af97DE0A643320')
    token = utils.load_contract('0xdc77acc82cce1cc095cba197474cc06824ade6f7')
    print('Contracts loaded')
    # Get events dataframes
    build_df = eu.get_event_df(
        contract=market,
        from_block=from_blk,
        event_type='Build'
    )
    unwind_df = eu.get_event_df(
        contract=market,
        from_block=from_blk,
        event_type='Unwind'
    )
    liq_df = eu.get_event_df(
        contract=market,
        from_block=from_blk,
        event_type='Liquidate'
    )
    trans_df = eu.get_event_df(
        contract=token,
        from_block=from_blk,
        event_type='Transfer'
    )
    trans_df = eu.transfer_cols(trans_df)
    print('Dataframes built')

    # Join build and transfers to get initial collateral from `value`
    build_df = build.join_build_trans(build_df, trans_df)

    # Remove build fees
    build_df = build.remove_build_fees(build_df)

    # Add leverage info
    build_df = build.add_lev_col(build_df)

    # Get value and fraction unwound
    unwind_df = unwind.get_unwound_value(unwind_df, trans_df)

    # Merge build and unwind dfs
    df = build_df.merge(unwind_df, how='left',
                        on=['market', 'user', 'positionId'])

    # Merge liquidations df
    df = liq.merge_liqs(df, liq_df)

    # Get unrealised values
    pos = df.loc[df['fraction_remain'] > 0, ['market', 'user', 'positionId']]
    pos_list = pos.values.tolist()
    pos_values = positions.active_pos_value(pos_list, state)
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
    df['total_pnl'] = pd.to_numeric(df['total_pnl'])
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
    df['user'] = df.user.str.lower()
    return df
