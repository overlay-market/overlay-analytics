import pandas as pd


def join_build_trans(build_df, trans_df):
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
    return build_df


def remove_build_fees(build_df):
    # Remove build fees
    # Formula: collateral = (amount_in - debt*trading_fee)/(1 + trading_fee)
    build_df['amount_in'] =\
        (build_df.amount_in - (build_df.debt*0.00075))/(1.00075)
    return build_df


def add_lev_col(build_df):
    # Add leverage info
    build_df['leverage'] = 1 + (build_df.debt/build_df.amount_in)
    return build_df
