import numpy as np


def merge_liqs(df, liq_df):
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
    return df
