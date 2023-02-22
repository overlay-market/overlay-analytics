from brownie import Contract


def load_contract(address):
    try:
        return Contract(address)
    except ValueError:
        return Contract.from_explorer(address)


def load_state():
    return load_contract('0x477122219aa1F76E190f480a85af97DE0A643320')
