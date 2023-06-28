from brownie import Contract, multicall
import pandas as pd


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


def main():
    token = load_contract('0xdc77acc82cce1cc095cba197474cc06824ade6f7')
    token_events = token.events.get_sequence(from_block=15691468)

    trans_df = get_event_df(
                token_events.Transfer,
                ['address', 'event', 'logIndex', 'transactionHash']
                )
    trans_df['from'] = trans_df['from'].str.lower()
    trans_df['to'] = trans_df['to'].str.lower()

    air = pd.read_csv('csv_inputs/airdropped_users.csv')
    air_tx = trans_df.merge(air, left_on='from', right_on='user', how='inner')
    air_tx2 = air_tx.merge(air, left_on='to', right_on='user', how='inner')
