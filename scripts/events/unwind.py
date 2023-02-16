import pandas as pd


def get_unwound_value(unwind_df, trans_df):
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
    return unwind_df
