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


NETWORKS = {
    "main": "https://mainnet-tezos.giganode.io",
    "florence": "https://florence-tezos.giganode.io",
}


def network_name_to_rpc(network_name):
    url = NETWORKS.get(network_name)
    if url is None:
        raise Exception("Unknown network")
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
        default="main",
        choices=NETWORKS.keys(),
        help="name of Tezos network. Default: %(default)s",
    )
    p.add_argument(
        "--rpc",
        help="Custom URL for Tezos node RPC, overrides one derived from --network",
    )

    return p.parse_args()


def main():
    args = parse_args()
    rpc = args.rpc or network_name_to_rpc(args.network)
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
