import pandas as pd


def get_events(contract, from_block, to_block, event_type):
    events = contract.events.get_sequence(
        from_block=from_block,
        to_block=to_block,
        event_type=event_type
    )
    return events


def get_args_df(event_list):
    args = []
    for i in range(len(event_list)):
        args.append(event_list[i].args)
    return pd.DataFrame(args)


def get_event_df(contract, from_block, to_block=None, event_type=None):
    event_list = get_events(contract, from_block, to_block, event_type)
    args_df = get_args_df(event_list)
    event_df = pd.DataFrame(
        event_list,
        columns=['address', 'event', 'logIndex', 'transactionHash']
    )
    return event_df.join(args_df)


def transfer_cols(df):
    '''
    Add columns for joining with build, unwind and liq dfs
    '''
    df.loc[:, 'logIndexMinusOne'] = df.loc[:, 'logIndex'] - 1
    df.loc[:, 'logIndexMinusTwo'] = df.loc[:, 'logIndex'] - 2
    df.loc[:, 'logIndexMinusThr'] = df.loc[:, 'logIndex'] - 3
    return df
