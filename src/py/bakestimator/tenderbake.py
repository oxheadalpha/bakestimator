from collections.abc import Iterable

from scipy.stats import binom

MUTEZ = 1000000


def calc_active_stake(staking_balance, deposit_cap, frozen_deposits_percentage=10):
    """
    >>> full_balance = 1000
    >>> calc_active_stake(9000, full_balance)
    9000.0
    >>> calc_active_stake(12000, full_balance)
    10000.0
    >>> calc_active_stake(9000, 400)
    4000.0
    >>> calc_active_stake(12000, 400)
    4000.0

    """
    return min(float(staking_balance), deposit_cap * 100 / frozen_deposits_percentage)


def args_from_constants(constants):
    """
    >>> c = {
    ...     "proof_of_work_nonce_size": 8,
    ...     "nonce_length": 32,
    ...     "max_anon_ops_per_block": 132,
    ...     "max_operation_data_length": 32768,
    ...     "max_proposals_per_delegate": 20,
    ...     "max_micheline_node_count": 50000,
    ...     "max_micheline_bytes_limit": 50000,
    ...     "max_allowed_global_constants_depth": 10000,
    ...     "cache_layout": ["100000000", "240000", "2560"],
    ...     "michelson_maximum_type_size": 2001,
    ...     "preserved_cycles": 3,
    ...     "blocks_per_cycle": 4096,
    ...     "blocks_per_commitment": 32,
    ...     "blocks_per_stake_snapshot": 256,
    ...     "blocks_per_voting_period": 20480,
    ...     "hard_gas_limit_per_operation": "1040000",
    ...     "hard_gas_limit_per_block": "5200000",
    ...     "proof_of_work_threshold": "70368744177663",
    ...     "tokens_per_roll": "6000000000",
    ...     "seed_nonce_revelation_tip": "125000",
    ...     "origination_size": 257,
    ...     "baking_reward_fixed_portion": "5000000",
    ...     "baking_reward_bonus_per_slot": "2143",
    ...     "endorsing_reward_per_slot": "1428",
    ...     "cost_per_byte": "250",
    ...     "hard_storage_limit_per_operation": "60000",
    ...     "quorum_min": 2000,
    ...     "quorum_max": 7000,
    ...     "min_proposal_quorum": 500,
    ...     "liquidity_baking_subsidy": "2500000",
    ...     "liquidity_baking_sunset_level": 525600,
    ...     "liquidity_baking_escape_ema_threshold": 666667,
    ...     "max_operations_time_to_live": 120,
    ...     "minimal_block_delay": "15",
    ...     "delay_increment_per_round": "5",
    ...     "consensus_committee_size": 7000,
    ...     "consensus_threshold": 4667,
    ...     "minimal_participation_ratio": {"numerator": 2, "denominator": 3},
    ...     "max_slashing_period": 2,
    ...     "frozen_deposits_percentage": 10,
    ...     "double_baking_punishment": "640000000",
    ...     "ratio_of_frozen_deposits_slashed_per_double_endorsement": {
    ...         "numerator": 1,
    ...         "denominator": 2,
    ...       }
    ...     }
    >>> r = {
    ...     "blocks_per_cycle": 4096,
    ...     "baking_reward_fixed_portion": 5000000,
    ...     "baking_reward_bonus_per_slot": 2143,
    ...     "endorsing_reward_per_slot": 1428,
    ...     "frozen_deposits_percentage": 10,
    ...     "consensus_committee_size": 7000,
    ...     "consensus_threshold": 4667,
    ... }
    >>> args_from_constants(c) == r
    True

    """
    return dict(
        (name, int(constants[name]))
        for name in (
            "blocks_per_cycle",
            "baking_reward_fixed_portion",
            "baking_reward_bonus_per_slot",
            "endorsing_reward_per_slot",
            "frozen_deposits_percentage",
            "consensus_committee_size",
            "consensus_threshold",
        )
    )


