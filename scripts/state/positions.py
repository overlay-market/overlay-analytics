from brownie import multicall


def active_pos_value(positions, state):
    multicall(address='0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696')
    with multicall:
        pos_value = [state.value(pos[0], pos[1], pos[2])
                     for pos in positions]
    return pos_value


def pos_value_historic(pos, state, blk):
    pos_value = state.value(pos[0], pos[1], pos[2], block_identifier=blk)
    return pos_value
