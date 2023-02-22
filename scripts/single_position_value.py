from datetime import datetime
from scripts.state import positions
from scripts.state import prices
from scripts.events import event_utils as eu
from scripts import utils

MKT_ADDR = "0x7f72986e190bbd1d02dac52b8dda82eea363d313"
USER = "0x69e4cF9a2C778Fb5b08F14F65CFa2f425DCA3eAC".lower()
POS_ID = 246
FRM_BLK = 15949364


def main(mkt_addr=MKT_ADDR, user=USER, pos_id=POS_ID, frm_blk=FRM_BLK):
    pos = (mkt_addr, user, pos_id)

    market = utils.load_contract(mkt_addr)
    state = utils.load_state()

    # Get all positions built
    build_df = eu.get_event_df(
        contract=market,
        from_block=frm_blk,
        event_type='Build'
    )

    build_block = int(build_df[build_df.positionId == pos_id].blockNumber)
