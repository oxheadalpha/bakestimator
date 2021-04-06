def text(result):
    output = [
        f"active rolls: {result['active_rolls']}",
        f"cycles: {result['cycles']}",
        "",
    ]
    for key in ["bakes", "endorsements", "total"]:
        output.append(key)
        for key2 in ["mean", "max"]:
            output.append(f"  {key2}")
            d = result[key][key2]
            for key3 in ["count", "deposits", "rewards"]:
                output.append(f"    {key3:>8}: {d[key3]:.2f}")
        output.append("\n")
    return "\n".join(output)
