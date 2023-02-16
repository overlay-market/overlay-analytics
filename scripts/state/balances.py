from brownie import multicall


def get_current_balances(users, token):
    multicall(address='0x5BA1e12693Dc8F9c48aAD8770482f4739bEeD696')
    with multicall:
        bal = [token.balanceOf(user) for user in users]
    return bal
