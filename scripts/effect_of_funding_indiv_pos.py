import pandas as pd
from brownie import chain
from scripts.state import positions
from scripts.state import prices
from scripts.events import event_utils as eu
from scripts import utils
from scripts.visualizations import visualizations as vis

MKT_ADDR = "0x7f72986e190bbd1d02dac52b8dda82eea363d313"
USER = "0x69e4cF9a2C778Fb5b08F14F65CFa2f425DCA3eAC".lower()
POS_ID = 246
FRM_BLK = 15949364
STEP = 86400


def main(mkt_addr=MKT_ADDR,
         user=USER,
         pos_id=POS_ID,
         frm_blk=FRM_BLK,
         step=STEP):
    '''
    Inputs:
        mkt_addr: Address of the market being analysed
        user: EOA of position builder
        pos_id: Position ID
        frm_blk: Block number at a sufficiently old time in history, after
        which user should have created position
        step: Interval at which value of position is queried (in secs)
    '''

    pos = (mkt_addr, user, pos_id)

    market = utils.load_contract(mkt_addr)
    state = utils.load_state()

    # Get all positions built
    build_df = eu.get_event_df(
        contract=market,
        from_block=frm_blk,
        event_type='Build'
    )

    # Get block number when position was built
    build_block = int(build_df[build_df.positionId == pos_id].blockNumber)

    # Get historic prices and position values at various blocks
    blk_l = list(range(build_block, chain.height, int(step/12)))
    values = []
    bids = []
    for i in blk_l:
        values.append(positions.pos_value_historic(pos, state, i))
        bids.append(prices.get_historic_bids(market, state, i))

    # Create dataframe
    df = pd.DataFrame({'block': blk_l, 'bid': bids, 'value': values})

    # Find out value of position only due to changes in bid price
    df['value_without_funding'] = (df.bid/df.bid[0]) * df.value[0]
    df['PnL'] = df.value - df.value[0]
    df['Pnl without funding'] = df.value_without_funding - df.value[0]
    df['% lost or gained due to funding'] = \
        (df.value/df.value_without_funding - 1) * 100

    # Get timestamps wrt blocks
    df['time'] = df['block'].apply(
        lambda x: eu.get_block_timestamp(x, "%Y-%m-%d")
    )

    # Plot
    plt = vis.lines_bar(df, 'time', 'PnL', 'Pnl without funding',
                        '% lost or gained due to funding',
                        'Time', '# OVL', 'Percentage')
    plt.show()
