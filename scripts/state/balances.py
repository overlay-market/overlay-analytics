from brownie import multicall


def get_current_balances(users, token):
    multicall(address='0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696')
    with multicall:
        bal = [token.balanceOf(user) for user in users]
    dec = int(token.decimals())
    return [b/(10**dec) for b in bal]


def get_past_balances(users, token, block):
    dec = int(token.decimals())
    bal = []
    for user in users:
        bal.append(
            token.balanceOf(user, block_identifier=block)/(10**dec)
        )
    return bal
