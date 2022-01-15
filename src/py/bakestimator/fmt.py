from collections.abc import Iterable


def emmy(result):
    output = [
        f"active rolls: {result['active_rolls']}",
        f"cycles: {result['cycles']}",
        "",
    ]
    for key in ["bakes", "endorsements", "total"]:
        output.append(key)
        col1 = "mean"
        col2 = "max"
        header = " " * 10 + f"{col1:>10} {col2:>10}"
        output.append("-" * len(header))
        output.append(header)
        d = result[key]
        for key2 in ["count", "deposits", "rewards"]:
            mean = d["mean"][key2]
            max = d["max"][key2]
            output.append(f"{key2:>8}: {mean:10.2f} {max:10.2f}")
        output.append("\n")
    return "\n".join(output)


def fmt_rewards_range(values: Iterable):
    return " - ".join("{0:.1f}".format(v) for v in values)


def fmt_count(value: float):
    return f"{value:.2f}" if value < 100 else f"{value:.0f}"


def tenderbake(result):
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
        f"{key2:>8}: {fmt_rewards_range(rewards_mean):>16}ꜩ{fmt_rewards_range(rewards_max):>16}ꜩ"
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
    output.append(f"{key2:>8}: {rewards:16.1f}ꜩ")
    output.append("\n")

    return "\n".join(output)
