import argparse

import requests

from . import tenderbake

RPC_CONSTANTS = "chains/main/blocks/head/context/constants"
RPC_TOTAL_VOTING_POWER = "chains/main/blocks/head/votes/total_voting_power"


def fetch_constants(tezos_rpc_url):
    return requests.get(f"{tezos_rpc_url}/{RPC_CONSTANTS}").json()


def fetch_total_voting_power(tezos_rpc_url):
    return requests.get(f"{tezos_rpc_url}/{RPC_TOTAL_VOTING_POWER}").json()


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
        default=1,
        help=("Calculate estimates for this number of cycles. Default: %(default)s"),
    )

    p.add_argument(
        "-b",
        "--full-balance",
        default=6000.0,
        type=float,
        help=(
            "[tenderbake] Calculate estimates using this number as baker's full balance. "
            "Default: %(default)s"
        ),
    )
    p.add_argument(
        "-D",
        "--deposit-limit",
        default=None,
        type=float,
        help=(
            "[tenderbake] Calculate estimates with this deposit limit. "
            "If not specified, max deposit if baker's full balance. "
            "Default: %(default)s"
        ),
    )

    p.add_argument(
        "-d",
        "--delegated-balance",
        default=0.0,
        type=float,
        help=(
            "[tenderbake] Calculate estimates assuming this delegated balance. "
            "Default: %(default)s"
        ),
    )

    p.add_argument(
        "--confidence",
        default=0.9,
        type=float,
        help=(
            "Probability that calculated max values are not exceeded. "
            "Default: %(default)s"
        ),
    )
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
    except Exception:
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
    total_voting_power = fetch_total_voting_power(rpc)
    preserved_cycles = constants["preserved_cycles"]
    if isinstance(total_voting_power, str):
        # in Jakarta total voting power is total active stake in mutez
        total_active_stake = int(total_voting_power)
    else:
        raise Exception("Unexpected total_voting_power value %r" % total_voting_power)
        # in Ithaca total voting power is the same as in previous protocols - number of rolls
    print(f"preserved cycles: {preserved_cycles}")
    print()

    minimal_stake = int(constants["minimal_stake"])
    print(
        tenderbake.run(
            constants,
            total_active_stake,
            cycles=args.cycles,
            confidence=0.9,
            full_balance=args.full_balance,
            delegated_balance=args.delegated_balance,
            eligibility_threshold=minimal_stake,
        )
    )
