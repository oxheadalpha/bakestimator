import argparse

import requests

from . import calc
from . import fmt

RPC_CONSTANTS = "chains/main/blocks/head/context/constants"
RPC_ACTIVE_ROLLS = "chains/main/blocks/head/votes/total_voting_power"


def fetch_constants(tezos_rpc_url):
    return requests.get(f"{tezos_rpc_url}/{RPC_CONSTANTS}").json()


def fetch_active_rolls(tezos_rpc_url):
    return requests.get(f"{tezos_rpc_url}/{RPC_ACTIVE_ROLLS}").json()


def network_name_to_rpc(networks, network_name):
    url = networks.get(network_name)
    if url is None:
        raise Exception(
            f"Unknown network. Network must be one of: {sorted(networks.keys())}"
        )
    return url


def parse_args():

    p = argparse.ArgumentParser()
    p.add_argument(
        "-c",
        "--cycles",
        type=int,
        help=(
            "Calculate estimates for this number of cycles. "
            "By default estimates are calculated for "
            "preserved_cycles for selected network"
        ),
    )
    p.add_argument(
        "-r",
        "--rolls",
        default=1,
        type=int,
        help="Calculate estimates for this number of rolls of tez used for baking",
    )
    p.add_argument("--confidence", default=0.9, type=float)
    p.add_argument(
        "-n",
        "--network",
        default="mainnet",
        help="name of Tezos network. Default: %(default)s",
    )
    p.add_argument(
        "--rpc",
        help="Custom URL for Tezos node RPC, overrides one derived from --network",
    )

    return p.parse_args()


def fetch_test_networks():
    testnets_info_url = "https://teztnets.xyz/teztnets.json"
    name2rpc = {}
    try:
        testnets = requests.get(testnets_info_url).json()
    except err:
        print(f"Failed to get testnet info from {testnets_info_url}")
    else:
        for (key, net) in testnets.items():
            if "rpc_url" not in net:
                print(f"rpc url not provided for {key}, skipping")
            else:
                name2rpc[net.get("human_name", key).lower()] = net["rpc_url"]
                name2rpc[key] = net["rpc_url"]
    return name2rpc


def main():
    args = parse_args()
    rpc = args.rpc or network_name_to_rpc(
        dict(mainnet="https://mainnet.api.tez.ie", **fetch_test_networks()),
        args.network.lower(),
    )
    constants = fetch_constants(rpc)
    active_rolls = fetch_active_rolls(rpc)
    preserved_cycles = constants["preserved_cycles"]
    roll_size = int(constants["tokens_per_roll"])
    print(f"preserved cycles: {preserved_cycles}")
    print(f"roll size: {roll_size//calc.MUTEZ}")
    print()
    args_from_constants = calc.args_from_constants(constants)

    result = calc.compute(
        active_rolls,
        cycles=args.cycles or preserved_cycles,
        baking_rolls=args.rolls,
        confidence=args.confidence,
        **args_from_constants,
    )
    print(fmt.text(result))
