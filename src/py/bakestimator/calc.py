from scipy.stats import binom

MUTEZ = 1000000


def args_from_constants(constants):
    return dict(
        blocks_per_cycle=constants["blocks_per_cycle"],
        block_security_deposit=int(constants["block_security_deposit"]),
        endorsement_security_deposit=int(constants["endorsement_security_deposit"]),
        # 'baking_reward_per_endorsement': ['1250000', '187500'],
        baking_reward_per_endorsement=int(
            constants["baking_reward_per_endorsement"][0]
        ),
        # 'endorsement_reward': ['1250000', '833333'],
        endorsement_reward=int(constants["endorsement_reward"][0]),
        endorsers_per_block=constants["endorsers_per_block"],
    )


def compute(
    active_rolls,
    cycles=1,
    baking_rolls=1,
    confidence=0.9,
    blocks_per_cycle=4096,
    block_security_deposit=512000000,
    endorsement_security_deposit=64000000,
    baking_reward_per_endorsement=1250000,
    endorsement_reward=1250000,
    endorsers_per_block=32,
):

    one_roll_probability = 1.0 / active_rolls
    selection_probability = baking_rolls * one_roll_probability
    max_block_reward = baking_reward_per_endorsement * endorsers_per_block

    def mean_for_n(n):
        return selection_probability * n

    def max_for_n(n):
        return binom.ppf(confidence, n, selection_probability)

    block_count = blocks_per_cycle * cycles

    b_mean = mean_for_n(block_count)
    b_max = max_for_n(block_count)

    endorsement_count = block_count * endorsers_per_block
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
        "active_rolls": active_rolls,
        "cycles": cycles,
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
                deposits_mean,
                rewards_mean,
            ),
            "max": mkobj(
                e_max + b_max,
                deposits_max,
                rewards_max,
            ),
        },
    }
