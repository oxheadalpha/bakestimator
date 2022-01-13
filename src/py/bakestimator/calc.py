from scipy.stats import binom

MUTEZ = 1000000


def emmy_args_from_constants(constants):
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


def emmy_compute(
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


def tenderbake_args_from_constants(constants):
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
    >>> tenderbake_args_from_constants(c) == r
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


def tenderbake_compute(
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
):
    """
    >>> r = tenderbake_compute(
    ...     100, 5, 0.5, consensus_committee_size=8000, endorsing_reward_per_slot=2500
    ... )
    ...
    >>> e = r['endorsements']
    >>> e['count']
    3276800.0
    >>> e['rewards']
    8192000000.0
    """
    active_stake = calc_active_stake(
        staking_balance,
        deposit_cap,
        frozen_deposits_percentage=frozen_deposits_percentage,
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