def compute(
    total_active_stake,
    staking_balance,
    deposit_cap,
    cycles=1,
    confidence=0.9,
    blocks_per_cycle=8_192,
    frozen_deposits_percentage=10,
    consensus_committee_size=7_000,
    consensus_threshold=4_667,
    endorsing_reward_per_slot=2_857,
    baking_reward_fixed_portion=10_000_000,
    baking_reward_bonus_per_slot=4_286,
    eligibility_threshold=6_000_000,
):
    """
    >>> r = compute(
    ...     100, 5, 0.5,
    ...     consensus_committee_size=8000,
    ...     endorsing_reward_per_slot=2500,
    ...     eligibility_threshold=1
    ... )
    ...
    >>> e = r['endorsements']
    >>> e['count']
    3276800.0
    >>> e['rewards']
    8192.0
    >>> r = compute(
    ...     100, 0, 0.5
    ... )
    >>> r['bakes']['mean']['count']
    0

    """
    active_stake = calc_active_stake(
        staking_balance,
        deposit_cap,
        frozen_deposits_percentage=frozen_deposits_percentage,
    )

    selection_probability = (
        active_stake / total_active_stake
        if staking_balance >= eligibility_threshold
        else 0
    )

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
        "active_stake": active_stake / MUTEZ,
        "cycles": cycles,
        "bakes": {
            "mean": {
                "count": b_mean,
                "rewards": [b_rewards_mean_min / MUTEZ, b_rewards_mean_max / MUTEZ],
            },
            "max": {
                "count": b_max,
                "rewards": [b_rewards_max_min / MUTEZ, b_rewards_max_max / MUTEZ],
            },
        },
        "endorsements": {"count": e_mean, "rewards": e_rewards_mean / MUTEZ},
    }


def fmt_rewards_range(values: Iterable):
    return " - ".join("{0:.1f}".format(v) for v in values)


def fmt_count(value: float):
    return f"{value:.2f}" if value < 100 else f"{value:.0f}"


def format(result):
    output = [
        f"active stake: {result['active_stake']}",
        f"cycles: {result['cycles']}",
        "",
    ]

    key1 = "bakes"
    output.append(key1)
    col1 = "mean"
    col2 = "max"
    bakes_header = " " * 10 + f"{col1:>16} {col2:>16}"
    output.append("-" * len(bakes_header))
    output.append(bakes_header)
    d = result[key1]

    key2 = "count"
    count_mean = d[col1][key2]
    count_max = d[col2][key2]
    output.append(f"{key2:>8}: {fmt_count(count_mean):>16} {fmt_count(count_max):>16}")

    key2 = "rewards"
    rewards_mean = d[col1][key2]
    rewards_max = d[col2][key2]
    output.append(
        f"{key2:>8}: {fmt_rewards_range(rewards_mean):>16} {fmt_rewards_range(rewards_max):>16}"
    )
    output.append("\n")

    key1 = "endorsements"
    output.append(key1)
    output.append("-" * len(bakes_header))
    d = result[key1]

    key2 = "count"
    count = d[key2]
    output.append(f"{key2:>8}: {fmt_count(count):>16}")
    key2 = "rewards"
    rewards = d[key2]
    output.append(f"{key2:>8}: {rewards:16.1f}")
    output.append("\n")

    return "\n".join(output)


def run(
    constants,
    active_rolls,
    full_balance=6000,
    delegated_balance=0,
    deposit_limit=None,
    cycles=1,
    confidence=0.9,
    eligibility_rolls=1,
):
    args = args_from_constants(constants)
    roll_size = int(constants["tokens_per_roll"])
    total_active_stake = active_rolls * roll_size
    staking_balance = full_balance + delegated_balance
    deposit_cap = deposit_limit or full_balance
    result = compute(
        total_active_stake,
        staking_balance * MUTEZ,
        deposit_cap=deposit_cap * MUTEZ,
        cycles=cycles,
        confidence=confidence,
        eligibility_threshold=eligibility_rolls * roll_size,
        **args,
    )
    return format(result)
