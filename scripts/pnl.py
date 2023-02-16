from brownie import Contract, multicall
import pandas as pd
import numpy as np
import time
from scripts.events import event_utils as eu
from scripts import utils


def active_pos_value(positions, state):
    multicall(address='0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696')
    with multicall:
        pos_value = [state.value(pos[0], pos[1], pos[2])
                     for pos in positions]
    return pos_value


def main(addr, from_block):
    # Load contracts
    market = utils.load_contract(addr)
    state = utils.load_contract('0x477122219aa1F76E190f480a85af97DE0A643320')
    token = utils.load_contract('0xdc77acc82cce1cc095cba197474cc06824ade6f7')
    print('Contracts loaded')
    # Get events dataframes
    build_df = eu.get_event_df(
        contract=market,
        from_block=from_block,
        event_type='Build'
    )
    unwind_df = eu.get_event_df(
        contract=market,
        from_block=from_block,
        event_type='Unwind'
    )
    liq_df = eu.get_event_df(
        contract=market,
        from_block=from_block,
        event_type='Liquidate'
    )
    trans_df = eu.get_event_df(
        contract=token,
        from_block=from_block,
        event_type='Transfer'
    )
    trans_df = eu.transfer_cols(trans_df)
    print('Dataframes built')
