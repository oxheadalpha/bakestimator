import requests
from scipy.stats import binom

RPC_CONSTANTS = "chains/main/blocks/head/context/constants"
RPC_ACTIVE_ROLLS = "chains/main/blocks/head/votes/total_voting_power"
RPC_METADATA = "chains/main/blocks/head/metadata"
RPC_NETWORK_VESION = "network/version"
MUTEZ = 1000000

DEFAULT_RPC = "https://mainnet-tezos.giganode.io"
# DEFAULT_RPC = "https://florence-tezos.giganode.io"


def fetch_constants(tezos_rpc_url=DEFAULT_RPC):
    return requests.get(f"{tezos_rpc_url}/{RPC_CONSTANTS}").json()


def fetch_active_rolls(tezos_rpc_url=DEFAULT_RPC):
    return requests.get(f"{tezos_rpc_url}/{RPC_ACTIVE_ROLLS}").json()


def stats(
    constants,
    active_rolls,
    cycles,
    baking_roll_count=1,
    confidence=0.9,
):

    one_roll_probability = 1.0 / active_rolls
    selection_probability = baking_roll_count * one_roll_probability

    blocks_per_cycle = constants["blocks_per_cycle"]

    block_security_deposit = int(constants["block_security_deposit"])
    endorsement_security_deposit = int(constants["endorsement_security_deposit"])
    # 'baking_reward_per_endorsement': ['1250000', '187500'],
    baking_reward_per_endorsement = int(constants["baking_reward_per_endorsement"][0])
    # 'endorsement_reward': ['1250000', '833333'],
    endorsement_reward = int(constants["endorsement_reward"][0])

    endorsers_per_block = constants["endorsers_per_block"]

    max_block_reward = baking_reward_per_endorsement * endorsers_per_block

    def mean_for_n(n):
        return selection_probability * n

    def max_for_n(n):
        return binom.ppf(confidence, n, selection_probability)

    def compute(cycles):
        block_count = blocks_per_cycle * cycles
        b_mean = mean_for_n(block_count)
        b_max = max_for_n(block_count)

        endorsement_count = blocks_per_cycle * endorsers_per_block * cycles
        e_mean = mean_for_n(endorsement_count)
        e_max = max_for_n(endorsement_count)

        b_deposits_mean = b_mean * block_security_deposit
        e_deposits_mean = e_mean * endorsement_security_deposit
        deposits_mean = b_deposits_mean + e_deposits_mean

        b_deposits_max = b_max * block_security_deposit
        e_deposits_max = e_max * endorsement_security_deposit
        deposits_max = b_deposits_max + e_deposits_max

        b_rewards_mean = b_mean * max_block_reward
        e_rewards_mean = e_mean * endorsement_reward
        rewards_mean = b_rewards_mean + e_rewards_mean

        b_rewards_max = b_max * max_block_reward
        e_rewards_max = e_max * endorsement_reward
        rewards_max = b_rewards_max + e_rewards_max

        def mkobj(count, deposits, rewards):
            return {
                "count": count,
                "deposits": deposits / MUTEZ,
                "rewards": rewards / MUTEZ,
            }

        return {
            "bakes": {
                "mean": mkobj(b_mean, b_deposits_mean, b_rewards_mean),
                "max": mkobj(
                    b_max,
                    b_deposits_max,
                    b_rewards_max,
                ),
            },
            "endorsements": {
                "mean": mkobj(e_mean, e_deposits_mean, e_rewards_mean),
                "max": mkobj(
                    e_max,
                    e_deposits_max,
                    e_rewards_max,
                ),
            },
            "total": {
                "mean": mkobj(
                    e_mean + b_mean,
                    e_deposits_mean + b_deposits_mean,
                    e_rewards_mean + b_deposits_mean,
                ),
                "max": mkobj(
                    e_max + b_max,
                    e_deposits_max + b_deposits_max,
                    e_rewards_max + b_rewards_max,
                ),
            },
        }

    return compute(cycles)


def fmt_text(result):
    output = []
    for key in ["bakes", "endorsements", "total"]:
        output.append(key)
        for key2 in ["mean", "max"]:
            output.append(f"  {key2}")
            d = result[key][key2]
            for key3 in ["count", "deposits", "rewards"]:
                output.append(f"    {key3:>8}: {d[key3]:.2f}")
        output.append("\n")
    return "\n".join(output)


if __name__ == "__main__":
    constants = fetch_constants()
    active_rolls = fetch_active_rolls()
    preserved_cycles = constants["preserved_cycles"]

    print(f"{active_rolls}=")

    import pprint

    for cycle in [1, preserved_cycles]:
        result = stats(constants, active_rolls, cycle)
        print(f"Cycles: {cycle}")
        print(fmt_text(result))
        print()
