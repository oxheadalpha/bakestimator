from scipy.stats import binom

MUTEZ = 1000000


def calc_active_stake(staking_balance, deposit_cap, frozen_deposit_percentage=10):
    return min(staking_balance, deposit_cap * 100 / frozen_deposit_percentage)


def compute(
    total_active_stake,
    staking_balance,
    deposit_cap,
    cycles=1,
    confidence=0.9,
    blocks_per_cycle=8192,
    frozen_deposit_percentage=10,
    consensus_committee_size=7000,
    consensus_threshold=4667,
    endorsing_reward_per_slot=2857,
    baking_reward_fixed_portion=5000000,
    baking_reward_bonus_per_slot=4286,
):
    """
    >>> r = compute(100, 5, 0.5, consensus_committee_size=8000,endorsing_reward_per_slot=2500)
    >>> e = r['endorsements']
    >>> e['count']
    3276800.0
    >>> e['rewards']
    8192000000.0
    """
    active_stake = calc_active_stake(
        staking_balance,
        deposit_cap,
        frozen_deposit_percentage=frozen_deposit_percentage,
    )

    selection_probability = active_stake / total_active_stake

    block_count = blocks_per_cycle * cycles

    def mean_for_n(n):
        return selection_probability * n

    def max_for_n(n):
        return binom.ppf(confidence, n, selection_probability)

    endorsement_count = block_count * consensus_committee_size

    e_mean = mean_for_n(endorsement_count)
    e_rewards_mean = e_mean * endorsing_reward_per_slot

    max_bonus = (
        consensus_committee_size - consensus_threshold
    ) * baking_reward_bonus_per_slot

    b_mean = mean_for_n(block_count)
    b_max = max_for_n(block_count)

    b_rewards_mean_min = b_mean * baking_reward_fixed_portion
    b_rewards_mean_max = b_mean * (baking_reward_fixed_portion + max_bonus)

    b_rewards_max_min = b_max * baking_reward_fixed_portion
    b_rewards_max_max = b_max * (baking_reward_fixed_portion + max_bonus)

    return {
        "active_stake": active_stake,
        "cycles": cycles,
        "bakes": {
            "mean": {
                "count": b_mean,
                "rewards": [b_rewards_mean_min, b_rewards_mean_max],
            },
            "max": {
                "count": b_max,
                "rewards": [b_rewards_max_min, b_rewards_max_max],
            },
        },
        "endorsements": {"count": e_mean, "rewards": e_rewards_mean},
    }
